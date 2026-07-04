"""medRxiv provider — uses the public Cold Spring Harbor Laboratory API.

No API key required. Quirk: the CSHL API has no keyword-search endpoint — it
only serves a chronological feed (by date range) or a single record lookup
(by DOI). `search()` works around this by paging through the recent-posts
feed and filtering client-side on title/abstract, which means results are
bounded by how far back the scan goes rather than a true relevance search.
See docs/KNOWN_LIMITATIONS.md.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests

BASE_URL = "https://api.biorxiv.org"
SERVER = "medrxiv"
_PAGE_SIZE = 100  # fixed by the API, not configurable
_MAX_PAGES_SCANNED = 20  # cap local filtering work (~2000 records)
_REQUEST_TIMEOUT = 30


def _to_dict(record: dict[str, Any]) -> dict[str, Any]:
    authors = record.get("authors") or ""
    return {
        "doi": record.get("doi"),
        "title": record.get("title"),
        "authors": [a.strip() for a in authors.split(";") if a.strip()],
        "corresponding_author": record.get("author_corresponding"),
        "corresponding_institution": record.get("author_corresponding_institution"),
        "date": record.get("date"),
        "version": record.get("version"),
        "category": record.get("category"),
        "abstract": record.get("abstract"),
        "license": record.get("license"),
        "published_journal_doi": record.get("published"),
        "url": f"https://www.medrxiv.org/content/{record.get('doi')}",
    }


def search(query: str, max_results: int = 10, days_back: int = 365) -> list[dict[str, Any]]:
    """Scan recent medRxiv postings and return those matching `query`.

    Returns list of paper dicts or [{"error": "..."}].
    """
    max_results = max(1, min(int(max_results), 100))
    days_back = max(1, min(int(days_back), 3650))
    terms = [t.lower() for t in query.split() if t.strip()]
    if not terms:
        return [{"error": "search requires a non-empty query"}]

    end = date.today()
    start = end - timedelta(days=days_back)
    interval = f"{start.isoformat()}/{end.isoformat()}"

    matches: list[dict[str, Any]] = []
    cursor = 0
    for _ in range(_MAX_PAGES_SCANNED):
        url = f"{BASE_URL}/details/{SERVER}/{interval}/{cursor}/json"
        try:
            resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            if matches:
                break
            return [{"error": f"medRxiv request failed: {e}"}]

        payload = resp.json()
        collection = payload.get("collection") or []
        if not collection:
            break

        for record in collection:
            haystack = f"{record.get('title', '')} {record.get('abstract', '')}".lower()
            if all(term in haystack for term in terms):
                matches.append(_to_dict(record))
                if len(matches) >= max_results:
                    return matches

        messages = payload.get("messages") or [{}]
        total_count = int(messages[0].get("count", 0) or 0)
        cursor += _PAGE_SIZE
        if cursor >= total_count:
            break

    return matches


def get_details(doi: str) -> dict[str, Any]:
    """Fetch metadata for a specific medRxiv preprint by DOI."""
    doi = doi.strip()
    url = f"{BASE_URL}/details/{SERVER}/{doi}/na/json"
    try:
        resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return {"error": f"medRxiv request failed: {e}"}

    collection = payload.get("collection") or []
    if not collection:
        return {"error": f"No medRxiv preprint found for doi={doi!r}"}
    return _to_dict(collection[0])
