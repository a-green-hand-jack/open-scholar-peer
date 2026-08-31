#!/usr/bin/env python3
"""
test_parity.py — Verify per-tool adapter parity against `extensions/_shared/`.

For every canonical command and skill in `_shared/`, every tool's adapter
directory must contain an equivalent file. This catches:
  - Adapter files deleted by hand and not regenerated.
  - Sync script bugs that drop a file silently.
  - New canonical content forgotten in the sync transformer.

Exit codes:
  0  — full parity, all tools complete.
  1  — drift detected (missing or extra files).
  2  — script error (e.g. _shared/ missing).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED = REPO_ROOT / "extensions" / "_shared"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    root: Path
    command_dir: str
    command_ext: str
    skill_dir: str
    rule_paths: list[str]  # files that the rules content lands at (relative to root)


TOOLS = [
    ToolSpec("claude", REPO_ROOT / "extensions" / ".claude",
             "commands", "md", "skills", ["rules/osp-rules.md"]),
    ToolSpec("cursor", REPO_ROOT / "extensions" / ".cursor",
             "commands", "md", "skills", ["rules/osp-rules.mdc"]),
    ToolSpec("gemini", REPO_ROOT / "extensions" / ".gemini",
             "commands", "toml", "skills", ["GEMINI.md"]),
    ToolSpec("antigravity", REPO_ROOT / "extensions" / ".agent",
             "workflows", "md", "skills", ["rules/osp-rules.md"]),
    ToolSpec("antigravity-cli", REPO_ROOT / "extensions" / ".agents",
             "workflows", "md", "skills", ["rules/osp-rules.md", "AGENTS.md"]),
    ToolSpec("copilot", REPO_ROOT / "extensions" / ".github",
             "prompts", "md", "skills", ["instructions/osp-rules.md", "AGENTS.md"]),
    ToolSpec("junie", REPO_ROOT / "extensions" / ".junie",
             "commands", "md", "skills", ["guidelines.md"]),
    ToolSpec("kiro", REPO_ROOT / "extensions" / ".kiro",
             "hooks", "md", "skills", ["steering/osp-rules.md"]),
    ToolSpec("codex", REPO_ROOT / "extensions" / ".codex",
             "prompts", "md", "skills", ["AGENTS.md"]),
    ToolSpec("kimi", REPO_ROOT / "extensions" / ".kimi",
             "commands", "md", "skills", ["AGENTS.md"]),
    ToolSpec("qwen", REPO_ROOT / "extensions" / ".qwen",
             "commands", "md", "agents", ["QWEN.md"]),
    ToolSpec("vibe", REPO_ROOT / "extensions" / ".vibe",
             "commands", "md", "skills", ["AGENTS.md"]),
    ToolSpec("opencode", REPO_ROOT / "extensions" / ".opencode",
             "commands", "md", "agents", ["AGENTS.md"]),
    ToolSpec("openhands", REPO_ROOT / "extensions" / ".openhands",
             "commands", "md", "skills", ["AGENTS.md"]),
]


def list_canonical_commands() -> list[str]:
    return sorted(p.stem for p in (SHARED / "commands").glob("*.md"))


def list_canonical_skills() -> list[str]:
    return sorted(p.parent.name for p in (SHARED / "skills").glob("*/SKILL.md"))


def list_canonical_skill_support() -> list[tuple[str, str]]:
    """(skill_name, relative_path) for every non-SKILL.md file bundled with a skill."""
    out: list[tuple[str, str]] = []
    for skill_md in (SHARED / "skills").glob("*/SKILL.md"):
        skill_dir = skill_md.parent
        for p in skill_dir.rglob("*"):
            if p.is_file() and p.name != "SKILL.md":
                out.append((skill_dir.name, p.relative_to(skill_dir).as_posix()))
    return sorted(out)


def list_canonical_defaults() -> list[str]:
    """Relative POSIX paths of every defaults file, at any depth.

    Deliberately recursive. This function used to be a non-recursive
    `glob("*.md")` — the exact same enumeration the sync script used — so when
    the sync silently dropped files under `defaults/domains/`, the expected set
    did not contain them either and this test still passed. An expectation
    derived from the same faulty assumption as the code under test cannot catch
    that code's bug. Walk the tree here, always.
    """
    d = SHARED / "defaults"
    if not d.exists():
        return []
    return sorted(p.relative_to(d).as_posix() for p in d.rglob("*.md") if p.is_file())


def check_tool(tool: ToolSpec, commands: list[str], skills: list[str], defaults: list[str],
               skill_support: list[tuple[str, str]] | None = None) -> list[str]:
    issues: list[str] = []
    if not tool.root.exists():
        issues.append(f"[{tool.name}] adapter root missing: {tool.root.relative_to(REPO_ROOT)}")
        return issues

    # Commands
    for cmd in commands:
        target = tool.root / tool.command_dir / f"{cmd}.{tool.command_ext}"
        if not target.exists():
            issues.append(f"[{tool.name}] missing command: {target.relative_to(REPO_ROOT)}")

    # Skills
    for skill in skills:
        target = tool.root / tool.skill_dir / skill / "SKILL.md"
        if not target.exists():
            issues.append(f"[{tool.name}] missing skill: {target.relative_to(REPO_ROOT)}")

    # Skill supporting files (references/, assets/, ...)
    for skill_name, rel in (skill_support or []):
        target = tool.root / tool.skill_dir / skill_name / rel
        if not target.exists():
            issues.append(f"[{tool.name}] missing skill support file: {target.relative_to(REPO_ROOT)}")

    # Rules
    for rel in tool.rule_paths:
        target = tool.root / rel
        if not target.exists():
            issues.append(f"[{tool.name}] missing rules artifact: {target.relative_to(REPO_ROOT)}")

    # Defaults (every tool gets the full set under defaults/, subdirectories included)
    for d in defaults:
        target = tool.root / "defaults" / d
        if not target.exists():
            issues.append(f"[{tool.name}] missing default: {target.relative_to(REPO_ROOT)}")

    # Reverse check: an adapter must not carry a defaults file that no longer
    # exists in _shared. Catches stale artifacts left behind by a rename.
    adapter_defaults = tool.root / "defaults"
    if adapter_defaults.exists():
        expected = set(defaults)
        for p in adapter_defaults.rglob("*.md"):
            if p.is_file():
                rel = p.relative_to(adapter_defaults).as_posix()
                if rel not in expected:
                    issues.append(f"[{tool.name}] stale default not in _shared: {p.relative_to(REPO_ROOT)}")

    return issues


def main() -> int:
    if not SHARED.exists():
        print(f"ERROR: {SHARED} does not exist.", file=sys.stderr)
        return 2

    commands = list_canonical_commands()
    skills = list_canonical_skills()
    defaults = list_canonical_defaults()
    skill_support = list_canonical_skill_support()

    if not commands or not skills:
        print("ERROR: _shared/ is empty (no commands or skills found).", file=sys.stderr)
        return 2

    print(f"  ▸ canonical: {len(commands)} commands, {len(skills)} skills, "
          f"{len(defaults)} defaults, {len(skill_support)} skill support files")

    all_issues: list[str] = []
    for tool in TOOLS:
        issues = check_tool(tool, commands, skills, defaults, skill_support)
        if issues:
            all_issues.extend(issues)
        else:
            print(f"  ✓ {tool.name}: parity OK")

    if all_issues:
        print("\n  ❌ Drift detected:")
        for i in all_issues:
            print(f"     - {i}")
        print(f"\n  → Run `python3 scripts/sync_adapters.py` to regenerate.")
        return 1

    print(f"\n  ✅ All {len(TOOLS)} tools have full parity with _shared/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
