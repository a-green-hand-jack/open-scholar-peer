#!/usr/bin/env node
import { Command } from "commander";
import { mkdir, cp, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { createHash, randomBytes } from "node:crypto";
import { fileURLToPath } from "node:url";
import { execa } from "execa";
import { checkpoint, initGit } from "./checkpoints.js";
import { digest, importSource, importedFiles } from "./input.js";
import { now, writeJsonAtomic } from "./fs.js";
import { initialPhases, RunStateSchema } from "./state.js";
import { PHASES } from "./phases.js";
import { validateRun } from "./validation.js";
import { ReviewController } from "./controller.js";
import { installRuntimeAssets, setQuestionPolicy } from "./config.js";
import { CONTRACTS, collectProvenance, packageVersion } from "./provenance.js";
import { resolveRun } from "./discover.js";
import { uploadTrail, writeTrail } from "./trail.js";

import { exportFinalReview } from "./delivery.js";
import { NETWORK_POLICIES, type NetworkPolicy } from "./network.js";
const program = new Command();
program.name("osp").description("OpenCode-native Open ScholarPeer review agent").version("2.2.0");

function repoRoot(): string {
  return resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
}

async function prepare(source: string, output: string, mode: "autonomous" | "collaborative", networkPolicy: NetworkPolicy, model?: string, variant?: string, allowLkmSpend = false, interactive = false): Promise<string> {
  const sourcePath = resolve(source);
  const parent = resolve(output);
  const token = randomBytes(3).toString("hex");
  const runDir = join(parent, `osp-${new Date().toISOString().replace(/[-:.]/g, "").replace("Z", "Z")}-${token}`);
  await mkdir(join(runDir, ".brain", "raw"), { recursive: true });
  await mkdir(join(runDir, ".brain", "review"), { recursive: true });
  await mkdir(join(runDir, ".brain", "tmp"), { recursive: true });
  await cp(join(repoRoot(), ".brain-template", "session.json"), join(runDir, ".brain", "session.json"));
  await installRuntimeAssets(runDir, networkPolicy, mode, true, allowLkmSpend, interactive);
  const sessionPath = join(runDir, ".brain", "session.json");
  const session = JSON.parse(await readFile(sessionPath, "utf8"));
  try {
    const result = await execa("bohr", ["auth", "status"]);
    const status = JSON.parse(result.stdout) as { data?: { logged_in?: boolean } };
    session.mcp.bohrium_available = status.data?.logged_in === true;
  } catch {
    session.mcp.bohrium_available = false;
  }
  await writeJsonAtomic(sessionPath, session);
  await writeFile(join(runDir, "AGENTS.md"), "# Open ScholarPeer Review Workspace\n\nFollow `.opencode/AGENTS.md`. Execute only the controller-selected phase. Never modify `source/`.\n", "utf8");
  const imported = await importSource(sourcePath, runDir);
  const provenance = await collectProvenance(repoRoot());
  session.osp = { version: provenance.osp_version, commit: provenance.osp_commit, contracts: CONTRACTS };
  await writeJsonAtomic(sessionPath, session);
  const scope = { workflow: [...PHASES], mode, network_policy: networkPolicy, allow_lkm_spend: allowLkmSpend, model: model ?? null, variant: variant ?? null, input_digest: imported.digest, source_kind: imported.kind };
  const state = RunStateSchema.parse({
    schema_version: "osp-run-v2", run_id: runDir.split("/").pop(), status: "prepared", mode,
    phases: initialPhases(), current_phase: null, scope,
    scope_digest: createHash("sha256").update(JSON.stringify(scope)).digest("hex"),
    provenance: { ...provenance, started_at: now(), status: "prepared", network_policy: networkPolicy, mode, model: model ?? null, variant: variant ?? null },
    created_at: now(), updated_at: now(), completed_at: null, final_review: null,
  });
  await writeJsonAtomic(join(runDir, ".osp-run", "run.json"), state);
  await writeJsonAtomic(join(runDir, ".osp-run", "provenance.json"), state.provenance);
  await writeJsonAtomic(join(runDir, ".osp-run", "source-manifest.json"), imported);
  await initGit(runDir);
  await checkpoint(runDir, state.run_id, "prepared", "prepared");
  return runDir;
}

type DeliveryOptions = { finalOutput?: string; trail?: string; trailRepo?: string; upload?: boolean };

function checkDelivery(options: DeliveryOptions): void {
  if (options.upload && (!options.trail || !options.trailRepo))
    throw new Error("--upload requires both --trail and --trail-repo so review content has an explicit destination");
}

/**
 * Publish the run's stable outputs. The final review is exported to a fixed,
 * documented path next to the run directory so unattended consumers never have
 * to guess a timestamped run id.
 */
async function deliver(runDir: string, options: DeliveryOptions): Promise<void> {
  const delivery = await exportFinalReview(runDir, options.finalOutput);
  console.log(`Final review: ${delivery.canonicalReview}`);
  if (delivery.submittedReview) console.log(`Submission review: ${delivery.submittedReview}`);
  if (!options.trail) return;
  const trail = await writeTrail(runDir, options.trail);
  console.log(`Trail: ${trail}`);
  if (!options.upload) return;
  console.log(`Uploading review content to ${options.trailRepo}; this publishes the review outside this machine.`);
  await uploadTrail(trail, options.trailRepo!);
  console.log(`Uploaded trail to ${options.trailRepo}`);
}

async function verifyRun(workspace: string): Promise<any> {
  const state = RunStateSchema.parse(JSON.parse(await readFile(join(workspace, ".osp-run", "run.json"), "utf8")));
  const manifest = JSON.parse(await readFile(join(workspace, ".osp-run", "source-manifest.json"), "utf8")) as { digest: string };
  const sourceFiles = await importedFiles(join(workspace, "source"));
  if (await digest(sourceFiles, join(workspace, "source")) !== manifest.digest) throw new Error("imported source changed since the last checkpoint; resume is refused");
  const scopeDigest = createHash("sha256").update(JSON.stringify(state.scope)).digest("hex");
  if (scopeDigest !== state.scope_digest) throw new Error("run scope changed since creation; resume is refused");
  return state;
}

program.command("review <source>")
  .option("-o, --output <directory>", "parent directory for review workspaces", "osp-review")
  .option("--mode <mode>", "autonomous or collaborative", "autonomous")
  .option("--headless", "run without attaching the TUI")
  .option("--prepare-only", "prepare and validate input without invoking OpenCode")
  .option("--model <model>", "provider/model reference")
  .option("--variant <variant>", "OpenCode model variant")
  .option("--timeout <seconds>", "phase timeout", "1800")
  .option("--qa-pairs <count>", "ordered Q&A pairs per criterion", "2")
  .option("--network-policy <policy>", "scholarly, online, or offline", "scholarly")
  .option("--allow-lkm-spend", "authorize billable Bohrium LKM calls for this run")
  .option("--trail <directory>", "write an immutable local trail entry for the completed run")
  .option("--final-output <path>", "copy the completed review to this explicit path")
  .option("--trail-repo <repository>", "Hugging Face dataset repository for --upload")
  .option("--upload", "publish the trail entry to --trail-repo (requires --trail)")
  .action(async (source: string, options: { output: string; mode: "autonomous" | "collaborative"; headless?: boolean; prepareOnly?: boolean; model?: string; variant?: string; timeout: string; qaPairs: string; networkPolicy: NetworkPolicy; allowLkmSpend?: boolean } & DeliveryOptions) => {
    if (!["autonomous", "collaborative"].includes(options.mode)) throw new Error("--mode must be autonomous or collaborative");
    if (!NETWORK_POLICIES.includes(options.networkPolicy)) throw new Error("--network-policy must be scholarly, online, or offline");
    checkDelivery(options);
    const runDir = await prepare(source, options.output, options.mode, options.networkPolicy, options.model, options.variant, Boolean(options.allowLkmSpend), !options.headless);
    const sessionPath = join(runDir, ".brain", "session.json");
    const session = JSON.parse(await readFile(sessionPath, "utf8"));
    const qaPairs = Number(options.qaPairs);
    if (!Number.isInteger(qaPairs) || qaPairs < 1) throw new Error("--qa-pairs must be a positive integer");
    session.qa_pairs_per_criterion = qaPairs;
    await writeJsonAtomic(sessionPath, session);
    console.log(`Prepared OSP review workspace: ${runDir}`);
    if (options.prepareOnly) return;
    const outcome = await new ReviewController({ workspace: runDir, mode: options.mode, headless: Boolean(options.headless), model: options.model, variant: options.variant, timeoutMs: Number(options.timeout) * 1000 }).run();
    if (outcome === "gate_waiting") {
      console.log(`Review is waiting for approval: ${runDir}`);
      return;
    }
    console.log(`Review complete: ${join(runDir, ".brain", "review", "final_review.md")}`);
    await deliver(runDir, options);
  });

program.command("status [run]").option("--json").action(async (run: string | undefined, options: { json?: boolean }) => {
  const workspace = await resolveRun(run);
  const state = JSON.parse(await readFile(join(workspace, ".osp-run", "run.json"), "utf8"));
  if (options.json) console.log(JSON.stringify(state, null, 2));
  else {
    console.log(`Run: ${state.run_id}\nWorkspace: ${workspace}\nStatus: ${state.status}\nMode: ${state.mode}\nOSP: ${state.provenance?.osp_version ?? "unknown"} (${state.provenance?.osp_commit ?? "no commit"})`);
    for (const [phase, item] of Object.entries(state.phases)) console.log(`  ${phase}: ${(item as { status: string }).status}`);
  }
});

program.command("validate [run]").option("--json").action(async (run: string | undefined, options: { json?: boolean }) => {
  const checks = await validateRun(await resolveRun(run));
  const valid = checks.every((check) => check.passed);
  if (options.json) console.log(JSON.stringify({ valid, checks }, null, 2)); else console.log(checks.map((check) => `${check.passed ? "PASS" : "FAIL"} ${check.name}: ${check.detail}`).join("\n"));
  if (!valid) process.exitCode = 2;
});

program.command("checkpoint [run]").action(async (run: string | undefined) => {
  const workspace = await resolveRun(run);
  const state = JSON.parse(await readFile(join(workspace, ".osp-run", "run.json"), "utf8"));
  console.log(await checkpoint(workspace, state.run_id, state.current_phase ?? "prepared", "manual"));
});

for (const commandName of ["start", "resume"]) {
  program.command(`${commandName} [run]`)
    .option("--headless")
    .option("--timeout <seconds>", "phase timeout", "1800")
    .option("--trail <directory>", "write an immutable local trail entry for the completed run")
    .option("--trail-repo <repository>", "Hugging Face dataset repository for --upload")
    .option("--final-output <path>", "copy the completed review to this explicit path")
    .option("--upload", "publish the trail entry to --trail-repo (requires --trail)")
    .action(async (run: string | undefined, options: { headless?: boolean; timeout: string } & DeliveryOptions) => {
      checkDelivery(options);
      const workspace = await resolveRun(run);
      const state = await verifyRun(workspace);
      if (state.status === "completed") { console.log("Review is already completed."); await deliver(workspace, options); return; }
      const outcome = await new ReviewController({ workspace, mode: state.mode, headless: Boolean(options.headless), model: state.scope.model ?? undefined, variant: state.scope.variant ?? undefined, timeoutMs: Number(options.timeout) * 1000 }).run();
      if (outcome === "gate_waiting") {
        console.log(`Review is waiting for approval: ${workspace}`);
        return;
      }
      console.log(`Review complete: ${join(workspace, ".brain", "review", "final_review.md")}`);
      await deliver(workspace, options);
    });
}

program.command("approve [run]").action(async (run: string | undefined) => {
  const path = join(await resolveRun(run), ".osp-run", "run.json");
  const state = JSON.parse(await readFile(path, "utf8"));
  if (state.status !== "gate_waiting") throw new Error(`run is not waiting for approval (status=${state.status})`);
  state.status = "prepared";
  state.updated_at = now();
  await writeJsonAtomic(path, state);
  console.log(`Approved gate for ${state.current_phase}`);
});

program.command("mode [run] [mode]")
  .description("show or change the gate policy for the remaining phases")
  .action(async (run: string | undefined, requested: string | undefined) => {
    // `osp mode collaborative` — a bare mode word is the mode, not a run path.
    if (!requested && run && ["autonomous", "collaborative"].includes(run)) { requested = run; run = undefined; }
    const workspace = await resolveRun(run);
    const path = join(workspace, ".osp-run", "run.json");
    const state = RunStateSchema.parse(JSON.parse(await readFile(path, "utf8")));
    if (!requested) { console.log(state.mode); return; }
    if (!["autonomous", "collaborative"].includes(requested)) throw new Error("mode must be autonomous or collaborative");
    if (state.status === "running") throw new Error("cannot change mode while a phase is running; interrupt the run first");
    if (state.mode === requested) { console.log(`Already ${requested}`); return; }
    // Only the gate policy moves. The locked scope, plan and input digest are
    // part of scope_digest and are deliberately left untouched.
    state.mode = requested as "autonomous" | "collaborative";
    state.updated_at = now();
    await writeJsonAtomic(path, state);
    await setQuestionPolicy(workspace, requested === "collaborative");
    await checkpoint(workspace, state.run_id, state.current_phase as never ?? "prepared", `mode-${requested}`);
    console.log(`Gate policy for the remaining phases is now ${requested}; the locked run scope is unchanged.`);
  });

program.command("doctor").action(async () => {
  const checks: Array<{ name: string; passed: boolean; required: boolean; detail: string }> = [];
  const probe = async (name: string, required: boolean, command: string, args: string[], detail?: (stdout: string) => string) => {
    try {
      const result = await execa(command, args, { all: true });
      const stdout = (result.stdout.trim() || result.all?.trim() || "").trim();
      checks.push({ name, passed: true, required, detail: detail ? detail(stdout) : stdout.split("\n")[0] || "available" });
    } catch { checks.push({ name, passed: false, required, detail: "not available" }); }
  };
  const nodeMajor = Number(process.versions.node.split(".")[0]);
  checks.push({ name: "node", passed: nodeMajor >= 20, required: true, detail: `${process.version} (requires >= 20)` });
  checks.push({ name: "osp", passed: true, required: true, detail: `${await packageVersion(repoRoot())} (contracts brain=${CONTRACTS.brain_layout} artifact=${CONTRACTS.artifact_contract})` });
  await probe("opencode", true, "opencode", ["--version"]);
  await probe("git", true, "git", ["--version"]);
  await probe("pdftotext", true, "pdftotext", ["-v"], (stdout) => stdout.split("\n")[0]);
  // pdfinfo bounds the LKM PDF page limit inside the MCP server. It ships with
  // pdftotext in Poppler, but only matters when Bohrium extraction is used.
  await probe("pdfinfo", false, "pdfinfo", ["-v"], (stdout) => stdout.split("\n")[0]);
  try {
    const result = await execa("bohr", ["auth", "status"]);
    const status = JSON.parse(result.stdout) as { data?: { logged_in?: boolean } };
    if (status.data?.logged_in === true) checks.push({ name: "bohr", passed: true, required: false, detail: "authenticated (LKM enabled)" });
    else checks.push({ name: "bohr", passed: false, required: false, detail: "installed but not authenticated (LKM fallback-only)" });
  } catch {
    try { await execa("bohr", ["--version"], { stdio: "ignore" }); checks.push({ name: "bohr", passed: false, required: false, detail: "installed but not authenticated (LKM fallback-only)" }); }
    catch { checks.push({ name: "bohr", passed: false, required: false, detail: "not available (LKM fallback-only)" }); }
  }
  await probe("hf", false, "hf", ["version"]);
  for (const check of checks) console.log(`${check.passed ? "PASS" : check.required ? "FAIL" : "WARN"} ${check.name}: ${check.detail}`);
  if (checks.some((check) => check.required && !check.passed)) {
    console.error("osp: required dependencies are missing");
    process.exitCode = 2;
  }
});

program.parseAsync().catch((error: unknown) => { console.error(`osp: ${error instanceof Error ? error.message : String(error)}`); process.exitCode = 2; });
