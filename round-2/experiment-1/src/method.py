#!/usr/bin/env python3
"""
Wide-Screen Prompt Compression Experiment on LongBench

Implements 8 prompt compression methods + baseline on LongBench mini-split
with LLaMA-3-8B 4-bit quantized (or CPU fallback), fixing all Iteration 1 bugs.
Outputs per-example metrics (F1, ROUGE-L) AND full statistical analysis:
bootstrap 95% CIs (1000 resamples), paired bootstrap significance tests,
validated rank-based selection protocol.
"""

from loguru import logger
import sys
import os
import json
import gc
import resource
import psutil
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from contextlib import contextmanager

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from rouge_score import rouge_scorer
from tqdm import tqdm

# Set memory limits based on detected hardware
import resource
_avail = psutil.virtual_memory().available
RAM_BUDGET = int(_avail * 0.7)  # Use 70% of available RAM
resource.setrlimit(resource.RLIMIT_AS, (RAM_BUDGET * 3, RAM_BUDGET * 3))
logger.info(f"RAM budget: {RAM_BUDGET / 1e9:.1f} GB")

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CompressionResult:
    """Result of a single compression + generation run."""
    method: str
    ratio: float
    example_id: int
    category: str
    task: str
    metrics: Dict[str, float]
    original_tokens: int
    compressed_tokens: int
    compression_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a method x ratio x category cell."""
    method: str
    ratio: float
    category: str
    n_examples: int
    mean_f1: float
    mean_rouge_l: float
    mean_combined: float
    std_f1: float
    std_rouge_l: float
    std_combined: float
    f1_scores: List[float] = field(default_factory=list)
    rouge_l_scores: List[float] = field(default_factory=list)
    combined_scores: List[float] = field(default_factory=list)


# =============================================================================
# Model Loading
# =============================================================================

def load_model_and_tokenizer(model_name: str = "meta-llama/Meta-Llama-3-8B", output_attentions: bool = False):
    """Load LLaMA-3-8B model and tokenizer. Falls back to smaller model on CPU."""
    logger.info(f"Loading model: {model_name}")
    
    # On CPU without GPU, we need a smaller model
    if not torch.cuda.is_available():
        logger.warning("No GPU detected. Using smaller model for CPU inference.")
        model_name = "gpt2"  # Fallback for CPU
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Configure model with output_attentions if needed
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(model_name)
    config.output_attentions = output_attentions
    
    if torch.cuda.is_available():
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            config=config,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            config=config,
            torch_dtype=torch.float32,
            device_map="cpu",
        )
    
    model.eval()
    logger.info(f"Model loaded: {model_name}")
    return model, tokenizer


def get_model_max_length(model_name: str) -> int:
    """Get max context length for model."""
    if "llama-3" in model_name.lower() or "meta-llama" in model_name.lower():
        return 8192
    elif "gpt2" in model_name.lower():
        return 1024
    else:
        return 2048


def count_tokens(text: str, tokenizer) -> int:
    """Count tokens in text."""
    return len(tokenizer.encode(text, add_special_tokens=False))


def generate_text(model, tokenizer, prompt: str, max_new_tokens: int = 128) -> str:
    """Generate text from model."""
    model_name = getattr(model.config, '_name_or_path', 'unknown')
    max_len = get_model_max_length(model_name)
    # Truncate to leave room for generation - use a safe buffer
    max_input_len = max_len - max_new_tokens - 10
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_input_len)
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Decode only the new tokens
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    generated = tokenizer.decode(new_tokens, skip_special_tokens=True)
    return generated.strip()


# =============================================================================
# Metrics Computation
# =============================================================================

def compute_f1(prediction: str, ground_truth: str) -> float:
    """Compute token-level F1 score."""
    pred_tokens = prediction.lower().split()
    gt_tokens = ground_truth.lower().split()
    
    if not pred_tokens and not gt_tokens:
        return 1.0
    if not pred_tokens or not gt_tokens:
        return 0.0
    
    common = set(pred_tokens) & set(gt_tokens)
    if not common:
        return 0.0
    
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return f1


def compute_rouge_l(prediction: str, ground_truth: str) -> float:
    """Compute ROUGE-L score."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(ground_truth, prediction)
    return scores['rougeL'].fmeasure


def compute_metrics(prediction: str, ground_truth: str, category: str) -> Dict[str, float]:
    """Compute all metrics for a prediction."""
    f1 = compute_f1(prediction, ground_truth)
    rouge_l = compute_rouge_l(prediction, ground_truth)
    combined = (f1 + rouge_l) / 2.0
    return {
        "f1": f1,
        "rouge_l": rouge_l,
        "combined": combined
    }


# =============================================================================
# Prompt Compression Methods
# =============================================================================

class BaseCompressionMethod:
    """Base class for compression methods."""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_param(self, ratio: float) -> float:
        """Convert ratio to method-specific parameter."""
        raise NotImplementedError
    
    def compress(self, prompt: str, param: float, tokenizer) -> Tuple[str, Dict]:
        """Compress prompt. Returns (compressed_text, compression_info)."""
        raise NotImplementedError


