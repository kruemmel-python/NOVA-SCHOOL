from __future__ import annotations

import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from nova_school_server.config import ServerConfig
from nova_school_server.database import SchoolRepository
from nova_school_server.user_admin import UserAdministrationService
from nova_school_server.workspace import WorkspaceManager, slugify


class UserAdministrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp.name)
        self.config = ServerConfig(
            base_path=self.base_path,
            data_path=self.base_path / "data",
            docs_path=self.base_path / "data" / "docs",
            users_workspace_path=self.base_path / "data" / "workspaces" / "users",
            groups_workspace_path=self.base_path / "data" / "workspaces" / "groups",
            static_path=self.base_path / "static",
            database_path=self.base_path / "data" / "school.db",
        )
        self.workspace = WorkspaceManager(self.config)
        self.repository = SchoolRepository(self.config.database_path)
        self.service = UserAdministrationService(self.repository, self.workspace, self.config)
        self.repository.create_user(
            username="student",
            display_name="Student Demo",
            password_hash="hash",
            password_salt="salt",
            role="student",
            permissions={"chat.use": True},
            status="active",
        )
        self.repository.create_user(
            username="teacher",
            display_name="Teacher Demo",
            password_hash="hash",
            password_salt="salt",
            role="teacher",
            permissions={"admin.manage": True},
            status="active",
        )

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def _create_personal_project(self) -> dict[str, object]:
        project = self.repository.create_project(
            owner_type="user",
            owner_key="student",
            name="Test Projekt",
            slug=slugify("Test Projekt"),
            template="python",
            runtime="python",
            main_file="main.py",
            description="Demo",
            created_by="teacher",
        )
        self.workspace.materialize_project(project)
        return project

    def test_update_user_changes_status_role_and_logs_audit(self) -> None:
        payload = self.service.update_user(
            actor_username="teacher",
            username="student",
            display_name="Student Eins",
            role="teacher",
            status="suspended",
            password="NeuesPasswort123!",
        )

        self.assertEqual(payload["user"]["display_name"], "Student Eins")
        self.assertEqual(payload["user"]["role"], "teacher")
        self.assertEqual(payload["user"]["status"], "suspended")
        self.assertNotIn("password_hash", payload["user"])
        self.assertIn("password", payload["changes"])

        entries = self.service.audit_entries("student")
        self.assertEqual(entries[0]["action"], "admin.user.update")
        self.assertEqual(entries[0]["payload"]["changes"]["status"]["after"], "suspended")
        self.assertTrue(entries[0]["payload"]["changes"]["password"]["reset"])

    def test_permission_audit_payload_only_contains_changed_keys(self) -> None:
        before = self.repository.get_user("student")
        self.repository.update_user_permissions("student", {"chat.use": False, "ai.use": True})
        after = self.repository.get_user("student")

        payload = self.service.permission_audit_payload(before, after)
        self.assertEqual(set(payload["changes"]), {"chat.use", "ai.use"})
        self.assertEqual(payload["changes"]["chat.use"]["before"], True)
        self.assertEqual(payload["changes"]["chat.use"]["after"], False)

    def test_cannot_deactivate_own_current_account(self) -> None:
        with self.assertRaisesRegex(ValueError, "deaktiviert"):
            self.service.update_user(
                actor_username="student",
                username="student",
                display_name="Student Demo",
                role="student",
                status="inactive",
            )

    def test_export_user_data_includes_projects_groups_and_ai_threads(self) -> None:
        project = self._create_personal_project()
        self.repository.create_group("class-1a", "Klasse 1A", "Demo")
        self.repository.add_membership("student", "class-1a")
        self.repository.add_chat_message(
            f"project:{project['project_id']}",
            "student",
            "Student Demo",
            "Hallo Gruppe",
            metadata={"kind": "room"},
        )
        self.repository.add_chat_message(
            f"assistant:{project['project_id']}:student",
            "student",
            "Student Demo",
            "Was macht print()?",
            metadata={"role": "user", "mode": "assistant", "project_id": project["project_id"]},
        )
        self.repository.add_chat_message(
            f"assistant:{project['project_id']}:student",
            "assistant.bot",
            "Nova KI",
            "print() gibt Text aus.",
            metadata={"role": "assistant", "mode": "assistant", "project_id": project["project_id"]},
        )
        self.repository.add_chat_message(
            f"mentor:{project['project_id']}:student",
            "student",
            "Student Demo",
            "Warum kommt ein Fehler?",
            metadata={"role": "user", "mode": "mentor", "project_id": project["project_id"]},
        )
        self.repository.add_chat_message(
            f"mentor:{project['project_id']}:student",
            "mentor.bot",
            "Nova Mentor",
            "Welche Variable ist ungueltig?",
            metadata={"role": "assistant", "mode": "mentor", "project_id": project["project_id"]},
        )
        self.repository.add_audit("teacher", "admin.user.update", "user", "student", {"changes": {"status": {"before": "active", "after": "active"}}})

        payload = self.service.export_user_data("student")

        self.assertEqual(payload["user"]["username"], "student")
        self.assertEqual(payload["groups"][0]["group_id"], "class-1a")
        self.assertEqual(payload["personal_projects"][0]["project_id"], project["project_id"])
        self.assertEqual(len(payload["assistant_threads"]), 1)
        self.assertEqual(len(payload["assistant_threads"][0]["messages"]), 2)
        self.assertEqual(len(payload["mentor_threads"]), 1)
        self.assertEqual(len(payload["mentor_threads"][0]["messages"]), 2)
        self.assertGreaterEqual(payload["summary"]["audit_count"], 1)
        self.assertEqual(payload["summary"]["assistant_message_count"], 2)
        self.assertEqual(payload["summary"]["mentor_message_count"], 2)

    def test_hard_delete_user_removes_projects_files_and_histories(self) -> None:
        project = self._create_personal_project()
        project_root = self.workspace.project_root(project)
        assistant_room = f"assistant:{project['project_id']}:student"
        mentor_room = f"mentor:{project['project_id']}:student"
        self.repository.add_chat_message(assistant_room, "student", "Student Demo", "KI Frage", metadata={"role": "user"})
        self.repository.add_chat_message(assistant_room, "assistant.bot", "Nova KI", "KI Antwort", metadata={"role": "assistant"})
        self.repository.add_chat_message(mentor_room, "student", "Student Demo", "Mentor Frage", metadata={"role": "user"})
        self.repository.add_chat_message(mentor_room, "mentor.bot", "Nova Mentor", "Mentor Antwort", metadata={"role": "assistant"})
        self.repository.add_audit("student", "assistant.chat", "assistant", "litert", {"model": "gemma"})

        summary = self.service.hard_delete_user(actor_username="teacher", username="student")

        self.assertIsNone(self.repository.get_user("student"))
        self.assertFalse(project_root.exists())
        self.assertEqual(summary["counts"]["users"], 1)
        with self.repository._lock:
            remaining = self.repository._conn.execute(
                "SELECT COUNT(*) AS count FROM chat_messages WHERE room_key LIKE ? OR room_key LIKE ?",
                (assistant_room, mentor_room),
            ).fetchone()
        self.assertEqual(int(remaining["count"]), 0)
        audits = self.repository.list_audit_logs(target_type="user", limit=10)
        self.assertTrue(any(entry["action"] == "admin.user.hard_delete" for entry in audits))

    def test_export_project_archive_contains_manifest_and_project_files(self) -> None:
        project = self._create_personal_project()
        project_root = self.workspace.project_root(project)
        (project_root / "notes.txt").write_text("Datenschutz Demo", encoding="utf-8")

        payload = self.service.export_project_archive(actor_username="teacher", project=project)

        self.assertTrue(payload["filename"].endswith(".zip"))
        archive_path = self.base_path / "tmp-project-export.zip"
        archive_path.write_bytes(payload["content"])
        with zipfile.ZipFile(archive_path) as archive:
            self.assertIn("manifest.json", archive.namelist())
            self.assertIn("project/main.py", archive.namelist())
            self.assertIn("project/notes.txt", archive.namelist())

    def test_hard_delete_project_removes_workspace_and_project_chats(self) -> None:
        project = self._create_personal_project()
        project_root = self.workspace.project_root(project)
        self.repository.add_chat_message(f"project:{project['project_id']}", "student", "Student Demo", "Projektchat", metadata={})
        self.repository.add_chat_message(f"assistant:{project['project_id']}:student", "assistant.bot", "Nova KI", "Codehilfe", metadata={})
        self.repository.add_chat_message(f"mentor:{project['project_id']}:student", "mentor.bot", "Nova Mentor", "Hinweis", metadata={})
        self.repository.add_audit("teacher", "project.create", "project", project["project_id"], {})

        summary = self.service.hard_delete_project(actor_username="teacher", project=project)

        self.assertFalse(project_root.exists())
        self.assertIsNone(self.repository.get_project(project["project_id"]))
        self.assertEqual(summary["counts"]["projects"], 1)
        with self.repository._lock:
            remaining = self.repository._conn.execute(
                "SELECT COUNT(*) AS count FROM chat_messages WHERE room_key=? OR room_key LIKE ? OR room_key LIKE ?",
                (f"project:{project['project_id']}", f"mentor:{project['project_id']}:%", f"assistant:{project['project_id']}:%"),
            ).fetchone()
        self.assertEqual(int(remaining["count"]), 0)
        self.assertEqual(summary["counts"]["project_assistant_messages"], 1)
        audits = self.repository.list_audit_logs(target_type="project", target_id=project["project_id"], limit=10)
        self.assertTrue(any(entry["action"] == "project.hard_delete" for entry in audits))

    def test_apply_retention_deletes_old_chat_and_audits(self) -> None:
        old = time.time() - (10 * 86400)
        self.repository.put_setting("retention_chat_days", 1)
        self.repository.put_setting("retention_audit_days", 1)
        self.repository.add_chat_message("project:test", "student", "Student Demo", "alte Nachricht", metadata={})
        self.repository.set_mute("project:test", "student", duration_minutes=1, reason="alt", created_by="teacher")
        self.repository.add_audit("teacher", "chat.message", "room", "project:test", {})
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute("UPDATE chat_messages SET created_at=? WHERE room_key='project:test'", (old,))
            self.repository._conn.execute("UPDATE chat_mutes SET muted_until=?, created_at=?", (old, old))
            self.repository._conn.execute("UPDATE audit_logs SET created_at=? WHERE target_id='project:test'", (old,))

        summary = self.service.apply_retention(actor_username="teacher")

        self.assertEqual(summary["deleted"]["chat_messages"], 1)
        self.assertEqual(summary["deleted"]["audit_logs"], 1)
        self.assertEqual(summary["deleted"]["expired_mutes"], 1)
        with self.repository._lock:
            chats = self.repository._conn.execute("SELECT COUNT(*) AS count FROM chat_messages").fetchone()
            audits = self.repository._conn.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE target_id='project:test'").fetchone()
        self.assertEqual(int(chats["count"]), 0)
        self.assertEqual(int(audits["count"]), 0)


if __name__ == "__main__":
    unittest.main()
