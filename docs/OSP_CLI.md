# OSP CLI

The standalone OSP CLI is the supported distribution for Open ScholarPeer. It is a Node.js/TypeScript application that owns the review controller and uses OpenCode as its agent runtime.

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/main/install_cli.sh | bash
osp doctor
```

The installer copies the package to an isolated data directory, installs Node dependencies, builds the CLI, and creates `osp` and `open-scholar-peer` links in `${XDG_BIN_HOME:-$HOME/.local/bin}`. It refuses to overwrite an existing unrelated executable at those exact link paths; verify with `command -v osp` and `osp --version`.

## Runtime

```bash
osp review <pdf-or-tex-source> [options]
```

The command creates a timestamped isolated workspace, imports the source, installs canonical OSP assets from `extensions/_shared`, prepares the local MCP server, initializes Git state, and starts the fixed seven-phase controller. Native TUI mode is the default. `--headless` uses the same controller without attaching `opencode attach`. `--qa-pairs` persists the positive number of ordered Q&A pairs per criterion.

Important options are `--mode autonomous|collaborative`, `--model provider/model`, `--variant`, `--timeout`, `--qa-pairs`, `--network-policy online|offline`, `--output`, and `--prepare-only`.

## State and recovery

Run state is stored in `.osp-run/run.json`; OpenCode server/session metadata is in `.osp-run/session.json`; OSP artifacts remain in `.brain/`. Imported source is copied to `source/` and made read-only. Every successful or failed phase creates a Git checkpoint with OSP trailers.

```bash
osp status <run> --json
osp validate <run> --json
osp resume <run>
osp checkpoint <run>
osp approve <run>
```

Resume verifies the locked input digest and scope digest before starting. A collaborative gate is released by `osp approve <run>`; changing mode does not retroactively bypass an existing gate.

## Protocol contract

The controller cannot skip or reorder:

```text
onboarding -> summary -> literature -> historian -> baseline_scout -> qa -> review
```

Literature runs exactly three rounds. Q&A produces exactly `session.json.qa_pairs_per_criterion` pairs for each criterion. The validator checks artifact sections, round strategies, Q&A numbering, final review structure, score rows, recommendation vocabulary, and evidence anchors.

## Troubleshooting

- If `osp` resolves to an older program, inspect `command -v osp`, put the install bin directory first in `PATH`, or invoke the installed `dist/cli.js` directly.
- If PDF preparation fails, install Poppler and verify `pdftotext -v`.
- If MCP preparation fails, use Python 3.10+ with `ensurepip` and `venv`, or pass `PYTHON=/path/to/python` to the installer/runtime.
- If a run fails, keep the workspace, inspect `osp status` and `.osp-run`, then use `osp resume` after addressing the reported cause.
- Dedicated retrieval providers may be unavailable or rate-limited. OSP records that limitation as unresolved provenance; it must not be converted into invented evidence.
