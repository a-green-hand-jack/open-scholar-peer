# Domain Profile — Generic Fallback

## 01. Front matter

```yaml
domain: _generic
aliases: [other, unknown, cross-disciplinary, interdisciplinary,
          social-science, economics, humanities, earth-science, engineering]
version: 1
last_verified: 2026-08-30
```

**This is the fallback, not a default.** Route here only when no other profile
in this directory fits, or when the paper is genuinely cross-cutting. If a
specific profile applies, use it — this file is deliberately weaker than any of
them, because it cannot assume what evidence looks like.

## 02. Detection cues

This profile is selected by *exclusion*: no other profile's cues matched, or
several matched with none dominant. Common cases:

- Social science, economics, education, law, or humanities papers
- Earth, environmental, or climate science
- Engineering papers that are neither CS/ML nor physics
- Survey, position, dataset-release, benchmark, or replication papers
- Genuinely interdisciplinary work with no dominant methodology

**Before anything else, classify the paper's mode of justification.** Everything
downstream depends on it, and this profile cannot skip it:

| Evidence type | The paper's central claim is established by… |
|---|---|
| `formal` | A proof, derivation, or formal argument |
| `experimental` | A controlled intervention the authors performed |
| `observational` | Measurement or data collection without intervention |
| `computational` | Simulation, modelling, or analysis of existing data |
| `qualitative` | Interviews, ethnography, case study, textual or archival analysis |
| `corpus` | Construction or analysis of a dataset, corpus, or benchmark |
| `synthesis` | Review, meta-analysis, or systematic synthesis of prior work |
| `position` | Argument, framing, or agenda-setting without new evidence |

Record the classification in the summary. A paper may carry more than one — a
position paper with a small case study is `position` + `qualitative`. Apply the
questions for each type present, weighted by which carries the central claim.
If the central claim is `formal` and a second type supports it quantitatively,
also read `_numerical-slice.md`.

## 03. Criterion instantiation

How this profile reads the criteria the venue supplied. `gating` is the
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
| `novelty` | Is the contribution new relative to the literature the paper situates itself in? Judge against the paper's own claimed field, not against a field you assume. | `true` |
| `technical-soundness` | Does the method of justification actually support the claim being made? This is the only criterion whose instantiation depends entirely on the §02 evidence type. | `true` |
| `clarity` | Is the argument followable, are terms defined, and is the claim stated precisely enough to be assessed? | `false` |
| `significance` | Describe what the contribution would mean if it holds, judged against the paper's own claimed field. | venue-set |

**On significance in this profile specifically:** when the venue supplies no
rubric, do **not** gate on significance — report it and let it inform the
write-up without moving the recommendation. With no venue anchor and no domain
norm to calibrate against, a significance judgement here is not reliable enough
to drive a decision. If the venue does gate on significance, follow the venue.
| `reproducibility` | Read as **independent checkability**: is there enough detail for someone else to assess or repeat the work, by whatever standard this evidence type implies? | `false` |

### 0–5 anchors

The band semantics in `../review_vocabulary.md` say what a 2 or a 4 means in
general. These say what it means *here*. Quote the assigned band in the score
table's third column.

This profile covers papers whose evidence type is not fixed in advance, so every
band is stated **relative to the evidence type the paper itself claims** (§02).
Establish that type first — formal derivation, experiment, observation,
computation, qualitative study, corpus, synthesis, or position — then read the
bands against it. Do not import the expectations of a type the paper is not.

**`novelty`**
`0` the contribution already appears in work the paper cites ·
`1` a restatement of a known result in different vocabulary ·
`2` a routine application of an established approach to an adjacent case ·
`3` genuinely new, with a narrow margin over the nearest prior work ·
`4` resolves a question the field had left open, or supplies a method others will reuse ·
`5` changes how the question itself is posed

**`technical-soundness`**
`0` the method used cannot support the kind of claim being made — a correlational design carrying a causal conclusion, a derivation whose assumptions are violated by its own application ·
`1` a load-bearing step fails on the paper's own terms: an assumption contradicted later, an instrument used outside its stated range ·
`2` the approach is defensible but key justifications are absent and must come from the authors ·
`3` method and claim strength are matched; individual inferences reach slightly past what the evidence supports ·
`4` appropriate throughout, with minor unstated justifications ·
`5` every claim is supported by evidence of the type the claim requires, with limits stated where the evidence stops

