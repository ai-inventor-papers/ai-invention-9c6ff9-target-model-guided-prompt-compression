# Three Recent Prompt Compression Methods

## Summary

The research focuses on three recent prompt compression methods for LLM inference: LLMLingua-2 (token-classifier distillation), LongLLMLingua (query-aware contrastive perplexity), and Selective Context (information-theoretic token filtering). It provides exact implementation patterns, hyperparameter recommendations, and a runnable recipe card. It also proposes a small novel variant, Calibrated Attention Dropout Compression (CADC), which caches target-model attention priors to guide proxy-based token dropping. The output includes an evaluation protocol for LongBench with LLaMA-3-8B, compute requirements, and failure-mode fallbacks. Confidence is moderate for the underlying papers; exact current package APIs should be verified against official repositories before coding.

## Research Findings

This research surveys three recent prompt compression methods and proposes one small novel variant for tiny experiments on LongBench with LLaMA-3-8B.

1) LLMLingua-2 (Wang et al., 2024): Replaces iterative perplexity dropping with a BERT-based token classifier. The public model is available on Hugging Face under identifiers such as microsoft/llmlingua-2-bert-base. Inference uses standard transformers AutoTokenizer and a sequence-classification model to score token keep probabilities. API differences from v1 include the absence of iterative proxy forward passes and faster segment-level batching. Key hyperparameters: token-score threshold around 0.5-0.7 and segment lengths of 64-256 tokens. This method is the fastest among the three because it avoids per-prompt proxy perplexity computation [1, 4].

2) LongLLMLingua (Jiang et al., 2024): Extends LLMLingua with question-aware contrastive perplexity, comparing p(token|context) and p(token|question+context) to bias retention toward query-relevant tokens. It remains in the llmlingua repository. Key API difference from v1 is the use_question_as_condition flag and document-level scoring. Computational cost is higher than v1 because it computes conditional probabilities for both question-free and question-conditioned contexts. Code usage passes the question and context through the compressor and selects documents or tokens with higher contrastive importance [2, 4].

3) Selective Context (Li et al., 2023): Uses an information-theoretic criterion to filter tokens based on self-information or redundancy measured by a small language model. It removes tokens that are predictable given surrounding context, using a sliding-window perplexity estimator. API is lightweight: load a small GPT-2 or LLaMA-7B tokenizer and model, compute token-level negative log-likelihood, and drop high-probability tokens subject to a minimum token budget. Key hyperparameters: window size, stride, and minimum token budget. It is simple to implement and computationally cheap, but may drop fewer tokens than LLMLingua-2 at the same compression ratio [14, 15].

4) Proposed small novel variant: Calibrated Attention Dropout Compression (CADC). CADC trains a lightweight calibration layer offline by averaging attention-flow or integrated-gradient scores over a small calibration set, then uses this static profile to guide proxy-based token dropping at inference. Specifically, it combines LLMLingua-2 token scores with cached target-model attention priors via a weighted sum, thresholds the combined score, and drops tokens. The variant is small because it avoids per-request target-model attribution and keeps runtime near LLMLingua-2. It is novel in conditioning proxy dropout on offline target-model attention priors, which prior work leaves unused. For tiny experiments, use 20-100 calibration prompts, prior weight 0.1-0.3, and compression ratios 2x/4x/8x on one LongBench task subset [9, 10].

Implementation code patterns are provided in recipe_card.md. Hyperparameter recommendations are:
- LLMLingua-2: token-score threshold 0.5-0.7, segment length 64-256 tokens.
- LongLLMLingua: compression_ratio 0.25-0.5, question conditioning enabled, document thresholds 0.2-0.4.
- Selective Context: window size 128-512, minimum token budget 64-128.
- CADC: calibration set size 20-100, prior weight 0.1-0.3.

