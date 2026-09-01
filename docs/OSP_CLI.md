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
stable exported review is `--output/final_review.md`, while the complete run —
including its `.brain/` state — is in `--output/osp-<timestamp>-<digest>/` (see
[Run directory layout](#run-directory-layout)).

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

## Run directory layout

Each run is a self-contained workspace below `--output` (the printed
`osp-<timestamp>-<digest>-<rand>` directory). Nothing about a run lives in the
caller's working directory except through the explicit input and `--output`
paths; in particular `.brain/` is created **inside** the run directory, never
at your project root and never next to the input paper.

```
<output>/
├── final_review.md                  ← stable exported review (after completion)
└── osp-<timestamp>-<digest>-<rand>/
    ├── .brain/                      ← session state and phase artifacts
    │   ├── session.json             ← run state machine (venue, criteria, phases)
    │   ├── input/                   ← paper.md + paper.pdf (imported text)
    │   ├── raw/                     ← 00…06 phase artifacts
    │   ├── review/final_review.md   ← canonical final review
    │   └── tmp/                     ← agent scratch space
    ├── source/                      ← read-only copy of the imported paper
    ├── .opencode/                   ← generated OpenCode adapter bundle
    ├── opencode.json                ← run-local OpenCode config (agent `osp-runner`)
    ├── .osp-run/                    ← CLI-owned state
    │   ├── run.json                 ← status, scope, provenance, phase table
    │   ├── source-manifest.json     ← input digest manifest
    │   ├── checkpoints/             ← phase checkpoints (scope-locked)
    │   ├── logs/                    ← per-phase OpenCode event logs
    │   └── opencode-state/          ← OpenCode's sandbox-local state dir
    ├── .open-scholar-peer/mcp/      ← isolated MCP venv (unless `--no-mcp`)
    └── AGENTS.md                    ← report-only agent contract for the run
```

## How a run executes

`osp review` (and `osp resume`) drives the seven OSP phases in order:

`onboarding` → `summary` → `literature` → `historian` → `baseline_scout` →
`qa` → `review`

- Each phase is one `opencode run` invocation against the run-local
  `osp-runner` agent, except `literature`, which runs 3 strategy rounds
  (`k=3`, one invocation per round) before the phase is marked complete.
- After each invocation the CLI re-validates the phase artifacts against the
  artifact contract (required files, `## Method` / `## Output` / `## Provenance`
  sections, no unresolved templates, exact Q&A pair count, round strategy
  labels, final-review dimension table and recommendation vocabulary) before
  advancing.
- Phases may only write inside `.brain/` (plus `.brain/tmp/` scratch). The CLI
  snapshots `.brain/` and the workspace before each invocation and rejects a
  phase that wrote outside its contract.
- A checkpoint is written after preparation and after every phase. `resume`
  refuses any run whose input digest, invocation options, checkpoint artifacts,
  or session state diverged from the last legal checkpoint; it resumes from the
  first incomplete/invalid phase, then re-validates and exports.
- On completion the CLI exports the canonical review to
  `<output>/final_review.md`, then optionally writes an immutable trail
  (`--trail`) or uploads it (`--upload --trail-repo`).

## Provider and sandbox notes

On Linux every OpenCode invocation runs inside a Bubblewrap sandbox that
exposes only the minimum host state:

- `~/.opencode` and `~/.config/opencode` (`account-keys/` key files included)
  are mounted read-only;
- the OpenCode auth store `~/.local/share/opencode/auth.json` is mounted
  read-only when present;
- DNS resolves through `/run/systemd/resolve` on Ubuntu;
- everything else — other home directories, environment variables containing
  API keys — is invisible inside the sandbox.

The model provider therefore must be **self-contained under
`~/.config/opencode`**. For example `--model apex/gpt-5.6-sol` works because
the Apex key is read from `account-keys/apex-gpt.key` inside the mounted
config. Virtual routers whose backends read host credentials outside
`~/.config/opencode` (e.g. `gpt-priority`, which loads Codex OAuth files from
`~/.codex`) fail to initialize inside the sandbox by design; use the concrete
self-contained provider for CLI runs.

## Testing / smoke test

Use these three commands as a layered smoke test of the CLI — an install check,
a free structural test, and a real end-to-end case:

```bash
# 1. Environment prerequisites (also run at the end of the installer)
osp doctor

# 2. Structural test — import + provenance + artifact contract, no model cost
osp review ./paper.pdf --output ./osp-review --prepare-only
#    Expect: "Prepared isolated OSP run: …" then PASS/INFO lines per phase;
#    locked-scope must be PASS. No provider is contacted.

# 3. Real end-to-end case — full 7-phase review (requires a model provider)
osp review ./paper.pdf --output ./osp-review \
  --venue arxiv --mode autonomous --headless \
  --model apex/gpt-5.6-sol --variant medium
#    Expect: <output>/final_review.md, all phases "completed" in
#    `osp status <run>` (or `osp resume <run>` if interrupted).
```

Level 2 is the cheapest way to verify the pipeline wiring without spending
tokens: it runs the same import, isolation, and validation code as a real run
but never contacts a provider. Level 3 is the actual review; on Linux the
model must be self-contained under `~/.config/opencode` (see "Provider and
sandbox notes").
