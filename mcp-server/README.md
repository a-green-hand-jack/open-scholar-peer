# `osp_mcp` — Open ScholarPeer MCP Server

Single FastMCP server exposing academic-search tools across four providers.

## Tools

### Bohrium LKM (primary broad-coverage source; requires `bohr`)
- `search_bohrium_lkm`, `search_bohrium_reasoning`, `search_bohrium_paper`, and `get_bohrium_paper_graph`
- `submit_bohrium_pdf`, `check_bohrium_parse_task`, `wait_bohrium_parse_task`, and `get_bohrium_parse_result`

LKM search calls cost 0.05 CNY each. The OSP agent uses LKM first and Google Scholar only after an LKM error. Install the official CLI with `npm i -g @dptech-corp/bohr-cli`, then authenticate with `bohr auth login`. OSP never handles or logs the CLI credentials.

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

The TypeScript runtime copies this server into `<review-workspace>/.open-scholar-peer/mcp/` and creates an isolated Python virtualenv with all dependencies.

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
