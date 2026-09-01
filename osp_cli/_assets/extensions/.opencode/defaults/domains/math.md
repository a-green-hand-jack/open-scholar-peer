# Domain Profile — Mathematics

## 01. Front matter

```yaml
domain: math
aliases: [mathematics, pure-math, math-logic, combinatorics, number-theory,
          analysis, topology, algebra, probability-theory]
version: 1
last_verified: 2026-08-30
```

## 02. Detection cues

- arXiv primary category under `math.*`, or `cs.DM` / `cs.CC` with theorem-proof structure
- An MSC classification number
- Section headings of the form "Proof of Theorem 1", "Lemma", "Corollary", "Preliminaries"
- No "Experimental Section", no dataset table, no reported runtime
- References dominated by mathematics journals and arXiv `math.*` preprints

**Hybrid:** if the paper proves a result *and* reports computational search,
numerical verification, or machine-checked cases, also read
`_numerical-slice.md`. Papers resolving finite cases by computer search are
common in combinatorics and number theory and are frequently misfiled as purely
theoretical, losing every reported quantity.

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
| `novelty` | Is the result, or the proof strategy, new relative to the literature? Resolving an open problem, sharpening a known bound, or giving a materially different argument for a known result all qualify. A cited-but-unnoticed equivalent result is the main risk. | `true` |
| `technical-soundness` | Are definitions precise, are hypotheses complete and actually used, does each step follow, are degenerate and boundary cases handled rather than assumed away? | `true` |
| `clarity` | Can a competent reader in the subfield follow each step from the text and its citations alone, without reconstructing omitted steps? Is notation defined before use and used consistently? | `false` |
| `significance` | Does the result close a known gap, strengthen a known bound, or open a new line of argument — or is it a routine specialisation of standard technique? | venue-set |
| `reproducibility` | Read as **independent verifiability**: are enough intermediate steps, cited lemmas, and explicit constants present that an expert could reconstruct the argument? Not about released code. | `false` |

### 0–5 anchors

The band semantics in `../review_vocabulary.md` say what a 2 or a 4 means in
general. These say what it means *here*. Quote the assigned band in the score
table's third column.

**`novelty`**
`0` the result already appears in the paper's own references ·
`1` a direct special case or restatement of a known theorem ·
`2` a routine extension of standard technique to an adjacent setting ·
`3` genuinely new but close to the nearest prior result, or new only in technique ·
`4` resolves a known open problem, or materially sharpens a known bound ·
`5` introduces a method or framework likely to change how the subfield attacks the problem

**`technical-soundness`**
`0` a definite counterexample or logical error in the proof ·
`1` a lemma the argument depends on does not hold, or the dependency chain is circular ·
`2` the main line is plausible but several load-bearing steps are missing and need the author to supply them ·
`3` the argument holds; individual steps are compressed and degenerate or boundary cases go undiscussed ·
`4` complete argument; only presentation or secondary estimates could improve ·
`5` every step checkable by an expert from the text and its citations, with degenerate cases handled explicitly

**`clarity`**
`0` the argument cannot be followed at all as written ·
`1` notation is inconsistent or used before definition in ways that change meaning ·
`2` a specialist must reconstruct substantial structure to follow the proof ·
`3` followable, with passages that need rereading and some forward references ·
`4` clear throughout; minor wording or numbering improvements only ·
`5` structure and notation make the argument easy to verify step by step

**`significance`**
`0` the question addressed is already settled and the paper does not say so ·
`1` narrow technical remark with no consequence beyond itself ·
`2` routine specialisation of standard technique ·
`3` closes a real gap within the subfield ·
`4` strengthens a known bound or opens a line of argument others will use ·
`5` changes how researchers in the subfield think about the problem

**`reproducibility` (Independent Verifiability)**
`0` the argument cannot be reconstructed from what is written ·
`1` several load-bearing constants or dependencies are missing ·
`2` an expert must guess substantial omitted steps ·
`3` an expert can complete it, deriving some intermediate steps unaided ·
`4` constants and dependency chain essentially complete; a few left implicit ·
`5` constants, dependencies, and imported results all explicit, and any computational step is given with re-runnable parameters

Where the paper has a computational component, `_numerical-slice.md` governs how
its instances, precision, and independence bear on the `technical-soundness` and
`reproducibility` bands.

## 04. What counts as evidence

Evidence in this domain is the argument itself. The Summary phase must extract
these fields; each becomes a row the later phases can cite:

| Field | Content |
|---|---|
| `main_results` | Each theorem/proposition as stated, with its number |
| `hypotheses` | The standing assumptions of each main result, verbatim where short |
| `lemma_chain` | Which lemmas each main result depends on, including imported results |
| `proof_technique` | The named strategy (induction, probabilistic method, compactness, generating functions, …) |
| `prior_results_used` | External theorems invoked, with citation, and *what they are used for* |
| `explicit_constants` | Any constant, bound, or exponent the paper claims, with its scope of validity |
| `computational_component` | Present / absent. If present, `_numerical-slice.md` also applies |

Record a field as **not stated** when the paper does not supply it. Never
substitute a plausible value.

## 05. Nearest prior work

The Scout phase hunts for the **closest competing or superseding results**, not
for baselines. Specifically:

