import { describe, expect, it } from "vitest";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { installRuntimeAssets } from "../src/config.js";
import { allowsMcp, allowsOpenCodeWeb } from "../src/network.js";

describe("benchmark network policies", () => {
  it("keeps scholarly runs on the MCP path while denying generic web tools", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-scholarly-config-"));
    try {
      await installRuntimeAssets(directory, "scholarly", "autonomous", false);
      const config = JSON.parse(await readFile(join(directory, "opencode.json"), "utf8"));
      expect(allowsMcp("scholarly")).toBe(true);
      expect(allowsOpenCodeWeb("scholarly")).toBe(false);
      expect(config.permission.webfetch).toBe("deny");
      expect(config.permission.websearch).toBe("deny");
      expect(config.permission.question).toBe("deny");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });

  it("permits native questions only for an interactive collaborative run", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-collaborative-config-"));
    try {
      await installRuntimeAssets(directory, "scholarly", "collaborative", false, false, true);
      const config = JSON.parse(await readFile(join(directory, "opencode.json"), "utf8"));
      expect(config.permission.question).toBe("allow");
      expect(config.agent["osp-runner"].permission.question).toBe("allow");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });
});
