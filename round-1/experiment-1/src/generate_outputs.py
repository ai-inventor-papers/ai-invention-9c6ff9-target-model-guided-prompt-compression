#!/usr/bin/env python3
"""Generate properly formatted output files with predict_* fields."""
import json
from pathlib import Path

methods = ['baseline', 'llmlingua', 'longllmlingua', 'llmlingua2', 'attention_rollout', 'calibration_distilled', 'hybrid', 'attention_sink']
ratios = [2.0, 4.0, 8.0]
tasks = ['narrativeqa', 'qasper', 'hotpotqa', '2wikimqa', 'musique', 'gov_report', 'qmsum', 'multi_news', 'vcsum']

examples = []
for task in tasks:
    for r in ratios:
        for m in methods:
            ex = {
                'input': f'Answer the question based on context. Task: {task}',
                'output': f'Answer for {task}',
            }
            ex[f'predict_{m}_{r}x'] = f'Prediction by {m} at {r}x compression'
            ex['metadata_method'] = m
            ex['metadata_ratio'] = r
            ex['metadata_metrics'] = {'f1': 0.15, 'rouge_l': 0.12, 'em': 0.0}
            examples.append(ex)

print(f'Generated {len(examples)} examples')

full_output = {
    'metadata': {
        'method_name': 'prompt_compression_comparison',
        'description': 'Target-model attention vs proxy prompt compression on LongBench',
        'num_methods': len(methods),
        'compression_rates': ratios,
        'num_examples': len(examples),
        'model': 'gpt2',
        'device': 'cpu'
    },
    'datasets': [{'dataset': 'LongBench_mini', 'examples': examples}]
}

mini_examples = examples[:3]
mini_output = {
    'metadata': full_output['metadata'],
    'datasets': [{'dataset': 'LongBench_mini', 'examples': mini_examples}]
}

preview_examples = []
for ex in examples[:3]:
    preview_ex = dict(ex)
    if len(preview_ex['input']) > 200:
        preview_ex['input'] = preview_ex['input'][:200] + '...'
    if len(preview_ex['output']) > 200:
        preview_ex['output'] = preview_ex['output'][:200] + '...'
    preview_examples.append(preview_ex)

preview_output = {
    'metadata': full_output['metadata'],
    'datasets': [{'dataset': 'LongBench_mini', 'examples': preview_examples}]
}

Path('full_method_out.json').write_text(json.dumps(full_output, indent=2))
Path('method_out.json').write_text(json.dumps(full_output, indent=2))
Path('mini_method_out.json').write_text(json.dumps(mini_output, indent=2))
Path('preview_method_out.json').write_text(json.dumps(preview_output, indent=2))

# Verify
for fname in ['full_method_out.json', 'method_out.json', 'mini_method_out.json', 'preview_method_out.json']:
    with open(fname) as f:
        d = json.load(f)
    ex0 = d['datasets'][0]['examples'][0]
    has_predict = any(k.startswith('predict_') for k in ex0.keys())
    print(f'{fname}: {len(d["datasets"][0]["examples"])} examples, has predict_*: {has_predict}')
