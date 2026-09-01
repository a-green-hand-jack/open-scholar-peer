# Domain Profile — Computer Science / Machine Learning

## 01. Front matter

```yaml
domain: cs-ml
aliases: [machine-learning, deep-learning, nlp, computer-vision, ml-systems,
          reinforcement-learning, information-retrieval, hci-systems,
          software-engineering, computer-science]
version: 1
last_verified: 2026-08-30
```

**This profile is a peer of the others, not the default.** OSP's original
criteria were derived from ML conference review forms, which is precisely why
every other profile in this directory exists. Route here only when the paper's
primary contribution is genuinely a CS/ML method, model, system, or empirical
result — never as a fallback. `_generic.md` is the fallback.

## 02. Detection cues

- arXiv primary category under `cs.LG`, `cs.CL`, `cs.CV`, `cs.AI`, `cs.SE`, `cs.IR`, `stat.ML`
- A results table with named benchmarks as rows or columns
- Reported metrics: accuracy, F1, BLEU, mAP, perplexity, latency, throughput
- Sections named "Experiments", "Ablation Study", "Implementation Details"
- A checklist appended to the submission (conference requirement)
- References dominated by NeurIPS, ICML, ICLR, ACL, CVPR proceedings

**Hybrid:** a paper proving a learning-theoretic bound and validating it
empirically is `math.md` plus `_numerical-slice.md` when the theorem is the
contribution, and this profile when the empirical result is the contribution.
Decide by which half the paper would lose the most from having removed.

## 03. Criterion instantiation

How this domain reads the criteria the venue supplied. `gating` is the
**default** only — a venue's own gating always wins.

**This table is a lens, not the criteria list.** It says how a criterion is
read in this field. It does not decide which criteria exist, and it does not
cap them at these rows. Keep every criterion the venue's guidelines define,
and add a paper-specific criterion whenever the paper warrants one — a
completeness-and-scope criterion for a classification theorem, a
numerical-validity criterion for a computational claim, a data-availability
criterion for a resource paper. A criterion with no row below is instantiated
by reading it the way this field's §04 and §06 read evidence and verification.

Collapsing every paper in a field onto a fixed five rows trades away exactly
the paper-specific critique a referee exists to provide. That failure has been
observed: a fixed list dropped a completeness criterion, and with it a correct
finding that a classification theorem covered only the finite case.

| Criterion slug | What it means here | Default gating |
|---|---|---|
| `novelty` | Is the method, framing, dataset, or analysis substantively new? Concurrent work is common in this field and its existence is not by itself a novelty defect. | `true` |
| `technical-soundness` | Do the experiments support the claims actually made? Are baselines tuned with comparable effort to the proposed method? Are theoretical claims proved rather than asserted? | `true` |
| `clarity` | Can the method be implemented from the description? Do the equations match the released implementation where one exists? | `false` |
| `significance` | Would this change practice, enable new research, or shift understanding? Note that some venues separate this from soundness explicitly and treat the two as orthogonal axes. | venue-set |
| `reproducibility` | Are code, data, hyperparameters, seeds, and compute disclosed sufficiently to re-run? Distinguish *artifact availability* from *result verification* — see §07. | `false` |

### 0–5 anchors

The band semantics in `../review_vocabulary.md` say what a 2 or a 4 means in
general. These say what it means *here*. Quote the assigned band in the score
table's third column.

**`novelty`**
`0` the contribution already exists in work the paper cites ·
`1` a reimplementation or minor reparameterisation of a published method ·
`2` a routine combination of known components with no new insight into why it works ·
`3` a genuine new idea whose advance over the nearest prior method is narrow ·
`4` a new method, analysis, or resource others will build on ·
`5` reframes how the problem is approached, not just how well it is solved.
Note: **absence of a comparison to the current best result is not by itself a novelty defect** — ICLR states plainly that missing SOTA is not grounds for rejection. Score the idea, not the leaderboard position.

**`technical-soundness`**
`0` the experiments cannot support the claim made — wrong task, leaked test data, or a metric that does not measure the claimed property ·
`1` comparisons are unfair in a way that drives the result: baselines untuned while the method is tuned, or different data or budget across arms ·
`2` single runs reported as differences with no seeds, variance, or significance treatment ·
`3` setup supports the claim; some choices unjustified and a few conclusions reach past what was measured ·
`4` sound design with appropriate controls; minor gaps in ablation coverage ·
`5` claims and evidence match exactly, with variance reported and the decisive components isolated

