# Recipe Card: Prompt Compression with Target-Model Attribution

## A. Method implementations

### 1. LLMLingua baseline
```python
from llmlingua import PromptCompressor
compressor = PromptCompressor(device_map="auto")
compressed = compressor.compress_prompt(
    prompt,
    instruction="",  # optional
    question="",
    target_token=256,
    compression_ratio=0.5,
    force_tokens=["must_keep_token_1"],
    token_distance=300,
    stride=300
)
```
Notes: `compression_ratio` is in [0,1]. `force_tokens` guarantees retention. `token_distance` prevents overly local retention. `stride` controls segment chunking for long prompts.

### 2. LongLLMLingua
```python
compressed = compressor.compress_prompt(
    prompt,
    instruction="",
    question=query,
    target_token=256,
    compression_ratio=0.5,
    use_question_as_condition=True
)
```
Notes: Contrastive perplexity compares `p(token|context)` and `p(token|question+context)`.

### 3. LLMLingua-2
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model_name = "microsoft/llmlingua-2-bert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
inputs = tokenizer(prompt, return_tensors="pt")
logits = model(**inputs).logits
scores = logits.softmax(-1)[..., 1]  # keep probability
mask = scores > 0.5
compressed_ids = inputs.input_ids[mask]
compressed = tokenizer.decode(compressed_ids, skip_special_tokens=True)
```
Notes: BERT classifier predicts token-level importance. API differs from v1 by avoiding iterative forward passes.

### 4. Attention rollout
```python
def attention_rollout(attentions, residual=True):
    # attentions: list of (batch, heads, seq, seq)
    rollout = torch.eye(attentions[0].shape[-1]).unsqueeze(0).unsqueeze(0)
    rollout = rollout.to(attentions[0].device)
    for att in attentions:
        att = att.mean(dim=1)  # mean over heads
        if residual:
            att = att + torch.eye(att.shape[-1]).to(att.device)
        rollout = torch.matmul(rollout, att)
        rollout = rollout / (rollout.sum(dim=-1, keepdim=True) + 1e-8)
    return rollout.squeeze(0).squeeze(0)  # token importance
```
Notes: Requires `output_attentions=True`. Memory heavy on long contexts.

### 5. Integrated gradients
```python
from captum.attr import LayerIntegratedGradients
lig = LayerIntegratedGradients(model, model.bert.embeddings)
attributions = lig.attribute(
    inputs=inputs.input_ids,
    baselines=torch.zeros_like(inputs.input_ids),
    target=0,
    n_steps=50
)
scores = attributions.sum(dim=-1)
```
Notes: Baseline can be zero embeddings or padding embeddings. Use 20-50 steps.

### 6. Hybrid proxy-target compression
```python
# Stage 1: proxy selection
proxy_ids = proxy_model.select_sentences(prompt, budget=0.5)
# Stage 2: target attribution
target_ids = target_model.attribute_tokens(proxy_ids)
mask = target_ids > threshold
compressed_ids = proxy_ids[mask]
```
Notes: Reduces cost by compressing before expensive attribution.

### 7. Attention sinks fallback
```python
sink_mask = torch.ones_like(input_ids, dtype=torch.bool)
sink_mask[:N] = True  # retain first N tokens
sink_mask[question_mask] = True  # retain query tokens
mask = sink_mask | attribution_mask
compressed_ids = inputs_ids[mask]
```
Notes: Cheap black-box approximation; strongest in streaming-trained models.

### 8. CADC variant
```python
# Offline calibration
cal_scores = []
for prompt in calibration_set:
    s = target_model.attention_rollout(prompt)
    cal_scores.append(s)
prior = torch.stack(cal_scores).mean(0)

# Online compression
attrib = proxy_model.classify(prompt)
combined = attrib + prior_weight * prior
mask = combined > threshold
compressed = decode(mask)
```
Notes: Keeps runtime near LLMLingua-2 by caching attention priors.

## B. Hyperparameter table
| Method | compression_ratio | token_distance | steps | batch/segment size | recommended values |
|--------|-------------------|----------------|-------|--------------------|--------------------|
| LLMLingua | 0.25-0.5 | 100-300 | N/A | stride 300-500 | 0.5 default |
| LongLLMLingua | 0.25-0.5 | 100-300 | N/A | stride 300-500 | 0.5 default |
| LLMLingua-2 | 0.25-0.5 | N/A | N/A | 64-256 tokens | threshold 0.5-0.7 |
| Attention rollout | N/A | N/A | layers all | N/A | mean-over-heads |
| Integrated gradients | N/A | N/A | 20-50 | 8-16 | zero baseline |
| Hybrid | N/A | N/A | N/A | coarse 0.5 budget | N/A |
| Attention sinks | retain first 1-32 tokens | N/A | N/A | N/A | 16 tokens default |
| CADC | 0.25-0.5 | N/A | N/A | 64-256 tokens | prior_weight 0.1-0.3 |

## C. Evaluation protocol
- Benchmark: LongBench [12, 13].
- Model: LLaMA-3-8B-Instruct or base, loaded via `transformers.AutoModelForCausalLM`.
- Compression ratios: 2x, 4x, 8x.
- Metrics:
  - Single-doc QA, multi-doc QA: F1 / exact match
  - Summarization: ROUGE-1/2/L
  - Few-shot learning: accuracy
- Data split: Use repository splits; if unavailable, random 80/20 calibration/test.
- Reproducibility: Seed all sampling, fix padding, log token counts.

## D. Compute requirements
- Proxy methods: CPU acceptable for 10k tokens; small model forward passes dominate.
- Attention rollout and integrated gradients: GPU recommended; 10k tokens may require chunking.
- LLMLingua-2: Fastest; suitable for CPU/GPU batching.
- Hybrid: Reduces target attribution cost by reducing token count first.
- CADC: Near real-time inference similar to LLMLingua-2 plus one offline calibration run.

## E. Failure modes and fallback strategies
- Proxy-target mismatch: reduce compression ratio or reorder hybrid stages.
- Attention/gradient instability: increase IG steps or fix baseline.
- Attention rollout memory blowup: aggregate only top layers or chunk multiplication.
- Attention sink failure on short contexts: disable for <50 tokens.
- Missing API compatibility: pin package versions and validate imports before experiments.

## Source URLs
- LLMLingua paper: https://arxiv.org/abs/2310.05778
- LongLLMLingua paper: https://arxiv.org/abs/2310.06839
- LLMLingua-2 paper: https://arxiv.org/abs/2403.2403.12972
- LLMLingua repo: https://github.com/microsoft/LLMLingua
- LLMLingua-2 repo: https://github.com/microsoft/LLMLingua-2
- Attention rollout paper: https://arxiv.org/abs/2005.00928
- HuggingFace attentions docs: https://huggingface.co/docs/transformers/main/output_attentions
- Integrated gradients paper: https://arxiv.org/abs/1703.01365
- Captum docs: https://captum.ai/
- Attention sinks paper: https://arxiv.org/abs/2309.17453
- LongBench paper: https://arxiv.org/abs/2405.20309
- LongBench repo: https://github.com/THUDM/LongBench
- Subset selection framing: https://arxiv.org/abs/2305.14242