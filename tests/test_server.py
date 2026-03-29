from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nova_school_server.server import NovaSchoolRequestHandler


class _Repo:
    def __init__(self, settings: dict[str, str]) -> None:
        self.settings = settings

    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)


class _App:
    def __init__(self, settings: dict[str, str], port: int = 8877) -> None:
        self.repository = _Repo(settings)
        self.config = type("Config", (), {"port": port})()


class RequestHandlerTlsTests(unittest.TestCase):
    def _handler(self, settings: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> NovaSchoolRequestHandler:
        handler = NovaSchoolRequestHandler.__new__(NovaSchoolRequestHandler)
        handler.application = _App(settings or {})
        handler.headers = headers or {}
        return handler

    def test_cookie_header_uses_secure_when_public_host_is_https(self) -> None:
        handler = self._handler({"server_public_host": "https://nova.schule.local"})
        cookie = handler._cookie_header("token-123")
        self.assertIn("; Secure", cookie)

    def test_cookie_header_uses_secure_when_forwarded_proto_is_https(self) -> None:
        handler = self._handler(headers={"Host": "nova.schule.local", "X-Forwarded-Proto": "https"})
        cookie = handler._cookie_header("token-123")
        self.assertIn("; Secure", cookie)

    def test_clear_cookie_header_uses_secure_when_forwarded_proto_is_https(self) -> None:
        handler = self._handler(headers={"Host": "nova.schule.local", "X-Forwarded-Proto": "https"})
        cookie = handler._clear_cookie_header()
        self.assertIn("; Secure", cookie)

    def test_certificate_verification_url_prefers_https_public_host(self) -> None:
        handler = self._handler({"server_public_host": "https://nova.schule.local"})
        url = handler._certificate_verification_url("course:student")
        self.assertTrue(url.startswith("https://nova.schule.local/certificate/verify?certificate_id="))

    def test_certificate_verification_url_uses_forwarded_https_for_bare_public_host(self) -> None:
        handler = self._handler(
            {"server_public_host": "nova.schule.local"},
            headers={"Host": "nova.schule.local", "X-Forwarded-Proto": "https"},
        )
        url = handler._certificate_verification_url("course:student")
        self.assertTrue(url.startswith("https://nova.schule.local/certificate/verify?certificate_id="))

    def test_resolve_relative_file_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(PermissionError):
                NovaSchoolRequestHandler._resolve_relative_file(root, "../secret.txt")


if __name__ == "__main__":
    unittest.main()
