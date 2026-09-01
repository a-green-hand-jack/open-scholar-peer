"""Offline tests for the standalone OSP CLI runtime.

No test invokes a provider.  The fake executor makes the OSP phase contract
observable while exercising source import, ordering, checkpoints, and resume.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from osp_cli.runtime import COMMANDS, OSPError, OSPRun, PHASES, RunOptions, sha256_file


def artifact(title: str) -> str:
    return f"# {title}\n\n## Method\nOffline fake executor.\n\n## Output\nVerified test artifact.\n\n## Provenance\nLocal fixture only.\n"


class FakeExecutor:
    def __init__(self, fail_phase: str | None = None) -> None:
        self.fail_phase = fail_phase
        self.calls: list[str] = []

    def __call__(self, prompt: str, workspace: Path, _options: RunOptions) -> subprocess.CompletedProcess[str]:
        phase = next(name for name, command in COMMANDS.items() if f"/{command}" in prompt)
        self.calls.append(phase)
        if phase == self.fail_phase:
            return subprocess.CompletedProcess(["fake"], 1, "", "planned failure")
        raw = workspace / ".brain" / "raw"
        review = workspace / ".brain" / "review"
        if phase == "onboarding":
            (raw / "00_review_guidelines.md").write_text(artifact("Guidelines"), encoding="utf-8")
            (raw / "05_qa_soundness.md").write_text("# Q&A — Soundness\n", encoding="utf-8")
            session = json.loads((workspace / ".brain" / "session.json").read_text())
            session["qa_criteria"] = [{"slug": "soundness", "label": "Soundness", "definition": "test"}]
        elif phase == "summary":
            (raw / "01_structured_summary.md").write_text(artifact("Summary"), encoding="utf-8")
        elif phase == "literature":
            for name, strategy in (("02a_literature_round1.md", "sub-domain-anchor"), ("02b_literature_round2.md", "method-anchor"), ("02c_literature_round3.md", "temporal-expansion")):
                (raw / name).write_text(artifact(name).replace("Offline fake executor.", f"Strategy: {strategy}\nOffline fake executor."), encoding="utf-8")
            (raw / "02_retrieved_literature.md").write_text(artifact("retrieved literature"), encoding="utf-8")
        elif phase == "historian":
            (raw / "03_domain_narrative.md").write_text(artifact("Narrative"), encoding="utf-8")
        elif phase == "baseline_scout":
            (raw / "04_missing_baselines.md").write_text(artifact("Baselines"), encoding="utf-8")
        elif phase == "qa":
            (raw / "05_qa_soundness.md").write_text(artifact("Q&A") + "\n### Q1\nQuestion\n### A1\nAnswer\n### Q2\nQuestion\n### A2\nAnswer\n", encoding="utf-8")
        else:
            final = artifact("Final review") + "\n## Summary\nSummary.\n\n## Strengths\nStrength.\n\n## Weaknesses\nWeakness.\n\n## Dimension Scores\n\n| Dimension | Score |\n|---|---|\n| Soundness | 3/5 |\n\n## Recommendation\nNeeds revision.\n\n## What was not checked\nNothing else.\n\nEvidence: `01_structured_summary.md`.\n"
            (review / "final_review.md").write_text(final, encoding="utf-8")
        session = locals().get("session") or json.loads((workspace / ".brain" / "session.json").read_text())
        session["phases"][phase]["status"] = "completed"
        session["phases"][phase]["started_at"] = "2026-01-01T00:00:00Z"
        session["phases"][phase]["completed_at"] = "2026-01-01T00:00:01Z"
        session["phases"][phase]["notes"] = "offline test artifact"
        session["resume_from"] = "completed" if phase == "review" else PHASES[PHASES.index(phase) + 1]
        (workspace / ".brain" / "session.json").write_text(json.dumps(session), encoding="utf-8")
        return subprocess.CompletedProcess(["fake"], 0, json.dumps({"phase": phase}), "")


class OSPRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "paper"
        self.source.mkdir()
        (self.source / "main.tex").write_text("\\documentclass{article}\n\\begin{document}Hello\\end{document}\n", encoding="utf-8")
        self.options = RunOptions(output=self.root / "runs", prepare_mcp=False, headless=True, venue="arXiv", domain="cs")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_isolated_run_completes_in_contract_order(self) -> None:
        run = OSPRun.prepare(self.source, self.options)
        fake = FakeExecutor()
        run.executor = fake
        run.run(self.options)
        self.assertEqual(fake.calls, ["onboarding", "summary", "literature", "literature", "literature", "historian", "baseline_scout", "qa", "review"])
        self.assertEqual(run.state()["status"], "completed")
        self.assertTrue((run.run_dir / ".brain" / "review" / "final_review.md").is_file())
        self.assertTrue((run.run_dir.parent / "final_review.md").is_file())
        self.assertTrue(all(check.passed for check in run.validate()))
        checkpoints = list(run.checkpoint_dir.glob("*.json"))
        self.assertGreaterEqual(len(checkpoints), len(PHASES) + 2)

    def test_failure_preserves_state_and_resume_only_runs_remaining_phases(self) -> None:
        run = OSPRun.prepare(self.source, self.options)
        failing = FakeExecutor(fail_phase="literature")
        run.executor = failing
        with self.assertRaises(OSPError):
            run.run(self.options)
        self.assertEqual(run.state()["phases"]["literature"]["status"], "failed")
        self.assertTrue(run.state()["phases"]["literature"]["log"])
        recovered = FakeExecutor()
        run.executor = recovered
        run.run(self.options)
        self.assertEqual(recovered.calls, ["literature", "literature", "literature", "historian", "baseline_scout", "qa", "review"])

    def test_archive_import_preserves_manifest_and_does_not_modify_source(self) -> None:
        archive = self.root / "paper.zip"
        import zipfile

        with zipfile.ZipFile(archive, "w") as handle:
            handle.writestr("paper/main.tex", "\\documentclass{article}\n\\begin{document}Archive\\end{document}\n")
            handle.writestr("paper/refs.bib", "")
        before = sha256_file(archive)
        run = OSPRun.prepare(archive, self.options)
        manifest = json.loads((run.run_dir / ".osp-run" / "source-manifest.json").read_text())
        self.assertEqual(manifest["kind"], "archive")
        self.assertEqual(manifest["entrypoint"], "main.tex")
        self.assertEqual(before, sha256_file(archive))
        self.assertTrue((run.run_dir / "source" / "main.tex").is_file())

    def test_scope_tampering_blocks_resume(self) -> None:
        run = OSPRun.prepare(self.source, self.options)
        state = run.state()
        state["scope"]["options"]["venue"] = "different"
        (run.run_dir / ".osp-run" / "run.json").write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(OSPError):
            run.verify_scope()

    def test_existing_workspace_seeds_configuration_without_importing_old_review(self) -> None:
        workspace = self.root / "existing-osp"
        (workspace / ".brain" / "input").mkdir(parents=True)
        (workspace / ".brain" / "raw").mkdir()
        (workspace / ".brain" / "input" / "paper.md").write_text("# Existing paper\n", encoding="utf-8")
        previous = {
            "venue": {"name": "ICLR", "year": "2026", "source_url": "", "criteria_source": "user"},
            "paper": {"field": "cs-ml", "review_mode": "empirical", "domain_profile": "cs-ml", "numerical_slice": False},
            "qa_criteria": [{"slug": "soundness", "label": "Soundness", "definition": "test"}],
            "qa_pairs_per_criterion": 3,
        }
        (workspace / ".brain" / "session.json").write_text(json.dumps(previous), encoding="utf-8")
        (workspace / ".brain" / "raw" / "old_review.md").write_text("must not be imported", encoding="utf-8")
        run = OSPRun.prepare(workspace, RunOptions(output=self.root / "workspace-runs", prepare_mcp=False, headless=True))
        session = json.loads((run.run_dir / ".brain" / "session.json").read_text())
        self.assertEqual(session["venue"]["name"], "ICLR")
        self.assertEqual(session["qa_pairs_per_criterion"], 3)
        self.assertFalse((run.run_dir / "source" / "old_review.md").exists())

    def test_pdf_source_digest_matches_locked_import(self) -> None:
        pdf = Path(__file__).resolve().parents[1] / "docs" / "paper" / "scholar_peer_arxiv.pdf"
        run = OSPRun.prepare(pdf, RunOptions(output=self.root / "pdf-runs", prepare_mcp=False, headless=True))
        run.verify_scope()
        self.assertTrue((run.run_dir / "source" / "paper.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
