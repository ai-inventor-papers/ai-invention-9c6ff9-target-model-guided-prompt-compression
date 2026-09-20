#!/usr/bin/env python3
"""Convert LongBench processed data to exp_sel_data_out.json schema."""

from loguru import logger
from pathlib import Path
import json
import sys

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/data_conversion.log", rotation="30 MB", level="DEBUG")


@logger.catch(reraise=True)
def load_processed_data(file_path: Path):
    """Load JSONL file."""
    examples = []
    with file_path.open() as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


@logger.catch(reraise=True)
def convert_to_schema(examples: list) -> dict:
    """Convert LongBench examples to exp_sel_data_out schema."""
    # Group by task_name
    from collections import defaultdict
    by_task = defaultdict(list)
    
    for ex in examples:
        by_task[ex["task_name"]].append(ex)
    
    datasets = []
    for task_name, task_examples in by_task.items():
        # Determine category from first example
        category = task_examples[0]["category"]
        
        schema_examples = []
        for idx, ex in enumerate(task_examples):
            # Build input: context + question
            input_text = f"{ex['input_tokens']}\n\n{ex['question']}"
            
            # Build output: ground truth answers (join if multiple)
            if isinstance(ex['ground_truth'], list):
                output_text = " | ".join(ex['ground_truth'])
            else:
                output_text = str(ex['ground_truth'])
            
            schema_ex = {
                "input": input_text,
                "output": output_text,
                "metadata_task_name": ex["task_name"],
                "metadata_category": category,
                "metadata_task_id": ex["task_id"],
                "metadata_original_token_count": ex["original_token_count"],
                "metadata_compression_budget_2x": ex["compression_budgets"]["2x"],
                "metadata_compression_budget_4x": ex["compression_budgets"]["4x"],
                "metadata_compression_budget_8x": ex["compression_budgets"]["8x"],
                "metadata_split": ex["split"],
                "metadata_row_index": idx,
            }
            schema_examples.append(schema_ex)
        
        datasets.append({
            "dataset": f"longbench_{task_name}",
            "examples": schema_examples
        })
        
        logger.info(f"  {task_name}: {len(schema_examples)} examples")
    
    return {
        "metadata": {
            "source": "LongBench (Xnhyacinth/LongBench on HuggingFace)",
            "tokenizer": "meta-llama/Meta-Llama-3-8B",
            "description": "Long-context benchmark for prompt compression evaluation",
            "compression_budgets": {"2x": 0.5, "4x": 0.25, "8x": 0.125},
        },
        "datasets": datasets
    }


@logger.catch(reraise=True)
def main():
    processed_dir = Path("processed_data")
    
    # Load all three splits
    logger.info("Loading processed data...")
    mini = load_processed_data(processed_dir / "longbench_mini.jsonl")
    holdout = load_processed_data(processed_dir / "longbench_holdout.jsonl")
    full = load_processed_data(processed_dir / "longbench_full.jsonl")
    
    logger.info(f"Loaded: mini={len(mini)}, holdout={len(holdout)}, full={len(full)}")
    
    # Convert each split
    for split_name, examples in [("mini", mini), ("holdout", holdout), ("full", full)]:
        logger.info(f"Converting {split_name} split...")
        output = convert_to_schema(examples)
        
        output_path = processed_dir / f"longbench_{split_name}_schema.json"
        output_path.write_text(json.dumps(output, indent=2))
        logger.info(f"Saved to {output_path}")
    
    # Also create combined full_data_out.json (using full split)
    logger.info("Creating full_data_out.json...")
    full_output = convert_to_schema(full)
    (processed_dir / "full_data_out.json").write_text(json.dumps(full_output, indent=2))
    logger.success("Conversion complete!")


if __name__ == "__main__":
    main()