import { describe, expect, it } from "vitest";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { validatePhase } from "../src/validation.js";

describe("artifact compatibility", () => {
  it("accepts the canonical bold Markdown literature strategy", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-validation-"));
    try {
      await mkdir(join(directory, ".brain", "raw"), { recursive: true });
      await writeFile(join(directory, ".brain", "session.json"), JSON.stringify({ qa_criteria: [], phases: { literature: { status: "completed", completed_at: "now", notes: "ok" } } }));
      for (const [name, strategy] of [["02a_literature_round1.md", "sub-domain-anchor"], ["02b_literature_round2.md", "method-anchor"], ["02c_literature_round3.md", "temporal-expansion"]]) {
        await writeFile(join(directory, ".brain", "raw", name), `## Method\n- **Strategy:** \`${strategy}\`\n\n## Output\ncontent\n\n## Provenance\nsource\n`);
      }
      await writeFile(join(directory, ".brain", "raw", "02_retrieved_literature.md"), "## Method\nmethod\n\n## Output\ncontent\n\n## Provenance\nsource\n");
      expect((await validatePhase(directory, "literature")).filter((check) => check.name.startsWith("literature:")).every((check) => check.passed)).toBe(true);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("accepts pair-labelled QA artifacts", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-qa-validation-"));
    try {
      await mkdir(join(directory, ".brain", "raw"), { recursive: true });
      await writeFile(join(directory, ".brain", "session.json"), JSON.stringify({ qa_pairs_per_criterion: 2, qa_criteria: [{ slug: "novelty" }], phases: { qa: { status: "completed", completed_at: "now", notes: "ok" } } }));
      await writeFile(join(directory, ".brain", "raw", "05_qa_novelty.md"), "## Method\n## Output\n### Pair 1\n**Question:** q1\n**Answer:** a1\n### Pair 2\n**Question:** q2\n**Answer:** a2\n## Provenance\nsource\n");
      expect((await validatePhase(directory, "qa")).find((check) => check.name.endsWith(":qa-count"))?.passed).toBe(true);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });
});
