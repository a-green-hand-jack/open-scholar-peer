import { mkdir, cp, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { execa } from "execa";
import { allowsMcp, allowsOpenCodeWeb, type NetworkPolicy } from "./network.js";

function projectRoot(): string {
  return resolve(dirname(fileURLToPath(import.meta.url)), "..");
}

async function venvPython(): Promise<string> {
  const candidates = [process.env.PYTHON, "python3.13", "python3.12", "python3.11", "python3"].filter((value): value is string => Boolean(value));
  for (const candidate of [...new Set(candidates)]) {
    try { await execa(candidate, ["-c", "import ensurepip"]); return candidate; } catch { /* try next interpreter */ }
  }
  throw new Error("no Python interpreter with ensurepip is available");
}

export async function installRuntimeAssets(workspace: string, networkPolicy: NetworkPolicy, mode: "autonomous" | "collaborative", prepareMcp = true, allowLkmSpend = false, interactive = false): Promise<string> {
  const root = projectRoot();
  const canonical = join(root, "extensions", "_shared");
  await cp(join(canonical, "commands"), join(workspace, ".opencode", "commands"), { recursive: true });
  await cp(join(canonical, "skills"), join(workspace, ".opencode", "agents"), { recursive: true });
  await cp(join(canonical, "defaults"), join(workspace, ".opencode", "defaults"), { recursive: true });
  await cp(join(canonical, "rules", "osp-rules.md"), join(workspace, ".opencode", "AGENTS.md"));
  const mcpRoot = join(workspace, ".open-scholar-peer", "mcp");
  await mkdir(mcpRoot, { recursive: true });
  await cp(join(root, "mcp-server"), mcpRoot, { recursive: true });
  const enableMcp = prepareMcp && allowsMcp(networkPolicy);
  const allowWeb = allowsOpenCodeWeb(networkPolicy);
  const allowQuestions = mode === "collaborative" && interactive;
  const pythonBase = enableMcp ? await venvPython() : "python3";
  const venv = join(mcpRoot, ".venv");
  let python = pythonBase;
  if (enableMcp) {
    python = join(venv, "bin", "python");
    try {
      await execa(pythonBase, ["-m", "venv", venv]);
      await execa(python, ["-m", "pip", "install", "--quiet", "-r", join(mcpRoot, "requirements.txt")]);
    } catch (error) {
      throw new Error(`could not prepare isolated MCP runtime: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  const config = {
    $schema: "https://opencode.ai/config.json",
    share: "disabled",
    permission: {
      "*": "deny", read: "allow", glob: "allow", grep: "allow", edit: "allow", write: "allow", patch: "allow", task: "allow", "osp_*": "allow",
      webfetch: allowWeb ? "allow" : "deny", websearch: allowWeb ? "allow" : "deny",
      external_directory: "deny", question: allowQuestions ? "allow" : "deny", bash: "deny",
    },
    agent: {
      "osp-runner": {
        mode: "primary", description: "Open ScholarPeer phase executor",
        permission: { "*": "deny", read: "allow", glob: "allow", grep: "allow", edit: "allow", write: "allow", patch: "allow", task: "allow", "osp_*": "allow", webfetch: allowWeb ? "allow" : "deny", websearch: allowWeb ? "allow" : "deny", external_directory: "deny", question: allowQuestions ? "allow" : "deny", bash: "deny" },
      },
    },
     mcp: enableMcp ? { osp: { type: "local", command: ["env", `OSP_ALLOW_LKM_SPEND=${allowLkmSpend ? "1" : "0"}`, `OSP_NETWORK_POLICY=${networkPolicy}`, `OSP_WORKSPACE_ROOT=${workspace}`, python, join(mcpRoot, "osp_mcp.py")], enabled: true } } : {},
  };
  await writeFile(join(workspace, "opencode.json"), `${JSON.stringify(config, null, 2)}\n`, "utf8");
  return join(mcpRoot, "osp_mcp.py");
}

/**
 * Single-persona phases run inline; only Q&A needs its answer subagent, so the
 * `task` permission is granted for that phase alone.
 */
export async function setPhaseTaskPolicy(workspace: string, phase: string): Promise<void> {
  const path = join(workspace, "opencode.json");
  const config = JSON.parse(await readFile(path, "utf8")) as { permission: Record<string, string>; agent: Record<string, { permission: Record<string, string> }> };
  const action = phase === "qa" ? "allow" : "deny";
  config.permission.task = action;
  config.agent["osp-runner"].permission.task = action;
  await writeFile(path, `${JSON.stringify(config, null, 2)}\n`, "utf8");
}

/** Keep interactive questions unavailable in autonomous and headless runs. */
export async function setQuestionPolicy(workspace: string, allowed: boolean): Promise<void> {
  const path = join(workspace, "opencode.json");
  const config = JSON.parse(await readFile(path, "utf8")) as { permission: Record<string, string>; agent: Record<string, { permission: Record<string, string> }> };
  const action = allowed ? "allow" : "deny";
  config.permission.question = action;
  config.agent["osp-runner"].permission.question = action;
  await writeFile(path, `${JSON.stringify(config, null, 2)}\n`, "utf8");
}
