"""ACM Digital Library provider.

The ACM Digital Library has no self-service public search API. Coverage is
instead obtained via the Crossref REST API (https://api.crossref.org), which
is free, keyless, and indexes every DOI ACM deposits (member id 320 — verified
live against https://api.crossref.org/members?query=association+for+computing+machinery).
Results are scoped to ACM-deposited works via `filter=member:320`.

Crossref asks non-key API consumers to identify themselves via a `mailto`
param to join the "polite pool" (higher, steadier rate limits, no auth
required). We default to a generic contact but let users override it via
CROSSREF_MAILTO for their own polite-pool standing.
"""
from __future__ import annotations

import os
import re
from typing import Any

import requests

BASE_URL = "https://api.crossref.org/works"
ACM_MEMBER_ID = 320  # Association for Computing Machinery (ACM)
_JATS_TAG_RE = re.compile(r"<[^>]+>")


def _mailto() -> str:
    return os.environ.get("CROSSREF_MAILTO", "osp-mcp@example.com")


def _clean_abstract(raw: str | None) -> str | None:
    """Crossref abstracts are wrapped in JATS XML (e.g. <jats:p>...</jats:p>)."""
    if not raw:
        return None
    return _JATS_TAG_RE.sub("", raw).strip() or None


def _date_from_parts(field: dict[str, Any] | None) -> str | None:
    if not field:
        return None
    parts = field.get("date-parts")
    if not parts or not parts[0]:
        return None
    return "-".join(str(p).zfill(2) for p in parts[0])


def _to_dict(item: dict[str, Any]) -> dict[str, Any]:
    authors = [
        " ".join(filter(None, [a.get("given"), a.get("family")])).strip()
        for a in (item.get("author") or [])
    ]
    published = (
        _date_from_parts(item.get("published"))
        or _date_from_parts(item.get("published-print"))
        or _date_from_parts(item.get("published-online"))
    )
    return {
        "doi": item.get("DOI"),
        "title": (item.get("title") or [None])[0],
        "authors": [a for a in authors if a],
        "abstract": _clean_abstract(item.get("abstract")),
        "published": published,
        "venue": (item.get("container-title") or [None])[0],
        "type": item.get("type"),
        "publisher": item.get("publisher"),
        "url": item.get("URL"),
        "citationCount": item.get("is-referenced-by-count"),
        "page": item.get("page"),
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search ACM Digital Library-deposited works via Crossref, scoped to ACM."""
    max_results = max(1, min(int(max_results), 100))
    params = {
        "query.bibliographic": query,
        "filter": f"member:{ACM_MEMBER_ID}",
        "rows": max_results,
        "select": "DOI,title,author,abstract,published,published-print,"
        "published-online,container-title,type,publisher,URL,"
        "is-referenced-by-count,page",
        "mailto": _mailto(),
    }
    resp = requests.get(BASE_URL, params=params, timeout=90)
    resp.raise_for_status()
    items = resp.json().get("message", {}).get("items", [])
    return [_to_dict(i) for i in items]


def get_paper_details(doi: str) -> dict[str, Any]:
    """Fetch full Crossref metadata for a single ACM work by DOI."""
    doi = doi.strip().removeprefix("https://doi.org/")
    resp = requests.get(f"{BASE_URL}/{doi}", params={"mailto": _mailto()}, timeout=90)
    if resp.status_code == 404:
        return {"error": f"No ACM/Crossref record found for doi={doi!r}"}
    resp.raise_for_status()
    return _to_dict(resp.json().get("message", {}))
