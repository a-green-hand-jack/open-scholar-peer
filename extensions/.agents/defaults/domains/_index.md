# Domain Profiles — Routing Table

A **domain profile** supplies the discipline-specific half of a review. It is
orthogonal to the venue's review guidelines:

| Layer | Decides | Source |
|---|---|---|
| **Venue** | which criteria exist, the scoring rubric, the output format, and which criteria gate the decision | `00_review_guidelines.md` (web / user / generic fallback) |
| **Domain** | what counts as evidence, what "nearest prior work" means, which verifiability checks apply, which questions must never be asked | this directory |

Both layers always apply. A venue rubric never removes a domain's anti-pattern
list, and a domain profile never overrides a venue's criteria or gating.

## Routing

At onboarding, classify the paper and read **exactly one** profile below.
Record the choice in `session.json` as `paper.field`.

| If the paper's primary contribution is… | Read |
|---|---|
| a proof, theorem, or formal result in mathematics or mathematical logic | `math.md` |
| a derivation, model, or formal result in physics, with no new measurement | `theoretical-physics.md` |
| a measurement, observation, or instrument result in physics | `experimental-physics.md` |
| a wet-lab, omics, ecological, or organismal result in the life sciences | `biology.md` |
| a synthesis, characterization, or computational-chemistry result | `chemistry.md` |
| a clinical, epidemiological, or health-outcomes result in human subjects | `medicine.md` |
| a method, model, system, or empirical result in CS / ML / NLP | `cs-ml.md` |
| none of the above, or genuinely cross-cutting | `_generic.md` |

**Hybrid papers.** If the paper's core claim is formal (a proof or derivation)
**and** it also reports substantive numerical, computational, or simulation
results in support of that claim, read the matching profile **and**
`_numerical-slice.md`. Do not choose between them.

This rule exists because of a measured regression: under a single
three-way `review_mode` switch, a paper whose contribution was a proof
validated by numerics lost 3 of its 5 reported headline numbers, because the
theoretical framing had no field in which to record them. The overlay restores
the quantitative slice without pretending the whole paper is empirical.

**When the field is ambiguous**, prefer the profile matching the paper's
*method of justification*, not its subject matter. A paper that proves a
theorem about a biological network is `math.md`, not `biology.md`.

## Shared vocabulary

Every profile's §11 defers to `../review_vocabulary.md` for the assessment
scales. Read that file once per review, regardless of domain.

## Profile structure

Every profile in this directory has the same twelve sections in the same order.
Sections marked ★ are required; a profile missing one is invalid.

| # | Section | Purpose |
|---|---|---|
| 01 ★ | Front matter | `domain`, `aliases`, `version`, `last_verified` |
| 02 ★ | Detection cues | how to recognise this domain; hybrid handling |
| 03 ★ | Criterion instantiation | what each venue criterion *means here*, plus default gating |
| 04 ★ | What counts as evidence | the extraction fields the Summary phase must fill |
| 05 ★ | Nearest prior work | what the Scout phase should hunt for in this domain |
| 06 ★ | Verifiability checks | each tagged automatic / semi-automatic / manual |
| 07 | Reporting standards | conditional hooks; may be "none" but the section stays |
| 08 ★ | Red lines | boolean blockers, scored separately from criteria |
| 09 ★ | Anti-patterns | questions that must never be generated, with replacements |
| 10 | Seed questions | per-criterion starters and where the answer should live |
| 11 ★ | Output vocabulary | defers to `../review_vocabulary.md`; notes domain deviations |
| 12 ★ | Provenance | sources, retrieval dates, and which claims lack a primary source |

`last_verified` is required because reviewing standards move: CONSORT was
revised in 2025, and at least one tool the EQUATOR network still links to has
lapsed and been re-registered by an unrelated party. A profile that does not
say when it was last checked cannot be trusted to still be correct.