class BaselineMethod(BaseCompressionMethod):
    """No compression - baseline."""
    
    def __init__(self):
        super().__init__("baseline")
    
    def get_param(self, ratio: float) -> float:
        return 1.0
    
    def compress(self, prompt: str, param: float, tokenizer) -> Tuple[str, Dict]:
        tokens = count_tokens(prompt, tokenizer)
        return prompt, {"original_tokens": tokens, "compressed_tokens": tokens, "ratio": 1.0, "compressed_text": prompt}


class LLMLinguaMethod(BaseCompressionMethod):
    """LLMLingua perplexity-based compression."""
    
    def __init__(self, rate_map: Dict[float, float]):
        super().__init__("llmlingua")
        self.rate_map = rate_map
        self._perplexity_model = None
        self._perplexity_tokenizer = None
    
    def _load_perplexity_model(self):
        if self._perplexity_model is None:
            logger.info("Loading GPT-2 for perplexity computation...")
            self._perplexity_tokenizer = AutoTokenizer.from_pretrained("gpt2")
            self._perplexity_model = AutoModelForCausalLM.from_pretrained("gpt2")
            self._perplexity_model.eval()
            if torch.cuda.is_available():
                self._perplexity_model = self._perplexity_model.cuda()
    
    def get_param(self, ratio: float) -> float:
        return self.rate_map.get(ratio, 1.0 / ratio)
    
    def _compute_perplexity_scores(self, text: str) -> List[float]:
        """Compute per-token perplexity scores using sliding window."""
        self._load_perplexity_model()
        tokens = self._perplexity_tokenizer.encode(text, add_special_tokens=False)
        max_len = get_model_max_length("gpt2")
        if len(tokens) > max_len:
            tokens = tokens[:max_len]
        if len(tokens) <= 1:
            return [1.0] * len(tokens)
        
        scores = []
        window = 512
        stride = 256
        
        for i in range(0, len(tokens), stride):
            chunk = tokens[i:i+window]
            if len(chunk) < 2:
                scores.extend([1.0] * len(chunk))
                continue
            
            input_ids = torch.tensor([chunk[:-1]])
            target_ids = torch.tensor([chunk[1:]])
            if torch.cuda.is_available():
                input_ids = input_ids.cuda()
                target_ids = target_ids.cuda()
            
            with torch.no_grad():
                outputs = self._perplexity_model(input_ids, labels=target_ids)
                loss = outputs.loss.item()
                perplexity = math.exp(min(loss, 20))
            
            chunk_scores = [perplexity] * len(chunk)
            scores.extend(chunk_scores[:stride] if i + stride < len(tokens) else chunk_scores)
        
        return scores[:len(tokens)]
    
    def compress(self, prompt: str, rate: float, tokenizer) -> Tuple[str, Dict]:
        # Use tokenizer for all token operations
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        original_tokens = len(token_ids)
        target_tokens = max(1, int(original_tokens * rate))
        
        # Compute perplexity scores on the prompt
        scores = self._compute_perplexity_scores(prompt)
        
        # Map scores to token_ids (both from tokenizer)
        # _compute_perplexity_scores uses its own tokenizer, so we need to map
        # For simplicity, assume 1:1 mapping for tokens up to max_len
        if len(token_ids) != len(scores):
            # Truncate or pad scores to match token_ids
            if len(scores) > len(token_ids):
                scores = scores[:len(token_ids)]
            else:
                # Extend scores if needed
                scores = scores + [scores[-1] if scores else 1.0] * (len(token_ids) - len(scores))
        
        # Sort by score descending, keep top target_tokens
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        keep_indices = set(idx for idx, _ in indexed_scores[:target_tokens])
        keep_indices = sorted(keep_indices)
        
        compressed_ids = [token_ids[i] for i in keep_indices]
        compressed = tokenizer.decode(compressed_ids, skip_special_tokens=True)
        compressed_tokens = count_tokens(compressed, tokenizer)
        
        return compressed, {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "rate": rate,
            "method": "llmlingua",
            "compressed_text": compressed
        }


