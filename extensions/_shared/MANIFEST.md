# `_shared/` Manifest — Single Source of Truth

This file enumerates every canonical OSP asset under `extensions/_shared/`. The TypeScript runtime installs these assets directly into isolated OpenCode review workspaces; no per-tool adapter generation is performed.

**Rule of thumb:** humans only edit files in `_shared/`. The runtime packages these canonical assets into each isolated OpenCode review workspace.

## Files in `_shared/`

### Skills (8 — one per persona + one orchestrator)

| Path | Persona | Triggered by |
|---|---|---|
| `skills/osp-orchestrator/SKILL.md` | Top-level brain protocol + dispatcher behavior | Any review-related phrasing or `/open-scholar-peer` |
| `skills/osp-summary-agent/SKILL.md` | Internal Compression — extract claims/method/evidence | `/1-osp-summary` |
| `skills/osp-literature-review-agent/SKILL.md` | External retrieval — 3-round strategy | `/2-osp-literature` |
| `skills/osp-historian-agent/SKILL.md` | Domain narrative compression | `/3-osp-historian` |
| `skills/osp-baseline-scout-agent/SKILL.md` | Adversarial baseline auditor | `/4-osp-baseline-scout` |
| `skills/osp-query-agent/SKILL.md` | Probing question generator (main thread) | `/5-osp-qa` |
| `skills/osp-answer-generator-agent/SKILL.md` | Verifier/responder (subagent or self-reflection) | spawned by query agent |
| `skills/osp-reviewer-agent/SKILL.md` | Final synthesis | `/6-osp-review` |

### Commands (8 — one dispatcher + 7 numbered steps)

| Path | Slash command | Notes |
|---|---|---|
| `commands/open-scholar-peer.md` | `/open-scholar-peer` | Stateless dispatcher — reads `session.json`, prints status, advises next command |
| `commands/0-osp-onboarding.md` | `/0-osp-onboarding` | Venue lookup, paper detection, criteria scaffolding |
| `commands/1-osp-summary.md` | `/1-osp-summary` | Invokes Summary Agent |
| `commands/2-osp-literature.md` | `/2-osp-literature` | Invokes Literature Review Agent (3 rounds) |
| `commands/3-osp-historian.md` | `/3-osp-historian` | Invokes Historian Agent |
| `commands/4-osp-baseline-scout.md` | `/4-osp-baseline-scout` | Invokes Baseline Scout Agent |
| `commands/5-osp-qa.md` | `/5-osp-qa` | Invokes Query Agent (loops criteria, delegates to Answer Generator) |
| `commands/6-osp-review.md` | `/6-osp-review` | Invokes Reviewer Agent |

### Rules (always-on)

| Path | Notes |
|---|---|
| `rules/osp-rules.md` | Brain protocol summary — read session.json, load prior artifacts, update session.json, prefer subagent over self-reflection |

### Defaults (templates and fallback content)

| Path | Used by |
|---|---|
| `defaults/generic_review_guidelines.md` | `/0-osp-onboarding` when venue lookup fails and user has no guidelines |
| `defaults/qa_pair_template.md` | `/5-osp-qa` to enforce the N-pair structure per criterion (N = `session.json.qa_pairs_per_criterion`, default 2) |
| `defaults/round_strategy_template.md` | `/2-osp-literature` to enforce the 3-round structure |

## Runtime installation map

`src/config.ts` copies the canonical assets into each isolated review workspace:

| Source | Workspace destination |
|---|---|
| `commands/*.md` | `.opencode/commands/*.md` |
| `skills/*/SKILL.md` | `.opencode/agents/*/SKILL.md` |
| `rules/osp-rules.md` | `.opencode/AGENTS.md` |
| `defaults/**/*.md` | `.opencode/defaults/**/*.md` |

OpenCode provides subagent isolation for Q&A. Autonomous runs deny interactive questions; collaborative runs allow questions and add controller-owned phase gates.
