import { readFile, stat } from "node:fs/promises";
import { join } from "node:path";
import { expectedOutputs, FIXED_OUTPUTS, LITERATURE_STRATEGIES, PHASES, type Phase } from "./phases.js";
import { readJson } from "./fs.js";
import { recommendationContract, recommendationFormat } from "./recommendation.js";
import type { RecommendationContract } from "./recommendation.js";
import { RunStateSchema } from "./state.js";
import { CONTRACTS, contractsMatch } from "./provenance.js";

export type Check = { name: string; passed: boolean; detail: string };

async function exists(path: string): Promise<boolean> {
  try { await stat(path); return true; } catch { return false; }
}

export async function validatePhase(workspace: string, phase: Phase, expectedRecommendation?: RecommendationContract): Promise<Check[]> {
  const checks: Check[] = [];
  const session = await readJson(join(workspace, ".brain", "session.json")) as { qa_criteria?: Array<{ slug?: string }>; qa_pairs_per_criterion?: number; phases?: Record<string, { status?: string; completed_at?: string; notes?: string }> };
  const outputs = expectedOutputs(session, phase);
  if (phase === "qa" && outputs.length === 0) checks.push({ name: "qa-criteria", passed: false, detail: "qa_criteria is empty" });
  for (const relative of outputs) {
    const path = join(workspace, relative);
    if (!await exists(path)) {
      checks.push({ name: relative, passed: false, detail: "missing artifact" });
      continue;
    }
    const content = await readFile(path, "utf8");
    for (const section of ["## Method", "## Output", "## Provenance"]) {
      checks.push({ name: `${relative}:${section}`, passed: content.includes(section), detail: content.includes(section) ? "present" : "missing" });
    }
    if (content.includes("{{") || content.includes("}}")) checks.push({ name: `${relative}:template`, passed: false, detail: "unresolved template placeholder" });
    if (phase === "qa") {
      const count = session.qa_pairs_per_criterion ?? 2;
      const questions = [...content.matchAll(/^### Q(\d+)\s*$/gm)].map((match) => Number(match[1]));
      const answers = [...content.matchAll(/^### A(\d+)\s*$/gm)].map((match) => Number(match[1]));
      const pairHeadings = [...content.matchAll(/^### Pair\s+(\d+)\s*$/gim)].map((match) => Number(match[1]));
      const labelledQuestions = [...content.matchAll(/^\*\*Question:\*\*/gim)].length;
      const labelledAnswers = [...content.matchAll(/^\*\*Answer:\*\*/gim)].length;
      const expected = Number.isInteger(count) && count > 0 ? Array.from({ length: count }, (_, index) => index + 1) : [];
      const templatedPairs = JSON.stringify(questions) === JSON.stringify(expected) && JSON.stringify(answers) === JSON.stringify(expected);
      const labelledPairs = JSON.stringify(pairHeadings) === JSON.stringify(expected) && labelledQuestions === count && labelledAnswers === count;
      checks.push({ name: `${relative}:qa-count`, passed: Number.isInteger(count) && count > 0 && (templatedPairs || labelledPairs), detail: `expected ${count} ordered pairs` });
    }
  }
  if (phase === "onboarding") {
    const contract = recommendationContract(session);
    checks.push({ name: "onboarding:recommendation-contract", passed: contract.valid, detail: "session.json.recommendation must contain unique labels plus a non-pending source and rationale" });
  }
  if (phase === "literature") {
    for (const [index, strategy] of LITERATURE_STRATEGIES.entries()) {
      const path = join(workspace, FIXED_OUTPUTS.literature[index]);
      if (await exists(path)) {
        const content = await readFile(path, "utf8");
        const escaped = strategy.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const pattern = new RegExp(`(?:\\*\\*)?Strategy:(?:\\*\\*)?\\s*\`?${escaped}\`?`, "i");
        checks.push({ name: `literature:${strategy}`, passed: pattern.test(content), detail: `round ${index + 1}` });
      }
    }
  }
  if (phase === "review" && await exists(join(workspace, FIXED_OUTPUTS.review[0]))) {
    const review = await readFile(join(workspace, FIXED_OUTPUTS.review[0]), "utf8");
    const required = ["Summary", "Strengths", "Weaknesses", "Dimension Scores", "Assessment"];
    for (const section of required) {
      const present = new RegExp(`^## ${section}\\s*$`, "m").test(review);
      checks.push({ name: `review:## ${section}`, passed: present, detail: present ? "present" : "missing" });
    }
    const recommendationHeading = /^## Recommendation\s*$/m;
    const notCheckedHeading = /^## What was not checked\s*$/m;
    checks.push({ name: "review:recommendation-heading", passed: recommendationHeading.test(review), detail: "recommendation heading" });
    checks.push({ name: "review:not-checked", passed: notCheckedHeading.test(review), detail: "confidence or what-was-not-checked section" });
    const criteria = (session.qa_criteria ?? []).filter((criterion): criterion is { slug: string; label?: string } => Boolean(criterion.slug));
    const scoreSection = review.split(/^#{2,3} Dimension Scores[ \t]*$/im)[1]?.split(/^#{2,3} /m)[0] ?? "";
    const scoreRows = scoreSection.split("\n").filter((line) => line.trim().startsWith("|")).map((line) => line.split("|").slice(1, -1).map((cell) => cell.trim())).filter((cells) => cells.length >= 5 && !/^[-: ]+$/.test(cells[0]) && !/^(?:criterion|dimension)$/i.test(cells[0]));
    const expectedLabels = new Set(criteria.map((criterion) => (criterion.label ?? criterion.slug).trim().toLowerCase()));
    const actualLabels = new Set(scoreRows.map((cells) => cells[0].toLowerCase()));
    const validScore = (value: string) => /^(?:[0-5]\s*\/\s*5|insufficient evidence to judge)$/i.test(value.trim());
    checks.push({ name: "review:score-rows", passed: scoreRows.length === criteria.length && actualLabels.size === criteria.length && [...actualLabels].every((label) => expectedLabels.has(label)) && scoreRows.every((cells) => validScore(cells[1]) && cells.slice(2, 5).every(Boolean) && /(?:\.md|paper §|paper section)/i.test(cells[4])), detail: `${scoreRows.length} five-column evidenced rows for ${criteria.length} criteria` });
    const recommendationBody = review.split(/^## Recommendation[ \t]*$/m)[1]?.split(/^## /m)[0] ?? "";
    const recommendation = recommendationBody.split("\n").map((line) => line.trim().replace(/^\*\*(.*)\*\*$/, "$1").replace(/^[-*]\s+/, "").trim()).find(Boolean) ?? "";
    const guidelines = await readFile(join(workspace, ".brain", "raw", "00_review_guidelines.md"), "utf8").catch(() => undefined);
    const sessionContract = recommendationContract(session, guidelines);
    const contract = expectedRecommendation ?? sessionContract;
    const escapedLabels = contract.labels.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    const allowed = new RegExp(`^(?:${escapedLabels.join("|")})(?:,\\s+conditional on\\s+.+)?$`);
    const lowScore = scoreRows.some((cells) => /^(?:[0-2])\s*\/\s*5$/i.test(cells[1]));
    const conditional = /\bconditional on\b/i.test(recommendation);
    const rationalePresent = recommendationBody.includes(contract.rationale);
    checks.push({ name: "review:recommendation", passed: contract.valid && allowed.test(recommendation) && (!lowScore || conditional) && rationalePresent, detail: lowScore ? `first recommendation line must be ${recommendationFormat(contract)} with an inline ', conditional on <required changes>' clause for scores 0-2 and the justification must state '${contract.rationale}'` : `first recommendation line must use ${recommendationFormat(contract)} and the justification must state '${contract.rationale}'` });
    if (expectedRecommendation) checks.push({ name: "review:recommendation-contract", passed: sessionContract.valid && JSON.stringify(sessionContract.labels) === JSON.stringify(expectedRecommendation.labels) && sessionContract.source === expectedRecommendation.source && sessionContract.rationale === expectedRecommendation.rationale, detail: "review phase must not alter the controller-owned recommendation contract" });
    checks.push({ name: "review:evidence-anchor", passed: /(?:\.brain\/raw\/01_structured_summary\.md|01_structured_summary\.md)/.test(review), detail: "summary artifact anchor" });
  }
  const phaseState = session.phases?.[phase];
  checks.push({ name: `session:${phase}`, passed: phaseState?.status === "completed" && Boolean(phaseState.completed_at) && Boolean(phaseState.notes), detail: phaseState?.status ?? "missing" });
  return checks;
}

export async function validateRun(workspace: string): Promise<Check[]> {
  const checks: Check[] = [];
  const state = RunStateSchema.parse(await readJson(join(workspace, ".osp-run", "run.json")));
  const actualContracts = (state.provenance as { contracts?: unknown } | undefined)?.contracts;
  const contractsValid = contractsMatch(actualContracts);
  checks.push({
    name: "run:contract-versions", passed: contractsValid,
    detail: contractsValid ? `matches ${JSON.stringify(CONTRACTS)}` : `incompatible or missing contract versions: ${JSON.stringify(actualContracts ?? null)}`,
  });
  for (const phase of PHASES) {
    const expectedRecommendation = phase === "review" && state.review_contract
      ? { ...state.review_contract, valid: true }
      : undefined;
    checks.push(...await validatePhase(workspace, phase, expectedRecommendation));
  }
  return checks;
}
