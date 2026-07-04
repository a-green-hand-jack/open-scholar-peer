"""Elsevier ScienceDirect provider.

Wraps two Elsevier APIs (api.elsevier.com), verified against the official
pybliometrics client source (github.com/pybliometrics-dev/pybliometrics):
  - ScienceDirect Search API V2 (GET /content/search/sciencedirect/) for
    keyword search — response envelope: {"search-results": {"entry": [...]}}.
  - Article Retrieval API (GET /content/article/{id_type}/{id}) for a single
    record by DOI/PII/EID — response envelope:
    {"full-text-retrieval-response": {"coredata": {...}}}.

Auth: X-ELS-APIKey header. Free key + weekly quota: https://dev.elsevier.com/
Metadata/abstract depth depends on your institution's entitlements — without
a subscription, expect bibliographic metadata (title/authors/DOI/venue) and
often no abstract.
"""
from __future__ import annotations

import os
from typing import Any

import requests

SEARCH_URL = "https://api.elsevier.com/content/search/sciencedirect/"
RETRIEVAL_BASE = "https://api.elsevier.com/content/article/"


def _get_api_key() -> str | None:
    return os.environ.get("SCIENCEDIRECT_API_KEY")


def _missing_key_error() -> str:
    return (
        "SCIENCEDIRECT_API_KEY is not set. Get a free key at "
        "https://dev.elsevier.com/ and add it to your .env."
    )


def _headers(api_key: str) -> dict[str, str]:
    return {"Accept": "application/json", "X-ELS-APIKey": api_key}


def _detect_id_type(identifier: str) -> str:
    """Same heuristic Elsevier client libraries use to route DOI/PII/EID."""
    if identifier.startswith("1-s2.0-") or identifier.startswith("2-s2.0-"):
        return "eid"
    if "/" in identifier or "." in identifier:
        return "doi"
    return "pii"


def _authors_from_search_entry(entry: dict[str, Any]) -> list[str]:
    authors_field = (entry.get("authors") or {}).get("author")
    if isinstance(authors_field, list):
        return [a.get("$") for a in authors_field if isinstance(a, dict) and a.get("$")]
    if isinstance(authors_field, dict) and authors_field.get("$"):
        return [authors_field["$"]]
    return []


def _doi_from_search_entry(entry: dict[str, Any]) -> str | None:
    if entry.get("prism:doi"):
        return entry["prism:doi"]
    identifier = entry.get("dc:identifier") or ""
    return identifier[4:] if identifier.lower().startswith("doi:") else None


def _scidir_link(entry: dict[str, Any]) -> str | None:
    for link in entry.get("link") or []:
        if link.get("@ref") == "scidir":
            return link.get("@href")
    return None


def _entry_to_dict(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "doi": _doi_from_search_entry(entry),
        "pii": entry.get("pii"),
        "title": entry.get("dc:title"),
        "authors": _authors_from_search_entry(entry),
        "publicationName": entry.get("prism:publicationName"),
        "coverDate": entry.get("prism:coverDate"),
        "startingPage": entry.get("prism:startingPage"),
        "endingPage": entry.get("prism:endingPage"),
        "volume": entry.get("prism:volume"),
        "openaccess": entry.get("openaccess"),
        "url": _scidir_link(entry),
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search ScienceDirect metadata via the Elsevier Search API V2."""
    api_key = _get_api_key()
    if not api_key:
        return [{"error": _missing_key_error()}]
    max_results = max(1, min(int(max_results), 100))  # STANDARD view cap
    params = {"query": query, "count": max_results, "start": 0, "view": "STANDARD"}
    resp = requests.get(SEARCH_URL, headers=_headers(api_key), params=params, timeout=90)
    if resp.status_code in (401, 403):
        return [{"error": f"ScienceDirect rejected the key ({resp.status_code}) — check SCIENCEDIRECT_API_KEY."}]
    resp.raise_for_status()
    entries = resp.json().get("search-results", {}).get("entry", [])
    return [_entry_to_dict(e) for e in entries]


def get_paper_details(identifier: str) -> dict[str, Any]:
    """Fetch full metadata (+ abstract, if entitled) for one article by DOI/PII/EID."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": _missing_key_error()}
    identifier = identifier.strip().removeprefix("https://doi.org/")
    id_type = _detect_id_type(identifier)
    url = f"{RETRIEVAL_BASE}{id_type}/{identifier}"
    resp = requests.get(url, headers=_headers(api_key), params={"view": "META_ABS"}, timeout=90)
    if resp.status_code in (401, 403):
        return {"error": f"ScienceDirect rejected the key ({resp.status_code}) — check SCIENCEDIRECT_API_KEY."}
    if resp.status_code == 404:
        return {"error": f"No ScienceDirect record found for {id_type}={identifier!r}"}
    resp.raise_for_status()
    coredata = resp.json().get("full-text-retrieval-response", {}).get("coredata", {})
    if not coredata:
        return {"error": f"No ScienceDirect record found for {id_type}={identifier!r}"}
    creators = coredata.get("dc:creator") or []
    authors = [c.get("$") for c in creators if isinstance(c, dict) and c.get("$")]
    return {
        "doi": coredata.get("prism:doi"),
        "eid": coredata.get("eid"),
        "pii": coredata.get("pii"),
        "title": coredata.get("dc:title"),
        "authors": authors,
        "abstract": coredata.get("dc:description"),
        "publicationName": coredata.get("prism:publicationName"),
        "coverDate": coredata.get("prism:coverDate"),
        "aggregationType": coredata.get("prism:aggregationType"),
        "volume": coredata.get("prism:volume"),
        "startingPage": coredata.get("prism:startingPage"),
        "endingPage": coredata.get("prism:endingPage"),
        "openaccess": coredata.get("openaccess"),
    }
