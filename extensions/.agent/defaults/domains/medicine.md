# Domain Profile — Medicine / Clinical Research

## 01. Front matter

```yaml
domain: medicine
aliases: [clinical, clinical-trials, epidemiology, public-health,
          health-outcomes, diagnostics, prognostic-modelling,
          evidence-synthesis]
version: 1
last_verified: 2026-08-30
```

## 02. Detection cues

- Human participants as the unit of analysis, with a described population
- A trial registration identifier, or a review protocol registration
- Section headings "Participants", "Interventions", "Outcomes", "Statistical Analysis"
- A CONSORT-style flow diagram, a PRISMA flow diagram, or a baseline-characteristics table
- Effect estimates reported with confidence intervals; primary and secondary outcomes distinguished
- Ethics approval naming an IRB or research ethics committee, plus a consent statement

**Hybrid:** a paper whose core contribution is a statistical method, validated
on clinical data as illustration, routes to the method's domain plus
`_numerical-slice.md`. A prediction-model paper with clinical intent stays here
even when the modelling is machine learning.

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
| `novelty` | Does this address a question not already settled by existing trials, cohorts, or syntheses? Replication of an important result is a contribution — say so rather than scoring it as unoriginal. | `false` |
| `technical-soundness` | Does the design answer the question asked? Are confounders addressed? Are primary and secondary outcomes pre-specified and analysed as registered? Is **causal language proportionate to the design**? | `true` |
| `clarity` | Is the abstract structured, are effect estimates reported with dispersion, and do the conclusions match the results rather than the hypothesis? | `false` |
| `significance` | Is the effect clinically meaningful, not merely statistically detectable? Would it change practice, guidelines, or standard of care? | venue-set |
| `reproducibility` | Read as **independent verifiability**: are the protocol and statistical analysis plan obtainable, is the registration consistent with what was reported, is individual-level data sharing addressed? | `true` |

Clinical review conventionally separates methodological and statistical
assessment. Where the venue supplies a distinct statistics criterion, treat it
as gating regardless of this table.

## 04. What counts as evidence

Evidence here is an effect estimate produced by a design, in a defined
population. The Summary phase must extract these fields:

| Field | Content |
|---|---|
| `claims` | Each clinical claim, with the table or figure supporting it |
| `design` | Trial, cohort, case-control, cross-sectional, diagnostic accuracy, synthesis |
| `population` | Eligibility criteria, setting, and recruitment period |
| `intervention_exposure` | What was given or observed, including comparator |
| `outcomes` | Primary and secondary outcomes as defined, with measurement timing |
| `registration` | Registry name, identifier, and registration date, or "not stated" |
| `n_flow` | Screened, enrolled, allocated, analysed, and lost to follow-up |
| `effect_estimates` | Point estimates with confidence intervals; absolute and relative where both are reported |
| `analysis_plan` | Pre-specified analysis, handling of missing data, and any deviations |
| `conflicts_funding` | Funding source and declared conflicts |

Record a field as **not stated** when the paper does not supply it. Never
reconstruct a denominator or infer an outcome definition.

## 05. Nearest prior work

The Scout phase hunts for the evidence context the paper sits in:

- Existing trials or cohorts answering the same question, including null results
- Current clinical guidelines or standard of care the comparator should reflect
- Systematic reviews that already synthesise this question
- The registration record itself, compared against the reported outcomes
- Retraction and expression-of-concern notices touching key cited evidence

Frame findings as "this question appears already addressed by / this comparator
differs from current standard of care as described in X" with the citation. A
registered primary outcome differing from the reported one is a finding
regardless of what the literature shows.

## 06. Verifiability checks

Checks operate at **article level**, not sentence level — article-level
aggregation measures materially better than sentence-level extraction on
reporting-checklist corpora, and it matches how a reviewer acts.

| Check | Tier |
|---|---|
| A registration identifier is present, and located where the venue requires it | automatic |
| Flow-diagram numbers are internally consistent (screened ≥ enrolled ≥ analysed; losses reconcile) | automatic |
| Every effect estimate is reported with a confidence interval | automatic |
| Ethics approval and consent statements are present | automatic |
| Funding and conflict-of-interest statements are present | automatic |
| An applicable reporting checklist is cited or supplied | automatic |
| Reported outcomes match the registered outcomes | semi-automatic |
| Registration date precedes enrolment start | semi-automatic |
| Numbers in the abstract match the corresponding results tables | semi-automatic |
| Protocol and statistical analysis plan are obtainable | semi-automatic |
| Randomization method and allocation concealment are adequate | manual |
| Blinding, where claimed, is credible for the outcome measured | manual |
| Confounding is adequately addressed for the causal claim made | manual |
| Missing-data handling is appropriate | manual |
| The clinical interpretation is proportionate to the effect size | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.
Flow-diagram reconciliation is pure arithmetic and the single highest-value
automatic check in this domain — run it first.

## 07. Reporting standards

Standards apply **by study type, not by domain**. Check each trigger; several
may fire at once. Naming the wrong checklist is itself an error.

