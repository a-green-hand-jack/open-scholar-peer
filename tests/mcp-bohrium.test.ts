import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

// execa is mocked so no test can reach the real `bohr` CLI or spend money.
const execa = vi.hoisted(() => vi.fn());
vi.mock("execa", () => ({ execa }));

const { searchLkm, parseSubmit, getPaperGraph } = await import("../src/mcp/providers/bohrium.js");

async function workspaceWithPdf(): Promise<{ workspace: string; pdf: string }> {
  const workspace = await mkdtemp(join(tmpdir(), "osp-bohr-"));
  const input = join(workspace, ".brain", "input");
  await mkdir(input, { recursive: true });
  const pdf = join(input, "paper.pdf");
  await writeFile(pdf, "%PDF-1.4\n");
  return { workspace, pdf };
}

describe("bohrium LKM guards", () => {
  beforeEach(() => {
    execa.mockReset();
    delete process.env.OSP_ALLOW_LKM_SPEND;
    delete process.env.OSP_WORKSPACE_ROOT;
  });
  afterEach(() => {
    delete process.env.OSP_ALLOW_LKM_SPEND;
    delete process.env.OSP_WORKSPACE_ROOT;
  });

  it("refuses billable calls without --allow-lkm-spend and never invokes bohr", async () => {
    const result = await searchLkm("anything", 1);
    expect(result).toEqual({
      error: "LKM spending is not authorized for this run; pass --allow-lkm-spend to osp review",
    });
    expect(execa).not.toHaveBeenCalled();
  });

  it("gates the paper graph too, since graph calls are billable", async () => {
    const result = await getPaperGraph("paper-1");
    expect(result).toEqual({
      error: "LKM spending is not authorized for this run; pass --allow-lkm-spend to osp review",
    });
    expect(execa).not.toHaveBeenCalled();
  });

  it("rejects a PDF over the page limit before spending, and probes pdfinfo exactly once", async () => {
    process.env.OSP_ALLOW_LKM_SPEND = "1";
    const { workspace, pdf } = await workspaceWithPdf();
    process.env.OSP_WORKSPACE_ROOT = workspace;
    execa.mockResolvedValue({ exitCode: 0, failed: false, timedOut: false, stdout: "Pages:          51\n" });

    const result = await parseSubmit(pdf);

    expect(result).toEqual({ error: "PDF exceeds the 50-page LKM extraction limit" });
    expect(execa).toHaveBeenCalledTimes(1);
    const [command, args, options] = execa.mock.calls[0];
    expect(command).toBe("pdfinfo");
    expect(args).toEqual([pdf]);
    expect(options).toMatchObject({ timeout: 10_000, reject: false });
  });

  it("refuses a PDF outside .brain/input even when spending is authorized", async () => {
    process.env.OSP_ALLOW_LKM_SPEND = "1";
    const { workspace } = await workspaceWithPdf();
    process.env.OSP_WORKSPACE_ROOT = workspace;
    const outside = join(workspace, "elsewhere.pdf");
    await writeFile(outside, "%PDF-1.4\n");

    const result = await parseSubmit(outside);

    expect(result).toEqual({ error: "pdf_path must be a regular PDF directly under .brain/input" });
    expect(execa).not.toHaveBeenCalled();
  });

  it("refuses submission when no workspace is configured", async () => {
    process.env.OSP_ALLOW_LKM_SPEND = "1";
    const result = await parseSubmit("/etc/passwd");
    expect(result).toEqual({ error: "OSP_WORKSPACE_ROOT is not configured" });
    expect(execa).not.toHaveBeenCalled();
  });
});
