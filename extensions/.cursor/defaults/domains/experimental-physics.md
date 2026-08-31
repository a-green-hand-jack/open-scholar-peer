# Domain Profile — Experimental Physics

## 01. Front matter

```yaml
domain: experimental-physics
aliases: [experimental-physics, hep-ex, condensed-matter, cond-mat,
          astro-ph-observational, physics-ins-det, optics-experimental,
          nuclear-experiment, atomic-physics]
version: 1
last_verified: 2026-08-30
```

## 02. Detection cues

- arXiv primary category under `hep-ex`, `nucl-ex`, `physics.ins-det`, observational `astro-ph`, or experimental `cond-mat.*`
- Section headings like "Apparatus", "Detector", "Systematic uncertainties", "Calibration", "Data taking"
- The central claim is a measured value, a limit, an observation, or a device characterisation
- An error budget, an integrated-luminosity or exposure figure, or figures with error bars and exclusion contours

**Hybrid:** if the paper reports a measurement *and* its interpretation rests on
a derivation the authors present, read `theoretical-physics.md` alongside this
profile. If the analysis depends on simulation whose parameters are load-bearing
for the result, also read `_numerical-slice.md` so those inputs are extracted
rather than summarised away.

Distinguish from `theoretical-physics.md` by what is *new*: a new measurement
belongs here even when heavily modelled; a new framework applied to archival
data does not.

## 03. Criterion instantiation

How this domain reads the criteria the venue supplied. `gating` is the
**default** only — a venue's own gating always wins.

| Criterion slug | What it means here | Default gating |
|---|---|---|
| `novelty` | Is this a first observation, a materially improved precision, a new regime, or a new technique? A repeat measurement at comparable precision is a confirmation, which some venues value and others do not. | `true` |
| `technical-soundness` | Are calibration, background subtraction, and efficiency corrections correct? Are statistical and systematic uncertainties separated and both propagated? Is the analysis blind, and if so when were selection criteria frozen? One major publisher lists appropriate use of statistics and treatment of uncertainties as its own review dimension, separate from general validity. | `true` |
| `clarity` | Are error bars defined in the figure legends? Are units, conventions, and the meaning of every band and contour stated? One publisher instructs referees to comment explicitly whenever an error bar is left undefined. | `false` |
| `significance` | Does the measurement settle a question, constrain a model, or enable new work? A venue may additionally require a discernible reason why the work deserves its visibility rather than that of a good specialist journal — that is a venue bar, not a domain one. | venue-set |
| `reproducibility` | Are data and code available, are analysis parameters disclosed, and could the measurement be repeated from the description? Some venues require both data- and code-availability statements and take core analysis code into peer review. | `true` |

## 04. What counts as evidence

Evidence here is the measurement and its uncertainty budget. The Summary phase
must extract these fields:

| Field | Content |
|---|---|
| `measured_quantities` | Each reported value with units, central value, and uncertainties as quoted |
| `uncertainty_breakdown` | Statistical and systematic contributions separately, plus how systematics were estimated |
| `error_bar_definition` | What the error bars in each figure represent, and whether the legend says so |
| `apparatus` | Instrument, sample, or detector configuration relevant to the claim |
| `dataset_provenance` | Exposure, integrated luminosity, run period, or number of samples |
| `calibration_and_background` | Calibration procedure and background subtraction method |
| `blinding` | Whether the analysis was blind, and at what point selection criteria were frozen |
| `significance_reported` | Any claimed significance, and whether it is **local** or **global** |
| `simulation_dependence` | Which results depend on simulation, and which simulation inputs are load-bearing |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value, never convert units silently, and never merge
statistical and systematic uncertainties that the paper reports separately.

## 05. Nearest prior work

The Scout phase hunts for the **closest competing or superseding measurements**,
not for baselines. Specifically:

- A prior measurement of the same quantity, and whether this one is consistent with it
- An existing limit this result should be compared against, tightens, or that already excludes the claim
- A more precise measurement by another collaboration or technique
- A known systematic effect in this class of measurement that the paper does not discuss
- A competing explanation for the observed signal that the paper does not exclude

Frame every finding as "this appears to be superseded by / in tension with /
already excluded by X" with the citation, or as a question when retrieval is
inconclusive. **Never** report a "missing baseline" or a "missing dataset" —
the domain term is a prior measurement or an existing limit.

## 06. Verifiability checks

| Check | Tier |
|---|---|
| Every figure with error bars has a legend defining what they represent | automatic |
| Every reported value carries units; values in abstract, text, and tables agree | automatic |
| Data- and code-availability statements are present where the venue requires them | automatic |
| Statistical and systematic uncertainties are reported separately | semi-automatic |
| A claimed significance states whether it is local or global | semi-automatic |
| Quoted uncertainties are consistent with the significance claimed | semi-automatic |
| The systematic uncertainty budget is complete for this class of measurement | manual |
| Background subtraction and efficiency corrections are correct | manual |
| Selection criteria were frozen before the signal region was examined | manual |
| The look-elsewhere effect is accounted for where a search scans many hypotheses | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.

