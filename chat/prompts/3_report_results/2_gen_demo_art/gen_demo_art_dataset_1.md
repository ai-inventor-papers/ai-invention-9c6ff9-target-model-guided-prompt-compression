# gen_demo_art_dataset_1 — report_results

> Phase: `gen_paper_repo` · `gen_demo_art`
> Run: `run_8az8NIQ1qgmY` — Target-Model-Guided Prompt Compression via Attention Saliency
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_demo_art_dataset_1` (sdk_openhands_agent)

### [1] SYSTEM-USER prompt · 2026-09-21 00:53:12 UTC

````
<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<task>
Convert this artifact's Python script into a demo notebook with MINIMAL changes to the original code.
Split into cells, add markdown explanations between sections, add a visualization cell at the end.
Output: mini_demo_data.json + code_demo.ipynb (notebook that loads data from GitHub URL)
</task>

<artifact_info>
id: art_5_Iw7LOgL61k
type: dataset
title: LongBench Dataset for Prompt Compression Evaluation
summary: >-
  This artifact downloads LongBench from HuggingFace (Xnhyacinth/LongBench fork), selects 9 representative tasks (3 per category:
  narrativeqa, qasper, multifieldqa_en for single-doc QA; hotpotqa, 2wikimqa, musique for multi-doc QA; multi_news, gov_report,
  qmsum for summarization), tokenizes all documents with LLaMA-3-8B tokenizer to compute original token counts, defines compression
  budgets (2x=50%, 4x=25%, 8x=12.5% retention), and creates stratified splits: 450 examples (50/task) for iteration 1 mini-split
  and 1300 holdout examples for iteration 2. Output is formatted to exp_sel_data_out.json schema with 9 dataset groups and
  1750 total examples, each containing input (context+question), output (ground truth), and metadata fields (task_name, category,
  original_token_count, compression budgets, split assignment). Schema validation passes. File size 88MB (under 100MB limit).
  Includes pyproject.toml with pinned dependencies for reproducibility.
workspace_path: >-
  /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_1/gen_art/gen_art_dataset_1
out_expected_files:
- data.py
- full_data_out.json
- preview_data_out.json
- mini_data_out.json
out_demo_files:
- path: data.py
  description: Dataset fetching/generation script
</artifact_info>

<github_repo>
Repo URL: https://github.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression
Raw data URL: https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression/main/round-1/dataset-1/demo/mini_demo_data.json

URLs won't work yet — files pushed to GitHub AFTER notebook creation.
Use local fallback pattern so notebook works locally (now) and in Colab (after deployment).
</github_repo>

<data_file_sizes>
Data files come in three sizes:
- preview_*_out.json — READ THIS to inspect the data structure
- mini_*_out.json (~3 examples) — use for prototyping/testing
- full_*_out.json (complete) — use for the final production run. NEVER open it directly (too large to read into context). Instead, extract values programmatically with shell commands (e.g. grep) or a Python script (use aii-long-running-tasks skill for scripts).
</data_file_sizes>

<install_dependencies_pattern>
Follow the aii-colab skill exactly. It has the install cell pattern, pre-installed package list, numpy 2.0 compat shims, and all Colab-specific rules.
</install_dependencies_pattern>

<data_loading_pattern>
`mini_demo_data.json` = curated subset for the demo.
Use this pattern for Colab compatibility (GitHub URL with local fallback):
```python
GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression/main/round-1/dataset-1/demo/mini_demo_data.json"
import json
from pathlib import Path

def load_data():
    try:
        import urllib.request
        with urllib.request.urlopen(GITHUB_DATA_URL) as response:
            return json.loads(response.read().decode())
    except Exception: pass
    local = Path("mini_demo_data.json")
    if local.exists(): return json.loads(local.read_text())
    raise FileNotFoundError("Could not load mini_demo_data.json")
