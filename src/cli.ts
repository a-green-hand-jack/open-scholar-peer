#!/usr/bin/env node
import { Command } from "commander";
import { mkdir, cp, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { createHash, randomBytes } from "node:crypto";
import { fileURLToPath } from "node:url";
import { execa } from "execa";
import { checkpoint, git, initGit } from "./checkpoints.js";
import { importSource } from "./input.js";
import { now, writeJsonAtomic } from "./fs.js";
import { initialPhases, RunStateSchema } from "./state.js";
import { PHASES } from "./phases.js";
import { validateRun } from "./validation.js";

const program = new Command();
program.name("osp").description("OpenCode-native Open ScholarPeer review agent").version("2.0.0");

function repoRoot(): string {
  return resolve(fileURLToPath(new URL("..", import.meta.url)), "..");
}

async function prepare(source: string, output: string, mode: "autonomous" | "collaborative"): Promise<string> {
  const sourcePath = resolve(source);
  const parent = resolve(output);
  const token = randomBytes(3).toString("hex");
  const runDir = join(parent, `osp-${new Date().toISOString().replace(/[-:.]/g, "").replace("Z", "Z")}-${token}`);
  await mkdir(join(runDir, ".brain", "raw"), { recursive: true });
  await mkdir(join(runDir, ".brain", "review"), { recursive: true });
  await mkdir(join(runDir, ".brain", "tmp"), { recursive: true });
  await cp(join(repoRoot(), ".brain-template", "session.json"), join(runDir, ".brain", "session.json"));
  const canonical = join(repoRoot(), "extensions", "_shared");
  await cp(join(canonical, "commands"), join(runDir, ".opencode", "commands"), { recursive: true });
  await cp(join(canonical, "skills"), join(runDir, ".opencode", "agents"), { recursive: true });
  await cp(join(canonical, "defaults"), join(runDir, ".opencode", "defaults"), { recursive: true });
  await cp(join(canonical, "rules", "osp-rules.md"), join(runDir, ".opencode", "AGENTS.md"));
  await writeFile(join(runDir, "AGENTS.md"), "# Open ScholarPeer Review Workspace\n\nFollow `.opencode/AGENTS.md`. Execute only the controller-selected phase. Never modify `source/`.\n", "utf8");
  const imported = await importSource(sourcePath, runDir);
  const scope = { workflow: [...PHASES], mode, input_digest: imported.digest, source_kind: imported.kind };
  const state = RunStateSchema.parse({
    schema_version: "osp-run-v2", run_id: runDir.split("/").pop(), status: "prepared", mode,
    phases: initialPhases(), current_phase: null, scope,
    scope_digest: createHash("sha256").update(JSON.stringify(scope)).digest("hex"),
    created_at: now(), updated_at: now(), completed_at: null, final_review: null,
  });
  await writeJsonAtomic(join(runDir, ".osp-run", "run.json"), state);
  await writeJsonAtomic(join(runDir, ".osp-run", "source-manifest.json"), imported);
  await initGit(runDir);
  await checkpoint(runDir, state.run_id, "prepared", "prepared");
  return runDir;
}

program.command("review <source>")
  .option("-o, --output <directory>", "parent directory for review workspaces", "osp-review")
  .option("--mode <mode>", "autonomous or collaborative", "autonomous")
  .option("--headless", "run without attaching the TUI")
  .option("--prepare-only", "prepare and validate input without invoking OpenCode")
  .action(async (source: string, options: { output: string; mode: "autonomous" | "collaborative"; prepareOnly?: boolean }) => {
    if (!["autonomous", "collaborative"].includes(options.mode)) throw new Error("--mode must be autonomous or collaborative");
    const runDir = await prepare(source, options.output, options.mode);
    console.log(`Prepared OSP review workspace: ${runDir}`);
    if (options.prepareOnly) return;
    console.log("OpenCode controller execution will be started in the next runtime stage. Use --prepare-only for offline preparation.");
  });

program.command("status <run>").option("--json").action(async (run: string, options: { json?: boolean }) => {
  const state = JSON.parse(await readFile(join(resolve(run), ".osp-run", "run.json"), "utf8"));
  if (options.json) console.log(JSON.stringify(state, null, 2));
  else { console.log(`Run: ${state.run_id}\nStatus: ${state.status}`); for (const [phase, item] of Object.entries(state.phases)) console.log(`  ${phase}: ${(item as { status: string }).status}`); }
});

program.command("validate <run>").option("--json").action(async (run: string, options: { json?: boolean }) => {
  const checks = await validateRun(resolve(run));
  const valid = checks.every((check) => check.passed);
  if (options.json) console.log(JSON.stringify({ valid, checks }, null, 2)); else console.log(checks.map((check) => `${check.passed ? "PASS" : "FAIL"} ${check.name}: ${check.detail}`).join("\n"));
  if (!valid) process.exitCode = 2;
});

program.command("checkpoint <run>").action(async (run: string) => {
  const state = JSON.parse(await readFile(join(resolve(run), ".osp-run", "run.json"), "utf8"));
  console.log(await checkpoint(resolve(run), state.run_id, state.current_phase ?? "prepared", "manual"));
});

program.command("doctor").action(async () => {
  console.log(`node: ${process.version}`);
  try { console.log(`opencode: ${(await execa("opencode", ["--version"])).stdout.trim()}`); } catch { console.log("opencode: not available"); }
});

program.parseAsync().catch((error: unknown) => { console.error(`osp: ${error instanceof Error ? error.message : String(error)}`); process.exitCode = 2; });
