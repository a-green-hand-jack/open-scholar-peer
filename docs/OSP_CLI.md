# OpenCode-native OSP CLI

`osp` is the standalone Open ScholarPeer runner. It owns input isolation,
OpenCode invocation, phase ordering, checkpoints, provenance, and final-review
export. It does not replace the canonical OSP commands, skills, defaults, or
adapter generation under `extensions/_shared/`.

## Install

From a source checkout:

```bash
python3 -m pip install --user .
```

This installs both `osp` and `open-scholar-peer` command names. The wheel
contains a generated OpenCode adapter bundle; regenerate it after changing
canonical adapter content:

```bash
python3 scripts/sync_adapters.py
python3 scripts/build_cli_assets.py
```

## Review

```bash
osp review ./paper.pdf \
  --output ./osp-review \
  --venue arxiv \
  --mode autonomous \
  --headless \
  --model openai/gpt-5.6-sol \
  --variant medium
```

Supported inputs are PDFs, TeX source directories, `.zip` / `.tar.gz` source
archives, and an existing OSP workspace. Every invocation creates a new
timestamped directory below `--output`; it never edits the input source. The
stable exported review is `--output/final_review.md`, while the complete run is
in `--output/osp-<timestamp>-<digest>/`.

`--headless` is an explicit opt-in to OpenCode's autonomous permission mode.
The CLI runs only in an isolated workspace, instructs the agent to write only
review artifacts, records the policy in provenance, and does not copy `.env`,
credentials, `.git`, old `.brain` artifacts, or `.open-scholar-peer` runtimes.

Optional inputs include `--domain`, `--brief`, `--previous-review`, and
`--revision-context`. `--provider` prefixes a model which lacks a provider
component. `--timeout` applies to each OpenCode phase. `--network-policy` is
recorded in the locked run scope for auditable retrieval behavior.

## Lifecycle commands

```bash
osp doctor
osp status ./osp-review/osp-20260901T120000Z-abc123
osp validate ./osp-review/osp-20260901T120000Z-abc123
osp checkpoint ./osp-review/osp-20260901T120000Z-abc123
osp resume ./osp-review/osp-20260901T120000Z-abc123
```

`resume` refuses a run whose locked input digest or invocation scope has
changed. It resumes from the first incomplete/invalid phase and retains logs,
session state, artifacts, and every phase checkpoint. Final export is rejected
until phases 0–5 completed under the artifact contract.

Use `--prepare-only` to validate import and provenance without contacting an
OpenCode provider. `--trail <directory>` produces a non-overwriting local trail
containing the final review and minimum reproduction metadata. `--upload`
requires both the explicit flag and `--trail-repo`; upload failure returns a
non-zero status.
