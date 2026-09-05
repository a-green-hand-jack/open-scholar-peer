# Contributing

Open ScholarPeer is an OpenCode-native TypeScript Agent. The runtime is in `src/`; canonical OSP prompts, personas, rules, and defaults are in `extensions/_shared/`; the MCP retrieval server is in `src/mcp/`.

## Checks

```bash
npm install
npm run typecheck
npm run build
npm run lint
```

## Changes

Changes to the seven-stage protocol must update `src/phases.ts`, `docs/ARTIFACT_CONTRACTS.md`, validators, and tests together. Preserve the original phase order, literature round strategies, configurable Q&A pair count, and `Method`/`Output`/`Provenance` artifact structure.

Do not add per-tool adapters or installers. Do not modify imported `source/` files. Runtime changes must preserve source isolation, scope digest checks, Git checkpoints, and report-only review behavior.

## Docker acceptance test

```bash
docker build -t open-scholar-peer:dev .
docker run --rm -e OSP_MODEL=provider/model open-scholar-peer:dev
```

This runs a real model-backed review in an isolated user-like environment. Pass
provider credentials and optional `OPENCODE_CONFIG` through the container
environment; do not bake secrets into the image.
