from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nova_school_server.nova_bridge import load_nova_bridge


class EmbeddedNovaBridgeTests(unittest.TestCase):
    def test_embedded_bridge_handles_token_flow_without_external_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = load_nova_bridge()
            self.assertEqual(bridge.source, "embedded")
            security = bridge.SecurityPlane(Path(tmp))
            security.register_tenant("nova-school", display_name="Nova School")

            token_payload = security.issue_token("nova-school", "teacher", roles={"teacher"}, ttl_seconds=3600)
            principal = security.authenticate(str(token_payload["token"]))

            self.assertIsNotNone(principal)
            self.assertEqual(principal.subject, "teacher")
            self.assertEqual(principal.token_id, str(token_payload["token_id"]))
            self.assertEqual(security.snapshot()["backend"], "embedded")

    def test_embedded_tool_sandbox_authorizes_requests(self) -> None:
        bridge = load_nova_bridge()
        sandbox = bridge.ToolSandbox()

        session = sandbox.authorize(
            "user:teacher",
            allowed_tools={"run.python", "ai.use"},
            requested_tools={"run.python"},
            metadata={"project_id": "abc"},
        )

        self.assertTrue(session["authorized"])
        self.assertIn("run.python", session["requested_tools"])
        self.assertEqual(sandbox.snapshot()["backend"], "embedded")


if __name__ == "__main__":
    unittest.main()