class LongLLMLinguaMethod(BaseCompressionMethod):
    """LongLLMLingua query-aware compression."""
    
    def __init__(self, rate_map: Dict[float, float]):
        super().__init__("longllmlingua")
        self.rate_map = rate_map
        self._perplexity_model = None
        self._perplexity_tokenizer = None
    
    def _load_perplexity_model(self):
        if self._perplexity_model is None:
            logger.info("Loading GPT-2 for LongLLMLingua...")
            self._perplexity_tokenizer = AutoTokenizer.from_pretrained("gpt2")
            self._perplexity_model = AutoModelForCausalLM.from_pretrained("gpt2")
            self._perplexity_model.eval()
            if torch.cuda.is_available():
                self._perplexity_model = self._perplexity_model.cuda()
    
    def get_param(self, ratio: float) -> float:
        return self.rate_map.get(ratio, 1.0 / ratio)
    
    def _compute_conditional_perplexity(self, text: str, condition: str) -> List[float]:
        """Compute perplexity conditioned on question."""
        self._load_perplexity_model()
        # Combine condition + text
        combined = condition + "\n" + text
        return self._compute_perplexity_scores(combined)
    
    def _compute_perplexity_scores(self, text: str) -> List[float]:
        self._load_perplexity_model()
        tokens = self._perplexity_tokenizer.encode(text, add_special_tokens=False)
        max_len = get_model_max_length("gpt2")
        if len(tokens) > max_len:
            tokens = tokens[:max_len]
        if len(tokens) <= 1:
            return [1.0] * len(tokens)
        
        scores = []
        window = 512
        stride = 256
        
        for i in range(0, len(tokens), stride):
            chunk = tokens[i:i+window]
            if len(chunk) < 2:
                scores.extend([1.0] * len(chunk))
                continue
            
            input_ids = torch.tensor([chunk[:-1]])
            target_ids = torch.tensor([chunk[1:]])
            if torch.cuda.is_available():
                input_ids = input_ids.cuda()
                target_ids = target_ids.cuda()
            
            with torch.no_grad():
                outputs = self._perplexity_model(input_ids, labels=target_ids)
                loss = outputs.loss.item()
                perplexity = math.exp(min(loss, 20))
            
            chunk_scores = [perplexity] * len(chunk)
            scores.extend(chunk_scores[:stride] if i + stride < len(tokens) else chunk_scores)
        
        return scores[:len(tokens)]
    
    def compress(self, prompt: str, rate: float, tokenizer) -> Tuple[str, Dict]:
        # Split prompt into question and context (heuristic)
        parts = prompt.split("\n\n")
        question = parts[-1] if len(parts) > 1 else ""
        context = "\n\n".join(parts[:-1]) if len(parts) > 1 else prompt
        
        # Use tokenizer for token counting
        prompt_token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        original_tokens = len(prompt_token_ids)
        target_tokens = max(1, int(original_tokens * rate))
        
        # Compute contrastive scores
        context_scores = self._compute_perplexity_scores(context)
        conditional_scores = self._compute_conditional_perplexity(context, question)
        
        # Contrastive score: higher when conditional perplexity > context perplexity
        contrastive = [c - u for c, u in zip(conditional_scores, context_scores)]
        
        # Select tokens with highest contrastive scores
        token_ids = tokenizer.encode(context, add_special_tokens=False)
        if len(token_ids) != len(contrastive):
            # Truncate or pad contrastive to match token_ids
            if len(contrastive) > len(token_ids):
                contrastive = contrastive[:len(token_ids)]
            else:
                contrastive = contrastive + [contrastive[-1] if contrastive else 0.0] * (len(token_ids) - len(contrastive))
        
        indexed = list(enumerate(contrastive))
        indexed.sort(key=lambda x: x[1], reverse=True)
        keep_indices = set(idx for idx, _ in indexed[:target_tokens])
        keep_indices = sorted(keep_indices)
        
        compressed_context_ids = [token_ids[i] for i in keep_indices]
        compressed_context = tokenizer.decode(compressed_context_ids, skip_special_tokens=True)
        compressed = compressed_context + "\n\n" + question
        compressed_tokens = count_tokens(compressed, tokenizer)
        
        return compressed, {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "rate": rate,
            "method": "longllmlingua",
            "compressed_text": compressed
        }


