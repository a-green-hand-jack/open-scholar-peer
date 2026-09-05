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
- [x] MCP retrieval server compiled into the CLI build
- [x] OpenCode server/session integration
- [x] Headless controller and native TUI attach path
- [x] Autonomous and collaborative gate policy with `osp approve`
- [x] Artifact validation, Git checkpoints, scope checks, and resume
- [x] Versioned downstream contracts and stable final-review delivery manifest
- [x] Harbor material-manifest import and explicit submission-path export
- [x] Scholarly, online, and offline network policies
- [x] Real PDF end-to-end review producing final review output
- [x] TypeScript, lint, install, and validation tests

## Verification

```bash
npm run typecheck
npm run build
npm run lint
osp doctor
osp review docs/paper/scholar_peer_arxiv.pdf --output /tmp/osp-e2e --headless --mode autonomous
osp validate /tmp/osp-e2e/<run>
```

```bash
docker build -t open-scholar-peer:dev .
docker run --rm open-scholar-peer:dev
```

For the six-task Harbor acceptance run and its pinned, agent-agnostic
submission contract, see [`HARBOR.md`](HARBOR.md).

## Scope

The former per-tool adapter directories, installers, parity scripts, sync pipeline, and Python CLI are retired. OSP is distributed as an OpenCode-native CLI.