```
</data_loading_pattern>

<notebook_structure>
--- Setup ---
Cell 1 (markdown): Title, description, what this artifact does.
Cell 2 (code): Install dependencies — follow the aii-colab skill's install cell pattern exactly. Fill in all packages imported by the artifact's code.
Cell 3 (code): Imports — copy original import block as-is, plus any additional imports needed for the notebook (e.g. matplotlib for visualization).
Cell 4 (code): Data loading helper — use the <data_loading_pattern> above.
Cell 5 (code): `data = load_data()`

--- Config ---
Config cell (code): Define ALL tunable parameters (iterations, epochs, n_samples, hidden_size, etc.) as variables at the top of this cell. Start with the ABSOLUTE MINIMUM values — the smallest that produce any output at all (e.g. 1 iteration, 2 samples, smallest array size). These get gradually increased during testing — see TODOs.

--- Processing ---
Remaining cells: One code cell per logical section of the original script. Add a markdown cell BEFORE each code cell. Copy code as closely as possible, with these changes:
  1. Replace file paths to use the loaded `data` variable.
  2. Use the config variables from the config cell (NOT hardcoded values).
  3. Minimal fixes are allowed if something doesn't work in notebook context (e.g. adjusting paths, removing CLI args, fixing imports), but keep changes to the absolute minimum.

--- Results ---
Visualization cell (code): Print key results in a readable table, plot numeric data with matplotlib if appropriate.
</notebook_structure>

<priority>
WORKING > OPTIMIZED. A small-scale demo that runs correctly is the goal. Once the notebook passes with minimum config values, scale up only if time permits — do NOT spend multiple retries chasing larger parameters. If a working version exists, finish and move on.
</priority>

<max_notebook_total_runtime>600s (10 min)</max_notebook_total_runtime>

<test_environment>
To test-run the notebook in a clean environment (simulating Colab), create a disposable `.nb_env` in your workspace:
```bash
/usr/bin/python3.12 -m venv .nb_env
.nb_env/bin/pip install -q pip jupyter ipykernel
.nb_env/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 code_demo.ipynb --output code_demo.ipynb
rm -rf .nb_env
```
The timeout is set to <max_notebook_total_runtime>. The entire notebook must finish within this time.

What happens: the .venv starts empty (just jupyter). When the notebook's install cell runs, `google.colab` is NOT in sys.modules, so ALL packages get installed — non-Colab packages unconditionally, and Colab packages (numpy, pandas, etc.) at Colab's exact versions via the guard block. The result mirrors Colab's environment as closely as possible. If a cell fails, fix the notebook and re-run.
</test_environment>

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.


<todos>
TODO 1. Read and STRICTLY follow these skills: aii-colab, aii-long-running-tasks.
TODO 2. Read demo file and relevant preview_* files (preview only). Understand script structure: imports, setup, processing, output. Identify ALL tunable parameters (iterations, epochs, n_samples, hidden_size, batch_size, etc.) — these go in the config cell.
TODO 3. Create `mini_demo_data.json`: curated subset from at most ONE dataset (no more than 100 diverse examples). CRITICAL: do NOT read/grep full output file — may crash. Use `head -c 5000` or stream first entries with Python to pick examples.
TODO 4. Create `code_demo.ipynb` via NotebookEdit following <notebook_structure>. Set ALL config parameters to ABSOLUTE MINIMUM values — the smallest that produce any output (e.g. 1 iteration, 2 samples, smallest array sizes). Test-run using <test_environment>. Fix all errors until it passes.
TODO 5. GRADUALLY SCALE (but don't overdo it): increase config params step by step (e.g. ~2x each round). After each increase: test-run, record runtime, fix errors. STOP SCALING as soon as results look meaningful — a working small-scale demo beats a failed large-scale one. If full original params fit within <max_notebook_total_runtime> (10% margin), use them. Otherwise keep whatever works and comment out the true original values. Do NOT spend more than 2-3 scaling rounds.
TODO 6. Verify: (1) code_demo.ipynb contains GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression/main/round-1/dataset-1/demo/mini_demo_data.json" exactly, (2) mini_demo_data.json exists, (3) uses GitHub URL pattern not just open('mini_demo_data.json').
</todos>

---

Output the result as JSON to: `/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k/.sdk_openhands_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "DemoExpectedFiles": {
      "description": "Expected output files from code demo notebook generation.",
      "properties": {
        "notebook": {
          "default": "",
          "description": "Path to the generated demo notebook. Example: 'code_demo.ipynb'",
          "title": "Notebook",
          "type": "string"
        },
        "mini_data_file": {
          "default": "",
          "description": "Path to the mini demo data JSON (curated subset). Example: 'mini_demo_data.json'",
          "title": "Mini Data File",
          "type": "string"
        }
      },
      "title": "DemoExpectedFiles",
      "type": "object"
    }
  },
  "description": "Dataset/experiment/evaluation \u2192 Jupyter notebook demo.\n\nTitle and summary come from the parent artifact (gen_art step),\nnot from the demo agent. The agent only outputs expected files.",
  "properties": {
    "out_expected_files": {
      "$ref": "#/$defs/DemoExpectedFiles",
      "description": "All output files you created. Must include the demo notebook."
    }
  },
  "required": [],
  "title": "CodeDemo",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k/.sdk_openhands_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-09-21 00:53:12 UTC

