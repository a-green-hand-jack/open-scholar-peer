"""Isolated, resumable execution of the Open ScholarPeer review protocol.

The module deliberately uses only the Python standard library.  OpenCode stays
the agent runtime; this layer owns source import, phase ordering, validation,
checkpoints, and provenance rather than relying on an unstructured prompt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import signal
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PHASES = (
    "onboarding",
    "summary",
    "literature",
    "historian",
    "baseline_scout",
    "qa",
    "review",
)
COMMANDS = {
    "onboarding": "0-osp-onboarding",
    "summary": "1-osp-summary",
    "literature": "2-osp-literature",
    "historian": "3-osp-historian",
    "baseline_scout": "4-osp-baseline-scout",
    "qa": "5-osp-qa",
    "review": "6-osp-review",
}
PHASE_OUTPUTS = {
    "onboarding": (".brain/raw/00_review_guidelines.md",),
    "summary": (".brain/raw/01_structured_summary.md",),
    "literature": (
        ".brain/raw/02a_literature_round1.md",
        ".brain/raw/02b_literature_round2.md",
        ".brain/raw/02c_literature_round3.md",
        ".brain/raw/02_retrieved_literature.md",
    ),
    "historian": (".brain/raw/03_domain_narrative.md",),
    "baseline_scout": (".brain/raw/04_missing_baselines.md",),
    "qa": (),
    "review": (".brain/review/final_review.md",),
}
ARTIFACT_HEADINGS = ("## Method", "## Output", "## Provenance")
RUNTIME_DIR = ".osp-run"
SENSITIVE_SOURCE_NAME = re.compile(
    r"(^|/)(\.env(?:\.|$)|\.npmrc$|\.netrc$|auth\.json$|id_(?:rsa|ed25519|ecdsa)$|.*\.(?:pem|key|p12|pfx)$|credentials?(?:\.|$)|.*(?:token|secret|credential).*(?:\.json|\.ya?ml|\.toml)?$)",
    re.IGNORECASE,
)
PAPER_SOURCE_SUFFIXES = {".tex", ".bib", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".sty", ".cls", ".bst", ".csv", ".tsv", ".md", ".txt"}
PAPER_SOURCE_NAMES = {"makefile", "latexmkrc"}


class OSPError(RuntimeError):
    """A user-actionable OSP CLI error."""


@dataclass(frozen=True)
class RunOptions:
    output: Path
    mode: str = "autonomous"
    headless: bool = False
    model: str | None = None
    provider: str | None = None
    variant: str | None = None
    timeout: int = 1800
    venue: str | None = None
    domain: str | None = None
    brief: Path | None = None
    previous_review: Path | None = None
    revision_context: Path | None = None
    network_policy: str = "online"
    prepare_mcp: bool = True
    trail: Path | None = None
    trail_repo: str | None = None
    upload: bool = False

    def resolved_model(self) -> str | None:
        if not self.model:
            return None
        if "/" in self.model or not self.provider:
            return self.model
        return f"{self.provider}/{self.model}"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OSPError(f"Cannot read JSON state at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OSPError(f"Expected JSON object at {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def digest_paths(paths: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(sha256_file(path).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def safe_relative(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise OSPError(f"Unsafe source path outside import root: {path}") from exc


def iter_regular_files(root: Path, excluded: set[str] | None = None) -> list[Path]:
    excluded = excluded or set()
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        if SENSITIVE_SOURCE_NAME.search(relative.as_posix()):
            continue
        if path.is_symlink():
            raise OSPError(f"Symbolic links are not supported in imported source: {relative}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise OSPError(f"Special files are not supported in imported source: {relative}")
    return files


def is_paper_source(path: Path) -> bool:
    return path.suffix.lower() in PAPER_SOURCE_SUFFIXES or path.name.lower() in PAPER_SOURCE_NAMES


def resource_root() -> Path:
    """Return bundled assets, falling back to the source checkout for development."""
    bundled = Path(__file__).with_name("_assets")
    if bundled.is_dir():
        return bundled
    checkout = Path(__file__).resolve().parent.parent
    if (checkout / "extensions" / ".opencode").is_dir():
        return checkout
    raise OSPError("OSP runtime assets are missing; reinstall the osp package.")


def source_asset(root: Path, name: str) -> Path:
    assets = resource_root()
    candidate = assets / name
    if candidate.exists():
        return candidate
    raise OSPError(f"Bundled OSP asset is missing: {name}")


def copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def command_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return (completed.stdout or completed.stderr).strip().splitlines()[0] if (completed.stdout or completed.stderr) else None


def source_manifest(source: Path) -> dict[str, Any]:
    files = iter_regular_files(source, {".git", ".brain", ".open-scholar-peer", RUNTIME_DIR})
    excluded = [
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file() and SENSITIVE_SOURCE_NAME.search(path.relative_to(source).as_posix())
    ]
    return {
        "source": str(source.resolve()),
        "files": [
            {"path": path.relative_to(source).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in files
        ],
        "digest": digest_paths(files, source),
        "unresolved_metadata": {"excluded_sensitive_files": sorted(excluded)},
    }


def tex_graph(source: Path) -> dict[str, Any]:
    tex_files = [path for path in iter_regular_files(source) if path.suffix.lower() == ".tex"]
    documents: list[Path] = []
    for path in tex_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"(^|\n)\s*\\documentclass(?:\[[^]]*])?\s*\{", content):
            documents.append(path)
    entrypoint = documents[0] if len(documents) == 1 else None
    source_graph: list[str] = []
    missing: list[dict[str, str]] = []
    visited: set[Path] = set()

    def visit(path: Path) -> None:
        if path in visited or not path.exists():
            return
        visited.add(path)
        source_graph.append(path.relative_to(source).as_posix())
        content = re.sub(r"(?<!\\)%.*", "", path.read_text(encoding="utf-8", errors="replace"))
        for match in re.finditer(r"\\(?:input|include|subfile)\s*\{([^}]+)}", content):
            requested = match.group(1).strip()
            candidate = path.parent / (requested if requested.endswith(".tex") else f"{requested}.tex")
            if candidate.exists():
                visit(candidate)
            else:
                missing.append({"from": path.relative_to(source).as_posix(), "requested": requested})

    if entrypoint:
        visit(entrypoint)
    return {
        "entrypoint": entrypoint.relative_to(source).as_posix() if entrypoint else None,
        "entrypoints": [path.relative_to(source).as_posix() for path in documents],
        "source_graph": source_graph,
        "bibliography": [path.relative_to(source).as_posix() for path in iter_regular_files(source) if path.suffix.lower() == ".bib"],
        "figures": [path.relative_to(source).as_posix() for path in iter_regular_files(source) if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg"}],
        "unresolved_metadata": {"missing_includes": missing, "multiple_or_missing_entrypoint": not bool(entrypoint)},
    }


def extract_archive(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    if archive.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive) as handle:
            members = handle.infolist()
            for member in members:
                target = destination / member.filename
                safe_relative(target, destination)
                if member.is_dir():
                    continue
                if member.external_attr >> 16 & 0o170000 == 0o120000:
                    raise OSPError(f"Archive contains unsupported symlink: {member.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with handle.open(member) as src, target.open("wb") as dest:
                    shutil.copyfileobj(src, dest)
    else:
        try:
            handle = tarfile.open(archive, "r:*")
        except tarfile.TarError as exc:
            raise OSPError(f"Unsupported source archive: {archive}") from exc
        with handle:
            for member in handle.getmembers():
                target = destination / member.name
                safe_relative(target, destination)
                if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                    raise OSPError(f"Archive contains unsupported entry: {member.name}")
            for member in handle.getmembers():
                if member.isdir():
                    (destination / member.name).mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target = destination / member.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    extracted = handle.extractfile(member)
                    if extracted is None:
                        raise OSPError(f"Could not extract archive entry: {member.name}")
                    with extracted, target.open("wb") as output:
                        shutil.copyfileobj(extracted, output)
    entries = [entry for entry in destination.iterdir() if entry.name not in {"__MACOSX", ".DS_Store"}]
    return entries[0] if len(entries) == 1 and entries[0].is_dir() else destination


class OSPRun:
    """A single immutable OSP review run."""

    def __init__(self, run_dir: Path, executor: Callable[[str, Path, RunOptions], subprocess.CompletedProcess[str]] | None = None):
        self.run_dir = run_dir.resolve()
        self.executor = executor

    @property
    def state_path(self) -> Path:
        return self.run_dir / RUNTIME_DIR / "run.json"

    @property
    def session_path(self) -> Path:
        return self.run_dir / ".brain" / "session.json"

    @property
    def checkpoint_dir(self) -> Path:
        return self.run_dir / RUNTIME_DIR / "checkpoints"

    @classmethod
    def prepare(cls, source: Path, options: RunOptions) -> "OSPRun":
        source = source.expanduser().resolve()
        if not source.exists():
            raise OSPError(f"Input does not exist: {source}")
        if source.is_dir() and options.output.expanduser().resolve().is_relative_to(source):
            raise OSPError("--output must be outside a source directory to avoid importing a run into itself.")
        if options.upload and (not options.trail or not options.trail_repo):
            raise OSPError("--upload requires both --trail and --trail-repo so review content has an explicit destination.")
        if options.provider and not options.model:
            raise OSPError("--provider requires --model; use provider/model or pass both flags.")
        if options.network_policy == "offline" and options.prepare_mcp:
            raise OSPError("Offline mode cannot prepare an MCP runtime; rerun with --no-mcp and a local OpenCode provider.")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        input_digest = sha256_file(source)[:12] if source.is_file() else source_manifest(source)["digest"][:12]
        run_dir = options.output.expanduser().resolve() / f"osp-{timestamp}-{input_digest}-{secrets.token_hex(3)}"
        if run_dir.exists():
            raise OSPError(f"Refusing to overwrite existing run: {run_dir}")
        run = cls(run_dir)
        run._prepare(source, options)
        return run

    def _prepare(self, source: Path, options: RunOptions) -> None:
        self.run_dir.mkdir(parents=True)
        write_json(self.state_path, {"schema_version": "osp-run-v1", "run_id": self.run_dir.name, "status": "preparing", "created_at": now(), "updated_at": now()})
        try:
            self._install_adapter()
            self._initialize_brain()
            imported = self._import_source(source)
            self._lock_imported_source()
            self._copy_optional_context(options)
            if options.venue:
                session = read_json(self.session_path)
                session["venue"]["name"] = options.venue
                write_json(self.session_path, session)
            if options.domain:
                session = read_json(self.session_path)
                session["paper"]["field"] = options.domain
                write_json(self.session_path, session)
            if options.prepare_mcp:
                self._prepare_mcp()
            else:
                self._write_opencode_config(None, options.network_policy)
            scope = self._scope(options, imported)
            state = {
                "schema_version": "osp-run-v1",
                "run_id": self.run_dir.name,
                "status": "prepared",
                "created_at": now(),
                "updated_at": now(),
                "run_dir": str(self.run_dir),
                "scope": scope,
                "scope_digest": hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest(),
                "phases": {phase: {"status": "pending", "attempts": 0, "started_at": None, "completed_at": None, "log": None, "error": None} for phase in PHASES},
                "provenance": {
                    "osp_version": self._osp_version(),
                    "opencode_version": command_version(["opencode", "--version"]),
                    "python_version": sys.version.split()[0],
                    "input": imported,
                    "workspace_input_digest": self._workspace_input_digest(),
                    "network_policy": options.network_policy,
                    "permission_policy": "isolated-workspace; autonomous execution only when explicitly requested; no secret material copied",
                },
            }
            write_json(self.state_path, state)
            self.checkpoint("prepared")
        except Exception as exc:
            state = self.state()
            state.update({"status": "failed", "updated_at": now(), "failure": {"phase": "preparation", "error": str(exc)}})
            write_json(self.state_path, state)
            raise

    def _install_adapter(self) -> None:
        copy_tree(source_asset(self.run_dir, "extensions/.opencode"), self.run_dir / ".opencode")

    def _initialize_brain(self) -> None:
        template = source_asset(self.run_dir, ".brain-template/session.json")
        (self.run_dir / ".brain" / "input").mkdir(parents=True)
        (self.run_dir / ".brain" / "raw").mkdir()
        (self.run_dir / ".brain" / "review").mkdir()
        (self.run_dir / ".brain" / "tmp").mkdir()
        shutil.copy2(template, self.session_path)
        (self.run_dir / "AGENTS.md").write_text(
            "# OSP CLI Runtime\n\n"
            "This is an isolated, autonomous, report-only OSP run. The CLI invokes one phase at a time. "
            "The primary agent must execute the requested phase directly, write only `.brain/` and `.osp-run/`, "
            "never modify `source/`, never advance another phase, and never route the user to another slash command. "
            "Use persona skills as inline instructions; do not delegate a non-Q&A phase.\n",
            encoding="utf-8",
        )

    def _lock_imported_source(self) -> None:
        source = self.run_dir / "source"
        for path in iter_regular_files(source):
            path.chmod(0o444)
        for path in sorted((item for item in source.rglob("*") if item.is_dir()), reverse=True):
            path.chmod(0o555)
        source.chmod(0o555)

    def _workspace_input_digest(self) -> str:
        input_root = self.run_dir / ".brain" / "input"
        return digest_paths(iter_regular_files(input_root), input_root)

    def _import_source(self, source: Path) -> dict[str, Any]:
        input_dir = self.run_dir / ".brain" / "input"
        source_dir = self.run_dir / "source"
        source_dir.mkdir()
        existing_session: dict[str, Any] | None = None
        if source.is_file() and source.suffix.lower() == ".pdf":
            copied = source_dir / "paper.pdf"
            shutil.copy2(source, copied)
            shutil.copy2(copied, input_dir / "paper.pdf")
            parsed = input_dir / "paper.md"
            conversion = subprocess.run(["pdftotext", "-layout", str(copied), str(parsed)], capture_output=True, text=True, check=False)
            if conversion.returncode != 0 or not parsed.exists() or not parsed.read_text(encoding="utf-8", errors="replace").strip():
                raise OSPError("Could not produce .brain/input/paper.md from PDF; install Poppler pdftotext or provide a readable workspace.")
            manifest = {"kind": "pdf", **source_manifest(source_dir), "unresolved_metadata": {"entrypoint": "not applicable", "excluded_sensitive_files": []}}
        else:
            existing_session = read_json(source / ".brain" / "session.json") if source.is_dir() and (source / ".brain" / "session.json").is_file() else None
            if source.is_file():
                staging = source_dir / ".archive-staging"
                root = extract_archive(source, staging)
            elif (source / ".brain" / "session.json").is_file():
                root = source / ".brain" / "input"
            else:
                root = source
            if not root.is_dir():
                raise OSPError("Expected a PDF, TeX directory, source archive, or existing OSP workspace.")
            excluded_sensitive = [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and SENSITIVE_SOURCE_NAME.search(path.relative_to(root).as_posix())]
            all_files = iter_regular_files(root, {".git", ".brain", ".open-scholar-peer", RUNTIME_DIR})
            excluded_unsupported = [path.relative_to(root).as_posix() for path in all_files if not is_paper_source(path)]
            files = [path for path in all_files if is_paper_source(path)]
            workspace_pdf = next((path for path in files if path.suffix.lower() == ".pdf"), None)
            if not any(path.suffix.lower() == ".tex" for path in files) and not (root / "paper.md").is_file() and not workspace_pdf:
                raise OSPError("Source directory contains neither TeX files nor paper.md.")
            for file in files:
                relative = file.relative_to(root)
                target = source_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target)
            staging = source_dir / ".archive-staging"
            if staging.exists():
                shutil.rmtree(staging)
            graph = tex_graph(source_dir) if any(path.suffix.lower() == ".tex" for path in files) else {"entrypoint": None, "source_graph": [], "bibliography": [], "figures": [], "unresolved_metadata": {}}
            markdown = source_dir / "paper.md"
            if markdown.exists():
                shutil.copy2(markdown, input_dir / "paper.md")
            elif workspace_pdf:
                copied_pdf = source_dir / workspace_pdf.relative_to(root)
                shutil.copy2(copied_pdf, input_dir / "paper.pdf")
                try:
                    conversion = subprocess.run(["pdftotext", "-layout", str(copied_pdf), str(input_dir / "paper.md")], capture_output=True, text=True, check=False)
                except FileNotFoundError as exc:
                    raise OSPError("PDF input requires Poppler pdftotext; run `osp doctor` for details.") from exc
                if conversion.returncode or not (input_dir / "paper.md").is_file():
                    raise OSPError("Could not convert PDF in an existing OSP workspace to paper.md.")
            else:
                text_parts = ["# Imported TeX source\n"]
                selected = graph["source_graph"] or [path.relative_to(source_dir).as_posix() for path in source_dir.rglob("*.tex")]
                for relative in selected:
                    text_parts.extend((f"\n## Source: {relative}\n", (source_dir / relative).read_text(encoding="utf-8", errors="replace")))
                (input_dir / "paper.md").write_text("\n".join(text_parts), encoding="utf-8")
            manifest = {"kind": "osp-workspace" if (source / ".brain").is_dir() else ("archive" if source.is_file() else "tex-directory"), **source_manifest(source_dir), **graph}
            manifest.setdefault("unresolved_metadata", {}).update({"excluded_sensitive_files": sorted(excluded_sensitive), "excluded_unsupported_files": sorted(excluded_unsupported)})
        manifest["original_input"] = {
            "path": str(source),
            "sha256": sha256_file(source) if source.is_file() else source_manifest(source)["digest"],
        }
        write_json(self.run_dir / RUNTIME_DIR / "source-manifest.json", manifest)
        session = read_json(self.session_path)
        session["paper"].update({"path": str(source), "parsed_path": ".brain/input/paper.md", "type": manifest["kind"]})
        if existing_session:
            for key in ("venue", "qa_criteria", "qa_pairs_per_criterion"):
                if key in existing_session:
                    session[key] = existing_session[key]
            for key in ("review_mode", "field", "domain_profile", "numerical_slice"):
                if key in existing_session.get("paper", {}):
                    session["paper"][key] = existing_session["paper"][key]
            session["notes"] = "Seeded non-artifact configuration from an existing OSP workspace; prior review trail was intentionally not imported."
        write_json(self.session_path, session)
        return manifest

    def _copy_optional_context(self, options: RunOptions) -> None:
        for label, path in (("review_brief", options.brief), ("previous_review", options.previous_review), ("revision_context", options.revision_context)):
            if not path:
                continue
            path = path.expanduser().resolve()
            if not path.is_file():
                raise OSPError(f"{label.replace('_', ' ')} is not a file: {path}")
            if SENSITIVE_SOURCE_NAME.search(path.name):
                raise OSPError(f"Refusing to copy potential credential material as {label.replace('_', ' ')}: {path.name}")
            target = self.run_dir / ".brain" / "input" / f"{label}{path.suffix or '.md'}"
            shutil.copy2(path, target)

    def _prepare_mcp(self) -> None:
        mcp_root = self.run_dir / ".open-scholar-peer" / "mcp"
        copy_tree(source_asset(self.run_dir, "mcp-server"), mcp_root)
        python = mcp_root / ".venv" / "bin" / "python"
        if not python.exists():
            base_python = self._venv_python()
            completed = subprocess.run([base_python, "-m", "venv", str(mcp_root / ".venv")], capture_output=True, text=True, check=False)
            if completed.returncode:
                detail = (completed.stderr or completed.stdout).strip() or "Python venv returned no diagnostic output."
                raise OSPError(f"Could not create MCP virtual environment: {detail}")
        installed = subprocess.run([str(python), "-m", "pip", "install", "--quiet", "-r", str(mcp_root / "requirements.txt")], capture_output=True, text=True, check=False)
        if installed.returncode:
            raise OSPError(f"Could not install MCP dependencies: {installed.stderr.strip()}")
        self._write_opencode_config([str(python), str(mcp_root / "osp_mcp.py")], "online")

    @staticmethod
    def _venv_python() -> str:
        candidates = [sys.executable, *(path for path in (shutil.which("python3.13"), shutil.which("python3.12"), shutil.which("python3.11"), shutil.which("python3")) if path)]
        for candidate in dict.fromkeys(candidates):
            available = subprocess.run([candidate, "-c", "import ensurepip"], capture_output=True, check=False)
            if available.returncode == 0:
                return candidate
        raise OSPError("No Python with ensurepip is available to create the isolated MCP runtime. Install a python3-venv package and retry.")

    def _write_opencode_config(self, mcp_command: list[str] | None, network_policy: str) -> None:
        config = {
            "$schema": "https://opencode.ai/config.json",
            "share": "disabled",
            "permission": {
                "*": "deny",
                "read": "allow",
                "glob": "allow",
                "grep": "allow",
                "edit": "allow",
                "write": "allow",
                "patch": "allow",
                "task": "allow",
                "webfetch": "deny" if network_policy == "offline" else "allow",
                "websearch": "deny" if network_policy == "offline" else "allow",
                "external_directory": "deny",
                "question": "deny",
                "bash": "deny",
            },
            "agent": {
                "osp-runner": {
                    "description": "File-capable primary executor for isolated Open ScholarPeer review phases.",
                    "mode": "primary",
                    "permission": {
                        "*": "deny",
                        "read": "allow",
                        "glob": "allow",
                        "grep": "allow",
                        "edit": "allow",
                        "write": "allow",
                        "patch": "allow",
                        "task": "allow",
                        "webfetch": "deny" if network_policy == "offline" else "allow",
                        "websearch": "deny" if network_policy == "offline" else "allow",
                        "external_directory": "deny",
                        "question": "deny",
                        "bash": "deny",
                    },
                }
            },
            "mcp": {"osp": {"type": "local", "command": mcp_command, "enabled": True}} if mcp_command else {}
        }
        write_json(self.run_dir / "opencode.json", config)

    def _scope(self, options: RunOptions, imported: dict[str, Any]) -> dict[str, Any]:
        fields = asdict(options)
        for key, value in list(fields.items()):
            if isinstance(value, Path):
                fields[key] = str(value.expanduser().resolve())
        fields["model"] = options.resolved_model()
        fields.pop("output", None)
        return {"workflow": list(PHASES), "input_digest": imported["digest"], "options": fields}

    @staticmethod
    def _osp_version() -> str | None:
        try:
            from importlib.metadata import version

            return version("open-scholar-peer")
        except Exception:
            return "1.5.0+source"

    def state(self) -> dict[str, Any]:
        return read_json(self.state_path)

    def checkpoint(self, reason: str = "manual") -> Path:
        state = self.state() if self.state_path.exists() else None
        if state is None:
            raise OSPError(f"No OSP run state at {self.run_dir}")
        session = read_json(self.session_path)
        artifacts = self._artifact_digests()
        checkpoint = {
            "schema_version": "osp-checkpoint-v1",
            "reason": reason,
            "created_at": now(),
            "scope_digest": state["scope_digest"],
            "completed_phases": [phase for phase in PHASES if state["phases"][phase]["status"] == "completed"],
            "session": session,
            "artifacts": artifacts,
        }
        path = self.checkpoint_dir / f"{len(list(self.checkpoint_dir.glob('*.json'))):02d}-{reason}.json"
        write_json(path, checkpoint)
        return path

    def _artifact_digests(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for phase in PHASES:
            for artifact in self._expected_outputs(phase):
                if artifact.exists():
                    result[str(artifact.relative_to(self.run_dir))] = sha256_file(artifact)
        return result

    def _expected_outputs(self, phase: str) -> list[Path]:
        if phase != "qa":
            return [self.run_dir / path for path in PHASE_OUTPUTS[phase]]
        criteria = read_json(self.session_path).get("qa_criteria", [])
        return [self.run_dir / ".brain" / "raw" / f"05_qa_{item['slug']}.md" for item in criteria if isinstance(item, dict) and item.get("slug")]

    def verify_scope(self) -> None:
        state = self.state()
        actual = hashlib.sha256(json.dumps(state["scope"], sort_keys=True).encode()).hexdigest()
        if actual != state["scope_digest"]:
            raise OSPError("Run scope has changed since creation; resume is refused.")
        manifest = read_json(self.run_dir / RUNTIME_DIR / "source-manifest.json")
        if manifest["digest"] != state["scope"]["input_digest"]:
            raise OSPError("Input provenance does not match the locked run scope; resume is refused.")
        source_digest = source_manifest(self.run_dir / "source")["digest"]
        if source_digest != state["scope"]["input_digest"]:
            raise OSPError("Imported source changed after preparation; resume is refused.")
        if self._workspace_input_digest() != state["provenance"]["workspace_input_digest"]:
            raise OSPError("Parsed paper input changed after preparation; resume is refused.")
        checkpoints = sorted(self.checkpoint_dir.glob("*.json"))
        if checkpoints:
            checkpoint = read_json(checkpoints[-1])
            if checkpoint.get("scope_digest") != state["scope_digest"]:
                raise OSPError("Latest checkpoint belongs to a different locked scope; resume is refused.")
            current_artifacts = self._artifact_digests()
            for path, digest in checkpoint.get("artifacts", {}).items():
                if current_artifacts.get(path) != digest:
                    raise OSPError(f"Artifact changed since the latest legal checkpoint: {path}")
            session = read_json(self.session_path)
            for phase in checkpoint.get("completed_phases", []):
                if session.get("phases", {}).get(phase, {}).get("status") != "completed":
                    raise OSPError(f"Completed phase state diverged from latest checkpoint: {phase}")
            if checkpoint.get("session") != session:
                raise OSPError("Review session changed since the latest legal checkpoint; resume is refused.")

    def validate(self) -> list[Check]:
        checks: list[Check] = []
        try:
            self.verify_scope()
            checks.append(Check("locked-scope", True, "input and invocation scope match"))
        except OSPError as exc:
            checks.append(Check("locked-scope", False, str(exc)))
        session = read_json(self.session_path)
        state = self.state()
        for phase in PHASES:
            valid, detail = self.validate_phase(phase, session)
            recorded = state["phases"][phase]["status"]
            checks.append(Check(f"phase:{phase}", valid and (recorded != "completed" or valid), f"{recorded}; {detail}"))
        final = self.run_dir / ".brain" / "review" / "final_review.md"
        prerequisite = all(state["phases"][phase]["status"] == "completed" for phase in PHASES[:-1])
        checks.append(Check("final-export", not final.exists() or prerequisite, "final review only present after required phases"))
        return checks

    def validate_phase(self, phase: str, session: dict[str, Any] | None = None) -> tuple[bool, str]:
        session = session or read_json(self.session_path)
        expected = self._expected_outputs(phase)
        if phase == "qa" and not expected:
            return False, "qa_criteria is empty; onboarding did not scaffold Q&A artifacts"
        missing = [path.relative_to(self.run_dir).as_posix() for path in expected if not path.is_file()]
        if missing:
            return False, f"missing {', '.join(missing)}"
        for artifact in expected:
            content = artifact.read_text(encoding="utf-8", errors="replace")
            absent = [heading for heading in ARTIFACT_HEADINGS if heading not in content]
            if absent:
                return False, f"{artifact.relative_to(self.run_dir)} missing {', '.join(absent)}"
            for heading in ARTIFACT_HEADINGS:
                after = content.split(heading, 1)[1]
                if phase == "review" and heading == "## Output":
                    # The venue-formatted review document (## Summary…## What was
                    # not checked) lives inside ## Output, so the section ends
                    # at the closing ## Provenance heading, not the next ## .
                    section = after.split("## Provenance", 1)[0].strip()
                else:
                    section = after.split("## ", 1)[0].strip()
                if not section:
                    return False, f"{artifact.relative_to(self.run_dir)} has empty {heading[3:]} section"
            if "{{" in content or "}}" in content:
                return False, f"{artifact.relative_to(self.run_dir)} contains an unresolved template placeholder"
        if phase == "literature":
            strategies = ("sub-domain-anchor", "method-anchor", "temporal-expansion")
            for artifact, strategy in zip(expected[:3], strategies):
                strategy_pattern = rf"(?:\*\*)?Strategy:(?:\*\*)?\s*`?{re.escape(strategy)}`?(?:\*\*)?"
                if not re.search(strategy_pattern, artifact.read_text(encoding="utf-8", errors="replace"), re.IGNORECASE):
                    return False, f"{artifact.relative_to(self.run_dir)} missing Strategy: {strategy}"
        if phase == "onboarding":
            criteria = session.get("qa_criteria", [])
            if not criteria:
                return False, "onboarding did not populate qa_criteria"
            scaffolded = [self.run_dir / ".brain" / "raw" / f"05_qa_{item.get('slug')}.md" for item in criteria if isinstance(item, dict) and item.get("slug")]
            if len(scaffolded) != len(criteria) or any(not path.is_file() for path in scaffolded):
                return False, "onboarding did not scaffold one Q&A file per criterion"
        if phase == "review":
            review = expected[0].read_text(encoding="utf-8", errors="replace")
            required_sections = ("## Summary", "## Strengths", "## Weaknesses", "## Dimension Scores", "## Recommendation", "## What was not checked")
            absent_sections = [section for section in required_sections if section not in review]
            if absent_sections:
                return False, f"final review missing {', '.join(absent_sections)}"
            if not re.search(r"(?m)^\|\s*Dimension\s*\|\s*Score\s*\|", review):
                return False, "final review is missing the dimension score table"
            if ".brain/raw/01_structured_summary.md" not in review and "01_structured_summary.md" not in review:
                return False, "final review has no required artifact evidence anchor"
            missing_criteria = [item.get("label", item.get("slug", "criterion")) for item in session.get("qa_criteria", []) if isinstance(item, dict) and item.get("label", item.get("slug")) not in review]
            if missing_criteria:
                return False, f"final review does not cover criteria: {', '.join(missing_criteria)}"
            score_rows = re.findall(r"(?m)^\|\s*([^|]+?)\s*\|\s*([0-5])\s*/\s*5\s*\|", review)
            scored = {name.strip() for name, _ in score_rows}
            if any(item.get("label", item.get("slug", "criterion")) not in scored for item in session.get("qa_criteria", []) if isinstance(item, dict)):
                return False, "dimension score table lacks a valid 0–5 row for every review criterion"
            recommendation = re.search(r"(?is)## Recommendation\s+(.+?)(?=\n## |\Z)", review)
            if not recommendation or not re.search(r"\b(accept|reject|minor revision|major revision|needs revision|not enough evidence)\b", recommendation.group(1), re.IGNORECASE):
                return False, "final review recommendation is outside the controlled review vocabulary"
        if phase == "qa":
            required_pairs = session.get("qa_pairs_per_criterion")
            if not isinstance(required_pairs, int) or required_pairs < 1:
                return False, "qa_pairs_per_criterion must be a positive integer"
            for artifact in expected:
                content = artifact.read_text(encoding="utf-8", errors="replace")
                questions = re.findall(r"(?m)^### Q(\d+)\s*$", content)
                answers = re.findall(r"(?m)^### A(\d+)\s*$", content)
                expected_numbers = [str(number) for number in range(1, required_pairs + 1)]
                if questions != expected_numbers or answers != expected_numbers:
                    return False, f"{artifact.relative_to(self.run_dir)} must contain exactly {required_pairs} ordered Q&A pairs"
        status = session.get("phases", {}).get(phase, {}).get("status")
        if status != "completed":
            return False, f"session phase status is {status!r}, expected 'completed'"
        phase_state = session["phases"][phase]
        if not phase_state.get("completed_at") or not phase_state.get("notes"):
            return False, "session phase is missing required completed_at or notes provenance"
        return True, f"{len(expected)} artifact(s) verified"

    def run(self, options: RunOptions) -> None:
        if self.executor is None:
            self._require_compatible_opencode()
        self.verify_scope()
        state = self.state()
        for index, phase in enumerate(PHASES):
            current = state["phases"][phase]["status"]
            valid, _ = self.validate_phase(phase)
            if current == "completed" and valid:
                continue
            if any(state["phases"][prior]["status"] != "completed" for prior in PHASES[:index]):
                raise OSPError(f"Cannot execute {phase}: earlier OSP phase is incomplete.")
            self._execute_phase(phase, options)
            state = self.state()
        checks = self.validate()
        if not all(check.passed for check in checks):
            raise OSPError("Run completed without satisfying the OSP artifact contract.")
        try:
            self._export_final(options)
        except Exception as exc:
            state = self.state()
            state.update({"status": "failed", "updated_at": now(), "failure": {"phase": "post-processing", "error": str(exc)}})
            write_json(self.state_path, state)
            self.checkpoint("failed-post-processing")
            raise
        state = self.state()
        state["status"] = "completed"
        state["completed_at"] = now()
        state["updated_at"] = now()
        write_json(self.state_path, state)
        self.checkpoint("completed")
        try:
            self._write_trail(options)
        except Exception as exc:
            state = self.state()
            state.update({"status": "failed", "updated_at": now(), "failure": {"phase": "trail-upload", "error": str(exc)}})
            write_json(self.state_path, state)
            self.checkpoint("failed-trail-upload")
            raise

    def _execute_phase(self, phase: str, options: RunOptions) -> None:
        state = self.state()
        entry = state["phases"][phase]
        entry.update({"status": "running", "started_at": now(), "attempts": entry["attempts"] + 1, "error": None})
        state["status"] = "running"
        state["updated_at"] = now()
        write_json(self.state_path, state)
        self._set_phase_task_policy(phase)
        invocations = range(1, 4) if phase == "literature" else range(1, 2)
        before = self._brain_snapshot()
        workspace_before = self._workspace_snapshot()
        log_paths: list[Path] = []
        completions: list[subprocess.CompletedProcess[str]] = []
        try:
            for invocation in invocations:
                prompt = self._phase_prompt(phase, options, invocation if phase == "literature" else None)
                log_path = self.run_dir / RUNTIME_DIR / "logs" / f"{phase}-attempt-{entry['attempts']}-step-{invocation}.jsonl"
                log_paths.append(log_path)
                if self.executor:
                    completed = self.executor(prompt, self.run_dir, options)
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    log_path.write_text(self._redact_text((completed.stdout or "") + ("\n[stderr]\n" + completed.stderr if completed.stderr else "")), encoding="utf-8")
                else:
                    completed = self._opencode_executor(prompt, self.run_dir, options, log_path)
                completions.append(completed)
                self._append_mcp_events(phase, log_path)
                if completed.returncode != 0:
                    raise OSPError(f"{phase} invocation {invocation} failed: OpenCode exit={completed.returncode}")
            valid, detail = self.validate_phase(phase)
            if not valid:
                raise OSPError(f"{phase} failed contract validation: {detail}")
            self._verify_phase_writes(before, workspace_before, phase)
        except BaseException as exc:
            state = self.state()
            log = str(log_paths[-1].relative_to(self.run_dir)) if log_paths else None
            state["phases"][phase].update({"status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", "completed_at": now(), "log": log, "error": str(exc) or type(exc).__name__})
            state.update({"status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", "updated_at": now(), "failure": {"phase": phase, "error": str(exc) or type(exc).__name__, "exit_code": completions[-1].returncode if completions else None}})
            write_json(self.state_path, state)
            self.checkpoint(f"failed-{phase}")
            raise
        state = self.state()
        state["phases"][phase].update({"status": "completed", "completed_at": now(), "log": str(log_paths[-1].relative_to(self.run_dir)), "error": None})
        state.setdefault("opencode", {})[phase] = [self._opencode_metadata(completed) for completed in completions]
        state["updated_at"] = now()
        write_json(self.state_path, state)
        self.checkpoint(phase)

    def _brain_snapshot(self) -> dict[str, str]:
        root = self.run_dir / ".brain"
        return {path.relative_to(root).as_posix(): sha256_file(path) for path in iter_regular_files(root)}

    def _workspace_snapshot(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for path in self.run_dir.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            # .opencode/ holds the generated adapter bundle plus npm packages
            # OpenCode auto-installs there while a phase runs; it is
            # CLI-owned, not an agent artifact, so it is outside the write
            # contract enforced for phase runs.
            if (
                path.is_relative_to(self.run_dir / ".brain")
                or path.is_relative_to(self.run_dir / RUNTIME_DIR)
                or path.is_relative_to(self.run_dir / ".opencode")
            ):
                continue
            result[path.relative_to(self.run_dir).as_posix()] = sha256_file(path)
        return result

    def _verify_phase_writes(self, before: dict[str, str], workspace_before: dict[str, str], phase: str) -> None:
        after = self._brain_snapshot()
        changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
        allowed = {"session.json", *(path.relative_to(self.run_dir / ".brain").as_posix() for path in self._expected_outputs(phase))}
        if phase == "onboarding":
            allowed.update(path.relative_to(self.run_dir / ".brain").as_posix() for path in self._expected_outputs("qa"))
        violations = sorted(path for path in changed if path not in allowed and not path.startswith("tmp/") and not path.startswith("raw/transcripts/"))
        if violations:
            raise OSPError(f"{phase} changed files outside its artifact contract: {', '.join(violations)}")
        workspace_after = self._workspace_snapshot()
        changed_workspace = sorted(path for path in set(workspace_before) | set(workspace_after) if workspace_before.get(path) != workspace_after.get(path))
        if changed_workspace:
            raise OSPError(f"{phase} changed files outside .brain/: {', '.join(changed_workspace)}")

    def _append_mcp_events(self, phase: str, log_path: Path) -> None:
        """Preserve structured retrieval/tool events without treating prose logs as provenance."""
        events: list[dict[str, Any]] = []
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            serialized = json.dumps(event).lower()
            if "mcp" not in serialized and not any(name in serialized for name in ("arxiv", "semantic_scholar", "google_scholar")):
                continue
            events.append({"phase": phase, "timestamp": event.get("timestamp"), "type": event.get("type"), "event": self._redact_metadata(event)})
        if not events:
            return
        destination = self.run_dir / RUNTIME_DIR / "mcp-retrieval.jsonl"
        with destination.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

    @staticmethod
    def _redact_metadata(value: Any, key: str = "") -> Any:
        if re.search(r"(?:api.?key|token|secret|password|authorization|cookie)", key, re.IGNORECASE):
            return "[REDACTED]"
        if isinstance(value, dict):
            return {item_key: OSPRun._redact_metadata(item_value, item_key) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [OSPRun._redact_metadata(item) for item in value]
        if isinstance(value, str) and re.search(r"(?:sk-[A-Za-z0-9_-]{12,}|bearer\s+\S+)", value, re.IGNORECASE):
            return "[REDACTED]"
        return value

    @staticmethod
    def _redact_text(text: str) -> str:
        text = re.sub(r"(?i)(bearer\s+|api[_ -]?key[=:]\s*|token[=:]\s*)[A-Za-z0-9_\-.]{12,}", r"\1[REDACTED]", text)
        return re.sub(r"\bsk-[A-Za-z0-9_-]{12,}\b", "[REDACTED]", text)

    def _set_phase_task_policy(self, phase: str) -> None:
        """Keep single-persona phases inline; Q&A alone needs its answer subagent."""
        config_path = self.run_dir / "opencode.json"
        config = read_json(config_path)
        action = "allow" if phase == "qa" else "deny"
        config["permission"]["task"] = action
        config["agent"]["osp-runner"]["permission"]["task"] = action
        write_json(config_path, config)

    @staticmethod
    def _opencode_metadata(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        """Keep session identifiers when OpenCode emits JSON event streams."""
        identifiers: set[str] = set()

        def visit(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key.lower() in {"sessionid", "session_id"} and isinstance(item, str):
                        identifiers.add(item)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)

        for line in (completed.stdout or "").splitlines():
            try:
                visit(json.loads(line))
            except json.JSONDecodeError:
                continue
        return {"returncode": completed.returncode, "session_ids": sorted(identifiers)}

    def _phase_prompt(self, phase: str, options: RunOptions, literature_round: int | None = None) -> str:
        command = COMMANDS[phase]
        final_structure = " For the final review, preserve the venue-formatted review inside `## Output` and wrap it in the mandatory top-level `## Method`, `## Output`, and `## Provenance` sections." if phase == "review" else ""
        if phase == "onboarding":
            required_hint = "Write `.brain/raw/00_review_guidelines.md`, populate `session.json.qa_criteria`, and scaffold one empty `05_qa_<slug>.md` per criterion under `.brain/raw/`."
        elif phase == "review":
            required_hint = ("Inside `## Output`, use top-level `## ` headings exactly: "
                             "`## Summary`, `## Strengths`, `## Weaknesses`, `## Dimension Scores`, "
                             "`## Recommendation`, `## What was not checked`, plus the `| Dimension | Score |` table.")
        elif phase == "qa":
            required_hint = "Write exactly one `05_qa_<slug>.md` per criterion under `.brain/raw/`."
        elif phase == "literature" and literature_round:
            round_artifact = PHASE_OUTPUTS["literature"][literature_round - 1]
            required_hint = f"Write exactly this round's artifact: `{round_artifact}`."
        else:
            required_hint = "Write exactly these artifacts: " + ", ".join(f"`{path}`" for path in PHASE_OUTPUTS[phase]) + "."
        if phase != "review":
            required_hint += " Every `.brain/raw/` artifact you write must contain the universal `## Method`, `## Output`, and `## Provenance` sections."
        return f"""Execute only OSP phase `{phase}` by following `/{command}` in this isolated workspace. You are the file-capable primary executor: perform all required reads and writes yourself in this turn. Do not delegate the phase to a subagent or merely describe the work.

