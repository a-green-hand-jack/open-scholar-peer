# Domain Profile — Theoretical Physics

## 01. Front matter

```yaml
domain: theoretical-physics
aliases: [hep-th, hep-ph, theoretical-physics, high-energy-theory,
          quantum-field-theory, string-theory, general-relativity,
          statistical-mechanics-theory, mathematical-physics]
version: 1
last_verified: 2026-08-30
```

## 02. Detection cues

- arXiv primary category under `hep-th`, `hep-ph`, `gr-qc`, `math-ph`, or the theory-facing part of `cond-mat.stat-mech`
- A PACS number; section headings like "The model", "Effective action", "Large-N limit", "Perturbative expansion"
- The central claim is a derived relation, a computed quantity, or a proposed model — not a measurement
- No apparatus description, no error budget, no data-taking period

**Hybrid:** if the paper derives a result *and* backs it with lattice
simulation, Monte Carlo, numerical integration, or a parameter scan, also read
`_numerical-slice.md`. This is the common case here, not the exception, and
treating such a paper as purely formal discards every reported quantity.

Distinguish from `experimental-physics.md` by what is *new*: a reanalysis of
existing data under a new framework belongs here; a new measurement does not.

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
| `novelty` | Is the model, derivation, or calculated quantity new? A known result re-derived by a materially different technique can qualify; a re-parameterisation does not. Main risk: an equivalent result already present under different conventions or in another limit. | `true` |
| `technical-soundness` | Are the derivation steps valid, is dimensional consistency maintained, do stated limits reduce to known results, and is each approximation's domain of validity stated rather than assumed? | `true` |
| `clarity` | Are conventions (metric signature, units, normalisation) declared before use and held consistently? Can a subfield reader reproduce each step from the text and its citations? | `false` |
| `significance` | Does the result resolve a tension, extend a framework to a new regime, or supply a needed calculation — or is it routine application of established machinery? One theory venue's only published criterion is whether scientific interest is proportional to length. | venue-set |
| `reproducibility` | Read as **independent verifiability**: could an expert reconstruct the derivation from the steps given, and re-run any numerical component from the disclosed inputs? Not about released code alone. | `false` |

### 0–5 anchors

The band semantics in `../review_vocabulary.md` say what a 2 or a 4 means in
general. These say what it means *here*. Quote the assigned band in the score
table's third column.

**`novelty`**
`0` the result is already present in the paper's own references, or is the same calculation under different conventions ·
`1` a re-parameterisation, or a known result restated in another limit ·
`2` established machinery applied to an adjacent model with no new structure ·
`3` a genuinely new relation, or a known one re-derived by a materially different technique ·
`4` extends the framework to a regime it could not previously reach, or supplies a calculation the field had been missing ·
`5` introduces a method or formulation likely to change how the subfield performs this class of calculation

**`technical-soundness`**
`0` a derivation step is invalid, or the result fails dimensional consistency ·
`1` a stated limit does not reduce to the known result it is claimed to reproduce, or an approximation is applied outside any regime where it holds ·
`2` several steps between framework and result are missing, and approximations are used with no domain of validity stated ·
`3` the derivation holds; individual steps are compressed and some approximations' regimes are asserted rather than argued ·
`4` complete derivation with limits checked; only secondary estimates or presentation could improve ·
`5` every step follows from the stated framework, dimensions carry consistently throughout, and each approximation's domain of validity is established rather than assumed

**`clarity`**
`0` conventions are never declared, so the equations cannot be read unambiguously ·
`1` metric signature, units, or normalisation change between sections without notice ·
`2` a subfield reader must reconstruct conventions or missing intermediate steps to follow the derivation ·
`3` followable; some symbols are used before definition and a few steps need rereading ·
`4` conventions declared and held; only wording or equation numbering could improve ·
`5` conventions, symbols, and equation structure make each step checkable in sequence

**`significance`**
`0` the calculation is already superseded by published work the paper does not cite ·
`1` a narrow technical remark with no consequence beyond the specific model ·
`2` routine application of established machinery to one more case ·
`3` resolves a real tension, or supplies a calculation the subfield needed ·
`4` extends a framework to a new regime others will build on ·
`5` changes how the subfield frames the problem

Length is a venue matter, not a domain one: one theory venue's only published
criterion is whether scientific interest is proportional to length. Apply it
only when that venue asks for it.

**`reproducibility` (Independent Verifiability)**
`0` the derivation cannot be reconstructed from what is written ·
`1` load-bearing intermediate steps or imported results are missing, with no citation from which to recover them ·
`2` an expert must re-derive substantial portions unaided, and any numerical component gives neither inputs nor truncation parameters ·
`3` an expert can complete it, deriving some intermediate steps unaided; numerical inputs partially disclosed ·
`4` derivation chain essentially complete; a few steps left implicit, numerical parameters mostly given ·
`5` every step recoverable from the text and its citations, and any numerical component discloses inputs, truncation or lattice parameters, and convergence checks

Where the paper has a computational component, `_numerical-slice.md` governs how
its instances, precision, and independence from the analytic result bear on the
`technical-soundness` and `reproducibility` bands.

## 04. What counts as evidence

Evidence here is the derivation, plus any numerical support for it. The Summary
phase must extract these fields:

