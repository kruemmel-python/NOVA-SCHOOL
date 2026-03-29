from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nova_school_server.ai_service import LiteRTLmService, LocalAIService, LlamaCppService
from nova_school_server.database import SchoolRepository


class LlamaCppServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp.name)
        self.data_path = self.base_path / "data"
        self.model_path = self.base_path / "Model"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.repository = SchoolRepository(self.data_path / "school.db")

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def test_status_prefers_local_gguf_model(self) -> None:
        model_file = self.model_path / "gemma-3-1b-it-q4_k_m.gguf"
        model_file.write_bytes(b"GGUF")
        service = LlamaCppService(self.repository, base_path=self.base_path, data_path=self.data_path)

        status = service.status(enabled=True)

        self.assertEqual(status["provider"], "server-llama.cpp")
        self.assertTrue(status["configured"])
        self.assertEqual(status["model_path"], str(model_file))
        self.assertEqual(status["model_label"], model_file.stem)
        self.assertEqual(status["backend"], "vulkan")
        self.assertFalse(status["requires_webgpu"])

    def test_status_uses_explicit_model_override(self) -> None:
        default_file = self.model_path / "default.gguf"
        override_file = self.model_path / "override.gguf"
        default_file.write_bytes(b"default")
        override_file.write_bytes(b"override")
        self.repository.put_setting("llamacpp_model_path", str(override_file))
        self.repository.put_setting("llamacpp_model_alias", "Nova GGUF")
        service = LlamaCppService(self.repository, base_path=self.base_path, data_path=self.data_path)

        status = service.status(enabled=True)

        self.assertEqual(status["model_path"], str(override_file))
        self.assertEqual(status["model_label"], "Nova GGUF")

    def test_prepare_direct_completion_builds_server_prompt(self) -> None:
        service = LlamaCppService(self.repository, base_path=self.base_path, data_path=self.data_path)

        payload = service.prepare_direct_completion(
            prompt="Warum ist meine Schleife falsch?",
            code="for i in range(len(values)+1): print(values[i])",
            path_hint="main.py",
        )

        self.assertIn("Warum ist meine Schleife falsch?", payload["prompt"])
        self.assertIn("Codekontext", payload["prompt"])
        self.assertIn("Aktive Datei: main.py", payload["prompt"])
        self.assertIn("lokaler Codehelfer", payload["system_prompt"])


class LiteRTLmServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp.name)
        self.data_path = self.base_path / "data"
        self.model_path = self.base_path / "Model"
        self.bin_path = self.base_path / "tools"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.bin_path.mkdir(parents=True, exist_ok=True)
        self.repository = SchoolRepository(self.data_path / "school.db")

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def test_status_prefers_local_litert_model(self) -> None:
        model_file = self.model_path / "gemma-3n-E4B-it-int4.litertlm"
        binary_file = self.bin_path / "lit.windows_x86_64.exe"
        model_file.write_bytes(b"LITERT")
        binary_file.write_bytes(b"EXE")
        self.repository.put_setting("litertlm_binary_path", str(binary_file))
        service = LiteRTLmService(self.repository, base_path=self.base_path, data_path=self.data_path)

        status = service.status(enabled=True)

        self.assertEqual(status["provider"], "server-litert-lm")
        self.assertTrue(status["configured"])
        self.assertEqual(status["model_path"], str(model_file))
        self.assertEqual(status["model_label"], model_file.stem)
        self.assertEqual(status["backend"], "cpu")
        self.assertFalse(status["requires_webgpu"])

    def test_auto_provider_prefers_litert_when_binary_and_model_exist(self) -> None:
        litert_model = self.model_path / "gemma-3n-E4B-it-int4.litertlm"
        binary_file = self.bin_path / "lit.windows_x86_64.exe"
        litert_model.write_bytes(b"LITERT")
        binary_file.write_bytes(b"EXE")
        self.repository.put_setting("litertlm_binary_path", str(binary_file))
        service = LocalAIService(self.repository, base_path=self.base_path, data_path=self.data_path)

        status = service.status(enabled=True)

        self.assertEqual(status["provider"], "server-litert-lm")
        self.assertEqual(status["model_path"], str(litert_model))

    def test_local_ai_service_proxies_max_tokens_to_active_provider(self) -> None:
        litert_model = self.model_path / "gemma-3n-E4B-it-int4.litertlm"
        binary_file = self.bin_path / "lit.windows_x86_64.exe"
        litert_model.write_bytes(b"LITERT")
        binary_file.write_bytes(b"EXE")
        self.repository.put_setting("litertlm_binary_path", str(binary_file))
        self.repository.put_setting("ondevice_max_tokens", 1536)
        service = LocalAIService(self.repository, base_path=self.base_path, data_path=self.data_path)

        self.assertEqual(service.provider_id, "server-litert-lm")
        self.assertEqual(service.max_tokens, 1536)

    def test_prepare_direct_completion_builds_server_prompt(self) -> None:
        service = LiteRTLmService(self.repository, base_path=self.base_path, data_path=self.data_path)

        payload = service.prepare_direct_completion(
            prompt="Antworte nur mit OK",
            code="print('Hallo')",
            path_hint="main.py",
        )

        self.assertIn("Antworte nur mit OK", payload["prompt"])
        self.assertIn("Codekontext", payload["prompt"])
        self.assertIn("Aktive Datei: main.py", payload["prompt"])
        self.assertIn("lokaler Codehelfer", payload["system_prompt"])


if __name__ == "__main__":
    unittest.main()
