# `osp_mcp` — Open ScholarPeer MCP Server

Single FastMCP server exposing academic-search tools across multiple providers.

## Tools

### arXiv (no API key needed)
- `search_arxiv(query, max_results=10)`
- `get_arxiv_paper_details(arxiv_id)`

### Semantic Scholar (API key recommended for higher rate limits)
- `search_semantic_scholar(query, limit=10)`
- `get_semantic_scholar_paper_details(paper_id)`
- `get_semantic_scholar_author_details(author_id)`
- `get_semantic_scholar_citations_and_references(paper_id)`

### Google Scholar (best-effort, HTML-scraped)
- `search_google_scholar(query, num_results=5)`
- `search_google_scholar_advanced(query, author=None, year_start=None, year_end=None, num_results=5)`
- `get_google_scholar_author_info(author_name)`

### DBLP (no API key needed)
- `search_dblp(query, max_results=10)`
- `get_dblp_publication_details(key)`

### PubMed (no API key needed)
- `search_pubmed(query, max_results=10)`
- `get_pubmed_article_details(pmid)`

### bioRxiv (no API key needed; search is proxied via Europe PMC — see providers/biorxiv.py docstring)
- `search_biorxiv(query, max_results=10)`
- `get_biorxiv_preprint_details(doi)`

### medRxiv (no API key needed)
- `search_medrxiv(query, max_results=10, days_back=365)`
- `get_medrxiv_paper_details(doi)`

### Web of Science (API key required)
- `search_wos(query, max_results=10, database="WOS")`
- `get_wos_paper_details(doi, database="WOS")`

### Scopus (API key required)
- `search_scopus(query, max_results=10)`
- `get_scopus_paper_details(doi)`

### ACM Digital Library (no API key needed — via Crossref)
- `search_acm(query, max_results=10)`
- `get_acm_paper_details(doi)`

### Springer Nature (API key required)
- `search_springer(query, max_results=10)`
- `get_springer_paper_details(doi)`

### IEEE Xplore (API key required)
- `search_ieee_xplore(query, max_results=10)`
- `get_ieee_xplore_paper_details(article_number_or_doi)`

### ScienceDirect (API key required; abstract/full text depend on entitlement)
- `search_sciencedirect(query, max_results=10)`
- `get_sciencedirect_paper_details(identifier)`

## Setup

The installer (`bash install.sh`) copies this server into `<your-project>/.open-scholar-peer/mcp/` and creates a Python virtualenv with all dependencies. You don't need to manage it manually.

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

## Getting a Web of Science API key

Requires an institutional/paid Clarivate subscription. Register an application at https://developer.clarivate.com/apis/wos-starter to obtain a key, then set:
```bash
export WOS_API_KEY=...
```
Without it, `search_wos` and `get_wos_paper_details` return `{"error": "..."}`.

## Getting a Scopus API key

Register a free API key at https://dev.elsevier.com/. Full result sets typically also require requests to originate from a subscribing institution's network, or an institutional token:
```bash
export SCOPUS_API_KEY=...
export SCOPUS_INST_TOKEN=...  # optional, for institutional access
```
Without `SCOPUS_API_KEY`, `search_scopus` and `get_scopus_paper_details` return `{"error": "..."}`.

## ACM Digital Library — no key needed

`search_acm`/`get_acm_paper_details` query the free, keyless Crossref REST API scoped to ACM's Crossref member id. Optionally set `CROSSREF_MAILTO` to your email to join Crossref's "polite pool" for steadier rate limits:
```bash
export CROSSREF_MAILTO=you@example.com
```

## Getting a Springer Nature API key

Free at: https://dev.springernature.com/ (sign up, then create a Meta API key). Set it at install time or later via env var:
```bash
export SPRINGER_API_KEY=...
```
Without a key, `search_springer`/`get_springer_paper_details` return an error envelope instead of failing the server.

## Getting an IEEE Xplore API key

Free at: https://developer.ieee.org/ (register, then create a Metadata API key from "My Account"). Set it at install time or later via env var:
```bash
export IEEE_XPLORE_API_KEY=...
```
Without a key, `search_ieee_xplore`/`get_ieee_xplore_paper_details` return an error envelope instead of failing the server.

## Getting an Elsevier (ScienceDirect) API key

Free at: https://dev.elsevier.com/ (register, then create an API key). Set it at install time or later via env var:
```bash
export SCIENCEDIRECT_API_KEY=...
```
Without a key, `search_sciencedirect`/`get_sciencedirect_paper_details` return an error envelope instead of failing the server. Note: without an institutional subscription, abstracts are often unavailable — only bibliographic metadata is guaranteed.

## Extending — adding a new provider

1. Create `providers/<name>.py` with plain Python functions for search/get-detail.
2. Import it at the top of `osp_mcp.py` and add `@mcp.tool()`-decorated wrappers.
3. Document each tool with a rich docstring (the MCP host shows it to the LLM).
4. Add the new dependencies to `requirements.txt`.
5. (Optional) Document API-key env vars in this README.

The framework principle is **dumb tools only** — no agentic logic in the server. Cognitive decisions about *what* to search and *when* to stop belong to the OSP agents in the calling tool.