**`clarity`**
`0` the argument or procedure cannot be followed ·
`1` internal inconsistency between what is described and what is reported ·
`2` a reader in the field must reconstruct substantial structure to follow it ·
`3` followable, with passages needing rereading ·
`4` clear; wording and organisation improvements only ·
`5` structure and terminology let a reader check each step in turn

**`significance`**
`0` the question is already settled and the paper does not say so ·
`1` the result has no consequence beyond the specific case examined ·
`2` a routine addition to an established line of work ·
`3` closes a real gap within its area ·
`4` matters beyond the immediate subfield ·
`5` would change how the area approaches its central questions

**`reproducibility`**
`0` an independent party could not check the claim from what is provided ·
`1` the materials the paper's own evidence type requires are missing — data for an empirical claim, intermediate steps for a formal one, protocol for an observational one ·
`2` checking is possible in principle but requires guessing substantial undisclosed choices ·
`3` a competent reader could verify with effort, supplying some details themselves ·
`4` supporting material is essentially complete, a few items left implicit ·
`5` everything needed to check the claim independently is disclosed and locatable

Where a mandatory reporting standard applies to the paper's type (see §07), an
absent or hollow checklist caps `reproducibility` at band 2 regardless of what
else is provided.


## 04. What counts as evidence

Extraction is conditional on the §02 classification. Extract the common fields
always, then the fields for each evidence type present.

**Always:**

| Field | Content |
|---|---|
| `claims` | Each central claim as stated |
| `evidence_type` | The §02 classification, with which type carries the central claim |
| `justification_link` | For each claim, what in the paper is offered as support |
| `scope_conditions` | The stated limits of the claim — population, setting, regime, period |

**By evidence type:**

| Type | Additional fields |
|---|---|
| `formal` | `assumptions`, `derivation_steps`, `prior_results_used` |
| `experimental` | `design`, `units_of_analysis`, `n`, `controls`, `randomization`, `outcome_measures` |
| `observational` | `data_source`, `time_window`, `population`, `confounders_addressed`, `attrition` |
| `computational` | `model_or_method`, `parameters`, `software_versions`, `validation_against` |
| `qualitative` | `sampling_strategy`, `n_participants_or_cases`, `analytic_approach`, `saturation_or_stopping_rule` |
| `corpus` | `size`, `provenance`, `annotation_process`, `inter_annotator_agreement`, `license` |
| `synthesis` | `search_strategy`, `databases_and_dates`, `inclusion_criteria`, `n_screened_vs_included` |
| `position` | `argument_structure`, `counterarguments_addressed` |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value, and never fill an experimental field for a paper
that ran no experiment.

## 05. Nearest prior work

The Scout phase hunts for **the closest work in the paper's own claimed field**.
Because the field is uncertain here, anchor the search to the paper's own
references and terminology rather than to an assumed literature:

- Work the paper's own citations point toward but do not engage with
- A prior result making the same claim, in whatever form that field uses
- A prior study with a contradicting finding
- An established method in the paper's field that the paper does not use or justify not using

Frame findings as "this appears related to X — does it anticipate or contradict
the claim?" **Never** report a missing baseline, dataset, or ablation. Those
belong to one specific field and are meaningless here unless §02 says otherwise.

## 06. Verifiability checks

| Check | Tier |
|---|---|
| Every quantitative claim in the abstract appears somewhere in the body | automatic |
| Every claim of statistical significance names the test used | automatic |
| Data and code links, where given, resolve | automatic |
| An ethics-approval statement is present when human or animal subjects are involved | automatic |
| Reported sample sizes are internally consistent across text, tables, and figures | semi-automatic |
| Stated scope conditions match the generality of the claims made | semi-automatic |
| The method of justification is appropriate to the claim | manual |
| Confounders or alternative explanations are adequately addressed | manual |
| The interpretation stays within what the evidence supports | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.

## 07. Reporting standards

No standard applies unconditionally here. **Look one up rather than assuming
one.** The EQUATOR Network maintains a decision tree for selecting the
appropriate reporting guideline by study type:

<https://www.equator-network.org/toolkits/selecting-the-appropriate-reporting-guideline/>

Conditional hooks:

| If the evidence type is… | Then a reporting standard likely applies |
|---|---|
| `synthesis` (systematic review or meta-analysis) | PRISMA 2020, and PRISMA-S for the search strategy |
| `experimental` with human participants | CONSORT 2025 if randomized; otherwise consult the decision tree |
| `observational` | STROBE |
| `experimental` with animals | ARRIVE 2.0 |
| `corpus` with a released dataset | FAIR data principles, and a stated license |
| social-science reporting with no more specific standard | APA Journal Article Reporting Standards (JARS) |

