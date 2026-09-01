# `osp_mcp` — Open ScholarPeer MCP Server

Single FastMCP server exposing academic-search tools across four providers.

## Tools

### Bohrium LKM (primary broad-coverage source; requires the `bohr` CLI)
- `search_bohrium_lkm(query, top_k=10, scopes="conclusion,abstract")` — claims + papers
- `search_bohrium_reasoning(query, top_k=10)` — reasoning chains (same-technique hits)
- `get_bohrium_paper_graph(paper_id, max_nodes=25, max_edges=40)` — paper knowledge graph
- `search_bohrium_paper(query, size=10, year_from=None, year_to=None, jcr=None)` — paper records with year/JCR filters
- `submit_bohrium_pdf(pdf_path)` — async knowledge extraction of a local PDF (free)
- `check_bohrium_parse_task(task_id)` / `wait_bohrium_parse_task(task_id, interval_s=5, timeout_s=60)` — poll the parse task (free)
- `get_bohrium_parse_result(task_id)` — fetched extraction; 1.00 CNY first time / 0.10 CNY on cache hit

### arXiv (no API key needed)
- `search_arxiv(query, max_results=10)`
- `get_arxiv_paper_details(arxiv_id)`

### Semantic Scholar (API key recommended for higher rate limits)
- `search_semantic_scholar(query, limit=10)`
- `get_semantic_scholar_paper_details(paper_id)`
- `get_semantic_scholar_author_details(author_id)`
- `get_semantic_scholar_citations_and_references(paper_id)`

### Google Scholar (fallback only, best-effort, HTML-scraped)
- `search_google_scholar(query, num_results=5)`
- `search_google_scholar_advanced(query, author=None, year_start=None, year_end=None, num_results=5)`
- `get_google_scholar_author_info(author_name)`

## Setup

The installer (`bash install.sh`) copies this server into `<your-project>/.open-scholar-peer/mcp/` and creates a Python virtualenv with all dependencies. You don't need to manage it manually.

For the Bohrium LKM tools you also need the official `bohr` CLI on PATH (the server shells out to it; it stores its own login, no API key is handled by OSP):

```bash
npm i -g @dptech-corp/bohr-cli
bohr auth login
```

If `bohr` is missing or not logged in, the LKM tools return `{"error": ...}` and the OSP literature agents fall back to the Google Scholar tools. LKM searches are fixed-price calls (0.05 CNY each; the personal monthly 1,000-call quota, Asia/Shanghai calendar month, covers the first calls). The tools never page through results automatically.

If you want to run it standalone for testing:

```bash
cd mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: provide a Semantic Scholar API key for higher rate limits
export SEMANTIC_SCHOLAR_API_KEY=sk-...

python osp_mcp.py
```

The server runs on stdio and is meant to be spawned by an MCP-aware host (Claude Code, Cursor, Gemini CLI, etc.) — not invoked directly by users.

## Getting a Semantic Scholar API key

Free at: https://www.semanticscholar.org/product/api#api-key. Without a key, anonymous rate limits apply (~100 requests / 5 min). With a key, ~1 request/sec sustained.

Set it at install time or later via env var:
```bash
export SEMANTIC_SCHOLAR_API_KEY=sk-...
```

## Extending — adding a new provider

1. Create `providers/<name>.py` with plain Python functions for search/get-detail. See `providers/bohrium.py` for an example of wrapping an external CLI with a short timeout while keeping the server's `{"error": ...}` envelope.
2. Import it at the top of `osp_mcp.py` and add `@mcp.tool()`-decorated wrappers.
3. Document each tool with a rich docstring (the MCP host shows it to the LLM).
4. Add the new dependencies to `requirements.txt` (none needed for CLI wrappers).
5. (Optional) Document API-key env vars in this README.

The framework principle is **dumb tools only** — no agentic logic in the server. Cognitive decisions about *what* to search and *when* to stop belong to the OSP agents in the calling tool.
