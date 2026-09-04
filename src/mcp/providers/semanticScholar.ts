// Semantic Scholar provider — talks to the public Graph API directly.
//
// The retired Python implementation wrapped the `semanticscholar` client, which
// chose its own default field sets. The REST API returns only `paperId` unless
// `fields` is given, so every request below names its fields explicitly to keep
// the emitted records identical to the ones downstream artifacts already cite.
const GRAPH = "https://api.semanticscholar.org/graph/v1";
const RECOMMENDATIONS = "https://api.semanticscholar.org/recommendations/v1";

const PAPER_FIELDS =
  "paperId,title,abstract,year,authors,url,venue,publicationTypes,citationCount,externalIds";
const SLIM_FIELDS = "paperId,title,year,citationCount,authors";
const AUTHOR_FIELDS = "authorId,name,url,affiliations,paperCount,citationCount,hIndex";

type Json = Record<string, unknown>;

export interface Paper {
  paperId: string | null;
  title: string | null;
  abstract: string | null;
  year: number | null;
  authors: { name: string | null; authorId: string | null }[];
  url: string | null;
  venue: string | null;
  publicationTypes: string[] | null;
  citationCount: number | null;
  externalIds: Json | null;
}

export interface SlimPaper {
  paperId: string | null;
  title: string | null;
  year: number | null;
  citationCount: number | null;
  authors: { name: string | null; authorId: string | null }[];
}

function clamp(value: number, max: number): number {
  return Math.max(1, Math.min(Math.trunc(value), max));
}

function asAuthors(value: unknown): { name: string | null; authorId: string | null }[] {
  if (!Array.isArray(value)) return [];
  return value.map((author) => ({
    name: (author as Json)?.name as string ?? null,
    authorId: (author as Json)?.authorId as string ?? null,
  }));
}

function toPaper(value: Json | null | undefined): Paper {
  const paper = value ?? {};
  return {
    paperId: (paper.paperId as string) ?? null,
    title: (paper.title as string) ?? null,
    abstract: (paper.abstract as string) ?? null,
    year: (paper.year as number) ?? null,
    authors: asAuthors(paper.authors),
    url: (paper.url as string) ?? null,
    venue: (paper.venue as string) ?? null,
    publicationTypes: (paper.publicationTypes as string[]) ?? null,
    citationCount: (paper.citationCount as number) ?? null,
    externalIds: (paper.externalIds as Json) ?? null,
  };
}

function toSlim(value: Json | null | undefined): SlimPaper {
  const paper = value ?? {};
  return {
    paperId: (paper.paperId as string) ?? null,
    title: (paper.title as string) ?? null,
    year: (paper.year as number) ?? null,
    citationCount: (paper.citationCount as number) ?? null,
    authors: asAuthors(paper.authors),
  };
}

function headers(): Record<string, string> {
  // The key only raises the rate limit; anonymous access stays supported.
  const key = process.env.SEMANTIC_SCHOLAR_API_KEY;
  return key ? { "x-api-key": key } : {};
}

async function request(url: string, signal?: AbortSignal, init?: RequestInit): Promise<Json> {
  const response = await fetch(url, { ...init, signal, headers: { ...headers(), ...(init?.headers ?? {}) } });
  if (!response.ok) {
    // 429 is the common case and the message is what the agent sees, so name it.
    throw new Error(
      response.status === 429
        ? "Semantic Scholar rate limit reached; set SEMANTIC_SCHOLAR_API_KEY or retry later"
        : `Semantic Scholar returned HTTP ${response.status}`,
    );
  }
  return (await response.json()) as Json;
}

export async function searchPapers(query: string, limit = 10, signal?: AbortSignal): Promise<Paper[]> {
  const params = new URLSearchParams({ query, limit: String(clamp(limit, 100)), fields: PAPER_FIELDS });
  const payload = await request(`${GRAPH}/paper/search?${params}`, signal);
  return ((payload.data as Json[]) ?? []).map(toPaper);
}

export async function getPaper(paperId: string, signal?: AbortSignal): Promise<Paper> {
  const params = new URLSearchParams({ fields: PAPER_FIELDS });
  return toPaper(await request(`${GRAPH}/paper/${encodeURIComponent(paperId)}?${params}`, signal));
}

