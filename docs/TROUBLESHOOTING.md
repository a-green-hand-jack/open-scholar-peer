# Troubleshooting

## CLI

Check the installation and executable selected by `PATH`:

```bash
command -v osp
osp --version
osp doctor
```

The supported CLI requires Node.js 20+, OpenCode 1.18.25+, Python 3.10+ with `venv`, and Poppler `pdftotext` for PDF input. If an older Python `osp` wrapper is found first, put the directory from `OSP_BIN_DIR` first in `PATH`.

## Preparation

Use prepare-only to isolate input and dependency problems:

```bash
osp review ./paper.pdf --output ./osp-review --prepare-only
```

OSP accepts PDF, TeX directories, ZIP/TAR archives, and existing OSP workspaces. It rejects symlinks, special files, sensitive credentials, archive path traversal, and output directories inside the source.

## Runtime and resume

```bash
osp status <run> --json
osp validate <run> --json
osp resume <run>
```

Do not edit `source/`, `.brain/`, or `.osp-run/run.json` while a run is active. Resume verifies the input and locked scope digests. A failed phase is preserved in Git and can be retried from the same workspace.

In collaborative mode, a run with status `gate_waiting` requires:

```bash
osp approve <run>
```

Autonomous mode never waits for user questions and uses the configured/default venue and domain policy.

## MCP

The MCP server is installed per run at `.open-scholar-peer/mcp/`. If setup fails, provide a Python interpreter with `ensurepip`:

```bash
PYTHON=/path/to/python3 osp review ./paper.pdf --prepare-only
```

Provider failures and rate limits are recorded as unresolved provenance. They must not be replaced with fabricated citations.

## Development

```bash
npm run typecheck
npm run build
npm test
python3 -m unittest tests/test_osp_cli.py
```

The old multi-tool adapter and installer system has been retired. Canonical Markdown assets are under `extensions/_shared/`; do not run or recreate the deleted adapter scripts.
