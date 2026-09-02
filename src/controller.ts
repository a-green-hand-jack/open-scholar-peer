import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { checkpoint } from "./checkpoints.js";
import { now, readJson, writeJsonAtomic } from "./fs.js";
import { COMMANDS, PHASES, type Phase } from "./phases.js";
import { validatePhase } from "./validation.js";
import { abortSession, createSession, prompt, startOpenCode, waitForIdle, type OpenCodeRuntime } from "./opencode.js";
import { recommendationContract, recommendationFormat } from "./recommendation.js";

type ControllerOptions = { workspace: string; mode: "autonomous" | "collaborative"; headless: boolean; model?: string; variant?: string; timeoutMs: number };

export class ReviewController {
  private runtime?: OpenCodeRuntime;
  private sessionId?: string;
  private interrupted = false;
  private rejectInterruption?: (error: Error) => void;
  private readonly interruption = new Promise<never>((_, reject) => { this.rejectInterruption = reject; });
  private readonly options: ControllerOptions;

  constructor(options: ControllerOptions) { this.options = options; }

  async run(): Promise<void> {
    this.runtime = await startOpenCode(this.options.workspace);
    let tui: ReturnType<typeof import("./opencode.js")["attachTui"]> | undefined;
    const abortController = new AbortController();
    const interrupt = (signal: NodeJS.Signals) => {
      this.interrupted = true;
      abortController.abort();
      this.rejectInterruption?.(new Error(`review interrupted by ${signal}`));
    };
    process.once("SIGINT", interrupt);
    process.once("SIGTERM", interrupt);
    let activePhase: Promise<void> | undefined;
    try {
      this.sessionId = await createSession(this.runtime, this.options.workspace);
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "session.json"), { server_url: this.runtime.serverUrl, session_id: this.sessionId, created_at: now(), pid: process.pid });
      tui = this.options.headless ? undefined : (await import("./opencode.js")).attachTui(this.runtime, this.options.workspace, this.sessionId);
      const tuiExited = tui?.exited;
      for (const phase of PHASES) {
        const state = await this.state();
        if (state.phases[phase]?.status === "completed") continue;
        activePhase = this.runPhase(phase, abortController.signal);
        const outcome = await Promise.race([activePhase, this.interruption, ...(tuiExited ? [tuiExited] : [])]);
        if (typeof outcome === "number") {
          this.interrupted = true;
          abortController.abort();
          throw new Error(`OpenCode TUI exited with code ${outcome}`);
        }
        activePhase = undefined;
      }
      const state = await this.state();
      state.status = "completed";
      state.completed_at = now();
      state.updated_at = now();
      state.final_review = join(this.options.workspace, ".brain", "review", "final_review.md");
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
      await checkpoint(this.options.workspace, state.run_id, "completed", "completed", this.sessionId);
    } catch (error) {
      if (this.sessionId) await abortSession(this.runtime, this.options.workspace, this.sessionId);
      if (activePhase) await activePhase.catch(() => undefined);
      const state = await this.state();
      state.status = this.interrupted ? "interrupted" : "failed";
      state.updated_at = now();
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
      throw error;
    } finally {
      process.removeListener("SIGINT", interrupt);
      process.removeListener("SIGTERM", interrupt);
      if (tui && tui.process.exitCode === null && tui.process.signalCode === null) {
        tui.process.kill("SIGTERM");
        await tui.exited;
      }
      this.runtime.close();
    }
  }

  private async runPhase(phase: Phase, signal?: AbortSignal): Promise<void> {
    const state = await this.state();
    state.status = "running";
    state.current_phase = phase;
    state.updated_at = now();
    state.phases[phase] = { ...state.phases[phase], status: "running", attempts: (state.phases[phase]?.attempts ?? 0) + 1, started_at: now(), error: null };
    await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
    const command = await readFile(join(this.options.workspace, ".opencode", "commands", `${COMMANDS[phase]}.md`), "utf8");
    const session = await readJson(join(this.options.workspace, ".brain", "session.json"));
    const guidelines = await readFile(join(this.options.workspace, ".brain", "raw", "00_review_guidelines.md"), "utf8").catch(() => undefined);
    const liveRecommendation = recommendationContract(session, guidelines);
    if (phase !== "onboarding" && !state.review_contract) {
      if (!liveRecommendation.valid) throw new Error("recommendation contract was not validly configured during onboarding");
      state.review_contract = { labels: liveRecommendation.labels, source: liveRecommendation.source, rationale: liveRecommendation.rationale };
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
    }
    const frozen = state.review_contract;
    if (frozen && (JSON.stringify(frozen.labels) !== JSON.stringify(liveRecommendation.labels) || frozen.source !== liveRecommendation.source || frozen.rationale !== liveRecommendation.rationale)) throw new Error("recommendation contract changed after onboarding");
    const recommendation = frozen ? { ...frozen, valid: true } : liveRecommendation;
    const promptText = `Execute only OSP phase ${phase} in this isolated, autonomous, report-only review workspace.

Read .brain/session.json first and follow the installed command below exactly. Do not ask the user questions: use the configured venue/domain/default fallback and continue autonomously. Do not modify source/. Do not execute or advance another phase. Perform the file reads and writes yourself; do not merely describe the work. Unknown evidence must be marked unresolved or not assessable.

The controller will not trust a textual completion claim. The phase is complete only when its required files exist, contain non-empty ## Method, ## Output, and ## Provenance sections, and .brain/session.json marks this phase completed with completed_at and notes.

For onboarding, write .brain/raw/00_review_guidelines.md, create exactly one .brain/raw/05_qa_<criterion-slug>.md scaffold for every session.json.qa_criteria item, and update session.json. For literature, perform all three distinct rounds and write the three round artifacts plus the consolidated artifact. For QA, write exactly the configured number of ordered Q/A pairs per criterion. For review, write .brain/review/final_review.md only after every earlier phase is complete.

Follow the installed command below:

    ${command}${phase === "literature" ? "\n\nLKM behavior: use the round's primary osp_search_bohrium_* tool first, then osp_get_bohrium_paper_graph on a returned top hit where required. Google Scholar is fallback only when the round's primary LKM search returns an error and no primary LKM search returned usable data; graph or PDF-extraction errors do not authorize fallback. Record actual tools and source IDs in Provenance. Optional PDF extraction is best-effort and must not block the three rounds." : ""}${phase === "review" ? `\n\nController validation is strict: the final file must contain exact level-two headings \`## Summary\`, \`## Strengths\`, \`## Weaknesses\`, \`## Dimension Scores\`, \`## Assessment\`, \`## Recommendation\`, and \`## What was not checked\`. Use exactly \`## Recommendation\`, not \`Readiness Recommendation\` or another alias. Under \`## Dimension Scores\`, use the exact five columns \`Dimension | Score | What this band means here | Why this score | Evidence\` and write exactly one row for every \`session.json.qa_criteria\` item. Each row must use the exact criterion label, a score such as \`3/5\` or \`insufficient evidence to judge\`, and a concrete artifact anchor in Evidence. The first non-empty line under \`## Recommendation\` must be ${recommendationFormat(recommendation)}. The justification must include this exact vocabulary-set rationale: \`${recommendation.rationale}\`. If any score is 0-2/5, that same first line must use the exact form \`**<controlled label>, conditional on <concrete required changes>**\`; do not invent a label or put the condition in a later paragraph.` : ""}`;
    try {
      const invocations = phase === "literature" ? 3 : 1;
      for (let round = 1; round <= invocations; round += 1) {
        await prompt(this.runtime!, this.options.workspace, this.sessionId!, `${promptText}\n\nThis is literature round ${round} of 3.` , this.options.model, this.options.variant);
        await waitForIdle(this.runtime!, this.options.workspace, this.sessionId!, this.options.timeoutMs, signal);
      }
      let checks = await validatePhase(this.options.workspace, phase, phase === "review" ? recommendation : undefined);
      let failed = checks.filter((check) => !check.passed);
      if (failed.length > 0) {
        const details = failed.map((check) => `${check.name}: ${check.detail}`).join("; ");
        await prompt(this.runtime!, this.options.workspace, this.sessionId!, `The ${phase} phase output failed controller validation: ${details}. Remediate only this phase now. ${phase === "review" ? `For the recommendation check, the first non-empty line under \`## Recommendation\` must be ${recommendationFormat(recommendation)} and the justification must include \`${recommendation.rationale}\`. If any score is 0-2/5, write it on that same line exactly as \`**<controlled label>, conditional on <concrete required changes>**\`; do not add a \`Controlled label:\` prefix, invent a label, or put the condition in a later paragraph. ` : ""}Write the missing or invalid artifacts and update .brain/session.json; do not advance to another phase.`, this.options.model, this.options.variant);
        await waitForIdle(this.runtime!, this.options.workspace, this.sessionId!, this.options.timeoutMs, signal);
        checks = await validatePhase(this.options.workspace, phase, phase === "review" ? recommendation : undefined);
        failed = checks.filter((check) => !check.passed);
      }
      if (failed.length > 0) throw new Error(`${phase} failed validation: ${failed.map((check) => `${check.name}: ${check.detail}`).join("; ")}`);
      const current = await this.state();
      if (phase === "onboarding") {
        const completedSession = await readJson(join(this.options.workspace, ".brain", "session.json"));
        const completedGuidelines = await readFile(join(this.options.workspace, ".brain", "raw", "00_review_guidelines.md"), "utf8").catch(() => undefined);
        const completedRecommendation = recommendationContract(completedSession, completedGuidelines);
        if (!completedRecommendation.valid) throw new Error("onboarding did not produce a valid recommendation contract");
        current.review_contract = { labels: completedRecommendation.labels, source: completedRecommendation.source, rationale: completedRecommendation.rationale };
      }
      current.phases[phase] = { ...current.phases[phase], status: "completed", completed_at: now(), notes: `${phase} artifacts validated`, error: null };
      current.status = "prepared";
      current.updated_at = now();
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), current);
      await checkpoint(this.options.workspace, current.run_id, phase, "completed", this.sessionId);
      if (this.options.mode === "collaborative" && phase !== "review") {
        current.status = "gate_waiting";
        await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), current);
        await this.waitForApproval(signal);
      }
    } catch (error) {
      const failed = await this.state();
      const status = this.interrupted ? "interrupted" : "failed";
      failed.phases[phase] = { ...failed.phases[phase], status, completed_at: now(), error: error instanceof Error ? error.message : String(error) };
      failed.status = status;
      failed.updated_at = now();
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), failed);
      await checkpoint(this.options.workspace, failed.run_id, phase, status, this.sessionId);
      throw error;
    }
  }

  private async waitForApproval(signal?: AbortSignal): Promise<void> {
    const deadline = Date.now() + this.options.timeoutMs;
    while (Date.now() < deadline) {
      if (signal?.aborted) throw new Error("collaborative gate interrupted");
      const state = await this.state();
      if (state.status === "prepared") return;
      if (state.status === "failed" || state.status === "interrupted") throw new Error(`gate ended with status ${state.status}`);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    throw new Error(`collaborative gate was not approved within ${this.options.timeoutMs}ms`);
  }

  private async state(): Promise<any> { return readJson(join(this.options.workspace, ".osp-run", "run.json")); }
}
