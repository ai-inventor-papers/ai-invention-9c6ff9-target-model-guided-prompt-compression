# gen_paper_site — report_results

> Phase: `gen_paper_repo` · `gen_full_paper`
> Run: `run_8az8NIQ1qgmY` — Target-Model-Guided Prompt Compression via Attention Saliency
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_paper_site` (sdk_openhands_agent)

### [1] SYSTEM-USER prompt · 2026-09-21 01:58:19 UTC

````
<task>
Build the paper's public web page: ONE self-contained `index.html` that lets a reader grasp
this paper faster than opening the PDF would. It is published as this run's GitHub Pages site, so
it is the first thing anyone sees.
</task>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<what_is_already_here>
Your workspace is the finished paper folder. It already holds everything the page is made of, and
you must not change any of it — you are adding one file, not revising the paper.

- `paper.tex` — the paper as it was actually written. This is the source of truth for
  every claim, name and NUMBER that goes on the page.
- `paper.pdf` — the compiled paper. The page must NOT link to it by this local name:
  the PDF is published on the code branch and the page on a different one. Link to it at the
  full URL below instead.
- `references.bib` — the bibliography, when the paper has one.
- `figures/` — every figure the paper uses, flattened into one folder.
- `workspace/` — the scratch folder the LaTeX task worked in. Ignore it.
</what_is_already_here>

<paper_text>
title: Target-Model-Guided Prompt Compression via Attention Saliency
abstract: >-
  Prompt compression reduces the token length of inputs to large language models (LLMs) to lower inference cost and latency.
  All existing methods estimate token importance using a small proxy model, creating a distribution mismatch: the proxy's
  notion of importance may not match what the target LLM actually attends to during generation. We propose using the target
  model's own attention-saliency maps, computed via attention rollout, to directly measure which prompt tokens the target
  model uses. On LongBench, attention rollout outperforms all proxy-based methods and the no-compression baseline across three
  task categories and two compression ratios, as measured by mean rank. A hybrid variant combining proxy coarse filtering
  with target-model fine selection ranks second. These results demonstrate that eliminating the proxy gap yields measurable
  gains, though the effect is modest and task-dependent.
paper_text: |-
  # Target-Model-Guided Prompt Compression via Attention Saliency

  ## Abstract

  Prompt compression reduces the token length of inputs to large language models (LLMs) to lower inference cost and latency. All existing methods estimate token importance using a small proxy model, creating a distribution mismatch: the proxy's notion of importance may not match what the target LLM actually attends to during generation. We propose using the target model's own attention-saliency maps, computed via attention rollout, to directly measure which prompt tokens the target model uses. On LongBench, attention rollout outperforms all proxy-based methods and the no-compression baseline across three task categories and two compression ratios, as measured by mean rank. A hybrid variant combining proxy coarse filtering with target-model fine selection ranks second. These results demonstrate that eliminating the proxy gap yields measurable gains, though the effect is modest and task-dependent.

  ## 1 Introduction

  ### The problem

  Large language models achieve strong performance on diverse tasks when given long, detailed prompts. Chain-of-thought reasoning, in-context learning, and retrieval-augmented generation routinely produce prompts of thousands to tens of thousands of tokens. Processing such prompts incurs quadratic attention cost, high latency, and degraded information perception as key content is diluted across the context window.

  ### Why it matters

  Compressing prompts before they reach the target LLM directly reduces compute, memory, and monetary cost. A 4× compression ratio cuts attention FLOPs by 16× and can accelerate end-to-end latency by 1.5–2×. For production deployments serving millions of queries, these savings are substantial.

  ### Why prior work has not solved it

  Every existing prompt compression method uses a proxy model to estimate token importance [1, 2, 3, 4, 5, 6]. LLMLingua uses GPT-2 perplexity [1]. LongLLMLingua adds query-aware contrastive perplexity with LLaMA-7B [2]. LLMLingua-2 trains a BERT-based token classifier on GPT-4 distilled data [3]. Selective Context uses self-information from a small LM [4]. PCRL trains a compression policy on DistilBERT with RL rewards [5]. Perception Compressor uses guiding questions and contrastive perplexity from a small LM [6]. None of these methods has access to the target model's actual attention patterns.

  ### Our approach and results

  We propose Target-Attention Prompt Compression (TAPC): compute attention-saliency maps from the target model itself using attention rollout [7], and retain tokens with the highest saliency scores. This directly measures what the target model attends to, eliminating the proxy gap. We evaluate seven compression methods plus a no-compression baseline on LongBench across three task categories and two compression ratios. Attention rollout achieves the best mean rank across all task categories and both compression ratios, outperforming all proxy methods and the baseline. A hybrid variant combining LLMLingua-2 coarse filtering with attention-based fine selection ranks second.

  [FIGURE:fig1]

  ### Summary of Contributions

  - **Target-model attention for prompt compression.** We introduce attention rollout from the target model as a token importance signal for prompt compression, replacing proxy-model estimates.
  - **Comprehensive empirical comparison.** We evaluate seven methods (four proxy-based, three target-model-guided) on LongBench across three task categories and two compression ratios, with a rank-based selection criterion.
  - **Key finding: proxy gap is real but modest.** Attention rollout outperforms all proxy methods and the no-compression baseline at both compression ratios, demonstrating that the target model's own attention better predicts token utility for generation. The advantage grows with compression aggressiveness.
  - **Practical hybrid variant.** A two-stage hybrid (LLMLingua-2 coarse + target attention fine) achieves near-best performance with reduced compute, offering a practical deployment path.

  ## 2 Related Work

  ### Proxy-model-based prompt compression

  LLMLingua [1] pioneered iterative token dropping guided by GPT-2 perplexity, with a budget controller for high compression ratios. LongLLMLingua [2] extended this with query-aware contrastive perplexity: the difference between p(token|context) and p(token|question, context), using LLaMA-7B. LLMLingua-2 [3] reformulated compression as token classification, training a BERT-based encoder on GPT-4 distilled data to achieve 3–6× speedups over iterative methods. Selective Context [4] uses self-information from a causal LM to drop predictable tokens. PCRL [5] applies reinforcement learning with ROUGE rewards to train a discrete compression policy on DistilBERT. Perception Compressor [6] generates guiding questions and uses contrastive perplexity from a small LM. All these methods share a fundamental limitation: they rely on a proxy model's internal signals, which may not match the target LLM's attention patterns.

  ### Target-model attention for other purposes

  Attention rollout [7] recursively multiplies attention matrices across layers to approximate token-to-token attribution in transformers. Integrated gradients [8] provides axiomatic feature attribution via path integrals of gradients. Both originate in mechanistic interpretability [9, 10] and have been used for model compression (e.g., MiniLMv2 attention distillation [11]) and KV cache compression during generation (Keyformer [12], PyramidInfer [13]). StreamingLLM [14] exploits attention sinks, i.e., disproportionate attention to initial tokens, to enable infinite-length generation. Our work is the first to apply target-model attention/attribution to *prompt compression* (selecting input tokens before generation) rather than model compression or KV cache selection. The distinction is meaningful: prompt compression selects tokens before any generation, operating on the input modality, while KV cache compression selects keys during autoregressive generation based on future attention patterns.

  ### Benchmarks

  LongBench [15] provides 21 datasets across six task categories in English and Chinese, with average context lengths of ~6,700 words. We use nine representative tasks from three categories: single-document QA (narrativeqa, qasper, multifieldqa_en), multi-document QA (hotpotqa, 2wikimqa, musique), and summarization (multi_news, gov_report, qmsum).

  ## 3 Method

  ### 3.1 Problem formulation

  Given a prompt $x = [x_1, ..., x_n]$ of $n$ tokens and a target LLM $M$, prompt compression seeks a subset $S \subset \{1,...,n\}$ of size $k = \lfloor n/r \rfloor$ (compression ratio $r$) such that $M(x_S)$ performs well on the downstream task. The importance score $I_i$ for token $x_i$ determines the selection.

  ### 3.2 Proxy-model importance (baselines)

  **LLMLingua** [1]: $I_i = -\log p_{\text{GPT-2}}(x_i | x_{<i})$, computed iteratively with a budget controller.

  **LongLLMLingua** [2]: $I_i = \text{perp}(x_i|x_{<i}) - \text{perp}(x_i|q, x_{<i})$, where $q$ is the question. Uses LLaMA-7B.

  **LLMLingua-2** [3]: $I_i = p_{\text{BERT}}(\text{keep} | x_i, \text{context})$, a token classifier trained on GPT-4 distilled data.

  ### 3.3 Target-model attention-saliency

  **Attention rollout.** For each layer $\ell$, let $A^{(\ell)} \in \mathbb{R}^{h \times n \times n}$ be the attention weights averaged over $h$ heads. The rollout matrix is
  $$R = \prod_{\ell=1}^L \left( \bar{A}^{(\ell)} + I \right)$$
  where $\bar{A}^{(\ell)}$ is the mean over heads and $I$ is the identity. Token importance is the row-sum of the final row corresponding to the first generated token (or mean over output positions): $I_i = \sum_j R_{:,j}$ [7].

  ### 3.4 Target-model-guided methods

  | Method | Description |
  |--------|-------------|
  | **Attention Rollout (per-query)** | Compute rollout on the full prompt for each query; retain top-$k$ tokens by $I_i$. |
  | **Hybrid** | Stage 1: LLMLingua-2 compresses to 50% (2×). Stage 2: Attention rollout on retained tokens; final top-$k$ by combined score. |
  | **Attention Sink** | Retain first $k_{\text{sink}} = \max(3, 0.1n)$ tokens (BOS, instruction, question); fill remaining budget with LLMLingua-2 selections from the rest. |

  All methods operate on tokenized input; importance scores are interpolated to match token boundaries when needed.

  ## 4 Experimental Setup

  ### 4.1 Dataset

  We use the LongBench mini-split [15]: 27 examples (3 per task × 9 tasks) stratified across three categories. Each example includes context, question, ground truth, and token counts under LLaMA-3-8B tokenizer. Compression budgets are 50% (2×) and 25% (4×) of original tokens.

  ### 4.2 Target model

  GPT-2 (124M parameters, 12 layers) serves as the target model [ARTIFACT:art_-q7txtqSk26A]. The hypothesis assumes white-box access to open models such as LLaMA-3-8B; GPT-2 provides attention matrices with an identical API, enabling a proof-of-concept validation. Results on larger models remain future work.

  ### 4.3 Baselines and methods compared

  Seven methods plus baseline:
  1. **Baseline**: no compression
  2. **LLMLingua**: GPT-2 perplexity proxy
  3. **LongLLMLingua**: contrastive perplexity proxy
  4. **LLMLingua-2**: BERT classifier proxy
  5. **Attention Rollout**: per-query target attention
  6. **Hybrid**: LLMLingua-2 (2×) → Attention Rollout
  7. **Attention Sink**: first-$k$ + proxy

  ### 4.4 Metrics and protocol

  We report token-level F1 and ROUGE-L for QA tasks, ROUGE-L for summarization. For each method–ratio–category combination we compute mean F1 and ROUGE-L across examples. Methods are ranked by mean of (F1+ROUGE-L)/2 averaged across all category–ratio pairs; lower rank is better [ARTIFACT:art_-q7txtqSk26A].

  ### 4.5 Compute

  Experiments run on CPU with GPT-2. Each method requires one forward pass with attention output per example at each compression ratio.

  ## 5 Results

  ### 5.1 Main results

  Table 1 shows the mean rank of each method across all nine tasks and two compression ratios.

  | Rank | Method | Mean Rank |
  |------|--------|-----------|
  | 1 | Attention Rollout | 1.0 |
  | 2 | Hybrid | 1.5 |
  | 3 | Baseline | 2.0 |
  | 4 | LLMLingua | 2.5 |
  | 5 | LLMLingua-2 | 3.0 |
  | 6 | Attention Sink | 3.5 |
  | 7 | LongLLMLingua | 4.0 |
  | 8 | No Compression | 4.5 |

  [FIGURE:fig2]

  Figure 2 (left) shows F1 scores for single-document QA at 2× compression. Attention Rollout leads at 0.31, with Baseline at 0.28, Hybrid at 0.27, LLMLingua at 0.25, LLMLingua-2 at 0.24, Attention Sink at 0.22, LongLLMLingua at 0.20, and No Compression at 0.19. Figure 2 (right) shows ROUGE-L for summarization at 2×: Attention Rollout 0.26, Hybrid 0.25, Baseline 0.24, LLMLingua 0.22, LLMLingua-2 0.21, Attention Sink 0.19, LongLLMLingua 0.17, and No Compression 0.16.

  [FIGURE:fig3]

  **Single-document QA** (narrativeqa, qasper, multifieldqa_en): Attention Rollout achieves mean F1 0.31, ROUGE-L 0.28. Hybrid: F1 0.27, ROUGE-L 0.25. Baseline: F1 0.28, ROUGE-L 0.24. LLMLingua: F1 0.25, ROUGE-L 0.22. The proxy methods lose 10–15% relative to baseline; target-model methods match or exceed baseline.

  **Multi-document QA** (hotpotqa, 2wikimqa, musique): Attention Rollout F1 0.29, ROUGE-L 0.26. Hybrid F1 0.26, ROUGE-L 0.24. Baseline F1 0.25, ROUGE-L 0.22. The gap between target-model and proxy methods widens: LongLLMLingua F1 0.19, LLMLingua-2 F1 0.21.

  **Summarization** (multi_news, gov_report, qmsum): Attention Rollout ROUGE-L 0.26. Hybrid 0.25. Baseline 0.24. LLMLingua 0.22. Target-model methods consistently outperform proxy methods across all three categories.

  ### 5.3 Compression ratio sensitivity

  Figure 4 shows how the rank ordering evolves with compression ratio. At 2×, all methods are close to baseline (ranks 1.2–2.5). At 4×, Attention Rollout (1.0) and Hybrid (1.3) separate from the pack. The advantage of target-model attention grows with compression aggressiveness: at 4×, Attention Rollout extends its lead while all proxy methods fall below 3.5.

  [FIGURE:fig4]

  ### 5.4 Ablation: target-model methods only

  Among the three target-model methods, per-query attention rollout is best (rank 1.0), hybrid second (1.5), and attention sink last (3.5). The hybrid method recovers 80% of the per-query gain with ~50% less compute (coarse stage on proxy). Attention sink underperforms because the sink tokens (BOS, instruction) are not always the most task-relevant.

  ## 6 Discussion and Limitations

  ### 6.1 Why target-model attention works

  Proxy models estimate importance from their own next-token prediction objective. The target model, however, attends to tokens based on the full context and the specific generation task. Attention rollout captures this by aggregating cross-layer attention flow toward output positions. The consistent win across categories suggests the proxy gap is systematic, not task-specific.

  ### 6.2 Compute trade-offs

  Per-query attention rollout requires one forward pass with attention output per example. For LLaMA-3-8B on 10k tokens, this is ~0.5s on A100. The hybrid method reduces this by using LLMLingua-2 (fast, CPU) for coarse filtering, then attention on the reduced set. Calibration distilled amortizes the cost over many queries but loses task-specificity. Production systems can choose based on latency budget.

  ### 6.3 Limitations

  **Model scale.** Experiments use GPT-2 as the target model. Attention patterns may differ qualitatively at larger scales (7B+ parameters). We have not tested on larger models; the current results demonstrate the principle but may not generalize to production-scale LLMs.

  **Dataset scope.** The LongBench mini-split (27 examples) is a screening set. Results may shift on the full distribution (1,300 examples) and additional benchmarks.

  **Metric limitations.** Token F1 and ROUGE-L measure surface overlap; they may not capture semantic faithfulness for open-ended generation. Human evaluation is needed for qualitative assessment.

  **Attention rollout approximations.** Rollout assumes linear attention composition and adds identity; recent work questions its fidelity [16]. Integrated gradients were not evaluated due to compute constraints.

  ## 7 Conclusion

  We introduced Target-Attention Prompt Compression (TAPC), using the target LLM's own attention-saliency maps to select prompt tokens. On LongBench, attention rollout outperforms all proxy-model baselines (LLMLingua, LongLLMLingua, LLMLingua-2) and the no-compression baseline across single-document QA, multi-document QA, and summarization at 2× and 4× compression. A hybrid variant achieves near-parity with reduced compute. The proxy gap is real and measurable: the target model's attention better predicts which tokens it needs for generation than any small proxy model's perplexity or classifier scores.

  Future work: (1) Scale to LLaMA-3-8B/Mistral-7B as target models. (2) Evaluate integrated gradients vs attention rollout. (3) Test on the full LongBench distribution and additional benchmarks. (4) Explore learned combinations of proxy and target signals. (5) Human evaluation of compressed prompt quality.

  ## References

  [1] Jiang, H., Wu, Q., Lin, C.-Y., Yang, Y., & Qiu, L. (2023). LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models. *EMNLP 2023*, 5345–5359.

  [2] Jiang, H., Wu, Q., Luo, X., Li, D., Lin, C.-Y., Yang, Y., & Qiu, L. (2024). LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression. *ACL 2024*, 1628–1643.

  [3] Pan, Z., Wu, Q., Jiang, H., Xia, M., Luo, X., Zhang, J., Lin, Q., Rühle, V., Yang, Y., Lin, C.-Y., Zhao, H. V., Qiu, L., & Zhang, D. (2024). LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression. *ACL Findings 2024*, 648–663.

  [4] Li, Y., Zhang, Z., Wang, H., Zhou, M., Chen, Y., Li, Y., Liu, J., Chen, J., Lin, Z., Wang, Y., et al. (2023). Selective Context: Compressing Prompts via Self-Information. *EMNLP Findings 2023*, 13610–13622.

  [5] Jung, J. & Kim, H. (2023). Prompt Compression and Contrastive Conditioning for Controllable Text Generation. *EMNLP 2023*, 13278–13292.

  [6] Tang, J., Bai, Y., Huang, Z., Du, Z., Liu, X., Tang, J., & Li, J. (2025). Perception Compressor: Training-free Prompt Compression via Guiding Questions and Contrastive Perplexity. *NAACL Findings 2025*.

  [7] Abnar, S. & Zuidema, W. (2020). Quantifying Attention Flow in Transformers. *ACL 2020*, 4190–4197.

  [8] Sundararajan, M., Taly, A., & Yan, Q. (2017). Axiomatic Attribution for Deep Networks. *ICML 2017*, 3319–3328.

  [9] Vig, J. (2019). A Multiscale Visualization of Attention in the Transformer Model. *ACL 2019 (demo)*.

  [10] Chefer, H., Gur, S., & Wolf, L. (2021). Transformer Interpretability Beyond Attention Visualization. *CVPR 2021*.

  [11] Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2021). MiniLMv2: Multi-Head Self-Attention Relation Distillation for Compressing Pretrained Transformers. *ACL Findings 2021*.

  [12] Liu, Z., Yuan, J., Jin, H., Luo, Z., Chen, Q., Zhang, B., Yu, X., Liu, J., Shi, Y., Ma, X., et al. (2023). Keyformer: KV Cache Reduction with Key Token Selection for Efficient LLM Inference. *NeurIPS 2023*.

  [13] Zhang, B., Liu, Z., Yuan, J., Jin, H., Luo, Z., Chen, Q., Yu, X., Liu, J., Shi, Y., Ma, X., et al. (2023). PyramidInfer: Efficient LLM Inference with Pyramid KV Cache. *NeurIPS 2023*.

  [14] Xiao, G., Tian, Y., Chen, B., Han, S., & Lewis, M. (2024). Efficient Streaming Language Models with Attention Sinks. *ICLR 2024*.

  [15] Bai, Y., Lv, X., Zhang, J., Lyu, H., Tang, J., Huang, Z., Du, Z., Liu, X., Zeng, A., Hou, L., Dong, Y., Tang, J., & Li, J. (2024). LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding. *ACL 2024*, 3158–3173.

  [16] Jain, S. & Wallace, B. C. (2019). Attention is not Explanation. *NAACL 2019*.
summary: >-
  This paper introduces target-model attention (attention rollout) for prompt compression, demonstrating that using the target
  LLM's own attention signals outperforms proxy-model-based methods on LongBench across QA and summarization tasks.
</paper_text>

<available_figures>
Each line gives the path the PAGE must use, then the figure's title and caption. It is the same
path the file has on disk here: the publish step copies the page and its figures into one folder,
so what works in this workspace is what works on the live site.

- figures/fig1_v0.jpg — "System Architecture" (caption: "Pipeline for target-model-guided prompt compression. The target LLM's attention maps are computed via attention rollout, and tokens are ranked by aggregated attention flow to the first generated token.")
- figures/fig2_v0.png [render from fig2_v0.pdf first] — "Performance Comparison by Metric" (caption: "Comparison of F1 (left) and ROUGE-L (right) across eight methods at 2× compression on LongBench. Attention Rollout achieves the highest scores in both metrics.")
- figures/fig3_v0.png [render from fig3_v0.pdf first] — "Performance by Task Category" (caption: "Mean F1 scores by task category (single-doc QA, multi-doc QA, summarization) at 2× compression. Target-model methods consistently outperform proxy methods across all categories.")
- figures/fig4_v0.png [render from fig4_v0.pdf first] — "Compression Ratio Sensitivity" (caption: "Mean rank across methods at 2× and 4× compression ratios. The advantage of attention rollout grows with compression aggressiveness.")
</available_figures>

<figure_requirements>
- Reference every figure as `figures/` plus its filename, exactly as listed above.
  The publish step copies the page and its figures into one folder together, so that relative
  path is what resolves on the live site; anything else breaks once published.
- A browser cannot draw a PDF in an image element. Data figures are delivered as vector PDF for
  LaTeX's benefit, so for each one check whether a PNG of the same name already sits in
  `figures/`; if it does not, render one there at about 200 DPI with pdftoppm or
  pymupdf before referencing it. Renderable formats: .avif, .gif, .jpeg, .jpg, .png, .svg, .webp.
- Write those PNG files into `figures/` and nowhere else — that folder is published, a
  new folder of your own is not.
- Use each figure's own caption. Do not invent new ones, and do not describe a figure you did not
  place on the page.
- Look at every figure before you place it. A figure whose axis labels are unreadable at the size
  you give it is worse than no figure.
</figure_requirements>

<page_structure>
In this order, top to bottom:

1. HERO — the paper's title, the author line as the paper gives it, and a one-paragraph TL;DR in
   plain language: what was asked, what was found, and the single number that carries the finding.
   Not the abstract, and not a rewrite of it. Below it, two links: the PDF and the code
   repository, both at the exact URLs given in the links section below.
2. CONTRIBUTIONS — the paper's actual contributions as three to five scannable cards, each a short
   heading plus one or two sentences. If the paper claims four things, show four cards, not five.
3. METHOD — a walkthrough a technically literate non-specialist can follow: what goes in, what
   happens to it, what comes out, and why the design is the way it is. Lead with the paper's own
   method figure when it has one.
4. RESULTS — the paper's real headline numbers, read out of `paper.tex` and the data
   files behind it, each next to what it was measured on and what it is being compared against.
   A number that is not in the paper does not go on the page, and neither does a comparison the
   paper did not make. If a slot has no number, drop the slot.
5. FIGURE GALLERY — every figure, each with its caption, click-to-enlarge into a lightbox that
   closes on Escape, on a click outside, and on a visible close control.
6. LIMITATIONS — what the paper says it does not show. Verbatim in substance; do not soften it.
7. FOOTER — links to the PDF and the repository again, and the citation if the paper carries one.

A sticky section navigation runs alongside all of it and marks where the reader currently is.
</page_structure>

<technical_requirements>
- ONE file. All CSS in a style element, all JavaScript in a script element, both inline in
  `index.html`. No build step, no bundler, no framework, no external script, stylesheet, web
  font or analytics — nothing fetched at load time. The page must render with the network off,
  and the only files it may point at are the figures listed above and the PDF beside it.
- System font stack only, since no font may be downloaded.
- Light theme. Responsive from a 360px phone to a wide desktop, with no horizontal page scroll;
  wide content scrolls inside its own container.
- Honour prefers-reduced-motion: under it, transitions and any scroll-driven effect stop.
- Keyboard-navigable: every control reachable by Tab in a sensible order, a visible focus ring,
  the lightbox trapping focus while open and returning it to the thumbnail on close, and a skip
  link to the main content.
- Semantic HTML: one top-level heading, headings that descend without skipping, landmark elements,
  and alt text on every image that says what the figure shows rather than repeating its number.
- No emoji anywhere. No purple-to-blue gradients. No decorative icon fonts.
- Keep the whole file comfortably under a megabyte.
</technical_requirements>

<writing_register>
Write in the register of the field's best papers (the paper this page presents, which was written to them), not in the register of a language
model. Four things are measured on the finished draft, and a draft outside them is sent back with
the numbers:
- Never use: delve, underscore, showcase, intricate, pivotal, realm, commendable, meticulous, tapestry, garner, multifaceted, it is worth noting, plays a crucial role, not only ... but also. These are 10 to 30 times more frequent in machine-written abstracts than in
  human ones, and reviewers read them as such.
- Em dashes: at most 3 per 1,000 words. Use a comma, a colon or a full stop.
- Sentence rhythm: mix short and long sentences. An interquartile range of sentence length under
  8 words reads as machine-written.
- Hedging: at most 15 hedges (may, likely, suggests, appears) per 1,000
  words. State what the evidence supports plainly; hedge where it is thin, not everywhere.
Style never changes substance: numbers, claims, citations and figure markers stay exactly as the
evidence gives them. The user's original request (delivered as a separate message) overrides all
of this wherever the two conflict.
</writing_register>

<links>
Use these two URLs VERBATIM wherever the page links to the paper or the code. Do not shorten them,
do not turn either into a relative path, and do not compose one of your own.

- The paper PDF: https://cdn.jsdelivr.net/gh/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression@main/paper.pdf
- The code repository: https://github.com/ai-inventor-papers/ai-invention-9c6ff9-target-model-guided-prompt-compression

Both carry the branch this run publishes to. A link without it opens a DIFFERENT run's work —
it resolves and looks correct, which is why it must be copied rather than derived. They begin
resolving only after this run finishes publishing, so do NOT try to open or verify them.
</links>

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.

<todos>
TODO 1. Read and STRICTLY follow these skills: aii-web-tools.
TODO 2. Read `paper.tex` end to end and list `figures/`. Write down the
paper's title, its author line, its contributions, and every headline number together with the
sentence it appears in — those sentences are the only numbers allowed on the page. Note which
figures are PDFs and so need a PNG rendered.
TODO 3. Render a PNG at about 200 DPI, into `figures/`, for every figure not already
in a browser-renderable format, then LOOK at each image you plan to use so you know what it shows
and how large it has to be on the page to stay legible.
TODO 4. Write `index.html` following the page_structure and technical_requirements sections
above: one file, inline CSS and JavaScript, every image referenced through the published figure
prefix.
TODO 5. VERIFY THE NUMBERS: for each number on the page, grep `paper.tex` for it and
confirm it appears there with the same meaning. Delete any number you cannot find. Then confirm
every claim on the page is one the paper actually makes.
TODO 6. VERIFY THE PAGE: confirm `index.html` has no external script, stylesheet or font
reference; that every image path starts with the published figure prefix and names a file that
exists in `figures/`; and that the PDF and repository links are character-for-
character the two URLs given in the links section, not `paper.pdf` and not any URL you
composed. Then open the page in a browser, screenshot it at a phone width and a desktop width,
read both screenshots, and fix anything cramped, overlapping or cut off.
TODO 7. ACCESSIBILITY PASS: tab through the whole page and confirm every control is reachable with a
visible focus ring, the lightbox traps focus and closes on Escape, headings descend without
skipping, and every image has alt text. Fix what fails.
</todos>

---

Output the result as JSON to: `/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_4_assemble_paper/paper/.sdk_openhands_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "PaperSiteExpectedFiles": {
      "description": "All expected output files from paper-site generation.",
      "properties": {
        "site_html_path": {
          "description": "Path to the single self-contained HTML page. Example: 'index.html'",
          "title": "Site Html Path",
          "type": "string"
        }
      },
      "required": [
        "site_html_path"
      ],
      "title": "PaperSiteExpectedFiles",
      "type": "object"
    }
  },
  "description": "Paper site \u2014 structured output from presentation-page generation.",
  "properties": {
    "summary": {
      "description": "Brief summary of the page you built: the sections it carries, which figures it shows, which numbers it quotes and where each came from in the paper.",
      "maxLength": 5000,
      "minLength": 300,
      "title": "Summary",
      "type": "string"
    },
    "out_expected_files": {
      "$ref": "#/$defs/PaperSiteExpectedFiles",
      "description": "All output files you created. Must include index.html."
    }
  },
  "required": [
    "summary",
    "out_expected_files"
  ],
  "title": "PaperSite",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/4_gen_paper_repo/_4_assemble_paper/paper/.sdk_openhands_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-09-21 01:58:19 UTC

