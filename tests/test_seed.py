from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nova_school_server.auth import AuthService, hash_password
from nova_school_server.database import SchoolRepository
from nova_school_server.docs_catalog import DocumentationCatalog
from nova_school_server.embedded_nova import EmbeddedSecurityPlane
from nova_school_server.seed import bootstrap_application
from nova_school_server.workspace import WorkspaceManager
from nova_school_server.config import ServerConfig


class SeedBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp.name)
        self.config = ServerConfig.from_base_path(self.base_path)
        self.repository = SchoolRepository(self.config.database_path)
        self.security = EmbeddedSecurityPlane(self.base_path)
        self.auth = AuthService(self.repository, self.security, self.config.tenant_id, self.config.session_ttl_seconds)
        self.docs = DocumentationCatalog(self.config.docs_path)
        self.workspace = WorkspaceManager(self.config)

    def tearDown(self) -> None:
        self.repository.close()
        self.security.close()
        self.tmp.cleanup()

    def test_bootstrap_resets_demo_accounts_to_role_defaults_even_when_old_overrides_exist(self) -> None:
        salt, password_hash = hash_password("x")
        self.repository.create_user(
            username="teacher",
            display_name="Falsch",
            password_hash=password_hash,
            password_salt=salt,
            role="teacher",
            permissions={"ai.use": False, "teacher.materials.use": False, "curriculum.manage": False, "admin.manage": False},
            status="suspended",
        )
        self.repository.create_user(
            username="student",
            display_name="Falsch",
            password_hash=password_hash,
            password_salt=salt,
            role="student",
            permissions={"ai.use": False, "mentor.use": False, "run.python": False},
            status="inactive",
        )
        self.repository.create_group(
            "class-1a",
            "Alt",
            description="Alt",
            permissions={"workspace.group": False, "chat.use": False, "docs.read": False},
        )

        payload = bootstrap_application(self.repository, self.auth, self.docs, self.workspace)

        self.assertIn("teacher", {item["username"] for item in payload["seed_users"]})
        teacher = self.repository.get_user("teacher")
        student = self.repository.get_user("student")
        group = self.repository.get_group("class-1a")
        self.assertIsNotNone(teacher)
        self.assertIsNotNone(student)
        self.assertIsNotNone(group)
        self.assertEqual(teacher["status"], "active")
        self.assertEqual(student["status"], "active")
        self.assertEqual(teacher["display_name"], "Lehrkraft")
        self.assertEqual(student["display_name"], "Schueler Demo")
        self.assertEqual(teacher["permissions"], {})
        self.assertEqual(student["permissions"], {})
        self.assertEqual(group["permissions"], {"workspace.group": True, "chat.use": True, "docs.read": True})


if __name__ == "__main__":
    unittest.main()
