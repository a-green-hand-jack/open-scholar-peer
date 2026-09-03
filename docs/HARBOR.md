# Harbor Benchmark Contract

Open ScholarPeer is a standalone OpenCode-native CLI. It does not add a
Harbor-specific agent, task wrapper, or benchmark fork. A Harbor agent invokes
the released `osp` CLI inside the task environment, and OSP writes the standard
submission file itself.

## Task inputs

The Paper-Reviewing-Exam task layout supplies:

```text
/workspace/paper/                    sanitized manuscript material
/workspace/material-manifest.json    task-wide material manifest
```

When its input is `/workspace/paper`, OSP reads a `material-manifest.json`
either inside that directory or immediately next to it. The manifest's
`manuscript_pdf` is resolved only relative to `/workspace/paper`; a missing,
malformed, or escaping pointer fails closed. OSP imports that material into its
own read-only `source/` tree and records the input digest and manifest fields in
the run state.

## Released CLI invocation

Provision a pinned OSP release in the agent environment, then use this command:

```bash
export OSP_REF=v2.2.0
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/$OSP_REF/install_cli.sh | bash
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"

osp review /workspace/paper \
  --output /workspace/osp-review \
  --final-output /workspace/submission/review.md \
  --trail /workspace/submission/osp-trail \
  --headless \
  --mode autonomous \
  --network-policy scholarly \
  --model openai/gpt-5.6-sol
```

Replace the model with the configured OpenCode provider/model. Provider
credentials are passed by Harbor as environment variables; do not put them in
the task, OSP arguments, run state, or trail.

On success, the required file is at `/workspace/submission/review.md`. OSP also
writes stable machine-readable outputs at
`/workspace/osp-review/final_review.md` and
`/workspace/osp-review/run-manifest.json`. The optional submission-local trail
keeps the final review, source manifest, run state, provenance, session state,
and redacted retrieval-event log for Harbor to archive as task output.

## Network policy

`scholarly` is the default benchmark policy. It permits OSP's academic MCP
providers while denying generic OpenCode `webfetch` and `websearch`. The
benchmark's scholarly allowlist must include its normal agent-install and
provider hosts plus arXiv, Semantic Scholar, OpenAlex, Crossref, DOI, Bohrium,
and Google Scholar. `online` additionally enables generic OpenCode web tools;
`offline` disables OSP's networked MCP server.

## Versioned compatibility

Each run records these contracts in `.osp-run/run.json`,
`.osp-run/provenance.json`, and the stable `run-manifest.json`:

```text
brain_layout       2.2
artifact_contract  2.2
final_review       2.2
run_state          osp-run-v2
```

`osp validate` rejects missing or incompatible contract versions. Archive only
trails whose validation succeeds; this prevents a benchmark collector from
silently accepting an output written by an incompatible OSP release.

## Acceptance run

Run the six canonical benchmark task names under one pinned exam revision with
Harbor's scholarly network preset and preserve `/workspace/material-manifest.json`
as an artifact. Every trial must finish with a substantive
`/workspace/submission/review.md`, and the OSP trail must contain matching
contract versions and a source manifest. The Harbor reward proves the
submission contract only; it is not a review-quality score.
