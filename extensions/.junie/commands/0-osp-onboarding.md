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

### 1.5. Detect Bohrium LKM availability

Bohrium LKM is the Literature phase's primary broad-coverage retrieval source; Google Scholar is the fallback. Record which one is available so downstream phases know what to expect.

- Probe the environment (best-effort, if shell commands are possible): `command -v bohr`. If present, optionally confirm login with `bohr auth status` (expect `ok: true` / `logged_in: true`).
- Set `session.json.mcp.bohrium_available = true` when the `bohr` CLI is installed and logged in; otherwise `false`. Never read, print, or log any credential — the CLI stores its own login.
- If the probe cannot run, leave `bohrium_available` at its default (`false`); the Literature agent will attempt LKM tools anyway and fall back to Google Scholar on `{"error": ...}` from the MCP layer.

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
- **Exception — the caller already answered.** If `venue.name` is already non-empty in `session.json`, use it and do not ask; a batch caller set it deliberately. Note in `phases.onboarding.notes` that the venue came from `session.json` rather than from confirmation, so a reader can tell an assumed value from a confirmed one. Never block waiting for an answer that will not come — see "Unattended runs" in the OSP rules.
- Use your tool's native ask/input mechanism if one is available (e.g. ask_user, an interactive prompt, or a confirmation dialog). If no native ask exists, print the question and wait for a reply before continuing.
- Ask: "Which venue or journal are you reviewing for? (e.g. ICLR 2026, NeurIPS 2025, Nature Machine Intelligence, arXiv-only)"
- If the paper appears to list a venue, show what you found and ask the user to confirm or correct it: "The paper mentions [venue]. Is that the submission venue you want to review against, or a different one?"
- Save `venue.name` and `venue.year` to `session.json`.

### 3.5. Select the domain profile

OSP's default criteria were derived from ML/NLP/CS conference review forms. Most
papers reviewed with OSP are not empirical ML papers, and asking a proof paper
about baselines and datasets produces forced, low-value output. The **domain
profile** supplies the discipline-specific half of the review.

Venue and domain are **orthogonal layers, and both always apply**:

| Layer | Decides |
|---|---|
| Venue (steps 4–6) | which criteria exist, the rubric, the output format, and which criteria gate the decision |
| Domain (this step) | what counts as evidence, what "nearest prior work" means, which verifiability checks apply, which questions must never be asked |

A venue rubric never removes a domain's anti-pattern list. A domain profile
never overrides a venue's criteria or gating.

Steps:

1. Read `defaults/domains/_index.md` (or its synced equivalent in your tool's
   `defaults/` directory) for the routing table.
2. From the paper's title, abstract, structure, and reference list, pick
   **exactly one** profile. Route on the paper's *method of justification*, not
   its subject matter — a paper proving a theorem about a biological network is
   `math`, not `biology`.
3. Read that one profile file. Do not read the others.
4. **Hybrid check.** If the paper's core claim is formal *and* it reports
   computed values, a computational search, simulation output, or any claim of
   agreement between an analytic and a computed result, **also** read
   `defaults/domains/_numerical-slice.md`. One reported number is enough to
   trigger this. Do not choose between the two files — read both.
5. Also set `paper.review_mode` to `theoretical`, `empirical`, or `other`. This
   remains in the schema because step 4's generic fallback branches on it; the
   profile, not this flag, now carries the domain behaviour.

Save to `session.json`:

- `paper.domain_profile` — the profile filename without extension (e.g. `math`)
- `paper.numerical_slice` — `true` if the overlay was read, else `false`
- `paper.field` — the free-text discipline label, usually the same as the profile name
- `paper.review_mode` — as above

