// Bohrium LKM provider backed by the official `bohr` CLI.
//
// Two safety properties are load-bearing and must not be relaxed:
//   1. Billable subcommands refuse to run unless OSP_ALLOW_LKM_SPEND is exactly
//      "1", so a run without --allow-lkm-spend can never incur a charge.
//   2. parse_submit only accepts a PDF sitting directly in the run's
//      .brain/input, so a prompt cannot walk the agent out of the workspace.
import { execa } from "execa";
import { realpath, stat } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";

const BOHR_TIMEOUT_MS = 30_000;
const PDFINFO_TIMEOUT_MS = 10_000;
const MAX_PDF_BYTES = 64 * 1024 * 1024;
const MAX_PDF_PAGES = 50;
const BILLABLE = new Set(["search", "reasoning", "graph", "result"]);

export type Json = Record<string, unknown>;
export type Failure = { error: string };

function isFailure(value: Json | Failure): value is Failure {
  return typeof (value as Failure).error === "string";
}

async function pdfPageCount(pdfPath: string): Promise<number | string> {
  try {
    const result = await execa("pdfinfo", [pdfPath], {
      timeout: PDFINFO_TIMEOUT_MS,
      reject: false,
    });
    if (result.failed && result.timedOut) {
      return "pdfinfo timed out while validating the LKM PDF page limit";
    }
    if (result.exitCode !== 0) {
      return "could not determine the PDF page count for LKM extraction";
    }
    const match = /^Pages:\s*(\d+)\s*$/m.exec(result.stdout);
    return match ? Number.parseInt(match[1], 10) : "could not determine the PDF page count for LKM extraction";
  } catch (error) {
    if ((error as { code?: string }).code === "ENOENT") {
      return "pdfinfo is required to validate the LKM PDF page limit";
    }
    return "could not determine the PDF page count for LKM extraction";
  }
}

async function call(args: string[], keepErrorData = false): Promise<Json | Failure> {
  if (args.some((part) => BILLABLE.has(part)) && process.env.OSP_ALLOW_LKM_SPEND !== "1") {
    return { error: "LKM spending is not authorized for this run; pass --allow-lkm-spend to osp review" };
  }

  let stdout: string;
  try {
    const result = await execa("bohr", [...args, "--yes", "-o", "json"], {
      timeout: BOHR_TIMEOUT_MS,
      reject: false,
    });
    if (result.timedOut) return { error: `bohr command timed out after ${BOHR_TIMEOUT_MS / 1000}s` };
    stdout = (result.stdout ?? "").trim();
  } catch (error) {
    if ((error as { code?: string }).code === "ENOENT") {
      return { error: "bohr CLI not found; install @dptech-corp/bohr-cli and run bohr auth login" };
    }
    return { error: `bohr invocation failed: ${(error as Error).message}` };
  }

  let payload: Json;
  try {
    payload = JSON.parse(stdout) as Json;
  } catch {
    // The CLI sometimes prefixes progress lines; the last JSON object wins.
    const line = stdout.split("\n").reverse().find((candidate) => candidate.trim().startsWith("{"));
    if (!line) return { error: "bohr returned invalid JSON: no JSON object in output" };
    try {
      payload = JSON.parse(line) as Json;
    } catch (error) {
      return { error: `bohr returned invalid JSON: ${(error as Error).message}` };
    }
  }

  if (payload.ok !== true) {
    if (keepErrorData && payload.data) return payload.data as Json;
    const error = (payload.error ?? {}) as Json;
    return { error: String(error.message ?? error.code ?? JSON.stringify(error)) };
  }
  return (payload.data as Json) ?? {};
}

function paper(value: Json): Json {
  return {
    id: value.id ?? value.paperId ?? "",
    title: value.en_title || value.zh_title || value.enName || value.zhName || "",
    authors: value.authors ?? "",
    abstract: value.enAbstract ?? "",
    doi: value.doi ?? "",
    venue: value.publication_name || value.publicationEnName || "",
    date: value.cover_date_start || value.coverDateStart || "",
    citations: value.citationNums ?? 0,
    jcr_zone: value.jcrZone ?? "",
    url: value.paperUrl ?? "",
  };
}

function papersFromMap(value: unknown): Json[] {
  return Object.values((value as Record<string, Json>) ?? {}).map(paper);
}

