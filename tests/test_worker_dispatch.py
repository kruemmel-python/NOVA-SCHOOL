from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from nova_school_server.config import ServerConfig
from nova_school_server.database import SchoolRepository
from nova_school_server.worker_dispatch import RemoteWorkerDispatchService
from nova_school_server.workspace import WorkspaceManager


class _FakeSecurityPlane:
    def __init__(self) -> None:
        self.secrets: dict[tuple[str, str], dict[str, object]] = {}

    def store_secret(self, tenant_id: str, name: str, secret_value: str, metadata=None) -> dict[str, object]:
        payload = {"tenant_id": tenant_id, "name": name, "secret_value": secret_value, "metadata": metadata or {}}
        self.secrets[(tenant_id, name)] = payload
        return payload

    def resolve_secret(self, tenant_id: str, name: str) -> dict[str, object] | None:
        return self.secrets.get((tenant_id, name))

    def onboard_worker(self, *_args, **_kwargs) -> dict[str, object]:
        return {}

    def list_worker_enrollments(self, *_args, **_kwargs) -> list[dict[str, object]]:
        return []


class WorkerDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp.name)
        self.config = ServerConfig.from_base_path(self.base_path)
        self.repository = SchoolRepository(self.config.database_path)
        self.workspace = WorkspaceManager(self.config)
        self.security = _FakeSecurityPlane()
        self.service = RemoteWorkerDispatchService(self.repository, self.workspace, self.security, self.config)

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def test_claim_next_job_includes_signed_artifact_hash(self) -> None:
        self.service.issue_bootstrap(worker_id="worker-1", display_name="Worker 1")
        runtime_root = self.base_path / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "main.py").write_text("print('ok')\n", encoding="utf-8")

        job = self.service.create_playground_job(
            worker_id="worker-1",
            project={"project_id": "proj-1", "name": "Project 1"},
            service={"name": "svc", "runtime": "python"},
            backend="process",
            payload={"entrypoint": "main.py"},
            created_by="teacher",
            runtime_root=runtime_root,
        )

        claimed = self.service.claim_next_job("worker-1")

        self.assertIsNotNone(claimed)
        assert claimed is not None
        self.assertTrue(claimed["artifact_sha256"])
        artifact = self.service.resolve_job_artifact(str(job["job_id"]))
        self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), claimed["artifact_sha256"])
        self.assertEqual(claimed["artifact_sha256"], self.service._job_signature_payload(claimed)["artifact_sha256"])


if __name__ == "__main__":
    unittest.main()
