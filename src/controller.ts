import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { checkpoint } from "./checkpoints.js";
import { now, readJson, writeJsonAtomic } from "./fs.js";
import { COMMANDS, PHASES, type Phase } from "./phases.js";
import { validatePhase } from "./validation.js";
import { abortSession, createSession, prompt, startOpenCode, waitForIdle, type OpenCodeRuntime } from "./opencode.js";

type ControllerOptions = { workspace: string; mode: "autonomous" | "collaborative"; headless: boolean; model?: string; variant?: string; timeoutMs: number };

export class ReviewController {
  private runtime?: OpenCodeRuntime;
  private sessionId?: string;
  private readonly options: ControllerOptions;

  constructor(options: ControllerOptions) { this.options = options; }

  async run(): Promise<void> {
    this.runtime = await startOpenCode(this.options.workspace);
    try {
      this.sessionId = await createSession(this.runtime, this.options.workspace);
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "session.json"), { server_url: this.runtime.serverUrl, session_id: this.sessionId, created_at: now(), pid: process.pid });
      const tui = this.options.headless ? undefined : (await import("./opencode.js")).attachTui(this.runtime, this.options.workspace, this.sessionId);
      let tuiExit: number | undefined;
      if (tui) tui.exited.then((code) => { tuiExit = code; });
      for (const phase of PHASES) {
        if (tuiExit !== undefined) throw new Error(`OpenCode TUI exited with code ${tuiExit}`);
        const state = await this.state();
        if (state.phases[phase]?.status === "completed") continue;
        await this.runPhase(phase);
      }
      const state = await this.state();
      state.status = "completed";
      state.completed_at = now();
      state.updated_at = now();
      state.final_review = join(this.options.workspace, ".brain", "review", "final_review.md");
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
      await checkpoint(this.options.workspace, state.run_id, "completed", "completed", this.sessionId);
      if (tui) { await new Promise((resolve) => setTimeout(resolve, 1500)); tui.process.kill("SIGTERM"); }
    } catch (error) {
      const state = await this.state();
      state.status = "failed";
      state.updated_at = now();
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
      if (this.sessionId) await abortSession(this.runtime, this.options.workspace, this.sessionId);
      throw error;
    } finally { this.runtime.close(); }
  }

  private async runPhase(phase: Phase): Promise<void> {
    const state = await this.state();
    state.status = "running";
    state.current_phase = phase;
    state.updated_at = now();
    state.phases[phase] = { ...state.phases[phase], status: "running", attempts: (state.phases[phase]?.attempts ?? 0) + 1, started_at: now(), error: null };
    await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), state);
    const command = await readFile(join(this.options.workspace, ".opencode", "commands", `${COMMANDS[phase]}.md`), "utf8");
    const promptText = `Execute only OSP phase ${phase}. Follow the installed command below exactly. Do not advance another phase, modify source/, or claim completion without writing and updating .brain/session.json.\n\n${command}`;
    try {
      const invocations = phase === "literature" ? 3 : 1;
      for (let round = 1; round <= invocations; round += 1) {
        await prompt(this.runtime!, this.options.workspace, this.sessionId!, `${promptText}\n\nThis is literature round ${round} of 3.` , this.options.model, this.options.variant);
        await waitForIdle(this.runtime!, this.options.workspace, this.sessionId!, this.options.timeoutMs);
      }
      const checks = await validatePhase(this.options.workspace, phase);
      const failed = checks.find((check) => !check.passed);
      if (failed) throw new Error(`${phase} failed validation: ${failed.name}: ${failed.detail}`);
      const current = await this.state();
      current.phases[phase] = { ...current.phases[phase], status: "completed", completed_at: now(), notes: `${phase} artifacts validated`, error: null };
      current.status = "prepared";
      current.updated_at = now();
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), current);
      await checkpoint(this.options.workspace, current.run_id, phase, "completed", this.sessionId);
      if (this.options.mode === "collaborative" && phase !== "review") {
        current.status = "gate_waiting";
        await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), current);
        await this.waitForApproval();
      }
    } catch (error) {
      const failed = await this.state();
      failed.phases[phase] = { ...failed.phases[phase], status: "failed", completed_at: now(), error: error instanceof Error ? error.message : String(error) };
      failed.status = "failed";
      failed.updated_at = now();
      await writeJsonAtomic(join(this.options.workspace, ".osp-run", "run.json"), failed);
      await checkpoint(this.options.workspace, failed.run_id, phase, "failed", this.sessionId);
      throw error;
    }
  }

  private async waitForApproval(): Promise<void> {
    const deadline = Date.now() + this.options.timeoutMs;
    while (Date.now() < deadline) {
      const state = await this.state();
      if (state.status === "prepared") return;
      if (state.status === "failed" || state.status === "interrupted") throw new Error(`gate ended with status ${state.status}`);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    throw new Error(`collaborative gate was not approved within ${this.options.timeoutMs}ms`);
  }

  private async state(): Promise<any> { return readJson(join(this.options.workspace, ".osp-run", "run.json")); }
}
