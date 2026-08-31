# Domain Profile — Biology / Life Sciences

## 01. Front matter

```yaml
domain: biology
aliases: [life-sciences, molecular-biology, cell-biology, genetics, genomics,
          neuroscience, immunology, microbiology, ecology, physiology,
          bioinformatics-wet-lab]
version: 1
last_verified: 2026-08-30
```

## 02. Detection cues

- arXiv `q-bio.*`, a bioRxiv preprint, or a life-sciences journal venue
- Headings "Materials and Methods", "STAR Methods", "Results and Discussion"
- A Key Resources Table, or antibody/cell-line/strain listings with catalog numbers
- Sample sizes in units of biological material; error bars over biological replicates
- Ethics statements naming an IACUC, IRB, or equivalent committee

**Hybrid:** if the core claim is a theorem or formal model that measurements
only illustrate, route to `math.md` plus `_numerical-slice.md` — routing
follows the method of justification, not the subject matter.

## 03. Criterion instantiation

How this domain reads the criteria the venue supplied. `gating` is the
**default** only — a venue's own gating always wins.

| Criterion slug | What it means here | Default gating |
|---|---|---|
| `novelty` | Is the biological finding, mechanism, or method new relative to the literature? A confirmatory result in a new system, or a known mechanism in a new organism, may be valuable without being novel — say which. | `true` |
| `technical-soundness` | Does the design support the causal claim made? Is the **experimental unit** correctly identified? Are the statistical tests matched to the design, and is the reported n the number of independent biological units rather than technical repeats? | `true` |
| `clarity` | Are figure legends complete (what the error bars represent, what n is, which test)? Can the Methods be followed by a competent lab without contacting the authors? | `false` |
| `significance` | Does the finding change understanding of a mechanism, or extend it to a new context? | venue-set |
| `reproducibility` | Read as **independent verifiability**: are reagents identified to the level of a persistent identifier, are data and analysis code accessible, are exclusion and randomization decisions disclosed? | `true` |

**Why `significance` is never fixed here.** Two life-sciences venues can assign
opposite consequences to the same significance judgement. At least one
high-volume journal asks reviewers on its form how significant the results are
for the discipline, while explicitly declining to reject on that basis —
publishing instead on validity and methodological rigour. Other life-sciences
journals require originality, importance in field, and interest outside field
to be simultaneously exceptional. Hard-coding a gating value here would import
one venue's editorial policy into every review. Read `gating` from
`session.json.qa_criteria[]`.

## 04. What counts as evidence

Evidence here is measurement under a design. The Summary phase must extract
these fields; each becomes a row later phases can cite:

| Field | Content |
|---|---|
| `claims` | Each biological claim, with the figure or table that supports it |
| `experimental_unit` | What was independently manipulated or sampled — animal, cage, culture, well, subject |
| `n_reported` | The n for each comparison, and whether it counts biological or technical replicates |
| `design` | Randomization, blinding, and allocation as described (or "not stated") |
| `exclusions` | Any data excluded, with the stated criterion and whether it was pre-specified |
| `statistics` | Test used, effect size, dispersion measure, and what the error bars represent |
| `reagents` | Antibodies, cell lines, organisms, and software, with RRIDs or catalog numbers |
| `cell_line_provenance` | Source, authentication (STR), and mycoplasma status, where cell lines are used |
| `data_availability` | Accession numbers, repositories, and code location |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value, and never infer n from a figure.

## 05. Nearest prior work

The Scout phase hunts for work that constrains or competes with the claim:

- Prior studies reporting the same effect, including ones that failed to find it
- The established mechanism this result would revise, and what supports it
- Work in an adjacent organism or system that bounds how far the claim generalizes
- Reagent-validation literature relevant to the antibodies or lines used
- Retraction or expression-of-concern notices touching key cited work

Frame findings as "this effect appears already reported in / contradicted by /
bounded by X" with the citation. Where novelty rests on a system rather than a
mechanism, say so rather than treating it as a defect.

## 06. Verifiability checks

Checks operate at **article level**, not sentence level — article-level
aggregation measures materially better on reporting-checklist corpora, and it
matches how a reviewer acts.

| Check | Tier |
|---|---|
| Every resource in a Key Resources Table also appears in the reference list | automatic |
| Data-availability and code-availability statements are present and non-empty | automatic |
| Accession numbers resolve to a live record | automatic |
| Every figure legend states what error bars represent and gives n | automatic |
| Ethics approval identifiers are present when animal or human subjects are used | automatic |
| Reagents carry RRIDs rather than bare catalog numbers | semi-automatic |
| n values in figure legends are consistent with the Methods and any flow description | semi-automatic |
| Reported statistics are consistent with the stated design | semi-automatic |
| The experimental unit is correctly identified, and n counts independent units | manual |
| Sample size is adequate for the effect claimed | manual |
| Randomization and blinding, where claimed, are credible | manual |
| Exclusion criteria were pre-specified rather than applied post hoc | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.

## 07. Reporting standards

Standards apply **by paper type, not by domain**. Check each trigger; several
may fire at once. Absence of an applicable standard is itself reportable.

