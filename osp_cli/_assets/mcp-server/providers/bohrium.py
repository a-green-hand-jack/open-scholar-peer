"""Bohrium LKM provider.

Wraps the official `bohr` CLI (npm package `@dptech-corp/bohr-cli`) so the OSP
literature agents can query Bohrium's Large Knowledge Model (LKM) — papers,
claims, reasoning chains, and paper knowledge graphs — without owning any
credential in this process. The CLI uses its own stored login
(`bohr auth login`); no API key is read, passed, or logged here.

Why this replaces Google Scholar as the primary "broader coverage" source:
  • LKM is a semantic+keyword knowledge index over scientific claims,
    abstracts, conclusions, and reasoning chains — not a raw web scrape.
  • Measured latency is ~3 s/call vs Google Scholar's best-effort HTML
    scraping, which routinely hits Google-side blocks and can hang for tens
    of seconds (the old provider's requests timeout was 90 s).

Cost / billing notes:
  • `lkm search`, `lkm reasoning`, `lkm graph`, `lkm claim reasoning`, and
    `lkm variables` are fixed-price calls at 0.05 CNY each, covered first by
    LKM's personal monthly 1,000-call quota (Asia/Shanghai calendar month).
  • `paper search` normal tier is 0.05 CNY/call; enhanced tier is 0.10 CNY.
  • Every call passes `--yes` to satisfy the CLI's billing-confirmation gate
    in non-interactive use. Spending must be authorized by the OSP user once
    before this provider is enabled (see the onboarding docs).
  • Pagination is a new paid call each time — the tools below never page
    automatically.

Invariant: every public function returns either a dict holding the requested
data or `{"error": "..."}`. The MCP wrappers in `osp_mcp.py` pass this
through, keeping the server-wide error envelope consistent.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

BOHR_BIN = "bohr"
# Measured latency is ~3 s; 30 s is a generous cap so a wedged CLI cannot
# burn the full 90 s OSP_CALL_TIMEOUT the way Google Scholar scraping could.
BOHR_TIMEOUT = 30


def _parse_stdout_json(stdout: str) -> dict[str, Any]:
    """Parse bohr's stdout, tolerating NDJSON progress lines / trailing text.

    Some commands (e.g. `lkm parse wait`) emit several JSON documents (poll
    progress) and occasionally a plain-text line. The authoritative state is
    the last valid JSON document; everything else is transient.
    """
    text = stdout.strip()
    if not text:
        raise json.JSONDecodeError("empty stdout", stdout, 0)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    last: dict[str, Any] | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            last = candidate
    if last is not None:
        return last
    raise json.JSONDecodeError("no JSON object found", stdout, 0)


def _call_bohr(args: list[str], allow_error_data: bool = False) -> dict[str, Any]:
    """Run `bohr <args> --yes -o json` and return the `data` envelope.

    `allow_error_data` lets a caller keep the CLI's `data` payload even when
    `ok` is false — needed for `lkm graph`, where OK=false still returns the
    paper record when the knowledge graph is empty (a usable, non-fatal state).
    """
    if shutil.which(BOHR_BIN) is None:
        return {"error": (
            f"{BOHR_BIN} CLI not found on PATH. Install with "
            "`npm i -g @dptech-corp/bohr-cli`, then `bohr auth login`."
        )}
    cmd = [BOHR_BIN, *args, "--yes", "-o", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=BOHR_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"error": f"{BOHR_BIN} {' '.join(args)} timed out after {BOHR_TIMEOUT}s"}
    stderr = (proc.stderr or "").strip()[:500]
    if proc.returncode != 0 and not (proc.stdout or "").strip():
        return {"error": f"{BOHR_BIN} {' '.join(args)} exited {proc.returncode}: {stderr}"}
    try:
        payload = _parse_stdout_json(proc.stdout)
    except json.JSONDecodeError:
        return {"error": (
            f"{BOHR_BIN} {' '.join(args)} exited {proc.returncode} "
            f"with non-JSON output: {(proc.stdout or '')[:300]}"
        )}
    if not payload.get("ok", False):
        if allow_error_data and payload.get("data"):
            return payload["data"]
        err = payload.get("error", {}) or {}
        msg = err.get("message") or err.get("code") or str(err)
        return {"error": f"{BOHR_BIN} error: {msg}"}
    return payload.get("data", {})


def _lkm_paper_record(p: dict[str, Any]) -> dict[str, Any]:
    """Map an LKM corpus paper record to a lean, LLM-friendly shape."""
    return {
        "id": p.get("id", ""),
        "title": p.get("en_title") or p.get("zh_title") or "",
        "authors": p.get("authors") or "",
        "doi": p.get("doi") or "",
        "venue": p.get("publication_name") or "",
        "area": p.get("area") or "",
        "date": p.get("cover_date_start") or p.get("publication_date") or "",
    }


def _paper_search_record(r: dict[str, Any]) -> dict[str, Any]:
    """Map a `bohr paper search` record to a lean, LLM-friendly shape."""
    return {
        "title": r.get("enName") or r.get("zhName") or "",
        "authors": r.get("authors") or "",
        "abstract": r.get("enAbstract") or "",
        "doi": r.get("doi") or "",
        "paper_id": r.get("paperId") or "",
        "venue": r.get("publicationEnName") or "",
        "date": r.get("coverDateStart") or "",
        "citations": r.get("citationNums") or 0,
        "jcr_zone": r.get("jcrZone") or "",
        "url": r.get("paperUrl") or "",
    }


def search_lkm(query: str, top_k: int = 10, scopes: str = "conclusion,abstract") -> dict[str, Any]:
    """Semantic+keyword search over the LKM ingested corpus.

    Combines paper records with the claims/variables attached to them. This is
    the primary replacement for Google Scholar in the Literature phase: it
    indexes scientific claims, abstracts, and conclusions rather than raw web
    pages, so a query hits the *content* of prior work, not just its title.
    """
    data = _call_bohr(["lkm", "search", query, "--top-k", str(top_k), "--scopes", scopes])
    if "error" in data:
        return data
    papers = data.get("papers") or {}
    variables = data.get("variables") or []
    return {
        "papers": [_lkm_paper_record(v) for v in papers.values()],
        "variables": variables[:top_k],
    }


def search_reasoning(query: str, top_k: int = 10) -> dict[str, Any]:
    """Search whole reasoning chains in the LKM corpus.

    Each hit is a conclusion plus its supporting factors/motivating questions
    and the paper it belongs to. Ideal for the method-anchor round: it finds
    prior work that reached a result through the *same technique*.
    """
    data = _call_bohr(["lkm", "reasoning", "--query", query, "--top-k", str(top_k)])
    if "error" in data:
        return data
    papers = data.get("papers") or {}
    chains = data.get("reasoning_chains") or []
    return {
        "papers": [_lkm_paper_record(v) for v in papers.values()],
        "reasoning_chains": [
            {
                "paper_id": c.get("paper_id", ""),
                "conclusion_title": c.get("conclusion_title", ""),
                "conclusion_text": c.get("conclusion_text", ""),
                "score": c.get("score", 0),
            }
            for c in chains[:top_k]
        ],
    }


def get_paper_graph(paper_id: str, max_nodes: int = 25, max_edges: int = 40) -> dict[str, Any]:
    """Retrieve a paper-level knowledge graph from LKM.

    Node contents are truncated to keep the LLM payload bounded; the full
    content hash stays in the CLI output if a caller needs it verbatim.
    A paper that is found but has no extracted graph returns the paper record
    with `graph_empty: true` and zero nodes/edges — not an error.
    """
    data = _call_bohr(["lkm", "graph", "--paper-id", paper_id], allow_error_data=True)
    if "error" in data:
        return data
    items = data.get("items") or []
    if not items:
        return {"error": f"no graph found for paper {paper_id}"}
    item = items[0]
    graph = item.get("graph") or {}
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    return {
        "paper": _lkm_paper_record(item.get("paper") or {}),
        "addressed_problems": item.get("addressed_problems") or [],
        "open_questions": item.get("open_questions") or [],
        "graph": {
            "graph_empty": len(nodes) == 0,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": [
                {
                    "id": n.get("id", ""),
                    "kind": n.get("kind", ""),
                    "type": n.get("type", ""),
                    "content": (n.get("content") or "")[:400],
                }
                for n in nodes[:max_nodes]
            ],
            "edges": [
                {"source": e.get("source", ""), "target": e.get("target", ""), "type": e.get("type", "")}
                for e in edges[:max_edges]
            ],
        },
    }


def search_papers(
    query: str,
    size: int = 10,
    year_from: int | None = None,
    year_to: int | None = None,
    jcr: str | None = None,
) -> dict[str, Any]:
    """Search Bohrium's academic paper index (normal tier).

    Supports year windows (`year_from`/`year_to`) which makes it the natural
    tool for the temporal-expansion round (last 12 months of work), and JCR
    zone filters for journal-quality filtering. It returns clean citation
    counts and venue metadata, unlike Google Scholar's scrape.
    """
    args = ["paper", "search", query, "--size", str(size), "--type", "0"]
    if year_from is not None:
        args += ["--year-from", str(year_from)]
    if year_to is not None:
        args += ["--year-to", str(year_to)]
    if jcr:
        args += ["--jcr", jcr]
    data = _call_bohr(args)
    if "error" in data:
        return data
    items = data.get("items") or []
    return {
        "papers": [_paper_search_record(i) for i in items],
        "pagination": data.get("pagination") or {},
    }


def parse_submit(pdf_path: str) -> dict[str, Any]:
    """Submit a local PDF to LKM for asynchronous knowledge extraction.

    Free. Returns the task_id plus `pdf_md5` and `cache_hit`. A cache hit
    means a previous extraction already exists, so `parse_result` will be
    charged at the discounted rate.
    """
    return _call_bohr(["lkm", "parse", "submit", pdf_path])


def parse_status(task_id: str) -> dict[str, Any]:
    """Check an LKM parse task's current stage. Free."""
    return _call_bohr(["lkm", "parse", "status", task_id])


