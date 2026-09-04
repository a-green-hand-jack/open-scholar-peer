// Google Scholar provider — best-effort HTML scraping.
//
// Google Scholar has no public API. This provider is the documented fallback
// used only when a Bohrium LKM search returns an error, so every path here
// degrades to an empty result rather than throwing on a layout change.
import * as cheerio from "cheerio";

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";
const TIMEOUT_MS = 90_000;

export interface ScholarResult {
  title: string;
  authors: string;
  abstract: string;
  url: string;
}

async function get(url: string, signal?: AbortSignal): Promise<string> {
  const response = await fetch(url, { headers: { "User-Agent": UA }, signal: signal ?? AbortSignal.timeout(TIMEOUT_MS) });
  if (!response.ok) {
    // 429 here means Google is throttling the scrape, which the caller reports
    // as an unavailable fallback rather than a retrieval failure.
    throw new Error(`Google Scholar returned HTTP ${response.status}`);
  }
  return response.text();
}

function parseResults(html: string, numResults: number): ScholarResult[] {
  const $ = cheerio.load(html);
  // Google answers a blocked scrape with HTTP 200 and a page that carries the
  // stylesheet but no results container. Returning [] for that is dangerous:
  // the caller cannot tell "nothing matched" from "we were blocked", and a
  // literature round would look complete having retrieved nothing. A genuine
  // empty result set still renders #gs_res_ccl_mid, so its absence is the
  // signal to fail loudly instead.
  if ($("#gs_res_ccl_mid").length === 0) {
    throw new Error("Google Scholar did not return a results page (blocked or rate limited)");
  }
  const out: ScholarResult[] = [];
  $("div.gs_ri").each((_, element) => {
    if (out.length >= numResults) return false;
    const item = $(element);
    const titleTag = item.find("h3.gs_rt").first();
    out.push({
      title: titleTag.text().trim(),
      authors: item.find("div.gs_a").first().text().trim(),
      abstract: item.find("div.gs_rs").first().text().trim(),
      url: titleTag.find("a").first().attr("href") ?? "",
    });
    return undefined;
  });
  return out;
}

export async function search(query: string, numResults = 5, signal?: AbortSignal): Promise<ScholarResult[]> {
  const limit = Math.max(1, Math.min(Math.trunc(numResults), 20));
  const url = `https://scholar.google.com/scholar?q=${encodeURIComponent(query)}`;
  return parseResults(await get(url, signal), limit);
}

export async function searchAdvanced(
  query: string,
  author?: string,
  yearFrom?: number,
  yearTo?: number,
  numResults = 5,
  signal?: AbortSignal,
): Promise<ScholarResult[]> {
  const limit = Math.max(1, Math.min(Math.trunc(numResults), 20));
  const params = new URLSearchParams({ q: query });
  if (author) params.set("as_auth", author);
  if (yearFrom) params.set("as_ylo", String(yearFrom));
  if (yearTo) params.set("as_yhi", String(yearTo));
  const url = `https://scholar.google.com/scholar?${params.toString()}`;
  return parseResults(await get(url, signal), limit);
}

// The retired Python provider used the `scholarly` package for this one call.
// It has no Node equivalent, so the profile pages are scraped directly. Google
// blocks this path more aggressively than keyword search, which is why the
// return value distinguishes "no profile found" from a transport error.
export async function getAuthorInfo(
  authorName: string,
  signal?: AbortSignal,
): Promise<Record<string, unknown> | { error: string }> {
  const searchUrl = `https://scholar.google.com/citations?view_op=search_authors&mauthors=${encodeURIComponent(authorName)}`;
  const $search = cheerio.load(await get(searchUrl, signal));
  const profileHref = $search("h3.gs_ai_name a").first().attr("href");
  if (!profileHref) {
    return { error: `No Google Scholar profile found for ${JSON.stringify(authorName)}` };
  }

  const $profile = cheerio.load(await get(`https://scholar.google.com${profileHref}`, signal));
  const citedBy = Number.parseInt($profile("table#gsc_rsb_st td.gsc_rsb_std").first().text().trim(), 10);

  const publications: { title: string; year: string; citations: number }[] = [];
  $profile("tr.gsc_a_tr").each((_, element) => {
    if (publications.length >= 5) return false;
    const row = $profile(element);
    publications.push({
      title: row.find("a.gsc_a_at").text().trim(),
      year: row.find("span.gsc_a_h").text().trim(),
      citations: Number.parseInt(row.find("a.gsc_a_ac").text().trim(), 10) || 0,
    });
    return undefined;
  });

  return {
    name: $profile("div#gsc_prf_in").text().trim(),
    affiliation: $profile("div.gsc_prf_il").first().text().trim(),
    interests: $profile("a.gsc_prf_inta").map((_, element) => $profile(element).text().trim()).get(),
    citedby: Number.isNaN(citedBy) ? 0 : citedBy,
    publications,
  };
}
