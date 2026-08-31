# Domain Profile — Chemistry

## 01. Front matter

```yaml
domain: chemistry
aliases: [organic-chemistry, inorganic-chemistry, synthesis, catalysis,
          materials-chemistry, computational-chemistry, crystallography,
          medicinal-chemistry, electrochemistry, polymer-chemistry]
version: 1
last_verified: 2026-08-30
```

## 02. Detection cues

- arXiv primary category under `physics.chem-ph`, `cond-mat.mtrl-sci` with synthesis content, or no arXiv presence at all (chemistry preprints often appear only on ChemRxiv)
- Section headings "Experimental Section", "General Procedure", "Synthesis of N", "Supporting Information"
- Compound numbering in bold (**1**, **2a**, **3b**) used as the primary referent throughout the text
- Reported yields, melting points, R_f values, or spectroscopic assignments (δ ppm, m/z, cm⁻¹)
- A crystallographic deposition number (CCDC / ICSD) or a `.cif` file
- References dominated by JACS, Angew. Chem., Org. Lett., Chem. Sci., Nature Chem.

**Hybrid:** computational-chemistry papers that derive a mechanism analytically
and validate it with DFT are still this domain — but if the core claim is a
formal derivation rather than a chemical result, read `math.md` or
`theoretical-physics.md` and treat the chemistry as the numerical slice via
`_numerical-slice.md`.

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
| `novelty` | Is the transformation, structure, mechanism, or material new? A claim of prior report must carry a citation — asserting "this has been reported before" without one is itself a defect in the review, not a finding. | `true` |
| `technical-soundness` | Is the mechanistic argument supported by the data presented? Are control experiments present for each mechanistic claim? Is the computational method appropriate to the system, and is the basis set adequate? | `true` |
| `clarity` | Are schemes legible, is compound numbering consistent between the main text and the SI, and does every characterized compound appear in both? | `false` |
| `significance` | Does the work enable a transformation, structure, or property that was previously inaccessible, or improve access materially? | venue-set |
| `reproducibility` | Read as **synthetic and computational reproducibility**: can the procedure be repeated from the SI alone? Are spectra reproduced, are coordinates machine-readable, are software versions and computational keywords stated? | `true` |

Note the elevated default gating on `reproducibility`: chemistry treats
characterization completeness as a threshold rather than a quality gradient — a
compound whose identity is not established has not been made, however
interesting the claim.

### 0–5 anchors

The band semantics in `../review_vocabulary.md` say what a 2 or a 4 means in
general. These say what it means *here*. Quote the assigned band in the score
table's third column.

This field has unusually hard criteria — checkCIF alert levels, which methods
can and cannot establish purity, machine-readable coordinates. Those belong in
the low bands, because they are decidable rather than matters of taste.

**`novelty`**
`0` the compound or transformation already appears in the paper's own cited literature ·
`1` a published transformation applied to an adjacent substrate, with no new selectivity or mechanistic insight ·
`2` routine substrate-scope extension of a published method ·
`3` genuinely new, but close to a published route and with modest advantage over it ·
`4` reaches a transformation, structure, or property prior routes could not, or improves access materially ·
`5` opens a class of reactivity or structure type others will build on

**`technical-soundness`**
`0` the reported data contradict the assigned structure ·
`1` a mechanistic claim rests on no control at all (`control_experiments: none`), or the computational method is inappropriate to the system studied ·
`2` the identity/purity/yield triple is incomplete for a compound claimed as new, or the basis set is inadequate for the system ·
`3` data support the assigned structures; some mechanistic claims rest on controls weaker than the claim needs ·
`4` complete characterization with discriminating controls; secondary mechanistic claims could use more support ·
`5` every mechanistic claim discriminated against alternatives by control, and the computational treatment matched to the system

**`clarity`**
`0` compound numbering cannot be reconciled between the main text and the SI ·
`1` characterized compounds appear in one document but not the other ·
`2` schemes must be reconstructed to follow the route, or numbering drifts between sections ·
`3` followable; some schemes crowded, a few cross-references need chasing ·
`4` legible schemes and consistent numbering throughout ·
`5` every compound traceable at a glance across text, SI, and spectra

**`significance`**
`0` the transformation or structure is already routinely accessible by the cited methods ·
`1` a single compound or result with no consequence beyond itself ·
`2` incremental improvement in yield or conditions over an established route ·
`3` materially improves access to a useful class of compounds or properties ·
`4` enables work that was previously impractical ·
`5` establishes a method or structural class that redirects effort in the area

