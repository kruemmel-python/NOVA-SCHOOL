from __future__ import annotations

import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from nova_school_server.analysis_archive_builder import build_source_analysis_archive


class SourceAnalysisArchiveBuilderTests(unittest.TestCase):
    def test_build_source_analysis_archive_keeps_text_source_and_skips_binaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._git(repo, "init")
            self._git(repo, "config", "user.name", "Nova School")
            self._git(repo, "config", "user.email", "nova@example.invalid")

            (repo / "pyproject.toml").write_text('[project]\nversion = "0.1.12"\n', encoding="utf-8")
            (repo / "server.py").write_text("print('ok')\n", encoding="utf-8")
            (repo / "static").mkdir()
            (repo / "static" / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
            (repo / "Docs").mkdir()
            (repo / "Docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (repo / "Docs" / "guide.html").write_text("<html></html>\n", encoding="utf-8")
            (repo / "LIT").mkdir()
            (repo / "LIT" / "README.md").write_text("# Runtime\n", encoding="utf-8")
            (repo / "LIT" / "model.gguf").write_bytes(b"GGUF")
            (repo / "Model").mkdir()
            (repo / "Model" / "offline.gguf").write_bytes(b"GGUF")
            (repo / "dist").mkdir()
            (repo / "dist" / "old.zip").write_bytes(b"ZIP")
            (repo / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

            self._git(repo, "add", ".")
            self._git(repo, "commit", "-m", "Add source analysis builder fixtures")

            result = build_source_analysis_archive(repo, output_dir=repo / "out")

            self.assertTrue(result.archive_path.exists())
            self.assertEqual("0.1.12", result.version)

            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())

            prefix = "NovaSchoolAnalyzer-v0.1.12/"
            self.assertIn(prefix + "server.py", names)
            self.assertIn(prefix + "static/index.html", names)
            self.assertIn(prefix + "Docs/guide.md", names)
            self.assertIn(prefix + "LIT/README.md", names)
            self.assertNotIn(prefix + "Docs/guide.html", names)
            self.assertNotIn(prefix + "LIT/model.gguf", names)
            self.assertNotIn(prefix + "Model/offline.gguf", names)
            self.assertNotIn(prefix + "dist/old.zip", names)
            self.assertNotIn(prefix + "image.png", names)

    @staticmethod
    def _git(repo: Path, *args: str) -> None:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout or f"git {' '.join(args)} failed")


if __name__ == "__main__":
    unittest.main()
