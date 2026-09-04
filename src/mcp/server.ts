#!/usr/bin/env node
// osp_mcp — Open ScholarPeer consolidated MCP server.
//
// Exposes academic-search tools across four providers:
//   • arXiv            — pre-prints, no API key needed
//   • Semantic Scholar — citation graph, abstracts; API key raises rate limits
//   • Bohrium LKM      — primary broad-coverage source, via the `bohr` CLI
//   • Google Scholar   — best-effort fallback used only when LKM errors
//
// Design principles carried over from the retired Python server:
//   1. Dumb tools only — each tool is atomic and stateless.
//   2. Rich descriptions — agents read them to pick a tool (see descriptions.ts).
//   3. Consistent error envelope — search-style tools return [{"error": ...}],
//      single-record tools return {"error": ...}. A tool never throws.
//   4. Per-call timeout — a hanging provider cannot block the server.
//
// Environment:
//   SEMANTIC_SCHOLAR_API_KEY — optional, higher rate limits
//   OSP_CALL_TIMEOUT         — per-call timeout in seconds (default 90)
//   OSP_ALLOW_LKM_SPEND      — "1" authorizes billable Bohrium calls
//   OSP_WORKSPACE_ROOT       — run directory; bounds LKM PDF extraction
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { DESCRIPTIONS } from "./descriptions.js";
import * as arxiv from "./providers/arxiv.js";
import * as bohrium from "./providers/bohrium.js";
import * as googleScholar from "./providers/googleScholar.js";
import * as semanticScholar from "./providers/semanticScholar.js";

const TIMEOUT_MS = Number.parseInt(process.env.OSP_CALL_TIMEOUT ?? "90", 10) * 1000;

// stdout carries the MCP protocol, so diagnostics must go to stderr only.
function log(message: string): void {
  process.stderr.write(`${new Date().toISOString()} - osp_mcp - ${message}\n`);
}

type Result = { content: { type: "text"; text: string }[] };

function reply(value: unknown): Result {
  return { content: [{ type: "text", text: JSON.stringify(value) }] };
}

/**
 * Run a provider call under the shared timeout and error envelope.
 *
 * `style` decides the failure shape so a caller that always iterates a list
 * never has to special-case an error object, matching the Python contract.
 */
async function guard(
  tool: string,
  style: "list" | "object",
  run: (signal: AbortSignal) => Promise<unknown>,
): Promise<Result> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return reply(await run(controller.signal));
  } catch (error) {
    const reason = controller.signal.aborted
      ? `timed out after ${TIMEOUT_MS / 1000}s`
      : (error as Error).message;
    const envelope = { error: `${tool} failed: ${reason}` };
    log(`${tool} failed: ${reason}`);
    return reply(style === "list" ? [envelope] : envelope);
  } finally {
    clearTimeout(timer);
  }
}

const server = new McpServer({ name: "osp_mcp", version: "2.2.0" });

function register(
  name: string,
  inputSchema: z.ZodRawShape,
  style: "list" | "object",
  run: (args: Record<string, never>, signal: AbortSignal) => Promise<unknown>,
): void {
  server.registerTool(
    name,
    { description: DESCRIPTIONS[name], inputSchema },
    // The SDK types the handler against the schema; the providers take plain
    // values, so the cast is confined to this one adapter.
    (async (args: Record<string, never>) =>
      guard(name, style, (signal) => run(args, signal))) as never,
  );
}

// ---------- arXiv ----------------------------------------------------------

register(
  "search_arxiv",
  {
    query: z.string(),
    max_results: z.number().int().optional().default(10),
    sort_by: z.string().optional().default("relevance"),
    date_from: z.string().nullable().optional(),
    date_to: z.string().nullable().optional(),
    categories: z.array(z.string()).nullable().optional(),
  },
  "list",
  (a, signal) =>
    arxiv.search(a.query, a.max_results, a.sort_by, a.date_from ?? undefined, a.date_to ?? undefined, a.categories ?? undefined, signal),
);

register("get_arxiv_paper_details", { arxiv_id: z.string() }, "object", (a, signal) =>
  arxiv.getDetails(a.arxiv_id, signal),
);

// ---------- Semantic Scholar -----------------------------------------------

register(
  "search_semantic_scholar",
  { query: z.string(), limit: z.number().int().optional().default(10) },
  "list",
  (a, signal) => semanticScholar.searchPapers(a.query, a.limit, signal),
);

register("get_semantic_scholar_paper", { paper_id: z.string() }, "object", (a, signal) =>
  semanticScholar.getPaper(a.paper_id, signal),
);

register(
  "get_semantic_scholar_paper_references",
  { paper_id: z.string(), limit: z.number().int().optional().default(50) },
  "list",
  (a, signal) => semanticScholar.getPaperReferences(a.paper_id, a.limit, signal),
);

