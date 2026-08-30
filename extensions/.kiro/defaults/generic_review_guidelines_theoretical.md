# Generic Peer Review Guidelines — Theoretical / Proof Papers (Fallback)

Used when:
1. The user did not specify a venue at onboarding, OR
2. Web search failed to retrieve the venue's official review form, AND
3. The user could not provide review guidelines manually, AND
4. `paper.review_mode == "theoretical"` (see `0-osp-onboarding.md` step 3.5) — the paper's core contribution is a proof, derivation, or formal result rather than an experimental/empirical claim.

This file exists because `generic_review_guidelines.md` was derived from ML/NLP/CS conference review forms (baselines, ablations, datasets, hyperparameters). Those concepts do not apply to a pure mathematical proof, a theoretical-physics derivation, or similar formal work, and forcing them onto such a paper produces vestigial or fabricated review content. Use this file instead for that population of papers.

## Default criteria

| Slug | Label | Definition |
|---|---|---|
| `novelty` | Novelty & Originality | Is the result, proof strategy, or framing substantively new relative to prior work? Does it resolve an open problem, sharpen a known bound, or offer a materially different argument for an already-known result? |
| `technical-soundness` | Technical Soundness | Are the definitions, lemmas, and proof steps correct? Does each step follow from the stated assumptions? Are edge cases (degenerate inputs, boundary conditions, singular cases) handled, or silently assumed away? If the paper includes numerical/computational validation of its result, is that validation methodologically adequate (representative instances, disclosed precision, no circular reasoning)? |
| `clarity` | Clarity & Presentation | Is the notation consistent and defined before use? Is the logical structure of the argument easy to follow? Could a competent reader in the sub-field verify each step from the text and cited results alone, without reconstructing missing steps? |
| `significance` | Significance & Impact | Does the result close a known gap, strengthen a known bound, or open a new line of argument? Would it change how researchers in the sub-field think about the problem, or is it a routine specialization of known techniques? |
| `reproducibility` | Independent Verifiability | Are enough intermediate steps, cited lemmas, and explicit constants provided that an independent expert could reconstruct and check the proof without guessing omitted steps? If the paper reports numerical/computational validation, are the instances, precision, and code/parameters disclosed well enough to re-run the check? (This is the theoretical-paper analogue of "reproducibility" — it is about verifiability of an argument, not about released code or datasets.) |

Do **not** ask for baselines, ablations, benchmark comparisons, hyperparameters, or released code/data unless the paper itself makes empirical claims that would require them — in that case, apply the relevant slice of `generic_review_guidelines.md`'s `technical-soundness`/`reproducibility` definitions to that slice only, without pretending the whole paper is an empirical ML submission.

## Final review structure (generic — theoretical)

Same skeleton as the empirical generic fallback; only the criteria and framing above differ:

1. **Summary** — 2–3 paragraph précis of the paper's claimed result(s) and proof strategy.
2. **Strengths** — bulleted list grounded in the structured summary + verified Q&A.
3. **Weaknesses** — bulleted list, each item cross-referenced to a discrepancy in the interrogation log, a gap identified in the proof, or a high-severity entry from the Baseline Scout's "closest prior/competing results" audit.
4. **Detailed comments per criterion** — one section per criterion above, citing the relevant `05_qa_<slug>.md`.
5. **Questions for authors** — 3–5 questions raised during the Q&A phase that remain unresolved (e.g. an unjustified step, an ambiguous definition, an unaddressed edge case).
6. **Decision recommendation** — accept / weak accept / borderline / weak reject / reject, with one-paragraph justification.
7. **Confidence** — 1–5 scale with a one-sentence rationale (e.g. "Confidence 3: verified the main construction but could not fully check Appendix B's estimate without redoing the computation.").
