from __future__ import annotations

import json
import secrets
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    return value


@dataclass(slots=True)
class EmbeddedPrincipal:
    tenant_id: str
    token_id: str
    subject: str
    roles: list[str]
    metadata: dict[str, Any]
    expires_at: float


class EmbeddedSecurityPlane:
    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path).resolve(strict=False)
        self.state_path = self.base_path / "data" / "embedded_security_plane.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._state = self._load_state()

    def register_tenant(self, tenant_id: str, *, display_name: str = "") -> dict[str, Any]:
        with self._lock:
            tenant = self._state["tenants"].get(tenant_id) or {"tenant_id": tenant_id, "quotas": {}}
            if display_name:
                tenant["display_name"] = display_name
            self._state["tenants"][tenant_id] = tenant
            self._save_state()
            return dict(tenant)

    def get_tenant(self, tenant_id: str) -> dict[str, Any] | None:
        with self._lock:
            tenant = self._state["tenants"].get(tenant_id)
            return dict(tenant) if tenant is not None else None

    def issue_token(
        self,
        tenant_id: str,
        subject: str,
        *,
        roles: set[str] | list[str] | tuple[str, ...] | None = None,
        ttl_seconds: int = 43_200,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.register_tenant(tenant_id)
            token = secrets.token_urlsafe(32)
            token_id = uuid.uuid4().hex
            record = {
                "tenant_id": tenant_id,
                "token_id": token_id,
                "subject": str(subject),
                "roles": sorted({str(item) for item in (roles or [])}),
                "metadata": _json_safe(metadata or {}),
                "issued_at": time.time(),
                "expires_at": time.time() + max(60, int(ttl_seconds)),
                "revoked": False,
            }
            self._state["tokens"][token] = record
            self._save_state()
            return {"token": token, "token_id": token_id, "expires_at": record["expires_at"]}

    def authenticate(self, token: str) -> EmbeddedPrincipal | None:
        with self._lock:
            record = self._state["tokens"].get(str(token) or "")
            if record is None:
                return None
            if bool(record.get("revoked")):
                return None
            if float(record.get("expires_at") or 0.0) <= time.time():
                return None
            return EmbeddedPrincipal(
                tenant_id=str(record.get("tenant_id") or ""),
                token_id=str(record.get("token_id") or ""),
                subject=str(record.get("subject") or ""),
                roles=list(record.get("roles") or []),
                metadata=dict(record.get("metadata") or {}),
                expires_at=float(record.get("expires_at") or 0.0),
            )

    def revoke_token(self, token_id: str) -> dict[str, Any]:
        with self._lock:
            for record in self._state["tokens"].values():
                if str(record.get("token_id") or "") == str(token_id):
                    record["revoked"] = True
                    self._save_state()
                    return {"token_id": token_id, "revoked": True}
            return {"token_id": token_id, "revoked": False}

    def store_secret(self, tenant_id: str, name: str, secret_value: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            payload = {
                "tenant_id": tenant_id,
                "name": name,
                "secret_value": str(secret_value),
                "metadata": _json_safe(metadata or {}),
            }
            self._state["secrets"][self._secret_key(tenant_id, name)] = payload
            self._save_state()
            return dict(payload)

    def resolve_secret(self, tenant_id: str, name: str) -> dict[str, Any] | None:
        with self._lock:
            payload = self._state["secrets"].get(self._secret_key(tenant_id, name))
            return dict(payload) if payload is not None else None

    def create_certificate_authority(self, name: str, *, common_name: str) -> dict[str, Any]:
        with self._lock:
            payload = {"name": name, "common_name": common_name, "created_at": time.time()}
            self._state["certificate_authorities"][name] = payload
            self._save_state()
            return dict(payload)

    def get_certificate_authority(self, name: str) -> dict[str, Any] | None:
        with self._lock:
            payload = self._state["certificate_authorities"].get(name)
            return dict(payload) if payload is not None else None

    def set_trust_policy(self, name: str, **payload: Any) -> dict[str, Any]:
        with self._lock:
            policy = {"name": name, **_json_safe(payload)}
            self._state["trust_policies"][name] = policy
            self._save_state()
            return dict(policy)

    def get_trust_policy(self, name: str) -> dict[str, Any] | None:
        with self._lock:
            policy = self._state["trust_policies"].get(name)
            return dict(policy) if policy is not None else None

    def onboard_worker(self, worker_id: str, tenant_id: str, **payload: Any) -> dict[str, Any]:
        with self._lock:
            worker = {"worker_id": worker_id, "tenant_id": tenant_id, **_json_safe(payload)}
            self._state["worker_enrollments"][worker_id] = worker
            self._save_state()
            return dict(worker)

    def list_worker_enrollments(self, tenant_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [
                dict(worker)
                for worker in self._state["worker_enrollments"].values()
                if str(worker.get("tenant_id") or "") == str(tenant_id)
            ]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            active_tokens = sum(
                1
                for record in self._state["tokens"].values()
                if not bool(record.get("revoked")) and float(record.get("expires_at") or 0.0) > time.time()
            )
            return {
                "backend": "embedded",
                "tenant_count": len(self._state["tenants"]),
                "active_token_count": active_tokens,
                "secret_count": len(self._state["secrets"]),
                "worker_enrollment_count": len(self._state["worker_enrollments"]),
            }

    def close(self) -> None:
        with self._lock:
            self._save_state()

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._empty_state()
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return self._empty_state()
        state = self._empty_state()
        if isinstance(payload, dict):
            for key in state:
                raw = payload.get(key)
                if isinstance(raw, dict):
                    state[key] = raw
        return state

    def _save_state(self) -> None:
        temp_path = self.state_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.state_path)

    @staticmethod
    def _empty_state() -> dict[str, dict[str, Any]]:
        return {
            "tenants": {},
            "tokens": {},
            "secrets": {},
            "certificate_authorities": {},
            "trust_policies": {},
            "worker_enrollments": {},
        }

    @staticmethod
    def _secret_key(tenant_id: str, name: str) -> str:
        return f"{tenant_id}::{name}"


class EmbeddedToolSandbox:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._recent: list[dict[str, Any]] = []

    def authorize(
        self,
        principal: str,
        *,
        allowed_tools: set[str] | list[str] | tuple[str, ...] | None = None,
        requested_tools: set[str] | list[str] | tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "authorized": True,
            "principal": str(principal),
            "allowed_tools": sorted({str(item) for item in (allowed_tools or [])}),
            "requested_tools": sorted({str(item) for item in (requested_tools or [])}),
            "metadata": _json_safe(metadata or {}),
        }
        with self._lock:
            self._recent.append(payload)
            if len(self._recent) > 50:
                self._recent = self._recent[-50:]
        return payload

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "backend": "embedded",
                "recent_authorizations": len(self._recent),
            }


@dataclass(slots=True)
class EmbeddedNovaAIProviderRuntime:
    provider_id: str = "embedded"

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)
