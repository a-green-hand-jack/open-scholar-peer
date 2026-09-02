# OSP Runtime Phases

The supported implementation is the TypeScript/OpenCode-native Agent. The controller owns ordering, validation, input isolation, checkpointing, gates, and resume. The review method remains the original ScholarPeer protocol.

## Fixed Protocol

```text
onboarding -> summary -> literature -> historian -> baseline_scout -> qa -> review
```

`literature` always has three auditable rounds: `sub-domain-anchor`, `method-anchor`, and `temporal-expansion`. `qa` creates exactly `qa_pairs_per_criterion` ordered pairs for every onboarding criterion. Every raw artifact and the final review contain `## Method`, `## Output`, and `## Provenance`.

## Runtime Stages

- [x] TypeScript package and Node.js 20+ CLI
- [x] Fixed seven-phase registry and versioned run state
- [x] PDF, TeX directory, ZIP/TAR input import and source digest
- [x] Canonical `_shared` asset installation into isolated `.opencode/`
- [x] Per-run MCP server and Python venv setup
- [x] OpenCode server/session integration
- [x] Headless controller and native TUI attach path
- [x] Autonomous and collaborative gate policy with `osp approve`
- [x] Artifact validation, Git checkpoints, scope checks, and resume
- [x] Real PDF end-to-end review producing final review output
- [x] TypeScript, Python compatibility, install, and validation tests

## Verification

```bash
npm run typecheck
npm run build
npm test
python3 -m unittest discover tests -p 'test_*.py'
osp doctor
osp review docs/paper/scholar_peer_arxiv.pdf --output /tmp/osp-e2e --headless --mode autonomous
osp validate /tmp/osp-e2e/<run>
```

## Scope

The former per-tool adapter directories, installers, parity scripts, sync pipeline, and Python CLI are retired. OSP is distributed as an OpenCode-native CLI.
