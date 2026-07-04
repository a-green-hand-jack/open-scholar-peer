"""IEEE Xplore provider.

Wraps the IEEE Xplore Metadata API (search/articles endpoint) — metadata and
abstracts for journals, conference proceedings, books, courses, and standards.

Base URL: https://ieeexploreapi.ieee.org/api/v1/search/articles
Auth: `apikey` query param. Free key (with a request quota): https://developer.ieee.org/

Reads the required IEEE_XPLORE_API_KEY env var. Like Springer, IEEE has no
anonymous tier, so a missing key returns a clean error envelope.
"""
from __future__ import annotations

import os
from typing import Any

import requests

BASE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


def _get_api_key() -> str | None:
    return os.environ.get("IEEE_XPLORE_API_KEY")


def _missing_key_error() -> str:
    return (
        "IEEE_XPLORE_API_KEY is not set. Get a free key at "
        "https://developer.ieee.org/ and add it to your .env."
    )


def _to_dict(article: dict[str, Any]) -> dict[str, Any]:
    authors = [
        a.get("full_name") for a in (article.get("authors", {}).get("authors") or [])
    ]
    return {
        "articleNumber": article.get("article_number"),
        "doi": article.get("doi"),
        "title": article.get("title"),
        "authors": [a for a in authors if a],
        "abstract": article.get("abstract"),
        "publicationTitle": article.get("publication_title"),
        "publicationYear": article.get("publication_year"),
        "publicationDate": article.get("publication_date"),
        "contentType": article.get("content_type"),
        "publisher": article.get("publisher"),
        "volume": article.get("volume"),
        "issue": article.get("issue"),
        "startPage": article.get("start_page"),
        "endPage": article.get("end_page"),
        "citingPaperCount": article.get("citing_paper_count"),
        "htmlUrl": article.get("html_url"),
        "pdfUrl": article.get("pdf_url"),
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search IEEE Xplore metadata for articles, conference papers, and standards."""
    api_key = _get_api_key()
    if not api_key:
        return [{"error": _missing_key_error()}]
    max_results = max(1, min(int(max_results), 200))  # IEEE's own documented cap
    params = {
        "apikey": api_key,
        "format": "json",
        "querytext": query,
        "max_records": max_results,
        "start_record": 1,
    }
    resp = requests.get(BASE_URL, params=params, timeout=90)
    if resp.status_code in (401, 403):
        return [{"error": f"IEEE Xplore rejected the key ({resp.status_code}) — check IEEE_XPLORE_API_KEY."}]
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    return [_to_dict(a) for a in articles]


def get_details(article_number_or_doi: str) -> dict[str, Any]:
    """Fetch a single IEEE Xplore record by article number or DOI."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": _missing_key_error()}
    identifier = article_number_or_doi.strip()
    param_name = "doi" if "/" in identifier else "article_number"
    params = {"apikey": api_key, "format": "json", param_name: identifier}
    resp = requests.get(BASE_URL, params=params, timeout=90)
    if resp.status_code in (401, 403):
        return {"error": f"IEEE Xplore rejected the key ({resp.status_code}) — check IEEE_XPLORE_API_KEY."}
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    if not articles:
        return {"error": f"No IEEE Xplore record found for {param_name}={identifier!r}"}
    return _to_dict(articles[0])
