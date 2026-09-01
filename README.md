# Open ScholarPeer

Open ScholarPeer (OSP) is an independent OpenCode-native Paper Review Agent for the ScholarPeer seven-stage review protocol. It provides a TypeScript/Node.js CLI, a native OpenCode TUI mode, and a headless mode for unattended runs.

## Install

Requirements: Node.js 20+, OpenCode 1.18.25+, Python 3.10+ with `venv`, and Poppler `pdftotext` for PDF input.

```bash
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/main/install_cli.sh | bash
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
osp doctor
```

For a checkout:

```bash
npm install
npm run build
node dist/cli.js review ./paper.pdf
```

## Review

```bash
osp review ./paper.pdf
osp review ./paper.pdf --headless --mode autonomous --model openai/gpt-5.6-sol
osp review ./paper.zip --output ./osp-review --mode collaborative
```

Without `--headless`, OSP starts an OpenCode server and attaches the native `opencode attach` TUI. `--headless` uses the same controller without attaching a terminal UI. Modes are `autonomous` and `collaborative`; the latter pauses at phase gates until approved.

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

## Development

```bash
npm run typecheck
npm run build
npm test
python3 -m unittest tests/test_osp_cli.py
```

The canonical OSP commands, personas, defaults, and rules are in [`extensions/_shared`](extensions/_shared). The Python MCP server and academic providers are in [`mcp-server`](mcp-server). Other coding-agent adapters and their installers are intentionally not part of this project.

See [`docs/OSP_CLI.md`](docs/OSP_CLI.md) for runtime details and [`docs/ARTIFACT_CONTRACTS.md`](docs/ARTIFACT_CONTRACTS.md) for the phase contracts.

## License

MIT.