```
Survey three recent methods for prompt compression in LLM inference and propose one small novel variant; keep experiments tiny.
```

### [3] SYSTEM-USER prompt · 2026-09-21 01:23:33 UTC

````
YOUR PREVIOUS SESSION WAS INTERRUPTED: A single operation exceeded the 1800s message timeout. Each individual operation must complete within 1800s. Do NOT mock, skip, or compromise your execution — still do the real work. Try to make operations run faster if possible. If a command genuinely takes longer than 1800s, split it into sequential parts that each complete within the time limit.

Last messages before interruption:
  - [agent_think]: Let me create the build script and run it in a single command.
  - [agent_response]: Your last response did not include a function call or a message. Please use a tool to proceed with the task.
  - [agent_think]: Let me run the commands sequentially to build the notebook and then test it.
  - [agent_tool_call] terminal: Tool: terminal
{
  "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && cat > build_notebook.py << 'PYEOF'\nimport json\n\n# Build the notebook as a Python dict, then seria
  - [agent_tool_result] terminal: Tool: terminal
Result:
{"content": [{"cache_prompt": false, "type": "text", "text": ""}], "is_error": false, "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && cat > buil
  - [agent_think]: Now let me run the build script.
  - [agent_tool_call] terminal: Tool: terminal
{
  "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && python3 build_notebook.py",
  "is_input": false,
  "timeout": null,
  "reset": false
}
  - [agent_tool_result] terminal: Tool: terminal
Result:
python3: can't open file '/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k/build_notebook.py': [Errno 2] No such file or directory
  - [agent_think]: The file wasn't created properly. Let me check the current directory and try again.
  - [agent_tool_call] terminal: Tool: terminal
{
  "command": "ls -la /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k/",
  "is_input": false,
  "timeout": null,
  "reset": false
}
  - [agent_tool_result] terminal: Tool: terminal
Result:
total 48
drwxrwxr-x 3 adrian adrian  4096 Sep 21 02:57 .
drwxrwxr-x 4 adrian adrian  4096 Sep 21 02:53 ..
drwxrwxr-x 7 adrian adrian  4096 Sep 21 02:57 .nb_env
-rw------- 1 adrian adrian 17182 Sep 21 02:57 code_demo.ipynb
-rw------- 1 adrian adrian 14638 Sep 21 02:56 mini_demo
  - [agent_think]: The build_notebook.py wasn't created. Let me try writing it differently - maybe the heredoc didn't work properly. Let me use a Python script instead
  - [agent_tool_call] terminal: Tool: terminal
{
  "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && python3 -c \"\nimport json\n\n# Build the notebook as a Python dict, then serialize to JSON\ncells =
  - [agent_tool_result] terminal: Tool: terminal
Result:
{"content": [{"cache_prompt": false, "type": "text", "text": ""}], "is_error": false, "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && python3 -c
  - [agent_think]: The notebook was built successfully. Now let me validate it and test run it.
  - [agent_tool_call] terminal: Tool: terminal
{
  "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && python3 -c \"\nimport json\nwith open('code_demo.ipynb', 'r') as f:\n    content = f.read()\ntry:\n 
  - [agent_tool_result] terminal: Tool: terminal
Result:
JSON error at line 292, col 5: Expecting value
  - [agent_think]: The JSON is still invalid. There's something wrong with the file writing. Let me check what's happening by looking at the raw content of the file.
  - [agent_tool_call] terminal: Tool: terminal
{
  "command": "cd /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k && python3 -c \"\nwith open('code_demo.ipynb', 'r') as f:\n    content = f.read()\nlines = content.spli
  - [agent_tool_result] terminal: Tool: terminal
Result:
289: '    "# Plot 1: Token count distribution by category\\n",'
 290: '    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\\n",'
 291: '    "\\n",'
 292: '    # Box plot by category\\n",'
 293: '    "df.boxplot(column=\\"tokens\\", by=\\"category\\", ax=axes[0])\\n",'
 294: '

CONTINUE FOLLOWING THESE INSTRUCTIONS:

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<task>
Convert this artifact's Python script into a demo notebook with MINIMAL changes to the original code.
Split into cells, add markdown explanations between sections, add a visualization cell at the end.
Output: mini_demo_data.json + code_demo.ipynb (notebook that loads data from GitHub URL)
</task>

<artifact_info>
id: art_5_Iw7LOgL61k
type: dataset
title: LongBench Dataset for Prompt Compression Evaluation
summary: >-
  This artifact downloads LongBench from HuggingFace (Xnhyacinth/LongBench fork), selects 9 representative tasks (3 per category:
  narrativeqa, qasper, multifieldqa_en for single-doc QA; hotpotqa, 2wikimqa, musique for multi-doc QA; multi_news, gov_report,
  qmsum for summarization), tokenizes all documents with LLaMA-3-8B tokenizer to compute original token counts, defines compression
  budgets (2x=50%, 4x=25%, 8x=12.5% retention), and creates stratified splits: 450 examples (50/task) for iteration 1 mini-split
  and 1300 holdout examples for iteration 2. Output is formatted to exp_sel_data_out.json schema with 9 dataset groups and
  1750 total examples, each containing input (context+question), output (ground truth), and metadata fields (task_name, category,
  original_token_count, compression budgets, split assignment). Schema validation passes. File size 88MB (under 100MB limit).
  Includes pyproject.toml with pinned dependencies for reproducibility.
workspace_path: >-
  /home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_1/gen_art/gen_art_dataset_1
out_expected_files:
- data.py
- full_data_out.json
- preview_data_out.json
- mini_data_out.json
out_demo_files:
- path: data.py
  description: Dataset fetching/generation script
</artifact_info>

<github_repo>
Repo URL: https://github.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression
Raw data URL: https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression/main/round-1/dataset-1/demo/mini_demo_data.json

URLs won't work yet — files pushed to GitHub AFTER notebook creation.
Use local fallback pattern so notebook works locally (now) and in Colab (after deployment).
</github_repo>

<data_file_sizes>
Data files come in three sizes:
- preview_*_out.json — READ THIS to inspect the data structure
- mini_*_out.json (~3 examples) — use for prototyping/testing
- full_*_out.json (complete) — use for the final production run. NEVER open it directly (too large to read into context). Instead, extract values programmatically with shell commands (e.g. grep) or a Python script (use aii-long-running-tasks skill for scripts).
</data_file_sizes>

<install_dependencies_pattern>
Follow the aii-colab skill exactly. It has the install cell pattern, pre-installed package list, numpy 2.0 compat shims, and all Colab-specific rules.
</install_dependencies_pattern>

<data_loading_pattern>
`mini_demo_data.json` = curated subset for the demo.
Use this pattern for Colab compatibility (GitHub URL with local fallback):
```python
GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression/main/round-1/dataset-1/demo/mini_demo_data.json"
import json
from pathlib import Path

def load_data():
    try:
        import urllib.request
        with urllib.request.urlopen(GITHUB_DATA_URL) as response:
            return json.loads(response.read().decode())
    except Exception: pass
    local = Path("mini_demo_data.json")
    if local.exists(): return json.loads(local.read_text())
    raise FileNotFoundError("Could not load mini_demo_data.json")
```
</data_loading_pattern>

<notebook_structure>
--- Setup ---
Cell 1 (markdown): Title, description, what this artifact does.
Cell 2 (code): Install dependencies — follow the aii-colab skill's install cell pattern exactly. Fill in all packages imported by the artifact's code.
Cell 3 (code): Imports — copy original import block as-is, plus any additional imports needed for the notebook (e.g. matplotlib for visualization).
Cell 4 (code): Data loading helper — use the <data_loading_pattern> above.
Cell 5 (code): `data = load_data()`

--- Config ---
Config cell (code): Define ALL tunable parameters (iterations, epochs, n_samples, hidden_size, etc.) as variables at the top of this cell. Start with the ABSOLUTE MINIMUM values — the smallest that produce any output at all (e.g. 1 iteration, 2 samples, smallest array size). These get gradually increased during testing — see TODOs.

--- Processing ---
Remaining cells: One code cell per logical section of the original script. Add a markdown cell BEFORE each code cell. Copy code as closely as possible, with these changes:
  1. Replace file paths to use the loaded `data` variable.
  2. Use the config variables from the config cell (NOT hardcoded values).
  3. Minimal fixes are allowed if something doesn't work in notebook context (e.g. adjusting paths, removing CLI args, fixing imports), but keep changes to the absolute minimum.

--- Results ---
Visualization cell (code): Print key results in a readable table, plot numeric data with matplotlib if appropriate.
</notebook_structure>

<priority>
WORKING > OPTIMIZED. A small-scale demo that runs correctly is the goal. Once the notebook passes with minimum config values, scale up only if time permits — do NOT spend multiple retries chasing larger parameters. If a working version exists, finish and move on.
</priority>

<max_notebook_total_runtime>600s (10 min)</max_notebook_total_runtime>

<test_environment>
To test-run the notebook in a clean environment (simulating Colab), create a disposable `.nb_env` in your workspace:
```bash
/usr/bin/python3.12 -m venv .nb_env
.nb_env/bin/pip install -q pip jupyter ipykernel
.nb_env/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 code_demo.ipynb --output code_demo.ipynb
rm -rf .nb_env
```
The timeout is set to <max_notebook_total_runtime>. The entire notebook must finish within this time.

What happens: the .venv starts empty (just jupyter). When the notebook's install cell runs, `google.colab` is NOT in sys.modules, so ALL packages get installed — non-Colab packages unconditionally, and Colab packages (numpy, pandas, etc.) at Colab's exact versions via the guard block. The result mirrors Colab's environment as closely as possible. If a cell fails, fix the notebook and re-run.
</test_environment>

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.


<todos>
TODO 1. Read and STRICTLY follow these skills: aii-colab, aii-long-running-tasks.
TODO 2. Read demo file and relevant preview_* files (preview only). Understand script structure: imports, setup, processing, output. Identify ALL tunable parameters (iterations, epochs, n_samples, hidden_size, batch_size, etc.) — these go in the config cell.
TODO 3. Create `mini_demo_data.json`: curated subset from at most ONE dataset (no more than 100 diverse examples). CRITICAL: do NOT read/grep full output file — may crash. Use `head -c 5000` or stream first entries with Python to pick examples.
TODO 4. Create `code_demo.ipynb` via NotebookEdit following <notebook_structure>. Set ALL config parameters to ABSOLUTE MINIMUM values — the smallest that produce any output (e.g. 1 iteration, 2 samples, smallest array sizes). Test-run using <test_environment>. Fix all errors until it passes.
TODO 5. GRADUALLY SCALE (but don't overdo it): increase config params step by step (e.g. ~2x each round). After each increase: test-run, record runtime, fix errors. STOP SCALING as soon as results look meaningful — a working small-scale demo beats a failed large-scale one. If full original params fit within <max_notebook_total_runtime> (10% margin), use them. Otherwise keep whatever works and comment out the true original values. Do NOT spend more than 2-3 scaling rounds.
TODO 6. Verify: (1) code_demo.ipynb contains GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression/main/round-1/dataset-1/demo/mini_demo_data.json" exactly, (2) mini_demo_data.json exists, (3) uses GitHub URL pattern not just open('mini_demo_data.json').
</todos>

---

Output the result as JSON to: `/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k/.sdk_openhands_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "DemoExpectedFiles": {
      "description": "Expected output files from code demo notebook generation.",
      "properties": {
        "notebook": {
          "default": "",
          "description": "Path to the generated demo notebook. Example: 'code_demo.ipynb'",
          "title": "Notebook",
          "type": "string"
        },
        "mini_data_file": {
          "default": "",
          "description": "Path to the mini demo data JSON (curated subset). Example: 'mini_demo_data.json'",
          "title": "Mini Data File",
          "type": "string"
        }
      },
      "title": "DemoExpectedFiles",
      "type": "object"
    }
  },
  "description": "Dataset/experiment/evaluation \u2192 Jupyter notebook demo.\n\nTitle and summary come from the parent artifact (gen_art step),\nnot from the demo agent. The agent only outputs expected files.",
  "properties": {
    "out_expected_files": {
      "$ref": "#/$defs/DemoExpectedFiles",
      "description": "All output files you created. Must include the demo notebook."
    }
  },
  "required": [],
  "title": "CodeDemo",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_1/art_5_Iw7LOgL61k/.sdk_openhands_agent_struct_out.json` exists and contains JSON matching the schema above.

Survey three recent methods for prompt compression in LLM inference and propose one small novel variant; keep experiments tiny.
````
