from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nova_school_server.curriculum import CurriculumService
from nova_school_server.database import SchoolRepository
from nova_school_server.virtual_lecturer import VirtualLecturerService


class _Session:
    def __init__(self, username: str, *, is_teacher: bool = False, permissions: dict | None = None) -> None:
        self.username = username
        self.is_teacher = is_teacher
        self.permissions = permissions or {}
        self.group_ids: list[str] = []
        self.user = {"display_name": username.title()}


class VirtualLecturerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repository = SchoolRepository(Path(self.tmp.name) / "school.db")
        self.curriculum = CurriculumService(self.repository)
        self.repository.create_user("teacher", "Lehrkraft", "hash", "salt", "teacher", permissions={"curriculum.use": True, "curriculum.manage": True})
        self.repository.create_user("student", "Schueler", "hash", "salt", "student", permissions={"curriculum.use": True, "mentor.use": True})
        self.teacher = _Session("teacher", is_teacher=True, permissions={"curriculum.use": True, "curriculum.manage": True})
        self.student = _Session("student", permissions={"curriculum.use": True, "mentor.use": True})
        self.project = {"project_id": "p1", "name": "Python Labor", "main_file": "main.py"}
        self.service = VirtualLecturerService(self.repository, curriculum_service=self.curriculum)

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def test_start_creates_session_and_opening_message(self) -> None:
        self.curriculum.set_release(self.teacher, "python-grundlagen", "user", "student", True)

        payload = self.service.start(
            self.student,
            self.project,
            course_id="python-grundlagen",
            module_id="m01_einstieg_python",
        )

        session = payload["session"]
        self.assertEqual(session["course_id"], "python-grundlagen")
        self.assertEqual(session["module_id"], "m01_einstieg_python")
        self.assertEqual(session["task_title"], "Aufgabe 1: Erste Ausgabe mit Python")
        self.assertIn("Guido van Rossum", session["course_history"])
        self.assertEqual(len(payload["thread"]), 1)
        self.assertIn("print()", payload["thread"][0]["text"])

    def test_prepare_includes_task_and_runtime_context(self) -> None:
        self.curriculum.set_release(self.teacher, "python-grundlagen", "user", "student", True)
        self.service.start(
            self.student,
            self.project,
            course_id="python-grundlagen",
            module_id="m01_einstieg_python",
        )

        prepared = self.service.prepare(
            self.student,
            self.project,
            prompt="",
            code='print("Hallo")\nprint("Python ist gut lesbar")',
            path_hint="main.py",
            run_output="Hallo\nPython ist gut lesbar",
            event_type="run_result",
            run_returncode=0,
        )

        self.assertIn("Aktive Aufgabe: Aufgabe 1: Erste Ausgabe mit Python", prepared["prompt"])
        self.assertIn("Letzter Returncode: 0", prepared["prompt"])
        self.assertIn("Ich habe die aktuelle Aufgabe ausgefuehrt.", prepared["prompt"])
        self.assertIn("Erfolgskriterien:", prepared["prompt"])
        self.assertIn("Python ist gut lesbar", prepared["prompt"])
        self.assertEqual(prepared["mode"], "direct")

    def test_prepare_direct_feedback_accepts_valid_extended_python_intro_run(self) -> None:
        self.curriculum.set_release(self.teacher, "python-grundlagen", "user", "student", True)
        self.service.start(
            self.student,
            self.project,
            course_id="python-grundlagen",
            module_id="m01_einstieg_python",
        )

        prepared = self.service.prepare(
            self.student,
            self.project,
            prompt="",
            code=(
                'print("Hallo und herzlich willkommen!")\n'
                'print("Python ist bekannt fuer seinen gut lesbaren Quelltext.")\n'
                'print("Das macht das Lernen der Sprache einfacher.")\n'
                'print("Viel Erfolg beim Programmieren!")'
            ),
            path_hint="main.py",
            run_output=(
                "Hallo und herzlich willkommen!\n"
                "Python ist bekannt fuer seinen gut lesbaren Quelltext.\n"
                "Das macht das Lernen der Sprache einfacher.\n"
                "Viel Erfolg beim Programmieren!"
            ),
            event_type="run_result",
            run_returncode=0,
        )

        self.assertEqual(prepared["mode"], "direct")
        self.assertIn("Die Aufgabe ist inhaltlich erfuellt.", prepared["reply"])
        self.assertIn("Du verwendest 4 `print()`-Ausgaben", prepared["reply"])
        self.assertIn("Die zusaetzlichen 2 Ausgaben sind eine sinnvolle Erweiterung", prepared["reply"])
        self.assertNotIn("Es fehlt", prepared["reply"])

    def test_prepare_direct_feedback_accepts_web_intro_with_semantics_lists_and_extensions(self) -> None:
        self.curriculum.set_release(self.teacher, "web-frontend-grundlagen", "user", "student", True)
        self.service.start(
            self.student,
            self.project,
            course_id="web-frontend-grundlagen",
            module_id="w01_html_struktur",
        )

        prepared = self.service.prepare(
            self.student,
            self.project,
            prompt="Es ist doch alles drin im Code, was du als naechste Schritte genannt hast.",
            code="""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <title>Demo</title>
  <style>body { font-family: Arial; }</style>
</head>
<body>
  <header><h1>Mein Web-Frontend Projekt</h1></header>
  <main>
    <section>
      <h2>Lernfortschritt</h2>
      <ul><li>Listen</li><li>Semantik</li></ul>
    </section>
    <section>
      <button id="checkButton">Struktur pruefen</button>
      <p id="feedback"></p>
    </section>
  </main>
  <script>
    document.getElementById('checkButton').addEventListener('click', () => {
      document.getElementById('feedback').textContent = 'Erfolgreich';
    });
  </script>
</body>
</html>""",
            path_hint="index.html",
            run_output="",
            event_type="message",
            run_returncode=0,
        )

        self.assertEqual(prepared["mode"], "direct")
        self.assertIn("Du hast recht", prepared["reply"])
        self.assertIn("erfuellt den Praxisauftrag", prepared["reply"])
        self.assertIn("CSS ist eine sinnvolle Erweiterung", prepared["reply"])
        self.assertIn("JavaScript sind ebenfalls eine freiwillige Erweiterung", prepared["reply"])
        self.assertNotIn("JavaScript einsetzen", prepared["reply"])

    def test_student_cannot_start_explicitly_disabled_course(self) -> None:
        self.curriculum.set_release(self.teacher, "python-grundlagen", "user", "student", False)

        with self.assertRaises(PermissionError):
            self.service.start(
                self.student,
                self.project,
                course_id="python-grundlagen",
                module_id="m01_einstieg_python",
            )

    def test_store_reply_persists_thread_entries(self) -> None:
        self.curriculum.set_release(self.teacher, "python-grundlagen", "user", "student", True)
        self.service.start(
            self.student,
            self.project,
            course_id="python-grundlagen",
            module_id="m01_einstieg_python",
        )

        payload = self.service.store_reply(
            self.student,
            self.project,
            prompt="Ich habe die Aufgabe ausgefuehrt.",
            reply="Starker Start. Welche der beiden Ausgaben erklaert Python?",
            model="fake-lecturer",
            event_type="run_result",
        )

        self.assertEqual(payload["model"], "fake-lecturer")
        self.assertEqual(len(payload["thread"]), 3)
        self.assertEqual(payload["thread"][-1]["author"], "Nova Dozent")

    def test_store_reply_strips_internal_answer_instructions(self) -> None:
        self.curriculum.set_release(self.teacher, "python-grundlagen", "user", "student", True)
        self.service.start(
            self.student,
            self.project,
            course_id="python-grundlagen",
            module_id="m01_einstieg_python",
        )

        payload = self.service.store_reply(
            self.student,
            self.project,
            prompt="Ich habe die Aufgabe ausgefuehrt.",
            reply=(
                "## Rueckmeldung\n"
                "Alles gut.\n\n"
                "### Kontrollfrage\n"
                "Was ist `print()`?\n\n"
                "Antwortauftrag: Reagiere als virtueller Dozent. 1) Werte den Stand knapp bezogen auf die Aufgabe aus."
            ),
            model="fake-lecturer",
            event_type="run_result",
        )

        self.assertIn("## Rueckmeldung", payload["reply"])
        self.assertNotIn("Antwortauftrag:", payload["reply"])
        self.assertNotIn("Antwortauftrag:", payload["thread"][-1]["text"])


if __name__ == "__main__":
    unittest.main()