Two cautions for the `manual` tier. Discovery thresholds here are deliberately
severe — the particle-physics 5σ convention exists because 3σ and 4σ effects
have historically evaporated, and because underestimating a systematic by a
factor of two turns a 4σ result into a 2σ one; do not treat a sub-threshold
excess as a finding in either direction. And where a search scans many
hypotheses a trial factor applies, with published practice applying the 5σ
convention to the *local* p-value — so a paper quoting only one of the two is
following a real convention. Ask which is quoted; do not assert the other is
missing.

## 07. Reporting standards

**No community-wide checklist analogous to CONSORT or ARRIVE exists here.**
What applies instead is venue policy, which is real and enforceable: at least
one major publisher requires data- and code-availability statements as a
condition of publication, takes core analysis code into peer review rather than
merely citing it, and maintains subject-specific submission templates for
particular claim types (solar-cell performance and claims of lasing are two
documented examples).

Check the venue's own requirements at onboarding rather than assuming this list
is complete. If the paper's claim type matches a templated category, that
template's fields become extraction targets in §04.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- A central measured value is reported without any uncertainty
- Statistical and systematic uncertainties are conflated where the claim depends on the distinction
- A discovery claim is made without stating the significance, or a significance is quoted with no statement of local versus global
- Selection criteria were tuned after the signal region was examined, and this is not disclosed
- Data or code required by the venue's policy is neither provided nor accompanied by a stated exemption
- Evidence of image manipulation or duplicated figure panels
- Plagiarism, duplicate submission, or undisclosed overlap with the authors' prior work

## 09. Anti-patterns — never generate these

The failure mode this profile exists to prevent is asking machine-learning
questions of a measurement. Each row is a question class that must not be
produced.

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "Which prior measurement or existing limit does this supersede, and are they consistent?" |
| "Were ablations performed?" | "Which systematic uncertainties dominate the budget, and how was each estimated?" |
| "Which benchmark datasets were used?" | "What exposure, luminosity, or sample count underlies this result?" |
| "Are hyperparameters disclosed?" | "Are the selection criteria and calibration constants disclosed, and when were they frozen?" |
| "What is the model's accuracy?" | "What is the total uncertainty, and how does it split between statistical and systematic?" |
| "Is the improvement statistically significant?" | "Is the quoted significance local or global, and does a trial factor apply?" |
| "Was a train/test split used?" | "Was the analysis blind, and was the signal region opened only after criteria were fixed?" |
| "Would this generalize to another dataset?" | "Does the measurement hold across run periods, detector regions, or sample batches?" |
| "How does this compare to state of the art?" | "Is this the most precise measurement of this quantity to date, and by how much?" |
| "Is the code released?" | "Are data and analysis code available as the venue's policy requires, and is core code available for review?" |

Do not merely rephrase a forbidden question in domain vocabulary. If a question
has no meaningful form here, drop it and use the criterion's remaining budget
on a different angle.

## 10. Seed questions

- `technical-soundness` — "Figure N's error bars are not defined in the legend. Are they statistical only, or combined?" (figure legends, uncertainties section)
- `technical-soundness` — "Which systematic dominates the budget for the headline value, and how was its magnitude estimated?" (systematic uncertainties section)
- `technical-soundness` — "The paper quotes a significance of Nσ. Is this local or global, and how many hypotheses were scanned?" (statistical analysis section)
- `novelty` — "Reference [X] reports the same quantity. Is this consistent with it, and is the improvement in precision or in regime?" (introduction, comparison figures)
- `reproducibility` — "The result depends on simulation of [process]. Which generator, tune, and version were used?" (methods or simulation section)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates **the
measurement and its uncertainty budget**: `convincing` means the uncertainties
are credibly estimated and the claim is supported at the field's conventional
threshold, not merely that a number was reported.

The *"never claim an experiment is sound"* rule applies with full force. Judging
a systematic uncertainty budget complete requires knowledge of the apparatus a
reviewer working from the text does not have — record it as a verification
agenda item naming the specific systematic, not as a verdict.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Eleven-item referee dimension list (statistics and treatment of uncertainties is a distinct dimension); referees told to comment when error bars are undefined in figure legends; venue bar phrased as a discernible reason for visibility over the best specialist journals | Nature Portfolio peer review policy page | 2026-08-30 |
| Mandatory data- and code-availability statements; core code enters peer review; subject-specific templates including solar cells and claims of lasing | Nature Portfolio reporting standards page | 2026-08-30 |
| Nature Physics has no independent referee guide | `nature.com/nphys/for-referees` observed to 302-redirect to the portfolio-wide policy | 2026-08-30 |

**Not established from a primary source — do not cite as policy:**

- **APS journals (PRL, PRD, PRB) could not be retrieved.** All paths returned
  HTTP 403 behind Cloudflare, including referee and data-policy pages. Nothing
  in §03 or §07 derives from APS. For an APS venue, retrieve the rubric at
  onboarding.
- The 5σ convention, the systematic-underestimation rationale, the
  look-elsewhere effect, and applying the threshold to the local p-value are
  **field conventions gathered from the literature**, not quoted from any
  publisher's referee policy. §06 states them as cautions against over-claiming;
  they must not be presented to authors as a venue requirement.

The §03 gating defaults are conventions plus one publisher's policy, not a
field-wide standard. `reproducibility` defaults to `true` here — unlike in the
theoretical profiles — because at least one major venue makes availability
statements a publication condition; a venue without that policy should override
it.