| If the paper is… | Then check against | Notes |
|---|---|---|
| a randomised controlled trial | CONSORT 2025 | Revised from the 2010 statement, with items added and an Open Science section introduced; do not check a 2025 submission against the 2010 item list |
| an RCT protocol | SPIRIT 2025 | Aligned item-by-item with CONSORT 2025 |
| a trial of an AI or ML intervention | CONSORT-AI extension | Applies **in addition to** the base statement |
| a systematic review or meta-analysis | PRISMA 2020 | Flow arithmetic first; PRISMA-S for the search, where searching is the contribution |
| a scoping review | PRISMA-ScR | An independent standard, not a reduced PRISMA |
| an observational study | STROBE | Several items are worded differently by design subtype — use the right variant |
| a diagnostic-accuracy study | STARD | |
| a prediction-model study, including ML-based | TRIPOD+AI | |
| a case report | CARE | |
| reporting sex or gender | SAGER | |
| releasing individual-level data | the venue's data-sharing policy | Statement presence is automatic; adequacy is not |

Where the venue mandates a checklist and none is supplied, that is a reportable
gap; where no standard applies, say so rather than inventing one. Two policies
hold regardless of study type: authors are expected to retain raw data for a
substantial period after publication, and AI use in preparing or reviewing the
manuscript requires prior journal permission and disclosure.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- Human-subject research without ethics approval or a consent statement
- A prospective trial with no registration, or registered after enrolment began
- The reported primary outcome differs from the registered one, undisclosed
- Causal language for an association from a design that cannot establish causation
- Undisclosed financial conflicts material to the intervention studied
- Selective reporting: registered outcomes collected but not reported
- Undisclosed overlap or duplicate publication of the same participants

## 09. Anti-patterns — never generate these

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "What is the comparator, and does it reflect current standard of care?" |
| "Were ablations performed?" | "Were subgroup and sensitivity analyses pre-specified, and are they interpreted as such?" |
| "Which benchmark datasets were used?" | "What is the study population, and how were participants recruited?" |
| "Are hyperparameters disclosed?" | "Is the statistical analysis plan available, and were deviations from it disclosed?" |
| "Is the model state-of-the-art?" | "Is the effect clinically meaningful, and how does it compare to existing evidence?" |
| "Is the code released?" | "Are the protocol, analysis plan, and individual-level data obtainable?" |
| "What is the training/test split?" | "For a prediction model: was validation internal, temporal, or external — and in whom?" |
| "Is the improvement statistically significant?" | "Is the absolute effect reported alongside the relative one, and is it clinically important?" |
| "How large is the dataset?" | "Was the sample size pre-specified, and what effect was it powered to detect?" |

Do not merely rephrase a forbidden question in domain vocabulary. If a question
has no meaningful form here, drop it and use the criterion's remaining budget
on a different angle.

## 10. Seed questions

- `technical-soundness` — "The registered primary outcome is X; the paper reports Y as primary. Is the change disclosed and justified?" (look in the registration record and Methods)
- `technical-soundness` — "The design is observational but the Discussion uses causal language. Is that supported?" (look in the Discussion and Limitations)
- `reproducibility` — "Is the statistical analysis plan available, and were any deviations from it reported?" (look in the Methods and supplementary materials)
- `technical-soundness` — "Loss to follow-up is N. How were missing outcomes handled, and was that pre-specified?" (look in the flow diagram and analysis section)
- `significance` — "The relative risk reduction is reported. What is the absolute risk difference in this population?" (look in the results tables)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates the design
and its execution, not the importance of the condition studied: an important
question addressed by an under-powered single-centre study is `incomplete`,
not `solid`. Where a required checklist item is simply absent, prefer
`insufficient evidence to judge` over `concern` — a reporting gap is raised as
a gap. A registration–outcome mismatch is the exception: it is a finding on its
own evidence.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Confidentiality, conflict handling, raw-data retention, prior-permission requirement for AI use | ICMJE Recommendations, submission and peer-review responsibilities | 2026-08-30 |
| Mandatory EQUATOR checklists, registration details in the abstract, SAP submission, graded evidence levels | JAMA instructions for authors | 2026-08-30 |
| 2025 revision of the trial-reporting statement, with added items and an Open Science section | CONSORT 2025 statement (BMJ) | 2026-08-30 |
| Systematic-review reporting items and extensions | PRISMA statement site | 2026-08-30 |
| Observational-study items and design-specific wording | STROBE statement site | 2026-08-30 |
| Multiple review models, minimum two reviews, provenance labelling | BMJ Author Hub peer-review policy pages | 2026-08-30 |
| Article-level checklist extraction outperforms sentence-level | Published CONSORT/SPIRIT text-mining evaluations | 2026-08-30 |

**Access failures — not established from a primary source:**

- BMJ reviewer-resources pages returned 403. Patient-and-public-involvement
  requirements and the statistical-review workflow are **not confirmed**.
- The Lancet's reviewer-facing pages returned 403 site-wide. Secondary sources
  describe subject reviewers plus a dedicated statistical reviewer and a
  protocol/SAP hand-off. **Unverified** — do not cite it as that journal's
  policy, and do not generalise it to other journals.

**Standing caution:** an evidence-synthesis guideline-selection tool still
linked from a major reporting-guideline network has lapsed and its domain is
now held by an unrelated party. Verify any checklist-selection tool resolves
before routing users to it; prefer the network's own decision tree.
