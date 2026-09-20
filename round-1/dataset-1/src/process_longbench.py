#!/usr/bin/env python3
"""Process LongBench dataset for target-model prompt compression evaluation.

Extracts 9 tasks (3 per category), tokenizes with LLaMA-3-8B, computes original token counts,
defines compression budgets, and creates stratified mini-split (50 examples/task) + holdout.
"""

from loguru import logger
from pathlib import Path
import json
import sys
import random

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

# Configuration
TASKS = {
    "single_doc_qa": ["narrativeqa", "qasper", "multifieldqa_en"],
    "multi_doc_qa": ["hotpotqa", "2wikimqa", "musique"],
    "summarization": ["multi_news", "gov_report", "qmsum"],
}

ALL_TASKS = [t for tasks in TASKS.values() for t in tasks]
MINI_EXAMPLES_PER_TASK = 50
COMPRESSION_BUDGETS = {
    "2x": 0.5,      # retain 50%
    "4x": 0.25,     # retain 25%
    "8x": 0.125,    # retain 12.5%
}

OUTPUT_DIR = Path("processed_data")
OUTPUT_DIR.mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# Tokenizer
from transformers import AutoTokenizer


@logger.catch(reraise=True)
def load_task_data(task_name: str, split: str = "test"):
    """Load a specific task from LongBench."""
    from datasets import load_dataset
    logger.info(f"Loading {task_name} ({split})...")
    ds = load_dataset("Xnhyacinth/LongBench", task_name, split=split)
    return ds


@logger.catch(reraise=True)
def tokenize_text(text: str, tokenizer) -> int:
    """Tokenize text and return token count."""
    return len(tokenizer.encode(text, add_special_tokens=False))


@logger.catch(reraise=True)
def process_task(task_name: str, category: str, tokenizer, all_examples: list) -> list:
    """Process a single task and return examples with token counts."""
    logger.info(f"Processing {task_name} ({category})...")
    
    ds = load_task_data(task_name)
    
    for idx, item in enumerate(ds):
        context = item["context"]
        question = item["question"]
        answers = item["answers"]
        
        # Compute original token count from context
        original_token_count = tokenize_text(context, tokenizer)
        
        if original_token_count <= 0:
            logger.warning(f"Zero token count for {task_name} example {idx}, skipping")
            continue
        
        # Compute compression budgets
        compression_budgets = {
            budget_name: int(original_token_count * ratio)
            for budget_name, ratio in COMPRESSION_BUDGETS.items()
        }
        
        example = {
            "task_id": f"{task_name}_{idx}",
            "task_name": task_name,
            "category": category,
            "input_tokens": context,
            "question": question,
            "ground_truth": answers,
            "original_token_count": original_token_count,
            "compression_budgets": compression_budgets,
            "split": "holdout",  # default, will be overridden for mini
        }
        
        all_examples.append(example)
    
    logger.info(f"  Loaded {len(ds)} examples for {task_name}")
    return all_examples


@logger.catch(reraise=True)
def create_splits(all_examples: list) -> tuple:
    """Create stratified mini-split (50 per task) and holdout split."""
    # Group by task_name
    by_task = {}
    for ex in all_examples:
        by_task.setdefault(ex["task_name"], []).append(ex)
    
    mini_examples = []
    holdout_examples = []
    
    for task_name, examples in by_task.items():
        random.shuffle(examples)
        mini = examples[:MINI_EXAMPLES_PER_TASK]
        holdout = examples[MINI_EXAMPLES_PER_TASK:]
        
        for ex in mini:
            ex["split"] = "mini"
        for ex in holdout:
            ex["split"] = "holdout"
        
        mini_examples.extend(mini)
        holdout_examples.extend(holdout)
        
        logger.info(f"  {task_name}: mini={len(mini)}, holdout={len(holdout)}")
    
    logger.info(f"Total mini: {len(mini_examples)}, holdout: {len(holdout_examples)}")
    return mini_examples, holdout_examples


@logger.catch(reraise=True)
def save_jsonl(examples: list, output_path: Path):
    """Save examples as JSONL."""
    with output_path.open("w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")
    logger.info(f"Saved {len(examples)} examples to {output_path}")


@logger.catch(reraise=True)
def main():
    # Load tokenizer
    logger.info("Loading LLaMA-3-8B tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
    logger.info(f"Tokenizer loaded: {tokenizer.__class__.__name__}")
    
    all_examples = []
    
    # Process all tasks
    for category, tasks in TASKS.items():
        for task_name in tasks:
            process_task(task_name, category, tokenizer, all_examples)
    
    logger.info(f"Total examples loaded: {len(all_examples)}")
    
    # Create splits
    random.seed(42)  # reproducible
    mini_examples, holdout_examples = create_splits(all_examples)
    
    # Save outputs
    save_jsonl(mini_examples, OUTPUT_DIR / "longbench_mini.jsonl")
    save_jsonl(holdout_examples, OUTPUT_DIR / "longbench_holdout.jsonl")
    save_jsonl(all_examples, OUTPUT_DIR / "longbench_full.jsonl")
    
    # Save metadata
    metadata = {
        "tasks": ALL_TASKS,
        "categories": TASKS,
        "mini_examples_per_task": MINI_EXAMPLES_PER_TASK,
        "compression_budgets": COMPRESSION_BUDGETS,
        "total_examples": len(all_examples),
        "mini_count": len(mini_examples),
        "holdout_count": len(holdout_examples),
        "tokenizer": "meta-llama/Meta-Llama-3-8B",
    }
    
    (OUTPUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))
    logger.info("Metadata saved")
    
    # Validation
    logger.info("Running validation...")
    for split_name, examples in [("mini", mini_examples), ("holdout", holdout_examples)]:
        for ex in examples:
            assert ex["input_tokens"], f"Empty input_tokens in {split_name}"
            assert ex["ground_truth"], f"Empty ground_truth in {split_name}"
            assert ex["original_token_count"] > 0, f"Zero token count in {split_name}"
            assert ex["split"] == split_name, f"Split mismatch in {split_name}"
        logger.info(f"  {split_name}: all validation checks passed")
    
    logger.success("Processing complete!")


if __name__ == "__main__":
    main()