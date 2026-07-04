# Known Limitations — Open ScholarPeer v2

These are limitations users should know about going in. None block normal operation, but each affects the quality or smoothness of specific phases. Workarounds are listed.

---

## 1. Some tools fall back to self-reflection for the Q&A engine

**What:** The Multi-Aspect Q&A Engine (`/5-osp-qa`) is designed around true subagent isolation: the Query Agent (main thread) delegates each question to a fresh Answer Generator subagent so the verification cannot be biased by the question's reasoning trace.

**Limitation:** Three of the supported tools — **Antigravity** (legacy desktop app), **Mistral Vibe**, and **OpenHands** — either do not support subagents or have only profile-style independence (no documented subagent delegation). On these, the Q&A engine falls back to **self-reflection mode**: both Query and Answer Generator personas run in the same context window, separated by strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`).

**Impact:** Reviews on the Q&A axis from these tools are likely lower in independent-verification depth than reviews from Claude Code, Cursor, Gemini CLI, Antigravity CLI, Copilot CLI, Codex CLI, Qwen Code, OpenCode, Junie, Kiro, or Kimi Code. The other downstream phases (literature, historian, baseline scout, reviewer) are unaffected.

**Workaround:** If you need full subagent isolation for a paper, use one of the subagent-capable tools listed above.

---

## 2. Semantic Scholar anonymous rate limits are aggressive

**What:** The `osp_mcp.search_semantic_scholar` and related tools use the official Semantic Scholar API. Without an API key, anonymous limits apply (~100 requests / 5 min, frequently bursty 429s).

**Impact:** During the 3-round literature retrieval (`/2-osp-literature`), an anonymous user may hit rate limits mid-round, causing partial corpora.

**Workaround:** Get a free API key at https://www.semanticscholar.org/product/api#api-key and export it before launching your AI tool:

```bash
export SEMANTIC_SCHOLAR_API_KEY=sk-...
```

The MCP server reads the env var at startup. Add it to your shell profile to persist.

---

## 3. PDF parsing depends on the host tool's native Read or markitdown MCP

**What:** OSP needs a readable text version of the paper at `.brain/input/paper.md` for the Summary Agent. The `markitdown` MCP server is registered by the installer for this purpose.

**Limitation:** If `markitdown-mcp` is not installed (or `uvx` is not on PATH), and the paper is supplied as a PDF/DOCX, conversion will fail.

**Impact:** `/0-osp-onboarding` will refuse to advance until either (a) markitdown is installed, or (b) the user manually provides `.brain/input/paper.md`. This is intentional fail-fast behavior to avoid silent downstream errors.

**Workaround:** Install markitdown:
```bash
pipx install uv          # if not already installed
uvx markitdown-mcp       # smoke-test that the package is fetchable
```
or convert manually:
```bash
markitdown paper.pdf > .brain/input/paper.md
```

---

## 4. Antigravity and Copilot CLI MCP configs require manual setup

**What:** Most tools store MCP config in a project-local file the installer can write directly. Two exceptions:
- **Antigravity** uses a global config at `~/.gemini/antigravity/mcp_config.json`.
- **Copilot CLI** uses `~/.copilot/mcp-config.json`.

**Limitation:** Programmatically modifying user-global config files would be intrusive. The installers print a paste-ready snippet (or attempt a careful merge in Copilot's case) but the user must verify the file.

**Impact:** Slightly higher first-run friction on Antigravity. Copilot CLI is auto-merged by `merge_mcp_config.py` but the user should still verify the file looks right.

**Workaround:** Check the snippet at `.open-scholar-peer/antigravity_mcp_snippet.json` (Antigravity) or `~/.copilot/mcp-config.json` (Copilot CLI) after install.

---

## 5. Single paper per `.brain/` (multi-paper sessions deferred)

**What:** v1 of OSP supports one active review per project directory.

**Limitation:** To review a second paper in the same project, you must archive or delete the existing `.brain/` and start fresh.

**Impact:** Researchers who maintain a directory of in-progress reviews must either use separate project directories or move `.brain/` aside between papers.

**Future:** Multi-paper sessions (`.brain/sessions/<paper_slug>/` with active-session pointer) are planned but deferred.

**Workaround:** Use one project directory per paper, or:
```bash
mv .brain .brain.archive-$(date +%F)
```

---

## 6. Google Scholar tools are best-effort (HTML scraping)

**What:** Google Scholar has no public API. The `osp_mcp.search_google_scholar` tools scrape HTML.

**Limitation:** Subject to Google's rate limits and HTML structure changes. Results may be empty or stale during heavy usage.

**Impact:** The Literature Agent and Baseline Scout still have arXiv and Semantic Scholar as primary sources; Google Scholar adds breadth (blog posts, theses, workshop papers) but isn't load-bearing.

**Workaround:** None needed unless Google Scholar is your primary source, in which case consider running searches at off-peak times.

---

## 7. Hyperparameters are structurally enforced, not numerically configurable

**What:** The paper specifies `k=3` literature rounds and `N_QA=10` probing pairs per criterion. OSP enforces `k=3` via file structure (3 separate round files). `N_QA` is **user-configurable** at the start of `/5-osp-qa` — the default is 2 pairs per criterion (lighter cost; the user can choose any N at runtime, and the template renders `### Q1`…`### QN` accordingly). The choice persists in `session.json.qa_pairs_per_criterion`.

