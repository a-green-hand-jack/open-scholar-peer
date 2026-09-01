import { mkdir, cp, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

function projectRoot(): string {
  return resolve(dirname(fileURLToPath(import.meta.url)), "..");
}

export async function installRuntimeAssets(workspace: string, networkPolicy: "online" | "offline"): Promise<string> {
  const root = projectRoot();
  const canonical = join(root, "extensions", "_shared");
  await cp(join(canonical, "commands"), join(workspace, ".opencode", "commands"), { recursive: true });
  await cp(join(canonical, "skills"), join(workspace, ".opencode", "agents"), { recursive: true });
  await cp(join(canonical, "defaults"), join(workspace, ".opencode", "defaults"), { recursive: true });
  await cp(join(canonical, "rules", "osp-rules.md"), join(workspace, ".opencode", "AGENTS.md"));
  const mcpRoot = join(workspace, ".open-scholar-peer", "mcp");
  await mkdir(mcpRoot, { recursive: true });
  await cp(join(root, "mcp-server"), mcpRoot, { recursive: true });
  const python = process.env.PYTHON ?? "python3";
  const config = {
    $schema: "https://opencode.ai/config.json",
    share: "disabled",
    permission: {
      "*": "deny", read: "allow", glob: "allow", grep: "allow", edit: "allow", write: "allow", patch: "allow", task: "allow",
      webfetch: networkPolicy === "offline" ? "deny" : "allow", websearch: networkPolicy === "offline" ? "deny" : "allow",
      external_directory: "deny", question: "allow", bash: "deny",
    },
    agent: {
      "osp-runner": {
        mode: "primary", description: "Open ScholarPeer phase executor",
        permission: { "*": "deny", read: "allow", glob: "allow", grep: "allow", edit: "allow", write: "allow", patch: "allow", task: "allow", webfetch: networkPolicy === "offline" ? "deny" : "allow", websearch: networkPolicy === "offline" ? "deny" : "allow", external_directory: "deny", question: "allow", bash: "deny" },
      },
    },
    mcp: { osp: { type: "local", command: [python, join(mcpRoot, "osp_mcp.py")], enabled: true } },
  };
  await writeFile(join(workspace, "opencode.json"), `${JSON.stringify(config, null, 2)}\n`, "utf8");
  return join(mcpRoot, "osp_mcp.py");
}
