import { execa } from "execa";
import { now } from "./fs.js";
import type { Phase } from "./phases.js";

export async function git(cwd: string, ...args: string[]): Promise<string> {
  const result = await execa("git", args, { cwd });
  return result.stdout.trim();
}

export async function initGit(cwd: string): Promise<void> {
  try {
    await git(cwd, "rev-parse", "--git-dir");
  } catch {
    await git(cwd, "init", "--quiet");
    await git(cwd, "config", "user.email", "osp@localhost");
    await git(cwd, "config", "user.name", "OSP Agent");
  }
}

export async function checkpoint(cwd: string, runId: string, phase: Phase | "prepared" | "completed" | "failed", status: string, sessionId = "none"): Promise<string> {
  await git(cwd, "add", "-A");
  await git(cwd, "commit", "--allow-empty", "-m", `OSP: ${phase} — ${status}`, "-m", [
    `OSP-Run: ${runId}`,
    `OSP-Phase: ${phase}`,
    `OSP-Status: ${status}`,
    `OSP-Session: ${sessionId}`,
    `OSP-Timestamp: ${now()}`,
  ].join("\n"));
  return git(cwd, "rev-parse", "HEAD");
}
