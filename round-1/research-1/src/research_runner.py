#!/usr/bin/env python3
"""
Lightweight web research helper for prompt compression methods.
Uses requests + BeautifulSoup if available, otherwise falls back to regex.
Writes results to sources_raw.jsonl in the workspace.
"""

import os
import re
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

WORKSPACE = Path("/home/adrian/projects/ai-inventor-wt-integ/aii_data/users/admin/runs/run_8az8NIQ1qgmY/3_invention_loop/iter_1/gen_art/gen_art_research_1")
OUT_PATH = WORKSPACE / "sources_raw.jsonl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIInventorResearchBot/1.0)"
}

QUERIES = [
    ("LLMLingua", "LLMLingua prompt compression GitHub pip install API"),
    ("LLMLingua", "LLMLingua perplexity scoring token retention compression_ratio"),
    ("LongLLMLingua", "LongLLMLingua contrastive perplexity query-aware compression"),
    ("LongLLMLingua", "LongLLMLingua GitHub implementation API differences"),
    ("LLMLingua-2", "LLMLingua-2 huggingface token classifier data distillation"),
    ("LLMLingua-2", "LLMLingua-2 performance speed tradeoffs"),
    ("attention rollout", "attention rollout Abnar Zuidema 2020 transformers implementation"),
    ("attention rollout", "attention rollout recursive multiplication attention flow code"),
    ("integrated gradients", "integrated gradients Captum LayerIntegratedGradients transformers API"),
    ("integrated gradients", "integrated gradients per-token importance baseline steps"),
    ("calibration-set distillation", "prompt compression calibration set token importance cross-task stability"),
    ("hybrid proxy-target", "two-stage prompt compression coarse fine sentence token selection"),
    ("attention sinks", "attention sinks streaming LLM first token retention generalizability"),
    ("attention sinks", "attention sinks Xiao 2023 black-box approximation"),
    ("LongBench", "LongBench benchmark long context evaluation script metrics dataset"),
]


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def duckduckgo_search(query):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    html = fetch(url)
    results = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html):
        href = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2))
        # extract snippet
        snippet = ""
        sm = re.search(re.escape(urllib.parse.quote_plus(query.split()[0])) + r'.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html, re.S)
        if sm:
            snippet = re.sub(r'<[^>]+>', '', sm.group(1))
        results.append({"url": href, "title": title, "snippet": snippet})
    return results


def github_search(query):
    url = "https://github.com/search?q=" + urllib.parse.quote_plus(query) + "&type=repositories"
    try:
        html = fetch(url)
        results = []
        for m in re.finditer(r'<a[^>]+class="Link--primary"[^>]*href="(/[^"]+)"[^>]*>(.*?)</a>', html):
            href = "https://github.com" + m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            results.append({"url": href, "title": title, "snippet": ""})
        return results
    except Exception as e:
        return [{"url": url, "title": "GitHub search failed", "snippet": str(e)}]


def main():
    out = []
    for topic, query in QUERIES:
        print(f"=== {topic}: {query}")
        # DuckDuckGo HTML search
        try:
            ddg = duckduckgo_search(query)
        except Exception as e:
            ddg = [{"url": "", "title": "DDG failed", "snippet": str(e)}]
        time.sleep(1.5)
        # GitHub search for code-related queries
        gh = []
        if any(k in query.lower() for k in ["github", "implementation", "code", "api"]):
            try:
                gh = github_search(query)
            except Exception as e:
                gh = [{"url": "", "title": "GitHub search failed", "snippet": str(e)}]
            time.sleep(1.5)
        for r in ddg[:3] + gh[:2]:
            out.append({
                "topic": topic,
                "type": "search",
                "query": query,
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "status": "found"
            })
        if not ddg and not gh:
            out.append({
                "topic": topic,
                "type": "search",
                "query": query,
                "url": "",
                "title": "",
                "snippet": "",
                "status": "empty"
            })
    OUT_PATH.write_text("\n".join(json.dumps(x) for x in out))
    print(f"Wrote {len(out)} entries to {OUT_PATH}")


if __name__ == "__main__":
    main()
