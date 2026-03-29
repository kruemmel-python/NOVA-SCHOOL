from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .database import SchoolRepository


DIRECT_ASSISTANT_SYSTEM_PROMPT = (
    "Du bist ein lokaler Codehelfer fuer einen Schulserver. "
    "Antworte knapp, konkret und sicherheitsbewusst. "
    "Wenn die Nutzernachricht eine exakt kurze Antwort verlangt, gib genau diese Antwort ohne Zusatztext aus. "
    "Nutze Codekontext nur, wenn die Nutzernachricht erkennbar danach fragt oder ein Codeproblem beschreibt."
)

LLAMA_CPP_RELEASE_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
LLAMA_CPP_RUNTIME_DIRNAME = "llama_cpp_runtime"
LITERT_LM_RUNTIME_DIRNAME = "litert_lm_runtime"
LLAMA_CPP_WINDOWS_ASSETS = {
    "vulkan": "llama-{tag}-bin-win-vulkan-x64.zip",
    "hip-radeon": "llama-{tag}-bin-win-hip-radeon-x64.zip",
    "cpu": "llama-{tag}-bin-win-cpu-x64.zip",
}
LITERT_LM_WINDOWS_BINARIES = (
    "lit.windows_x86_64.exe",
    "lit.exe",
    "lit",
)
THINK_BLOCK_PATTERN = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)
THINK_TAG_PATTERN = re.compile(r"</?think\b[^>]*>", re.IGNORECASE)
MODEL_ID_SANITIZE_PATTERN = re.compile(r"[^a-z0-9]+")
SHORT_REPLY_PATTERNS = (
    re.compile(r"^\s*antworte\s+(?:bitte\s+)?nur\s+mit\s+(?P<target>.+?)\s*$", re.IGNORECASE | re.DOTALL),
    re.compile(r"^\s*gib\s+(?:bitte\s+)?nur\s+(?P<target>.+?)\s+aus\s*$", re.IGNORECASE | re.DOTALL),
    re.compile(r"^\s*(?:reply|respond)\s+(?:please\s+)?only\s+with\s+(?P<target>.+?)\s*$", re.IGNORECASE | re.DOTALL),
)
LITERT_INPUT_TOKEN_LIMIT_PATTERN = re.compile(
    r"Input token ids are too long.*?(\d+)\s*>=\s*(\d+)",
    re.IGNORECASE | re.DOTALL,
)


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(float(value))
    except Exception:
        parsed = default
    return max(minimum, min(parsed, maximum))


def _clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        parsed = default
    return max(minimum, min(parsed, maximum))


def _sanitize_model_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = THINK_BLOCK_PATTERN.sub("", text)
    text = THINK_TAG_PATTERN.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _unwrap_short_reply(value: str) -> str:
    text = _sanitize_model_text(value).splitlines()[0].strip() if str(value or "").strip() else ""
    if text.startswith(("**", "__")) and text.endswith(("**", "__")) and len(text) > 4:
        text = text[2:-2].strip()
    if text.startswith(("*", "_", "`")) and text.endswith(("*", "_", "`")) and len(text) > 2:
        text = text[1:-1].strip()
    if text and text[-1] in ".!?" and text.count(" ") <= 4:
        text = text[:-1].rstrip()
    return text.strip()


def _extract_exact_short_reply_target(prompt: str) -> str:
    text = str(prompt or "").strip()
    if not text:
        return ""
    for pattern in SHORT_REPLY_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        target = str(match.group("target") or "").strip()
        if not target:
            return ""
        if len(target) >= 2 and target[0] in "\"'`" and target[-1] == target[0]:
            target = target[1:-1].strip()
        target = re.sub(r"\s+", " ", target)
        if target and target[-1] in ".!?" and target.count(" ") <= 4:
            target = target[:-1].rstrip()
        return target
    return ""


