from __future__ import annotations

import copy
import hashlib
import html
import hmac
import io
import json
import re
import time
import uuid
import zipfile
from typing import Any

from .curriculum_catalog import get_course, list_courses
from .curriculum_certificate_pdf import build_curriculum_certificate_pdf


FINAL_MODULE_ID = "__final__"
CURRICULUM_BUNDLE_SCHEMA_VERSION = 1
CURRICULUM_ACTIVE_BUNDLE_SETTING = "curriculum_active_bundle_id"
CURRICULUM_BUNDLE_SECRET_SETTING = "curriculum_bundle_secret"
CURRICULUM_BUNDLE_ALLOWED_TOP_LEVEL = frozenset({"manifest.json", "signature.json"})


class CurriculumService:
    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self._ensure_schema()

    def _catalog_courses(self) -> list[dict[str, Any]]:
        courses_by_id = {
            str(course.get("course_id") or ""): copy.deepcopy(course)
            for course in list_courses()
            if str(course.get("course_id") or "").strip()
        }
        for course in self._active_bundle_courses():
            courses_by_id[str(course["course_id"])] = course
        courses = list(courses_by_id.values())
        courses.extend(self._custom_courses())
        return sorted(
            courses,
            key=lambda course: (
                0 if not course.get("is_custom") else 1,
                str(course.get("title") or "").lower(),
            ),
        )

    def _catalog_course(self, course_id: str) -> dict[str, Any] | None:
        custom = self._custom_course(course_id)
        if custom is not None:
            return custom
        bundle_course = self._active_bundle_course(course_id)
        if bundle_course is not None:
            return bundle_course
        course = get_course(course_id)
        return copy.deepcopy(course) if course else None

    def active_bundle_id(self) -> str:
        return str(self.repository.get_setting(CURRICULUM_ACTIVE_BUNDLE_SETTING, "") or "").strip()

    def _active_bundle_row(self) -> dict[str, Any] | None:
        bundle_id = self.active_bundle_id()
        if not bundle_id:
            return None
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT * FROM curriculum_update_bundles WHERE bundle_id=?",
                (bundle_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def active_bundle(self) -> dict[str, Any] | None:
        row = self._active_bundle_row()
        if row is None:
            return None
        return self._bundle_row_payload(row)

    def _active_bundle_courses(self) -> list[dict[str, Any]]:
        bundle_id = self.active_bundle_id()
        if not bundle_id:
            return []
        with self.repository._lock:
            rows = self.repository._conn.execute(
                """
                SELECT course_id, payload_json
                FROM curriculum_bundle_courses
                WHERE bundle_id=?
                ORDER BY course_id ASC
                """,
                (bundle_id,),
            ).fetchall()
        courses: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(row["payload_json"] or "{}")
            payload["is_bundle"] = True
            payload["bundle_id"] = bundle_id
            courses.append(payload)
        return courses

    def _active_bundle_course(self, course_id: str) -> dict[str, Any] | None:
        bundle_id = self.active_bundle_id()
        if not bundle_id:
            return None
        with self.repository._lock:
            row = self.repository._conn.execute(
                """
                SELECT payload_json
                FROM curriculum_bundle_courses
                WHERE bundle_id=? AND course_id=?
                """,
                (bundle_id, course_id),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload_json"] or "{}")
        payload["is_bundle"] = True
        payload["bundle_id"] = bundle_id
        return payload

    def _active_bundle_material_presets(self) -> list[dict[str, Any]]:
        bundle_id = self.active_bundle_id()
        if not bundle_id:
            return []
        with self.repository._lock:
            rows = self.repository._conn.execute(
                """
                SELECT payload_json
                FROM curriculum_bundle_material_presets
                WHERE bundle_id=?
                ORDER BY language ASC, profile_key ASC, preset_key ASC
                """,
                (bundle_id,),
            ).fetchall()
        return [json.loads(row["payload_json"] or "{}") for row in rows]

    def _active_bundle_mentor_rules(self) -> list[dict[str, Any]]:
        bundle_id = self.active_bundle_id()
        if not bundle_id:
            return []
        with self.repository._lock:
            rows = self.repository._conn.execute(
                """
                SELECT payload_json
                FROM curriculum_bundle_mentor_rules
                WHERE bundle_id=?
                ORDER BY course_id ASC, module_id ASC, rule_key ASC
                """,
                (bundle_id,),
            ).fetchall()
        return [json.loads(row["payload_json"] or "{}") for row in rows]

    def _resolve_mentor_rule(self, course_id: str, module_id: str) -> dict[str, Any] | None:
        best_rule: dict[str, Any] | None = None
        best_score = -1
        for item in self._active_bundle_mentor_rules():
            if str(item.get("course_id") or "").strip() != str(course_id or "").strip():
                continue
            item_module_id = str(item.get("module_id") or "").strip()
            score = 1
            if item_module_id:
                if item_module_id != str(module_id or "").strip():
                    continue
                score = 2
            if score > best_score:
                best_rule = dict(item)
                best_score = score
        return best_rule

    def _custom_courses(self) -> list[dict[str, Any]]:
        with self.repository._lock:
            rows = self.repository._conn.execute(
                "SELECT payload_json, created_by, updated_by, created_at, updated_at FROM curriculum_custom_courses ORDER BY updated_at DESC, title ASC"
            ).fetchall()
        courses: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(row["payload_json"] or "{}")
            payload["is_custom"] = True
            payload["created_by"] = row["created_by"]
            payload["updated_by"] = row["updated_by"]
            payload["created_at"] = row["created_at"]
            payload["updated_at"] = row["updated_at"]
            courses.append(payload)
        return courses

    def _custom_course(self, course_id: str) -> dict[str, Any] | None:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT payload_json, created_by, updated_by, created_at, updated_at FROM curriculum_custom_courses WHERE course_id=?",
                (course_id,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload_json"] or "{}")
        payload["is_custom"] = True
        payload["created_by"] = row["created_by"]
        payload["updated_by"] = row["updated_by"]
        payload["created_at"] = row["created_at"]
        payload["updated_at"] = row["updated_at"]
        return payload

    @staticmethod
    def _slug(value: str) -> str:
        text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
        return text.strip("-")

    @staticmethod
    def _listify(value: Any, *, separator: str = "\n") -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            if separator == ",":
                items = value.split(",")
            else:
                items = value.splitlines()
            return [item.strip() for item in items if item.strip()]
        return []

    def _normalize_question(self, raw: dict[str, Any], *, fallback_id: str) -> dict[str, Any]:
        question_id = self._slug(str(raw.get("id") or fallback_id)) or fallback_id
        question_type = str(raw.get("type") or "single").strip().lower()
        if question_type not in {"single", "multi", "text"}:
            raise ValueError("Fragentyp muss single, multi oder text sein.")
        prompt = str(raw.get("prompt") or "").strip()
        if not prompt:
            raise ValueError("Jede Frage braucht einen Prompt.")
        explanation = str(raw.get("explanation") or "").strip()
        points = max(1.0, float(raw.get("points") or 1))
        payload: dict[str, Any] = {
            "id": question_id,
            "type": question_type,
            "prompt": prompt,
            "points": points,
            "explanation": explanation,
        }
        if question_type in {"single", "multi"}:
            raw_options = raw.get("options") or []
            options: list[dict[str, str]] = []
            for index, option in enumerate(list(raw_options), start=1):
                option_id = self._slug(str((option or {}).get("id") or f"option-{index}")) or f"option-{index}"
                label = str((option or {}).get("label") or "").strip()
                if label:
                    options.append({"id": option_id, "label": label})
            if len(options) < 2:
                raise ValueError("Single- und Multi-Fragen brauchen mindestens zwei Optionen.")
            payload["options"] = options
            raw_correct = self._listify(raw.get("correct"), separator=",")
            correct = [item for item in raw_correct if item in {option["id"] for option in options}]
            if question_type == "single":
                if len(correct) != 1:
                    raise ValueError("Single-Choice-Fragen brauchen genau eine korrekte Option.")
                payload["correct"] = [correct[0]]
            else:
                if not correct:
                    raise ValueError("Multi-Choice-Fragen brauchen mindestens eine korrekte Option.")
                payload["correct"] = correct
        else:
            accepted = self._listify(raw.get("accepted"))
            if not accepted:
                raise ValueError("Textfragen brauchen mindestens eine akzeptierte Antwort.")
            payload["accepted"] = accepted
            payload["placeholder"] = str(raw.get("placeholder") or "").strip()
        return payload

    def _normalize_course_definition(
        self,
        payload: dict[str, Any],
        *,
        editor_username: str,
        allow_standard_override: bool = False,
        is_custom: bool = True,
    ) -> dict[str, Any]:
        requested_course_id = str(payload.get("course_id") or "").strip()
        course_id = self._slug(requested_course_id)
        if not course_id:
            raise ValueError("Kurs-ID fehlt.")
        if not allow_standard_override and self._catalog_course(course_id) is not None and self._custom_course(course_id) is None:
            raise ValueError("Vordefinierte Standardkurse koennen nicht direkt ueberschrieben werden.")
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("Kurstitel fehlt.")
        modules_raw = list(payload.get("modules") or [])
        if not modules_raw:
            raise ValueError("Ein Kurs braucht mindestens ein Mini-Modul.")
        modules: list[dict[str, Any]] = []
        seen_module_ids: set[str] = set()
        for index, raw_module in enumerate(modules_raw, start=1):
            base_title = str((raw_module or {}).get("title") or f"Mini-Modul {index}").strip()
            module_id = self._slug(str((raw_module or {}).get("module_id") or f"m{index:02d}_{base_title}")) or f"m{index:02d}"
            if module_id in seen_module_ids:
                raise ValueError("Mini-Modul-IDs muessen eindeutig sein.")
            seen_module_ids.add(module_id)
            questions = [
                self._normalize_question(dict(question or {}), fallback_id=f"{module_id}_q{question_index}")
                for question_index, question in enumerate(list((raw_module or {}).get("questions") or []), start=1)
            ]
            if not questions:
                raise ValueError("Jedes Mini-Modul braucht mindestens eine Frage.")
            modules.append(
                {
                    "module_id": module_id,
                    "title": base_title,
                    "estimated_minutes": max(10, int((raw_module or {}).get("estimated_minutes") or 30)),
                    "objectives": self._listify((raw_module or {}).get("objectives")),
                    "lesson_markdown": str((raw_module or {}).get("lesson_markdown") or "").strip(),
                    "quiz_pass_ratio": min(1.0, max(0.1, float((raw_module or {}).get("quiz_pass_ratio") or payload.get("pass_ratio") or 0.7))),
                    "questions": questions,
                }
            )
        final_raw = dict(payload.get("final_assessment") or {})
        final_questions = [
            self._normalize_question(dict(question or {}), fallback_id=f"{course_id}_final_q{index}")
            for index, question in enumerate(list(final_raw.get("questions") or []), start=1)
        ]
        if not final_questions:
            raise ValueError("Die Abschlusspruefung braucht mindestens eine Frage.")
        theme = dict(payload.get("certificate_theme") or {})
        normalized = {
            "course_id": course_id,
            "title": title,
            "subtitle": str(payload.get("subtitle") or "").strip(),
            "subject_area": str(payload.get("subject_area") or "").strip(),
            "summary": str(payload.get("summary") or "").strip(),
            "audience": str(payload.get("audience") or "").strip(),
            "estimated_hours": max(1, int(payload.get("estimated_hours") or 1)),
            "certificate_title": str(payload.get("certificate_title") or f"Nova School Zertifikat {title}").strip(),
            "pass_ratio": min(1.0, max(0.1, float(payload.get("pass_ratio") or 0.7))),
            "final_pass_ratio": min(1.0, max(0.1, float(payload.get("final_pass_ratio") or 0.75))),
            "certificate_theme": {
                "label": str(theme.get("label") or payload.get("subject_area") or title).strip(),
                "accent": str(theme.get("accent") or "").strip(),
                "accent_dark": str(theme.get("accent_dark") or "").strip(),
                "warm": str(theme.get("warm") or "").strip(),
                "paper": str(theme.get("paper") or "").strip(),
            },
            "modules": modules,
            "final_assessment": {
                "assessment_id": str(final_raw.get("assessment_id") or f"{course_id}-abschluss").strip(),
                "title": str(final_raw.get("title") or f"Abschlusspruefung {title}").strip(),
                "instructions": str(final_raw.get("instructions") or "").strip(),
                "questions": final_questions,
            },
            "is_custom": bool(is_custom),
            "updated_by": editor_username,
        }
        return normalized

    def save_custom_course(self, session: Any, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_course_definition(dict(payload or {}), editor_username=session.username)
        current = self._custom_course(normalized["course_id"])
        now = time.time()
        created_by = str(current.get("created_by") if current else session.username)
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                """
                INSERT INTO curriculum_custom_courses(course_id, title, payload_json, created_by, updated_by, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(course_id) DO UPDATE SET
                    title=excluded.title,
                    payload_json=excluded.payload_json,
                    updated_by=excluded.updated_by,
                    updated_at=excluded.updated_at
                """,
                (
                    normalized["course_id"],
                    normalized["title"],
                    json.dumps(normalized, ensure_ascii=False),
                    created_by,
                    session.username,
                    float(current.get("created_at") if current else now),
                    now,
                ),
            )
        return self._custom_course(normalized["course_id"]) or normalized

    def validate_bundle_archive(self, archive_bytes: bytes, *, signature_secret: str = "") -> dict[str, Any]:
        bundle = self._parse_bundle_archive(archive_bytes, signature_secret=signature_secret)
        return self._bundle_preview_payload(bundle)

    def import_bundle_archive(
        self,
        session: Any,
        *,
        archive_bytes: bytes,
        source_name: str = "",
        signature_secret: str = "",
    ) -> dict[str, Any]:
        bundle = self._parse_bundle_archive(archive_bytes, signature_secret=signature_secret)
        preview = self._bundle_preview_payload(bundle)
        now = time.time()
        source_label = str(source_name or bundle["manifest"].get("title") or bundle["bundle_id"]).strip()
        manifest = dict(bundle["manifest"])
        signature = dict(bundle["signature"])
        with self.repository._lock, self.repository._conn:
            existing = self.repository._conn.execute(
                "SELECT bundle_id FROM curriculum_update_bundles WHERE bundle_id=?",
                (bundle["bundle_id"],),
            ).fetchone()
            if existing is not None:
                raise ValueError("Dieses Curriculum-Bundle wurde bereits importiert.")
            self.repository._conn.execute(
                """
                INSERT INTO curriculum_update_bundles(
                    bundle_id, title, version, status, source_name, archive_sha256,
                    manifest_json, signature_json, imported_by, imported_at, activated_by, activated_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bundle["bundle_id"],
                    str(manifest.get("title") or bundle["bundle_id"]),
                    str(manifest.get("version") or ""),
                    "imported",
                    source_label,
                    bundle["archive_sha256"],
                    json.dumps(manifest, ensure_ascii=False),
                    json.dumps(signature, ensure_ascii=False),
                    session.username,
                    now,
                    "",
                    0.0,
                ),
            )
            for course in bundle["courses"]:
                self.repository._conn.execute(
                    """
                    INSERT INTO curriculum_bundle_courses(bundle_id, course_id, title, payload_json)
                    VALUES(?, ?, ?, ?)
                    """,
                    (
                        bundle["bundle_id"],
                        course["course_id"],
                        str(course.get("title") or course["course_id"]),
                        json.dumps(course, ensure_ascii=False),
                    ),
                )
            for preset in bundle["material_presets"]:
                self.repository._conn.execute(
                    """
                    INSERT INTO curriculum_bundle_material_presets(bundle_id, preset_key, profile_key, language, payload_json)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        bundle["bundle_id"],
                        str(preset["key"]),
                        str(preset["profile"]),
                        str(preset["language"]),
                        json.dumps(preset, ensure_ascii=False),
                    ),
                )
            for rule in bundle["mentor_rules"]:
                self.repository._conn.execute(
                    """
                    INSERT INTO curriculum_bundle_mentor_rules(bundle_id, rule_key, course_id, module_id, payload_json)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        bundle["bundle_id"],
                        str(rule["key"]),
                        str(rule.get("course_id") or ""),
                        str(rule.get("module_id") or ""),
                        json.dumps(rule, ensure_ascii=False),
                    ),
                )
        imported = self._bundle_payload(bundle["bundle_id"])
        if imported is None:
            raise RuntimeError("Curriculum-Bundle konnte nach dem Import nicht gelesen werden.")
        return {"bundle": imported, "preview": preview}

    def activate_bundle(self, session: Any, bundle_id: str) -> dict[str, Any]:
        target_id = str(bundle_id or "").strip()
        if not target_id:
            raise ValueError("bundle_id fehlt.")
        target = self._bundle_payload(target_id)
        if target is None:
            raise FileNotFoundError("Curriculum-Bundle nicht gefunden.")
        now = time.time()
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                "UPDATE curriculum_update_bundles SET status='imported' WHERE status='active' AND bundle_id<>?",
                (target_id,),
            )
            self.repository._conn.execute(
                """
                UPDATE curriculum_update_bundles
                SET status='active', activated_by=?, activated_at=?
                WHERE bundle_id=?
                """,
                (session.username, now, target_id),
            )
            self.repository._conn.execute(
                """
                INSERT INTO settings(key, value_json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json=excluded.value_json,
                    updated_at=excluded.updated_at
                """,
                (
                    CURRICULUM_ACTIVE_BUNDLE_SETTING,
                    json.dumps(target_id, ensure_ascii=False),
                    now,
                ),
            )
        return self._bundle_payload(target_id) or target

    def rollback_bundle(self, session: Any, *, bundle_id: str = "") -> dict[str, Any]:
        target_id = str(bundle_id or "").strip()
        if not target_id:
            current_id = self.active_bundle_id()
            candidates = [
                item for item in self.list_bundles()
                if item["bundle_id"] != current_id and item["status"] != "retired"
            ]
            candidates.sort(key=lambda item: float(item.get("activated_at") or item.get("imported_at") or 0.0), reverse=True)
            if not candidates:
                raise FileNotFoundError("Kein vorheriges Curriculum-Bundle fuer einen Rollback verfuegbar.")
            target_id = str(candidates[0]["bundle_id"])
        return self.activate_bundle(session, target_id)

    def list_bundles(self) -> list[dict[str, Any]]:
        with self.repository._lock:
            rows = self.repository._conn.execute(
                "SELECT * FROM curriculum_update_bundles ORDER BY imported_at DESC, bundle_id DESC"
            ).fetchall()
        return [self._bundle_row_payload(dict(row)) for row in rows]

    def _bundle_payload(self, bundle_id: str) -> dict[str, Any] | None:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT * FROM curriculum_update_bundles WHERE bundle_id=?",
                (bundle_id,),
            ).fetchone()
        return self._bundle_row_payload(dict(row)) if row is not None else None

    def _bundle_row_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        manifest = json.loads(row.get("manifest_json") or "{}")
        signature = json.loads(row.get("signature_json") or "{}")
        with self.repository._lock:
            course_count = self.repository._conn.execute(
                "SELECT COUNT(*) AS count FROM curriculum_bundle_courses WHERE bundle_id=?",
                (row["bundle_id"],),
            ).fetchone()["count"]
            preset_count = self.repository._conn.execute(
                "SELECT COUNT(*) AS count FROM curriculum_bundle_material_presets WHERE bundle_id=?",
                (row["bundle_id"],),
            ).fetchone()["count"]
            mentor_rule_count = self.repository._conn.execute(
                "SELECT COUNT(*) AS count FROM curriculum_bundle_mentor_rules WHERE bundle_id=?",
                (row["bundle_id"],),
            ).fetchone()["count"]
        return {
            "bundle_id": row["bundle_id"],
            "title": row["title"],
            "version": row["version"],
            "status": row["status"],
            "source_name": row["source_name"],
            "archive_sha256": row["archive_sha256"],
            "imported_by": row["imported_by"],
            "imported_at": row["imported_at"],
            "activated_by": row["activated_by"],
            "activated_at": row["activated_at"],
            "course_count": int(course_count),
            "material_preset_count": int(preset_count),
            "mentor_rule_count": int(mentor_rule_count),
            "manifest": manifest,
            "signature": signature,
            "is_active": row["bundle_id"] == self.active_bundle_id(),
        }

    def _bundle_preview_payload(self, bundle: dict[str, Any]) -> dict[str, Any]:
        return {
            "bundle_id": bundle["bundle_id"],
            "manifest": dict(bundle["manifest"]),
            "signature": dict(bundle["signature"]),
            "courses": [
                {
                    "course_id": str(course.get("course_id") or ""),
                    "title": str(course.get("title") or ""),
                    "module_count": len(list(course.get("modules") or [])),
                }
                for course in bundle["courses"]
            ],
            "material_presets": [
                {
                    "key": str(item.get("key") or ""),
                    "label": str(item.get("label") or ""),
                    "profile": str(item.get("profile") or ""),
                    "language": str(item.get("language") or ""),
                }
                for item in bundle["material_presets"]
            ],
            "mentor_rules": [
                {
                    "key": str(item.get("key") or ""),
                    "course_id": str(item.get("course_id") or ""),
                    "module_id": str(item.get("module_id") or ""),
                }
                for item in bundle["mentor_rules"]
            ],
            "archive_sha256": bundle["archive_sha256"],
        }

    def _parse_bundle_archive(self, archive_bytes: bytes, *, signature_secret: str = "") -> dict[str, Any]:
        payload_bytes = bytes(archive_bytes or b"")
        if not payload_bytes:
            raise ValueError("Curriculum-Bundle ist leer.")
        try:
            archive = zipfile.ZipFile(io.BytesIO(payload_bytes))
        except zipfile.BadZipFile as exc:
            raise ValueError("Curriculum-Bundle ist kein gueltiges ZIP-Archiv.") from exc
        with archive:
            members = archive.namelist()
            if "manifest.json" not in members or "signature.json" not in members:
                raise ValueError("Curriculum-Bundle braucht mindestens manifest.json und signature.json.")
            for member in members:
                normalized_member = str(member or "").replace("\\", "/").strip()
                if not normalized_member:
                    raise ValueError("Leerer ZIP-Eintrag ist nicht erlaubt.")
                if normalized_member.startswith("/") or normalized_member.startswith("../") or "/../" in normalized_member:
                    raise ValueError("Curriculum-Bundle enthaelt einen ungueltigen Pfad.")
            manifest = self._decode_bundle_json(archive, "manifest.json")
            signature = self._decode_bundle_json(archive, "signature.json")
            bundle_id = self._slug(str(manifest.get("bundle_id") or ""))
            if not bundle_id:
                raise ValueError("manifest.json braucht eine bundle_id.")
            manifest["bundle_id"] = bundle_id
            schema_version = int(manifest.get("schema_version") or 0)
            if schema_version != CURRICULUM_BUNDLE_SCHEMA_VERSION:
                raise ValueError("Curriculum-Bundle nutzt eine nicht unterstuetzte schema_version.")
            raw_courses = self._load_bundle_raw_section(archive, "courses")
            raw_material_presets = self._load_bundle_raw_section(archive, "material_presets")
            raw_mentor_rules = self._load_bundle_raw_section(archive, "mentor_rules")
        self._verify_bundle_signature(
            manifest,
            raw_courses,
            raw_material_presets,
            raw_mentor_rules,
            signature,
            signature_secret=signature_secret,
        )
        courses = [self._normalize_bundle_course(item) for item in raw_courses]
        material_presets = [self._normalize_material_preset(item) for item in raw_material_presets]
        mentor_rules = [self._normalize_mentor_rule(item) for item in raw_mentor_rules]
        self._ensure_unique_bundle_entries(courses, key_name="course_id", section="courses")
        self._ensure_unique_bundle_entries(material_presets, key_name="key", section="material_presets")
        self._ensure_unique_bundle_entries(mentor_rules, key_name="key", section="mentor_rules")
        return {
            "bundle_id": bundle_id,
            "manifest": manifest,
            "signature": signature,
            "courses": courses,
            "material_presets": material_presets,
            "mentor_rules": mentor_rules,
            "archive_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        }

    @staticmethod
    def _decode_bundle_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
        try:
            raw = archive.read(member)
        except KeyError as exc:
            raise ValueError(f"Curriculum-Bundle-Eintrag fehlt: {member}") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"Curriculum-Bundle-Eintrag ist kein gueltiges UTF-8-JSON: {member}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Curriculum-Bundle-Eintrag muss ein JSON-Objekt sein: {member}")
        return payload

    def _load_bundle_section(
        self,
        archive: zipfile.ZipFile,
        folder_name: str,
        normalizer: Any,
    ) -> list[dict[str, Any]]:
        prefix = f"{folder_name}/"
        items: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for member in sorted(archive.namelist()):
            normalized_member = str(member or "").replace("\\", "/").strip()
            if not normalized_member.startswith(prefix) or not normalized_member.endswith(".json"):
                continue
            raw = self._decode_bundle_json(archive, normalized_member)
            normalized = normalizer(raw)
            unique_key = str(normalized.get("key") or normalized.get("course_id") or "")
            if unique_key in seen_keys:
                raise ValueError(f"Doppelte Curriculum-Bundle-ID in {folder_name}: {unique_key}")
            seen_keys.add(unique_key)
            items.append(normalized)
        return items

    def _load_bundle_raw_section(self, archive: zipfile.ZipFile, folder_name: str) -> list[dict[str, Any]]:
        prefix = f"{folder_name}/"
        items: list[dict[str, Any]] = []
        for member in sorted(archive.namelist()):
            normalized_member = str(member or "").replace("\\", "/").strip()
            if not normalized_member.startswith(prefix) or not normalized_member.endswith(".json"):
                continue
            items.append(self._decode_bundle_json(archive, normalized_member))
        return items

    @staticmethod
    def _ensure_unique_bundle_entries(items: list[dict[str, Any]], *, key_name: str, section: str) -> None:
        seen: set[str] = set()
        for item in items:
            value = str(item.get(key_name) or "").strip()
            if value in seen:
                raise ValueError(f"Doppelte Curriculum-Bundle-ID in {section}: {value}")
            seen.add(value)

    def _normalize_bundle_course(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_course_definition(
            dict(payload or {}),
            editor_username=str(payload.get("updated_by") or payload.get("issuer") or "curriculum-update"),
            allow_standard_override=True,
            is_custom=False,
        )
        normalized["is_bundle"] = True
        return normalized

    @staticmethod
    def _normalize_material_preset(payload: dict[str, Any]) -> dict[str, Any]:
        from .material_studio import PROFILE_BY_KEY, SUPPORTED_LANGUAGES

        key = str(payload.get("key") or "").strip()
        label = str(payload.get("label") or "").strip()
        profile = str(payload.get("profile") or "").strip().lower()
        language = str(payload.get("language") or "").strip().lower()
        prompt = str(payload.get("prompt") or "").strip()
        if not key or not label or not profile or not language or not prompt:
            raise ValueError("Material-Presets im Curriculum-Bundle brauchen key, label, profile, language und prompt.")
        if profile not in PROFILE_BY_KEY:
            raise ValueError("Material-Preset nutzt ein ungueltiges Agentenprofil.")
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError("Material-Preset nutzt eine ungueltige Lernsprache.")
        course_id = CurriculumService._slug(str(payload.get("course_id") or "").strip()) or str(payload.get("course_id") or "").strip()
        module_id = CurriculumService._slug(str(payload.get("module_id") or "").strip()) or str(payload.get("module_id") or "").strip()
        return {
            "key": key,
            "label": label,
            "summary": str(payload.get("summary") or payload.get("description") or "").strip(),
            "description": str(payload.get("description") or "").strip(),
            "profile": profile,
            "language": language,
            "prompt": prompt,
            "course_id": course_id,
            "module_id": module_id,
            "objectives": CurriculumService._listify(payload.get("objectives")),
        }

    @staticmethod
    def _normalize_mentor_rule(payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload.get("key") or "").strip()
        course_id = CurriculumService._slug(str(payload.get("course_id") or "").strip()) or str(payload.get("course_id") or "").strip()
        if not key or not course_id:
            raise ValueError("Mentor-Regeln im Curriculum-Bundle brauchen key und course_id.")
        module_id = CurriculumService._slug(str(payload.get("module_id") or "").strip()) or str(payload.get("module_id") or "").strip()
        return {
            "key": key,
            "course_id": course_id,
            "module_id": module_id,
            "mentor_instruction": str(payload.get("mentor_instruction") or "").strip(),
            "already_taught": CurriculumService._listify(payload.get("already_taught")),
            "avoid_revealing": CurriculumService._listify(payload.get("avoid_revealing")),
            "focus_questions": CurriculumService._listify(payload.get("focus_questions")),
        }

    def _verify_bundle_signature(
        self,
        manifest: dict[str, Any],
        courses: list[dict[str, Any]],
        material_presets: list[dict[str, Any]],
        mentor_rules: list[dict[str, Any]],
        signature: dict[str, Any],
        *,
        signature_secret: str = "",
    ) -> None:
        secret = str(signature_secret or self.repository.get_setting(CURRICULUM_BUNDLE_SECRET_SETTING, "") or "").strip()
        if not secret:
            raise ValueError("Kein Curriculum-Signaturschluessel vorhanden. Bitte im Admin-Importdialog mitgeben oder serverseitig hinterlegen.")
        algorithm = str(signature.get("algorithm") or "").strip().lower()
        if algorithm != "hmac-sha256":
            raise ValueError("Curriculum-Bundle-Signatur muss algorithm=hmac-sha256 verwenden.")
        canonical = self._canonical_bundle_payload(manifest, courses, material_presets, mentor_rules)
        expected_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if str(signature.get("canonical_sha256") or "").strip().lower() != expected_digest:
            raise ValueError("Curriculum-Bundle-Signatur passt nicht zum Paketinhalt.")
        expected_signature = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        actual_signature = str(signature.get("signature") or "").strip().lower()
        if not actual_signature or not hmac.compare_digest(expected_signature, actual_signature):
            raise ValueError("Curriculum-Bundle-Signatur ist ungueltig.")

    @staticmethod
    def _canonical_bundle_payload(
        manifest: dict[str, Any],
        courses: list[dict[str, Any]],
        material_presets: list[dict[str, Any]],
        mentor_rules: list[dict[str, Any]],
    ) -> str:
        payload = {
            "manifest": manifest,
            "courses": sorted(courses, key=lambda item: str(item.get("course_id") or "")),
            "material_presets": sorted(material_presets, key=lambda item: str(item.get("key") or "")),
            "mentor_rules": sorted(mentor_rules, key=lambda item: str(item.get("key") or "")),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def dashboard(self, session: Any) -> dict[str, Any]:
        courses = [self._course_payload(session, course) for course in self._catalog_courses()]
        payload: dict[str, Any] = {"courses": courses}
        if session.permissions.get("curriculum.manage", False):
            manager_payload: dict[str, Any] = {
                "users": [self._sanitize_user(user) for user in self.repository.list_users()],
                "groups": self.repository.list_groups(),
                "releases": self._list_releases(),
                "learners": self._learner_overview(),
                "course_definitions": [copy.deepcopy(course) for course in self._catalog_courses()],
            }
            if session.permissions.get("admin.manage", False):
                manager_payload["bundles"] = self.list_bundles()
                manager_payload["active_bundle_id"] = self.active_bundle_id()
            payload["manager"] = manager_payload
        return payload

    def material_studio_instruction_preset_catalog(self) -> list[dict[str, Any]]:
        from .material_studio import material_studio_instruction_preset_catalog

        defaults = material_studio_instruction_preset_catalog()
        bundle_presets = self._active_bundle_material_presets()
        if not bundle_presets:
            return defaults
        by_key = {str(item.get("key") or ""): dict(item) for item in defaults}
        for item in bundle_presets:
            by_key[str(item.get("key") or "")] = dict(item)
        return list(by_key.values())

    def resolve_material_studio_instruction_preset(self, preset_key: str, *, profile: str, language: str) -> dict[str, Any] | None:
        key = str(preset_key or "").strip()
        resolved_profile = str(profile or "").strip().lower()
        resolved_language = str(language or "").strip().lower()
        if not key:
            return None
        for item in self._active_bundle_material_presets():
            if str(item.get("key") or "").strip() != key:
                continue
            if str(item.get("profile") or "").strip().lower() != resolved_profile:
                continue
            if str(item.get("language") or "").strip().lower() != resolved_language:
                continue
            return dict(item)
        from .material_studio import resolve_material_studio_instruction_preset

        return resolve_material_studio_instruction_preset(key, profile=resolved_profile, language=resolved_language)

    def mentor_context(self, session: Any, *, course_id: str = "", module_id: str = "") -> dict[str, Any] | None:
        resolved_course_id = str(course_id or "").strip()
        if not resolved_course_id:
            return None
        course = self._catalog_course(resolved_course_id)
        if course is None:
            return None
        course_payload = self._course_payload(session, course)
        selected_module = None
        raw_module_id = str(module_id or "").strip()
        resolved_module_id = self._slug(raw_module_id) or raw_module_id
        if resolved_module_id and resolved_module_id != FINAL_MODULE_ID:
            selected_module = next((item for item in list(course.get("modules") or []) if str(item.get("module_id") or "") == resolved_module_id), None)
        mentor_rule = self._resolve_mentor_rule(resolved_course_id, resolved_module_id)
        passed_modules = [item["title"] for item in course_payload["modules"] if bool(item.get("passed"))]
        return {
            "course_id": resolved_course_id,
            "course_title": str(course.get("title") or resolved_course_id),
            "course_summary": str(course.get("summary") or ""),
            "module_id": resolved_module_id,
            "module_title": str((selected_module or {}).get("title") or ("Abschlusspruefung" if resolved_module_id == FINAL_MODULE_ID else "")),
            "module_objectives": list((selected_module or {}).get("objectives") or []),
            "passed_modules": passed_modules,
            "release_enabled": bool(course_payload.get("release", {}).get("enabled")),
            "mentor_rule": mentor_rule,
        }

    def attempt_history(self, course_id: str, username: str) -> dict[str, Any]:
        course = self._catalog_course(course_id)
        if course is None:
            raise FileNotFoundError("Kurs nicht gefunden.")
        user = self.repository.get_user(username)
        if user is None:
            raise FileNotFoundError("Benutzer nicht gefunden.")
        with self.repository._lock:
            rows = self.repository._conn.execute(
                """
                SELECT * FROM curriculum_attempts
                WHERE course_id=? AND username=?
                ORDER BY submitted_at DESC
                """,
                (course_id, username),
            ).fetchall()
        module_titles = {module["module_id"]: module["title"] for module in course["modules"]}
        attempts: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            module_key = str(item["module_id"])
            attempts.append(
                {
                    "attempt_id": item["attempt_id"],
                    "course_id": item["course_id"],
                    "module_id": module_key,
                    "module_title": "Abschlusspruefung" if module_key == FINAL_MODULE_ID else module_titles.get(module_key, module_key),
                    "assessment_kind": item["assessment_kind"],
                    "username": item["username"],
                    "score": float(item["score"]),
                    "max_score": float(item["max_score"]),
                    "passed": bool(item["passed"]),
                    "submitted_at": item["submitted_at"],
                    "feedback": json.loads(item["feedback_json"] or "[]"),
                }
            )
        learner_session = type(
            "CurriculumSession",
            (),
            {
                "username": username,
                "is_teacher": False,
                "permissions": {"curriculum.use": True},
                "group_ids": [group["group_id"] for group in self.repository.list_user_groups(username)],
            },
        )()
        course_payload = self._course_payload(learner_session, course)
        return {
            "learner": self._sanitize_user(user),
            "course": {
                "course_id": course["course_id"],
                "title": course["title"],
                "subject_area": course.get("subject_area", ""),
                "subtitle": course["subtitle"],
            },
            "progress": course_payload["progress"],
            "attempts": attempts,
        }

    def set_release(self, session: Any, course_id: str, scope_type: str, scope_key: str, enabled: bool, note: str = "") -> dict[str, Any]:
        course = self._catalog_course(course_id)
        if course is None:
            raise FileNotFoundError("Kurs nicht gefunden.")
        if scope_type not in {"user", "group"}:
            raise ValueError("scope_type muss 'user' oder 'group' sein.")
        scope_key = str(scope_key or "").strip()
        if not scope_key:
            raise ValueError("scope_key fehlt.")
        now = time.time()
        release_id = f"{course_id}:{scope_type}:{scope_key}"
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                """
                INSERT INTO curriculum_releases(release_id, course_id, scope_type, scope_key, enabled, note, granted_by, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(release_id) DO UPDATE SET
                    enabled=excluded.enabled,
                    note=excluded.note,
                    granted_by=excluded.granted_by,
                    updated_at=excluded.updated_at
                """,
                (release_id, course_id, scope_type, scope_key, 1 if enabled else 0, note.strip(), session.username, now, now),
            )
        return self._release_payload(release_id)

    def submit_assessment(self, session: Any, course_id: str, module_id: str, assessment_kind: str, answers: dict[str, Any]) -> dict[str, Any]:
        course = self._catalog_course(course_id)
        if course is None:
            raise FileNotFoundError("Kurs nicht gefunden.")
        release = self._resolve_release(session, course_id)
        if not release["enabled"] and not getattr(session, "is_teacher", False):
            raise PermissionError("Dieser Kurs ist fuer diese Sitzung noch nicht freigeschaltet.")

        module = self._resolve_module(course, module_id, assessment_kind)
        course_payload = self._course_payload(session, course)
        if assessment_kind == "final":
            if not bool(course_payload["progress"]["final_unlocked"]) and not getattr(session, "is_teacher", False):
                raise PermissionError("Die Abschlusspruefung ist erst nach allen bestandenen Mini-Modulen freigeschaltet.")
        else:
            module_payload = next((item for item in course_payload["modules"] if item["module_id"] == module_id), None)
            if module_payload is None:
                raise FileNotFoundError("Mini-Modul nicht gefunden.")
            if module_payload["status"] == "locked" and not getattr(session, "is_teacher", False):
                raise PermissionError("Dieses Mini-Modul ist noch nicht freigeschaltet.")

        pass_ratio = course.get("final_pass_ratio", course.get("pass_ratio", 0.75)) if assessment_kind == "final" else module.get("quiz_pass_ratio", course.get("pass_ratio", 0.7))
        grading = self._grade_assessment(module, dict(answers or {}), pass_ratio)
        attempt_id = uuid.uuid4().hex[:12]
        now = time.time()
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                """
                INSERT INTO curriculum_attempts(
                    attempt_id, course_id, module_id, assessment_kind, username, answers_json,
                    score, max_score, passed, feedback_json, submitted_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    course_id,
                    FINAL_MODULE_ID if assessment_kind == "final" else module_id,
                    assessment_kind,
                    session.username,
                    json.dumps(dict(answers or {}), ensure_ascii=False),
                    grading["score"],
                    grading["max_score"],
                    1 if grading["passed"] else 0,
                    json.dumps(grading["feedback"], ensure_ascii=False),
                    now,
                ),
            )
        certificate = self._refresh_certificate(session.username, course_id, grading if assessment_kind == "final" else None)
        return {
            "attempt_id": attempt_id,
            "course_id": course_id,
            "module_id": module_id,
            "assessment_kind": assessment_kind,
            "score": grading["score"],
            "max_score": grading["max_score"],
            "passed": grading["passed"],
            "feedback": grading["feedback"],
            "certificate": certificate,
            "course": self._course_payload(session, course),
        }

    def build_certificate_pdf(self, session: Any, course_id: str, school_name: str) -> dict[str, Any]:
        course = self._catalog_course(course_id)
        if course is None:
            raise FileNotFoundError("Kurs nicht gefunden.")
        certificate = self._certificate_for(session.username, course_id)
        if certificate is None or certificate.get("status") != "issued":
            raise FileNotFoundError("Fuer diesen Kurs liegt noch kein Zertifikat vor.")
        user = self.repository.get_user(session.username) or {}
        student_name = str(user.get("display_name") or session.username)
        pdf_bytes = build_curriculum_certificate_pdf(
            school_name=school_name,
            student_name=student_name,
            course_title=course["title"],
            certificate_title=course.get("certificate_title") or f"Zertifikat {course['title']}",
            subject_label=str(course.get("subject_area") or ""),
            theme=dict(course.get("certificate_theme") or {}),
            score=float(certificate["score"]),
            max_score=float(certificate["metadata"].get("max_score", certificate["score"])),
            issued_at=float(certificate["issued_at"]),
            certificate_id=str(certificate["certificate_id"]),
            verification_url=str(certificate["metadata"].get("verification_url", "")),
            signatory_name=str(certificate["metadata"].get("signatory_name", "")),
            signatory_title=str(certificate["metadata"].get("signatory_title", "")),
            logo_path=str(certificate["metadata"].get("logo_path", "")),
        )
        filename = f"{course_id}-{session.username}-zertifikat.pdf"
        return {"filename": filename, "content_type": "application/pdf", "content": pdf_bytes, "certificate": certificate}

    def prepare_certificate_metadata(
        self,
        username: str,
        course_id: str,
        *,
        verification_url: str,
        signatory_name: str = "",
        signatory_title: str = "",
        logo_path: str = "",
    ) -> dict[str, Any] | None:
        certificate = self._certificate_for(username, course_id)
        if certificate is None:
            return None
        metadata = dict(certificate["metadata"] or {})
        metadata["verification_url"] = str(verification_url or "").strip()
        metadata["signatory_name"] = str(signatory_name or "").strip()
        metadata["signatory_title"] = str(signatory_title or "").strip()
        metadata["logo_path"] = str(logo_path or "").strip()
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                "UPDATE curriculum_certificates SET metadata_json=?, updated_at=? WHERE certificate_id=?",
                (json.dumps(metadata, ensure_ascii=False), time.time(), certificate["certificate_id"]),
            )
        return self._certificate_for(username, course_id)

    def certificate_by_id(self, certificate_id: str) -> dict[str, Any] | None:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT * FROM curriculum_certificates WHERE certificate_id=?",
                (certificate_id,),
            ).fetchone()
        if row is None:
            return None
        metadata = json.loads(row["metadata_json"] or "{}")
        user = self.repository.get_user(str(row["username"])) or {}
        course = self._catalog_course(str(row["course_id"])) or {}
        return {
            "certificate_id": row["certificate_id"],
            "course_id": row["course_id"],
            "course_title": course.get("title") or row["course_id"],
            "certificate_title": course.get("certificate_title") or f"Zertifikat {course.get('title') or row['course_id']}",
            "subject_area": course.get("subject_area") or "",
            "username": row["username"],
            "student_name": user.get("display_name") or row["username"],
            "score": row["score"],
            "status": row["status"],
            "issued_at": row["issued_at"],
            "updated_at": row["updated_at"],
            "metadata": metadata,
        }

    def render_certificate_verification_page(self, certificate_id: str, school_name: str) -> str:
        payload = self.certificate_by_id(certificate_id)
        if payload is None:
            title = "Zertifikat nicht gefunden"
            body = """
              <article class="verify-card">
                <h1>Zertifikat nicht gefunden</h1>
                <p>Der angegebene Pruefcode ist auf diesem Server nicht bekannt.</p>
              </article>
            """
        else:
            title = "Zertifikat verifiziert"
            body = f"""
              <article class="verify-card">
                <p class="eyebrow">Zertifikatspruefung</p>
                <h1>Zertifikat verifiziert</h1>
                <p>Dieses Zertifikat wurde auf dem Nova School Server der Einrichtung <strong>{html.escape(school_name)}</strong> erstellt.</p>
                <dl class="verify-grid">
                  <div><dt>Schueler</dt><dd>{html.escape(str(payload['student_name']))}</dd></div>
                  <div><dt>Kurs</dt><dd>{html.escape(str(payload['course_title']))}</dd></div>
                  <div><dt>Fachbereich</dt><dd>{html.escape(str(payload['subject_area'] or '-'))}</dd></div>
                  <div><dt>Zertifikatsnummer</dt><dd>{html.escape(str(payload['certificate_id']))}</dd></div>
                  <div><dt>Status</dt><dd>{html.escape(str(payload['status']))}</dd></div>
                  <div><dt>Punktzahl</dt><dd>{html.escape(str(payload['score']))}</dd></div>
                  <div><dt>Ausgestellt</dt><dd>{time.strftime('%d.%m.%Y %H:%M', time.localtime(float(payload['issued_at'])))}</dd></div>
                </dl>
              </article>
            """
        return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)} | Nova School Server</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f4ead7;
        --panel: rgba(255,255,252,0.94);
        --ink: #182126;
        --muted: #5e6c6e;
        --accent: #126d67;
        --warm: #8f412f;
        --line: rgba(24,33,38,0.12);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--ink);
        background: linear-gradient(135deg, #f7eed9 0%, #d8e8df 52%, #bfd1d7 100%);
        padding: 2rem;
      }}
      .verify-shell {{
        max-width: 860px;
        margin: 0 auto;
      }}
      .verify-card {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 28px;
        padding: 2rem;
        box-shadow: 0 28px 80px rgba(24,33,38,0.14);
      }}
      .eyebrow {{
        margin: 0 0 .4rem;
        letter-spacing: .2em;
        text-transform: uppercase;
        color: var(--warm);
        font-size: .82rem;
      }}
      h1 {{ margin: 0 0 1rem; }}
      p {{ line-height: 1.6; }}
      .verify-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0 0;
      }}
      .verify-grid div {{
        background: rgba(255,255,255,0.76);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: .9rem 1rem;
      }}
      dt {{
        font-size: .85rem;
        color: var(--muted);
        margin-bottom: .25rem;
      }}
      dd {{
        margin: 0;
        font-weight: 600;
      }}
    </style>
  </head>
  <body>
    <main class="verify-shell">
      {body}
    </main>
  </body>