export async function getPaperReferences(paperId: string, limit = 50, signal?: AbortSignal): Promise<SlimPaper[]> {
  const params = new URLSearchParams({ limit: String(clamp(limit, 100)), fields: SLIM_FIELDS });
  const payload = await request(`${GRAPH}/paper/${encodeURIComponent(paperId)}/references?${params}`, signal);
  return ((payload.data as Json[]) ?? [])
    .map((row) => row.citedPaper as Json)
    .filter(Boolean)
    .map(toSlim);
}

export async function getPaperCitations(paperId: string, limit = 50, signal?: AbortSignal): Promise<SlimPaper[]> {
  const params = new URLSearchParams({ limit: String(clamp(limit, 100)), fields: SLIM_FIELDS });
  const payload = await request(`${GRAPH}/paper/${encodeURIComponent(paperId)}/citations?${params}`, signal);
  return ((payload.data as Json[]) ?? [])
    .map((row) => row.citingPaper as Json)
    .filter(Boolean)
    .map(toSlim);
}

export async function getPapersBatch(paperIds: string[], signal?: AbortSignal): Promise<Paper[]> {
  if (paperIds.length === 0) return [];
  const params = new URLSearchParams({ fields: PAPER_FIELDS });
  const response = await fetch(`${GRAPH}/paper/batch?${params}`, {
    method: "POST",
    signal,
    headers: { ...headers(), "content-type": "application/json" },
    body: JSON.stringify({ ids: paperIds.slice(0, 500) }),
  });
  if (!response.ok) throw new Error(`Semantic Scholar returned HTTP ${response.status}`);
  const payload = (await response.json()) as (Json | null)[];
  return payload.filter(Boolean).map((paper) => toPaper(paper));
}

export async function getAuthor(authorId: string, signal?: AbortSignal): Promise<Json> {
  const params = new URLSearchParams({ fields: AUTHOR_FIELDS });
  const author = await request(`${GRAPH}/author/${encodeURIComponent(authorId)}?${params}`, signal);
  return toAuthor(author);
}

function toAuthor(value: Json | null | undefined): Json {
  const author = value ?? {};
  return {
    authorId: author.authorId ?? null,
    name: author.name ?? null,
    url: author.url ?? null,
    affiliations: author.affiliations ?? null,
    paperCount: author.paperCount ?? null,
    citationCount: author.citationCount ?? null,
    hIndex: author.hIndex ?? null,
  };
}

export async function searchAuthors(query: string, limit = 10, signal?: AbortSignal): Promise<Json[]> {
  const params = new URLSearchParams({ query, limit: String(clamp(limit, 100)), fields: AUTHOR_FIELDS });
  const payload = await request(`${GRAPH}/author/search?${params}`, signal);
  return ((payload.data as Json[]) ?? []).map(toAuthor);
}

export async function getAuthorPapers(authorId: string, limit = 50, signal?: AbortSignal): Promise<SlimPaper[]> {
  const params = new URLSearchParams({ limit: String(clamp(limit, 100)), fields: SLIM_FIELDS });
  const payload = await request(`${GRAPH}/author/${encodeURIComponent(authorId)}/papers?${params}`, signal);
  return ((payload.data as Json[]) ?? []).map(toSlim);
}

export async function getPaperRecommendations(paperId: string, limit = 10, signal?: AbortSignal): Promise<SlimPaper[]> {
  const params = new URLSearchParams({ limit: String(clamp(limit, 100)), fields: SLIM_FIELDS });
  const payload = await request(
    `${RECOMMENDATIONS}/papers/forpaper/${encodeURIComponent(paperId)}?${params}`,
    signal,
  );
  return ((payload.recommendedPapers as Json[]) ?? []).map(toSlim);
}

export async function searchSnippets(query: string, limit = 10, signal?: AbortSignal): Promise<Json[]> {
  const params = new URLSearchParams({ query, limit: String(clamp(limit, 20)) });
  const payload = await request(`${GRAPH}/snippet/search?${params}`, signal);
  return ((payload.data as Json[]) ?? []).map((row) => {
    const snippet = (row.snippet as Json) ?? {};
    const paper = row.paper as Json | undefined;
    return {
      snippetId: snippet.snippetId ?? null,
      text: snippet.text ?? null,
      paper: paper ? toSlim(paper) : null,
    };
  });
}
