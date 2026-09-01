import { createReadStream } from "node:fs";
import { mkdir, chmod, cp, readdir, readFile, stat } from "node:fs/promises";
import { basename, join, relative, resolve } from "node:path";
import { createHash } from "node:crypto";
import { execa } from "execa";

const SENSITIVE = /(^|\/)(\.env(?:\.|$)|\.npmrc$|\.netrc$|auth\.json$|id_(?:rsa|ed25519|ecdsa)$|.*\.(?:pem|key|p12|pfx)$|.*(?:token|secret|credential).*(?:json|ya?ml|toml)?$)/i;
const ALLOWED = new Set([".tex", ".bib", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".sty", ".cls", ".bst", ".csv", ".tsv", ".md", ".txt"]);

export async function importedFiles(root: string): Promise<string[]> {
  const result: string[] = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    const rel = relative(root, path).replaceAll("\\", "/");
    if (SENSITIVE.test(rel) || [".git", ".brain", ".osp-run", ".open-scholar-peer"].includes(entry.name)) continue;
    if (entry.isSymbolicLink()) throw new Error(`symbolic links are not supported: ${rel}`);
    if (entry.isDirectory()) result.push(...await importedFiles(path));
    else if (entry.isFile()) result.push(path);
    else throw new Error(`special files are not supported: ${rel}`);
  }
  return result;
}

export async function digest(paths: string[], root: string): Promise<string> {
  const hash = createHash("sha256");
  for (const path of paths.sort()) {
    hash.update(relative(root, path).replaceAll("\\", "/"));
    hash.update("\0");
    hash.update(await readFile(path));
    hash.update("\n");
  }
  return hash.digest("hex");
}

export async function importSource(sourceArg: string, workspace: string): Promise<{ kind: string; digest: string; source: string }> {
  const source = resolve(sourceArg);
  const sourceStat = await stat(source);
  const sourceRoot = join(workspace, "source");
  const inputRoot = join(workspace, ".brain", "input");
  await mkdir(sourceRoot, { recursive: true });
  await mkdir(inputRoot, { recursive: true });
  if (sourceStat.isFile() && source.toLowerCase().endsWith(".pdf")) {
    await cp(source, join(sourceRoot, "paper.pdf"));
    await cp(source, join(inputRoot, "paper.pdf"));
    try { await execa("pdftotext", ["-layout", join(sourceRoot, "paper.pdf"), join(inputRoot, "paper.md")]); }
    catch { throw new Error("could not convert PDF; install Poppler pdftotext"); }
    const sourceFiles = await importedFiles(sourceRoot);
    return { kind: "pdf", digest: await digest(sourceFiles, sourceRoot), source: source };
  }
  let importRoot = source;
  let kind = "tex-directory";
  if (sourceStat.isFile() && /\.(zip|tar|tgz|tar\.gz)$/i.test(source)) {
    importRoot = join(workspace, ".archive-staging");
    await mkdir(importRoot, { recursive: true });
    const command = source.toLowerCase().endsWith(".zip") ? "unzip" : "tar";
    try {
      if (command === "unzip") {
        const listing = await execa("unzip", ["-Z1", source]);
        for (const member of listing.stdout.split("\n").filter(Boolean)) {
          const target = resolve(importRoot, member);
          if (target !== importRoot && !target.startsWith(`${importRoot}/`)) throw new Error(`archive path escapes workspace: ${member}`);
        }
        await execa("unzip", ["-q", source, "-d", importRoot]);
      } else {
        const listing = await execa("tar", ["-tzf", source]);
        for (const member of listing.stdout.split("\n").filter(Boolean)) {
          const target = resolve(importRoot, member);
          if (target !== importRoot && !target.startsWith(`${importRoot}/`)) throw new Error(`archive path escapes workspace: ${member}`);
        }
        if (listing.stdout.split("\n").some((member) => member.startsWith("../") || member.includes("/../"))) throw new Error("archive contains an unsafe path");
        await execa("tar", ["-xzf", source, "-C", importRoot]);
      }
    } catch (error) { throw new Error(`could not safely extract archive: ${error instanceof Error ? error.message : String(error)}`); }
    const entries = await readdir(importRoot, { withFileTypes: true });
    if (entries.length === 1 && entries[0].isDirectory()) importRoot = join(importRoot, entries[0].name);
    kind = "archive";
  }
  if (!sourceStat.isDirectory() && kind !== "archive") throw new Error("expected a PDF, TeX directory, or source archive");
  const sourceFiles = await importedFiles(importRoot);
  const paperFiles = sourceFiles.filter((path) => ALLOWED.has(path.slice(path.lastIndexOf(".")).toLowerCase()) || basename(path).toLowerCase() === "makefile");
  if (!paperFiles.some((path) => path.endsWith(".tex") || path.endsWith(".pdf") || basename(path) === "paper.md")) throw new Error("source directory contains neither TeX files, paper.md, nor PDF");
  for (const path of paperFiles) await cp(path, join(sourceRoot, relative(importRoot, path)));
  const paper = paperFiles.find((path) => basename(path) === "paper.md") ?? paperFiles.find((path) => path.endsWith(".pdf"));
  if (paper && paper.endsWith(".pdf")) {
    await cp(join(sourceRoot, relative(importRoot, paper)), join(inputRoot, "paper.pdf"));
    try { await execa("pdftotext", ["-layout", join(inputRoot, "paper.pdf"), join(inputRoot, "paper.md")]); } catch { throw new Error("could not convert source PDF"); }
  } else if (paper) await cp(join(sourceRoot, relative(importRoot, paper)), join(inputRoot, "paper.md"));
  else await (await import("node:fs/promises")).writeFile(join(inputRoot, "paper.md"), "# Imported TeX source\n\n" + (await Promise.all(paperFiles.filter((path) => path.endsWith(".tex")).map(async (path) => `## Source: ${relative(importRoot, path)}\n\n${await readFile(path, "utf8")}`))).join("\n"));
  for (const path of await importedFiles(sourceRoot)) await chmod(path, 0o444);
  const imported = await importedFiles(sourceRoot);
  return { kind, digest: await digest(imported, sourceRoot), source };
}