</html>"""

    def _ensure_schema(self) -> None:
        with self.repository._lock, self.repository._conn:
            self.repository._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS curriculum_releases (
                    release_id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    scope_type TEXT NOT NULL,
                    scope_key TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_releases_scope
                ON curriculum_releases(course_id, scope_type, scope_key);

                CREATE TABLE IF NOT EXISTS curriculum_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    assessment_kind TEXT NOT NULL,
                    username TEXT NOT NULL,
                    answers_json TEXT NOT NULL,
                    score REAL NOT NULL,
                    max_score REAL NOT NULL,
                    passed INTEGER NOT NULL,
                    feedback_json TEXT NOT NULL,
                    submitted_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_curriculum_attempts_course_user
                ON curriculum_attempts(course_id, username, submitted_at DESC);

                CREATE TABLE IF NOT EXISTS curriculum_certificates (
                    certificate_id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    score REAL NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    issued_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_certificates_course_user
                ON curriculum_certificates(course_id, username);

                CREATE TABLE IF NOT EXISTS curriculum_custom_courses (
                    course_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    updated_by TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS curriculum_update_bundles (
                    bundle_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    archive_sha256 TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    signature_json TEXT NOT NULL,
                    imported_by TEXT NOT NULL,
                    imported_at REAL NOT NULL,
                    activated_by TEXT NOT NULL,
                    activated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS curriculum_bundle_courses (
                    bundle_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(bundle_id, course_id)
                );

                CREATE TABLE IF NOT EXISTS curriculum_bundle_material_presets (
                    bundle_id TEXT NOT NULL,
                    preset_key TEXT NOT NULL,
                    profile_key TEXT NOT NULL,
                    language TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(bundle_id, preset_key)
                );

                CREATE TABLE IF NOT EXISTS curriculum_bundle_mentor_rules (
                    bundle_id TEXT NOT NULL,
                    rule_key TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(bundle_id, rule_key)
                );
                """
            )

    @staticmethod
    def _sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
        return {
            "username": user.get("username"),
            "display_name": user.get("display_name"),
            "role": user.get("role"),
            "status": user.get("status"),
        }

    def _resolve_release(self, session: Any, course_id: str) -> dict[str, Any]:
        if getattr(session, "is_teacher", False):
            return {"enabled": True, "source": "teacher", "scope_type": "teacher", "scope_key": session.username, "note": "Lehrkraftzugriff"}

        user_rows = self._query_releases(course_id, "user", [session.username])
        if user_rows:
            row = user_rows[0]
            return {"enabled": bool(row["enabled"]), "source": "user", "scope_type": "user", "scope_key": row["scope_key"], "note": row["note"], "updated_at": row["updated_at"]}

        group_rows = self._query_releases(course_id, "group", list(getattr(session, "group_ids", []) or []))
        enabled_group = next((row for row in group_rows if bool(row["enabled"])), None)
        if enabled_group:
            return {"enabled": True, "source": "group", "scope_type": "group", "scope_key": enabled_group["scope_key"], "note": enabled_group["note"], "updated_at": enabled_group["updated_at"]}

        return {"enabled": False, "source": "none", "scope_type": "", "scope_key": "", "note": ""}

    def _query_releases(self, course_id: str, scope_type: str, scope_keys: list[str]) -> list[dict[str, Any]]:
        if not scope_keys:
            return []
        placeholders = ",".join("?" for _ in scope_keys)
        query = f"SELECT * FROM curriculum_releases WHERE course_id=? AND scope_type=? AND scope_key IN ({placeholders}) ORDER BY updated_at DESC"
        with self.repository._lock:
            rows = self.repository._conn.execute(query, (course_id, scope_type, *scope_keys)).fetchall()
        return [dict(row) for row in rows]

    def _list_releases(self) -> list[dict[str, Any]]:
        with self.repository._lock:
            rows = self.repository._conn.execute("SELECT * FROM curriculum_releases ORDER BY updated_at DESC").fetchall()
        return [self._release_row_payload(dict(row)) for row in rows]

    def _release_payload(self, release_id: str) -> dict[str, Any]:
        with self.repository._lock:
            row = self.repository._conn.execute("SELECT * FROM curriculum_releases WHERE release_id=?", (release_id,)).fetchone()
        if row is None:
            raise FileNotFoundError("Freigabe nicht gefunden.")
        return self._release_row_payload(dict(row))

    def _release_row_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "release_id": row["release_id"],
            "course_id": row["course_id"],
            "scope_type": row["scope_type"],
            "scope_key": row["scope_key"],
            "enabled": bool(row["enabled"]),
            "note": row["note"],
            "granted_by": row["granted_by"],
            "updated_at": row["updated_at"],
        }

    def _latest_attempts(self, username: str, course_id: str) -> dict[tuple[str, str], dict[str, Any]]:
        with self.repository._lock:
            rows = self.repository._conn.execute(
                "SELECT * FROM curriculum_attempts WHERE course_id=? AND username=? ORDER BY submitted_at DESC",
                (course_id, username),
            ).fetchall()
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rows:
            key = (row["assessment_kind"], row["module_id"])
            if key not in latest:
                latest[key] = dict(row)
        return latest

    def _certificate_for(self, username: str, course_id: str) -> dict[str, Any] | None:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT * FROM curriculum_certificates WHERE course_id=? AND username=?",
                (course_id, username),
            ).fetchone()
        if row is None:
            return None
        metadata = json.loads(row["metadata_json"] or "{}")
        return {
            "certificate_id": row["certificate_id"],
            "course_id": row["course_id"],
            "username": row["username"],
            "score": row["score"],
            "status": row["status"],
            "issued_at": row["issued_at"],
            "updated_at": row["updated_at"],
            "metadata": metadata,
        }

    def _course_payload(self, session: Any, course: dict[str, Any]) -> dict[str, Any]:
        release = self._resolve_release(session, course["course_id"])
        attempts = self._latest_attempts(session.username, course["course_id"])
        certificate = self._certificate_for(session.username, course["course_id"])
        released = bool(release["enabled"])
        previous_passed = released or getattr(session, "is_teacher", False)
        passed_modules = 0
        modules: list[dict[str, Any]] = []

        for index, module in enumerate(course["modules"], start=1):
            row = attempts.get(("module", module["module_id"]))
            passed = bool(row and row["passed"])
            if passed:
                passed_modules += 1
            status = "locked"
            if getattr(session, "is_teacher", False) or released:
                status = "passed" if passed else ("available" if previous_passed else "locked")
            modules.append(
                {
                    "module_id": module["module_id"],
                    "title": module["title"],
                    "estimated_minutes": module["estimated_minutes"],
                    "objectives": list(module["objectives"]),
                    "lesson_markdown": module["lesson_markdown"],
                    "status": status,
                    "passed": passed,
                    "attempt_count": self._attempt_count(session.username, course["course_id"], module["module_id"], "module"),
                    "last_score": float(row["score"]) if row else 0.0,
                    "last_max_score": float(row["max_score"]) if row else 0.0,
                    "quiz": {
                        "assessment_id": f"{course['course_id']}:{module['module_id']}",
                        "pass_ratio": module.get("quiz_pass_ratio", course.get("pass_ratio", 0.7)),
                        "questions": list(module["questions"]),
                    },
                    "index": index,
                }
            )
            previous_passed = previous_passed and passed

        final_row = attempts.get(("final", FINAL_MODULE_ID))
        final_unlocked = released and all(item["passed"] for item in modules)
        final_passed = bool(final_row and final_row["passed"])
        return {
            "course_id": course["course_id"],
            "title": course["title"],
            "subtitle": course["subtitle"],
            "subject_area": course.get("subject_area", ""),
            "summary": course["summary"],
            "audience": course["audience"],
            "estimated_hours": course["estimated_hours"],
            "release": release,
            "modules": modules,
            "progress": {
                "passed_modules": passed_modules,
                "total_modules": len(modules),
                "percent": int((passed_modules / len(modules)) * 100) if modules else 0,
                "final_unlocked": final_unlocked or getattr(session, "is_teacher", False),
                "final_passed": final_passed,
                "certified": bool(certificate and certificate["status"] == "issued"),
            },
            "final_assessment": {
                "assessment_id": course["final_assessment"]["assessment_id"],
                "title": course["final_assessment"]["title"],
                "instructions": course["final_assessment"]["instructions"],
                "unlocked": final_unlocked or getattr(session, "is_teacher", False),
                "passed": final_passed,
                "attempt_count": self._attempt_count(session.username, course["course_id"], FINAL_MODULE_ID, "final"),
                "last_score": float(final_row["score"]) if final_row else 0.0,
                "last_max_score": float(final_row["max_score"]) if final_row else 0.0,
                "pass_ratio": course.get("final_pass_ratio", 0.75),
                "questions": list(course["final_assessment"]["questions"]),
            },
            "certificate": certificate,
        }

    def _attempt_count(self, username: str, course_id: str, module_id: str, assessment_kind: str) -> int:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT COUNT(*) AS count FROM curriculum_attempts WHERE username=? AND course_id=? AND module_id=? AND assessment_kind=?",
                (username, course_id, module_id, assessment_kind),
            ).fetchone()
        return int(row["count"] if row else 0)

    @staticmethod
    def _resolve_module(course: dict[str, Any], module_id: str, assessment_kind: str) -> dict[str, Any]:
        if assessment_kind == "final":
            module = dict(course["final_assessment"])
            module["questions"] = list(course["final_assessment"]["questions"])
            return module
        for module in course["modules"]:
            if module["module_id"] == module_id:
                return dict(module)
        raise FileNotFoundError("Mini-Modul nicht gefunden.")

    @staticmethod
    def _grade_assessment(module: dict[str, Any], answers: dict[str, Any], pass_ratio: float) -> dict[str, Any]:
        feedback: list[dict[str, Any]] = []
        score = 0.0
        max_score = 0.0
        for question in module["questions"]:
            earned = 0.0
            points = float(question.get("points", 1))
            max_score += points
            answer = answers.get(question["id"])
            correct = False
            if question["type"] == "single":
                value = str(answer or "").strip()
                correct = value in set(question.get("correct", []))
            elif question["type"] == "multi":
                submitted = {str(item).strip() for item in list(answer or []) if str(item).strip()}
                correct = submitted == set(question.get("correct", []))
            elif question["type"] == "text":
                normalized = str(answer or "").strip().lower()
                correct = normalized in {item.strip().lower() for item in question.get("accepted", [])}
            if correct:
                earned = points
                score += points
            feedback.append(
                {
                    "question_id": question["id"],
                    "prompt": question["prompt"],
                    "correct": correct,
                    "earned": earned,
                    "points": points,
                    "explanation": question.get("explanation", ""),
                }
            )
        passed = bool(max_score) and (score / max_score) >= float(pass_ratio or 0.0)
        return {"score": score, "max_score": max_score, "passed": passed, "feedback": feedback}

    def _refresh_certificate(self, username: str, course_id: str, final_grading: dict[str, Any] | None) -> dict[str, Any] | None:
        course = self._catalog_course(course_id)
        if course is None:
            return None
        attempts = self._latest_attempts(username, course_id)
        modules_passed = all(bool(attempts.get(("module", module["module_id"])) and attempts.get(("module", module["module_id"]))["passed"]) for module in course["modules"])
        final_row = attempts.get(("final", FINAL_MODULE_ID))
        final_passed = bool(final_grading["passed"]) if final_grading is not None else bool(final_row and final_row["passed"])
        if not modules_passed or not final_passed:
            return self._certificate_for(username, course_id)
        score = float(final_grading["score"]) if final_grading is not None else float(final_row["score"])
        max_score = float(final_grading["max_score"]) if final_grading is not None else float(final_row["max_score"])
        payload = {"course_title": course["title"], "score": score, "max_score": max_score}
        now = time.time()
        certificate_id = f"{course_id}:{username}"
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                """
                INSERT INTO curriculum_certificates(certificate_id, course_id, username, score, status, metadata_json, issued_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(certificate_id) DO UPDATE SET
                    score=excluded.score,
                    status=excluded.status,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (certificate_id, course_id, username, score, "issued", json.dumps(payload, ensure_ascii=False), now, now),
            )
        return self._certificate_for(username, course_id)

    def _learner_overview(self) -> list[dict[str, Any]]:
        learners: list[dict[str, Any]] = []
        for user in self.repository.list_users():
            if str(user.get("role") or "") != "student":
                continue
            for course in self._catalog_courses():
                session = type(
                    "CurriculumSession",
                    (),
                    {
                        "username": user["username"],
                        "is_teacher": False,
                        "permissions": {"curriculum.use": True},
                        "group_ids": [group["group_id"] for group in self.repository.list_user_groups(user["username"])],
                    },
                )()
                payload = self._course_payload(session, course)
                learners.append(
                    {
                        "username": user["username"],
                        "display_name": user["display_name"],
                        "course_id": course["course_id"],
                        "course_title": course["title"],
                        "release_enabled": bool(payload["release"]["enabled"]),
                        "passed_modules": payload["progress"]["passed_modules"],
                        "total_modules": payload["progress"]["total_modules"],
                        "final_passed": bool(payload["progress"]["final_passed"]),
                        "certified": bool(payload["progress"]["certified"]),
                    }
                )
        return learners