**`clarity`**
`0` the method cannot be understood from the text ·
`1` the described method and the reported setup contradict each other ·
`2` reimplementation would require guessing central design decisions ·
`3` followable; some hyperparameters and preprocessing steps left to the appendix or omitted ·
`4` clear and complete; presentation improvements only ·
`5` method, setup, and results are stated precisely enough to reimplement from the paper alone

**`significance`**
`0` the problem is already solved and the paper does not acknowledge it ·
`1` improvement is within noise of existing methods ·
`2` narrow gain on one benchmark with no evidence of transfer ·
`3` a real advance within its subarea ·
`4` changes what practitioners would choose for this task, or enables work that was not previously feasible ·
`5` shifts how the community frames the problem

**`reproducibility`**
`0` no code, no data, and insufficient description to attempt a repeat ·
`1` the required checklist is absent entirely — under NeurIPS rules that is a desk-reject condition in itself, independent of what the answers would have been ·
`2` artifacts are promised but not in an archival repository with a DOI (a personal homepage does not satisfy ACM `Available`), or seeds, versions, and compute are undisclosed ·
`3` code and data available and runnable, with environment details thin ·
`4` meets ACM `Functional`: artifacts are complete, documented, and exercisable ·
`5` meets ACM `Reusable`: artifacts are usable beyond reproducing this paper, with the distinction between *Reproduced* (using the authors' artifact) and *Replicated* (without it) respected in what the paper claims.
Note: a checklist item answered "no" is **not** itself a defect — NeurIPS instructs reviewers not to penalise honest disclosure of limitations. Score the disclosure, not the answer.


## 04. What counts as evidence

The Summary phase must extract these fields:

| Field | Content |
|---|---|
| `claims` | Each empirical claim as stated, with the table or figure that supports it |
| `datasets` | Every dataset used, with split and version |
| `baselines` | Every method compared against, with its source (reimplemented / reported / official) |
| `metrics` | Which metrics are reported, and which are omitted relative to the benchmark convention |
| `headline_numbers` | Every quantitative result the paper foregrounds, with its uncertainty if given |
| `variance_reporting` | Seeds, run counts, error bars, or `single run` when that is what was done |
| `ablations` | Which components were ablated, and which were not |
| `compute` | Hardware, training time, and cost, or `not stated` |
| `artifact_availability` | Code and data location, and whether it is an archival repository with a DOI |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value, and never assume a standard split was used.

## 05. Nearest prior work

The Scout phase hunts for **methods and results the paper should have engaged
with**:

- A stronger published result on the same benchmark under the same protocol
- A simpler method reported to achieve comparable results
- Concurrent work with substantially the same idea
- A prior negative result suggesting the approach has been tried
- A benchmark or evaluation protocol the field has moved to that the paper does not use

**A missing state-of-the-art comparison is not by itself grounds for
rejection** — at least one major conference states this explicitly in its
reviewer guidance. Report the gap and let the venue's criteria decide its
weight; do not convert it into a recommendation on your own authority.

## 06. Verifiability checks

| Check | Tier |
|---|---|
| Every number in the abstract appears in a table or figure in the body | automatic |
| Every dataset named in the text appears in the experimental setup | automatic |
| Code and data links resolve, and point to an archival location rather than a personal homepage | automatic |
| Every claim of statistical significance names the test used | automatic |
| Reported improvements exceed the reported variance, where variance is given | semi-automatic |
| Baselines are cited to a source (official numbers, reimplementation, or reported) | semi-automatic |
| Baselines received tuning effort comparable to the proposed method | manual |
| The experimental design supports the causal claim being made | manual |
| Ablations isolate the component they claim to isolate | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.

## 07. Reporting standards

| If the paper… | Then check against |
|---|---|
| is submitted to a venue with a submission checklist | The checklist's items. Note the mechanism: answering "no" or "n/a" to a checklist item **is not itself grounds for rejection**, and reviewers are instructed not to penalize honest disclosure of limitations — but an entirely absent checklist is a desk-reject condition at some venues |
| releases artifacts | The three-badge scheme: **Available** (deposited in an archival repository with a DOI — a personal homepage does not qualify), **Functional**, **Reusable** |
| claims results were confirmed independently | The two-term distinction: **Reproduced** means a third party obtained the result *using* the authors' artifacts; **Replicated** means a third party obtained it *without* them. These are not interchangeable |

The badge scheme's value here is that it splits "the authors released code" from
"the result was verified" — two claims routinely conflated in review. Keep them
separate in the write-up.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- A headline number in the abstract has no corresponding entry in the body
- Test-set results were used to select the method or its hyperparameters
- A dataset is used in violation of its stated license or terms
- Human-subjects data is used with no ethics-board statement where one is required
- The paper's core content is substantially identical to the authors' undisclosed prior publication
- Results are reported for a method the paper does not describe sufficiently to identify

## 09. Anti-patterns — never generate these

This profile still needs an anti-pattern list. The failure mode here is not
importing foreign assumptions but applying the field's own conventions as though
they were universal requirements.

| Never ask | Ask instead |
|---|---|
| "Why is there no comparison to the state of the art?" *(as grounds for rejection)* | "Which published result on this benchmark is strongest, and what would comparing against it change?" |
| "Why were no ablations performed?" *(of a paper making no compositional claim)* | "The method has components A and B. Does the paper claim both are necessary, and if so what supports that?" |
| "Why is the code not released?" *(of a paper with no implementable artifact)* | "What in the description is insufficient to reimplement the method?" |
| "Why was this not evaluated on a larger model?" | "Does the paper claim its finding scales, and is that claim supported by what was run?" |
| "Is this novel?" | "Reference [X] proposes a similar mechanism. What distinguishes this contribution?" |
| "Why no theoretical analysis?" *(of a purely empirical paper)* | "Does the paper make any claim that requires proof rather than measurement?" |
| "The improvement is small." | "Is the improvement larger than the reported run-to-run variance, and is variance reported at all?" |
| "Why no human evaluation?" *(reflexively)* | "Does the metric used actually measure the property claimed, and is that established?" |

The pattern across these: **do not treat a field convention as a requirement the
paper must justify departing from.** Ask what the paper claims and whether the
evidence matches, not whether the paper resembles a typical paper.

## 10. Seed questions

- `technical-soundness` — "Table N reports a gain of X. Is variance across seeds reported, and does the gain exceed it?" (look in the results table and its caption)
- `technical-soundness` — "Baseline B is reported at value V. Is that number from the original paper, a reimplementation, or a re-run — and was it tuned?" (look in the experimental setup)
- `reproducibility` — "Are hyperparameters, seeds, and compute given for both the proposed method and the baselines, or only the former?" (look in implementation details and appendix)
- `novelty` — "Reference [X] appears to propose a closely related mechanism. What distinguishes this work?" (look in related work)
- `clarity` — "Equation N and the described algorithm appear to differ in the normalization term. Which is correct?" (look across method section and pseudocode)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates the
**experimental support for the claims made**, not the size of the improvement:
a modest, well-measured result with reported variance can be `convincing`,
while a large single-seed gain is at best `incomplete`.

Domain-specific note: some venues in this field already separate soundness from
significance as explicitly orthogonal scores. Where they do, that separation
maps directly onto the two axes in the shared vocabulary — do not collapse
them.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| 16-item submission checklist; "no"/"n/a" not grounds for rejection; reviewers not to penalize honest limitations; absent checklist is a desk-reject condition | NeurIPS Paper Checklist guidance | 2026-08-30 |
| A missing state-of-the-art comparison is not itself grounds for rejection | ICLR 2026 Reviewer Guide | 2026-08-30 |
| Soundness and excitement scored as orthogonal axes | ACL Rolling Review review form | 2026-08-30 |
| Available / Functional / Reusable badges; archival repository with DOI required, personal homepage insufficient; Reproduced vs Replicated distinction | ACM Artifact Review and Badging v1.1 | 2026-08-30 |

**Not established from a primary source:** the red lines in §08 are assembled
from general venue policy and community norms rather than from a single
authoritative checklist; individual venues differ on which are desk-reject
conditions versus review-stage findings. Treat §03 gating defaults as
conventions, not policy.