This is a judgement call, not an interactive question. If genuinely ambiguous,
prefer the profile whose §02 detection cues match more of the paper's actual
structure, and say which cues decided it in the phase notes.

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
  "definition": "<one-paragraph definition from the guidelines>",
  "gating": true,
  "gating_source": "venue"
}
```

`gating` records whether a poor score on this criterion may on its own justify
rejection. **Without this field the pipeline conflates "worth asking about" with
"worth penalising."** The distinction is real and venue-specific: some journals
collect a significance judgement on their review form while explicitly refusing
to reject on it, while others treat "why does this not belong in a good
specialist journal instead" as a hard bar. The same rating implies opposite
outcomes at those two venues.

Set `gating` in this order of precedence:

1. **The venue says so** — the review form marks a criterion as a rejection
   ground, or explicitly says it is not one. Set `gating_source` to `"venue"`.
2. **The domain profile's §03 default** — its criterion instantiation table
   carries a default for each slug. Set `gating_source` to `"domain-default"`.
3. **Unknown** — set `gating` to `false` and `gating_source` to `"unset"`. A
   criterion that cannot be shown to gate does not gate.

`significance` is the criterion this matters most for. Its default in every
domain profile is `venue-set` precisely because it must not be inferred from the
discipline — doing so introduces a systematic bias across every paper in that
field.

**The criteria list is driven by the venue and the paper, never by the profile.**
The domain profile's §03 table says how a criterion is *read* in this field; it
is not the list. Derive the criteria from `00_review_guidelines.md`, then **add
a paper-specific criterion whenever the paper warrants one** — a
completeness-and-scope criterion for a classification theorem, a
numerical-validity criterion for a computational claim, a data-availability
criterion for a resource paper. A criterion with no row in §03 is perfectly
valid; instantiate it by reading the profile's §04 and §06.

**Name added criteria from the canonical list.** `defaults/review_vocabulary.md`
carries slugs and labels for the criteria that recur across papers. If the
criterion you are adding matches one, use that slug and label verbatim; coin a
new one only when none fits. One batch produced `completeness-scope`,
`scope-and-quantification`, and `scope-and-assumptions` for the same concern,
which makes scores incomparable across papers — the concern is real each time,
but three names for it means a corpus can never be summarised on that dimension.

Do not normalise every paper in a field onto the same five slugs. A measured
case: a fixed five-criterion list dropped a completeness criterion, and with it
a correct finding that a classification theorem covered only the finite-outcome
case. The adaptive list had caught it; the fixed list did not. Reusing a
canonical *name* is not the same as reusing a fixed *list* — take the name when
it fits, and still add the criterion only when the paper earns it.

If the venue uses 7 criteria, you produce 7 entries. If 3, you produce 3, plus
any the paper itself demands. The number is venue- and paper-driven, not fixed.

### 7. Pre-scaffold empty Q&A files

For each criterion in `qa_criteria[]`, create `.brain/raw/05_qa_<slug>.md` from the template at `defaults/qa_pair_template.md` (or the synced equivalent). Pre-fill:
- The criterion label and definition in the header
- Empty `### Q1` … `### Q<N>` placeholders where N = `qa_pairs_per_criterion` (from session.json, default 2)

This is a **structural nudge**: when the Query Agent runs in Phase 5, the empty file is already on disk, signaling the required pair count.

### 8. Update `session.json`

- `phases.onboarding.status = "completed"`
- `phases.onboarding.completed_at = <now ISO 8601 UTC>`
- `phases.onboarding.notes = "Venue: <name>; domain profile: <name><+numerical-slice if applied>; review mode: <theoretical|empirical|other>; criteria: <N> (<G> gating); paper: <path>; guidelines source: <web|user|generic>"`
- `resume_from = "summary"`

### 9. User-facing report

Print:
```
── Onboarding complete ───────────────────────────────────
Venue: <name>  |  Criteria: <N> (<G> gating)  |  Guidelines: <web|user|generic>
Domain profile: <name><, + numerical-slice overlay>
Review mode: <theoretical|empirical|other>
Paper located and text-version confirmed.
Bohrium LKM: <available — primary literature source | unavailable — Google Scholar fallback>
↳ .brain/raw/00_review_guidelines.md
↳ .brain/raw/05_qa_<slug>.md  (pre-scaffolded for each criterion)
↳ .brain/session.json  (qa_pairs_per_criterion: <N>)
Next: /1-osp-summary
─────────────────────────────────────────────────────────
```
