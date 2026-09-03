import { chmod, cp, mkdir, readFile, stat } from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";
import { execa } from "execa";
import { now, readJson, sha256, writeJsonAtomic } from "./fs.js";

const MARKER = ".osp-trail.json";

type TrailState = {
  run_id: string;
  final_review_sha256: string;
  created_at: string;
  files: Record<string, string>;
  upload: { status: string; repo?: string; at?: string; returncode?: number };
};

async function isFile(path: string): Promise<boolean> {
  try { return (await stat(path)).isFile(); } catch { return false; }
}

async function digestFile(path: string): Promise<string> {
  return sha256(await readFile(path));
}

/**
 * Copy the auditable subset of a completed run into an immutable trail entry.
 * An existing entry is never rewritten: it is either verified and reused, or
 * the call fails.
 */
export async function writeTrail(runDir: string, trailRoot: string): Promise<string> {
  const runId = basename(runDir);
  const trail = join(resolve(trailRoot), runId);
  const marker = join(trail, MARKER);
  if (await isFile(marker)) {
    const state = await readJson(marker) as TrailState;
    if (state.run_id !== runId) throw new Error(`refusing to overwrite a trail not owned by this run: ${trail}`);
    for (const [relative, expected] of Object.entries(state.files)) {
      const path = join(trail, relative);
      if (!await isFile(path) || await digestFile(path) !== expected) throw new Error(`existing trail integrity check failed: ${relative}`);
    }
    return trail;
  }
  try { await stat(trail); throw new Error(`refusing to overwrite a trail not owned by this run: ${trail}`); } catch (error) {
    if (error instanceof Error && error.message.startsWith("refusing")) throw error;
  }
  const candidates = [
    join(".osp-run", "run.json"),
    join(".osp-run", "source-manifest.json"),
    join(".osp-run", "provenance.json"),
    join(".osp-run", "mcp-retrieval.jsonl"),
    join(".brain", "session.json"),
    join(".brain", "review", "final_review.md"),
  ];
  const finalReview = join(runDir, ".brain", "review", "final_review.md");
  if (!await isFile(finalReview)) throw new Error("refusing to write a trail without a final review");
  await mkdir(trail, { recursive: true });
  const files: Record<string, string> = {};
  for (const relative of candidates) {
    const source = join(runDir, relative);
    if (!await isFile(source)) continue;
    const target = join(trail, relative);
    await mkdir(dirname(target), { recursive: true });
    await cp(source, target);
    files[relative.replaceAll("\\", "/")] = await digestFile(target);
    await chmod(target, 0o444);
  }
  const state: TrailState = { run_id: runId, final_review_sha256: await digestFile(finalReview), created_at: now(), files, upload: { status: "not-requested" } };
  await writeJsonAtomic(marker, state);
  return trail;
}

/**
 * Publish a trail entry to a Hugging Face dataset. Uploading review content is
 * always explicit, is never retried silently, and fails the run on error.
 */
export async function uploadTrail(trail: string, repo: string): Promise<void> {
  const marker = join(trail, MARKER);
  const state = await readJson(marker) as TrailState;
  if (state.upload.status === "completed" && state.upload.repo === repo) return;
  const result = await execa("hf", ["upload", repo, trail, state.run_id, "--repo-type", "dataset"], { reject: false })
    .catch(() => { throw new Error("trail upload requested but the Hugging Face `hf` CLI is not installed"); });
  if (result.exitCode !== 0) {
    await writeJsonAtomic(marker, { ...state, upload: { status: "failed", repo, at: now(), returncode: result.exitCode ?? -1 } });
    throw new Error(`trail upload failed: ${(result.stderr || result.stdout || "").trim()}`);
  }
  await writeJsonAtomic(marker, { ...state, upload: { status: "completed", repo, at: now() } });
}