- A theorem that already implies the paper's main result, in whole or as a special case
- A sharper bound, or the same bound under weaker hypotheses
- The same statement proved by a different technique, which may reduce the novelty claim to the technique alone
- A known counterexample bounding how far the result can extend
- Prior work the authors cite for a technique but not for a result that subsumes theirs

Frame every finding as "this result appears to be implied by / sharpened by /
already proved in X" with the citation, or as a question when retrieval is
inconclusive. **Never** report a "missing baseline" or a "missing dataset".

## 06. Verifiability checks

| Check | Tier |
|---|---|
| Every numbered theorem/lemma referenced in a proof exists in the paper | automatic |
| No lemma's proof depends on a result stated later without forward reference | automatic |
| Every external theorem invoked has a citation | automatic |
| Constants and exponents used downstream match where they were introduced | semi-automatic |
| Hypotheses of a cited theorem are actually satisfied where it is applied | manual |
| Each proof step follows from the stated assumptions | manual |
| Degenerate and boundary cases are handled | manual |

Only `automatic` findings may be stated as fact. `semi-automatic` findings are
stated as "appears inconsistent — please confirm". `manual` findings enter the
verification agenda as questions and are **never** reported as verdicts.

## 07. Reporting standards

**No mandatory reporting standard exists for this domain.** No formal-verification
policy was found at any major mathematics publisher checked; machine-checked
proofs remain a voluntary supplement. Applicable conventions are limited to
arXiv category fit, an MSC number, and AI-use disclosure.

If the paper *does* ship a formalization (Lean, Coq, Isabelle), treat it as a
strength to verify, not a requirement whose absence is a weakness.

## 08. Red lines

Boolean blockers. Reported separately; never traded against strengths.

- A main result is stated without proof and without citation to where it is proved
- A cited result is misstated in a way that changes what it yields
- The same result is claimed as new when the paper's own references contain it
- A computational step is load-bearing but neither code nor certificate is available
- Plagiarism, duplicate submission, or undisclosed overlap with the authors' prior work

## 09. Anti-patterns — never generate these

The failure mode this profile exists to prevent is asking machine-learning
questions of a proof. Each row is a question class that must not be produced.

| Never ask | Ask instead |
|---|---|
| "What baselines were compared against?" | "Which prior theorem is closest, and does it already imply this one?" |
| "Were ablations performed?" | "Which hypotheses are load-bearing — does the result survive dropping each?" |
| "Which datasets were used?" | "Which worked examples or special cases are checked, and are they representative?" |
| "Are hyperparameters disclosed?" | "Are the constants explicit, and is their range of validity stated?" |
| "Is the code released?" | "Are the omitted steps recoverable by an expert from what is written?" |
| "Would this generalize to another dataset or larger scale?" | "Does the argument extend to weaker hypotheses, or is there a known obstruction?" |
| "How does this compare to state of the art?" | "Is this the sharpest known bound, and under which hypotheses?" |
| "Is the improvement statistically significant?" | "Is the improvement in the bound asymptotic, constant-factor, or in the hypotheses?" |

Do not merely rephrase a forbidden question in domain vocabulary. If a question
has no meaningful form here, drop it and use the criterion's remaining budget
on a different angle.

## 10. Seed questions

- `technical-soundness` — "Theorem N assumes H. Where in the proof is H used, and does the argument survive its removal?" (look in the proof body)
- `technical-soundness` — "Does the argument cover the degenerate case where [parameter] vanishes, or is it implicitly excluded?" (look in the statement's hypotheses)
- `novelty` — "Reference [X] proves a related bound. Is this result stronger, or a restatement under different notation?" (look in the introduction and related work)
- `reproducibility` — "Step S is asserted as immediate. Can it be reconstructed from the cited results alone?" (look in the proof body)
- `clarity` — "Symbol σ appears in Lemma 3 before its definition in §4. Is this a forward reference or an inconsistency?" (look across sections)

## 11. Output vocabulary

Use `../review_vocabulary.md` unchanged. Strength of evidence rates **the
argument**, not experiments: `convincing` means the proof is complete and
checkable as written, not that measurements were adequate.

Domain-specific constraint: the *"never claim a proof is correct"* rule in that
file applies with full force here. Report what a referee should check and why
each step is load-bearing.

## 12. Provenance

| Claim | Source | Retrieved |
|---|---|---|
| Correctness as an ethical obligation of editors and referees | AMS Ethical Guidelines, §on publication | 2026-08-30 |
| Unchecked portions must be declared in the report | Notices of the AMS, "How to Referee" (signed article, community practice, not policy) | 2026-08-30 |
| Two mandatory referee scales | SIAM Instructions for Referees | 2026-08-30 |
| Moderation is explicitly not peer review | arXiv moderation and endorsement policy pages | 2026-08-30 |
| No formal-verification policy at major publishers | Absence across AMS, Annals, SIAM, LMS, Springer pages retrieved | 2026-08-30 |

**Not established from a primary source:** Annals of Mathematics publishes no
review criteria at all; the criterion instantiation in §03 is therefore derived
from the AMS/SIAM/Notices sources above plus general practice, not from a
top-venue rubric. Treat §03 gating defaults as conventions, not as policy.
