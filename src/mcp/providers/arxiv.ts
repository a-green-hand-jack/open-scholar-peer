// arXiv provider — talks to the public Atom API directly.
//
// The retired Python implementation used the `arxiv` package for its built-in
// pagination and rate-limit delays. Only one page is ever requested here, so
// the delay logic is not needed; the single behaviour worth keeping is the
// over-fetch below, which absorbs date-filter attrition.
import { XMLParser } from "fast-xml-parser";

const API = "https://export.arxiv.org/api/query";
const MAX_RESULTS = 50;

export interface ArxivPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  summary: string;
  published: string | null;
  updated: string | null;
  link: string;
  pdf_url: string;
  primary_category: string;
  categories: string[];
  comment: string;
}

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  isArray: (name) => ["entry", "author", "category", "link"].includes(name),
});

function text(value: unknown): string {
  if (typeof value === "string") return value.trim();
  if (typeof value === "number") return String(value);
  if (value && typeof value === "object" && "#text" in value) {
    return text((value as Record<string, unknown>)["#text"]);
  }
  return "";
}

function isoOrNull(value: unknown): string | null {
  const raw = text(value);
  if (!raw) return null;
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString();
}

// `arxiv.Result.get_short_id()` returns the versioned id ("2501.01234v1"),
// which is what downstream artifacts cite, so strip only the URL prefix.
function shortId(entryId: string): string {
  return entryId.replace(/^https?:\/\/arxiv\.org\/abs\//, "").trim();
}

function toPaper(entry: Record<string, unknown>): ArxivPaper {
  const links = (entry.link as Record<string, unknown>[]) ?? [];
  const pdf = links.find((link) => link["@_title"] === "pdf");
  const categories = (entry.category as Record<string, unknown>[]) ?? [];
  const authors = (entry.author as Record<string, unknown>[]) ?? [];
  const entryId = text(entry.id);
  return {
    arxiv_id: shortId(entryId),
    title: text(entry.title).replace(/\s+/g, " "),
    authors: authors.map((author) => text(author.name)).filter(Boolean),
    summary: text(entry.summary),
    published: isoOrNull(entry.published),
    updated: isoOrNull(entry.updated),
    link: entryId,
    pdf_url: pdf ? String(pdf["@_href"] ?? "") : "",
    primary_category: String(
      (entry["arxiv:primary_category"] as Record<string, unknown>)?.["@_term"] ?? "",
    ),
    categories: categories.map((category) => String(category["@_term"] ?? "")).filter(Boolean),
    comment: text(entry["arxiv:comment"]),
  };
}

async function fetchEntries(params: URLSearchParams, signal?: AbortSignal): Promise<Record<string, unknown>[]> {
  const response = await fetch(`${API}?${params.toString()}`, { signal });
  if (!response.ok) {
    throw new Error(`arXiv API returned HTTP ${response.status}`);
  }
  const feed = parser.parse(await response.text())?.feed;
  return (feed?.entry as Record<string, unknown>[]) ?? [];
}

export async function search(
  query: string,
  maxResults = 10,
  sortBy = "relevance",
  dateFrom?: string,
  dateTo?: string,
  categories?: string[],
  signal?: AbortSignal,
): Promise<ArxivPaper[]> {
  const limit = Math.max(1, Math.min(Math.trunc(maxResults), MAX_RESULTS));
  const fullQuery = categories?.length
    ? `(${query}) (${categories.map((category) => `cat:${category}`).join(" OR ")})`
    : query;

  const params = new URLSearchParams({
    search_query: fullQuery,
    // Over-fetch so date filtering below still returns `limit` records.
    max_results: String(Math.min(limit + 10, MAX_RESULTS)),
    sortBy: sortBy === "relevance" ? "relevance" : "submittedDate",
    sortOrder: "descending",
  });

  const from = dateFrom ? Date.parse(dateFrom) : NaN;
  const to = dateTo ? Date.parse(dateTo) : NaN;
  const results: ArxivPaper[] = [];
  for (const entry of await fetchEntries(params, signal)) {
    if (results.length >= limit) break;
    const paper = toPaper(entry);
    if (paper.published) {
      const published = Date.parse(paper.published);
      if (!Number.isNaN(from) && published < from) continue;
      if (!Number.isNaN(to) && published > to) continue;
    }
    results.push(paper);
  }
  return results;
}

export async function getDetails(arxivId: string, signal?: AbortSignal): Promise<ArxivPaper | { error: string }> {
  const params = new URLSearchParams({ id_list: arxivId.trim() });
  const entries = await fetchEntries(params, signal);
  if (entries.length === 0) {
    return { error: `No paper found for arxiv_id=${JSON.stringify(arxivId)}` };
  }
  return toPaper(entries[0]);
}
