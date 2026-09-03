import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { execa } from "execa";

/**
 * Versioned contracts consumed by downstream benchmarks. A breaking change to
 * the `.brain/` tree, the artifact headings, or the final review structure must
 * bump the matching version so an archiver can refuse an incompatible trail
 * instead of silently archiving a malformed one.
 */
export const CONTRACTS = {
  brain_layout: "2.2",
  artifact_contract: "2.2",
  final_review: "2.2",
  run_state: "osp-run-v2",
} as const;

export function contractsMatch(actual: unknown, expected: typeof CONTRACTS = CONTRACTS): boolean {
  if (!actual || typeof actual !== "object") return false;
  const candidate = actual as Record<string, unknown>;
  return Object.entries(expected).every(([key, value]) => candidate[key] === value);
}

export type Provenance = {
  osp_version: string;
  osp_commit: string | null;
  opencode_version: string | null;
  node_version: string;
  platform: string;
  contracts: typeof CONTRACTS;
};

async function commandOutput(command: string, args: string[]): Promise<string | null> {
  try { return (await execa(command, args)).stdout.trim() || null; } catch { return null; }
}

export async function packageVersion(root: string): Promise<string> {
  return (JSON.parse(await readFile(join(root, "package.json"), "utf8")) as { version: string }).version;
}

/** Commit of the installed OSP checkout, or null when installed from an archive. */
export async function ospCommit(root: string): Promise<string | null> {
  try { return (await execa("git", ["rev-parse", "HEAD"], { cwd: root })).stdout.trim(); } catch { return null; }
}

export async function collectProvenance(root: string): Promise<Provenance> {
  return {
    osp_version: await packageVersion(root),
    osp_commit: await ospCommit(root),
    opencode_version: await commandOutput("opencode", ["--version"]),
    node_version: process.version,
    platform: `${process.platform}-${process.arch}`,
    contracts: CONTRACTS,
  };
}
