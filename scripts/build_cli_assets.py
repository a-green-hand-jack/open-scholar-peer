#!/usr/bin/env python3
"""Build the packaged OSP CLI runtime assets from repository-owned sources.

The assets are distribution inputs only.  The canonical adapter source remains
``extensions/_shared`` and ``extensions/.opencode`` is refreshed first by
``sync_adapters.py``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "osp_cli" / "_assets"
SOURCES = (
    (ROOT / "extensions" / ".opencode", ASSETS / "extensions" / ".opencode"),
    (ROOT / "mcp-server", ASSETS / "mcp-server"),
    (ROOT / ".brain-template", ASSETS / ".brain-template"),
)


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def main() -> None:
    if ASSETS.exists():
        shutil.rmtree(ASSETS)
    for source, target in SOURCES:
        if not source.exists():
            raise SystemExit(f"Missing CLI asset source: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv"))
    metadata = {str(source.relative_to(ROOT)): tree_digest(source) for source, _ in SOURCES}
    (ASSETS / "SOURCE_DIGESTS.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
