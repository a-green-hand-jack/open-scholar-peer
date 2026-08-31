# Review Output Vocabulary

Shared across every domain profile. Read once per review.

Two independent problems motivate this file. Both are measured, not
hypothetical:

- LLM reviewers report near-constant high confidence (typically 8–9 out of 10)
  that carries **no relationship to their actual error rate**, and skew
  systematically toward acceptance.
- LLM reviewers routinely flag an integrity or soundness concern and then
  assign an acceptance-level score anyway — the concern and the recommendation
  are not connected.

A free-form numeric score invites both. Closed, ordered vocabularies with an
explicit "not enough evidence" position do not.

## Axis 1 — Significance (5 levels)

Adapted from eLife's assessment vocabulary. Reports how much the result would
matter **if the evidence holds**. Independent of Axis 2.

| Level | Meaning |
|---|---|
| `landmark` | Profound implications; likely to exert widespread influence beyond the field |
| `fundamental` | Substantially advances understanding of a major research question |
| `important` | Implications extending beyond a single subfield |
| `valuable` | Implications within a subfield |
| `useful` | Focused importance and scope |

**Significance is venue-gated, not domain-gated.** Whether a low significance
rating may justify rejection is set by the venue, and the same rating implies
opposite outcomes at different venues: some journals collect a significance
judgement while explicitly refusing to reject on it, others treat "why does
this not belong in a good specialist journal instead" as a hard bar. Read the
`gating` value from `session.json.qa_criteria[]`; never infer it from the
domain.

## Axis 2 — Strength of evidence (6 levels)

Reports how well the paper's own evidence supports its own claims. Independent
of Axis 1 — a `useful` result can be `exceptional`ly supported, and a
`landmark` claim can be `inadequate`ly supported.

| Level | Meaning |
|---|---|
| `exceptional` | Sets a new methodological standard for the field |
| `compelling` | More rigorous than the current state of the art |
| `convincing` | Appropriate, validated methodology in line with the state of the art |
| `solid` | Broadly supports the claims, with only minor weaknesses |
| `incomplete` | Supports the claims only partially |
| `inadequate` | Does not support the primary claims |

The domain profile's §04 defines what "evidence" means here. In a proof paper
this axis rates the argument, not experiments.

## Per-finding assessment (ordered, with a legitimate middle)

Every individual finding — a claimed weakness, a suspected gap, a novelty
challenge — takes exactly one value:

```
explicit flaw
strong concern
concern
minor concern
insufficient evidence to judge     ← legitimate, not a failure
minor support
support
strong support
```

`insufficient evidence to judge` sits deliberately in the middle. It is a
**correct answer**, not an abstention or an error. A comparable ordered scale
with a central "lack of evidence" option was right on 98% of statements for
which no evidence existed. Choosing it when the paper genuinely does not say
is the desired behaviour; guessing toward either end is the failure.

Use it whenever the paper does not contain the information needed to judge, or
retrieval did not return work that settles the question. Do not soften it into
`minor concern`, and do not inflate it into `concern`.

## Aggregation

Do **not** average. Real venues aggregate non-linearly — one journal's
top-tier designation requires two strong endorsements but is revoked outright
if a third report falls below the top two bands.

Rules:

1. Any red line from the profile's §08 is a **blocker**. Blockers are reported
   separately and are never traded off against strengths.
2. Every finding at `explicit flaw` or `strong concern` **must** have a
   traceable consequence in the final recommendation. If the recommendation
   does not change, state explicitly why the finding does not affect it. An
   unexplained gap between a flagged concern and a favourable recommendation
   is the single most common failure of automated review and is not acceptable
   output.
3. Report both axes. Never collapse them into one number.
4. Non-gating criteria inform the write-up but do not move the recommendation.

## Confidence

Do not emit a numeric confidence score. Instead state, in one sentence, **what
was not checked** — the parts of the argument not verified, the claims not
traced to retrieved literature, the tooling that was unavailable. A list of
what remains unverified is actionable; a number that is always 4/5 is not.

## What must never be claimed

Never state that a proof is correct, that a result is verified, or that an
experiment is sound. Models judging proof correctness reach a balanced F1 of
roughly 65, and their errors run in one direction: **accepting flawed proofs**.
For context on the human ceiling, a twelve-referee panel spent four years on a
single famous proof and concluded it was "99% certain" while recording that
they could not certify correctness and never would.

Frame every such observation as a **verification agenda** — what a human expert
should check, and why that step is load-bearing — never as a verdict.