**`reproducibility`**
`0` the procedure cannot be repeated from the SI — steps, reagents, or stoichiometry missing ·
`1` purity rests on HRMS alone, which cannot establish purity, or coordinates are supplied only as an SI table or PDF ·
`2` checkCIF A- or B-level alerts unresolved and carrying no written justification; or R factor above 0.15 without explanation; or software version, method, or basis set absent ·
`3` procedure repeatable and spectra reproduced; secondary parameters such as k-point mesh or solvation keywords left implicit ·
`4` complete SI with machine-readable coordinates, CCDC number, and stated computational keywords ·
`5` spectra reproduced for every new compound, checkCIF clean or fully justified, coordinates machine-readable, computational setup completely specified

Where medicinal-chemistry claims are made, purity below the 95% convention
belongs in band `1`–`2` regardless of the method used to measure it.

## 04. What counts as evidence

Evidence here is characterization data plus the procedures that generated it.
The Summary phase must extract these fields:

| Field | Content |
|---|---|
| `new_compounds` | Every compound claimed as new, by its paper number |
| `identity_evidence` | Per compound: which techniques establish identity (¹H NMR, ¹³C NMR, HRMS, IR, X-ray) |
| `purity_evidence` | Per compound: what establishes purity, and by which method. Record `HRMS only` explicitly when that is all there is — see §08 |
| `yields` | Reported yield per compound or per step, with scale |
| `conditions` | Reagents, solvent, temperature, time, atmosphere, catalyst loading |
| `control_experiments` | Each mechanistic claim and the control that supports it, or `none` |
| `computational_setup` | Software and version, method/functional, basis set, solvation model; for periodic systems, k-point mesh and energy cutoff |
| `crystallographic_data` | CCDC number, R factor, and whether a checkCIF report is included |
| `coordinates_format` | Machine-readable (`.xyz`/`.mol2`/`.pdb`/`.cif`) or not — see §06 |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value, and never infer a yield or a purity from context.

## 05. Nearest prior work

The Scout phase hunts for **prior art on the same transformation, structure, or
system**:

- An existing synthesis of the same target, with comparable or better yield or step count
- A prior report of the same transformation under different conditions, which may reduce the novelty claim to the conditions alone
- A known structure matching the reported crystallographic parameters
- A prior computational study of the same system at a comparable or higher level of theory
- Methodology the authors cite for a technique but not for a result that anticipates theirs

ACS ethical guidance is explicit that a reviewer asserting prior publication
**must supply the citation**. Frame findings as "this appears anticipated by X"
with the reference, or as a question when retrieval is inconclusive. Never
assert prior art from memory.

## 06. Verifiability checks

`checkCIF` is the only fully industrialized automated review engine encountered
in this survey — over 400 enumerable tests, a four-level alert scheme, and, for
the two top levels, a *mandatory written scientific justification* from the
authors (a Validation Response Form). Its shape is worth imitating: **the
machine grades, the human justifies.** It does not decide.

| Check | Tier |
|---|---|
| Every compound number in the main text appears in the SI | automatic |
| Every compound claimed new has both ¹H and ¹³C NMR reported | automatic |
| A CCDC deposition number is present when a crystal structure is claimed | automatic |
| Coordinates are supplied in a machine-readable format, not as an SI table or PDF | automatic |
| Computational software version, method, and basis set are all stated | automatic |
| Periodic calculations state k-point mesh and energy cutoff | automatic |
| R factor is within the checkCIF alert bands (>0.20 → A, >0.15 → B, >0.10 → C) | automatic |
| checkCIF A- and B-level alerts are either resolved or carry a written justification | semi-automatic |
| Purity claim rests on a method that can establish purity | semi-automatic |
| Reported spectra match the assigned structures | manual |
| The computational method is appropriate to the system studied | manual |
| Control experiments actually discriminate between the proposed mechanism and alternatives | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts — in
particular, never assert that a spectrum is inconsistent with a structure; flag
it for expert inspection.

## 07. Reporting standards

Conditional hooks, triggered by paper content:

