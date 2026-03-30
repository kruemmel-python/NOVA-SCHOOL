from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import json

from nova_school_server.config import ServerConfig
from nova_school_server.workspace import WorkspaceManager


class WorkspaceTests(unittest.TestCase):
    def test_materialize_project_and_block_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            manager = WorkspaceManager(config)
            project = {
                "owner_type": "user",
                "owner_key": "student",
                "slug": "python-labor",
                "template": "python",
            }
            root = manager.materialize_project(project)
            self.assertTrue((root / "main.py").exists())
            with self.assertRaises(ValueError):
                manager.resolve_project_path(project, "..\\..\\evil.txt")

    def test_load_notebook_normalizes_legacy_starter_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            manager = WorkspaceManager(config)
            project = {
                "owner_type": "user",
                "owner_key": "student",
                "slug": "python-labor",
                "template": "python",
            }
            root = manager.materialize_project(project)
            notebook_path = root / ".nova-school" / "notebook.json"
            notebook_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "py-1",
                            "title": "Python Zelle",
                            "language": "python",
                            "code": "numbers = [1, 2, 3, 4]\\nprint(sum(numbers))\\n",
                        }
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            cells = manager.load_notebook(project)

            self.assertEqual(cells[0]["code"], "numbers = [1, 2, 3, 4]\nprint(sum(numbers))\n")
            persisted = json.loads(notebook_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted[0]["code"], "numbers = [1, 2, 3, 4]\nprint(sum(numbers))\n")

    def test_delete_file_removes_secondary_file_and_blocks_main_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            manager = WorkspaceManager(config)
            project = {
                "owner_type": "user",
                "owner_key": "student",
                "slug": "python-labor",
                "template": "python",
                "main_file": "main.py",
            }
            root = manager.materialize_project(project)
            extra = root / "notes" / "draft.txt"
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_text("demo", encoding="utf-8")

            payload = manager.delete_file(project, "notes/draft.txt")

            self.assertEqual(payload["path"], "notes/draft.txt")
            self.assertFalse(extra.exists())
            self.assertFalse(extra.parent.exists())
            with self.assertRaises(ValueError):
                manager.delete_file(project, "main.py")

    def test_directory_operations_support_create_delete_and_main_path_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            manager = WorkspaceManager(config)
            project = {
                "owner_type": "user",
                "owner_key": "student",
                "slug": "distributed-labor",
                "template": "distributed-system",
                "main_file": "services/coordinator.py",
            }
            root = manager.materialize_project(project)

            created = manager.create_directory(project, "src/components")

            self.assertEqual(created["path"], "src/components")
            self.assertTrue((root / "src" / "components").is_dir())

            draft_dir = root / "notes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            (draft_dir / "draft.txt").write_text("demo", encoding="utf-8")

            deleted = manager.delete_entry(project, "notes")

            self.assertEqual(deleted["kind"], "directory")
            self.assertFalse(draft_dir.exists())
            with self.assertRaises(ValueError):
                manager.delete_entry(project, "services")

            renamed = manager.rename_entry(project, "services", "core-services")

            self.assertEqual(renamed["path"], "services")
            self.assertEqual(renamed["new_path"], "core-services")
            self.assertEqual(renamed["main_file"], "core-services/coordinator.py")
            self.assertTrue((root / "core-services" / "coordinator.py").exists())
            self.assertFalse((root / "services").exists())


if __name__ == "__main__":
    unittest.main()
