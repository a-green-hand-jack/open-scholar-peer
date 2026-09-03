# Open ScholarPeer

Open ScholarPeer (OSP) is an independent OpenCode-native Paper Review Agent for the ScholarPeer seven-stage review protocol. It provides a TypeScript/Node.js CLI, a native OpenCode TUI mode, and a headless mode for unattended runs.

## Install

Requirements: Node.js 20+, OpenCode 1.18.25+, Python 3.10+ with `venv`, and Poppler `pdftotext`/`pdfinfo` for PDF input and optional LKM PDF extraction.

```bash
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/main/install_cli.sh | bash
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
osp doctor
```

To install from a checkout instead of the published `main` branch:

```bash
OSP_SOURCE_DIR="$PWD" bash install_cli.sh
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
```

For development, build and invoke the CLI directly:

```bash
npm install
npm run build
node dist/cli.js review ./paper.pdf
```

See [`docs/OSP_CLI.md`](docs/OSP_CLI.md) for the complete user guide,
dependency list, workflow, and recovery procedures.
For the supported agent-agnostic Harbor benchmark invocation, see
[`docs/HARBOR.md`](docs/HARBOR.md).

## Review

```bash
osp review ./paper.pdf
osp review ./paper.pdf --headless --mode autonomous --model openai/gpt-5.6-sol
osp review ./paper.zip --output ./osp-review --mode collaborative
```

For the recommended online run with Bohrium LKM enabled:

```bash
npm install -g @dptech-corp/bohr-cli
bohr auth login
osp review ./paper.pdf \
  --output ./osp-review \
  --headless \
  --mode autonomous \
  --model <provider/model> \
  --allow-lkm-spend
```

`--allow-lkm-spend` is required for billable LKM calls. Without it, OSP can
still run with the other available literature providers and records LKM as
unavailable. Use `--prepare-only` to validate the input and local runtime
before starting a model session.

Without `--headless`, OSP starts an OpenCode server and attaches the native `opencode attach` TUI. `--headless` uses the same controller without attaching a terminal UI. Modes are `autonomous` and `collaborative`; the latter pauses at phase gates until approved.

The default `--network-policy scholarly` permits the bundled academic MCP
providers while denying generic OpenCode web tools. Use `online` only when the
review explicitly needs generic web access, or `offline` to disable the
networked MCP runtime. The complete Harbor-ready command and its stable output
paths are in [`docs/HARBOR.md`](docs/HARBOR.md).

Useful commands:

```bash
osp status <run> [--json]
osp validate <run> [--json]
osp approve <run>
osp resume <run>
osp checkpoint <run>
osp doctor
```

## Protocol

OSP always runs the same ordered protocol:

```text
onboarding -> summary -> literature -> historian -> baseline_scout -> qa -> review
```

Literature has three auditable rounds. Q&A creates exactly the configured number of pairs for every criterion. Each artifact uses `## Method`, `## Output`, and `## Provenance`. Final output is report-only and never modifies the imported source.

Each run is isolated and contains `.brain/` artifacts, `.osp-run/` controller state, `.opencode/` OSP assets, a read-only `source/`, and Git checkpoint commits. Source manifests, digests, unresolved evidence, model metadata, and retrieval provenance are retained in the run workspace.

Supported inputs are PDF files, TeX directories, ZIP/TAR archives, and existing OSP workspaces. Sensitive files, symlinks, special files, archive path escapes, and external directory access are rejected.

## Dependencies

The runtime requires Node.js 20+, OpenCode 1.18.25+, Python 3.10+ with
`venv`/`ensurepip`, Git, and Poppler `pdftotext` for PDF input. Online runs
also need network access to the selected model provider and literature
providers. The per-run MCP Python environment is installed automatically.

Optional integrations are Bohrium `bohr` CLI for LKM retrieval and a Semantic
Scholar API key for higher rate limits. Check the local installation with:

```bash
node --version
python3 --version
python3 -c "import ensurepip, venv"
pdftotext -v
git --version
opencode --version
osp doctor
```

## Development

```bash
npm run typecheck
npm run build
npm run lint
npm test
python3 -m unittest discover tests -p 'test_*.py'
```

The canonical OSP commands, personas, defaults, and rules are in [`extensions/_shared`](extensions/_shared). The Python MCP server and academic providers are in [`mcp-server`](mcp-server). Other coding-agent adapters and their installers are intentionally not part of this project.

See [`docs/OSP_CLI.md`](docs/OSP_CLI.md) for runtime details and [`docs/ARTIFACT_CONTRACTS.md`](docs/ARTIFACT_CONTRACTS.md) for the phase contracts.

## License

MIT.
