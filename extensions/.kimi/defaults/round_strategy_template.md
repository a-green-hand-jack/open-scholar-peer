# Literature Round {{round_number}} — {{strategy_slug}}

## Method

- **Strategy:** `{{strategy_slug}}` (one of: `sub-domain-anchor`, `method-anchor`, `temporal-expansion`)
- **Goal of this round:** {{strategy_goal}}
- **Tools used (must use all available; LKM-first, Google Scholar as fallback):**
  - `osp-mcp.search_bohrium_lkm` (primary broad-coverage source; ~3 s, fixed-price)
  - `osp-mcp.search_bohrium_reasoning` (round 2 — reasoning chains)
  - `osp-mcp.search_bohrium_paper` (round 3 — year-window filters)
  - `osp-mcp.get_bohrium_paper_graph` (expand a top hit's graph)
  - `osp-mcp.search_arxiv`
  - `osp-mcp.search_semantic_scholar`
  - `osp-mcp.search_google_scholar` (FALLBACK only — when `mcp.bohrium_available` is `false` or LKM tools error out)
  - native Web Search (where available)
- **Query formulation rules for this round:**
  - Round 1 (sub-domain-anchor): use the paper's stated sub-domain and primary keywords; aim for the canonical 10–20 most-cited works in this area. LKM: `search_bohrium_lkm` with scopes `conclusion,abstract` (claims-level view of established prior art) + `search_bohrium_paper` for citation counts.
  - Round 2 (method-anchor): switch to the proposed method's name and key technical terms; find prior or concurrent work using the *same technique*. LKM: `search_bohrium_reasoning` with the method phrasing; `search_bohrium_lkm` on the method name; then `get_bohrium_paper_graph` on the top hit to expand its reasoning structure.
  - Round 3 (temporal-expansion): filter to the last 12 months; explicitly include arXiv pre-prints, workshop papers, and concurrent submissions; goal is catching what static knowledge cutoffs miss. LKM: `search_bohrium_paper` with `year_from`/`year_to` = the last 12 months + `search_arxiv` sorted by date.
- **Retention criteria:** keep papers that are (a) directly comparable on task or method, (b) cited >5 times if older than 12 months, (c) any pre-print regardless of citations if from the last 6 months and topically relevant.
- **Query seeding:** when `.brain/raw/02_lkm_paper_extraction.md` exists, derive at least one query per round from its open questions / conclusions (the paper's own research vocabulary).
- **Bohrium LKM billing:** LKM searches are fixed-price calls (0.05 CNY each; the personal monthly 1,000-call quota covers the first calls). Keep one bounded call per query — do not page automatically.

## Output

| # | Title | Authors | Year | Venue | Source(s) | Why kept |
|---|---|---|---|---|---|---|
| 1 | <title> | <authors> | <year> | <venue> | arxiv,semantic_scholar | <one-line justification> |
| 2 | ... | ... | ... | ... | ... | ... |

### Notes on what was excluded
<Brief mention of papers that surfaced but were dropped, with reason. Helps the next round avoid re-discovering them.>

## Provenance

- **Queries run:**
  - `<query 1>` — via `<tool>` — `<N results, K kept>`
  - `<query 2>` — via `<tool>` — `<N results, K kept>`
  - ...
- **Total unique papers retained from this round:** `<N>`
- **Time spent (approx):** `<N>` LLM-tool roundtrips
