from __future__ import annotations

import importlib.util
import os
import random
import struct
import tempfile
import threading
import time
import unittest
from pathlib import Path

from nova_school_server.code_runner import CodeRunner
from nova_school_server.config import ServerConfig
from nova_school_server.database import SchoolRepository
from nova_school_server.realtime import MAX_CLIENT_WS_FRAME_BYTES, LiveRunManager, RealtimeClient, WebSocketConnection
from nova_school_server.workspace import WorkspaceManager


class _FakeToolSandbox:
    def authorize(self, *_args, **_kwargs):
        return {"authorized": True}


class _Session:
    username = "student"
    role = "student"
    is_teacher = False
    permissions = {
        "run.python": True,
        "run.javascript": True,
        "run.cpp": True,
        "run.java": True,
        "run.rust": True,
        "run.node": True,
        "run.npm": True,
        "run.html": True,
        "web.access": True,
        "notebook.collaborate": True,
    }


class _TeacherSession(_Session):
    username = "teacher"
    role = "teacher"
    is_teacher = True


class _RecordingConnection:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []
        self._lock = threading.Lock()

    def send_json(self, payload):
        with self._lock:
            self.events.append(dict(payload))

    def snapshot(self) -> list[dict[str, object]]:
        with self._lock:
            return list(self.events)


class _FakeSocket:
    def __init__(self, chunks=None, *, raise_timeout: bool = False) -> None:
        self.timeout = "unset"
        self.chunks = list(chunks or [])
        self.raise_timeout = raise_timeout
        self.sent_frames: list[bytes] = []

    def settimeout(self, value) -> None:
        self.timeout = value

    def recv(self, size: int) -> bytes:
        if self.raise_timeout:
            raise TimeoutError("timed out")
        if self.chunks:
            chunk = bytes(self.chunks.pop(0))
            current = chunk[:size]
            remainder = chunk[size:]
            if remainder:
                self.chunks.insert(0, remainder)
            return current
        return b""

    def sendall(self, data: bytes) -> None:
        self.sent_frames.append(bytes(data))

    def shutdown(self, _how) -> None:
        return

    def close(self) -> None:
        return


def _build_masked_frame(
    *,
    opcode: int = 0x1,
    payload: bytes = b"",
    fin: bool = True,
    masked: bool = True,
    rsv: int = 0,
    mask_key: bytes = b"\x01\x02\x03\x04",
    declared_length: int | None = None,
) -> bytes:
    first = (0x80 if fin else 0x00) | (rsv & 0x70) | (opcode & 0x0F)
    actual_length = len(payload)
    wire_length = actual_length if declared_length is None else max(0, int(declared_length))
    second_base = 0x80 if masked else 0x00
    if wire_length < 126:
        header = bytes([first, second_base | wire_length])
    elif wire_length < 65536:
        header = bytes([first, second_base | 126]) + struct.pack("!H", wire_length)
    else:
        header = bytes([first, second_base | 127]) + struct.pack("!Q", wire_length)
    if not masked:
        return header + payload
    masked_payload = bytes(byte ^ mask_key[index % 4] for index, byte in enumerate(payload))
    return header + mask_key + masked_payload


def _chunk_bytes(data: bytes, seed: int) -> list[bytes]:
    randomizer = random.Random(seed)
    index = 0
    chunks: list[bytes] = []
    while index < len(data):
        step = randomizer.randint(1, 7)
        chunks.append(data[index : index + step])
        index += step
    return chunks


def _random_frame(seed: int) -> bytes:
    randomizer = random.Random(seed)
    mode = randomizer.randrange(4)
    if mode == 0:
        payload = bytes(randomizer.randrange(0, 256) for _ in range(randomizer.randrange(0, 48)))
        return _build_masked_frame(
            opcode=randomizer.randrange(0, 16),
            payload=payload,
            fin=bool(randomizer.getrandbits(1)),
            masked=bool(randomizer.getrandbits(1)),
            rsv=(randomizer.randrange(0, 8) << 4),
            mask_key=bytes(randomizer.randrange(0, 256) for _ in range(4)),
        )
    if mode == 1:
        wire_length = randomizer.choice([126, 127, 200, 1024, MAX_CLIENT_WS_FRAME_BYTES + randomizer.randrange(1, 256)])
        payload = bytes(randomizer.randrange(0, 256) for _ in range(randomizer.randrange(0, 32)))
        return _build_masked_frame(
            opcode=randomizer.choice([0x1, 0x8, 0x9, 0xA]),
            payload=payload,
            masked=True,
            declared_length=wire_length,
            mask_key=bytes(randomizer.randrange(0, 256) for _ in range(4)),
        )
    if mode == 2:
        return bytes(randomizer.randrange(0, 256) for _ in range(randomizer.randrange(0, 64)))
    payload = ("ok-" + str(seed)).encode("utf-8")
    return _build_masked_frame(opcode=0x1, payload=payload, masked=True)


