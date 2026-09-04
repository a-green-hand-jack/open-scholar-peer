import { describe, expect, it } from "vitest";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { checkpoint, git, initGit } from "../src/checkpoints.js";
import { exportFinalReview } from "../src/delivery.js";
import { resolveRun } from "../src/discover.js";
import { importSource, readMaterialManifest } from "../src/input.js";
import { CONTRACTS, contractsMatch } from "../src/provenance.js";
import { recordRetrievalEvents } from "../src/audit.js";

describe("runtime contracts", () => {
  it("imports an existing OSP workspace without reusing its mutable state", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-existing-workspace-"));
    try {
      const source = join(directory, "source-run");
      const target = join(directory, "target-run");
      await mkdir(join(source, ".brain", "input"), { recursive: true });
      await mkdir(join(target, ".brain"), { recursive: true });
      await writeFile(join(source, ".brain", "input", "paper.md"), "# Paper\n");
      const imported = await importSource(source, target);
      expect(imported.kind).toBe("osp-workspace");
      expect(await readFile(join(target, "source", "paper.md"), "utf8")).toBe("# Paper\n");
      expect(await readFile(join(target, ".brain", "input", "paper.md"), "utf8")).toBe("# Paper\n");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("imports the Harbor material manifest next to its paper directory", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-manifest-"));
    try {
      const source = join(directory, "paper");
      const workspace = join(directory, "run");
      await mkdir(join(workspace, ".brain"), { recursive: true });
      await mkdir(source, { recursive: true });
      await writeFile(join(source, "paper.md"), "# Harbor paper\n");
      await writeFile(join(directory, "material-manifest.json"), JSON.stringify({ manuscript_pdf: "paper.md" }));
      expect((await readMaterialManifest(source))?.manuscript_pdf).toBe(join(source, "paper.md"));
      expect((await importSource(source, workspace)).kind).toBe("tex-directory+material-manifest");
      expect(await readFile(join(workspace, "source", "material-manifest.json"), "utf8")).toContain("paper.md");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("refuses a material manifest that points outside its source tree", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-manifest-escape-"));
    try {
      await writeFile(join(directory, "material-manifest.json"), JSON.stringify({ manuscript_pdf: "../outside.pdf" }));
      await expect(readMaterialManifest(directory)).rejects.toThrow("escapes the imported source");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("exports a stable review and a versioned manifest", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-delivery-"));
    try {
      const run = join(directory, "runs", "osp-test");
      const requested = join(directory, "submission", "review.md");
      await mkdir(join(run, ".brain", "review"), { recursive: true });
      await mkdir(join(run, ".osp-run"), { recursive: true });
      await mkdir(join(run, "source"), { recursive: true });
      await writeFile(join(run, ".brain", "review", "final_review.md"), "## Review\n");
      await writeFile(join(run, ".osp-run", "run.json"), JSON.stringify({ run_id: "osp-test", status: "completed", provenance: { contracts: CONTRACTS }, scope: {}, completed_at: "now" }));
      const delivery = await exportFinalReview(run, requested);
      expect(await readFile(delivery.canonicalReview, "utf8")).toBe("## Review\n");
      expect(await readFile(requested, "utf8")).toBe("## Review\n");
      expect(JSON.parse(await readFile(delivery.manifest, "utf8")).contracts).toEqual(CONTRACTS);
      await expect(exportFinalReview(run, join(run, "source", "review.md"))).rejects.toThrow("must not write into the imported source tree");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("writes redacted retrieval provenance and matches only compatible contracts", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-audit-"));
    try {
      await mkdir(join(directory, ".osp-run"), { recursive: true });
      const count = await recordRetrievalEvents(directory, "literature", [{ parts: [{ type: "tool", callID: "retrieval-1", tool: "osp_search_bohrium_paper", state: { status: "completed", input: { token: "secret-token" }, error: "Bearer private-token" } }] }]);
      expect(count).toBe(1);
      const log = await readFile(join(directory, ".osp-run", "mcp-retrieval.jsonl"), "utf8");
      expect(log).not.toContain("secret-token");
      expect(log).not.toContain("private-token");
      expect(contractsMatch(CONTRACTS)).toBe(true);
      expect(contractsMatch({ ...CONTRACTS, final_review: "2.1" })).toBe(false);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("refuses ambiguous runs and records checkpoint trailers", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-run-resolution-"));
    try {
      for (const name of ["osp-one", "osp-two"]) {
        await mkdir(join(directory, name, ".osp-run"), { recursive: true });
        await writeFile(join(directory, name, ".osp-run", "run.json"), "{}");
      }
      await expect(resolveRun(directory)).rejects.toThrow("multiple OSP runs found");

      const checkpointDir = join(directory, "checkpoint");
      await mkdir(checkpointDir, { recursive: true });
      await initGit(checkpointDir);
      await writeFile(join(checkpointDir, "artifact.txt"), "evidence\n");
      await checkpoint(checkpointDir, "osp-checkpoint", "prepared", "prepared");
      expect(await git(checkpointDir, "log", "-1", "--format=%B")).toContain("OSP-Run: osp-checkpoint");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });
});
