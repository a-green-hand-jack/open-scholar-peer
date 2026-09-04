import { cp, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { allowsMcp, allowsOpenCodeWeb, type NetworkPolicy } from "./network.js";

function projectRoot(): string {
  return resolve(dirname(fileURLToPath(import.meta.url)), "..");
}

/**
 * The MCP server ships as part of the compiled CLI, so a run points at the
 * installed build instead of copying a server and building an environment for
 * it. Nothing is provisioned per run and the runtime needs only Node.
 */
function mcpServerEntry(root: string): string {
  return join(root, "dist", "mcp", "server.js");
}

export async function installRuntimeAssets(workspace: string, networkPolicy: NetworkPolicy, mode: "autonomous" | "collaborative", prepareMcp = true, allowLkmSpend = false, interactive = false): Promise<string> {
  const root = projectRoot();
  const canonical = join(root, "extensions", "_shared");
  await cp(join(canonical, "commands"), join(workspace, ".opencode", "commands"), { recursive: true });
  await cp(join(canonical, "skills"), join(workspace, ".opencode", "agents"), { recursive: true });
  await cp(join(canonical, "defaults"), join(workspace, ".opencode", "defaults"), { recursive: true });
  await cp(join(canonical, "rules", "osp-rules.md"), join(workspace, ".opencode", "AGENTS.md"));
  const enableMcp = prepareMcp && allowsMcp(networkPolicy);
  const allowWeb = allowsOpenCodeWeb(networkPolicy);
  const allowQuestions = mode === "collaborative" && interactive;
  const serverEntry = mcpServerEntry(root);
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
    // `env` prefixes the command rather than using OpenCode's `environment`
    // field so the server still inherits the parent environment, which is how
    // SEMANTIC_SCHOLAR_API_KEY reaches it. Naming the key here instead would
    // write it into opencode.json, and phase checkpoints commit that file.
    mcp: enableMcp ? { osp: { type: "local", command: ["env", `OSP_ALLOW_LKM_SPEND=${allowLkmSpend ? "1" : "0"}`, `OSP_NETWORK_POLICY=${networkPolicy}`, `OSP_WORKSPACE_ROOT=${workspace}`, "node", serverEntry], enabled: true } } : {},
  };
  await writeFile(join(workspace, "opencode.json"), `${JSON.stringify(config, null, 2)}\n`, "utf8");
  return serverEntry;
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
