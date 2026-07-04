"""Web of Science provider — wraps Clarivate's Web of Science Starter API.

Requires a WOS_API_KEY (a paid/institutional Clarivate subscription). If the
key is missing, functions return a clean error envelope instead of raising —
mirrors the lazy _get_client() pattern used by the semantic_scholar provider.
"""
from __future__ import annotations

import os
from typing import Any

import requests

BASE_URL = "https://api.clarivate.com/apis/wos-starter/v1"
_REQUEST_TIMEOUT = 30


def _get_api_key() -> str | None:
    return os.environ.get("WOS_API_KEY")


def _headers() -> dict[str, str]:
    return {"X-ApiKey": _get_api_key() or ""}


def _to_dict(hit: dict[str, Any]) -> dict[str, Any]:
    identifiers = hit.get("identifiers") or {}
    source = hit.get("source") or {}
    citations = hit.get("citations") or []
    names = (hit.get("names") or {}).get("authors") or []
    return {
        "uid": hit.get("uid"),
        "title": hit.get("title"),
        "authors": [a.get("displayName") for a in names if a.get("displayName")],
        "doi": identifiers.get("doi"),
        "source_title": source.get("sourceTitle"),
        "publish_year": source.get("publishYear"),
        "times_cited": (citations[0].get("count") if citations else None),
        "document_type": hit.get("types"),
        "url": hit.get("links", {}).get("record") if isinstance(hit.get("links"), dict) else None,
    }


def search(query: str, max_results: int = 10, database: str = "WOS") -> list[dict[str, Any]]:
    """Search Web of Science Core Collection. Returns [{"error": "..."}] if
    WOS_API_KEY is unset or the request fails."""
    api_key = _get_api_key()
    if not api_key:
        return [{"error": "WOS_API_KEY is not set — Web of Science requires a Clarivate subscription key."}]

    max_results = max(1, min(int(max_results), 50))
    params = {"db": database, "q": query, "limit": max_results, "page": 1}
    try:
        resp = requests.get(f"{BASE_URL}/documents", headers=_headers(), params=params, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return [{"error": f"Web of Science request failed: {e}"}]

    hits = payload.get("hits") or []
    return [_to_dict(h) for h in hits]


def get_details(doi: str, database: str = "WOS") -> dict[str, Any]:
    """Fetch a Web of Science record by DOI. Returns {"error": "..."} if
    WOS_API_KEY is unset, the DOI isn't found, or the request fails."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "WOS_API_KEY is not set — Web of Science requires a Clarivate subscription key."}

    params = {"db": database, "q": f"DO={doi.strip()}", "limit": 1, "page": 1}
    try:
        resp = requests.get(f"{BASE_URL}/documents", headers=_headers(), params=params, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return {"error": f"Web of Science request failed: {e}"}

    hits = payload.get("hits") or []
    if not hits:
        return {"error": f"No Web of Science record found for doi={doi!r}"}
    return _to_dict(hits[0])
