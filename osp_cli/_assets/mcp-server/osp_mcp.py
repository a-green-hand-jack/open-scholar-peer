"""
osp_mcp.py — Open ScholarPeer consolidated MCP server.

Exposes academic-search tools across four providers:
  • arXiv          — pre-prints, no API key needed
  • Semantic Scholar — citation graph, abstracts; API key recommended for higher rate limits
  • Bohrium LKM    — primary "broader coverage" source: claims, reasoning chains, paper
                     graphs via the `bohr` CLI (~3 s/call, fixed-price)
  • Google Scholar — fallback broader coverage (best-effort HTML scrape, slow,
                     only used when Bohrium LKM is unavailable)

Design principles:
  1. Dumb tools only — no agentic logic. Each tool is atomic, stateless.
  2. Rich docstrings — agents read these to decide when to call which tool.
  3. Consistent error envelope — all tools return either a list of records or
     [{"error": "..."}] (search-style) or {"error": "..."} (single-record style).
  4. Per-call timeout — every blocking call is wrapped with asyncio.wait_for
     so a hanging API call cannot block the server indefinitely.

Environment variables:
  SEMANTIC_SCHOLAR_API_KEY — optional; provides higher rate limits if set.
  OSP_CALL_TIMEOUT         — per-call timeout in seconds (default: 90).
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from typing import Any

from mcp.server.fastmcp import FastMCP

from providers import arxiv as arxiv_provider
from providers import semantic_scholar as ss_provider
from providers import google_scholar as gs_provider
from providers import bohrium as bohrium_provider

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env from CWD (project root) at server startup
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("osp_mcp")

mcp = FastMCP("osp_mcp")

_TIMEOUT = int(os.environ.get("OSP_CALL_TIMEOUT", "90"))


async def _run(fn, *args, **kwargs) -> Any:
    """Run a synchronous provider function in a thread with a timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, *args, **kwargs),
            timeout=_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"{fn.__name__} timed out after {_TIMEOUT}s")


# ---------- arXiv ----------------------------------------------------------

@mcp.tool()
async def search_arxiv(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search arXiv for pre-prints and published papers.

    arXiv is the primary repository for pre-prints in CS, math, physics, and ML.
    Use when you need recent unpublished work, concurrent submissions, or workshop
    papers that may not yet be indexed by Semantic Scholar.

    Query tips — use quoted phrases for precision:
      ti:"transformer attention"         → title search
      au:"Vaswani"                       → author search
      abs:"scaling laws"                 → abstract search
      "multi-agent" ANDNOT "survey"      → exclude surveys

    Category codes (pass in `categories`):
      cs.AI, cs.LG, cs.CL, cs.CV, cs.MA, cs.RO, cs.CR, cs.HC

    Args:
        query: Free-form or field-specific query string.
        max_results: Number of results (1-50, default 10).
        sort_by: "relevance" (default) or "date" (newest first).
        date_from: Optional start date filter (YYYY-MM-DD).
        date_to: Optional end date filter (YYYY-MM-DD).
        categories: Optional list of arXiv category codes.

    Returns:
        List of dicts with keys: arxiv_id, title, authors, summary, published,
        updated, link, pdf_url, primary_category, categories, comment.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_arxiv(query=%r, max=%d, sort=%s, from=%s, to=%s, cats=%s)",
             query, max_results, sort_by, date_from, date_to, categories)
    try:
        return await _run(arxiv_provider.search, query, max_results, sort_by,
                          date_from, date_to, categories)
    except Exception as e:
        return [{"error": f"search_arxiv failed: {e}"}]