export async function searchLkm(query: string, topK = 10, scopes = "claim,conclusion,abstract"): Promise<Json | Failure> {
  const data = await call(["lkm", "search", query, "--top-k", String(topK), "--scopes", scopes]);
  if (isFailure(data)) return data;
  return { papers: papersFromMap(data.papers), variables: ((data.variables as unknown[]) ?? []).slice(0, topK) };
}

export async function searchReasoning(query: string, topK = 10): Promise<Json | Failure> {
  const data = await call(["lkm", "reasoning", "--query", query, "--top-k", String(topK)]);
  if (isFailure(data)) return data;
  return {
    papers: papersFromMap(data.papers),
    reasoning_chains: ((data.reasoning_chains as unknown[]) ?? []).slice(0, topK),
  };
}

export async function searchPapers(
  query: string,
  size = 10,
  yearFrom?: number,
  yearTo?: number,
  jcr?: string,
): Promise<Json | Failure> {
  const args = ["paper", "search", query, "--size", String(size), "--type", "0"];
  if (yearFrom !== undefined) args.push("--year-from", String(yearFrom));
  if (yearTo !== undefined) args.push("--year-to", String(yearTo));
  if (jcr) args.push("--jcr", jcr);
  const data = await call(args);
  if (isFailure(data)) return data;
  return {
    papers: ((data.items as Json[]) ?? []).map(paper),
    pagination: (data.pagination as Json) ?? {},
  };
}

export async function getPaperGraph(paperId: string, maxNodes = 25, maxEdges = 40): Promise<Json | Failure> {
  const data = await call(["lkm", "graph", "--paper-id", paperId], true);
  if (isFailure(data)) return data;
  const item = ((data.items as Json[]) ?? [])[0];
  if (!item) return { error: `no graph found for paper ${paperId}` };
  const graph = (item.graph as Json) ?? {};
  const nodes = (graph.nodes as unknown[]) ?? [];
  const edges = (graph.edges as unknown[]) ?? [];
  return {
    paper: paper((item.paper as Json) ?? {}),
    addressed_problems: item.addressed_problems ?? [],
    open_questions: item.open_questions ?? [],
    graph: {
      graph_empty: nodes.length === 0,
      node_count: nodes.length,
      edge_count: edges.length,
      nodes: nodes.slice(0, maxNodes),
      edges: edges.slice(0, maxEdges),
    },
  };
}

export async function parseSubmit(pdfPath: string): Promise<Json | Failure> {
  const workspace = process.env.OSP_WORKSPACE_ROOT;
  if (!workspace) return { error: "OSP_WORKSPACE_ROOT is not configured" };

  // Resolve symlinks on both sides before comparing, so a link planted inside
  // .brain/input cannot point at a file outside the workspace.
  const root = await realpath(resolve(workspace, ".brain", "input")).catch(() => null);
  const candidate = await realpath(resolve(pdfPath)).catch(() => null);
  if (!root || !candidate || dirname(candidate) !== root || extname(candidate).toLowerCase() !== ".pdf") {
    return { error: "pdf_path must be a regular PDF directly under .brain/input" };
  }
  const info = await stat(candidate).catch(() => null);
  if (!info?.isFile()) return { error: "pdf_path must be a regular PDF directly under .brain/input" };
  if (info.size > MAX_PDF_BYTES) return { error: "PDF exceeds the 64 MiB extraction limit" };

  const pages = await pdfPageCount(candidate);
  if (typeof pages === "string") return { error: pages };
  if (pages > MAX_PDF_PAGES) return { error: `PDF exceeds the ${MAX_PDF_PAGES}-page LKM extraction limit` };

  return call(["lkm", "parse", "submit", candidate]);
}

export async function parseStatus(taskId: string): Promise<Json | Failure> {
  return call(["lkm", "parse", "status", taskId]);
}

export async function parseWait(taskId: string, intervalS = 5, timeoutS = 60): Promise<Json | Failure> {
  const result = await call(["lkm", "parse", "wait", taskId, "--interval", `${intervalS}s`, "--timeout", `${timeoutS}s`]);
  if (isFailure(result) && (result.error.includes("TIMEOUT") || result.error.includes("stopped waiting"))) {
    // A wait timeout is not a failure: the extraction is still running.
    return { task_id: taskId, status: "running", warning: result.error };
  }
  return result;
}

export async function parseResult(taskId: string): Promise<Json | Failure> {
  return call(["lkm", "parse", "result", taskId, "--format", "graph"]);
}