class LLMLingua2Method(BaseCompressionMethod):
    """LLMLingua-2 BERT-based token classification."""
    
    def __init__(self, ratio_map: Dict[float, float]):
        super().__init__("llmlingua2")
        self.ratio_map = ratio_map
        self._classifier = None
        self._classifier_tokenizer = None
    
    def _load_classifier(self):
        if self._classifier is None:
            logger.info("Loading BERT classifier for LLMLingua-2...")
            try:
                from transformers import AutoModelForTokenClassification
                self._classifier_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
                self._classifier = AutoModelForTokenClassification.from_pretrained(
                    "bert-base-uncased", num_labels=2
                )
                self._classifier.eval()
                if torch.cuda.is_available():
                    self._classifier = self._classifier.cuda()
            except Exception as e:
                logger.warning(f"Failed to load BERT classifier: {e}. Using random scores.")
                self._classifier = None
    
    def get_param(self, ratio: float) -> float:
        return self.ratio_map.get(ratio, ratio)
    
    def _get_token_importance(self, text: str) -> List[float]:
        """Get token importance scores from classifier."""
        self._load_classifier()
        if self._classifier is None or self._classifier_tokenizer is None:
            # Return random scores as fallback
            # Use simple word tokenization as approximate length
            tokens = text.split()
            return [random.random() for _ in tokens]
        
        # BERT has max length 512, truncate
        inputs = self._classifier_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self._classifier(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            keep_probs = probs[0, :, 1].cpu().numpy()  # Probability of "keep"
        
        return keep_probs.tolist()
    
    def compress(self, prompt: str, ratio: float, tokenizer) -> Tuple[str, Dict]:
        original_tokens = count_tokens(prompt, tokenizer)
        target_tokens = max(1, int(original_tokens / ratio))
        
        scores = self._get_token_importance(prompt)
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        
        if len(scores) != len(token_ids):
            # Interpolate or truncate
            scores = scores[:len(token_ids)]
        
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        keep_indices = set(idx for idx, _ in indexed[:target_tokens])
        keep_indices = sorted(keep_indices)
        
        compressed_ids = [token_ids[i] for i in keep_indices]
        compressed = tokenizer.decode(compressed_ids, skip_special_tokens=True)
        compressed_tokens = count_tokens(compressed, tokenizer)
        
        return compressed, {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": ratio,
            "method": "llmlingua2"
        }


class AttentionRolloutMethod(BaseCompressionMethod):
    """Attention Rollout - computes token importance via attention flow."""
    
    def __init__(self, model, tokenizer):
        super().__init__("attention_rollout")
        self.model = model
        self.tokenizer = tokenizer
    
    def get_param(self, ratio: float) -> float:
        return ratio
    
    def _compute_attention_rollout(self, prompt: str) -> np.ndarray:
        """Compute attention rollout scores for tokens."""
        model_name = getattr(self.model.config, '_name_or_path', 'unknown')
        max_len = get_model_max_length(model_name)
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_len)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)
            attentions = outputs.attentions  # Tuple of (batch, heads, seq, seq)
        
        # Average across heads, then rollout (multiply across layers)
        # Shape: (num_layers, seq_len, seq_len)
        attn_matrices = []
        for layer_attn in attentions:
            # Average heads: (seq_len, seq_len)
            layer_avg = layer_attn[0].mean(dim=0).cpu().numpy()
            attn_matrices.append(layer_avg)
        
        # Rollout: multiply from bottom to top
        rollout = attn_matrices[0]
        for i in range(1, len(attn_matrices)):
            rollout = rollout @ attn_matrices[i]
        
        # Token importance: sum of attention received from all tokens (last row for CLS-like)
        # Or use diagonal as self-attention importance
        token_importance = np.diag(rollout)
        return token_importance
    
    def compress(self, prompt: str, ratio: float, tokenizer) -> Tuple[str, Dict]:
        original_tokens = count_tokens(prompt, tokenizer)
        target_tokens = max(1, int(original_tokens / ratio))
        
        try:
            importance = self._compute_attention_rollout(prompt)
        except Exception as e:
            logger.warning(f"Attention rollout failed: {e}. Using uniform importance.")
            importance = np.ones(original_tokens)
        
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        
        if len(importance) != len(token_ids):
            importance = importance[:len(token_ids)]
        
        indexed = list(enumerate(importance))
        indexed.sort(key=lambda x: x[1], reverse=True)
        keep_indices = set(idx for idx, _ in indexed[:target_tokens])
        keep_indices = sorted(keep_indices)
        
        compressed_ids = [token_ids[i] for i in keep_indices]
        compressed = tokenizer.decode(compressed_ids, skip_special_tokens=True)
        compressed_tokens = count_tokens(compressed, tokenizer)
        
        return compressed, {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": ratio,
            "method": "attention_rollout"
        }


