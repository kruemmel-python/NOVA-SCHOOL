from __future__ import annotations

import hashlib
import hmac
import io
import json
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from nova_school_server.curriculum import CurriculumService
from nova_school_server.database import SchoolRepository
from nova_school_server.mentor import SocraticMentorService


class _Session:
    def __init__(self, username: str, *, is_teacher: bool = False, permissions: dict | None = None, group_ids: list[str] | None = None) -> None:
        self.username = username
        self.is_teacher = is_teacher
        self.permissions = permissions or {}
        self.group_ids = group_ids or []
        self.user = {"display_name": username.title()}


def _bundle_archive(secret: str) -> bytes:
    manifest = {
        "bundle_id": "mentor-context-2026-03",
        "schema_version": 1,
        "version": "2026.03",
        "title": "Mentor-Kontext",
        "issuer": "Nova Support",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    course = {
        "course_id": "python-grundlagen",
        "title": "Python Grundlagen",
        "subtitle": "Kontextkurs",
        "subject_area": "Programmierung mit Python",
        "summary": "Kontext fuer Mentor-Tests.",
        "audience": "Klasse 7/8",
        "estimated_hours": 8,
        "certificate_title": "Python Grundlagen",
        "pass_ratio": 0.7,
        "final_pass_ratio": 0.75,
        "certificate_theme": {},
        "modules": [
            {
                "module_id": "p01_einstieg",
                "title": "Einfuhrung in Python und Programmieren",
                "estimated_minutes": 30,
                "objectives": ["print() verstehen", "Input und Output einordnen"],
                "lesson_markdown": "## Einstieg",
                "quiz_pass_ratio": 0.7,
                "questions": [
                    {
                        "id": "q1",
                        "type": "single",
                        "prompt": "Welche Funktion erzeugt Ausgabe?",
                        "options": [{"id": "a", "label": "print"}, {"id": "b", "label": "input"}],
                        "correct": ["a"],
                        "points": 1,
                        "explanation": "print erzeugt Ausgabe.",
                    }
                ],
            }
        ],
        "final_assessment": {
            "assessment_id": "python-grundlagen-final",
            "title": "Abschluss",
            "instructions": "",
            "questions": [
                {
                    "id": "f1",
                    "type": "text",
                    "prompt": "Welches Stichwort startet eine Schleife?",
                    "accepted": ["for"],
                    "points": 1,
                    "explanation": "for startet die Schleife.",
                }
            ],
        },
    }
    mentor_rule = {
        "key": "python-grundlagen:p01_einstieg",
        "course_id": "python-grundlagen",
        "module_id": "p01_einstieg",
        "mentor_instruction": "Frage zuerst nach der Funktion von print().",
        "avoid_revealing": ["fertigen Endcode"],
        "focus_questions": ["Welche Zeile zeigt etwas auf dem Bildschirm?"],
    }
    canonical = json.dumps(
        {
            "manifest": manifest,
            "courses": [course],
            "material_presets": [],
            "mentor_rules": [mentor_rule],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    signature = {
        "algorithm": "hmac-sha256",
        "canonical_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "signature": hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest(),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
        archive.writestr("signature.json", json.dumps(signature, ensure_ascii=False))
        archive.writestr("courses/python-grundlagen.json", json.dumps(course, ensure_ascii=False))
        archive.writestr("mentor_rules/python-grundlagen-p01.json", json.dumps(mentor_rule, ensure_ascii=False))
    return buffer.getvalue()


class MentorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repository = SchoolRepository(Path(self.tmp.name) / "school.db")
        self.repository.put_setting("curriculum_bundle_secret", "mentor-secret")
        self.repository.create_user("student", "Schueler", "hash", "salt", "student", permissions={"curriculum.use": True, "mentor.use": True})
        self.service = CurriculumService(self.repository)
        admin = _Session("admin", is_teacher=True, permissions={"curriculum.update": True, "curriculum.manage": True, "curriculum.use": True})
        imported = self.service.import_bundle_archive(
            admin,
            archive_bytes=_bundle_archive("mentor-secret"),
            source_name="mentor-context.zip",
            signature_secret="mentor-secret",
        )
        self.service.activate_bundle(admin, imported["bundle"]["bundle_id"])
        self.mentor = SocraticMentorService(self.repository, curriculum_service=self.service)
        self.session = _Session("student", permissions={"curriculum.use": True, "mentor.use": True})
        self.project = {"project_id": "p1", "name": "Testprojekt", "main_file": "main.py"}

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def test_prepare_includes_curriculum_context_and_bundle_mentor_rules(self) -> None:
        payload = self.mentor.prepare(
            self.session,
            self.project,
            prompt="Warum sehe ich keine Ausgabe?",
            code='print("Hallo")',
            path_hint="main.py",
            run_output="",
            course_id="python-grundlagen",
            module_id="p01_einstieg",
        )

        self.assertIn("Kurskontext: Python Grundlagen", payload["prompt"])
        self.assertIn("Aktuelles Modul: Einfuhrung in Python und Programmieren", payload["prompt"])
        self.assertIn("Verbindliche Mentor-Vorgabe: Frage zuerst nach der Funktion von print().", payload["prompt"])
        self.assertIn("Welche Zeile zeigt etwas auf dem Bildschirm?", payload["prompt"])


if __name__ == "__main__":
    unittest.main()
