import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, join, resolve } from "node:path";
import { CONTRACTS } from "./provenance.js";
import { writeJsonAtomic } from "./fs.js";

export type DeliveryRecord = {
  canonicalReview: string;
  manifest: string;
  submittedReview: string | null;
};

/**
 * Export the completed report to paths that an unattended caller can consume
 * without discovering a timestamped workspace. A caller cannot redirect the
 * report into OSP's immutable imported-source tree.
 */
export async function exportFinalReview(runDir: string, requestedOutput?: string): Promise<DeliveryRecord> {
  const workspace = resolve(runDir);
  const parent = dirname(workspace);
  const review = join(workspace, ".brain", "review", "final_review.md");
  const content = await readFile(review, "utf8");
  const canonicalReview = join(parent, "final_review.md");
  await writeFile(canonicalReview, content, "utf8");

  let submittedReview: string | null = null;
  if (requestedOutput) {
    const target = resolve(requestedOutput);
    const sourceRoot = join(workspace, "source");
    if (target === sourceRoot || target.startsWith(`${sourceRoot}/`))
      throw new Error("--final-output must not write into the imported source tree");
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, content, "utf8");
    submittedReview = target;
  }

  const state = JSON.parse(await readFile(join(workspace, ".osp-run", "run.json"), "utf8"));
  const manifest = join(parent, "run-manifest.json");
  await writeJsonAtomic(manifest, {
    run_id: state.run_id,
    run_directory: workspace,
    status: state.status,
    final_review: canonicalReview,
    submission_review: submittedReview,
    final_review_sha256: createHash("sha256").update(content).digest("hex"),
    contracts: CONTRACTS,
    provenance: state.provenance,
    scope: state.scope,
    completed_at: state.completed_at,
  });
  return { canonicalReview, manifest, submittedReview };
}
