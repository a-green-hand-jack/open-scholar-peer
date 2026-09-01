---
description: "OSP Phase 4: Adversarial audit for the closest prior work the authors failed to engage with"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md", ".brain/raw/02_retrieved_literature.md"]
writes: [".brain/raw/04_missing_baselines.md", ".brain/session.json"]
---

# /4-osp-baseline-scout — Adversarial Prior-Work Audit

Acts as an adversarial auditor identifying the closest prior work the authors
should have engaged with but didn't.

**What counts as "closest prior work" is domain-specific.** In an ML paper it is
a missing baseline or benchmark. In a proof paper it is a theorem that already
implies the result, a sharper bound, or a known counterexample. In a synthesis
paper it is a prior route to the same compound. The domain profile's §05 defines
it; this command does not.

The phase name and the artifact filename retain the word "baseline" for
compatibility with existing sessions and archived trails. The framing inside the
artifact follows the profile, not the filename.

## Activation

Invoke the `osp-baseline-scout-agent` skill.

## Prerequisites

- `phases.literature.status == "completed"`. (`historian` is helpful but not strictly required — the Scout operates from the structured summary and the literature corpus.)

## Resource notice

⚠️ Makes ~6-10 API calls. Expect 1-2 minutes.

## Steps

1. Read `.brain/session.json`, `.brain/raw/01_structured_summary.md`, `.brain/raw/02_retrieved_literature.md`.
2. Read the domain profile named by `paper.domain_profile` — **§05 defines what to hunt for**, **§09 defines what must never be reported as missing**. If `paper.numerical_slice` is `true`, also read `defaults/domains/_numerical-slice.md`.
3. Activate the `osp-baseline-scout-agent` skill.
4. The skill identifies the paper's contribution and what the authors actually engaged with, from the structured summary's evidence section.
5. The skill independently searches for the closest competing, superseding, or subsuming work, framed as the profile's §05 prescribes. Tools: `osp-mcp.search_*`, native Web Search.
6. The skill produces a table of gaps with severity ratings (high/medium/low). Every entry must cite a specific retrieved work — an unsupported "they should have compared to something" is not a finding.
7. Write `.brain/raw/04_missing_baselines.md`.
8. Update `session.json`:
   - `phases.baseline_scout.status = "completed"`
   - `phases.baseline_scout.notes = "<N> prior-work gaps (<X> high severity)"`
   - `resume_from = "qa"`

## User-facing report (print after completion)

```
── Prior-Work Audit complete ─────────────────────────────
Domain framing: <profile name>
Found <N> gaps (<X> high severity) against the closest prior work.
↳ .brain/raw/04_missing_baselines.md
Next: /5-osp-qa
──────────────────────────────────────────────────────────
```

Do not print "missing baselines" or "missing datasets" unless the domain profile
actually frames the audit that way. A proof paper finishing this phase and being
told it is missing datasets is the surface symptom of the framing leaking
through the presentation layer.

## Re-run behavior

Re-running overwrites `04_missing_baselines.md`. Warn before doing so.
