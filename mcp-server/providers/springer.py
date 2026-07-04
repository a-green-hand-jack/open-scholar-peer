"""Springer Nature provider.

Wraps the Springer Nature Meta API v2 (JSON) — metadata + abstracts for
articles, book chapters, and books across Springer's catalog. No full text.

Base URL: https://api.springernature.com/meta/v2/json
Auth: `api_key` query param. Free key: https://dev.springernature.com/

Reads the required SPRINGER_API_KEY env var. Mirrors semantic_scholar.py's
lazy-key pattern, but Springer has no anonymous tier — a missing key returns
a clean error envelope instead of raising.
"""
from __future__ import annotations

import os
from typing import Any

import requests

BASE_URL = "https://api.springernature.com/meta/v2/json"


def _get_api_key() -> str | None:
    return os.environ.get("SPRINGER_API_KEY")


def _missing_key_error() -> str:
    return (
        "SPRINGER_API_KEY is not set. Get a free key at "
        "https://dev.springernature.com/ and add it to your .env."
    )


def _reverse_name(raw: str) -> str:
    """Springer creator names arrive as "Last, First" — flip to "First Last"."""
    if "," not in raw:
        return raw
    last, _, first = raw.partition(",")
    return f"{first.strip()} {last.strip()}".strip()


def _best_url(urls: list[dict[str, Any]]) -> str | None:
    html = next((u.get("value") for u in urls if u.get("format") == "html"), None)
    pdf = next((u.get("value") for u in urls if u.get("format") == "pdf"), None)
    return html or pdf or (urls[0].get("value") if urls else None)


def _to_dict(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "doi": record.get("doi"),
        "title": record.get("title"),
        "authors": [
            _reverse_name(c.get("creator", "")) for c in (record.get("creators") or [])
        ],
        "abstract": record.get("abstract"),
        "publicationName": record.get("publicationName"),
        "publicationDate": record.get("publicationDate"),
        "contentType": record.get("contentType"),
        "publisher": record.get("publisher"),
        "issn": record.get("issn"),
        "isbn": record.get("isbn"),
        "volume": record.get("volume"),
        "startingPage": record.get("startingPage"),
        "endingPage": record.get("endingPage"),
        "openaccess": record.get("openaccess"),
        "url": _best_url(record.get("url") or []),
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search the Springer Nature Meta API for articles, chapters, and books."""
    api_key = _get_api_key()
    if not api_key:
        return [{"error": _missing_key_error()}]
    max_results = max(1, min(int(max_results), 100))
    params = {"api_key": api_key, "q": query, "p": max_results, "s": 1}
    resp = requests.get(BASE_URL, params=params, timeout=90)
    if resp.status_code == 401:
        return [{"error": "Springer API rejected the key (401) — check SPRINGER_API_KEY."}]
    resp.raise_for_status()
    records = resp.json().get("records", [])
    return [_to_dict(r) for r in records]


def get_paper_details(doi: str) -> dict[str, Any]:
    """Fetch a single Springer record by DOI."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": _missing_key_error()}
    doi = doi.strip().removeprefix("https://doi.org/")
    params = {"api_key": api_key, "q": f"doi:{doi}", "p": 1, "s": 1}
    resp = requests.get(BASE_URL, params=params, timeout=90)
    if resp.status_code == 401:
        return {"error": "Springer API rejected the key (401) — check SPRINGER_API_KEY."}
    resp.raise_for_status()
    records = resp.json().get("records", [])
    if not records:
        return {"error": f"No Springer record found for doi={doi!r}"}
    return _to_dict(records[0])
