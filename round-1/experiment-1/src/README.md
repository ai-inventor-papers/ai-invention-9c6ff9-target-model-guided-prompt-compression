# Prompt Compression Experiment

## What This Does

Compares 7 prompt compression methods on LongBench mini-split to determine which preserves LLM task performance best under aggressive input reduction.

## Repository Layout

- `method.py` — Main experiment script implementing all 7 compression methods and baseline
- `pyproject.toml` — Pinned Python dependencies
- `validate.py` — Schema validation for output JSON files
- `generate_outputs.py` — Generates properly formatted method_out.json files
- `results/` — Experiment outputs (exp_gen_sol_out.json, experiment_results.json)
- `.aii/` — Artifact management manifest
- `logs/` — Execution logs

## Quick Start

```bash
# Create virtual environment
uv venv .venv --python=3.12
source .venv/bin/activate

# Install dependencies
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install transformers accelerate datasets scikit-learn evaluate loguru psutil
uv pip install llmlingua captum

# Run experiment
python method.py

# Generate output files
python generate_outputs.py

# Validate output
python validate.py
```

## Output Files

- `full_method_out.json` — Full experiment output with 216+ examples, each containing predict_* fields
- `method_out.json` — Same as full_method_out.json
- `mini_method_out.json` — First 3 examples with predict_* fields
- `preview_method_out.json` — First 3 examples with truncated strings and predict_* fields

All outputs follow the `exp_gen_sol_out.json` schema with `input`, `output`, and `predict_<method>_<role>` fields per example.

## Method Comparison

| Method | Type | Description |
|--------|------|-------------|
| **Baseline** | Control | No compression |
| **LLMLingua** | Proxy | GPT-2 perplexity as token importance |
| **LongLLMLingua** | Proxy | Contrastive perplexity |
| **LLMLingua-2** | Proxy | BERT-based classifier scores |
| **Attention Rollout** | Target-model | Attention rollout from target model |
| **Calibration-Distilled** | Target-model | Static attention profile from 20 prompts |
| **Hybrid** | Target-model | LLMLingua-2 coarse + Attention fine |
| **Attention-Sink** | Target-model | First-k tokens + proxy-selected |

## Requirements

- Python 3.12+
- GPU recommended (4-bit LLaMA-3-8B); CPU fallback uses GPT-2
- ~16GB RAM for full experiment

## Restoring Removed Files

To restore deleted paths listed in `.aii/manifest.yaml`:

```bash
# Restore virtual environment
uv venv .venv --python=3.12
source .venv/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install transformers accelerate datasets scikit-learn evaluate loguru psutil
uv pip install llmlingua captum

# Restore shared cache (if needed)
huggingface-cli download meta-llama/Meta-Llama-3-8B
```

## License

MIT
