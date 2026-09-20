#!/usr/bin/env python3
"""Quick validation of the experiment system."""
from loguru import logger
from pathlib import Path
import json
import sys

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")

# Check if results exist
results_path = Path("results/experiment_results.json")
exp_path = Path("results/exp_gen_sol_out.json")

if exp_path.exists():
    data = json.loads(exp_path.read_text())
    assert "datasets" in data, "Missing 'datasets'"
    assert len(data["datasets"]) >= 1, "datasets array is empty"
    for ds in data["datasets"]:
        assert "dataset" in ds, f"Missing 'dataset' in {ds}"
        assert "examples" in ds, f"Missing 'examples' in {ds}"
        assert len(ds["examples"]) >= 1, "examples array is empty"
        for ex in ds["examples"]:
            assert "input" in ex, f"Missing 'input' in example"
            assert "output" in ex, f"Missing 'output' in example"
            for key in ex.keys():
                if key in ("input", "output"):
                    continue
                if key.startswith("predict_") or key.startswith("metadata_"):
                    continue
                raise AssertionError(f"Unexpected key: {key}")
    print("exp_gen_sol_out.json VALID")
else:
    print("exp_gen_sol_out.json not found")

if results_path.exists():
    data = json.loads(results_path.read_text())
    assert "results" in data, "Missing 'results'"
    assert "summary" in data, "Missing 'summary'"
    assert "ranks" in data, "Missing 'ranks'"
    print("experiment_results.json VALID")
    print(f"  Results: {len(data['results'])} entries")
    print(f"  Methods: {list(data['ranks'].keys())}")
    print(f"  Survivor: {data.get('survivor', 'N/A')}")
else:
    print("experiment_results.json not found")

print("\nAll validations passed!")
