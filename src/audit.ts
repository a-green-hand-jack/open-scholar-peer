import { appendFile, readdir, readFile, stat } from "node:fs/promises";
import { join, relative } from "node:path";
import { expectedOutputs, type Phase } from "./phases.js";
import { now, sha256 } from "./fs.js";

/** Directories owned by the CLI runtime rather than by the review itself. */
const RUNTIME_DIRECTORIES = [".brain", ".osp-run", ".opencode", ".open-scholar-peer", ".git", ".archive-staging"];
const RETRIEVAL_TOOL = /(?:^osp[_.])|arxiv|semantic_?scholar|google_?scholar|bohrium|lkm/i;
const SECRET_KEY = /(?:api.?key|token|secret|password|authorization|cookie)/i;
const SECRET_VALUE = /(?:sk-[A-Za-z0-9_-]{12,}|bearer\s+\S+)/i;

export type Snapshot = Record<string, string>;

async function walk(root: string, current = root, skip: (name: string) => boolean = () => false): Promise<string[]> {
  const result: string[] = [];
  let entries;
  try { entries = await readdir(current, { withFileTypes: true }); } catch { return result; }
  for (const entry of entries) {
    const path = join(current, entry.name);
    if (skip(relative(root, path).replaceAll("\\", "/"))) continue;
    if (entry.isSymbolicLink() || entry.isFIFO() || entry.isSocket()) continue;
    if (entry.isDirectory()) result.push(...await walk(root, path, skip));
    else if (entry.isFile()) result.push(path);
  }
  return result;
}

async function snapshot(root: string, skip?: (name: string) => boolean): Promise<Snapshot> {
  const result: Snapshot = {};
  for (const path of await walk(root, root, skip)) {
    result[relative(root, path).replaceAll("\\", "/")] = sha256(await readFile(path));
  }
  return result;
}

export async function brainSnapshot(workspace: string): Promise<Snapshot> {
  return snapshot(join(workspace, ".brain"));
}

export async function workspaceSnapshot(workspace: string): Promise<Snapshot> {
  return snapshot(workspace, (name) => RUNTIME_DIRECTORIES.includes(name.split("/")[0]));
}

function changed(before: Snapshot, after: Snapshot): string[] {
  return [...new Set([...Object.keys(before), ...Object.keys(after)])].filter((path) => before[path] !== after[path]).sort();
}

/**
 * A phase may only touch its own contracted artifacts inside `.brain/`, and may
 * never touch the imported `source/` tree or any other workspace file. The
 * agent's own claim that it stayed in scope is not trusted.
 */
export async function verifyPhaseWrites(workspace: string, phase: Phase, brainBefore: Snapshot, workspaceBefore: Snapshot, session: unknown): Promise<void> {
  const allowed = new Set<string>(["session.json"]);
  for (const output of expectedOutputs(session, phase)) allowed.add(output.replace(/^\.brain\//, ""));
  if (phase === "onboarding") for (const output of expectedOutputs(session, "qa")) allowed.add(output.replace(/^\.brain\//, ""));
  const violations = changed(brainBefore, await brainSnapshot(workspace))
    .filter((path) => !allowed.has(path) && !path.startsWith("tmp/") && !path.startsWith("raw/transcripts/"));
  if (violations.length > 0) throw new Error(`${phase} changed files outside its artifact contract: ${violations.join(", ")}`);
  const outside = changed(workspaceBefore, await workspaceSnapshot(workspace));
  if (outside.length > 0) throw new Error(`${phase} changed files outside .brain/: ${outside.join(", ")}`);
}

export function redact(value: unknown, key = ""): unknown {
  if (SECRET_KEY.test(key)) return "[REDACTED]";
  if (Array.isArray(value)) return value.map((item) => redact(item));
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([itemKey, item]) => [itemKey, redact(item, itemKey)]));
  if (typeof value === "string" && SECRET_VALUE.test(value)) return "[REDACTED]";
  return value;
}

type ToolPart = { type: string; callID?: string; tool?: string; state?: { status?: string; input?: unknown; error?: string; title?: string; time?: { start?: number; end?: number } } };

/**
 * Append the retrieval tool calls a phase actually made to the run's provenance
 * log. Inputs are recorded; tool outputs are not, so paper content and secrets
 * never leak into provenance.
 */
export async function recordRetrievalEvents(workspace: string, phase: Phase, messages: unknown): Promise<number> {
  const path = join(workspace, ".osp-run", "mcp-retrieval.jsonl");
  const seen = new Set<string>();
  try {
    for (const line of (await readFile(path, "utf8")).split("\n")) {
      if (line.trim()) seen.add((JSON.parse(line) as { call_id?: string }).call_id ?? "");
    }
  } catch { /* first phase writes the log */ }
  const lines: string[] = [];
  for (const message of Array.isArray(messages) ? messages : []) {
    const parts = (message as { parts?: unknown[] }).parts ?? [];
    for (const part of parts as ToolPart[]) {
      if (part.type !== "tool" || !part.tool || !RETRIEVAL_TOOL.test(part.tool)) continue;
      const callId = part.callID ?? `${part.tool}-${lines.length}`;
      if (seen.has(callId)) continue;
      seen.add(callId);
      lines.push(JSON.stringify({
        phase, call_id: callId, tool: part.tool, status: part.state?.status ?? "unknown",
        input: redact(part.state?.input ?? {}), error: part.state?.error ? redact(part.state.error) : null,
        started_at: part.state?.time?.start ?? null, ended_at: part.state?.time?.end ?? null, recorded_at: now(),
      }));
    }
  }
  if (lines.length > 0) await appendFile(path, `${lines.join("\n")}\n`, "utf8");
  return lines.length;
}

export async function fileExists(path: string): Promise<boolean> {
  try { await stat(path); return true; } catch { return false; }
}