class RealtimeTests(unittest.TestCase):
    def test_websocket_accept_key_matches_reference(self) -> None:
        self.assertEqual(
            WebSocketConnection.accept_key("dGhlIHNhbXBsZSBub25jZQ=="),
            "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=",
        )

    def test_websocket_connection_is_long_lived_without_idle_timeout(self) -> None:
        fake_socket = _FakeSocket()
        connection = WebSocketConnection(fake_socket)
        self.assertIsNone(fake_socket.timeout)
        connection.close()

    def test_websocket_timeout_is_reported_as_connection_close(self) -> None:
        fake_socket = _FakeSocket(raise_timeout=True)
        connection = WebSocketConnection(fake_socket)
        with self.assertRaises(ConnectionError):
            connection.recv_text()
        connection.close()

    def test_websocket_rejects_unmasked_client_frames(self) -> None:
        fake_socket = _FakeSocket([b"\x81\x02"])
        connection = WebSocketConnection(fake_socket)
        with self.assertRaises(ConnectionError):
            connection.recv_text()
        connection.close()

    def test_websocket_rejects_oversized_frames_before_payload_read(self) -> None:
        frame_len = MAX_CLIENT_WS_FRAME_BYTES + 1
        fake_socket = _FakeSocket([b"\x81\xff", struct.pack("!Q", frame_len)])
        connection = WebSocketConnection(fake_socket)
        with self.assertRaises(ConnectionError):
            connection.recv_text()
        connection.close()

    def test_websocket_rejects_reserved_bits(self) -> None:
        frame = _build_masked_frame(opcode=0x1, payload=b"hello", rsv=0x40)
        connection = WebSocketConnection(_FakeSocket(_chunk_bytes(frame, 1)))
        with self.assertRaisesRegex(ConnectionError, "Extensionsbits"):
            connection.recv_text()
        connection.close()

    def test_websocket_rejects_oversized_control_frame_payloads(self) -> None:
        frame = _build_masked_frame(opcode=0x9, payload=b"", declared_length=126)
        connection = WebSocketConnection(_FakeSocket(_chunk_bytes(frame, 2)))
        with self.assertRaisesRegex(ConnectionError, "Control-Frames"):
            connection.recv_text()
        connection.close()

    def test_websocket_invalid_utf8_is_reported_as_connection_error(self) -> None:
        frame = _build_masked_frame(opcode=0x1, payload=b"\xff\xfe\xfa")
        connection = WebSocketConnection(_FakeSocket(_chunk_bytes(frame, 3)))
        with self.assertRaisesRegex(ConnectionError, "ungueltiges UTF-8"):
            connection.recv_text()
        connection.close()

    def test_websocket_parser_fuzz_harness_only_returns_text_or_connection_error(self) -> None:
        for seed in range(250):
            with self.subTest(seed=seed):
                frame = _random_frame(seed)
                connection = WebSocketConnection(_FakeSocket(_chunk_bytes(frame, seed + 1000)))
                try:
                    message = connection.recv_text()
                except ConnectionError:
                    pass
                except Exception as exc:  # pragma: no cover - regression guard
                    self.fail(f"Unerwarteter Parserfehler fuer Seed {seed}: {type(exc).__name__}: {exc}")
                else:
                    self.assertIsInstance(message, str)
                finally:
                    connection.close()

    def test_live_run_manager_streams_prompt_and_accepts_input(self) -> None:
        if os.name == "nt" and importlib.util.find_spec("winpty") is None:
            self.skipTest("pywinpty ist fuer Windows-PTY-Tests nicht installiert")
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            repository = SchoolRepository(config.database_path)
            repository.put_setting("runner_backend", "process")
            repository.put_setting("unsafe_process_backend_enabled", True)
            workspace = WorkspaceManager(config)
            runner = CodeRunner(config, _FakeToolSandbox(), workspace, repository)
            manager = LiveRunManager(runner, repository)

            try:
                project = {
                    "project_id": "proj-live",
                    "owner_type": "user",
                    "owner_key": "student",
                    "slug": "live-python",
                    "template": "python",
                    "runtime": "python",
                    "main_file": "main.py",
                    "name": "Live Python",
                }
                workspace.materialize_project(project)
                connection = _RecordingConnection()
                client = RealtimeClient("client-1", connection, _TeacherSession(), project)

                manager.start(
                    client,
                    {
                        "path": "main.py",
                        "language": "python",
                        "code": "name = input('Name: ')\nprint(f'Hallo {name}!')\n",
                        "client_meta": {"target_kind": "cell", "cell_id": "cell-1"},
                        "terminal": {"pty": True, "cols": 96, "rows": 28},
                    },
                )

                deadline = time.time() + 5
                session_id = ""
                while time.time() < deadline:
                    events = connection.snapshot()
                    started = next((event for event in events if event.get("type") == "run.started"), None)
                    if started:
                        session_id = str(started["session_id"])
                        break
                    time.sleep(0.05)
                self.assertTrue(session_id)
                manager.resize(_TeacherSession(), session_id, 100, 32)

                manager.send_input(_TeacherSession(), session_id, "Nova\n")

                deadline = time.time() + 5
                while time.time() < deadline:
                    events = connection.snapshot()
                    if any(event.get("type") == "run.exit" for event in events):
                        break
                    time.sleep(0.05)

                events = connection.snapshot()
                output = "".join(str(event.get("chunk", "")) for event in events if event.get("type") == "run.output")
                exit_event = next(event for event in events if event.get("type") == "run.exit")
                started_event = next(event for event in events if event.get("type") == "run.started")
                self.assertIn("Name:", output)
                self.assertIn("Hallo Nova!", output)
                self.assertEqual(exit_event["returncode"], 0)
                self.assertEqual(started_event["client_meta"]["cell_id"], "cell-1")
                self.assertEqual(exit_event["client_meta"]["target_kind"], "cell")
                self.assertTrue(started_event["terminal"]["requested"])
            finally:
                manager.close()
                repository.close()


if __name__ == "__main__":
    unittest.main()
