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

## Dimension scores (0–5, one per criterion)

Every criterion in `session.json.qa_criteria[]` gets a score from 0 to 5, in a
table in the final review. The table is what makes a weakness cost something:
prose can describe a serious problem and still read as approval, but a 2 cannot
be written as a 4 without a reason someone can check.

**Band semantics** — shared across every dimension. Each domain profile's §03
states what the bands mean for *that* criterion in *that* field; the wording
there wins, and this table is the frame it fills in.

| Score | Meaning |
|---|---|
| 0 | A definite, disqualifying problem on this dimension |
| 1 | Serious defect; needs redoing rather than patching |
| 2 | Clearly deficient; must be revised before the work stands |
| 3 | Adequate, with things worth improving |
| 4 | Good; only minor blemishes |
| 5 | Excellent; at the best standard of the field |

**0 through 2 are real bands and must be used when earned.** Automated reviewers
overestimate systematically and cluster in a narrow range, so a run whose scores
all land in 3–5 is evidence that the anchors were not applied, not evidence that
the papers were uniformly good.

### Required table

```markdown
## Dimension Scores

| Dimension | Score | What this band means here | Why this score | Evidence |
|---|---|---|---|---|
| Technical Soundness | 3/5 | 3 = argument holds, individual steps compressed, edge cases undiscussed | Quantifier exchange in the singular-state compactness argument is not spelled out; the Appendix B estimate cannot be checked without redoing it | `05_qa_technical-soundness.md` Q2; paper §4.3 |
```

Rules for the table:

- One row per criterion in `qa_criteria[]` — no more, no fewer.
- **Column 3 quotes only the band you assigned**, from the profile's §03 anchors.
  Not the whole scale, and not wording you invented. Naming the band forces the
  score to be a judgement against a written standard.
- **Column 5 must point at an artifact** — a `05_qa_*.md` file, a field in
  `01_structured_summary.md`, an entry in `04_missing_baselines.md`, or a
  section of the paper. Your own recollection is not evidence.
- A dimension you could not assess takes `insufficient evidence to judge` in
  column 2 rather than a number, with column 4 saying what was missing.

## Canonical names for recurring criteria

Criteria are venue- and paper-driven, so papers legitimately add dimensions
beyond whatever the venue lists. But three runs in one batch produced
`completeness-scope`, `scope-and-quantification`, and `scope-and-assumptions`
for the same underlying concern. Three names for one thing means scores cannot
be compared across papers: there is no way to say what a corpus scored on scope
when scope appears under three headings.

**When a criterion you are adding matches one below, use that slug and label
verbatim.** Coin a new one only when none fits — and when you do, write it as a
lowercase hyphenated slug naming the concern, not the paper.

| Slug | Label | Add it when |
|---|---|---|
| `scope-completeness` | Scope & Completeness | The formal result covers less than the prose claims — a classification that holds only for finite cases, a theorem stated for a special regime but described generally, an assumption doing more work than the abstract admits |
| `numerical-validity` | Numerical Validity | The paper reports computed values supporting a formal claim, and their instance coverage, precision, or independence from the result is in question |
| `statistical-validity` | Statistical Validity | Inference rests on statistical claims whose design, power, or multiplicity handling needs separate judgement from general soundness |
| `reporting-compliance` | Reporting Compliance | A mandatory reporting standard applies (CONSORT, PRISMA, ARRIVE, STROBE, MDAR, checkCIF) and adherence is separately assessable |
| `data-availability` | Data & Code Availability | The contribution is a dataset, resource, or artifact, so availability is part of the contribution rather than a reproducibility detail |
| `ethics-compliance` | Ethics & Compliance | Human subjects, animal work, dual-use concerns, or consent and approval documentation require separate judgement |

These are **additions**, never replacements: the venue's own criteria always
stay. And this list does not cap the count — a paper needing a dimension none of
these describes should get one.

## Aggregation

Do **not** average. Real venues aggregate non-linearly — one journal's
top-tier designation requires two strong endorsements but is revoked outright
if a third report falls below the top two bands.

Rules:

1. Any red line from the profile's §08 is a **blocker**. Blockers are reported
   separately and are never traded off against strengths.
2. Every finding at `explicit flaw` or `strong concern` **must** have a
   traceable consequence. Exactly two forms are acceptable:
   (a) it lowers the score of the dimension it touches, or
   (b) the recommendation carries an explicit condition naming what must change.

   **"This criterion is non-gating" is not a reason.** It restates a rule
   instead of stating a fact about the paper, and it was observed being used
   exactly that way — a review dismissed two high-severity numerical findings
   with "they do not move the recommendation because numerical validity is
   explicitly non-gating here". A real reason is specific: which claim the
   finding touches, and why the central result does not depend on it.
3. **Gating decides the recommendation; it never suppresses a score.** A
   non-gating criterion with a serious problem still scores 1 or 2. What gating
   controls is whether that score can pull the recommendation down — not
   whether the reader gets to see it.
4. **Any dimension scoring 2 or below makes the recommendation conditional**,
   whether or not the criterion gates. Write
   `<recommendation>, conditional on <what must change>` and name the
   correction. An unconditional positive recommendation alongside a 2 is not
   acceptable output.
5. Report the score table **and** both axes. Never collapse them into one
   number: significance and strength of evidence are orthogonal, and a `useful`
   result can be `exceptional`ly supported.

## Recommendation vocabulary

The recommendation is a closed vocabulary, not free prose. One validation batch
produced `weak accept, conditional on ...`, `Weak accept`, and `Suitable for
dissemination as an arXiv preprint.` for three papers in the same run — three
registers for one field, which cannot be compared or tallied.

**Pick the set by whether the venue actually makes a publication decision.**

**A — the venue decides.** A journal or conference with an editorial process.
Use its own labels if `00_review_guidelines.md` supplies them; otherwise:

```
accept · weak accept · borderline · weak reject · reject
```

**B — the venue makes no decision.** A preprint server such as arXiv, where
moderation is explicitly not peer review and nothing is accepted or rejected.
Judging readiness is honest; issuing a verdict on the venue's behalf is not:

```
ready · ready with minor revisions · needs revision · needs major revision · not ready
```

State which set you used and why, in one clause, at the start of the
justification — e.g. "arXiv runs no acceptance process, so this is a readiness
judgement." Never mix the two sets, and never invent a third label.

**The conditional clause attaches to either set.** With any dimension at 2 or
below, write `<label>, conditional on <what must change>`. The label itself
still comes from the list; `conditional on` is a suffix, not a new label.

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