```
Survey three recent methods for prompt compression in LLM inference and propose one small novel variant; keep experiments tiny.
```

### [3] SYSTEM-USER prompt · 2026-09-21 02:06:15 UTC

```
<validation-feedback>
Attempt 1 failed validation.

The output file `.sdk_openhands_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Produce `.sdk_openhands_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```

### [4] SYSTEM-USER prompt · 2026-09-21 02:12:50 UTC

```
<validation-feedback>
Attempt 2 failed validation.

The output file `.sdk_openhands_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Produce `.sdk_openhands_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```

### [5] SYSTEM-USER prompt · 2026-09-21 02:13:42 UTC

```
SITE VERIFICATION FAILED: 1 problem(s) in index.html.

- image source '' does not start with 'figures/', so it will not resolve once the page is published beside its figures folder

You MUST:
1. Fix every problem listed above in index.html.
2. Keep the page ONE self-contained file — all CSS and JavaScript inline, no external scripts, stylesheets or web fonts, nothing fetched at load time.
3. Point every image at figures/<filename>, where <filename> is a browser-renderable image that really exists in your figures/ folder. A vector PDF figure needs a PNG rendered beside it first; reference the PNG.
4. Re-open the page and confirm it still renders before finishing.
```

### [6] SYSTEM-USER prompt · 2026-09-21 02:14:02 UTC

```
SITE VERIFICATION FAILED: 1 problem(s) in index.html.

- image source '' does not start with 'figures/', so it will not resolve once the page is published beside its figures folder

You MUST:
1. Fix every problem listed above in index.html.
2. Keep the page ONE self-contained file — all CSS and JavaScript inline, no external scripts, stylesheets or web fonts, nothing fetched at load time.
3. Point every image at figures/<filename>, where <filename> is a browser-renderable image that really exists in your figures/ folder. A vector PDF figure needs a PNG rendered beside it first; reference the PNG.
4. Re-open the page and confirm it still renders before finishing.
```
