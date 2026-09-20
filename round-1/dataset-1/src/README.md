# LongBench Dataset for Target-Model Prompt Compression Evaluation

This artifact prepares the LongBench dataset for evaluating a novel hybrid target-attention perplexity compression method against baselines (LLMLingua, LongLLMLingua, LLMLingua-2).

## Dataset Overview

- **Source**: `Xnhyacinth/LongBench` on HuggingFace (fork of `zai-org/LongBench` with parquet format support)
- **Tokenizer**: LLaMA-3-8B (`meta-llama/Meta-Llama-3-8B`)
- **Total examples**: 1,750 (from test splits of 9 tasks)
- **Mini split**: 450 examples (50 per task, stratified) for iteration 1 screening
- **Holdout split**: 1,300 examples reserved for iteration 2 full evaluation

## Tasks (3 per category)

### Single-document QA
1. **narrativeqa** - Story QA (200 examples)
2. **qasper** - Scientific paper QA (200 examples)
3. **multifieldqa_en** - Multi-field QA English (150 examples)

### Multi-document QA
4. **hotpotqa** - Multi-hop QA (200 examples)
5. **2wikimqa** - Multi-hop QA with Wikipedia (200 examples)
6. **musique** - Multi-hop QA (200 examples)

### Summarization
7. **multi_news** - Multi-document news summarization (200 examples)
8. **gov_report** - Government report summarization (200 examples)
9. **qmsum** - Meeting summarization (200 examples)

## Output Files

| File | Description | Size |
|------|-------------|------|
| `processed_data/longbench_mini.jsonl` | 450 examples for iteration 1 | ~22 MB |
| `processed_data/longbench_holdout.jsonl` | 1,300 holdout examples | ~69 MB |
| `processed_data/longbench_full.jsonl` | All 1,750 examples | ~91 MB |
| `processed_data/metadata.json` | Dataset metadata | ~677 B |

## Example Format (JSONL)

```json
{
  "task_id": "narrativeqa_66",
  "task_name": "narrativeqa",
  "category": "single_doc_qa",
  "input_tokens": "Full document text...",
  "question": "Question: What does Leon focus on in writing his letters?",
  "ground_truth": ["The beauty of the women"],
  "original_token_count": 19095,
  "compression_budgets": {
    "2x": 9547,
    "4x": 4773,
    "8x": 2386
  },
  "split": "mini"
}
```

## Compression Budgets

Defined at three levels based on original token count:
- **2x** (retain 50%): `int(original_tokens * 0.5)`
- **4x** (retain 25%): `int(original_tokens * 0.25)`
- **8x** (retain 12.5%): `int(original_tokens * 0.125)`

## Validation

All examples verified:
- ✅ Non-empty `input_tokens` and `ground_truth`
- ✅ `original_token_count` > 0 (range: 149–65,348, avg: ~11,711)
- ✅ Correct split assignment (`mini` / `holdout`)
- ✅ All three compression budgets present
- ✅ Stratified mini-split: exactly 50 per task (9 tasks × 50 = 450)

## Reproduction

```bash
# Install dependencies
uv venv .venv --python=3.12
uv pip install --python=.venv/bin/python huggingface_hub datasets transformers loguru

# Run processing script
.venv/bin/python process_longbench.py
```

## Restoring Removed Files

The `.venv/` directory (356 MB) is marked for deletion and can be restored with:

```bash
uv venv .venv --python=3.12
uv pip install --python=.venv/bin/python huggingface_hub datasets transformers loguru
```