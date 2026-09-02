# Contributing

Open ScholarPeer is an OpenCode-native TypeScript Agent. The runtime is in `src/`; canonical OSP prompts, personas, rules, and defaults are in `extensions/_shared/`; the retained Python MCP server is in `mcp-server/`.

## Checks

```bash
npm install
npm run typecheck
npm run build
npm test
python3 -m unittest discover tests -p 'test_*.py'
```

## Changes

Changes to the seven-stage protocol must update `src/phases.ts`, `docs/ARTIFACT_CONTRACTS.md`, validators, and tests together. Preserve the original phase order, literature round strategies, configurable Q&A pair count, and `Method`/`Output`/`Provenance` artifact structure.

Do not add per-tool adapters or installers. Do not modify imported `source/` files. Runtime changes must preserve source isolation, scope digest checks, Git checkpoints, and report-only review behavior.

## Runtime smoke test

```bash
node dist/cli.js doctor
node dist/cli.js review docs/paper/scholar_peer_arxiv.pdf --output /tmp/osp-review --prepare-only
```

The full real review requires an available OpenCode provider and may use the academic retrieval MCP server. Keep failed workspaces for diagnosis and report unavailable tools as unresolved provenance.