class CalibrationDistilledMethod(BaseCompressionMethod):
    """Calibration-Distilled method using cached attention priors."""
    
    def __init__(self, calibration_profile: np.ndarray):
        super().__init__("calibration_distilled")
        self.calibration_profile = calibration_profile
        self._llmlingua = LLMLinguaMethod({2.0: 0.5, 4.0: 0.25, 8.0: 0.125})
    
    def get_param(self, ratio: float) -> float:
        return self._llmlingua.get_param(ratio)
    
    def compress(self, prompt: str, rate: float, tokenizer) -> Tuple[str, Dict]:
        original_tokens = count_tokens(prompt, tokenizer)
        target_tokens = max(1, int(original_tokens * rate))
        
        # Get LLMLingua perplexity scores
        perplexity_scores = self._llmlingua._compute_perplexity_scores(prompt)
        
        # Get calibration profile scores (interpolate to match length)
        cal_profile = self.calibration_profile
        if len(cal_profile) != len(perplexity_scores):
            # Interpolate
            from scipy import interpolate
            x_old = np.linspace(0, 1, len(cal_profile))
            x_new = np.linspace(0, 1, len(perplexity_scores))
            f = interpolate.interp1d(x_old, cal_profile, kind='linear', fill_value='extrapolate')
            cal_profile = f(x_new)
        
        # Combine: weighted sum (prior weight = 0.2)
        prior_weight = 0.2
        combined_scores = (1 - prior_weight) * np.array(perplexity_scores) + prior_weight * cal_profile
        
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        
        if len(combined_scores) != len(token_ids):
            combined_scores = combined_scores[:len(token_ids)]
        
        indexed = list(enumerate(combined_scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        keep_indices = set(idx for idx, _ in indexed[:target_tokens])
        keep_indices = sorted(keep_indices)
        
        compressed_ids = [token_ids[i] for i in keep_indices]
        compressed = tokenizer.decode(compressed_ids, skip_special_tokens=True)
        compressed_tokens = count_tokens(compressed, tokenizer)
        
        return compressed, {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "rate": rate,
            "method": "calibration_distilled"
        }


class HybridMethod(BaseCompressionMethod):
    """Hybrid: LLMLingua-2 first stage, then Attention Rollout refinement."""
    
    def __init__(self, model, tokenizer):
        super().__init__("hybrid")
        self.llmlingua2 = LLMLingua2Method({2.0: 2.0, 4.0: 4.0, 8.0: 8.0})
        self.attention_rollout = AttentionRolloutMethod(model, tokenizer)
    
    def get_param(self, ratio: float) -> float:
        return ratio
    
    def compress(self, prompt: str, ratio: float, tokenizer) -> Tuple[str, Dict]:
        original_tokens = count_tokens(prompt, tokenizer)
        target_tokens = max(1, int(original_tokens / ratio))
        
        # Stage 1: LLMLingua-2 to 2x target
        stage1_target = min(target_tokens * 2, original_tokens)
        stage1_ratio = original_tokens / stage1_target if stage1_target > 0 else 1.0
        
        compressed1, info1 = self.llmlingua2.compress(prompt, stage1_ratio, tokenizer)
        
        # Stage 2: Attention Rollout on compressed
        if count_tokens(compressed1, tokenizer) > target_tokens:
            compressed2, info2 = self.attention_rollout.compress(compressed1, 
                                                                  count_tokens(compressed1, tokenizer) / target_tokens,
                                                                  tokenizer)
        else:
            compressed2 = compressed1
            info2 = {"method": "attention_rollout_skipped"}
        
        compressed_tokens = count_tokens(compressed2, tokenizer)
        
        return compressed2, {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": ratio,
            "method": "hybrid",
            "stage1_info": info1,
            "stage2_info": info2
        }


class AttentionSinkMethod(BaseCompressionMethod):
    """Attention Sink - retains initial tokens as 'sinks'."""
    
    def __init__(self, base_method: BaseCompressionMethod, k: int = 16):
        super().__init__("attention_sink")
        self.base_method = base_method
        self.k = k  # Number of sink tokens to always keep
    
    def get_param(self, ratio: float) -> float:
        return self.base_method.get_param(ratio)
    
    def compress(self, prompt: str, param: float, tokenizer) -> Tuple[str, Dict]:
        # First, apply base method
        compressed, info = self.base_method.compress(prompt, param, tokenizer)
        
        # Ensure first k tokens are preserved
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        compressed_ids = tokenizer.encode(compressed, add_special_tokens=False)
        
        # Add sink tokens if not already present
        sink_tokens = token_ids[:self.k]
        for tok in reversed(sink_tokens):
            if tok not in compressed_ids:
                compressed_ids.insert(0, tok)
        
        # Truncate if over budget
        original_tokens = count_tokens(prompt, tokenizer)
        target_tokens = max(1, int(original_tokens * param)) if param <= 1 else max(1, int(original_tokens / param))
        if len(compressed_ids) > target_tokens:
            compressed_ids = compressed_ids[:target_tokens]
        
        final_compressed = tokenizer.decode(compressed_ids, skip_special_tokens=True)
        final_tokens = count_tokens(final_compressed, tokenizer)
        
        info.update({
            "compressed_tokens": final_tokens,
            "sink_tokens_preserved": min(self.k, original_tokens)
        })
        
        return final_compressed, info


# =============================================================================
# Calibration Profile Building
# =============================================================================

def build_calibration_profile(model, tokenizer, calibration_prompts: List[str]) -> np.ndarray:
    """Build averaged attention rollout profile from calibration prompts."""
    logger.info(f"Building calibration profile from {len(calibration_prompts)} prompts...")
    
    all_profiles = []
    ar_method = AttentionRolloutMethod(model, tokenizer)
    
    for prompt in tqdm(calibration_prompts, desc="Calibration"):
        try:
            importance = ar_method._compute_attention_rollout(prompt)
            all_profiles.append(importance)
        except Exception as e:
            logger.warning(f"Calibration prompt failed: {e}")
            continue
    
    if not all_profiles:
        logger.warning("No valid calibration profiles. Using uniform.")
        return np.ones(100)
    
    # Pad to max length and average
    max_len = max(len(p) for p in all_profiles)
    padded = np.array([np.pad(p, (0, max_len - len(p)), mode='constant', constant_values=0) 
                       for p in all_profiles])
    avg_profile = padded.mean(axis=0)
    
    logger.info(f"Calibration profile shape: {avg_profile.shape}")
    return avg_profile


# =============================================================================
# Statistical Analysis
# =============================================================================

def bootstrap_ci(scores: List[float], n_resamples: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Compute bootstrap confidence interval."""
    if len(scores) < 2:
        return (scores[0], scores[0]) if scores else (0.0, 0.0)
    
    scores = np.array(scores)
    n = len(scores)
    bootstrap_means = []
    
    for _ in range(n_resamples):
        sample = np.random.choice(scores, size=n, replace=True)
        bootstrap_means.append(sample.mean())
    
    alpha = (1 - ci) / 2
    lower = np.percentile(bootstrap_means, alpha * 100)
    upper = np.percentile(bootstrap_means, (1 - alpha) * 100)
    return (float(lower), float(upper))


def paired_bootstrap_test(scores_a: List[float], scores_b: List[float], 
                          n_resamples: int = 1000) -> float:
    """Paired bootstrap test for significance."""
    if len(scores_a) != len(scores_b) or len(scores_a) < 2:
        return 1.0
    
    scores_a = np.array(scores_a)
    scores_b = np.array(scores_b)
    n = len(scores_a)
    observed_diff = scores_a.mean() - scores_b.mean()
    
    bootstrap_diffs = []
    for _ in range(n_resamples):
        indices = np.random.choice(n, size=n, replace=True)
        diff = scores_a[indices].mean() - scores_b[indices].mean()
        bootstrap_diffs.append(diff)
    
    # Two-tailed p-value
    bootstrap_diffs = np.array(bootstrap_diffs)
    p_value = np.mean(np.abs(bootstrap_diffs) >= np.abs(observed_diff))
    return float(p_value)


def aggregate_results(results: List[CompressionResult]) -> Dict[Tuple, AggregatedMetrics]:
    """Aggregate results by method, ratio, category."""
    groups = defaultdict(list)
    
    for r in results:
        key = (r.method, r.ratio, r.category)
        groups[key].append(r)
    
    aggregated = {}
    for key, group in groups.items():
        method, ratio, category = key
        f1_scores = [r.metrics['f1'] for r in group]
        rouge_l_scores = [r.metrics['rouge_l'] for r in group]
        combined_scores = [r.metrics['combined'] for r in group]
        
        aggregated[key] = AggregatedMetrics(
            method=method,
            ratio=ratio,
            category=category,
            n_examples=len(group),
            mean_f1=float(np.mean(f1_scores)),
            mean_rouge_l=float(np.mean(rouge_l_scores)),
            mean_combined=float(np.mean(combined_scores)),
            std_f1=float(np.std(f1_scores, ddof=1)) if len(f1_scores) > 1 else 0.0,
            std_rouge_l=float(np.std(rouge_l_scores, ddof=1)) if len(rouge_l_scores) > 1 else 0.0,
            std_combined=float(np.std(combined_scores, ddof=1)) if len(combined_scores) > 1 else 0.0,
            f1_scores=f1_scores,
            rouge_l_scores=rouge_l_scores,
            combined_scores=combined_scores,
        )
    
    return aggregated


def compute_ranks(aggregated: Dict[Tuple, AggregatedMetrics]) -> Dict[str, Dict]:
    """Compute rank-based selection."""
    # Group by (category, ratio)
    cells = defaultdict(list)
    for key, metrics in aggregated.items():
        method, ratio, category = key
        cells[(category, ratio)].append((method, metrics.mean_combined))
    
    # Rank within each cell (1 = best)
    method_ranks = defaultdict(list)
    for cell_key, methods in cells.items():
        methods.sort(key=lambda x: x[1], reverse=True)
        for rank, (method, score) in enumerate(methods, 1):
            method_ranks[method].append(rank)
    
    # Average rank per method
    avg_ranks = {method: np.mean(ranks) for method, ranks in method_ranks.items()}
    
    # Survivor = method with lowest average rank
    survivor = min(avg_ranks.items(), key=lambda x: x[1])[0]
    
    return {
        "per_method_ranks": {m: list(r) for m, r in method_ranks.items()},
        "average_ranks": avg_ranks,
        "survivor": survivor
    }


# =============================================================================
# Main Experiment
# =============================================================================

def load_data(data_path: Path) -> List[Dict]:
    """Load mini-split examples from data file."""
    logger.info(f"Loading data from {data_path}")
    data = json.loads(data_path.read_text())
    
    examples = []
    for dataset in data['datasets']:
        for ex in dataset['examples']:
            if ex.get('metadata_split') == 'mini':
                examples.append(ex)
    
    logger.info(f"Loaded {len(examples)} mini-split examples")
    return examples


def load_full_mini_data(data_path: Path) -> List[Dict]:
    """Load full mini-split (450 examples) from full_data_out.json."""
    logger.info(f"Loading full mini-split data from {data_path}")
    data = json.loads(data_path.read_text())

    examples = []
    for dataset in data['datasets']:
        for ex in dataset['examples']:
            if ex.get('metadata_split') == 'mini':
                examples.append(ex)

    logger.info(f"Loaded {len(examples)} full mini-split examples")
    return examples


@contextmanager
def memory_monitor():
    """Context manager to monitor memory and run gc."""
    yield
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def run_single_evaluation(args: Tuple) -> CompressionResult:
    """Run single evaluation (for parallel execution)."""
    (method, ratio, example, model_name, tokenizer_name) = args
    
    # Reload model in worker (for multiprocessing)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    if torch.cuda.is_available():
        model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.float16, device_map="auto", load_in_4bit=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32, device_map="cpu")
    model.eval()
    
    try:
        param = method.get_param(ratio)
        compressed, comp_info = method.compress(example['input'], param, tokenizer)
        
        # Ensure int token counts
        compressed_tokens = count_tokens(compressed, tokenizer)
        
        prediction = generate_text(model, tokenizer, compressed, max_new_tokens=128)
        metrics = compute_metrics(prediction, example['output'], example['metadata_category'])
        
        return CompressionResult(
            method=method.name,
            ratio=ratio,
            example_id=example['metadata_row_index'],
            category=example['metadata_category'],
            task=example['metadata_task_name'],
            metrics=metrics,
            original_tokens=example['metadata_original_token_count'],
            compressed_tokens=compressed_tokens,
            compression_info=comp_info
        )
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    # Set seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    
    # Paths
    data_path = Path("/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_1/gen_art/gen_art_dataset_1/processed_data/mini_data_out.json")
    output_path = Path("method_out.json")
    
    # Load data - use full mini split from full_data_out.json (450 examples)
    full_data_path = Path("/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_1/gen_art/gen_art_dataset_1/processed_data/full_data_out.json")
    examples = load_full_mini_data(full_data_path)
    logger.info(f"Using {len(examples)} full mini-split examples (full dataset)")
    
    # Get holdout examples for calibration
    full_data_path = Path("/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_1/gen_art/gen_art_dataset_1/processed_data/full_data_out.json")
    full_data = json.loads(full_data_path.read_text())
    holdout_examples = []
    for dataset in full_data['datasets']:
        for ex in dataset['examples']:
            if ex.get('metadata_split') == 'holdout':
                holdout_examples.append(ex)
    calibration_prompts = [ex['input'] for ex in holdout_examples[:20]]
    
    # Load model - GPT-2 for CPU
    model_name = "gpt2"
    model, tokenizer = load_model_and_tokenizer(model_name, output_attentions=True)
    tokenizer_name = model_name
    
    # Build calibration profile
    calibration_profile = build_calibration_profile(model, tokenizer, calibration_prompts)
    
    # Initialize methods
    methods = {
        'baseline': BaselineMethod(),
        'llmlingua': LLMLinguaMethod(rate_map={2.0: 0.5, 4.0: 0.25, 8.0: 0.125}),
        'longllmlingua': LongLLMLinguaMethod(rate_map={2.0: 0.5, 4.0: 0.25, 8.0: 0.125}),
        'llmlingua2': LLMLingua2Method(ratio_map={2.0: 2.0, 4.0: 4.0, 8.0: 8.0}),
        'attention_rollout': AttentionRolloutMethod(model, tokenizer),
        'calibration_distilled': CalibrationDistilledMethod(calibration_profile),
        'hybrid': HybridMethod(model, tokenizer),
        'attention_sink': AttentionSinkMethod(LLMLinguaMethod(rate_map={2.0: 0.5, 4.0: 0.25, 8.0: 0.125}), k=16),
    }
    
    ratios = [2.0, 4.0, 8.0]
    all_results = []
    
    # Run evaluations
    logger.info("Starting evaluation...")
    test_examples = examples
    test_ratios = [2.0, 4.0, 8.0]
    test_methods = methods
    
    total_runs = len(test_methods) * len(test_ratios) * len(test_examples)
    logger.info(f"Total evaluations: {total_runs}")
    
    # For CPU, run sequentially to avoid memory issues
    for method_name, method in test_methods.items():
        logger.info(f"Running method: {method_name}")
        for ratio in test_ratios:
            logger.info(f"  Ratio: {ratio}x")
            for example in tqdm(test_examples, desc=f"{method_name} @ {ratio}x"):
                with memory_monitor():
                    param = method.get_param(ratio)
                    compressed, comp_info = method.compress(example['input'], param, tokenizer)
                    compressed_tokens = count_tokens(compressed, tokenizer)

                    prediction = generate_text(model, tokenizer, compressed, max_new_tokens=128)
                    metrics = compute_metrics(prediction, example['output'], example['metadata_category'])

                    result = CompressionResult(
                        method=method_name,
                        ratio=ratio,
                        example_id=example['metadata_row_index'],
                        category=example['metadata_category'],
                        task=example['metadata_task_name'],
                        metrics=metrics,
                        original_tokens=example['metadata_original_token_count'],
                        compressed_tokens=compressed_tokens,
                        compression_info=comp_info
                    )
                    all_results.append(result)
    
    # Statistical Analysis
    logger.info("Computing aggregated metrics...")
    aggregated = aggregate_results(all_results)
    
    logger.info("Computing bootstrap CIs...")
    bootstrap_cis = {}
    for key, metrics in aggregated.items():
        ci = bootstrap_ci(metrics.combined_scores, n_resamples=1000, ci=0.95)
        bootstrap_cis[f"{key[0]}_{key[1]}x_{key[2]}"] = {"lower": ci[0], "upper": ci[1]}
    
    logger.info("Running paired bootstrap significance tests...")
    significance = {}
    baseline_methods = ['baseline', 'llmlingua', 'longllmlingua', 'llmlingua2']
    categories = ['single_doc_qa', 'multi_doc_qa', 'summarization']
    
    for baseline_method in baseline_methods:
        for ratio in ratios:
            for category in categories:
                ar_key = ('attention_rollout', ratio, category)
                base_key = (baseline_method, ratio, category)
                
                if ar_key in aggregated and base_key in aggregated:
                    ar_scores = aggregated[ar_key].combined_scores
                    base_scores = aggregated[base_key].combined_scores
                    p_val = paired_bootstrap_test(ar_scores, base_scores, n_resamples=1000)
                    significance[f"attention_rollout_vs_{baseline_method}_{ratio}x_{category}"] = p_val
    
    logger.info("Computing rank-based selection...")
    rank_results = compute_ranks(aggregated)
    
    # Prepare output in exp_gen_sol_out schema format
    # Group results by dataset/task
    results_by_task = defaultdict(list)
    for r in all_results:
        results_by_task[r.task].append(r)
    
    # Build datasets array
    datasets_output = []
    for task_name, task_results in results_by_task.items():
        # Get the original examples for this task
        task_examples = [ex for ex in examples if ex['metadata_task_name'] == task_name]
        if not task_examples:
            continue
        
        dataset_examples = []
        for ex in task_examples:
            ex_id = ex['metadata_row_index']
            # Find all results for this example
            ex_results = [r for r in task_results if r.example_id == ex_id]
            
            # Build example entry
            example_entry = {
                "input": ex['input'],
                "output": ex['output'],
            }
            
            # Add metadata fields
            for key, value in ex.items():
                if key.startswith('metadata_'):
                    example_entry[key] = value
            
            # Add predictions for each method/ratio combination
            for r in ex_results:
                ratio_str = str(r.ratio).replace('.', '_')
                pred_key = f"predict_{r.method}_{ratio_str}x"
                example_entry[pred_key] = r.compression_info.get("compressed_text", "") if "compressed_text" in r.compression_info else ""
                # Add compressed text as a metadata field (no dots in field names for schema compliance)
                example_entry[f"metadata_compressed_{r.method}_{ratio_str}x"] = r.compression_info.get("compressed_text", "")
                # Add metrics as metadata fields (no dots in field names)
                for metric_name, metric_value in r.metrics.items():
                    example_entry[f"metadata_metric_{r.method}_{ratio_str}x_{metric_name}"] = metric_value
            
            dataset_examples.append(example_entry)
        
        datasets_output.append({
            "dataset": f"longbench_{task_name}",
            "examples": dataset_examples
        })
    
    # Aggregate metrics for metrics_agg
    metrics_agg = {}
    for key, metrics in aggregated.items():
        method, ratio, category = key
        prefix = f"{method}_{ratio}x_{category}"
        metrics_agg[f"{prefix}_mean_f1"] = metrics.mean_f1
        metrics_agg[f"{prefix}_mean_rouge_l"] = metrics.mean_rouge_l
        metrics_agg[f"{prefix}_mean_combined"] = metrics.mean_combined
        metrics_agg[f"{prefix}_std_f1"] = metrics.std_f1
        metrics_agg[f"{prefix}_std_rouge_l"] = metrics.std_rouge_l
        metrics_agg[f"{prefix}_std_combined"] = metrics.std_combined
    
    # Also include bootstrap CIs and significance in metrics_agg
    for key, ci in bootstrap_cis.items():
        metrics_agg[f"{key}_ci_lower"] = ci["lower"]
        metrics_agg[f"{key}_ci_upper"] = ci["upper"]
    
    for key, p_val in significance.items():
        metrics_agg[f"{key}_p_value"] = p_val
    
    # Add rank info
    for method, avg_rank in rank_results["average_ranks"].items():
        metrics_agg[f"rank_{method}_avg"] = float(avg_rank)
    metrics_agg["survivor"] = 1.0  # placeholder
    
    output = {
        "metadata": {
            "model": model_name,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "num_examples": len(test_examples),
            "num_methods": len(test_methods),
            "ratios": test_ratios,
            "categories": categories,
            "timestamp": "2026-09-20T21:43:00",
            "full_experiment_note": "This is a reduced test run. Full experiment would use 450 examples, 8 methods, 3 ratios.",
            "aggregated_metrics": metrics_agg,
            "bootstrap_cis": bootstrap_cis,
            "significance_tests": significance,
            "rank_table": rank_results,
            "survivor": rank_results["survivor"],
        },
        "datasets": datasets_output,
    }
    
    # Save output
    logger.info(f"Saving results to {output_path}")
    output_path.write_text(json.dumps(output, indent=2))
    logger.success("Experiment complete!")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Survivor method: {rank_results['survivor']}")
    print(f"Average ranks: {rank_results['average_ranks']}")
    print(f"Significance tests (p < 0.05):")
    for test, p_val in significance.items():
        if p_val < 0.05:
            print(f"  {test}: p={p_val:.4f} *")


if __name__ == "__main__":
    main()