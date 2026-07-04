"""bioRxiv provider.

bioRxiv's own API (api.biorxiv.org) has no keyword/full-text search endpoint —
only DOI lookup and date-range browsing (confirmed against the documented
endpoint list at https://api.biorxiv.org/). To support keyword search we use
Europe PMC's public search API (https://europepmc.org/RestfulWebService),
filtered to preprints published on the bioRxiv server, which yields the DOI.
That DOI is then resolved against the *official* bioRxiv details endpoint to
fetch the canonical abstract/metadata record — so search discovery goes
through Europe PMC, but all returned metadata is bioRxiv's own.

No API key is required for either service.
"""
from __future__ import annotations

from typing import Any

import requests

_EUROPEPMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_BIORXIV_DETAILS_URL = "https://api.biorxiv.org/details/biorxiv/{doi}/na/json"
_TIMEOUT_S = 30


def _latest_version(collection: list[dict[str, Any]]) -> dict[str, Any]:
    """bioRxiv details returns one entry per revision; keep the newest."""
    return max(collection, key=lambda c: int(c.get("version", 0) or 0))


def _record_to_dict(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "doi": record.get("doi"),
        "title": record.get("title"),
        "authors": [a.strip() for a in (record.get("authors") or "").split(";") if a.strip()],
        "abstract": record.get("abstract"),
        "date": record.get("date"),
        "version": record.get("version"),
        "category": record.get("category"),
        "license": record.get("license"),
        "published": record.get("published"),
        "url": f"https://www.biorxiv.org/content/{record['doi']}" if record.get("doi") else None,
    }


def get_details(doi: str) -> dict[str, Any]:
    """Fetch canonical bioRxiv metadata for a preprint by DOI (e.g. "10.1101/2025.01.22.634394")."""
    doi = doi.strip()
    try:
        resp = requests.get(_BIORXIV_DETAILS_URL.format(doi=doi), timeout=_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"bioRxiv details lookup failed for doi={doi!r}: {e}"}

    collection = data.get("collection") or []
    if not collection:
        status = data.get("messages", [{}])[0].get("status", "not found")
        return {"error": f"No bioRxiv record for doi={doi!r} ({status})"}
    return _record_to_dict(_latest_version(collection))


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search bioRxiv preprints by keyword via Europe PMC (see module docstring
    for why), then resolve each hit to its canonical bioRxiv record.

    Returns list of preprint dicts or [{"error": "..."}]."""
    max_results = max(1, min(int(max_results), 100))
    try:
        resp = requests.get(
            _EUROPEPMC_SEARCH_URL,
            params={
                "query": f'{query} AND SRC:PPR AND PUBLISHER:"bioRxiv"',
                "format": "json",
                "pageSize": max_results,
            },
            timeout=_TIMEOUT_S,
        )
        resp.raise_for_status()
        hits = resp.json().get("resultList", {}).get("result", [])
    except Exception as e:
        return [{"error": f"bioRxiv search failed: {e}"}]

    results: list[dict[str, Any]] = []
    for hit in hits:
        doi = hit.get("doi")
        if not doi:
            continue
        detail = get_details(doi)
        if "error" not in detail:
            results.append(detail)
    return results