If none applies, say so explicitly in the review rather than leaving the
question unaddressed. "No mandatory reporting standard applies to this paper
type" is a legitimate and useful statement.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- A quantitative claim in the abstract has no support anywhere in the body
- Human or animal subjects are involved with no ethics-approval statement
- A causal claim is made from a design that cannot support causal inference
- Data or materials are used in violation of a stated license or consent condition
- The paper's core content substantially duplicates undisclosed prior work by the same authors
- Plagiarism or duplicate submission

## 09. Anti-patterns — never generate these

**This is the most important section in this profile.** The fallback path is
where review most easily slides back into machine-learning defaults, because no
domain vocabulary is pulling it elsewhere. Every row is a question class that
must not be produced unless the §02 classification specifically licenses it.

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "What is the closest prior claim in this literature, and how does this one differ?" |
| "Were ablations performed?" | "Which components of the argument are load-bearing, and what supports each?" |
| "Which datasets were used?" | "What is the source of the evidence, and how was it obtained?" |
| "Are hyperparameters disclosed?" | "Are the method's parameters and choices stated well enough to be assessed?" |
| "Is the code released?" | "Is there enough detail for an independent reader to check or repeat this?" |
| "Is the improvement statistically significant?" | "Does the paper make a comparative claim, and if so what supports the comparison?" |
| "How does this compare to state of the art?" | "Does this field have an accepted benchmark for such claims, and does the paper engage with it?" |
| "What is the train/test split?" | "How was the evidence partitioned, if partitioning is meaningful for this method?" |
| "Why no experiments?" | "What method of justification does the paper use, and is it appropriate to the claim?" |
| "Why no quantitative evaluation?" *(of qualitative work)* | "Is the sampling strategy and analytic approach appropriate, and is the stopping rule stated?" |

Two rules govern the section. **Classify before questioning** — a question is
admissible only if the §02 evidence type makes it meaningful. And **do not
rephrase a forbidden question into local vocabulary**: if a question has no
meaningful form for this paper, drop it and spend the criterion's remaining
budget on a different angle.

## 10. Seed questions

- `technical-soundness` — "The central claim is C. Which part of the paper is offered as its justification, and is that method capable of establishing C?" (look in the results or argument section)
- `technical-soundness` — "Are the scope conditions stated in the method as broad as the claims made in the abstract?" (compare abstract and limitations)
- `reproducibility` — "What would an independent reader need that the paper does not provide, in order to check this?" (look in methods and supplementary material)
- `novelty` — "Reference [X] from the paper's own bibliography appears closely related. Is the contribution distinguished from it?" (look in related work)
- `clarity` — "Term T is central to the claim. Is it defined precisely enough that the claim can be assessed?" (look in the introduction and definitions)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates support for
the claims **by the standard of the paper's own evidence type**: a qualitative
study is not `incomplete` for lacking statistics, and a position paper is not
`inadequate` for lacking measurement.

Domain-specific constraint: because significance is ungated here absent a venue
rubric (§03), `insufficient evidence to judge` will be the correct per-finding
value more often in this profile than in any other. Use it freely — an honest
"the paper does not say, and retrieval did not settle it" beats a guess, and
guessing toward either end is the failure this vocabulary exists to prevent.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Reporting-guideline selection by study type | EQUATOR Network decision-tree toolkit | 2026-08-30 |
| PRISMA 2020 for systematic reviews and meta-analyses; PRISMA-S for search reporting | PRISMA statement site | 2026-08-30 |
| CONSORT 2025 for randomized trials | CONSORT 2025 statement | 2026-08-30 |
| STROBE for observational studies | STROBE statement site | 2026-08-30 |
| ARRIVE 2.0 for animal research | ARRIVE guidelines site | 2026-08-30 |
| FAIR data principles | GO FAIR | 2026-08-30 |

**Not established from a primary source:** the evidence-type taxonomy in §02 is
constructed for this profile, not adopted from any standard — it is a working
partition, and papers will occasionally sit awkwardly in it. The APA JARS
fallback was not retrieved directly. The §03 gating defaults are conventions
rather than policy, and the decision not to gate significance here is a
deliberate design choice made because no venue or domain anchor is available.

**Deliberately excluded:** one widely-cited guideline-selection tool that the
EQUATOR site still links to has lapsed, and its domain has been re-registered by
an unrelated party. It is omitted on purpose; use the §07 decision-tree URL.
