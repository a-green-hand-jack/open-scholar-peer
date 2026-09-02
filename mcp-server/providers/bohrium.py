"""Bohrium LKM provider backed by the official ``bohr`` CLI."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

BOHR_TIMEOUT = 30

def _call(args: list[str], keep_error_data: bool = False) -> dict[str, Any]:
    billable = any(part in {"search", "reasoning", "graph", "result"} for part in args)
    if billable and os.environ.get("OSP_ALLOW_LKM_SPEND") != "1":
        return {"error": "LKM spending is not authorized for this run; pass --allow-lkm-spend to osp review"}
    if shutil.which("bohr") is None:
        return {"error": "bohr CLI not found; install @dptech-corp/bohr-cli and run bohr auth login"}
    try:
        result = subprocess.run(["bohr", *args, "--yes", "-o", "json"], capture_output=True, text=True, timeout=BOHR_TIMEOUT, check=False)
        output = result.stdout.strip()
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            try:
                payload = next(json.loads(line) for line in reversed(output.splitlines()) if line.strip().startswith("{"))
            except (StopIteration, json.JSONDecodeError) as error:
                return {"error": f"bohr returned invalid JSON: {error}"}
    except subprocess.TimeoutExpired:
        return {"error": f"bohr command timed out after {BOHR_TIMEOUT}s"}
    except (json.JSONDecodeError, IndexError) as error:
        return {"error": f"bohr returned invalid JSON: {error}"}
    if not payload.get("ok", False):
        if keep_error_data and payload.get("data"):
            return payload["data"]
        error = payload.get("error") or {}
        return {"error": error.get("message") or error.get("code") or str(error)}
    return payload.get("data") or {}

def _paper(value: dict[str, Any]) -> dict[str, Any]:
    return {"id": value.get("id", value.get("paperId", "")), "title": value.get("en_title") or value.get("zh_title") or value.get("enName") or value.get("zhName") or "", "authors": value.get("authors") or "", "abstract": value.get("enAbstract") or "", "doi": value.get("doi") or "", "venue": value.get("publication_name") or value.get("publicationEnName") or "", "date": value.get("cover_date_start") or value.get("coverDateStart") or "", "citations": value.get("citationNums", 0), "jcr_zone": value.get("jcrZone") or "", "url": value.get("paperUrl") or ""}

def search_lkm(query: str, top_k: int = 10, scopes: str = "claim,conclusion,abstract") -> dict[str, Any]:
    data = _call(["lkm", "search", query, "--top-k", str(top_k), "--scopes", scopes])
    if "error" in data: return data
    return {"papers": [_paper(item) for item in (data.get("papers") or {}).values()], "variables": (data.get("variables") or [])[:top_k]}

def search_reasoning(query: str, top_k: int = 10) -> dict[str, Any]:
    data = _call(["lkm", "reasoning", "--query", query, "--top-k", str(top_k)])
    if "error" in data: return data
    return {"papers": [_paper(item) for item in (data.get("papers") or {}).values()], "reasoning_chains": (data.get("reasoning_chains") or [])[:top_k]}

def search_papers(query: str, size: int = 10, year_from: int | None = None, year_to: int | None = None, jcr: str | None = None) -> dict[str, Any]:
    args = ["paper", "search", query, "--size", str(size), "--type", "0"]
    if year_from is not None: args += ["--year-from", str(year_from)]
    if year_to is not None: args += ["--year-to", str(year_to)]
    if jcr: args += ["--jcr", jcr]
    data = _call(args)
    if "error" in data: return data
    return {"papers": [_paper(item) for item in data.get("items", [])], "pagination": data.get("pagination") or {}}

def get_paper_graph(paper_id: str, max_nodes: int = 25, max_edges: int = 40) -> dict[str, Any]:
    data = _call(["lkm", "graph", "--paper-id", paper_id], keep_error_data=True)
    if "error" in data: return data
    item = (data.get("items") or [None])[0]
    if not item: return {"error": f"no graph found for paper {paper_id}"}
    graph = item.get("graph") or {}
    nodes, edges = graph.get("nodes") or [], graph.get("edges") or []
    return {"paper": _paper(item.get("paper") or {}), "addressed_problems": item.get("addressed_problems") or [], "open_questions": item.get("open_questions") or [], "graph": {"graph_empty": not nodes, "node_count": len(nodes), "edge_count": len(edges), "nodes": nodes[:max_nodes], "edges": edges[:max_edges]}}

def parse_submit(pdf_path: str) -> dict[str, Any]:
    workspace = os.environ.get("OSP_WORKSPACE_ROOT")
    if not workspace:
        return {"error": "OSP_WORKSPACE_ROOT is not configured"}
    root = (Path(workspace) / ".brain" / "input").resolve()
    candidate = Path(pdf_path).resolve()
    if candidate.parent != root or candidate.suffix.lower() != ".pdf" or not candidate.is_file():
        return {"error": "pdf_path must be a regular PDF directly under .brain/input"}
    if candidate.stat().st_size > 64 * 1024 * 1024:
        return {"error": "PDF exceeds the 64 MiB extraction limit"}
    return _call(["lkm", "parse", "submit", str(candidate)])
def parse_status(task_id: str) -> dict[str, Any]: return _call(["lkm", "parse", "status", task_id])
def parse_wait(task_id: str, interval_s: int = 5, timeout_s: int = 60) -> dict[str, Any]:
    result = _call(["lkm", "parse", "wait", task_id, "--interval", f"{interval_s}s", "--timeout", f"{timeout_s}s"])
    if "error" in result and ("TIMEOUT" in result["error"] or "stopped waiting" in result["error"]):
        return {"task_id": task_id, "status": "running", "warning": result["error"]}
    return result
def parse_result(task_id: str) -> dict[str, Any]: return _call(["lkm", "parse", "result", task_id, "--format", "graph"])
