# Contributing to Open ScholarPeer

OSP is an OpenCode-native TypeScript Agent. The TypeScript runtime owns orchestration, validation, input isolation, checkpoints, resume, and TUI/headless integration. Markdown assets under `extensions/_shared/` define the OSP personas and review method; edit those assets directly.

## Checks

```bash
npm install
npm run typecheck
npm run build
npm test
```

The sample PDF can be used for a prepare-only check or a real review:

```bash
node dist/cli.js review docs/paper/scholar_peer_arxiv.pdf --output /tmp/osp-review --prepare-only
```

Do not add adapters for other coding agents. Do not modify imported `source/` files. Changes to the seven-stage protocol must update `docs/ARTIFACT_CONTRACTS.md`, `src/phases.ts`, validators, and tests together. Preserve `Method`, `Output`, and `Provenance` in every artifact.