| If the paper… | Then check against | Notes |
|---|---|---|
| reports vertebrate or cephalopod animal experiments | ARRIVE 2.0 | Essential 10 first; Recommended Set where the venue requires it |
| is submitted to a venue using a structured life-sciences reporting form | that venue's reporting summary | Sample size, data exclusions, replication, randomization, blinding are each mandatory disclosures — a negative answer must still be given, and "not applicable" is not an accepted response |
| is a systematic review or meta-analysis | PRISMA 2020 | Flow-diagram arithmetic is the cheapest high-value check |
| is an observational human study | STROBE | Also watch for causal language exceeding the design |
| is published under a framework covering materials, design, analysis and reporting | MDAR | Materials and Reporting items are the machine-checkable half |
| releases a dataset | FAIR principles | Identifier resolution, licence, and indexing are machine-checkable |
| uses a Key Resources Table convention | that venue's resource-table rules | Cross-referencing table entries against the bibliography is fully automatic |

Where no standard applies, say so — do not invent one, and do not penalise the
paper for failing a standard its venue does not require.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- Animal or human-subject work reported without an ethics approval identifier
- Human-participant work without a consent statement
- A cell line on a known misidentification register, used without authentication
- Image reuse, duplication, or manipulation across panels or between papers
- Undisclosed overlap with the authors' prior publications
- A causal claim asserted from a design that cannot support it

## 09. Anti-patterns — never generate these

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "What is the control condition, and does it isolate the manipulated variable?" |
| "Were ablations performed?" | "Which components of the mechanism were tested independently — and by what perturbation?" |
| "Which benchmark datasets were used?" | "What is the experimental system, and why is it appropriate for this claim?" |
| "Are hyperparameters disclosed?" | "Are reagent identities, concentrations, and protocol parameters disclosed?" |
| "Is the model state-of-the-art?" | "Does the finding revise, extend, or confirm the established mechanism?" |
| "Is the code released?" | "Are the underlying data deposited, and is the analysis code available?" |
| "How large is the training set?" | "What is n, and does it count independent biological units?" |
| "Would this generalize to a larger dataset?" | "Would this hold in another strain, line, or organism — and is there evidence either way?" |

Do not merely rephrase a forbidden question in domain vocabulary. If a question
has no meaningful form here, drop it and use the criterion's remaining budget
on a different angle.

## 10. Seed questions

- `technical-soundness` — "Figure N reports n=6. Are those six independent animals or six measurements from fewer animals?" (look in the Methods and figure legend)
- `technical-soundness` — "Was the sample size determined in advance, and on what basis?" (look in the Methods or reporting summary)
- `reproducibility` — "The antibody in §Methods is given by catalog number only. Is there an RRID or validation reference?" (look in the Methods or resource table)
- `technical-soundness` — "Data from one group were excluded. Was that criterion pre-specified?" (look in the Methods and any exclusions statement)
- `novelty` — "Reference [X] reports a comparable effect in a related system. What distinguishes this result?" (look in the Introduction and Discussion)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates the
measurement and design, not the plausibility of the mechanism: a well-motivated
hypothesis with under-powered support is `incomplete`, not `solid`.

Where a reporting-checklist item is simply absent, prefer
`insufficient evidence to judge` over `concern` — absence of disclosure is a
reporting gap to raise, not by itself evidence of a flawed experiment.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Life-sciences reporting items must be disclosed even when negative; "not applicable" is not accepted | Nature Reporting Summary (Apr 2023) | 2026-08-30 |
| Dual-axis significance / strength-of-evidence vocabulary | eLife assessment vocabulary | 2026-08-30 |
| Publication on validity and rigour rather than perceived significance, while the review form still asks about significance | PLOS ONE criteria-for-publication page and its review form | 2026-08-30 |
| Simultaneous originality / importance / outside-interest requirements | PLOS Biology reviewer guidelines | 2026-08-30 |
| Animal-research reporting items | ARRIVE 2.0 guidelines site | 2026-08-30 |
| Materials / design / analysis / reporting framework | MDAR framework publication (PNAS) | 2026-08-30 |
| All resource-table entries must appear in the reference list | Publisher Key Resources Table guidance (secondary page) | 2026-08-30 |
| Article-level checklist extraction outperforms sentence-level | Published CONSORT/SPIRIT text-mining evaluations | 2026-08-30 |

**Access failure.** The publisher's own STAR Methods / Key Resources Table page
returned 403 on every attempt. The KRT rule above comes from a secondary
publisher-hosted page; the number of mandated Methods subsections is **not
confirmed** and differs between versions. Do not cite a specific count.

**Two claims commonly made about this domain, corrected:**

- It is **not** accurate that the high-volume venue above "does not assess
  novelty or significance at all". Its form does ask reviewers to judge
  significance; what is documented is that significance is not grounds for
  rejection. State the narrower claim.
- No authoritative source was found for the assertion that the MDAR framework
  has **replaced** publishers' own reporting forms. The evidence supports only
  that they are related and interoperable. Do not assert replacement.