| If the paper reports… | Then check against |
|---|---|
| a new compound | Identity + purity + yield must all be established. Absent elemental analysis, homogeneity must be shown by NMR or HPLC |
| a compound intended for biological testing | Purity ≥95% is the common medicinal-chemistry threshold |
| combustion analysis | Values within 0.4% of theory (the stricter journals' bar) |
| a crystal structure | `.cif` deposited, checkCIF report included, CCDC number cited |
| computed structures | Machine-readable coordinates. ACS data guidance is explicit: *"A table in the SI or a PDF are not acceptable sources for coordinates."* Software version, method, basis set, and solvation keywords are required; periodic systems additionally require k-point and cutoff values |

**HRMS is not a purity criterion.** High-resolution mass spectrometry
establishes molecular formula, not homogeneity. A paper that offers HRMS alone
as evidence of purity has a gap, and this is one of the most reliably
detectable defects in the domain.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- A compound is claimed as new but its identity is not established by any technique
- Purity is claimed on the basis of HRMS alone
- A crystal structure is claimed with no CCDC number and no deposited `.cif`
- Computed structures are reported with coordinates only as a PDF or SI table
- checkCIF A-level alerts are present with neither resolution nor written justification
- The core finding has already appeared in the authors' own preprint, conference proceedings, or review article without disclosure
- Plagiarism, duplicate submission, or undisclosed substantial similarity to concurrent submissions elsewhere

## 09. Anti-patterns — never generate these

The failure mode this profile prevents is asking machine-learning questions of a
synthesis. Each row is a question class that must not be produced.

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "Is there an existing synthesis of this target, and how do yield and step count compare?" |
| "Were ablations performed?" | "Which control experiments discriminate this mechanism from the alternatives?" |
| "Which datasets were used?" | "Which compounds were characterized, and by which techniques?" |
| "Are hyperparameters disclosed?" | "Are the functional, basis set, solvation model, and software version all stated?" |
| "Is the code released?" | "Are coordinates deposited in a machine-readable format rather than as a PDF table?" |
| "Would this generalize to a larger dataset?" | "What is the substrate scope, and which failed substrates are reported?" |
| "Is the improvement statistically significant?" | "Is the yield improvement outside normal run-to-run variation, and was it replicated?" |
| "What is the train/test split?" | "For the computational work, was the method validated against experimental or higher-level reference data?" |

Do not merely rephrase a forbidden question in domain vocabulary. If a question
has no meaningful form here, drop it and use the criterion's remaining budget
on a different angle.

## 10. Seed questions

- `technical-soundness` — "The mechanism in Scheme N is proposed. Which experiment in the paper rules out the alternative pathway?" (look in the mechanistic studies section)
- `reproducibility` — "Compound **N** is claimed new. Which techniques establish its identity, and which separately establish its purity?" (look in the SI experimental section)
- `reproducibility` — "Are computed coordinates supplied in a machine-readable format, and are the software version and basis set stated?" (look in the SI and computational details)
- `novelty` — "Reference [X] reports a related transformation. Is the difference in substrate scope, conditions, or mechanism?" (look in the introduction and scope table)
- `clarity` — "Compound numbering in Scheme 2 and the SI appear to diverge. Which is authoritative?" (look across main text and SI)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates the
**characterization and control experiments**: `convincing` means identity,
purity, and mechanism are each supported by appropriate technique, not that the
chemistry is interesting.

Domain-specific note on aggregation: the non-averaging rule in that file has a
concrete precedent here. At least one major journal's top-tier designation
requires two strong endorsements yet is revoked outright if a third report
falls below the top two bands — a genuinely non-linear rule. Do not average
findings into a mean score.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Identity + purity + yield required; NMR/HPLC homogeneity absent elemental analysis | JACS author guidelines | 2026-08-30 |
| Combustion analysis within 0.4%; HRMS not a purity criterion | Org. Lett. author guidelines | 2026-08-30 |
| checkCIF: 400+ tests, A/B/C/G alert levels, R factor bands, VRF requirement for A/B | IUCr checkCIF FAQ | 2026-08-30 |
| Machine-readable coordinates required; *"A table in the SI or a PDF are not acceptable sources for coordinates"* | ACS Research Data Guidelines | 2026-08-30 |
| Prior-report claims must carry a citation; substantial similarity must be raised with the editor | ACS Ethical Guidelines, Obligations of Reviewers §7 and §8 | 2026-08-30 |
| Non-linear VIP aggregation (two endorsements, revoked by a third below band) | Angewandte Chemie 2002 guideline page | 2026-08-30 |

**Not established from a primary source:** the current ACS Ethical Guidelines
page returned HTTP 403; the §7 and §8 wording above comes from a 2006 printed
institutional mirror, and it was **not confirmed whether the eleven obligations
have been revised in the current edition**. Cell Press pages were also
unreachable (site-wide 403), so no Cell-family requirements are represented.
Medicinal-chemistry purity thresholds and combustion tolerances vary by journal;
the §07 values are the common stricter bars, not universal policy.