register(
  "get_semantic_scholar_paper_citations",
  { paper_id: z.string(), limit: z.number().int().optional().default(50) },
  "list",
  (a, signal) => semanticScholar.getPaperCitations(a.paper_id, a.limit, signal),
);

register("get_semantic_scholar_papers_batch", { paper_ids: z.array(z.string()) }, "list", (a, signal) =>
  semanticScholar.getPapersBatch(a.paper_ids, signal),
);

register("get_semantic_scholar_author", { author_id: z.string() }, "object", (a, signal) =>
  semanticScholar.getAuthor(a.author_id, signal),
);

register(
  "search_semantic_scholar_authors",
  { query: z.string(), limit: z.number().int().optional().default(10) },
  "list",
  (a, signal) => semanticScholar.searchAuthors(a.query, a.limit, signal),
);

register(
  "get_semantic_scholar_author_papers",
  { author_id: z.string(), limit: z.number().int().optional().default(50) },
  "list",
  (a, signal) => semanticScholar.getAuthorPapers(a.author_id, a.limit, signal),
);

register(
  "get_semantic_scholar_paper_recommendations",
  { paper_id: z.string(), limit: z.number().int().optional().default(10) },
  "list",
  (a, signal) => semanticScholar.getPaperRecommendations(a.paper_id, a.limit, signal),
);

register(
  "search_semantic_scholar_snippets",
  { query: z.string(), limit: z.number().int().optional().default(10) },
  "list",
  (a, signal) => semanticScholar.searchSnippets(a.query, a.limit, signal),
);

// ---------- Google Scholar --------------------------------------------------

register(
  "search_google_scholar",
  { query: z.string(), num_results: z.number().int().optional().default(5) },
  "list",
  (a, signal) => googleScholar.search(a.query, a.num_results, signal),
);

register(
  "search_google_scholar_advanced",
  {
    query: z.string(),
    author: z.string().nullable().optional(),
    year_start: z.number().int().nullable().optional(),
    year_end: z.number().int().nullable().optional(),
    num_results: z.number().int().optional().default(5),
  },
  "list",
  (a, signal) =>
    googleScholar.searchAdvanced(a.query, a.author ?? undefined, a.year_start ?? undefined, a.year_end ?? undefined, a.num_results, signal),
);

register("get_google_scholar_author_info", { author_name: z.string() }, "object", (a, signal) =>
  googleScholar.getAuthorInfo(a.author_name, signal),
);

// ---------- Bohrium LKM -----------------------------------------------------

register(
  "search_bohrium_lkm",
  {
    query: z.string(),
    top_k: z.number().int().optional().default(10),
    scopes: z.string().optional().default("claim,conclusion,abstract"),
  },
  "object",
  (a) => bohrium.searchLkm(a.query, a.top_k, a.scopes),
);

register(
  "search_bohrium_reasoning",
  { query: z.string(), top_k: z.number().int().optional().default(10) },
  "object",
  (a) => bohrium.searchReasoning(a.query, a.top_k),
);

register(
  "get_bohrium_paper_graph",
  {
    paper_id: z.string(),
    max_nodes: z.number().int().optional().default(25),
    max_edges: z.number().int().optional().default(40),
  },
  "object",
  (a) => bohrium.getPaperGraph(a.paper_id, a.max_nodes, a.max_edges),
);

register(
  "search_bohrium_paper",
  {
    query: z.string(),
    size: z.number().int().optional().default(10),
    year_from: z.number().int().nullable().optional(),
    year_to: z.number().int().nullable().optional(),
    jcr: z.string().nullable().optional(),
  },
  "object",
  (a) => bohrium.searchPapers(a.query, a.size, a.year_from ?? undefined, a.year_to ?? undefined, a.jcr ?? undefined),
);

register("submit_bohrium_pdf", { pdf_path: z.string() }, "object", (a) => bohrium.parseSubmit(a.pdf_path));

register("check_bohrium_parse_task", { task_id: z.string() }, "object", (a) => bohrium.parseStatus(a.task_id));

register(
  "wait_bohrium_parse_task",
  {
    task_id: z.string(),
    interval_s: z.number().int().optional().default(5),
    timeout_s: z.number().int().optional().default(60),
  },
  "object",
  (a) => bohrium.parseWait(a.task_id, a.interval_s, a.timeout_s),
);

register("get_bohrium_parse_result", { task_id: z.string() }, "object", (a) =>
  bohrium.parseResult(a.task_id),
);

async function main(): Promise<void> {
  log(
    `starting: timeout=${TIMEOUT_MS / 1000}s lkm_spend=${process.env.OSP_ALLOW_LKM_SPEND === "1" ? "authorized" : "denied"} s2_key=${process.env.SEMANTIC_SCHOLAR_API_KEY ? "present" : "absent"}`,
  );
  await server.connect(new StdioServerTransport());
}

main().catch((error: unknown) => {
  log(`fatal: ${(error as Error).message}`);
  process.exit(1);
});
