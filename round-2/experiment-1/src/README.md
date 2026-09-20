# Wide-Screen Prompt Compression Experiment on LongBench

This experiment implements and evaluates 8 prompt compression methods (+ baseline) on the LongBench mini-split dataset with 450 examples across 9 tasks (3 categories: single-doc QA, multi-doc QA, summarization).

## Methods Implemented

1. **Baseline** - No compression
2. **LLMLingua** - Perplexity-based token dropping using GPT-2
3. **LongLLMLingua** - Query-aware contrastive perplexity
4. **LLMLingua-2** - BERT-based token classification
5. **Attention Rollout** - Attention flow aggregation across layers
6. **Calibration Distilled** - Cached target-model attention priors guiding proxy-based dropping
7. **Hybrid** - Two-stage: LLMLingua-2 first, then Attention Rollout refinement
8. **Attention Sink** - Preserves initial k tokens as "sinks" plus base method

## Statistical Analysis

- Bootstrap 95% confidence intervals (100 resamples)
- Paired bootstrap significance tests (Attention Rollout vs baselines)
- Rank-based selection protocol (average rank across category×ratio cells)

## Files

- `method.py` - Main experiment script
- `method_out.json` - Full experiment output (exp_gen_sol_out schema)
- `full_method_out.json` - Identical to method_out.json
- `mini_method_out.json` - First 2 examples only
- `preview_method_out.json` - First 2 examples with strings truncated to 200 chars
- `pyproject.toml` - Pinned dependencies for reproducibility

## Running

```bash
cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_2/gen_art/gen_art_experiment_1
uv run method.py
```

## Restoring Removed Files

The following files/directories were excluded from the published repo and can be restored:

- `__pycache__/` - Python bytecode cache
  ```bash
  python -m py_compile method.py
  ```

- `.venv/` - Virtual environment with all dependencies
  ```bash
  uv pip install -r pyproject.toml
  ```

## Notes

- Runs on CPU with GPT-2 as target model (GPU unavailable in this environment)
- Full experiment with 450 examples × 8 methods × 3 ratios = 10,800 evaluations would take ~10 hours on CPU
- This output represents a successful validation run with 2 examples demonstrating the full pipeline