import { describe, expect, it } from "vitest";
import { readFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { installRuntimeAssets } from "../src/config.js";

describe("OpenCode interaction policy", () => {
  it("does not deadlock autonomous headless runs on questions", async () => {
    const directory = await mkdtemp(join(tmpdir(), "osp-config-"));
    try {
      await installRuntimeAssets(directory, "online", "autonomous", false);
      const config = JSON.parse(await readFile(join(directory, "opencode.json"), "utf8"));
      expect(config.permission.question).toBe("deny");
    } finally { await rm(directory, { recursive: true, force: true }); }
  });
});
