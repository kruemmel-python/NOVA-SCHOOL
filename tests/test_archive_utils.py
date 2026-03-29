from __future__ import annotations

import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from nova_school_server.archive_utils import extract_zip_safely


class ArchiveUtilsTests(unittest.TestCase):
    def test_extract_zip_safely_writes_normal_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "safe.zip"
            target = Path(tmp) / "extract"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("folder/main.py", "print('ok')\n")

            with zipfile.ZipFile(archive_path) as archive:
                extract_zip_safely(archive, target)

            self.assertEqual("print('ok')\n", (target / "folder" / "main.py").read_text(encoding="utf-8"))

    def test_extract_zip_safely_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "traversal.zip"
            target = Path(tmp) / "extract"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../../outside.txt", "boom")

            with zipfile.ZipFile(archive_path) as archive:
                with self.assertRaises(PermissionError):
                    extract_zip_safely(archive, target)

    def test_extract_zip_safely_rejects_symlink_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "symlink.zip"
            target = Path(tmp) / "extract"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(info, "../secret")

            with zipfile.ZipFile(archive_path) as archive:
                with self.assertRaises(PermissionError):
                    extract_zip_safely(archive, target)


if __name__ == "__main__":
    unittest.main()