This is an autonomous, report-only peer-review run. Do not modify `source/` or invent paper facts. Read `.brain/session.json` and obey the installed OSP artifact contract. {required_hint} {f'This is literature round {literature_round} of 3: execute exactly that round; only consolidate and mark the literature phase completed after round 3.' if literature_round else 'Complete the phase fully and update only the corresponding session phase to completed.'}{final_structure} Do not advance to another phase. Unknown evidence must be labeled unresolved or not assessable.

The CLI supplied venue={options.venue or 'unresolved'}, domain={options.domain or 'unresolved'}, network-policy={options.network_policy}. Do not request credentials or write secrets. Put any disposable scratch output only in `.brain/tmp/`.
"""

    @staticmethod
    def _opencode_executor(prompt: str, cwd: Path, options: RunOptions, log_path: Path) -> subprocess.CompletedProcess[str]:
        executable = shutil.which("opencode")
        if not executable:
            raise OSPError("OpenCode is not installed or not on PATH. Run `osp doctor`.")
        command = [executable, "run", "--pure", "--dir", str(cwd), "--agent", "osp-runner", "--format", "json", "--thinking"]
        model = options.resolved_model()
        if model:
            command.extend(("--model", model))
        if options.variant:
            command.extend(("--variant", options.variant))
        if options.mode == "autonomous" and options.headless:
            command.append("--auto")
        command.extend(("--", prompt))
        if options.network_policy == "offline" and not sys.platform.startswith("linux"):
            raise OSPError("Offline policy requires Linux bubblewrap network isolation.")
        if sys.platform.startswith("linux"):
            command = OSPRun._linux_sandbox(command, cwd, options)
        environment = {key: value for key, value in os.environ.items() if key in {"HOME", "PATH", "LANG", "LC_ALL", "TERM", "XDG_CONFIG_HOME", "XDG_DATA_HOME"}}
        for key in list(environment):
            if re.search(r"(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD)", key, re.IGNORECASE):
                environment.pop(key, None)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with log_path.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, text=True, env=environment, start_new_session=True)
                try:
                    returncode = process.wait(timeout=options.timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    log.write("\nOSP phase timed out\n")
                    returncode = 124
                except BaseException:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    raise
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            output = OSPRun._redact_text(log_path.read_text(encoding="utf-8", errors="replace"))
            log_path.write_text(output, encoding="utf-8")
            return subprocess.CompletedProcess(command, returncode, output, "")
        except FileNotFoundError as exc:
            raise OSPError("OpenCode is not installed or not on PATH. Run `osp doctor`.") from exc

    @staticmethod
    def _linux_sandbox(command: list[str], cwd: Path, options: RunOptions) -> list[str]:
        bwrap = shutil.which("bwrap")
        if not bwrap:
            raise OSPError("Linux headless OSP runs require bubblewrap (`bwrap`) to isolate host credentials.")
        home = Path.home()
        state_dir = cwd / RUNTIME_DIR / "opencode-state"
        state_dir.mkdir(parents=True, exist_ok=True)
        sandbox = [bwrap, "--die-with-parent", "--new-session", "--unshare-all"]
        if options.network_policy == "online":
            sandbox.append("--share-net")
        for path in ("/usr", "/bin", "/lib", "/lib64", "/etc"):
            if Path(path).exists():
                sandbox.extend(("--ro-bind", path, path))
        resolver = Path("/run/systemd/resolve")
        if resolver.exists():
            sandbox.extend(("--dir", "/run", "--dir", "/run/systemd", "--ro-bind", str(resolver), str(resolver)))
        sandbox.extend(("--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--dir", str(home), "--dir", str(home / ".config"), "--dir", str(home / ".local"), "--dir", str(home / ".local" / "share")))
        for path in (home / ".config" / "opencode", home / ".opencode"):
            if path.exists():
                sandbox.extend(("--ro-bind", str(path), str(path)))
        sandbox.extend(("--bind", str(state_dir), str(home / ".local" / "share" / "opencode")))
        auth = home / ".local" / "share" / "opencode" / "auth.json"
        if auth.is_file():
            sandbox.extend(("--ro-bind", str(auth), str(auth)))
        sandbox.extend(("--bind", str(cwd), str(cwd), "--chdir", str(cwd), "--", *command))
        return sandbox

    @staticmethod
    def _require_compatible_opencode() -> None:
        version = command_version(["opencode", "--version"])
        if not version:
            raise OSPError("OpenCode is not installed or not responding. Run `osp doctor`.")
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        if not match or tuple(map(int, match.groups())) < (1, 18, 0):
            raise OSPError(f"OpenCode {version!r} is unsupported; osp requires OpenCode 1.18.0 or newer.")

    def _export_final(self, options: RunOptions) -> None:
        final = self.run_dir / ".brain" / "review" / "final_review.md"
        if not final.is_file():
            raise OSPError("Cannot export missing final review.")
        exported = self.run_dir.parent / "final_review.md"
        shutil.copy2(final, exported)
        state = self.state()
        state["final_review"] = str(exported)
        state["updated_at"] = now()
        write_json(self.state_path, state)

    def _write_trail(self, options: RunOptions) -> None:
        if not options.trail:
            return
        trail = options.trail.expanduser().resolve() / self.run_dir.name
        marker = trail / ".osp-trail.json"
        if trail.exists():
            if not marker.is_file() or read_json(marker).get("run_id") != self.run_dir.name:
                raise OSPError(f"Refusing to overwrite a trail not owned by this run: {trail}")
            trail_state = read_json(marker)
            for relative, digest in trail_state.get("files", {}).items():
                path = trail / relative
                if not path.is_file() or sha256_file(path) != digest:
                    raise OSPError(f"Existing trail integrity check failed: {relative}")
        else:
            trail.mkdir(parents=True)
            relatives = [Path(RUNTIME_DIR) / "run.json", Path(RUNTIME_DIR) / "source-manifest.json", Path(".brain") / "session.json", Path(".brain") / "review" / "final_review.md"]
            if (self.run_dir / RUNTIME_DIR / "mcp-retrieval.jsonl").is_file():
                relatives.append(Path(RUNTIME_DIR) / "mcp-retrieval.jsonl")
            relatives.extend(path.relative_to(self.run_dir) for path in self.checkpoint_dir.glob("*.json"))
            copied: dict[str, str] = {}
            for relative in relatives:
                source = self.run_dir / relative
                target = trail / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied[relative.as_posix()] = sha256_file(target)
                target.chmod(0o444)
            write_json(marker, {"run_id": self.run_dir.name, "final_review_sha256": sha256_file(self.run_dir / ".brain" / "review" / "final_review.md"), "created_at": now(), "files": copied, "upload": {"status": "not-requested"}})
        if options.upload:
            if not options.trail_repo:
                raise OSPError("--upload requires --trail-repo so review content has an explicit destination.")
            trail_state = read_json(marker)
            if trail_state.get("upload", {}).get("status") == "completed":
                return
            try:
                completed = subprocess.run(["hf", "upload", options.trail_repo, str(trail), self.run_dir.name, "--repo-type", "dataset"], capture_output=True, text=True, check=False)
            except FileNotFoundError as exc:
                raise OSPError("Trail upload requested but the Hugging Face `hf` CLI is not installed.") from exc
            if completed.returncode:
                trail_state["upload"] = {"status": "failed", "repo": options.trail_repo, "at": now(), "returncode": completed.returncode}
                write_json(marker, trail_state)
                raise OSPError(f"Trail upload failed: {completed.stderr.strip()}")
            trail_state["upload"] = {"status": "completed", "repo": options.trail_repo, "at": now()}
            write_json(marker, trail_state)


def discover_run(path: Path) -> OSPRun:
    path = path.expanduser().resolve()
    if (path / RUNTIME_DIR / "run.json").is_file():
        return OSPRun(path)
    candidates = sorted(path.glob("osp-*")) if path.is_dir() else []
    if len(candidates) == 1 and (candidates[0] / RUNTIME_DIR / "run.json").is_file():
        return OSPRun(candidates[0])
    raise OSPError(f"No unambiguous OSP run found at {path}")


def doctor() -> list[Check]:
    checks = [
        Check("opencode", shutil.which("opencode") is not None, command_version(["opencode", "--version"]) or "not found"),
        Check("python", True, sys.version.split()[0]),
        Check("venv", __import__("venv") is not None, "stdlib venv available"),
        Check("pdftotext", shutil.which("pdftotext") is not None, command_version(["pdftotext", "-v"]) or "not found"),
    ]
    return checks