@mcp.tool()
async def get_arxiv_paper_details(arxiv_id: str) -> dict[str, Any]:
    """Fetch detailed metadata for a specific arXiv paper by its ID.

    Use when you have a specific arXiv ID (e.g. "2305.14314" or "1706.03762")
    and want the full record with abstract, authors, dates, and categories.

    Args:
        arxiv_id: The arXiv identifier (e.g. "2305.14314" or "cs.CL/0306050").

    Returns:
        Dict with keys: arxiv_id, title, authors, summary, published, updated,
        link, pdf_url, primary_category, categories, comment.
        Returns {"error": "..."} on failure.
    """
    log.info("get_arxiv_paper_details(arxiv_id=%r)", arxiv_id)
    try:
        return await _run(arxiv_provider.get_details, arxiv_id)
    except Exception as e:
        return {"error": f"get_arxiv_paper_details failed: {e}"}


# ---------- Semantic Scholar -----------------------------------------------

@mcp.tool()
async def search_semantic_scholar(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Semantic Scholar for academic papers across all fields.

    Semantic Scholar provides high-quality citation-graph data, abstracts, and
    venue metadata. Use for established publications; for very recent pre-prints,
    prefer search_arxiv. Returns citation counts and author IDs for follow-up.

    Args:
        query: Free-form search query.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        List of dicts with keys: paperId, title, abstract, year, authors, url,
        venue, publicationTypes, citationCount, externalIds.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar(query=%r, limit=%d)", query, limit)
    try:
        return await _run(ss_provider.search_papers, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper(paper_id: str) -> dict[str, Any]:
    """Fetch full metadata for a specific Semantic Scholar paper.

    Use after search_semantic_scholar to get richer information, or when you
    have a known paperId, DOI, ArXiv ID, or ACL ID.

    Args:
        paper_id: Semantic Scholar paperId, DOI (e.g. "10.1038/nature14539"),
            ArXiv ID (e.g. "arXiv:1706.03762"), or ACL ID.

    Returns:
        Dict with keys: paperId, title, abstract, year, authors, url, venue,
        publicationTypes, citationCount, externalIds.
        Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_paper(paper_id=%r)", paper_id)
    try:
        return await _run(ss_provider.get_paper, paper_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_paper failed: {e}"}


@mcp.tool()
async def get_semantic_scholar_paper_references(
    paper_id: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Fetch the reference list (bibliography) for a specific paper.

    Returns the papers cited BY this paper. Use to verify whether a paper
    actually cites work it claims to compare against, or to find papers this
    paper builds on.

    Args:
        paper_id: Semantic Scholar paperId, DOI, ArXiv ID, or ACL ID.
        limit: Max references to return (1-100, default 50).

    Returns:
        List of dicts with keys: paperId, title, year, citationCount, authors.
        Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_references(paper_id=%r, limit=%d)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_references, paper_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_paper_references failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper_citations(
    paper_id: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Fetch the papers that cite a specific paper.

    Use to find downstream work that builds on a paper, or to assess how
    widely cited a baseline or method is.

    Args:
        paper_id: Semantic Scholar paperId, DOI, ArXiv ID, or ACL ID.
        limit: Max citations to return (1-100, default 50).

    Returns:
        List of dicts with keys: paperId, title, year, citationCount, authors.
        Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_citations(paper_id=%r, limit=%d)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_citations, paper_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_paper_citations failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_papers_batch(
    paper_ids: list[str],
) -> list[dict[str, Any]]:
    """Fetch metadata for multiple papers in a single request (up to 500).

    More efficient than calling get_semantic_scholar_paper in a loop when you
    have many IDs from a prior search or reference list.

    Args:
        paper_ids: List of paper IDs (paperId, DOI, ArXiv ID, ACL ID, etc.).

    Returns:
        List of paper dicts. Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_papers_batch(n=%d)", len(paper_ids))
    try:
        return await _run(ss_provider.get_papers_batch, paper_ids)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_papers_batch failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_author(author_id: str) -> dict[str, Any]:
    """Fetch metadata for a specific Semantic Scholar author by ID.

    Returns profile information including affiliations, paper count, citation
    count, and h-index. Use to assess whether a paper's authors have prior
    expertise in the claimed sub-field.

    Args:
        author_id: Semantic Scholar authorId (e.g. "1741101").

    Returns:
        Dict with keys: authorId, name, url, affiliations, paperCount,
        citationCount, hIndex. Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_author(author_id=%r)", author_id)
    try:
        return await _run(ss_provider.get_author, author_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_author failed: {e}"}


@mcp.tool()
async def search_semantic_scholar_authors(
    query: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Search Semantic Scholar for authors by name.

    Use when you have an author name from a paper and need their authorId for
    follow-up queries (e.g. get_semantic_scholar_author_papers).

    Args:
        query: Author name or partial name (e.g. "Yann LeCun").
        limit: Max results (1-100, default 10).

    Returns:
        List of dicts with keys: authorId, name, url, affiliations, paperCount,
        citationCount, hIndex. Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar_authors(query=%r, limit=%d)", query, limit)
    try:
        return await _run(ss_provider.search_authors, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar_authors failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_author_papers(
    author_id: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Fetch the publication list for a specific author.

    Use to find an author's other work, or to determine whether the paper's
    claimed contribution is novel compared to the authors' prior work.

    Args:
        author_id: Semantic Scholar authorId.
        limit: Max papers to return (1-100, default 50).

    Returns:
        List of paper dicts. Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_author_papers(author_id=%r, limit=%d)", author_id, limit)
    try:
        return await _run(ss_provider.get_author_papers, author_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_author_papers failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper_recommendations(
    paper_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Get papers recommended by Semantic Scholar as similar to a given paper.

    Useful for discovering related work the paper may not have cited, or for
    expanding the literature corpus during the temporal expansion round.

    Args:
        paper_id: Semantic Scholar paperId, DOI, ArXiv ID, or ACL ID.
        limit: Max recommendations (1-100, default 10).

    Returns:
        List of slim paper dicts. Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_recommendations(paper_id=%r, limit=%d)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_recommendations, paper_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_paper_recommendations failed: {e}"}]


@mcp.tool()
async def search_semantic_scholar_snippets(
    query: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Search for text snippets from paper abstracts/bodies matching a query.

    Unlike search_semantic_scholar (which matches metadata), this returns actual
    ~500-word excerpts from the paper text. Use when you need to verify that a
    paper actually discusses a specific concept, or to find papers containing
    specific technical claims.

    Args:
        query: Free-form query describing the content to find.
        limit: Max snippets (1-20, default 10).

    Returns:
        List of dicts with keys: snippetId, text, paper (slim paper record).
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar_snippets(query=%r, limit=%d)", query, limit)
    try:
        return await _run(ss_provider.search_snippets, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar_snippets failed: {e}"}]


# ---------- Google Scholar -------------------------------------------------

@mcp.tool()
async def search_google_scholar(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search Google Scholar for broader academic coverage.

    Google Scholar indexes content beyond standard publications: blog posts,
    workshop papers, theses, technical reports, and pre-prints from sources
    other than arXiv. Use as a third retrieval source to catch what arXiv
    and Semantic Scholar miss.

    Note: Uses HTML scraping; results may vary and rate limits may apply.

    Args:
        query: Free-form search query.
        num_results: Maximum number of results (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_google_scholar(query=%r, num_results=%d)", query, num_results)
    try:
        return await _run(gs_provider.search, query, num_results)
    except Exception as e:
        return [{"error": f"search_google_scholar failed: {e}"}]


@mcp.tool()
async def search_google_scholar_advanced(
    query: str,
    author: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    num_results: int = 5,
) -> list[dict[str, Any]]:
    """Search Google Scholar with author and year-range filters.

    Use when you need to search within a specific time window (e.g. "last 12
    months" for the temporal-expansion round) or constrain to a specific
    author's body of work.

    Args:
        query: Free-form search query.
        author: Optional author-name filter.
        year_start: Optional inclusive start year (e.g. 2024).
        year_end: Optional inclusive end year (e.g. 2026).
        num_results: Maximum number of results (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url.
        Returns [{"error": "..."}] on failure.
    """
    log.info(
        "search_google_scholar_advanced(query=%r, author=%r, yr=%s-%s, n=%d)",
        query, author, year_start, year_end, num_results,
    )
    year_range = (year_start, year_end) if (year_start or year_end) else None
    try:
        return await _run(gs_provider.search_advanced, query, author, year_range, num_results)
    except Exception as e:
        return [{"error": f"search_google_scholar_advanced failed: {e}"}]


@mcp.tool()
async def get_google_scholar_author_info(author_name: str) -> dict[str, Any]:
    """Fetch a Google Scholar author profile.

    Returns affiliation, research interests, total citation count, and the
    author's top publications. Use to verify expertise claims or find an
    author's other work.

    Note: Uses the `scholarly` library; may be rate-limited by Google.

    Args:
        author_name: The author's name to look up (e.g. "Ian Goodfellow").

    Returns:
        Dict with keys: name, affiliation, interests, citedby, publications
        (list of top 5 with title, year, citations). Returns {"error": "..."}
        on failure.
    """
    log.info("get_google_scholar_author_info(author_name=%r)", author_name)
    try:
        return await _run(gs_provider.get_author_info, author_name)
    except Exception as e:
        return {"error": f"get_google_scholar_author_info failed: {e}"}


# ---------- Bohrium LKM ----------------------------------------------------

@mcp.tool()
async def search_bohrium_lkm(
    query: str,
    top_k: int = 10,
    scopes: str = "conclusion,abstract",
) -> dict[str, Any]:
    """Search Bohrium's Large Knowledge Model corpus (claims + papers).

    This is the PRIMARY replacement for Google Scholar in the Literature
    phase. LKM is a semantic + keyword index over scientific claims, abstracts,
    conclusions, and questions — not a web scrape — so queries hit the content
    of prior work, and results come back in ~3 seconds with structured paper
    metadata (title, authors, DOI, venue, date).

    Prefer this over search_google_scholar whenever it is available. Each call
    is fixed-price (0.05 CNY, covered first by LKM's personal monthly 1,000-call
    quota).

    Args:
        query: Natural-language search query (e.g. "multi-agent peer review").
        top_k: Number of results to return (default 10).
        scopes: Comma-separated content scopes to search:
            abstract|claim|premise|conclusion|question|problem|open_question|
            subproblem|reasoning_chain (default "conclusion,abstract").

    Returns:
        Dict with keys: papers (list of {id, title, authors, doi, venue, area,
        date}) and variables (list of LKM claim records). Returns
        {"error": "..."} on failure (e.g. bohr CLI missing or not logged in).
    """
    log.info("search_bohrium_lkm(query=%r, top_k=%d, scopes=%r)", query, top_k, scopes)
    try:
        return await _run(bohrium_provider.search_lkm, query, top_k, scopes)
    except Exception as e:
        return {"error": f"search_bohrium_lkm failed: {e}"}


@mcp.tool()
async def search_bohrium_reasoning(query: str, top_k: int = 10) -> dict[str, Any]:
    """Search LKM reasoning chains (conclusions with their supporting logic).

    Each hit is a conclusion plus a score and the paper it belongs to. Use this
    for the method-anchor literature round: it finds prior work that reached a
    result through the same technique, not just the same topic.

    Args:
        query: Natural-language query about the method/technique.
        top_k: Number of reasoning chains to return (default 10).

    Returns:
        Dict with keys: papers (list of paper records) and reasoning_chains
        (list of {paper_id, conclusion_title, conclusion_text, score}).
        Returns {"error": "..."} on failure.
    """
    log.info("search_bohrium_reasoning(query=%r, top_k=%d)", query, top_k)
    try:
        return await _run(bohrium_provider.search_reasoning, query, top_k)
    except Exception as e:
        return {"error": f"search_bohrium_reasoning failed: {e}"}


@mcp.tool()
async def get_bohrium_paper_graph(
    paper_id: str,
    max_nodes: int = 25,
    max_edges: int = 40,
) -> dict[str, Any]:
    """Retrieve a paper-level knowledge graph from LKM.

    Given a numeric LKM paper id (from search_bohrium_lkm / search_bohrium_
    reasoning / search_bohrium_paper), returns the paper metadata, the problems
    it addresses, its open questions, and a bounded node/edge graph. Use after
    a top hit to expand into its references and reasoning structure without
    another full search.

    Args:
        paper_id: Numeric LKM paper id (e.g. "1106616599630053397").
        max_nodes: Maximum graph nodes to include (default 25).
        max_edges: Maximum graph edges to include (default 40).

    Returns:
        Dict with keys: paper, addressed_problems, open_questions, graph
        ({graph_empty, node_count, edge_count, nodes, edges}). A paper that
        exists but has no extracted knowledge graph returns graph_empty=true
        with zero nodes/edges — inspect graph_empty before iterating nodes.
        Node contents are truncated to 400 chars to bound the payload.
        Returns {"error": "..."} on failure.
    """
    log.info("get_bohrium_paper_graph(paper_id=%r, nodes=%d, edges=%d)",
             paper_id, max_nodes, max_edges)
    try:
        return await _run(bohrium_provider.get_paper_graph, paper_id, max_nodes, max_edges)
    except Exception as e:
        return {"error": f"get_bohrium_paper_graph failed: {e}"}


@mcp.tool()
async def search_bohrium_paper(
    query: str,
    size: int = 10,
    year_from: int | None = None,
    year_to: int | None = None,
    jcr: str | None = None,
) -> dict[str, Any]:
    """Search Bohrium's academic paper index (normal tier).

    Returns clean paper records with citation counts, venue, DOI, and JCR
    zone. Year filters make this the natural tool for the temporal-expansion
    round ("last 12 months"). Normal tier is 0.05 CNY/call; enhanced tier
    (--type 1) is 0.10 CNY and is NOT used by this tool.

    Args:
        query: Free-form paper search query.
        size: Page size (default 10).
        year_from: Optional inclusive start year (e.g. 2025).
        year_to: Optional inclusive end year (e.g. 2026).
        jcr: Optional comma-separated JCR zones (e.g. "Q1,Q2").

    Returns:
        Dict with keys: papers (list of {title, authors, abstract, doi,
        paper_id, venue, date, citations, jcr_zone, url}) and pagination.
        Returns {"error": "..."} on failure.
    """
    log.info("search_bohrium_paper(query=%r, size=%d, yr=%s-%s, jcr=%r)",
             query, size, year_from, year_to, jcr)
    try:
        return await _run(
            bohrium_provider.search_papers, query, size, year_from, year_to, jcr
        )
    except Exception as e:
        return {"error": f"search_bohrium_paper failed: {e}"}


# ---------- Bohrium LKM PDF parse (query-seeding enhancement) ---------------

@mcp.tool()
async def submit_bohrium_pdf(pdf_path: str) -> dict[str, Any]:
    """Submit a local PDF to Bohrium LKM for knowledge extraction.

    Feed the paper UNDER REVIEW through this (from `.brain/input/`) to learn
    its own questions, conclusions, and reasoning steps — then use those as
    query seeds in `/2-osp-literature`, so the searches target the paper's
    actual claims instead of a paraphrase.

    Free to submit. Returns task_id plus pdf_md5 and cache_hit. The task runs
    asynchronously: poll with check_bohrium_parse_task or wait_bohrium_parse_
    task, then fetch the result with get_bohrium_parse_result (billable).

    Paper limits: non-empty regular PDF, at most 64 MiB and 50 pages. If the
    paper exceeds these, submit fails — proceed with the literature phase
    without the extraction.

    Args:
        pdf_path: Absolute or relative path to the PDF to parse.

    Returns:
        Dict with keys: task_id, status, pdf_md5, cache_hit, created_at.
        Returns {"error": "..."} on failure.
    """
    log.info("submit_bohrium_pdf(pdf_path=%r)", pdf_path)
    try:
        return await _run(bohrium_provider.parse_submit, pdf_path)
    except Exception as e:
        return {"error": f"submit_bohrium_pdf failed: {e}"}


@mcp.tool()
async def check_bohrium_parse_task(task_id: str) -> dict[str, Any]:
    """Check an LKM PDF-parse task's current status. Free.

    Non-terminal stages: queued, running. Terminal stages: succeeded, partial,
    failed. `partial` means the paper could not produce a complete knowledge
    graph (do not resubmit it); `failed` is technical and the PDF may be
    resubmitted.

    Args:
        task_id: The task id returned by submit_bohrium_pdf.

    Returns:
        Dict with keys: task_id, status, stage, updated_at. Returns
        {"error": "..."} on failure.
    """
    log.info("check_bohrium_parse_task(task_id=%r)", task_id)
    try:
        return await _run(bohrium_provider.parse_status, task_id)
    except Exception as e:
        return {"error": f"check_bohrium_parse_task failed: {e}"}


@mcp.tool()
async def wait_bohrium_parse_task(
    task_id: str,
    interval_s: int = 5,
    timeout_s: int = 60,
) -> dict[str, Any]:
    """Block until an LKM PDF-parse task reaches a terminal state. Free.

    The CLI wait is interrupted at `timeout_s` seconds. A timeout is NOT a
    failure — it returns status "running" and the remote task keeps going, so
    just call this again (or check_bohrium_parse_task). Keep `timeout_s`
    below the MCP server's OSP_CALL_TIMEOUT (default 90) or the outer wrapper
    will cut the call first.

    Args:
        task_id: The task id returned by submit_bohrium_pdf.
        interval_s: Poll interval in seconds (default 5).
        timeout_s: How long to wait before returning (default 60).

    Returns:
        Dict with the terminal status (task_id, status, stage) or a
        {"task_id", "status": "running", "warning"} on wait timeout.
        Returns {"error": "..."} on hard failure.
    """
    log.info("wait_bohrium_parse_task(task_id=%r, interval=%ds, timeout=%ds)",
             task_id, interval_s, timeout_s)
    try:
        return await _run(bohrium_provider.parse_wait, task_id, interval_s, timeout_s)
    except Exception as e:
        return {"error": f"wait_bohrium_parse_task failed: {e}"}


@mcp.tool()
async def get_bohrium_parse_result(task_id: str) -> dict[str, Any]:
    """Fetch a completed LKM PDF-parse task's knowledge extraction. Billable.

    Result pricing: 1.00 CNY the first time for a submission that did not hit
    cache, 0.10 CNY on a cache hit. Only call after the task is terminal
    (check_bohrium_parse_task / wait_bohrium_parse_task said succeeded).
    Returns addressed problems, open questions, and a nodes/edges graph —
    the paper's own research questions and conclusions that seed literature
    queries.

    Args:
        task_id: The task id returned by submit_bohrium_pdf.

    Returns:
        Dict shaped like get_bohrium_paper_graph: paper, addressed_problems,
        open_questions, graph. Returns {"error": "..."} on failure.
    """
    log.info("get_bohrium_parse_result(task_id=%r)", task_id)
    try:
        return await _run(bohrium_provider.parse_result, task_id)
    except Exception as e:
        return {"error": f"get_bohrium_parse_result failed: {e}"}


# ---------- Server entrypoint ----------------------------------------------

if __name__ == "__main__":
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        log.info("Semantic Scholar API key detected — higher rate limits enabled.")
    else:
        log.info("No SEMANTIC_SCHOLAR_API_KEY in env — Semantic Scholar will use anonymous limits.")
    log.info("Starting Open ScholarPeer MCP server (osp_mcp), timeout=%ds", _TIMEOUT)
    if shutil.which("bohr") is not None:
        log.info("Bohrium LKM CLI detected — LKM-first literature retrieval enabled.")
    else:
        log.info("No 'bohr' CLI found — Google Scholar will be used as fallback.")
    mcp.run(transport="stdio")