def parse_wait(task_id: str, interval_s: int = 5, timeout_s: int = 60) -> dict[str, Any]:
    """Block until an LKM parse task reaches a terminal state. Free.

    `queued`/`running` are non-terminal; `succeeded`/`partial`/`failed` are
    terminal. A wait timeout is NOT a hard failure — the remote task keeps
    running, so the caller should wait again or check `parse_status`. The CLI
    needs Go-style durations, hence the units appended here.
    """
    data = _call_bohr([
        "lkm", "parse", "wait", task_id,
        "--interval", f"{interval_s}s",
        "--timeout", f"{timeout_s}s",
    ])
    if "error" in data:
        msg = str(data["error"])
        # The CLI reports wait expiry as an error ("stopped waiting after…"),
        # but the remote task keeps running — a retryable state, not a failure.
        if "LKM_PARSE_WAIT_TIMEOUT" in msg or "stopped waiting after" in msg:
            return {"task_id": task_id, "status": "running", "warning": msg}
        return data
    return data


def parse_result(task_id: str) -> dict[str, Any]:
    """Fetch a completed parse task's knowledge extraction. Billable.

    The first successful Result costs 1.00 CNY when the submission did not hit
    cache, or 0.10 CNY on a cache hit. Uses `--format graph` so the returned
    shape matches `get_paper_graph` (addressed problems, open questions, and a
    nodes/edges graph) — ideal for seeding literature queries from the paper's
    own questions and conclusions. Only call after the task is terminal.
    """
    data = _call_bohr(["lkm", "parse", "result", task_id, "--format", "graph"])
    if "error" in data:
        return data
    graph = data.get("graph") or {}
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    data["graph"] = {
        "graph_empty": len(nodes) == 0,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [
            {
                "id": n.get("id", ""),
                "kind": n.get("kind", ""),
                "type": n.get("type", ""),
                "content": (n.get("content") or "")[:400],
            }
            for n in nodes[:25]
        ],
        "edges": [
            {"source": e.get("source", ""), "target": e.get("target", ""), "type": e.get("type", "")}
            for e in edges[:40]
        ],
    }
    return data