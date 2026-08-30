---
description: "OSP Phase 0: Venue lookup, paper detection, criteria scaffolding"
reads: [".brain/session.json"]
writes: [".brain/raw/00_review_guidelines.md", ".brain/raw/05_qa_<slug>.md (per criterion)", ".brain/session.json"]
---

# /0-osp-onboarding — Stage 0: Onboarding

Prepares the review environment. Must run before any other numbered step.

## Activation

Invoke the `osp-orchestrator` skill (no domain persona needed for this step).

## Steps

### 1. Read session state

- Read `.brain/session.json`. If missing, run `scripts/init_brain.sh` first or initialize a default per the v2 schema.
- If `phases.onboarding.status == "completed"` and `qa_criteria` is non-empty, ask the user whether to re-run (which would overwrite `00_review_guidelines.md` and any pre-scaffolded `05_qa_*.md` files). If they decline, exit.

### 2. Locate the paper and ensure a readable text version

- Check `.brain/input/` for a paper file. Common extensions: `.pdf`, `.md`, `.tex`, `.docx`.
- If empty, ask the user where the paper is. Help them collaboratively — accept any path, then copy the file into `.brain/input/`.
- **Always produce `.brain/input/paper.md`** (the canonical readable form):
  - If the original is `.md`, ensure it's named `paper.md` (rename if necessary).
  - If the original is `.pdf` / `.docx` / `.tex`, attempt conversion with the `markitdown` MCP tool (`markitdown.convert`). Save output to `.brain/input/paper.md`.
  - If `markitdown` is unavailable, **do not silently advance**. Tell the user explicitly that downstream phases require `paper.md` and offer two options: (a) install markitdown (`uvx markitdown-mcp`), or (b) provide a manual markdown conversion. Pause until one is in place.
- Save `paper.path` (original) and `paper.parsed_path` (the canonical `.brain/input/paper.md`) into `session.json`.

### 3. Identify the venue

- **Always ask the user explicitly**, even if the paper's title page, header, or metadata already shows a venue. Do not auto-fill from the paper.
- Use your tool's native ask/input mechanism if one is available (e.g. ask_user, an interactive prompt, or a confirmation dialog). If no native ask exists, print the question and wait for a reply before continuing.
- Ask: "Which venue or journal are you reviewing for? (e.g. ICLR 2026, NeurIPS 2025, Nature Machine Intelligence, arXiv-only)"
- If the paper appears to list a venue, show what you found and ask the user to confirm or correct it: "The paper mentions [venue]. Is that the submission venue you want to review against, or a different one?"
- Save `venue.name` and `venue.year` to `session.json`.

### 3.5. Identify the paper's review mode and field

OSP's default criteria were originally derived from ML/NLP/CS conference review forms. Many papers reviewed with OSP are not empirical ML papers — they may be pure mathematical proofs, theoretical physics derivations, or other non-experimental work. Applying baseline/dataset/ablation-style criteria to a proof paper produces forced, low-value output. Detect this **before** picking the generic fallback guidelines.

- Read the paper (title, abstract, and structure already visible from locating it in step 2) and classify:
  - `paper.review_mode`: one of `theoretical` (the core contribution is a proof, derivation, or formal result — even if it includes some numerical/computational validation of that result), `empirical` (the core contribution is measured via experiments, datasets, benchmarks, or ablations), or `other` (neither fits — e.g. a survey, a dataset-release paper, a position paper).
  - `paper.field`: a short free-text label for the discipline (e.g. `math`, `physics`, `cs-ml`, `biology`, `chemistry`). Best-effort; do not block on this.
- This is a judgment call, not an interactive question — infer it from the paper itself. If genuinely ambiguous (e.g. a theory paper with a substantial empirical section), prefer `empirical` only if the empirical results are the paper's primary claim; otherwise use `theoretical`.
- Save `paper.review_mode` and `paper.field` to `session.json`.
- This classification only changes which **generic fallback** guidelines get used in step 4, and how the Summary, Baseline Scout, and Reviewer personas frame their output later. It has no effect when a venue-specific or user-provided guideline is available — venue instructions always take precedence.

### 4. Retrieve venue review guidelines (fallback chain)

Try in order, stop at the first that succeeds:

1. **Web search** for the venue's official review form / reviewer instructions / scoring rubric. Use queries like `"<venue> <year> reviewer guidelines"`, `"<venue> review form"`, `"<venue> reviewer checklist"`.
2. **Ask the user** to paste guidelines if web search came up empty or returned irrelevant content.
3. **Generic fallback:** based on `paper.review_mode` from step 3.5, copy either `extensions/_shared/defaults/generic_review_guidelines.md` (for `empirical` or `other`) or `extensions/_shared/defaults/generic_review_guidelines_theoretical.md` (for `theoretical`) — or its synced equivalent in your tool's `defaults/` directory — into `.brain/raw/00_review_guidelines.md`.

Set `venue.criteria_source` in `session.json` to `"web"`, `"user"`, or `"generic"` accordingly. Set `venue.source_url` if web-sourced. When the generic fallback is used, note which variant (`generic` or `generic-theoretical`) in `venue.criteria_source` notes so downstream personas and human readers can see which one applied.

### 5. Write `00_review_guidelines.md`

Write the retrieved/provided/generic guidelines to `.brain/raw/00_review_guidelines.md` using the universal artifact structure (Method / Output / Provenance):

- **Method:** how the guidelines were sourced (web search query, user paste, generic fallback).
- **Output:** the actual guidelines content. Include the venue's scoring rubric, the required review sections, and the criteria the venue uses.
- **Provenance:** source URL or "user-provided" or "generic fallback".

### 6. Extract criteria and populate `qa_criteria[]`

Parse the guidelines to extract the evaluation criteria. Each criterion becomes an entry in `session.json.qa_criteria`:

```json
{
  "slug": "novelty",
  "label": "Novelty & Originality",
  "definition": "<one-paragraph definition from the guidelines>"
}
```

If the venue uses 7 criteria, you produce 7 entries. If 3, you produce 3. The number is venue-driven, not fixed.

### 7. Pre-scaffold empty Q&A files

For each criterion in `qa_criteria[]`, create `.brain/raw/05_qa_<slug>.md` from the template at `defaults/qa_pair_template.md` (or the synced equivalent). Pre-fill:
- The criterion label and definition in the header
- Empty `### Q1` … `### Q<N>` placeholders where N = `qa_pairs_per_criterion` (from session.json, default 2)

This is a **structural nudge**: when the Query Agent runs in Phase 5, the empty file is already on disk, signaling the required pair count.

### 8. Update `session.json`

- `phases.onboarding.status = "completed"`
- `phases.onboarding.completed_at = <now ISO 8601 UTC>`
- `phases.onboarding.notes = "Venue: <name>; review mode: <theoretical|empirical|other>; field: <field>; criteria: <N>; paper: <path>; guidelines source: <web|user|generic>"`
- `resume_from = "summary"`

### 9. User-facing report

Print:
```
── Onboarding complete ───────────────────────────────────
Venue: <name>  |  Criteria: <N>  |  Guidelines: <web|user|generic>
Review mode: <theoretical|empirical|other>  |  Field: <field>
Paper located and text-version confirmed.
↳ .brain/raw/00_review_guidelines.md
↳ .brain/raw/05_qa_<slug>.md  (pre-scaffolded for each criterion)
↳ .brain/session.json  (qa_pairs_per_criterion: <N>)
Next: /1-osp-summary
─────────────────────────────────────────────────────────
```
