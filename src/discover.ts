import { readdir, stat } from "node:fs/promises";
import { join, resolve } from "node:path";

async function isRun(path: string): Promise<boolean> {
  try { return (await stat(join(path, ".osp-run", "run.json"))).isFile(); } catch { return false; }
}

/**
 * Resolve a run directory from an explicit path, from a parent output
 * directory, or from the default output directory when no argument is given.
 * Ambiguity is refused rather than guessed so `resume`/`approve` can never act
 * on the wrong run.
 */
export async function resolveRun(argument?: string): Promise<string> {
  const roots = argument ? [resolve(argument)] : [resolve("osp-review"), resolve(".")];
  const searched: string[] = [];
  for (const root of roots) {
    if (await isRun(root)) return root;
    searched.push(root);
    let entries: string[];
    try { entries = (await readdir(root, { withFileTypes: true })).filter((entry) => entry.isDirectory() && entry.name.startsWith("osp-")).map((entry) => join(root, entry.name)); }
    catch { continue; }
    const candidates: string[] = [];
    for (const candidate of entries) if (await isRun(candidate)) candidates.push(candidate);
    if (candidates.length === 1) return candidates[0];
    if (candidates.length > 1) throw new Error(`multiple OSP runs found under ${root}; pass one explicitly:\n  ${candidates.sort().join("\n  ")}`);
  }
  throw new Error(`no OSP run found at ${searched.join(" or ")}`);
}
