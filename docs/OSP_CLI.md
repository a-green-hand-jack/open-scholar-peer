# OpenCode-native OSP CLI

`osp` is the standalone Open ScholarPeer runner. It owns input isolation,
OpenCode invocation, phase ordering, checkpoints, provenance, and final-review
export. It does not replace the canonical OSP commands, skills, defaults, or
adapter generation under `extensions/_shared/`.

## Install

One-command installation from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/main/install_cli.sh | bash
```

The script downloads the selected revision, finds Python 3.10+ with `pip` and
`venv`, and
installs both `osp` and `open-scholar-peer` into an isolated user-owned virtual
environment. Set `OSP_REPOSITORY=owner/repo` or `OSP_REF=branch-or-commit`
before the command to use a fork, non-main branch, or reviewed commit. Set
`OSP_INSTALL_DIR` or `OSP_BIN_DIR` to choose the venv and command locations.
The installer runs `osp doctor` using the installed path. For the default
command location, add it to your shell `PATH` before invoking `osp` yourself:

```bash
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
osp doctor
```

From a source checkout, install the checked-out revision instead:

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/osp doctor
```

This installs both `osp` and `open-scholar-peer` command names. The wheel
contains a generated OpenCode adapter bundle; regenerate it after changing
canonical adapter content:

```bash
python3 scripts/sync_adapters.py
python3 scripts/build_cli_assets.py
```

On Linux, reviews require Bubblewrap (`bwrap`) for filesystem isolation. The
CLI also requires OpenCode 1.18.0 or newer.

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
osp status ./osp-review
osp validate ./osp-review
osp checkpoint ./osp-review
osp resume ./osp-review
```

When the output directory contains more than one run, pass the full printed run
directory instead of its parent.

`resume` refuses a run whose locked input digest or invocation scope has
changed. It resumes from the first incomplete/invalid phase and retains logs,
session state, artifacts, and every phase checkpoint. Final export is rejected
until phases 0–5 completed under the artifact contract.

Use `--prepare-only` to validate import and provenance without contacting an
OpenCode provider. `--trail <directory>` produces a non-overwriting local trail
containing the final review and minimum reproduction metadata. `--upload`
requires both the explicit flag and `--trail-repo`; upload failure returns a
non-zero status.
