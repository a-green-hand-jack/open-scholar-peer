# Domain Overlay — Numerical / Computational Slice

**This is an overlay, not a profile.** It is read *in addition to* a domain
profile, never instead of one. It has no criteria of its own; it adds
extraction fields and question licences covering the quantitative portion of a
paper whose core contribution is formal.

## When this applies

Read this file when the paper's primary claim is a proof, derivation, or formal
result **and** the paper also reports any of:

- computed values, tables of results, or plotted quantities
- a computational search over cases, or machine-checked verification of cases
- simulation, numerical integration, or Monte Carlo output
- runtimes, problem sizes, precision, or tolerance figures
- a claim of agreement between an analytic result and a computed one

One reported number is enough. The trigger is the presence of quantities, not
their prominence.

## Why this overlay exists

A single three-way `theoretical` / `empirical` / `other` classification forced
an all-or-nothing choice. Papers proving a result and validating it numerically
were classified `theoretical`, which replaced the evidence-extraction section
wholesale with a formal-content section. The formal section had **no field in
which a number could be recorded**.

The measured consequence, on a real paper in the benchmark corpus: 3 of its 5
reported headline numbers disappeared from the structured summary, and were
therefore unavailable to every later phase. The reviewer could not cite figures
the paper had plainly reported.

The lesson generalises: **the loss was caused by changing framing without
changing the extraction contract.** Reworded criteria cannot restore a value
that no field captures. This overlay is the contract that captures it.

## Extraction fields

Add these to whatever the domain profile's §04 already requires. They do not
replace any formal-content field — a paper covered by this overlay fills both
sets.

| Field | Content |
|---|---|
| `reported_quantities` | Every headline number the paper states, with its unit, its symbol, and the table or figure it comes from. Record all of them; do not select for importance |
| `computed_vs_claimed` | For each quantity, whether it is computed here or quoted from prior work, with citation |
| `instance_set` | What was actually computed over — which cases, which parameter ranges, how many instances |
| `precision_and_tolerance` | Working precision, convergence tolerance, truncation order, grid or lattice spacing |
| `software_stack` | Named tools and versions; any custom code and whether it is available |
| `agreement_claim` | Exactly what the paper claims the computation shows about the formal result, quoted |
| `exhaustiveness` | Whether the computation is claimed to be exhaustive over a finite set, or illustrative of a general claim |

Record **not stated** when absent. A missing `precision_and_tolerance` is
itself a finding; a fabricated one is a fault.

## What the numerical slice licenses you to ask

These questions are legitimate here and only here. They apply to the
computational portion, never to the proof.

- Is the instance set representative of the claim, or does it sample only the
  easy region of parameter space?
- If exhaustiveness over a finite set is claimed, is the enumeration argued to
  be complete, and where?
- Is the working precision sufficient for the reported number of significant
  figures, or could the claimed agreement be a rounding artifact?
- Is the computation independent of the result it validates, or does it assume
  the theorem it is meant to support? (Circularity is the characteristic
  failure of numerical validation in formal work.)
- Are convergence or stability checks reported, or is a single run presented as
  settled?
- Could an independent party re-run this from what is written — code, inputs,
  parameters, versions?

## What remains forbidden

The overlay does **not** turn the paper into an empirical submission. Every
anti-pattern in the domain profile's §09 still holds. In particular:

| Still never ask | Reason |
|---|---|
| "What baselines does the computation beat?" | The computation validates a claim; it is not competing on a leaderboard |
| "Were ablations run on the numerical setup?" | Ablation presumes a system with removable components |
| "Which benchmark dataset was used?" | The instance set is not a benchmark; ask about representativeness instead |
| "Is the speedup statistically significant?" | Unless the paper itself makes a performance claim, runtime is context, not a result |
| "Why is there no comparison to state of the art?" | The formal result is the contribution; prior *results* belong in the domain profile's §05 |

The distinction to hold: ask whether the computation **supports the claim it is
offered for**. Do not ask whether it wins against anything.

## Effect on assessment

The numerical slice is rated on the strength-of-evidence axis together with the
formal argument, not separately. A rigorous proof with a circular or
underspecified numerical check is not `convincing` — the weakness of the check
is a weakness of the paper's evidence, and should be stated as such rather than
excused because the proof carries the claim.

Where the computation is load-bearing — the result does not hold without it —
and neither code nor certificate is available, that is a **red line** under the
domain profile's §08, not a minor concern.

## Provenance

Derived from the benchmark regression documented in
`paper-review/docs/DOMAIN_ADAPTIVE_AUDIT.md` (Regression #2, open at the time
this overlay was written) and from the reviewing conventions cited in the
mathematics and theoretical-physics profiles. No external reporting standard
governs numerical validation of formal results in these fields; the checks
above are conventions, not policy, and are labelled as such wherever they enter
the review.
