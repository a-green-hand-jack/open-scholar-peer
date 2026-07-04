"""DBLP provider — the open computer-science bibliography.

Uses DBLP's public JSON search API (no API key, no auth, no official rate
limit documented beyond "be reasonable"). Per-publication lookups fall back
to the per-record XML export since DBLP has no JSON endpoint for a single
record by key.

Reference: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
"""
from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

import requests

_SEARCH_URL = "https://dblp.org/search/publ/api"
_RECORD_URL = "https://dblp.org/rec/{key}.xml"
_TIMEOUT_S = 30


def _authors_to_list(authors_field: Any) -> list[str]:
    """Normalize the `info.authors.author` field, which is a dict for a
    single author and a list for multiple authors."""
    if not authors_field:
        return []
    author = authors_field.get("author")
    if author is None:
        return []
    if isinstance(author, list):
        return [a.get("text", "") for a in author]
    return [author.get("text", "")]


def _hit_to_dict(hit: dict[str, Any]) -> dict[str, Any]:
    info = hit.get("info", {})
    return {
        "key": info.get("key"),
        "title": info.get("title"),
        "authors": _authors_to_list(info.get("authors")),
        "year": info.get("year"),
        "venue": info.get("venue"),
        "type": info.get("type"),
        "pages": info.get("pages"),
        "volume": info.get("volume"),
        "doi": info.get("doi"),
        "ee": info.get("ee"),
        "url": info.get("url"),
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search DBLP publications. Returns list of publication dicts or [{"error": "..."}]."""
    max_results = max(1, min(int(max_results), 100))
    try:
        resp = requests.get(
            _SEARCH_URL,
            params={"q": query, "format": "json", "h": max_results},
            timeout=_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"error": f"DBLP search request failed: {e}"}]

    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    return [_hit_to_dict(h) for h in hits]


def get_publication_details(key: str) -> dict[str, Any]:
    """Fetch full metadata for a DBLP publication by its record key
    (e.g. "conf/dac/ZhangYY21" or "journals/corr/abs-2509-16058")."""
    key = key.strip()
    try:
        resp = requests.get(_RECORD_URL.format(key=key), timeout=_TIMEOUT_S)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
    except Exception as e:
        return {"error": f"DBLP record lookup failed for key={key!r}: {e}"}

    record = next(iter(root), None)
    if record is None:
        return {"error": f"No DBLP record found for key={key!r}"}

    return {
        "key": record.get("key", key),
        "type": record.tag,
        "title": (record.findtext("title") or "").rstrip("."),
        "authors": [a.text for a in record.findall("author") if a.text],
        "year": record.findtext("year"),
        "venue": record.findtext("booktitle") or record.findtext("journal"),
        "pages": record.findtext("pages"),
        "volume": record.findtext("volume"),
        "doi": (record.findtext("ee") or "").split("doi.org/")[-1]
        if "doi.org" in (record.findtext("ee") or "")
        else None,
        "ee": record.findtext("ee"),
        "url": f"https://dblp.org/rec/{key}",
    }
