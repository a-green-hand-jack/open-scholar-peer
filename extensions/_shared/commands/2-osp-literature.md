---
description: "OSP Phase 2: External retrieval — one round per invocation (sub-domain, method, temporal)"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md"]
writes: [".brain/raw/02a_literature_round1.md", ".brain/raw/02b_literature_round2.md", ".brain/raw/02c_literature_round3.md", ".brain/raw/02_retrieved_literature.md", ".brain/raw/02_lkm_paper_extraction.md", ".brain/session.json"]
---

# /2-osp-literature — Literature Review & Expansion

Runs ONE round of external retrieval per invocation. Invoke up to 3 times to complete all rounds.
After each round it shows a progress banner and asks whether to continue.

## Activation

Invoke the `osp-literature-review-agent` skill.

## Prerequisites

- `phases.summary.status == "completed"` and `01_structured_summary.md` exists.
- Rounds must be run in order (1 → 2 → 3).

## Resource notice

⚠️ LKM is the primary broad-coverage source (~3s/call, 0.05 CNY/search call). Optional PDF parse-result retrieval costs 1.00 CNY initially or 0.10 CNY on a cache hit. These calls require the explicit CLI flag `--allow-lkm-spend`; Google Scholar is fallback only after a primary LKM search error. Expect 1-3 minutes per round.

## Round definitions

| # | Strategy | Goal | Primary LKM tools |
|---|----------|------|-------------------|
| 1 | `sub-domain-anchor` | Search using the paper's stated sub-domain and primary keywords | `search_bohrium_lkm` + `search_bohrium_paper` |
| 2 | `method-anchor` | Search using the method's name and key technical terms | `search_bohrium_reasoning` + `get_bohrium_paper_graph` |
| 3 | `temporal-expansion` | Filter to last 12 months; include arXiv pre-prints, concurrent submissions | `search_bohrium_paper` + `search_arxiv` |

## Steps

1. Read `.brain/session.json`.
   - Determine `next_round = phases.literature.rounds_completed + 1` (default 0 → next = 1).
   - If `next_round > 3`, print: "All 3 rounds complete. Next: `/3-osp-historian`." and stop.
   - If any earlier round file is missing, resume from that round instead.

2. Read `.brain/raw/01_structured_summary.md`.

2.5. For the first invocation on a PDF, optionally use the Bohrium PDF parse tools to write `02_lkm_paper_extraction.md`. This is best-effort and must never block the three rounds.

3. Run the **next pending round only**:
   - Activate the `osp-literature-review-agent` skill for that round.
    - The skill searches using LKM first (`search_bohrium_lkm`, `search_bohrium_reasoning`, `search_bohrium_paper`, `get_bohrium_paper_graph`), plus arXiv and Semantic Scholar. Use Google Scholar only when an LKM call returns `{"error": ...}`.
    - Write the round file (`02a`, `02b`, or `02c`) using the template at `defaults/round_strategy_template.md`.
    - In the round artifact's `## Method`, write the exact marker `**Strategy:** \`<strategy-slug>\`` for the selected strategy.

4. Update `session.json`:
   - Increment `phases.literature.rounds_completed`.
   - If `rounds_completed == 1`: set `phases.literature.status = "in_progress"`.
   - If `rounds_completed == 3`: set `phases.literature.status = "completed"`,
     `phases.literature.notes = "3 rounds; <N> unique papers retained"`, `resume_from = "historian"`.
     Write the consolidated `02_retrieved_literature.md` (deduplicated table of all retained papers).

5. Print a progress banner and brief findings summary:
   ```
   ── Literature Review ────────────────────────────────────
   Round N/3 complete  (anchor: <anchor-name>)
   Papers retained this round: <n>
   Top finds: <2-3 bullet highlights>
   ↳ .brain/raw/02N_literature_round<N>.md
   ─────────────────────────────────────────────────────────
   ```
   - If `rounds_completed < 3`: "Run `/2-osp-literature` again to continue to round N+1."
   - If `rounds_completed == 3`: "Next: /3-osp-historian"

## Re-run behavior

Calling `/2-osp-literature` when a round is already complete will re-run that same round.
Warn once before overwriting its file, then proceed.
