import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp-server"))
from providers import bohrium  # noqa: E402


class BohriumProviderTests(unittest.TestCase):
    def test_parse_submit_rejects_pdf_over_page_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            input_dir = workspace / ".brain" / "input"
            input_dir.mkdir(parents=True)
            pdf_path = input_dir / "paper.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            result = SimpleNamespace(returncode=0, stdout="Pages:          51\n")
            with patch.dict(os.environ, {"OSP_WORKSPACE_ROOT": str(workspace)}), patch.object(
                bohrium.shutil, "which", return_value="/usr/bin/pdfinfo"
            ), patch.object(bohrium.subprocess, "run", return_value=result) as run:
                response = bohrium.parse_submit(str(pdf_path))
            self.assertEqual(response, {"error": "PDF exceeds the 50-page LKM extraction limit"})
            run.assert_called_once_with(
                ["pdfinfo", str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
