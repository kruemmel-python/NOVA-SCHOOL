from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from nova_school_server.distribution_builder import (
    build_distribution_archive,
    build_linux_project_archive,
    materialize_distribution_directory,
)


class DistributionBuilderTests(unittest.TestCase):
    def test_distribution_archive_excludes_runtime_data_and_adds_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / "start_server.ps1").write_text("start", encoding="utf-8")
            (root / "data").mkdir()
            (root / "data" / "school.db").write_text("secret", encoding="utf-8")
            (root / "LIT").mkdir()
            (root / "LIT" / "lit.windows_x86_64.exe").write_text("exe", encoding="utf-8")
            (root / "LIT" / "gemma-3n-E4B-it-int4.litertlm").write_text("model", encoding="utf-8")
            (root / "server.zip").write_text("zip", encoding="utf-8")
            (root / ".nova").mkdir()
            (root / ".nova" / "secret.txt").write_text("secret", encoding="utf-8")

            result = build_distribution_archive(root, output_dir=root)

            self.assertTrue(result.archive_path.exists())
            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())
            self.assertIn("Nova-School-Server-v1.2.3-distribution/README.md", names)
            self.assertIn("Nova-School-Server-v1.2.3-distribution/server_config.json.example", names)
            self.assertIn("Nova-School-Server-v1.2.3-distribution/DISTRIBUTION_README.md", names)
            self.assertIn("Nova-School-Server-v1.2.3-distribution/LIT/README.md", names)
            self.assertIn("Nova-School-Server-v1.2.3-distribution/data/workspaces/users/.gitkeep", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-distribution/data/school.db", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-distribution/server.zip", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-distribution/LIT/lit.windows_x86_64.exe", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-distribution/LIT/gemma-3n-E4B-it-int4.litertlm", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-distribution/.nova/secret.txt", names)

    def test_windows_server_package_excludes_linux_scripts_and_adds_windows_guide(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / "start_server.ps1").write_text("start", encoding="utf-8")
            (root / "start_server.sh").write_text("start", encoding="utf-8")
            (root / "run_tests.ps1").write_text("test", encoding="utf-8")
            (root / "run_tests.sh").write_text("test", encoding="utf-8")
            (root / "start_worker.ps1").write_text("worker", encoding="utf-8")
            (root / "start_worker.sh").write_text("worker", encoding="utf-8")

            result = build_distribution_archive(root, output_dir=root, flavor="windows-server-package")

            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())
            self.assertIn("Nova-School-Server-v1.2.3-windows-server-package/WINDOWS_SERVER_PACKAGE.md", names)
            self.assertIn("Nova-School-Server-v1.2.3-windows-server-package/start_server.ps1", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-windows-server-package/start_server.sh", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-windows-server-package/run_tests.sh", names)

    def test_linux_server_package_excludes_windows_scripts_and_adds_linux_guide(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / "start_server.ps1").write_text("start", encoding="utf-8")
            (root / "start_server.sh").write_text("start", encoding="utf-8")
            (root / "run_tests.ps1").write_text("test", encoding="utf-8")
            (root / "run_tests.sh").write_text("test", encoding="utf-8")
            (root / "start_worker.ps1").write_text("worker", encoding="utf-8")
            (root / "start_worker.sh").write_text("worker", encoding="utf-8")

            result = build_distribution_archive(root, output_dir=root, flavor="linux-server-package")

            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())
            self.assertIn("Nova-School-Server-v1.2.3-linux-server-package/LINUX_SERVER_PACKAGE.md", names)
            self.assertIn("Nova-School-Server-v1.2.3-linux-server-package/start_server.sh", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-linux-server-package/start_server.ps1", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-linux-server-package/run_tests.ps1", names)

    def test_materialize_distribution_directory_skips_generated_linux_project_recursion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / "start_server.sh").write_text("start", encoding="utf-8")
            (root / "Linux").mkdir()
            (root / "Linux" / "README.md").write_text("linux root", encoding="utf-8")
            generated = root / "Linux" / "project"
            generated.mkdir(parents=True)
            (generated / "secret.txt").write_text("generated", encoding="utf-8")

            result = materialize_distribution_directory(root, generated, flavor="linux-server-package")

            self.assertEqual(generated.resolve(strict=False), result.target_root)
            self.assertTrue((generated / "README.md").exists())
            self.assertTrue((generated / "Linux" / "README.md").exists())
            self.assertFalse((generated / "Linux" / "project" / "secret.txt").exists())

    def test_materialized_linux_project_copies_linux_lit_binary_but_not_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / "start_server.sh").write_text("start", encoding="utf-8")
            (root / "LIT").mkdir()
            (root / "LIT" / "lit.linux_x86_64").write_bytes(b"ELF")
            (root / "LIT" / "gemma-3n-E4B-it-int4.litertlm").write_bytes(b"MODEL")

            target = root / "Linux" / "project"
            result = materialize_distribution_directory(root, target, flavor="linux-server-package")

            self.assertEqual(target.resolve(strict=False), result.target_root)
            self.assertTrue((target / "LIT" / "lit.linux_x86_64").exists())
            self.assertFalse((target / "LIT" / "gemma-3n-E4B-it-int4.litertlm").exists())

    def test_linux_project_archive_includes_linux_runtime_binary_and_pure_linux_guide(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / "start_server.ps1").write_text("start", encoding="utf-8")
            (root / "start_server.sh").write_text("start", encoding="utf-8")
            (root / "LIT").mkdir()
            (root / "LIT" / "lit.linux_x86_64").write_bytes(b"ELF")
            (root / "LIT" / "gemma-3n-E4B-it-int4.litertlm").write_bytes(b"MODEL")

            result = build_linux_project_archive(root, output_dir=root)

            self.assertTrue(result.archive_path.exists())
            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())
            self.assertIn("Nova-School-Server-v1.2.3-linux-project/PURE_LINUX_RELEASE.md", names)
            self.assertIn("Nova-School-Server-v1.2.3-linux-project/start_server.sh", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-linux-project/start_server.ps1", names)
            self.assertIn("Nova-School-Server-v1.2.3-linux-project/LIT/lit.linux_x86_64", names)
            self.assertNotIn("Nova-School-Server-v1.2.3-linux-project/LIT/gemma-3n-E4B-it-int4.litertlm", names)


if __name__ == "__main__":
    unittest.main()
