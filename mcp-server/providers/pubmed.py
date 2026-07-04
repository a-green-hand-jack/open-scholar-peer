"""PubMed provider — uses the NCBI E-utilities REST API (ESearch + EFetch).

No API key is required for casual use (NCBI caps unauthenticated traffic at
3 requests/sec, which is more than sufficient for this tool's call pattern).

Reference: https://www.ncbi.nlm.nih.gov/books/NBK25497/
"""
from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

import requests

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TIMEOUT_S = 30


def _article_to_dict(article: ElementTree.Element) -> dict[str, Any]:
    pmid = article.findtext(".//PMID")
    title = article.findtext(".//ArticleTitle") or ""
    journal = article.findtext(".//Journal/Title")
    pub_date_el = article.find(".//JournalIssue/PubDate")
    year = pub_date_el.findtext("Year") if pub_date_el is not None else None

    authors: list[str] = []
    for author_el in article.findall(".//AuthorList/Author"):
        collective = author_el.findtext("CollectiveName")
        if collective:
            authors.append(collective)
            continue
        fore = author_el.findtext("ForeName") or ""
        last = author_el.findtext("LastName") or ""
        name = f"{fore} {last}".strip()
        if name:
            authors.append(name)

    doi = None
    for eloc in article.findall(".//ELocationID"):
        if eloc.get("EIdType") == "doi":
            doi = eloc.text

    abstract = " ".join(
        (t.text or "") for t in article.findall(".//Abstract/AbstractText")
    ).strip()

    return {
        "pmid": pmid,
        "title": title.rstrip("."),
        "authors": authors,
        "abstract": abstract,
        "journal": journal,
        "year": year,
        "doi": doi,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
    }


def _fetch_articles(pmids: list[str]) -> list[dict[str, Any]]:
    if not pmids:
        return []
    resp = requests.get(
        _EFETCH_URL,
        params={"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"},
        timeout=_TIMEOUT_S,
    )
    resp.raise_for_status()
    root = ElementTree.fromstring(resp.content)
    return [_article_to_dict(a) for a in root.findall(".//PubmedArticle")]


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search PubMed for biomedical/life-science literature. Returns list of
    article dicts or [{"error": "..."}]."""
    max_results = max(1, min(int(max_results), 100))
    try:
        esearch_resp = requests.get(
            _ESEARCH_URL,
            params={"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results},
            timeout=_TIMEOUT_S,
        )
        esearch_resp.raise_for_status()
        pmids = esearch_resp.json().get("esearchresult", {}).get("idlist", [])
        return _fetch_articles(pmids)
    except Exception as e:
        return [{"error": f"PubMed search failed: {e}"}]


def get_details(pmid: str) -> dict[str, Any]:
    """Fetch full metadata (including abstract) for a specific PubMed article by PMID."""
    pmid = str(pmid).strip()
    try:
        articles = _fetch_articles([pmid])
    except Exception as e:
        return {"error": f"PubMed lookup failed for pmid={pmid!r}: {e}"}
    if not articles:
        return {"error": f"No PubMed article found for pmid={pmid!r}"}
    return articles[0]
