---
description: "OSP Phase 2: External retrieval — one round per invocation (sub-domain, method, temporal)"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md"]
writes: [".brain/raw/02a_literature_round1.md", ".brain/raw/02b_literature_round2.md", ".brain/raw/02c_literature_round3.md", ".brain/raw/02_retrieved_literature.md", ".brain/session.json"]
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

⚠️ Each invocation makes ~8-12 API calls across the retrieval tools (Bohrium LKM, arXiv, Semantic Scholar; native web search where available). Expect ~1-2 minutes per round. Bohrium LKM is the primary broad-coverage source (~3 s/call, fixed-price 0.05 CNY each, personal monthly 1,000-call free quota) — Google Scholar is used only as fallback when LKM is unavailable.

## Round definitions

| # | Anchor | Goal | Primary LKM tools |
|---|--------|------|-------------------|
| 1 | `sub-domain-anchor` | Search using the paper's stated sub-domain and primary keywords | `search_bohrium_lkm` (scopes conclusion,abstract) + `search_bohrium_paper` |
| 2 | `method-anchor` | Search using the method's name and key technical terms | `search_bohrium_reasoning` + `search_bohrium_lkm` (method terms) + `get_bohrium_paper_graph` on top hit |
| 3 | `temporal-expansion` | Filter to last 12 months; include arXiv pre-prints, concurrent submissions | `search_bohrium_paper` (year_from/year_to = last 12 months) + `search_arxiv` (date-sorted) |

Google Scholar (`search_google_scholar*`) participates ONLY when `session.json.mcp.bohrium_available` is `false` or the LKM tools return `{"error": ...}`.

## Steps

1. Read `.brain/session.json`.
   - Determine `next_round = phases.literature.rounds_completed + 1` (default 0 → next = 1).
   - If `next_round > 3`, print: "All 3 rounds complete. Next: `/3-osp-historian`." and stop.
   - If any earlier round file is missing, resume from that round instead.

2. Read `.brain/raw/01_structured_summary.md`.

2.5. **Optional — LKM paper extraction (query seeding, first invocation only):**
   - Only when `rounds_completed == 0` and the original paper is a PDF at `.brain/input/` (use `session.json.paper.path`), and `.brain/raw/02_lkm_paper_extraction.md` does not yet exist.
   - Flow: `osp-mcp.submit_bohrium_pdf(<pdf path>)` → bounded `osp-mcp.wait_bohrium_parse_task` (repeat as needed; wait timeout is not a failure) → `osp-mcp.get_bohrium_parse_result(task_id)` after terminal `succeeded`.
   - Write `.brain/raw/02_lkm_paper_extraction.md` (universal Method / Output / Provenance): Output = addressed problems, open questions, key conclusions of the paper; Provenance = pdf path, task id, `cache_hit`, result cost.
   - **Best-effort only.** If submit fails (paper > 50 pages, > 64 MiB, bohr unavailable, budget), skip and note it in `phases.literature.notes` — never block the rounds on this.
   - On later invocations, read the extraction file if present and use it as a query seed source.

3. Run the **next pending round only**:
   - Activate the `osp-literature-review-agent` skill for that round.
   - The skill searches using **all available retrieval tools** (`search_bohrium_lkm`, `search_bohrium_reasoning`, `search_bohrium_paper`, `search_arxiv`, `search_semantic_scholar`; Google Scholar only as fallback) with **different query formulations**.
   - When `02_lkm_paper_extraction.md` exists, the round's query formulation derives at least one query from the paper's own open questions / conclusions.
   - Write the round file (`02a`, `02b`, or `02c`) using the template at `defaults/round_strategy_template.md`.

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
