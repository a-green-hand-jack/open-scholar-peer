# OSP CLI User Guide

The standalone OSP CLI is the supported distribution for Open ScholarPeer. It is a Node.js/TypeScript application that owns the review controller and uses OpenCode as its agent runtime.

## What OSP Does

Open ScholarPeer (OSP) is an OpenCode-native paper review agent. The OSP
controller prepares an isolated workspace, imports a paper without modifying
the original, starts an OpenCode session, runs the fixed seven-stage protocol,
validates every stage artifact, and writes a final structured review.

The supported product is the TypeScript/Node.js CLI. The native OpenCode TUI is
the default interface; headless mode uses the same controller for unattended
runs.

## Dependencies

Required on the host:

| Dependency | Minimum | Purpose |
| --- | --- | --- |
| Node.js | 20+ | Runs the OSP CLI |
| npm | Node-compatible | Installs and builds OSP |
| OpenCode | 1.18.25+ | Agent runtime, model access, and TUI |
| Python | 3.10+ | Runs the per-run MCP server |
| Python `venv` and `ensurepip` | available | Creates the isolated MCP environment |
| Git | available | Creates auditable phase checkpoints |
| Poppler `pdftotext` | available for PDF input | Extracts PDF text |

The selected OpenCode provider/model must already be configured and usable.
OSP does not store model credentials in the paper, workspace artifacts, or
command arguments.

Online runs require network access to the model provider and literature
providers. Offline mode disables web access and does not prepare the networked
MCP server.

### Optional Providers

Bohrium LKM is the primary broad-coverage literature source when installed and
authenticated:

```bash
npm install -g @dptech-corp/bohr-cli
bohr auth login
bohr auth status
```

The CLI must also receive `--allow-lkm-spend` for each run that may make
billable LKM calls. LKM search calls cost approximately `0.05 CNY` each;
optional PDF parsing costs approximately `1.00 CNY` initially or `0.10 CNY`
for a cache hit. OSP never handles or logs Bohrium credentials.

Semantic Scholar works without a key under anonymous rate limits. Set a key
only when higher rate limits are needed:

```bash
export SEMANTIC_SCHOLAR_API_KEY="<your-key>"
```

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/main/install_cli.sh | bash
osp doctor
```

The installer copies OSP into an isolated data directory, installs Node
dependencies, builds the CLI, and creates `osp` and `open-scholar-peer` links
under `${XDG_BIN_HOME:-$HOME/.local/bin}`. It refuses to overwrite an
unrelated executable at either link path.

To install from the current checkout instead of the published `main` branch:

```bash
OSP_SOURCE_DIR="$PWD" bash install_cli.sh
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
```

For development:

```bash
npm install
npm run build
node dist/cli.js doctor
```

Verify the selected executable after either installation method:

```bash
command -v osp
osp --version
osp doctor
```

## First Run

Validate the input and local setup without starting OpenCode:

```bash
osp review ./paper.pdf --output ./osp-review --prepare-only
```

Then start a complete autonomous headless review:

```bash
osp review ./paper.pdf \
  --output ./osp-review \
  --headless \
  --mode autonomous \
  --model <provider/model> \
  --allow-lkm-spend
```

Replace `<provider/model>` with a model already configured in OpenCode. Omit
`--allow-lkm-spend` when LKM spending is not authorized; the run will use
other available providers and retain the limitation in provenance.

## Runtime

```bash
osp review <pdf-or-tex-source> [options]
```

The command creates a timestamped isolated workspace, imports the source, installs canonical OSP assets from `extensions/_shared`, prepares the local MCP server, initializes Git state, and starts the fixed seven-phase controller. Native TUI mode is the default. `--headless` uses the same controller without attaching `opencode attach`. `--qa-pairs` persists the positive number of ordered Q&A pairs per criterion.

Important options are `--mode autonomous|collaborative`, `--model provider/model`, `--variant`, `--timeout`, `--qa-pairs`, `--network-policy online|offline`, `--output`, `--prepare-only`, and `--allow-lkm-spend`.

Supported input types are PDF files, TeX directories, ZIP/TAR archives, and
existing OSP workspaces. Input is copied into a read-only `source/` directory;
symlinks, special files, sensitive credentials, archive path traversal, and
external directory access are rejected.

`--qa-pairs <count>` defaults to `2` and controls the number of ordered Q&A
pairs generated for every criterion. Larger values increase model usage and
runtime.

Use collaborative mode when a human should inspect each completed phase:

```bash
osp review ./paper.pdf --output ./osp-review --mode collaborative
```

When the run reaches `gate_waiting`, inspect it and release the gate from
another terminal:

```bash
osp status <run-directory>
osp approve <run-directory>
```

Autonomous mode does not wait for questions or approval gates.

## Seven-Stage Workflow

OSP always executes the following order:

```text
onboarding -> summary -> literature -> historian -> baseline_scout -> qa -> review
```

1. **Onboarding** identifies the domain, venue, review mode, criteria, and
   review guidelines; it also records provider availability and creates Q&A
   scaffolds.
2. **Summary** extracts claims, methods, datasets, baselines, metrics, results,
   limitations, and evidence anchors from the paper.
3. **Literature** performs exactly three auditable rounds: sub-domain anchor,
   method anchor, and temporal expansion. LKM is attempted first, with
   arXiv/Semantic Scholar context and tightly gated Google Scholar fallback.
4. **Historian** builds the field narrative and checks whether the novelty
   framing matches the retrieved prior work.
5. **Baseline Scout** searches for missing or outdated baselines and unfair
   comparisons, including compute/token/call-budget mismatches.
6. **Q&A** generates the configured number of evidence-focused question/answer
   pairs for every onboarding criterion. Unknown claims remain unresolved or
   not assessable.
7. **Review** consolidates the evidence into the final report with criterion
   scores, evidence anchors, limitations, and a controlled recommendation.

Every raw artifact and the final review contains `## Method`, `## Output`, and
`## Provenance`. The controller validates these sections and the expected
structure before allowing the next phase.

## Run Outputs

Each invocation creates a directory like:

```text
osp-review/
└── osp-<timestamp>-<random>/
    ├── source/                       read-only imported paper
    ├── .brain/                       phase artifacts and final review
    ├── .osp-run/                     controller state and source manifest
    ├── .opencode/                    installed OSP commands and personas
    ├── .open-scholar-peer/mcp/       isolated MCP server and Python venv
    └── opencode.json                 per-run permissions and MCP config
```

The final report is:

```text
<run-directory>/.brain/review/final_review.md
```

Intermediate artifacts are under `.brain/raw/`. `.osp-run/run.json` records
phase status, model scope, input digest, and resume state. The original input
is never edited.

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
