import { readFile, stat } from "node:fs/promises";
import { join } from "node:path";
import { FIXED_OUTPUTS, LITERATURE_STRATEGIES, PHASES, type Phase } from "./phases.js";
import { readJson } from "./fs.js";

export type Check = { name: string; passed: boolean; detail: string };

async function exists(path: string): Promise<boolean> {
  try { await stat(path); return true; } catch { return false; }
}

export async function validatePhase(workspace: string, phase: Phase): Promise<Check[]> {
  const checks: Check[] = [];
  const session = await readJson(join(workspace, ".brain", "session.json")) as { qa_criteria?: Array<{ slug?: string }>; qa_pairs_per_criterion?: number; phases?: Record<string, { status?: string; completed_at?: string; notes?: string }> };
  const outputs = phase === "qa"
    ? (session.qa_criteria ?? []).map((criterion) => `.brain/raw/05_qa_${criterion.slug}.md`)
    : [...FIXED_OUTPUTS[phase]];
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
      const expected = Array.from({ length: count }, (_, index) => index + 1);
      checks.push({ name: `${relative}:qa-count`, passed: JSON.stringify(questions) === JSON.stringify(expected) && JSON.stringify(answers) === JSON.stringify(expected), detail: `expected ${count} ordered pairs` });
    }
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
  const phaseState = session.phases?.[phase];
  checks.push({ name: `session:${phase}`, passed: phaseState?.status === "completed" && Boolean(phaseState.completed_at) && Boolean(phaseState.notes), detail: phaseState?.status ?? "missing" });
  return checks;
}

export async function validateRun(workspace: string): Promise<Check[]> {
  const checks: Check[] = [];
  for (const phase of PHASES) checks.push(...await validatePhase(workspace, phase));
  return checks;
}
