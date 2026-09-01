import { describe, expect, it } from "vitest";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { validatePhase } from "../src/validation.js";

describe("final review contract", () => {
  it("rejects a review with missing criterion score rows", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-review-validation-"));
    try {
      await mkdir(join(directory, ".brain", "review"), { recursive: true });
      await writeFile(join(directory, ".brain", "session.json"), JSON.stringify({ qa_criteria: [{ slug: "novelty" }, { slug: "soundness" }], phases: { review: { status: "completed", completed_at: "now", notes: "ok" } } }));
      await writeFile(join(directory, ".brain", "review", "final_review.md"), "## Method\nx\n## Output\n## Summary\n## Strengths\n## Weaknesses\n## Dimension Scores\n| Dimension | Score |\n|---|---|\n| Novelty | 3/5 |\n## Recommendation\nReject\n## What was not checked\nx\n## Provenance\n01_structured_summary.md\n");
      const checks = await validatePhase(directory, "review");
      expect(checks.find((check) => check.name === "review:score-rows")?.passed).toBe(false);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("accepts the universal output wrapper and three-column score table", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-review-valid-"));
    try {
      await mkdir(join(directory, ".brain", "review"), { recursive: true });
      await writeFile(join(directory, ".brain", "session.json"), JSON.stringify({ qa_criteria: [{ slug: "novelty" }], phases: { review: { status: "completed", completed_at: "now", notes: "ok" } } }));
      await writeFile(join(directory, ".brain", "review", "final_review.md"), "## Method\nx\n## Output\n### Summary\nx\n### Strengths\nx\n### Weaknesses\nx\n### Dimension Scores\n| Criterion | Score (1–5) | Assessment |\n|---|---:|---|\n| Novelty | 3/5 | adequate |\n### Decision Recommendation\nReject\n### Confidence\nx\n## Provenance\n01_structured_summary.md\n");
      const checks = await validatePhase(directory, "review");
      expect(checks.every((check) => check.passed)).toBe(true);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("accepts insufficient-evidence scores but rejects unknown criteria", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-review-score-"));
    try {
      await mkdir(join(directory, ".brain", "review"), { recursive: true });
      await writeFile(join(directory, ".brain", "session.json"), JSON.stringify({ qa_criteria: [{ slug: "novelty", label: "Novelty & Originality" }], phases: { review: { status: "completed", completed_at: "now", notes: "ok" } } }));
      const common = "## Method\nx\n## Output\n### Summary\nx\n### Strengths\nx\n### Weaknesses\nx\n### Dimension Scores\n| Criterion | Score | Assessment |\n|---|---|---|\n";
      await writeFile(join(directory, ".brain", "review", "final_review.md"), `${common}| Novelty & Originality | insufficient evidence to judge | unresolved |\n### Decision Recommendation\nneeds revision\n### Confidence\nx\n## Provenance\n01_structured_summary.md\n`);
      expect((await validatePhase(directory, "review")).find((check) => check.name === "review:score-rows")?.passed).toBe(true);
      await writeFile(join(directory, ".brain", "review", "final_review.md"), `${common}| Other Criterion | 3/5 | unsupported |\n### Decision Recommendation\nneeds revision\n### Confidence\nx\n## Provenance\n01_structured_summary.md\n`);
      expect((await validatePhase(directory, "review")).find((check) => check.name === "review:score-rows")?.passed).toBe(false);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("requires a condition when a dimension score is 2 or lower", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-review-condition-"));
    try {
      await mkdir(join(directory, ".brain", "review"), { recursive: true });
      await writeFile(join(directory, ".brain", "session.json"), JSON.stringify({ qa_criteria: [{ slug: "novelty", label: "Novelty" }], phases: { review: { status: "completed", completed_at: "now", notes: "ok" } } }));
      const review = (recommendation: string) => `## Method\nx\n## Output\n### Summary\nx\n### Strengths\nx\n### Weaknesses\nx\n### Dimension Scores\n| Dimension | Score | Assessment |\n|---|---|---|\n| Novelty | 2/5 | weak |\n### Decision Recommendation\n${recommendation}\n### Confidence\nx\n## Provenance\n01_structured_summary.md\n`;
      await writeFile(join(directory, ".brain", "review", "final_review.md"), review("needs revision"));
      expect((await validatePhase(directory, "review")).find((check) => check.name === "review:recommendation")?.passed).toBe(false);
      await writeFile(join(directory, ".brain", "review", "final_review.md"), review("needs revision, conditional on additional evidence"));
      expect((await validatePhase(directory, "review")).find((check) => check.name === "review:recommendation")?.passed).toBe(true);
    } finally { await rm(directory, { recursive: true, force: true }); }
  });
});