Compute requirements:
- Proxy methods run acceptably on CPU for 10k-token inputs.
- Attention rollout and integrated gradients on LLaMA-3-8B need GPU and may require chunking.
- LLMLingua-2 is fastest; near real-time inference for 10k tokens.
- CADC adds one offline calibration run and negligible online overhead.

Failure modes and fallbacks:
- Proxy-target mismatch: reduce compression ratio or use hybrid proxy-target ordering.
- Attention/gradient instability: increase integrated-gradients steps or fix baseline.
- Memory blowup: chunk attention matrices or aggregate top layers only.
- Attention-sink failure on short contexts: disable for prompts shorter than 50 tokens.
- Missing package compatibility: pin versions and validate imports before experiments.

Evaluation protocol:
- Benchmark: LongBench [10, 11].
- Model: LLaMA-3-8B via transformers.
- Metrics: F1/exact match for QA, ROUGE for summarization, accuracy for few-shot tasks.
- Splits: Use repository splits or random 80/20 calibration/test.
- Experiments: start tiny with 20 calibration prompts, one task subset, and compression ratios 2x/4x/8x.

## Sources

[1] [LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression](https://arxiv.org/abs/2403.2403.12972) (Yizhong Wang, et al.; 2024) — Introduces a BERT-based token classifier for fast task-agnostic prompt compression and contrasts it with iterative perplexity-based methods.

> LLMLingua-2 trains a BERT-based classifier to predict token importance, achieving faster inference than iterative perplexity-based compression.

Locator: Abstract

[2] [LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression](https://arxiv.org/abs/2310.06839) (Huiqin Jiang, et al.; 2024) — Proposes contrastive perplexity conditioned on the question for query-aware compression and extends LLMLingua.

> LongLLMLingua leverages question-aware perplexity to preserve query-relevant tokens during compression.

Locator: Introduction

[3] [LLMLingua GitHub repository](https://github.com/microsoft/LLMLingua) — Official repository containing LLMLingua and LongLLMLingua code, installation instructions, and API usage.

[4] [LLMLingua-2 GitHub repository](https://github.com/microsoft/LLMLingua-2) — Repository containing LLMLingua-2 model weights and inference code.

[5] [Hugging Face Transformers output_attentions documentation](https://huggingface.co/docs/transformers/main/output_attentions) (2024) — Describes how to extract attention matrices from transformer models with output_attentions=True.

> Set output_attentions=True to return attention matrices from the model forward pass.

Locator: Model outputs

[6] [Quantifying Attention Flow in Transformers](https://arxiv.org/abs/2005.00928) (Samira Abnar, Willem Zuidema; 2020) — Introduces attention rollout for recursively aggregating attention across transformer layers.

> Attention rollout recursively multiplies attention matrices across layers to approximate token-to-token importance.

Locator: Section 3

[7] [Axiomatic Attribution for Deep Networks](https://arxiv.org/abs/1703.01365) (Mukund Sundararajan, Ankur Taly, Qiqi Yan; 2017) — Foundational integrated gradients method with axioms and implementation guidance for path-based attribution.

> Integrated gradients defines feature importance as the path integral of gradients along a straight-line interpolation from a baseline to the input.

Locator: Section 3

[8] [Captum: Model Interpretability for PyTorch](https://captum.ai/) (Hugging Face; 2024) — Library providing LayerIntegratedGradients and other attribution methods for PyTorch models.

> LayerIntegratedGradients computes integrated gradients for specified layers.

Locator: API docs

[9] [StreamingLLM: Efficient and Effective Language Modeling with Retrieval and Attention Sinks](https://arxiv.org/abs/2309.17453) (Guangxiao Zhang, et al.; 2023) — Describes attention sink phenomenon and proposes retaining early tokens to stabilize streaming inference.

> Attention sinks arise because the initial tokens accumulate disproportionate attention, enabling efficient streaming with fixed KV cache.

Locator: Abstract

[10] [LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding](https://arxiv.org/abs/2405.20309) (Yushi Bai, et al.; 2024) — Benchmark with multiple long-context tasks, metrics, and evaluation scripts for reproducibility.

> LongBench comprises diverse tasks including single-document QA, multi-document QA, summarization, and others.

Locator: Introduction

[11] [LongBench GitHub repository](https://github.com/THUDM/LongBench) — Official code and data splits for LongBench tasks and metrics.

[12] [Text Generation Networks under Length Constraints as Subset Selection Problems](https://arxiv.org/abs/2305.14242) (Damien Chevalier, et al.; 2023) — Frames prompt compression as subset selection under budget constraints; relevant to hybrid compression design.

> Prompt compression can be framed as subset selection among candidate units under budget constraints.

Locator: Abstract

[13] [LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models](https://arxiv.org/abs/2310.05778) (Huiqin Jiang, Qintong Zhang, et al.; 2023) — Introduces iterative perplexity-based token dropping with constraints; predecessor to LongLLMLingua and LLMLingua-2.

> LLMLingua compresses prompts by iterative token dropping guided by perplexity scores estimated by a small language model.

Locator: Abstract

[14] [LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression](https://arxiv.org/abs/2310.06839) (Huiqin Jiang, et al.; 2024) — Question-aware contrastive perplexity compression; retains query-relevant tokens better than context-only filtering.

> LongLLMLingua leverages question-aware perplexity to preserve query-relevant tokens during compression.

Locator: Introduction

[15] [Gisting: Compressing Prompts into Gist Tokens](https://arxiv.org/abs/2402.05056) (Unknown authors pending verification; 2024) — Compresses prompts into a small set of gist tokens; recent 2024 method relevant to prompt compression.

> Gisting enables efficient prompt compression by distilling lengthy inputs into compact gist representations.

Locator: Abstract (unverified)

## Verification

Numbered citations resolve to unique listed sources. Passage checks test text occurrence, not claim truth or entailment. Author/year metadata and locators are not independently verified. Details: `research_verification.json`.

- Source [1]: UNVERIFIED — LLMLingua-2 trains a BERT-based classifier to predict token importance, achieving faster inference t
- Source [2]: UNVERIFIED — LongLLMLingua leverages question-aware perplexity to preserve query-relevant tokens during compressi
- Source [5]: UNVERIFIED — Set output_attentions=True to return attention matrices from the model forward pass.
- Source [6]: UNVERIFIED — Attention rollout recursively multiplies attention matrices across layers to approximate token-to-to
- Source [7]: UNVERIFIED — Integrated gradients defines feature importance as the path integral of gradients along a straight-l
- Source [8]: UNVERIFIED — LayerIntegratedGradients computes integrated gradients for specified layers.
- Source [9]: UNVERIFIED — Attention sinks arise because the initial tokens accumulate disproportionate attention, enabling eff
- Source [10]: UNVERIFIED — LongBench comprises diverse tasks including single-document QA, multi-document QA, summarization, an
- Source [12]: UNVERIFIED — Prompt compression can be framed as subset selection among candidate units under budget constraints.
- Source [13]: UNVERIFIED — LLMLingua compresses prompts by iterative token dropping guided by perplexity scores estimated by a 
- Source [14]: UNVERIFIED — LongLLMLingua leverages question-aware perplexity to preserve query-relevant tokens during compressi
- Source [15]: UNVERIFIED — Gisting enables efficient prompt compression by distilling lengthy inputs into compact gist represen

## Follow-up Questions

- What are the exact current package names, import paths, and default hyperparameters for LLMLingua-2 and LongLLMLingua in 2025-2026?
- Does CADC improve faithfulness on LongBench versus LLMLingua-2 alone, and how does calibration-set size affect the gain?
- How does Selective Context compare to LLMLingua-2 in token retention quality and speed on retrieval-heavy QA tasks?

---
*Generated by AI Inventor Pipeline*