| Field | Content |
|---|---|
| `main_results` | Each derived relation or computed quantity, with its equation number |
| `framework` | The theory, action, or Lagrangian assumed as the starting point |
| `approximations` | Each approximation or expansion used, with the regime it is claimed valid in |
| `derivation_chain` | The sequence of steps from framework to result, including imported results |
| `limits_checked` | Known limits or special cases the paper shows its result reduces to |
| `prior_results_used` | External calculations invoked, with citation, and *what they are used for* |
| `reported_quantities` | Every numerical value, exponent, or coefficient claimed, with units and stated uncertainty |
| `computational_component` | Present / absent. If present, `_numerical-slice.md` also applies |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value, and never silently convert units.

## 05. Nearest prior work

The Scout phase hunts for the **closest competing or superseding calculations**,
not for baselines:

- A published calculation that already yields the paper's result, possibly in different conventions or a different limit
- A more general derivation from which this result follows as a special case
- The same quantity computed to higher order, or with fewer approximations
- A known result the paper's expression should reduce to but apparently does not
- A competing model making the same prediction, weakening a claim of distinctive signature

Frame every finding as "this appears to be implied by / already computed in /
in tension with X" with the citation, or as a question when retrieval is
inconclusive. **Never** report a "missing baseline" or a "missing dataset".

## 06. Verifiability checks

| Check | Tier |
|---|---|
| Every equation referenced in a derivation exists in the paper | automatic |
| Every external result invoked has a citation | automatic |
| Conventions (signature, units, normalisation) are declared before first use | automatic |
| Symbols used in the final result are all defined earlier | automatic |
| Quantities carried between equations keep consistent dimensions | semi-automatic |
| Numerical values in the text match those in tables and figures | semi-automatic |
| The stated limit genuinely reduces to the cited known result | manual |
| Each approximation is valid in the regime where it is applied | manual |
| The derivation steps follow from the stated framework | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.

## 07. Reporting standards

**No mandatory reporting standard exists for this domain.** No community-wide
checklist analogous to CONSORT or ARRIVE was found. Applicable conventions are
limited to arXiv category fit, a PACS number where required, and AI-use
disclosure. Where the paper carries a numerical component, the venue's data-
and code-availability expectations apply to that component; see
`_numerical-slice.md` rather than inventing a requirement here.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- A central result is asserted without derivation and without citation to where it is derived
- A cited result is misstated in a way that changes what it yields
- An approximation is applied outside the regime the paper itself states for it
- The same calculation is claimed as new when the paper's own references contain it
- A numerical result is load-bearing but neither code nor input parameters are available
- Plagiarism, duplicate submission, or undisclosed overlap with the authors' prior work

## 09. Anti-patterns — never generate these

The failure mode this profile exists to prevent is asking machine-learning
questions of a derivation. Each row is a question class that must not be
produced.

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "Which published calculation is closest, and does it already yield this result?" |
| "Were ablations performed?" | "Which approximations are load-bearing — what changes if each is relaxed?" |
| "Which datasets were used?" | "Which known limits or special cases is the result checked against?" |
| "Are hyperparameters disclosed?" | "Are the couplings, scales, and expansion parameters given, with their regime of validity?" |
| "Is the training data representative?" | "Is the parameter range scanned representative of the regime the claim covers?" |
| "Is the code released?" | "Are the intermediate steps sufficient for an expert to reconstruct the derivation?" |
| "Would this generalize to another dataset or larger scale?" | "Does the derivation extend beyond the stated regime, or is there a known obstruction?" |
| "How does this compare to state of the art?" | "Is this the highest-order or least-approximated calculation of this quantity to date?" |
| "What is the model's accuracy?" | "What is the estimated size of the neglected terms, and is it stated?" |

Do not merely rephrase a forbidden question in domain vocabulary. If a question
has no meaningful form here, drop it and use the criterion's remaining budget
on a different angle.

## 10. Seed questions

- `technical-soundness` — "Equation N assumes the expansion parameter is small. Is the regime where this holds stated, and does the claimed application stay inside it?" (look in the derivation and results)
- `technical-soundness` — "Does the result reduce to the known [limit] when [parameter] → 0, and is that check shown?" (look in a consistency-check subsection)
- `novelty` — "Reference [X] computes a related quantity. Is this a higher-order result, or the same result in different conventions?" (look in related work)
- `reproducibility` — "The step from Eq. N to Eq. N+1 is asserted as direct. Can it be reconstructed from the cited results alone?" (look in the derivation body)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates **the
derivation and any numerical support for it**, not measurements: `convincing`
means the derivation is complete and checkable as written and its numerical
checks are adequate, not that an apparatus was well calibrated.

The *"never claim a result is verified"* rule in that file applies here with the
same force as it does to proofs. A derivation the reviewer could not follow is a
verification-agenda item, not a soundness verdict in either direction.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Scientific interest must be proportional to paper length; no scoring rubric published | JHEP author/referee help pages | 2026-08-30 |
| Revision deadlines (90 days major / 30 days minor), point-by-point reply required, 12-month appeal window | JHEP author/referee help pages | 2026-08-30 |

**Not established from a primary source — do not cite as policy:**

- **APS journals (PRL, PRD, PRB) could not be retrieved**; every path returned
  HTTP 403 behind Cloudflare. Secondary indexes describe a
  validity / importance / broad interest / accessibility dimension set, which
  was **not** confirmed and is deliberately excluded from §03. For an APS
  venue, retrieve the rubric at onboarding.
- **SciPost Physics could not be retrieved**; its referee guidelines sit behind
  a proof-of-work gate. Secondary indexes describe a six-dimension public
  scoring model — the closest directly reusable rubric in this domain. It is
  unverified, is not encoded here, and is the highest-value gap to close next.

The only primary source obtained publishes one qualitative criterion and no
rubric, so §03 is derived from it plus general practice. Treat the §03 gating
defaults as conventions, not any venue's policy.