**Limitation:** You cannot easily run "k=5 rounds" or "5 Q&A pairs per criterion" without editing the canonical templates in `extensions/_shared/defaults/`.

**Why this design:** Host tools (Claude Code, Cursor, etc.) do not expose temperature or other LLM hyperparameters to slash commands. Structural enforcement (file templates the agent must fill) is the only reliable way to ensure the count without the LLM hallucinating compliance.

**Workaround:** If you need different counts for research purposes, fork the templates in `_shared/defaults/` and re-run the sync script.

---

## 8. Re-running an earlier phase invalidates downstream artifacts

**What:** OSP commands are idempotent (re-running overwrites their own artifact with a warning), but they do **not** automatically invalidate downstream artifacts.

**Limitation:** If you re-run `/1-osp-summary` after the Q&A phase has already produced `05_qa_*.md` files, those Q&A files now reflect a stale structured summary.

**Impact:** Reviews can become inconsistent across the artifact chain.

**Workaround:** After re-running an earlier phase, manually re-run each subsequent phase, or run `/open-scholar-peer` and follow the dispatcher's guidance.

---

## 9. ACM Digital Library has no public search API — Crossref is a proxy, not a mirror

**What:** ACM does not offer a self-service search API for the Digital Library. `osp_mcp.search_acm`/`get_acm_paper_details` query the free Crossref REST API filtered to ACM's Crossref member id (320), which covers every DOI ACM deposits but is metadata-only.

**Limitation:** Many ACM-deposited records omit abstract text in Crossref (`abstract` is frequently `null`); full text is never available through this path. Coverage reflects what ACM chooses to deposit with Crossref, which is comprehensive but not guaranteed byte-identical to what dl.acm.org shows.

**Impact:** Title/author/venue/DOI/citation-count metadata is reliable; abstract-dependent verification steps (e.g. the Answer Generator's claim cross-checking) may need to fall back to another source or the paper's own text when `abstract` is null.

**Workaround:** Set `CROSSREF_MAILTO` to your email for Crossref's "polite pool" (steadier rate limits, still no key/signup required). None needed otherwise.

---

## 10. Springer Nature has no anonymous tier

**What:** Unlike Semantic Scholar, Springer's Meta API rejects every request without a valid `api_key` — there is no reduced anonymous fallback. `osp_mcp.search_springer`/`get_springer_paper_details` return `[{"error": "..."}]` until `SPRINGER_API_KEY` is set.

**Limitation:** Exact request-quota numbers depend on your Springer Nature developer account plan; check https://dev.springernature.com/ after signup for your specific limits.

**Impact:** Without a key, the Literature Agent and Baseline Scout silently lose Springer as a source (falls back to arXiv/Semantic Scholar/Google Scholar/ACM), which is fine for CS-heavy papers but reduces coverage for Springer-only venues (many life-sciences and engineering journals, LNCS proceedings).

**Workaround:** Get a free key at https://dev.springernature.com/ and set `SPRINGER_API_KEY`.

---

## 11. IEEE Xplore has no anonymous tier and a per-account request quota

**What:** Like Springer, IEEE Xplore's Metadata API rejects every request without a valid `apikey`. `osp_mcp.search_ieee_xplore`/`get_ieee_xplore_paper_details` return `[{"error": "..."}]` until `IEEE_XPLORE_API_KEY` is set.

**Limitation:** Free developer accounts get a limited daily/monthly call quota (check your account at https://developer.ieee.org/ for the exact number — it has changed over time and depends on account type). Heavy literature-review sessions (3 rounds × multiple queries) can burn through a small quota quickly.

**Impact:** Without a key, or after exhausting quota, IEEE Xplore silently drops out as a source; the Literature Agent still has arXiv/Semantic Scholar/Google Scholar/ACM/Springer as coverage. This mainly affects electrical-engineering and hardware-adjacent CS papers.

**Workaround:** Get a free key at https://developer.ieee.org/ and set `IEEE_XPLORE_API_KEY`. If you hit quota limits, space out literature-review sessions or request a higher quota from IEEE.

---

## 12. ScienceDirect metadata depth depends on your Elsevier entitlements

**What:** `osp_mcp.search_sciencedirect`/`get_sciencedirect_paper_details` wrap the Elsevier Search API V2 and Article Retrieval API. They require `SCIENCEDIRECT_API_KEY` (no anonymous tier) but the *depth* of what comes back — abstracts in particular — depends on whether your API key is tied to a subscribing institution.

**Limitation:** Without an institutional subscription, expect reliable bibliographic metadata (title, authors, DOI, venue, cover date) but `abstract` is frequently null, and full text is never available through these tools.

**Impact:** Abstract-dependent verification steps (e.g. the Answer Generator's claim cross-checking) may need to fall back to another source when `abstract` is null for a ScienceDirect-only result.

**Workaround:** Get a free key at https://dev.elsevier.com/ and set `SCIENCEDIRECT_API_KEY`. If your organization has an Elsevier subscription, using a key associated with it (or adding `X-ELS-Insttoken`-style institutional access, not currently wired into this provider) unlocks richer metadata.

**Future:** Cascading invalidation (e.g. re-running `/1-osp-summary` resets `phases.qa` to `pending`) is on the roadmap.
