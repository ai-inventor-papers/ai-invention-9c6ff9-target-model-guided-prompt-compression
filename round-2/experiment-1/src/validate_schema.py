#!/usr/bin/env python3
"""
Quick schema validation
"""
import json
from jsonschema import validate

# Load schema
with open('/home/adrian/projects/ai-inventor-wt-integ/.claude/skills/aii-json/schemas/exp_gen_sol_out.json') as f:
    schema = json.load(f)

# Load output
with open('/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_2/gen_art/gen_art_experiment_1/method_out.json') as f:
    data = json.load(f)

try:
    validate(instance=data, schema=schema)
    print("Validation PASSED")
except Exception as e:
    print(f"Validation FAILED: {e}")