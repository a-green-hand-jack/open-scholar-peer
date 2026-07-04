"""Scopus provider — wraps Elsevier's Scopus Search / Abstract Retrieval APIs.

Requires a SCOPUS_API_KEY (free to register at dev.elsevier.com, but full
results typically require an institutional network/token — see
SCOPUS_INST_TOKEN). If the key is missing, functions return a clean error
envelope instead of raising — mirrors the lazy _get_client() pattern used by
the semantic_scholar provider.
"""
from __future__ import annotations

import os
from typing import Any

import requests

SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
ABSTRACT_URL = "https://api.elsevier.com/content/abstract/doi"
_REQUEST_TIMEOUT = 30


def _get_api_key() -> str | None:
    return os.environ.get("SCOPUS_API_KEY")


def _headers() -> dict[str, str]:
    headers = {"X-ELS-APIKey": _get_api_key() or "", "Accept": "application/json"}
    inst_token = os.environ.get("SCOPUS_INST_TOKEN")
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token
    return headers


def _entry_to_dict(entry: dict[str, Any]) -> dict[str, Any]:
    scopus_link = next(
        (link.get("@href") for link in (entry.get("link") or []) if link.get("@ref") == "scopus"),
        None,
    )
    return {
        "scopus_id": entry.get("dc:identifier"),
        "eid": entry.get("eid"),
        "title": entry.get("dc:title"),
        "creator": entry.get("dc:creator"),
        "doi": entry.get("prism:doi"),
        "publication_name": entry.get("prism:publicationName"),
        "cover_date": entry.get("prism:coverDate"),
        "cited_by_count": entry.get("citedby-count"),
        "aggregation_type": entry.get("prism:aggregationType"),
        "url": scopus_link,
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search Scopus. Returns [{"error": "..."}] if SCOPUS_API_KEY is unset
    or the request fails."""
    api_key = _get_api_key()
    if not api_key:
        return [{"error": "SCOPUS_API_KEY is not set — Scopus requires an Elsevier Developer API key."}]

    max_results = max(1, min(int(max_results), 100))
    params = {"query": query, "count": max_results}
    try:
        resp = requests.get(SEARCH_URL, headers=_headers(), params=params, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return [{"error": f"Scopus request failed: {e}"}]

    entries = (payload.get("search-results") or {}).get("entry") or []
    return [_entry_to_dict(e) for e in entries if "dc:title" in e]


def get_details(doi: str) -> dict[str, Any]:
    """Fetch a Scopus abstract record by DOI. Returns {"error": "..."} if
    SCOPUS_API_KEY is unset, the DOI isn't found, or the request fails."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "SCOPUS_API_KEY is not set — Scopus requires an Elsevier Developer API key."}

    url = f"{ABSTRACT_URL}/{doi.strip()}"
    try:
        resp = requests.get(url, headers=_headers(), params={"view": "META_ABS"}, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return {"error": f"Scopus request failed: {e}"}

    coredata = (payload.get("abstracts-retrieval-response") or {}).get("coredata") or {}
    if not coredata:
        return {"error": f"No Scopus record found for doi={doi!r}"}
    return {
        "scopus_id": coredata.get("dc:identifier"),
        "title": coredata.get("dc:title"),
        "abstract": coredata.get("dc:description"),
        "creator": coredata.get("dc:creator"),
        "doi": coredata.get("prism:doi"),
        "publication_name": coredata.get("prism:publicationName"),
        "cover_date": coredata.get("prism:coverDate"),
        "cited_by_count": coredata.get("citedby-count"),
        "aggregation_type": coredata.get("prism:aggregationType"),
    }