def _normalize_model_label(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        text = str(fallback or "").strip()
    if not text:
        return ""
    candidate = text.replace("\\", "/").split("/")[-1].strip()
    if candidate.lower().endswith(".gguf"):
        return Path(candidate).stem
    return candidate


def _sanitize_model_id(value: Any, *, fallback: str = "local-model") -> str:
    text = _normalize_model_label(value, fallback=fallback).lower()
    text = text.replace("_", "-")
    text = MODEL_ID_SANITIZE_PATTERN.sub("-", text).strip("-")
    return text or fallback


def _same_drive(left: Path, right: Path) -> bool:
    return bool(left.drive and right.drive and left.drive.casefold() == right.drive.casefold())


class LlamaCppService:
    provider_id = "server-llama.cpp"
    engine_id = "llama-server"

    def __init__(self, repository: SchoolRepository, *, base_path: Path, data_path: Path) -> None:
        self.repository = repository
        self.base_path = Path(base_path).resolve(strict=False)
        self.data_path = Path(data_path).resolve(strict=False)
        self.runtime_root = self.data_path / LLAMA_CPP_RUNTIME_DIRNAME
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None
        self._process_key: tuple[Any, ...] | None = None
        self._binary_path: Path | None = None
        self._idle_timer: threading.Timer | None = None
        self._last_error = ""

    def model_roots(self) -> list[Path]:
        package_root = Path(__file__).resolve(strict=False).parent
        candidates = [
            self.base_path / "Model",
            self.base_path / "nova_school_server" / "Model",
            package_root / "Model",
        ]
        seen: set[str] = set()
        unique: list[Path] = []
        for candidate in candidates:
            resolved = candidate.resolve(strict=False)
            key = str(resolved).lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(resolved)
        return unique

    @property
    def model_root(self) -> Path:
        for root in self.model_roots():
            if root.exists() and root.is_dir():
                return root
        return self.model_roots()[0]

    @property
    def explicit_model_path(self) -> str:
        return str(self.repository.get_setting("llamacpp_model_path", "") or "").strip()

    @property
    def model_label(self) -> str:
        return str(self.repository.get_setting("llamacpp_model_alias", "") or "").strip()

    @property
    def max_tokens(self) -> int:
        return _clamp_int(self.repository.get_setting("ondevice_max_tokens", 1024), 1024, 128, 8192)

    @property
    def top_k(self) -> int:
        return _clamp_int(self.repository.get_setting("ondevice_top_k", 40), 40, 1, 100)

    @property
    def temperature(self) -> float:
        return _clamp_float(self.repository.get_setting("ondevice_temperature", 0.7), 0.7, 0.0, 2.0)

    @property
    def random_seed(self) -> int:
        return _clamp_int(self.repository.get_setting("ondevice_random_seed", 1), 1, 0, 2_147_483_647)

    @property
    def backend(self) -> str:
        value = str(self.repository.get_setting("llamacpp_backend", "vulkan") or "vulkan").strip().lower()
        return value if value in LLAMA_CPP_WINDOWS_ASSETS else "vulkan"

    @property
    def ctx_size(self) -> int:
        return _clamp_int(self.repository.get_setting("llamacpp_ctx_size", 4096), 4096, 1024, 65536)

    @property
    def gpu_layers(self) -> int:
        return _clamp_int(self.repository.get_setting("llamacpp_gpu_layers", 99), 99, 0, 999)

    @property
    def threads(self) -> int:
        return _clamp_int(self.repository.get_setting("llamacpp_threads", 0), 0, 0, 256)

    @property
    def sleep_idle_seconds(self) -> int:
        return _clamp_int(self.repository.get_setting("llamacpp_sleep_idle_seconds", 45), 45, 5, 3600)

    @property
    def port(self) -> int:
        return _clamp_int(self.repository.get_setting("llamacpp_port", 11435), 11435, 1025, 65535)

    @property
    def server_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def explicit_binary_path(self) -> str:
        return str(self.repository.get_setting("llamacpp_server_path", "") or "").strip()

    def generation_options(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "top_k": self.top_k,
            "temperature": self.temperature,
            "random_seed": self.random_seed,
        }

    def local_model_files(self) -> list[Path]:
        def sort_key(path: Path) -> tuple[int, str]:
            name = path.name.lower()
            score = 100
            if "gemma" in name:
                score -= 20
            if "1b" in name:
                score -= 10
            if "q4" in name:
                score -= 8
            elif "q6" in name:
                score -= 4
            if "uncensored" in name or "thinking" in name or "heretic" in name:
                score += 15
            return score, name

        for root in self.model_roots():
            if not root.exists() or not root.is_dir():
                continue
            files: list[Path] = []
            for path in root.iterdir():
                if not path.is_file() or path.suffix.lower() != ".gguf":
                    continue
                files.append(path.resolve(strict=False))
            if files:
                return sorted(files, key=sort_key)

        return []

    def resolved_model_path(self) -> Path | None:
        explicit = self.explicit_model_path
        if explicit:
            candidate = Path(explicit).expanduser().resolve(strict=False)
            if candidate.exists() and candidate.is_file():
                return candidate
        files = self.local_model_files()
        return files[0] if files else None

    def resolved_model_label(self) -> str:
        if self.model_label:
            return self.model_label
        path = self.resolved_model_path()
        return path.stem if path else ""

    def _discover_binary_candidates(self) -> list[Path]:
        candidates: list[Path] = []
        explicit = self.explicit_binary_path
        if explicit:
            candidates.append(Path(explicit).expanduser().resolve(strict=False))
        discovered = shutil.which("llama-server.exe") or shutil.which("llama-server")
        if discovered:
            candidates.append(Path(discovered).resolve(strict=False))
        candidates.extend(self.runtime_root.rglob("llama-server.exe"))
        seen: set[str] = set()
        unique: list[Path] = []
        for item in candidates:
            key = str(item).lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _request_json(self, url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
        data = None
        headers = {"User-Agent": "NovaSchoolServer/llama.cpp", "Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _latest_release(self) -> dict[str, Any]:
        return self._request_json(LLAMA_CPP_RELEASE_API, timeout=20.0)

    def _download_binary(self) -> Path:
        release = self._latest_release()
        tag = str(release.get("tag_name") or "").strip()
        if not tag:
            raise RuntimeError("Konnte die aktuelle llama.cpp-Release nicht bestimmen.")
        expected_name = LLAMA_CPP_WINDOWS_ASSETS[self.backend].format(tag=tag)
        assets = list(release.get("assets") or [])
        asset = next((item for item in assets if str(item.get("name") or "") == expected_name), None)
        if not isinstance(asset, dict):
            raise RuntimeError(f"Keine passende llama.cpp-Binary fuer Backend '{self.backend}' gefunden.")

        download_url = str(asset.get("browser_download_url") or "").strip()
        if not download_url:
            raise RuntimeError("Release-Asset fuer llama.cpp hat keine Download-URL.")

        extract_root = self.runtime_root / tag / self.backend
        binary_path = next((path for path in extract_root.rglob("llama-server.exe") if path.is_file()), None)
        if binary_path:
            return binary_path

        extract_root.mkdir(parents=True, exist_ok=True)
        archive_path = extract_root / expected_name
        if not archive_path.exists():
            request = Request(download_url, headers={"User-Agent": "NovaSchoolServer/llama.cpp"})
            with urlopen(request, timeout=120.0) as response, archive_path.open("wb") as target:
                shutil.copyfileobj(response, target)

        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_root)
        binary_path = next((path for path in extract_root.rglob("llama-server.exe") if path.is_file()), None)
        if not binary_path:
            raise RuntimeError("Die heruntergeladene llama.cpp-Binary enthaelt kein llama-server.exe.")
        return binary_path

    def _ensure_binary_path(self) -> Path:
        if self._binary_path and self._binary_path.exists():
            return self._binary_path
        for candidate in self._discover_binary_candidates():
            if candidate.exists() and candidate.is_file():
                self._binary_path = candidate
                return candidate
        self._binary_path = self._download_binary()
        return self._binary_path

    def _desired_process_key(self) -> tuple[Any, ...]:
        model_path = self.resolved_model_path()
        return (
            str(self._ensure_binary_path()),
            str(model_path or ""),
            self.resolved_model_label(),
            self.backend,
            self.port,
            self.ctx_size,
            self.gpu_layers,
            self.threads,
            self.sleep_idle_seconds,
        )

    def _build_command(self, binary_path: Path, model_path: Path) -> list[str]:
        command = [
            str(binary_path),
            "-m",
            str(model_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "--alias",
            self.resolved_model_label() or model_path.name,
            "-c",
            str(self.ctx_size),
            "-n",
            str(self.max_tokens),
            "--top-k",
            str(self.top_k),
            "--temp",
            str(self.temperature),
            "--seed",
            str(self.random_seed),
            "--parallel",
            "1",
            "--no-cache-prompt",
            "--cache-ram",
            "0",
            "--log-file",
            str(self.runtime_root / "llama_server.log"),
        ]
        if self.threads > 0:
            command.extend(["-t", str(self.threads), "-tb", str(self.threads)])
        if self.gpu_layers >= 0:
            command.extend(["-ngl", str(self.gpu_layers)])
        return command

    def _poll_health(self, *, timeout_seconds: float = 90.0) -> None:
        deadline = time.time() + timeout_seconds
        last_error = ""
        while time.time() < deadline:
            process = self._process
            if process and process.poll() is not None:
                break
            try:
                self._request_json(urljoin(self.server_url, "/health"), timeout=2.0)
                self._last_error = ""
                return
            except Exception as exc:  # pragma: no cover - depends on runtime
                last_error = str(exc)
                time.sleep(1.0)
        if self._process and self._process.poll() is None:
            raise RuntimeError(f"llama-server hat innerhalb von {int(timeout_seconds)}s keinen Health-Status geliefert. {last_error}".strip())
        raise RuntimeError(self._read_failure_details(last_error))

    def _read_failure_details(self, fallback: str) -> str:
        log_path = self.runtime_root / "llama_server.log"
        if log_path.exists():
            try:
                tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:])
            except Exception:
                tail = ""
            if tail.strip():
                return f"llama-server konnte nicht starten.\n{tail}"
        return f"llama-server konnte nicht starten. {fallback}".strip()

    def _stop_process_locked(self) -> None:
        self._cancel_idle_timer_locked()
        if not self._process:
            return
        process = self._process
        self._process = None
        self._process_key = None
        try:
            process.terminate()
            process.wait(timeout=10)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def close(self) -> None:
        with self._lock:
            self._stop_process_locked()

    def _cancel_idle_timer_locked(self) -> None:
        if not self._idle_timer:
            return
        try:
            self._idle_timer.cancel()
        except Exception:
            pass
        self._idle_timer = None

    def _schedule_idle_shutdown(self) -> None:
        delay = self.sleep_idle_seconds
        if delay <= 0:
            return

        def shutdown() -> None:
            with self._lock:
                self._idle_timer = None
                self._stop_process_locked()

        with self._lock:
            self._cancel_idle_timer_locked()
            timer = threading.Timer(delay, shutdown)
            timer.daemon = True
            self._idle_timer = timer
            timer.start()

    def ensure_server_ready(self) -> None:
        with self._lock:
            self._cancel_idle_timer_locked()
            model_path = self.resolved_model_path()
            if model_path is None:
                raise RuntimeError("Kein GGUF-Modell gefunden. Bitte eine .gguf-Datei in den Ordner Model legen oder llamacpp_model_path setzen.")
            binary_path = self._ensure_binary_path()
            desired_key = self._desired_process_key()
            process = self._process
            if process and process.poll() is None and self._process_key == desired_key:
                try:
                    self._request_json(urljoin(self.server_url, "/health"), timeout=1.5)
                    self._last_error = ""
                    return
                except Exception:
                    self._stop_process_locked()
            else:
                self._stop_process_locked()

            command = self._build_command(binary_path, model_path)
            creationflags = 0
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW")
            self._process = subprocess.Popen(
                command,
                cwd=str(binary_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                text=True,
            )
            self._process_key = desired_key
        self._poll_health()

    def complete(
        self,
        *,
        prompt: str,
        system_prompt: str = "",
        response_format: dict[str, Any] | None = None,
        generation_options: dict[str, Any] | None = None,
        timeout_seconds: float = 120.0,
    ) -> tuple[str, str]:
        self.ensure_server_ready()
        options = dict(self.generation_options())
        if isinstance(generation_options, dict):
            options["max_tokens"] = _clamp_int(generation_options.get("max_tokens", options["max_tokens"]), options["max_tokens"], 64, 8192)
            options["top_k"] = _clamp_int(generation_options.get("top_k", options["top_k"]), options["top_k"], 1, 100)
            options["temperature"] = _clamp_float(generation_options.get("temperature", options["temperature"]), options["temperature"], 0.0, 2.0)
            options["random_seed"] = _clamp_int(generation_options.get("random_seed", options["random_seed"]), options["random_seed"], 0, 2_147_483_647)

        messages = []
        system_text = str(system_prompt or "").strip()
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": str(prompt or "")})
        payload: dict[str, Any] = {
            "model": self.resolved_model_label() or "nova-local-gguf",
            "messages": messages,
            "stream": False,
            "max_tokens": options["max_tokens"],
            "top_k": options["top_k"],
            "temperature": options["temperature"],
            "seed": options["random_seed"],
        }
        if isinstance(response_format, dict):
            payload["response_format"] = response_format

        try:
            response = self._request_json(
                urljoin(self.server_url, "/v1/chat/completions"),
                method="POST",
                payload=payload,
                timeout=timeout_seconds,
            )
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            self.close()
            raise RuntimeError(f"llama-server Fehler {exc.code}: {body}") from exc
        except URLError as exc:
            self.close()
            raise RuntimeError(f"llama-server ist nicht erreichbar: {exc.reason}") from exc

        try:
            choice = list(response.get("choices") or [])[0]
            message = dict(choice.get("message") or {})
            text = _sanitize_model_text(message.get("content") or "")
        except Exception as exc:
            self.close()
            raise RuntimeError(f"Unerwartete Antwort von llama-server: {response}") from exc
        if not text:
            self.close()
            raise RuntimeError("llama-server hat keine Textantwort geliefert.")
        model = _normalize_model_label(response.get("model"), fallback=self.resolved_model_label())
        self._schedule_idle_shutdown()
        return text, model

    def prepare_direct_completion(self, *, prompt: str, code: str, path_hint: str) -> dict[str, str]:
        context_bits = [prompt]
        code_text = str(code or "").strip()
        if code_text:
            context_bits.append(f"Codekontext:\n```text\n{code_text}\n```")
        path_text = str(path_hint or "").strip()
        if path_text:
            context_bits.append(f"Aktive Datei: {path_text}")
        return {
            "prompt": "\n\n".join(context_bits),
            "system_prompt": DIRECT_ASSISTANT_SYSTEM_PROMPT,
        }

    def complete_direct_completion(self, *, prompt: str, code: str, path_hint: str) -> dict[str, Any]:
        prepared = self.prepare_direct_completion(prompt=prompt, code=code, path_hint=path_hint)
        exact_target = _extract_exact_short_reply_target(prompt)
        text, model = self.complete(
            prompt=prepared["prompt"],
            system_prompt=prepared["system_prompt"],
            generation_options={
                "max_tokens": 48 if exact_target else min(self.max_tokens, 384),
                "temperature": 0.0 if exact_target else min(self.temperature, 0.35),
            },
            timeout_seconds=90.0,
        )
        if exact_target:
            reply = _unwrap_short_reply(text)
            if not reply:
                text = exact_target
            elif reply.casefold() == exact_target.casefold() or exact_target.casefold() in reply.casefold():
                text = exact_target
            else:
                text = reply
        return {"provider": self.provider_id, "model": model, "text": text}

    def status(self, *, enabled: bool = True) -> dict[str, Any]:
        model_path = self.resolved_model_path()
        binary_candidates = self._discover_binary_candidates()
        running = bool(self._process and self._process.poll() is None)
        warning = self._last_error or (
            f"GGUF-Modell ist lokal konfiguriert. Der llama.cpp-Server startet bei Bedarf "
            f"und entlaedt sich nach {self.sleep_idle_seconds}s Leerlauf automatisch."
        )
        return {
            "provider": self.provider_id,
            "engine": self.engine_id,
            "runtime": "server",
            "enabled": bool(enabled),
            "configured": bool(model_path),
            "model_path": str(model_path or ""),
            "model_label": self.resolved_model_label(),
            "server_url": self.server_url,
            "backend": self.backend,
            "binary_path": str(self._binary_path or (binary_candidates[0] if binary_candidates else "")),
            "generation_options": self.generation_options(),
            "requires_webgpu": False,
            "supports_local_file": False,
            "running": running,
            "warning": warning,
        }


class LiteRTLmService:
    provider_id = "server-litert-lm"
    engine_id = "lit"

    def __init__(self, repository: SchoolRepository, *, base_path: Path, data_path: Path) -> None:
        self.repository = repository
        self.base_path = Path(base_path).resolve(strict=False)
        self.data_path = Path(data_path).resolve(strict=False)
        self.runtime_root = self.data_path / LITERT_LM_RUNTIME_DIRNAME
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None
        self._process_key: tuple[Any, ...] | None = None
        self._binary_path: Path | None = None
        self._idle_timer: threading.Timer | None = None
        self._last_error = ""

    def model_roots(self) -> list[Path]:
        package_root = Path(__file__).resolve(strict=False).parent
        candidates = [
            self.base_path / "Model",
            self.base_path / "nova_school_server" / "Model",
            package_root / "Model",
        ]
        binary_dir = self._explicit_binary_directory()
        if binary_dir is not None:
            candidates.append(binary_dir)
        candidates.append(Path("D:/LIT"))
        seen: set[str] = set()
        unique: list[Path] = []
        for candidate in candidates:
            resolved = candidate.resolve(strict=False)
            key = str(resolved).lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(resolved)
        return unique

    @property
    def explicit_model_path(self) -> str:
        return str(self.repository.get_setting("litertlm_model_path", "") or "").strip()

    @property
    def model_label(self) -> str:
        return str(self.repository.get_setting("litertlm_model_alias", "") or "").strip()

    @property
    def backend(self) -> str:
        value = str(self.repository.get_setting("litertlm_backend", "cpu") or "cpu").strip().lower()
        return value if value in {"cpu", "gpu"} else "cpu"

    @property
    def max_tokens(self) -> int:
        return _clamp_int(self.repository.get_setting("ondevice_max_tokens", 1024), 1024, 64, 8192)

    @property
    def top_k(self) -> int:
        return _clamp_int(self.repository.get_setting("ondevice_top_k", 40), 40, 1, 100)

    @property
    def temperature(self) -> float:
        return _clamp_float(self.repository.get_setting("ondevice_temperature", 0.7), 0.7, 0.0, 2.0)

    @property
    def random_seed(self) -> int:
        return _clamp_int(self.repository.get_setting("ondevice_random_seed", 1), 1, 0, 2_147_483_647)

    @property
    def sleep_idle_seconds(self) -> int:
        return _clamp_int(self.repository.get_setting("litertlm_sleep_idle_seconds", 45), 45, 5, 3600)

    @property
    def port(self) -> int:
        return _clamp_int(self.repository.get_setting("litertlm_port", 9379), 9379, 1025, 65535)

    @property
    def server_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def explicit_binary_path(self) -> str:
        return str(self.repository.get_setting("litertlm_binary_path", "") or "").strip()

    @property
    def explicit_home_path(self) -> str:
        return str(self.repository.get_setting("litertlm_home_path", "") or "").strip()

    def generation_options(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "top_k": self.top_k,
            "temperature": self.temperature,
            "random_seed": self.random_seed,
        }

    def local_model_files(self) -> list[Path]:
        def sort_key(path: Path) -> tuple[int, str]:
            name = path.name.lower()
            score = 100
            if "gemma-3n-e4b" in name or "gemma3n-e4b" in name:
                score -= 30
            elif "gemma-3n-e2b" in name or "gemma3n-e2b" in name:
                score -= 20
            elif "gemma3-1b" in name or "gemma-3-1b" in name:
                score -= 10
            if "int4" in name or "q4" in name:
                score -= 5
            return score, name

        for root in self.model_roots():
            if not root.exists() or not root.is_dir():
                continue
            files = [path.resolve(strict=False) for path in root.iterdir() if path.is_file() and path.suffix.lower() == ".litertlm"]
            if files:
                return sorted(files, key=sort_key)
        return []

    def resolved_model_path(self) -> Path | None:
        explicit = self.explicit_model_path
        if explicit:
            candidate = Path(explicit).expanduser().resolve(strict=False)
            if candidate.exists() and candidate.is_file():
                return candidate
        files = self.local_model_files()
        return files[0] if files else None

    def resolved_model_label(self) -> str:
        if self.model_label:
            return self.model_label
        path = self.resolved_model_path()
        return path.stem if path else ""

    def resolved_model_id(self) -> str:
        path = self.resolved_model_path()
        label = (self.model_label or (path.stem if path else "")).lower()
        known_aliases = (
            ("gemma-3n-e4b", "gemma3n-e4b"),
            ("gemma3n-e4b", "gemma3n-e4b"),
            ("gemma-3n-e2b", "gemma3n-e2b"),
            ("gemma3n-e2b", "gemma3n-e2b"),
            ("gemma3-1b", "gemma3-1b"),
            ("gemma-3-1b", "gemma3-1b"),
            ("phi-4-mini", "phi4-mini"),
            ("phi4-mini", "phi4-mini"),
            ("qwen2.5-1.5b", "qwen2.5-1.5b"),
        )
        for needle, alias in known_aliases:
            if needle in label:
                return alias
        return _sanitize_model_id(label, fallback="local-litert")

    def resolved_home_root(self) -> Path:
        explicit = self.explicit_home_path
        if explicit:
            return Path(explicit).expanduser().resolve(strict=False)
        model_path = self.resolved_model_path()
        binary_dir = self._explicit_binary_directory()
        if model_path is not None:
            if binary_dir is not None and _same_drive(binary_dir, model_path):
                return binary_dir
            return model_path.parent
        if binary_dir is not None:
            return binary_dir
        return self.runtime_root

    def lit_root(self) -> Path:
        return self.resolved_home_root() / ".litert-lm"

    def model_registry_dir(self) -> Path:
        return self.lit_root() / "models" / self.resolved_model_id()

    def registry_model_path(self) -> Path:
        return self.model_registry_dir() / "model.litertlm"

    def registry_cache_path(self) -> Path:
        return self.model_registry_dir() / "model.litertlm.xnnpack_cache"

    def _explicit_binary_directory(self) -> Path | None:
        explicit = self.explicit_binary_path
        if not explicit:
            return None
        candidate = Path(explicit).expanduser().resolve(strict=False)
        if candidate.exists():
            return candidate.parent if candidate.is_file() else candidate
        return candidate.parent if candidate.suffix else candidate

    def _discover_binary_candidates(self) -> list[Path]:
        candidates: list[Path] = []
        explicit = self.explicit_binary_path
        if explicit:
            candidates.append(Path(explicit).expanduser().resolve(strict=False))
        for name in LITERT_LM_WINDOWS_BINARIES:
            discovered = shutil.which(name)
            if discovered:
                candidates.append(Path(discovered).resolve(strict=False))
        candidates.extend(
            [
                Path("D:/LIT/lit.windows_x86_64.exe"),
                self.base_path / "lit.windows_x86_64.exe",
                self.base_path / "tools" / "lit" / "lit.windows_x86_64.exe",
            ]
        )
        seen: set[str] = set()
        unique: list[Path] = []
        for item in candidates:
            key = str(item).lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _ensure_binary_path(self) -> Path:
        if self._binary_path and self._binary_path.exists():
            return self._binary_path
        for candidate in self._discover_binary_candidates():
            if candidate.exists() and candidate.is_file():
                self._binary_path = candidate
                return candidate
        raise RuntimeError(
            "LiteRT-LM-Binary nicht gefunden. Bitte lit.windows_x86_64.exe ablegen oder litertlm_binary_path setzen."
        )

    def _register_model_file(self, target: Path, source: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            try:
                if os.path.samefile(target, source):
                    return
            except Exception:
                pass
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            except Exception:
                pass
        try:
            if _same_drive(target, source):
                os.link(source, target)
                return
        except Exception:
            pass
        try:
            os.symlink(str(source), str(target))
            return
        except Exception:
            pass
        shutil.copy2(source, target)

    def ensure_model_registered(self) -> tuple[Path, Path]:
        model_path = self.resolved_model_path()
        if model_path is None:
            raise RuntimeError(
                "Kein LiteRT-LM-Modell gefunden. Bitte eine .litertlm-Datei in den Ordner Model legen oder litertlm_model_path setzen."
            )
        registry_model_path = self.registry_model_path()
        self._register_model_file(registry_model_path, model_path)
        cache_target = self.registry_cache_path()
        if cache_target.exists() and cache_target.is_file() and cache_target.stat().st_size == 0:
            cache_target.unlink(missing_ok=True)
        return model_path, registry_model_path

    def _desired_process_key(self) -> tuple[Any, ...]:
        model_path = self.resolved_model_path()
        return (
            str(self._ensure_binary_path()),
            str(model_path or ""),
            self.resolved_model_id(),
            self.backend,
            self.port,
            str(self.resolved_home_root()),
            self.sleep_idle_seconds,
        )

    def _build_command(self, binary_path: Path) -> list[str]:
        return [str(binary_path), "serve", "--port", str(self.port)]

    def _request_json(self, url: str, *, payload: dict[str, Any] | None = None, timeout: float = 30.0) -> dict[str, Any]:
        data = None
        headers = {"User-Agent": "NovaSchoolServer/LiteRT-LM", "Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _probe_server(self, *, timeout_seconds: float = 20.0) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            process = self._process
            if process and process.poll() is not None:
                break
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=1.0):
                    self._last_error = ""
                    return
            except OSError:
                time.sleep(0.5)
        raise RuntimeError(self._read_failure_details("LiteRT-LM-Server hat keinen offenen Port gemeldet."))

    def _read_failure_details(self, fallback: str) -> str:
        log_path = self.resolved_home_root() / "lit_serve.log"
        if log_path.exists():
            try:
                tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])
            except Exception:
                tail = ""
            if tail.strip():
                return f"LiteRT-LM-Server konnte nicht starten.\n{tail}"
        return f"LiteRT-LM-Server konnte nicht starten. {fallback}".strip()

    def _stop_process_locked(self) -> None:
        self._cancel_idle_timer_locked()
        if not self._process:
            return
        process = self._process
        self._process = None
        self._process_key = None
        try:
            process.terminate()
            process.wait(timeout=10)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def close(self) -> None:
        with self._lock:
            self._stop_process_locked()

    def _cancel_idle_timer_locked(self) -> None:
        if not self._idle_timer:
            return
        try:
            self._idle_timer.cancel()
        except Exception:
            pass
        self._idle_timer = None

    def _schedule_idle_shutdown(self) -> None:
        delay = self.sleep_idle_seconds
        if delay <= 0:
            return

        def shutdown() -> None:
            with self._lock:
                self._idle_timer = None
                self._stop_process_locked()

        with self._lock:
            self._cancel_idle_timer_locked()
            timer = threading.Timer(delay, shutdown)
            timer.daemon = True
            self._idle_timer = timer
            timer.start()

    def ensure_server_ready(self) -> None:
        with self._lock:
            self._cancel_idle_timer_locked()
            model_path = self.resolved_model_path()
            if model_path is None:
                raise RuntimeError(
                    "Kein LiteRT-LM-Modell gefunden. Bitte eine .litertlm-Datei in den Ordner Model legen oder litertlm_model_path setzen."
                )
            self.ensure_model_registered()
            binary_path = self._ensure_binary_path()
            desired_key = self._desired_process_key()
            process = self._process
            if process and process.poll() is None and self._process_key == desired_key:
                try:
                    self._probe_server(timeout_seconds=1.0)
                    return
                except Exception:
                    self._stop_process_locked()
            else:
                self._stop_process_locked()

            home_root = self.resolved_home_root()
            home_root.mkdir(parents=True, exist_ok=True)
            log_path = home_root / "lit_serve.log"
            creationflags = 0
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW")
            command = self._build_command(binary_path)
            environment = dict(os.environ)
            environment["USERPROFILE"] = str(home_root)
            environment["HOME"] = str(home_root)
            log_handle = log_path.open("a", encoding="utf-8", errors="replace")
            try:
                self._process = subprocess.Popen(
                    command,
                    cwd=str(binary_path.parent),
                    stdout=log_handle,
                    stderr=log_handle,
                    creationflags=creationflags,
                    text=True,
                    env=environment,
                )
            finally:
                log_handle.close()
            self._process_key = desired_key
        self._probe_server()

    def _compose_prompt(self, *, prompt: str, system_prompt: str) -> str:
        prompt_text = str(prompt or "").strip()
        system_text = str(system_prompt or "").strip()
        if system_text and prompt_text:
            return (
                "Systemanweisung fuer diese Antwort. Halte dich strikt daran:\n"
                f"{system_text}\n\n"
                "Nutzeranfrage:\n"
                f"{prompt_text}"
            )
        return prompt_text or system_text

    def _build_run_command(self, binary_path: Path, model_path: Path, prompt_file: Path) -> list[str]:
        return [
            str(binary_path),
            "--min_log_level",
            "4",
            "run",
            str(model_path),
            "--backend",
            self.backend,
            "-f",
            str(prompt_file),
        ]

    def _cli_environment(self) -> dict[str, str]:
        home_root = self.resolved_home_root()
        home_root.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
        environment["USERPROFILE"] = str(home_root)
        environment["HOME"] = str(home_root)
        return environment

    def _prompt_file_path(self) -> Path:
        prompt_dir = self.resolved_home_root() / ".litert-lm" / "requests"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"{int(time.time() * 1000)}-{os.getpid()}-{threading.get_ident()}"
        return prompt_dir / f"prompt-{suffix}.txt"

    def _extract_cli_response_text(self, raw_output: str) -> str:
        text = str(raw_output or "").replace("\r\n", "\n").replace("\r", "\n")
        cleaned_lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            if stripped.startswith("INFO: Created TensorFlow Lite XNNPACK delegate"):
                continue
            if stripped.startswith("Model \"") and "loaded. Start chatting" in stripped:
                continue
            if stripped == "Exiting." or stripped == ">>>":
                continue
            cleaned_lines.append(line)
        cleaned = _sanitize_model_text("\n".join(cleaned_lines))
        if not cleaned:
            raise RuntimeError("LiteRT-LM hat keine Textantwort geliefert.")
        return cleaned

    def _extract_response_text(self, response: dict[str, Any]) -> str:
        candidates = list(response.get("candidates") or [])
        if not candidates:
            raise RuntimeError(f"Unerwartete LiteRT-LM-Antwort: {response}")
        content = dict(candidates[0].get("content") or {})
        texts: list[str] = []
        for part in list(content.get("parts") or []):
            if isinstance(part, dict) and str(part.get("text") or "").strip():
                texts.append(str(part.get("text") or ""))
        text = _sanitize_model_text("\n".join(texts))
        if not text:
            raise RuntimeError("LiteRT-LM hat keine Textantwort geliefert.")
        return text

    def _request_completion(self, payload: dict[str, Any], *, timeout_seconds: float) -> dict[str, Any]:
        model_id = self.resolved_model_id()
        backend_suffix = f",{self.backend}" if self.backend else ""
        endpoint = urljoin(self.server_url, f"/v1beta/models/{model_id}{backend_suffix}:generateContent")
        return self._request_json(endpoint, payload=payload, timeout=timeout_seconds)

    def complete(
        self,
        *,
        prompt: str,
        system_prompt: str = "",
        response_format: dict[str, Any] | None = None,
        generation_options: dict[str, Any] | None = None,
        timeout_seconds: float = 120.0,
    ) -> tuple[str, str]:
        _ = response_format
        _ = generation_options
        model_path = self.resolved_model_path()
        if model_path is None:
            raise RuntimeError(
                "Kein LiteRT-LM-Modell gefunden. Bitte eine .litertlm-Datei in den Ordner Model legen oder litertlm_model_path setzen."
            )
        binary_path = self._ensure_binary_path()
        prompt_file = self._prompt_file_path()
        prompt_file.write_text(self._compose_prompt(prompt=prompt, system_prompt=system_prompt), encoding="utf-8")
        creationflags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW")
        command = self._build_run_command(binary_path, model_path, prompt_file)
        try:
            with self._lock:
                result = subprocess.run(
                    command,
                    cwd=str(binary_path.parent),
                    capture_output=True,
                    text=True,
                    env=self._cli_environment(),
                    timeout=timeout_seconds,
                    creationflags=creationflags,
                )
            combined_output = "\n".join(part for part in (result.stdout, result.stderr) if str(part or "").strip())
            if result.returncode != 0:
                token_limit_match = LITERT_INPUT_TOKEN_LIMIT_PATTERN.search(combined_output)
                if token_limit_match:
                    observed_tokens, token_limit = token_limit_match.groups()
                    self._last_error = (
                        f"LiteRT-LM Kontextlimit ueberschritten ({observed_tokens} >= {token_limit} Tokens). "
                        "Der Prompt muss vor dem Modellaufruf weiter gekuerzt werden."
                    )
                else:
                    self._last_error = combined_output.strip() or f"LiteRT-LM beendet sich mit Exit-Code {result.returncode}."
                raise RuntimeError(self._last_error)
            text = self._extract_cli_response_text(combined_output)
            self._last_error = ""
            return text, self.resolved_model_label() or model_path.name
        except subprocess.TimeoutExpired as exc:
            partial_output = "\n".join(part for part in (exc.stdout, exc.stderr) if str(part or "").strip())
            if partial_output.strip():
                try:
                    partial_text = self._extract_cli_response_text(partial_output)
                    if partial_text and (len(partial_text) >= 24 or "```" in partial_text or "\n" in partial_text):
                        self._last_error = "LiteRT-LM lieferte vor dem Timeout nur eine Teilausgabe."
                        return partial_text, self.resolved_model_label() or model_path.name
                except Exception:
                    pass
            self._last_error = (
                f"LiteRT-LM hat nach {timeout_seconds:.0f}s keine Antwort geliefert."
            )
            raise RuntimeError(self._last_error) from exc
        finally:
            try:
                prompt_file.unlink(missing_ok=True)
            except Exception:
                pass

    def prepare_direct_completion(self, *, prompt: str, code: str, path_hint: str) -> dict[str, str]:
        context_bits = [prompt]
        code_text = str(code or "").strip()
        if code_text:
            context_bits.append(f"Codekontext:\n```text\n{code_text}\n```")
        path_text = str(path_hint or "").strip()
        if path_text:
            context_bits.append(f"Aktive Datei: {path_text}")
        return {
            "prompt": "\n\n".join(context_bits),
            "system_prompt": DIRECT_ASSISTANT_SYSTEM_PROMPT,
        }

    def complete_direct_completion(self, *, prompt: str, code: str, path_hint: str) -> dict[str, Any]:
        prepared = self.prepare_direct_completion(prompt=prompt, code=code, path_hint=path_hint)
        exact_target = _extract_exact_short_reply_target(prompt)
        text, model = self.complete(
            prompt=prepared["prompt"],
            system_prompt=prepared["system_prompt"],
            generation_options={
                "max_tokens": 48 if exact_target else min(self.max_tokens, 384),
                "temperature": 0.0 if exact_target else min(self.temperature, 0.35),
            },
            timeout_seconds=90.0,
        )
        if exact_target:
            reply = _unwrap_short_reply(text)
            if not reply:
                text = exact_target
            elif reply.casefold() == exact_target.casefold() or exact_target.casefold() in reply.casefold():
                text = exact_target
            else:
                text = reply
        return {"provider": self.provider_id, "model": model, "text": text}

    def status(self, *, enabled: bool = True) -> dict[str, Any]:
        model_path = self.resolved_model_path()
        binary_candidates = self._discover_binary_candidates()
        warning = self._last_error or (
            "LiteRT-LM laeuft lokal pro Anfrage ueber 'lit run'. "
            "Der erste Lauf nach Modell- oder Cache-Aenderungen kann deutlich laenger dauern."
        )
        if self.backend == "gpu":
            warning = (
                f"{warning} GPU-Backend auf Windows benoetigt dxil.dll und dxcompiler.dll neben der lit-Binary."
            ).strip()
        return {
            "provider": self.provider_id,
            "engine": self.engine_id,
            "runtime": "server",
            "enabled": bool(enabled),
            "configured": bool(model_path),
            "model_path": str(model_path or ""),
            "model_label": self.resolved_model_label(),
            "model_id": self.resolved_model_id() if model_path else "",
            "server_url": self.server_url,
            "backend": self.backend,
            "binary_path": str(self._binary_path or (binary_candidates[0] if binary_candidates else "")),
            "generation_options": self.generation_options(),
            "requires_webgpu": False,
            "supports_local_file": False,
            "running": False,
            "warning": warning,
        }


class LocalAIService:
    def __init__(self, repository: SchoolRepository, *, base_path: Path, data_path: Path) -> None:
        self.repository = repository
        self.base_path = Path(base_path).resolve(strict=False)
        self.data_path = Path(data_path).resolve(strict=False)
        self.llama = LlamaCppService(repository, base_path=self.base_path, data_path=self.data_path)
        self.litert = LiteRTLmService(repository, base_path=self.base_path, data_path=self.data_path)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        active = self._active_service()
        try:
            return getattr(active, name)
        except AttributeError as exc:
            raise AttributeError(f"{type(self).__name__!s} object has no attribute {name!r}") from exc

    @property
    def provider_id(self) -> str:
        return self._active_service().provider_id

    @property
    def engine_id(self) -> str:
        return self._active_service().engine_id

    def _provider_preference(self) -> str:
        value = str(self.repository.get_setting("ai_provider", "auto") or "auto").strip().lower()
        aliases = {
            "auto": "auto",
            "litert": "litert-lm",
            "litert-lm": "litert-lm",
            "llama": "llama.cpp",
            "llama.cpp": "llama.cpp",
            "llamacpp": "llama.cpp",
        }
        return aliases.get(value, "auto")

    def _active_service(self) -> Any:
        preference = self._provider_preference()
        if preference == "litert-lm":
            return self.litert
        if preference == "llama.cpp":
            return self.llama
        if self.litert.resolved_model_path() is not None and any(path.exists() for path in self.litert._discover_binary_candidates()):
            return self.litert
        return self.llama

    def close(self) -> None:
        self.litert.close()
        self.llama.close()

    def complete(self, **kwargs: Any) -> tuple[str, str]:
        return self._active_service().complete(**kwargs)

    def prepare_direct_completion(self, *, prompt: str, code: str, path_hint: str) -> dict[str, str]:
        return self._active_service().prepare_direct_completion(prompt=prompt, code=code, path_hint=path_hint)

    def complete_direct_completion(self, *, prompt: str, code: str, path_hint: str) -> dict[str, Any]:
        return self._active_service().complete_direct_completion(prompt=prompt, code=code, path_hint=path_hint)

    def status(self, *, enabled: bool = True) -> dict[str, Any]:
        active = dict(self._active_service().status(enabled=enabled))
        active["provider_preference"] = self._provider_preference()
        active["available_providers"] = [
            {
                "key": "litert-lm",
                "configured": bool(self.litert.resolved_model_path()),
                "binary_path": str(self.litert._discover_binary_candidates()[0]) if self.litert._discover_binary_candidates() else "",
            },
            {
                "key": "llama.cpp",
                "configured": bool(self.llama.resolved_model_path()),
                "binary_path": str(self.llama._discover_binary_candidates()[0]) if self.llama._discover_binary_candidates() else "",
            },
        ]
        return active
