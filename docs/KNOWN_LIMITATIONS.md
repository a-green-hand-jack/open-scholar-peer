# Known Limitations

These limitations apply to the supported TypeScript/OpenCode-native CLI.

## Retrieval availability

The literature phase uses the bundled arXiv, Semantic Scholar, and Google Scholar providers. Anonymous Semantic Scholar access is rate-limited, and Google Scholar is best-effort HTML retrieval. Provider failures are preserved as unresolved provenance; the runtime never treats unavailable evidence as a citation.

## PDF conversion

PDF preparation requires Poppler `pdftotext`. The imported PDF and extracted `paper.md` are kept inside the isolated run workspace. Scanned PDFs without an extractable text layer require a manually supplied readable source.

## One paper per run

Each isolated run reviews one paper. Start another `osp review` command for a second paper rather than sharing `.brain/` state.

## Fixed literature depth

The protocol always executes three literature rounds: `sub-domain-anchor`, `method-anchor`, and `temporal-expansion`. This depth is intentionally fixed by the artifact contract.

## Configurable Q&A cost

`--qa-pairs <count>` controls the positive number of ordered Q&A pairs per criterion. Larger values increase model cost and runtime. Q&A output can still require controller remediation when a provider returns an incomplete structure.

## Downstream invalidation

Re-running an earlier phase does not automatically invalidate later artifacts. Use `osp resume` and inspect `osp validate`; rerun downstream phases when an upstream artifact has changed.

## Provider sandbox constraints

OpenCode runs with the run-local permissions configured by OSP. Network retrieval is controlled by `--network-policy`; offline runs must report unavailable external evidence. Review agents must write scratch files only under `.brain/tmp/` and may not modify the imported `source/` directory.

## Python reference package

`osp_cli/` remains as a behavior reference for migration tests. It is not the supported CLI distribution and does not expose the `osp` console entry points. Use the Node.js package and `install_cli.sh` for releases.
