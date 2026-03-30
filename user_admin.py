from __future__ import annotations

import hashlib
import io
import json
import shutil
import time
import zipfile
from pathlib import Path
from typing import Any

from .auth import hash_password
from .config import ServerConfig
from .database import SchoolRepository
from .workspace import WorkspaceManager, slugify


VALID_USER_ROLES: tuple[str, ...] = ("student", "teacher", "admin")
VALID_USER_STATUSES: tuple[str, ...] = ("active", "inactive", "suspended")
DELETED_ACTOR_LABEL = "[deleted]"
DEFAULT_CHAT_RETENTION_DAYS = 180
DEFAULT_AUDIT_RETENTION_DAYS = 365


class UserAdministrationService:
    def __init__(
        self,
        repository: SchoolRepository,
        workspace_manager: WorkspaceManager | None = None,
        config: ServerConfig | None = None,
    ) -> None:
        self.repository = repository
        self.workspace_manager = workspace_manager
        self.config = config

    @staticmethod
    def sanitize_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
        if user is None:
            return None
        return {
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
            "permissions": dict(user.get("permissions") or {}),
            "status": user["status"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
        }

    def sanitize_users(self, users: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item for item in (self.sanitize_user(user) for user in users) if item is not None]

    def update_user(
        self,
        *,
        actor_username: str,
        username: str,
        display_name: str,
        role: str,
        status: str,
        password: str = "",
    ) -> dict[str, Any]:
        current = self.repository.get_user(username)
        if current is None:
            raise FileNotFoundError("Benutzer nicht gefunden.")

        display_name = display_name.strip()
        role = role.strip()
        status = status.strip()
        password = password.strip()

        if not display_name:
            raise ValueError("Anzeigename fehlt.")
        if role not in VALID_USER_ROLES:
            raise ValueError("Ungueltige Rolle.")
        if status not in VALID_USER_STATUSES:
            raise ValueError("Ungueltiger Status.")
        if username == actor_username and role != current["role"]:
            raise ValueError("Die eigene Rolle kann in der aktuellen Sitzung nicht geaendert werden.")
        if username == actor_username and status != "active":
            raise ValueError("Das eigene Konto kann in der aktuellen Sitzung nicht deaktiviert werden.")

        updated = self.repository.update_user_account(username, display_name, role, status)
        if updated is None:
            raise FileNotFoundError("Benutzer nicht gefunden.")

        changes: dict[str, Any] = {}
        for field in ("display_name", "role", "status"):
            if current[field] != updated[field]:
                changes[field] = {"before": current[field], "after": updated[field]}

        if password:
            salt, password_hash = hash_password(password)
            self.repository.set_user_password(username, password_hash, salt)
            updated = self.repository.get_user(username) or updated
            changes["password"] = {"reset": True}

        if changes:
            self.repository.add_audit(actor_username, "admin.user.update", "user", username, {"changes": changes})

        return {
            "user": self.sanitize_user(updated),
            "changes": changes,
        }

    def permission_audit_payload(self, before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, Any]:
        before_permissions = dict((before or {}).get("permissions") or {})
        after_permissions = dict((after or {}).get("permissions") or {})
        changed_keys = sorted(set(before_permissions) | set(after_permissions))
        changes = {
            key: {"before": before_permissions.get(key), "after": after_permissions.get(key)}
            for key in changed_keys
            if before_permissions.get(key) != after_permissions.get(key)
        }
        return {"changes": changes}

    def audit_entries(self, username: str, limit: int = 40) -> list[dict[str, Any]]:
        return self.repository.list_audit_logs(target_type="user", target_id=username, limit=limit)

    def retention_policy(self) -> dict[str, int]:
        return {
            "chat_days": self._retention_days("retention_chat_days", DEFAULT_CHAT_RETENTION_DAYS),
            "audit_days": self._retention_days("retention_audit_days", DEFAULT_AUDIT_RETENTION_DAYS),
        }

    def export_user_data(self, username: str) -> dict[str, Any]:
        user = self.repository.get_user(username)
        if user is None:
            raise FileNotFoundError("Benutzer nicht gefunden.")
        memberships = self.repository.list_user_groups(username)
        personal_projects = [project for project in self.repository.list_projects() if project["owner_type"] == "user" and project["owner_key"] == username]
        authored_chats = self._rows_to_dicts(
            """
            SELECT * FROM chat_messages
            WHERE author_username=?
              AND room_key NOT LIKE 'mentor:%'
              AND room_key NOT LIKE 'assistant:%'
            ORDER BY created_at ASC
            """,
            (username,),
        )
        assistant_messages = self._rows_to_dicts(
            """
            SELECT * FROM chat_messages
            WHERE room_key LIKE ?
            ORDER BY room_key ASC, created_at ASC
            """,
            (f"assistant:%:{username}",),
        )
        mentor_messages = self._rows_to_dicts(
            """
            SELECT * FROM chat_messages
            WHERE room_key LIKE ?
            ORDER BY room_key ASC, created_at ASC
            """,
            (f"mentor:%:{username}",),
        )
        audits = self._rows_to_dicts(
            """
            SELECT * FROM audit_logs
            WHERE actor_username=? OR (target_type='user' AND target_id=?)
            ORDER BY created_at ASC
            """,
            (username, username),
        )
        mutes = self._rows_to_dicts(
            """
            SELECT * FROM chat_mutes
            WHERE target_username=? OR created_by=?
            ORDER BY created_at ASC
            """,
            (username, username),
        )
        review_submissions = self._rows_to_dicts_optional(
            "review_submissions",
            "SELECT * FROM review_submissions WHERE submitter_username=? ORDER BY created_at ASC",
            (username,),
        )
        review_assignments = self._rows_to_dicts_optional(
            "review_assignments",
            "SELECT * FROM review_assignments WHERE reviewer_username=? ORDER BY assigned_at ASC",
            (username,),
        )
        curriculum_attempts = self._rows_to_dicts_optional(
            "curriculum_attempts",
            "SELECT * FROM curriculum_attempts WHERE username=? ORDER BY submitted_at ASC",
            (username,),
        )
        curriculum_certificates = self._rows_to_dicts_optional(
            "curriculum_certificates",
            "SELECT * FROM curriculum_certificates WHERE username=? ORDER BY issued_at ASC",
            (username,),
        )
        curriculum_releases = self._rows_to_dicts_optional(
            "curriculum_releases",
            "SELECT * FROM curriculum_releases WHERE scope_type='user' AND scope_key=? ORDER BY updated_at ASC",
            (username,),
        )
        deployment_artifacts = self._rows_to_dicts_optional(
            "deployment_artifacts",
            "SELECT * FROM deployment_artifacts WHERE owner_username=? ORDER BY created_at ASC",
            (username,),
        )
        data = {
            "schema_version": 1,
            "exported_at": time.time(),
            "retention_policy": self.retention_policy(),
            "user": self.sanitize_user(user),
            "groups": [
                {
                    "group_id": group.get("group_id"),
                    "display_name": group.get("display_name"),
                    "description": group.get("description"),
                }
                for group in memberships
            ],
            "personal_projects": [self._project_export_payload(project) for project in personal_projects],
            "chat_messages_authored": [self._chat_export_payload(item) for item in authored_chats],
            "assistant_threads": self._group_chat_threads(assistant_messages),
            "mentor_threads": self._group_mentor_threads(mentor_messages),
            "chat_mutes": [dict(item) for item in mutes],
            "audit_logs": [self._json_row(item, ("payload_json",)) for item in audits],
            "review_submissions": [self._json_row(item, ("group_scope_json", "metadata_json")) for item in review_submissions],
            "review_assignments": [self._json_row(item, ("feedback_json",)) for item in review_assignments],
            "curriculum_attempts": [self._json_row(item, ("answers_json", "feedback_json")) for item in curriculum_attempts],
            "curriculum_certificates": [self._json_row(item, ("metadata_json",)) for item in curriculum_certificates],
            "curriculum_releases": curriculum_releases,
            "deployment_artifacts": [self._json_row(item, ("metadata_json",)) for item in deployment_artifacts],
        }
        data["summary"] = {
            "group_count": len(data["groups"]),
            "personal_project_count": len(data["personal_projects"]),
            "authored_chat_count": len(data["chat_messages_authored"]),
            "assistant_message_count": sum(len(thread["messages"]) for thread in data["assistant_threads"]),
            "mentor_message_count": sum(len(thread["messages"]) for thread in data["mentor_threads"]),
            "audit_count": len(data["audit_logs"]),
            "review_submission_count": len(data["review_submissions"]),
            "review_assignment_count": len(data["review_assignments"]),
            "curriculum_attempt_count": len(data["curriculum_attempts"]),
            "artifact_count": len(data["deployment_artifacts"]),
        }
        return data

    def hard_delete_user(self, *, actor_username: str, username: str) -> dict[str, Any]:
        if username == actor_username:
            raise ValueError("Das aktuell angemeldete Konto kann nicht hart geloescht werden.")
        user = self.repository.get_user(username)
        if user is None:
            raise FileNotFoundError("Benutzer nicht gefunden.")

        personal_projects = [project for project in self.repository.list_projects() if project["owner_type"] == "user" and project["owner_key"] == username]
        personal_project_ids = [str(project["project_id"]) for project in personal_projects]
        project_paths = [self.workspace_manager.project_root(project) for project in personal_projects] if self.workspace_manager is not None else []
        mentor_room_like = f"mentor:%:{username}"
        assistant_room_like = f"assistant:%:{username}"
        review_snapshots = [
            Path(snapshot_path).resolve(strict=False)
            for item in self._rows_to_dicts_optional("review_submissions", "SELECT snapshot_path FROM review_submissions WHERE submitter_username=?", (username,))
            for snapshot_path in [str(item.get("snapshot_path") or "").strip()]
            if snapshot_path
        ]
        artifact_paths = [
            self._artifact_fs_path(item)
            for item in self._rows_to_dicts_optional("deployment_artifacts", "SELECT relative_path FROM deployment_artifacts WHERE owner_username=?", (username,))
        ]

        summary = {
            "deleted_user": username,
            "personal_projects_removed": len(personal_project_ids),
            "project_ids": personal_project_ids,
            "counts": {},
            "anonymized_reference": hashlib.sha256(username.encode("utf-8")).hexdigest()[:16],
        }

        with self.repository._lock, self.repository._conn:
            counts = summary["counts"]
            counts["review_assignments"] = self._execute_optional(
                "review_assignments",
                """
                DELETE FROM review_assignments
                WHERE reviewer_username=?
                   OR submission_id IN (SELECT submission_id FROM review_submissions WHERE submitter_username=?)
                   OR submission_id IN (
                        SELECT submission_id FROM review_submissions
                        WHERE project_id IN ({project_placeholders})
                   )
                """.format(project_placeholders=",".join("?" for _ in personal_project_ids) or "''"),
                (username, username, *personal_project_ids),
            )
            counts["review_submissions"] = self._execute_optional(
                "review_submissions",
                """
                DELETE FROM review_submissions
                WHERE submitter_username=?
                   OR project_id IN ({project_placeholders})
                """.format(project_placeholders=",".join("?" for _ in personal_project_ids) or "''"),
                (username, *personal_project_ids),
            )
            counts["deployment_artifacts"] = self._execute_optional(
                "deployment_artifacts",
                """
                DELETE FROM deployment_artifacts
                WHERE owner_username=?
                   OR project_id IN ({project_placeholders})
                """.format(project_placeholders=",".join("?" for _ in personal_project_ids) or "''"),
                (username, *personal_project_ids),
            )
            counts["curriculum_attempts"] = self._execute_optional(
                "curriculum_attempts",
                "DELETE FROM curriculum_attempts WHERE username=?",
                (username,),
            )
            counts["curriculum_certificates"] = self._execute_optional(
                "curriculum_certificates",
                "DELETE FROM curriculum_certificates WHERE username=?",
                (username,),
            )
            counts["curriculum_releases"] = self._execute_optional(
                "curriculum_releases",
                "DELETE FROM curriculum_releases WHERE scope_type='user' AND scope_key=?",
                (username,),
            )
            self._execute_optional(
                "curriculum_custom_courses",
                "UPDATE curriculum_custom_courses SET created_by=? WHERE created_by=?",
                (DELETED_ACTOR_LABEL, username),
            )
            self._execute_optional(
                "curriculum_custom_courses",
                "UPDATE curriculum_custom_courses SET updated_by=? WHERE updated_by=?",
                (DELETED_ACTOR_LABEL, username),
            )
            counts["notebook_presence"] = self._execute_optional(
                "notebook_presence",
                "DELETE FROM notebook_presence WHERE username=?",
                (username,),
            )
            counts["notebook_ops"] = self._execute_optional(
                "notebook_collab_ops",
                "DELETE FROM notebook_collab_ops WHERE author_username=?",
                (username,),
            )
            self._execute_optional(
                "notebook_collab_state",
                "UPDATE notebook_collab_state SET updated_by=? WHERE updated_by=?",
                (DELETED_ACTOR_LABEL, username),
            )
            if personal_project_ids:
                project_placeholder = ",".join("?" for _ in personal_project_ids)
                counts["project_chat_messages"] = self.repository._conn.execute(
                    f"DELETE FROM chat_messages WHERE room_key IN ({','.join('?' for _ in personal_project_ids)})",
                    tuple(f"project:{project_id}" for project_id in personal_project_ids),
                ).rowcount
                counts["project_mentor_messages"] = self.repository._conn.execute(
                    f"DELETE FROM chat_messages WHERE {' OR '.join('room_key LIKE ?' for _ in personal_project_ids)}",
                    tuple(f"mentor:{project_id}:%" for project_id in personal_project_ids),
                ).rowcount
                counts["project_audits"] = self.repository._conn.execute(
                    f"DELETE FROM audit_logs WHERE target_type='project' AND target_id IN ({project_placeholder})",
                    tuple(personal_project_ids),
                ).rowcount
                counts["notebook_collab_state"] = self._execute_optional(
                    "notebook_collab_state",
                    f"DELETE FROM notebook_collab_state WHERE project_id IN ({project_placeholder})",
                    tuple(personal_project_ids),
                )
                counts["notebook_collab_snapshots"] = self._execute_optional(
                    "notebook_collab_snapshots",
                    f"DELETE FROM notebook_collab_snapshots WHERE project_id IN ({project_placeholder})",
                    tuple(personal_project_ids),
                )
                self._execute_optional(
                    "notebook_presence",
                    f"DELETE FROM notebook_presence WHERE project_id IN ({project_placeholder})",
                    tuple(personal_project_ids),
                )
                self._execute_optional(
                    "dispatch_jobs",
                    f"DELETE FROM dispatch_jobs WHERE project_id IN ({project_placeholder})",
                    tuple(personal_project_ids),
                )
                counts["projects"] = self.repository._conn.execute(
                    f"DELETE FROM projects WHERE owner_type='user' AND owner_key=? AND project_id IN ({project_placeholder})",
                    (username, *personal_project_ids),
                ).rowcount
            else:
                counts["project_chat_messages"] = 0
                counts["project_mentor_messages"] = 0
                counts["project_audits"] = 0
                counts["notebook_collab_state"] = 0
                counts["notebook_collab_snapshots"] = 0
                counts["projects"] = 0
            counts["mentor_messages"] = self.repository._conn.execute(
                "DELETE FROM chat_messages WHERE room_key LIKE ?",
                (mentor_room_like,),
            ).rowcount
            counts["assistant_messages"] = self.repository._conn.execute(
                "DELETE FROM chat_messages WHERE room_key LIKE ?",
                (assistant_room_like,),
            ).rowcount
            counts["chat_messages"] = self.repository._conn.execute(
                """
                DELETE FROM chat_messages
                WHERE author_username=?
                  AND room_key NOT LIKE 'mentor:%'
                  AND room_key NOT LIKE 'assistant:%'
                """,
                (username,),
            ).rowcount
            counts["chat_mutes"] = self.repository._conn.execute(
                "DELETE FROM chat_mutes WHERE target_username=? OR created_by=?",
                (username, username),
            ).rowcount
            counts["audit_logs"] = self.repository._conn.execute(
                "DELETE FROM audit_logs WHERE actor_username=? OR (target_type='user' AND target_id=?)",
                (username, username),
            ).rowcount
            self._execute_optional(
                "dispatch_jobs",
                "UPDATE dispatch_jobs SET created_by=? WHERE created_by=?",
                (DELETED_ACTOR_LABEL, username),
            )
            counts["memberships"] = self.repository._conn.execute(
                "DELETE FROM memberships WHERE username=?",
                (username,),
            ).rowcount
            counts["users"] = self.repository._conn.execute(
                "DELETE FROM users WHERE username=?",
                (username,),
            ).rowcount

        for path in project_paths:
            self._remove_path(path)
        for path in artifact_paths:
            self._remove_path(path)
        for path in review_snapshots:
            self._remove_path(path)

        self.repository.add_audit(
            actor_username,
            "admin.user.hard_delete",
            "user",
            f"deleted:{summary['anonymized_reference']}",
            {
                "counts": dict(summary["counts"]),
                "project_ids": personal_project_ids,
                "deleted_user_label": DELETED_ACTOR_LABEL,
            },
        )
        return summary

    def export_project_archive(self, *, actor_username: str, project: dict[str, Any]) -> dict[str, Any]:
        bundle = self._build_project_archive_bundle(project, archive_kind="export", actor_username=actor_username)
        self.repository.add_audit(
            actor_username,
            "project.export",
            "project",
            str(project["project_id"]),
            {
                "filename": bundle["filename"],
                "size_bytes": bundle["size_bytes"],
                "file_count": bundle["file_count"],
            },
        )
        return bundle

    def archive_project(self, *, actor_username: str, project: dict[str, Any]) -> dict[str, Any]:
        if self.config is None:
            raise RuntimeError("Archivierung ist ohne Server-Konfiguration nicht verfuegbar.")
        bundle = self._build_project_archive_bundle(project, archive_kind="archive", actor_username=actor_username)
        archive_root = self.config.data_path / "project_archives" / slugify(str(project["owner_type"])) / slugify(str(project["owner_key"]))
        archive_root.mkdir(parents=True, exist_ok=True)
        archive_path = archive_root / bundle["filename"]
        archive_path.write_bytes(bundle["content"])
        payload = {
            "project_id": str(project["project_id"]),
            "archive_name": bundle["filename"],
            "archive_path": str(archive_path),
            "size_bytes": bundle["size_bytes"],
            "file_count": bundle["file_count"],
            "stored_at": time.time(),
        }
        self.repository.add_audit(actor_username, "project.archive", "project", str(project["project_id"]), payload)
        return payload

    def hard_delete_project(self, *, actor_username: str, project: dict[str, Any]) -> dict[str, Any]:
        project_id = str(project["project_id"])
        project_root = self.workspace_manager.project_root(project) if self.workspace_manager is not None else None
        review_snapshots = [
            Path(snapshot_path).resolve(strict=False)
            for item in self._rows_to_dicts_optional("review_submissions", "SELECT snapshot_path FROM review_submissions WHERE project_id=?", (project_id,))
            for snapshot_path in [str(item.get("snapshot_path") or "").strip()]
            if snapshot_path
        ]
        artifact_paths = [
            self._artifact_fs_path(item)
            for item in self._rows_to_dicts_optional("deployment_artifacts", "SELECT relative_path FROM deployment_artifacts WHERE project_id=?", (project_id,))
        ]
        summary = {
            "deleted_project": project_id,
            "project_name": str(project.get("name") or ""),
            "counts": {},
        }
        with self.repository._lock, self.repository._conn:
            counts = summary["counts"]
            counts["review_assignments"] = self._execute_optional(
                "review_assignments",
                "DELETE FROM review_assignments WHERE submission_id IN (SELECT submission_id FROM review_submissions WHERE project_id=?)",
                (project_id,),
            )
            counts["review_submissions"] = self._execute_optional(
                "review_submissions",
                "DELETE FROM review_submissions WHERE project_id=?",
                (project_id,),
            )
            counts["deployment_artifacts"] = self._execute_optional(
                "deployment_artifacts",
                "DELETE FROM deployment_artifacts WHERE project_id=?",
                (project_id,),
            )
            counts["virtual_lecturer_sessions"] = self._execute_optional(
                "virtual_lecturer_sessions",
                "DELETE FROM virtual_lecturer_sessions WHERE project_id=?",
                (project_id,),
            )
            counts["project_chat_messages"] = self.repository._conn.execute(
                "DELETE FROM chat_messages WHERE room_key=?",
                (f"project:{project_id}",),
            ).rowcount
            counts["project_mentor_messages"] = self.repository._conn.execute(
                "DELETE FROM chat_messages WHERE room_key LIKE ?",
                (f"mentor:{project_id}:%",),
            ).rowcount
            counts["project_assistant_messages"] = self.repository._conn.execute(
                "DELETE FROM chat_messages WHERE room_key LIKE ?",
                (f"assistant:{project_id}:%",),
            ).rowcount
            counts["project_lecturer_messages"] = self.repository._conn.execute(
                "DELETE FROM chat_messages WHERE room_key LIKE ?",
                (f"lecturer:{project_id}:%",),
            ).rowcount
            counts["project_audits"] = self.repository._conn.execute(
                "DELETE FROM audit_logs WHERE target_type='project' AND target_id=?",
                (project_id,),
            ).rowcount
            counts["notebook_collab_ops"] = self._execute_optional(
                "notebook_collab_ops",
                "DELETE FROM notebook_collab_ops WHERE project_id=?",
                (project_id,),
            )
            counts["notebook_collab_state"] = self._execute_optional(
                "notebook_collab_state",
                "DELETE FROM notebook_collab_state WHERE project_id=?",
                (project_id,),
            )
            counts["notebook_collab_snapshots"] = self._execute_optional(
                "notebook_collab_snapshots",
                "DELETE FROM notebook_collab_snapshots WHERE project_id=?",
                (project_id,),
            )
            counts["notebook_presence"] = self._execute_optional(
                "notebook_presence",
                "DELETE FROM notebook_presence WHERE project_id=?",
                (project_id,),
            )
            counts["dispatch_jobs"] = self._execute_optional(
                "dispatch_jobs",
                "DELETE FROM dispatch_jobs WHERE project_id=?",
                (project_id,),
            )
            counts["projects"] = self.repository._conn.execute(
                "DELETE FROM projects WHERE project_id=?",
                (project_id,),
            ).rowcount

        self._remove_path(project_root.resolve(strict=False) if project_root is not None else None)
        for path in artifact_paths:
            self._remove_path(path)
        for path in review_snapshots:
            self._remove_path(path)

        self.repository.add_audit(
            actor_username,
            "project.hard_delete",
            "project",
            project_id,
            {
                "project_name": summary["project_name"],
                "counts": dict(summary["counts"]),
            },
        )
        return summary

    def apply_retention(self, *, actor_username: str = "system-retention") -> dict[str, Any]:
        policy = self.retention_policy()
        now = time.time()
        summary = {
            "policy": policy,
            "deleted": {
                "chat_messages": 0,
                "audit_logs": 0,
                "expired_mutes": 0,
            },
            "executed_at": now,
        }
        with self.repository._lock, self.repository._conn:
            if policy["chat_days"] > 0:
                chat_threshold = now - (policy["chat_days"] * 86400)
                summary["deleted"]["chat_messages"] = self.repository._conn.execute(
                    "DELETE FROM chat_messages WHERE created_at<?",
                    (chat_threshold,),
                ).rowcount
                summary["deleted"]["expired_mutes"] = self.repository._conn.execute(
                    "DELETE FROM chat_mutes WHERE muted_until<?",
                    (chat_threshold,),
                ).rowcount
            if policy["audit_days"] > 0:
                audit_threshold = now - (policy["audit_days"] * 86400)
                summary["deleted"]["audit_logs"] = self.repository._conn.execute(
                    "DELETE FROM audit_logs WHERE created_at<?",
                    (audit_threshold,),
                ).rowcount
        if any(summary["deleted"].values()):
            self.repository.add_audit(
                actor_username,
                "admin.retention.run",
                "retention",
                "policy",
                summary,
            )
        return summary

    def _retention_days(self, key: str, default: int) -> int:
        try:
            value = int(self.repository.get_setting(key, default))
        except Exception:
            value = default
        return max(0, value)

    def _artifact_fs_path(self, row: dict[str, Any]) -> Path | None:
        if self.config is None:
            return None
        relative_path = str(row.get("relative_path") or "").strip()
        if not relative_path:
            return None
        return self.config.data_path / relative_path

    def _remove_path(self, path: Path | None) -> None:
        if path is None:
            return
        path = path.resolve(strict=False)
        if not path.is_absolute() or str(path) in {str(path.anchor), str(Path(".").resolve(strict=False))}:
            return
        allowed_roots = [
            self.config.data_path.resolve(strict=False),
            self.config.users_workspace_path.resolve(strict=False),
            self.config.groups_workspace_path.resolve(strict=False),
        ] if self.config is not None else []
        if allowed_roots and not any(path.is_relative_to(root) for root in allowed_roots):
            return
        if not path.exists():
            return
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        except Exception:
            pass

    def _rows_to_dicts(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.repository._lock:
            rows = self.repository._conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def _rows_to_dicts_optional(self, table_name: str, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        if not self._table_exists(table_name):
            return []
        return self._rows_to_dicts(query, params)

    def _execute_optional(self, table_name: str, query: str, params: tuple[Any, ...] = ()) -> int:
        if not self._table_exists(table_name):
            return 0
        return int(self.repository._conn.execute(query, params).rowcount)

    def _table_exists(self, table_name: str) -> bool:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            ).fetchone()
        return row is not None

    @staticmethod
    def _json_row(row: dict[str, Any], json_fields: tuple[str, ...]) -> dict[str, Any]:
        payload = dict(row)
        for field in json_fields:
            raw = payload.pop(field, None)
            target_key = field.removesuffix("_json")
            try:
                payload[target_key] = json.loads(raw) if raw else {}
            except Exception:
                payload[target_key] = {}
        return payload

    @staticmethod
    def _chat_export_payload(row: dict[str, Any]) -> dict[str, Any]:
        payload = UserAdministrationService._json_row(row, ("metadata_json",))
        payload["metadata"] = payload.pop("metadata", {})
        return payload

    @staticmethod
    def _project_export_payload(project: dict[str, Any]) -> dict[str, Any]:
        return {
            "project_id": project["project_id"],
            "owner_type": project["owner_type"],
            "owner_key": project["owner_key"],
            "name": project["name"],
            "slug": project["slug"],
            "template": project["template"],
            "runtime": project["runtime"],
            "main_file": project["main_file"],
            "description": project["description"],
            "created_by": project["created_by"],
            "created_at": project["created_at"],
            "updated_at": project["updated_at"],
        }

    def _group_chat_threads(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            payload = self._chat_export_payload(row)
            grouped.setdefault(str(payload.get("room_key") or ""), []).append(payload)
        return [
            {"room_key": room_key, "messages": messages}
            for room_key, messages in sorted(grouped.items())
        ]

    def _group_mentor_threads(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._group_chat_threads(rows)

    def _build_project_archive_bundle(self, project: dict[str, Any], *, archive_kind: str, actor_username: str) -> dict[str, Any]:
        if self.workspace_manager is None:
            raise RuntimeError("Projektarchivierung ist ohne Workspace-Manager nicht verfuegbar.")
        project_root = self.workspace_manager.project_root(project)
        if not project_root.exists():
            raise FileNotFoundError("Projektordner nicht gefunden.")

        timestamp_label = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        archive_prefix = "nova-project-archive" if archive_kind == "archive" else "nova-project-export"
        filename = f"{archive_prefix}-{slugify(str(project.get('name') or project.get('slug') or project['project_id']))}-{timestamp_label}.zip"
        manifest = {
            "schema_version": 1,
            "archive_kind": archive_kind,
            "generated_at": time.time(),
            "generated_by": actor_username,
            "project": self._project_export_payload(project),
            "workspace_root": str(project_root),
            "files": [],
        }
        readme_name = "README_ARCHIVE.txt" if archive_kind == "archive" else "README_EXPORT.txt"
        readme_text = (
            "Nova School Server Projektarchiv\n\n"
            "Dieses Archiv enthaelt den Projektstand samt Dateien und Metadaten zum angegebenen Zeitpunkt.\n"
            "manifest.json beschreibt Projekt und Dateiliste.\n"
        )
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(readme_name, readme_text)
            for path in sorted(project_root.rglob("*"), key=lambda item: item.as_posix().lower()):
                if not path.is_file():
                    continue
                relative_path = path.relative_to(project_root).as_posix()
                archive.write(path, f"project/{relative_path}")
                manifest["files"].append(relative_path)
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        content = buffer.getvalue()
        return {
            "filename": filename,
            "content": content,
            "size_bytes": len(content),
            "file_count": len(manifest["files"]),
            "manifest": manifest,
        }
