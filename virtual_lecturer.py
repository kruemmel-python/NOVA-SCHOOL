from __future__ import annotations

import json
import re
import time
import unicodedata
import uuid
from typing import Any

from .ai_service import _prepare_prompt_with_budget
from .database import SchoolRepository


LECTURER_SYSTEM_PROMPT = (
    "Du bist Nova Dozent, ein virtueller KI-Dozent fuer Programmiergrundkurse in einer Schulumgebung. "
    "Arbeite didaktisch, klar und motivierend, aber bleibe fachlich praezise. "
    "Fuehre Lernende als sokratischer Mentor: gib keine komplette Loesung aus, ausser wenn explizit danach gefragt wird. "
    "Wenn der Lernende Code ausgefuehrt hat, bewerte den Stand bezogen auf den aktuellen Arbeitsauftrag. "
    "Lobe konkrete Fortschritte. Bei Fehlern gib 2 bis 4 gezielte Rueckfragen, Hinweise oder naechste Teilschritte. "
    "Schliesse mit genau einer passenden Kontrollfrage ab."
)
LECTURER_INPUT_TOKEN_BUDGET = 3200
AUTO_MODULE_ID = "__auto__"
FINAL_MODULE_ID = "__final__"

COURSE_HISTORY = {
    "python-grundlagen": (
        "Python wurde Anfang der 1990er Jahre von Guido van Rossum entwickelt. "
        "Die Sprache ist bewusst gut lesbar und eignet sich deshalb sehr gut fuer den Einstieg ins Programmieren."
    ),
    "datenanalyse-mit-python": (
        "Python hat sich durch Bibliotheken fuer Tabellen, Statistik und Visualisierung zu einer wichtigen Sprache fuer Datenanalyse entwickelt."
    ),
    "web-frontend-grundlagen": (
        "Web-Frontends bestehen aus HTML fuer Struktur, CSS fuer Gestaltung und JavaScript fuer Verhalten im Browser."
    ),
    "cpp-grundlagen": (
        "C++ entstand in den 1980er Jahren als Erweiterung von C und wird fuer performante und systemnahe Software eingesetzt."
    ),
    "java-oop-grundlagen": (
        "Java wurde in den 1990er Jahren fuer portable objektorientierte Anwendungen entwickelt und ist bis heute in Unterricht und Praxis verbreitet."
    ),
}

COURSE_LANGUAGES = {
    "python-grundlagen": "Python",
    "datenanalyse-mit-python": "Python",
    "web-frontend-grundlagen": "HTML, CSS und JavaScript",
    "cpp-grundlagen": "C++",
    "java-oop-grundlagen": "Java",
}


class VirtualLecturerService:
    def __init__(self, repository: SchoolRepository, *, curriculum_service: Any | None = None) -> None:
        self.repository = repository
        self.curriculum_service = curriculum_service
        self._ensure_schema()

    def session(self, session: Any, project: dict[str, Any], *, username: str | None = None) -> dict[str, Any] | None:
        owner = username or session.username
        if owner != session.username and not getattr(session, "is_teacher", False):
            raise PermissionError("Dozenten-Sitzungen anderer Nutzer sind nur fuer Lehrkraefte sichtbar.")
        row = self._session_row(str(project["project_id"]), owner)
        if row is None:
            return None
        return self._session_payload(row)

    def thread(self, session: Any, project: dict[str, Any], *, username: str | None = None) -> list[dict[str, Any]]:
        current = self.session(session, project, username=username)
        if current is None:
            return []
        messages = self.repository.list_chat_messages(str(current["room_key"]), limit=80)
        return [
            {
                "message_id": item["message_id"],
                "role": str(item["metadata"].get("role") or "assistant"),
                "author": item["author_display_name"],
                "text": item["message"],
                "created_at": item["created_at"],
                "mode": item["metadata"].get("mode") or "lecturer",
                "event_type": item["metadata"].get("event_type") or "message",
            }
            for item in messages
        ]

    def start(
        self,
        session: Any,
        project: dict[str, Any],
        *,
        course_id: str,
        module_id: str = "",
    ) -> dict[str, Any]:
        course_state = self._resolve_course_state(session, course_id=course_id, module_id=module_id)
        metadata = self._session_metadata(course_state)
        started_at = time.time()
        session_id = uuid.uuid4().hex[:12]
        room_key = self._room_key(str(project["project_id"]), session.username, session_id)
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                "DELETE FROM virtual_lecturer_sessions WHERE project_id=? AND username=?",
                (str(project["project_id"]), session.username),
            )
            self.repository._conn.execute(
                """
                INSERT INTO virtual_lecturer_sessions(
                    session_id, project_id, username, room_key, course_id, module_id, status, metadata_json, started_at, updated_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    str(project["project_id"]),
                    session.username,
                    room_key,
                    str(metadata["course_id"]),
                    str(metadata["module_id"]),
                    "active",
                    json.dumps(metadata, ensure_ascii=False),
                    started_at,
                    started_at,
                ),
            )
        opening = self._opening_message(session, project, metadata)
        self.repository.add_chat_message(
            room_key,
            "lecturer.bot",
            "Nova Dozent",
            opening,
            metadata={
                "role": "assistant",
                "mode": "lecturer",
                "event_type": "start",
                "project_id": project["project_id"],
                "course_id": metadata["course_id"],
                "module_id": metadata["module_id"],
            },
        )
        return {
            "session": self.session(session, project),
            "thread": self.thread(session, project),
        }

    def prepare(
        self,
        session: Any,
        project: dict[str, Any],
        *,
        prompt: str,
        code: str,
        path_hint: str,
        run_output: str,
        event_type: str = "message",
        run_returncode: int | None = None,
    ) -> dict[str, Any]:
        current = self.session(session, project)
        if current is None:
            raise FileNotFoundError("Es gibt noch keine aktive Dozenten-Sitzung fuer dieses Projekt.")
        resolved_prompt = str(prompt or "").strip()
        normalized_event = str(event_type or "message").strip() or "message"
        if not resolved_prompt:
            if normalized_event == "run_result":
                resolved_prompt = "Ich habe die aktuelle Aufgabe ausgefuehrt. Bitte bewerte meinen Stand."
            else:
                raise ValueError("Nachricht fuer den virtuellen Dozenten fehlt.")
        history = self.thread(session, project)
        compact_history = "\n".join(f"{item['role'].upper()}: {item['text']}" for item in history[-10:])
        prepared = {
            "mode": "infer",
            "prompt": self._compose_prompt(
                current=current,
                project=project,
                prompt=resolved_prompt,
                code=code,
                path_hint=path_hint,
                run_output=run_output,
                history=compact_history,
                event_type=normalized_event,
                run_returncode=run_returncode,
            ),
            "system_prompt": LECTURER_SYSTEM_PROMPT,
            "event_type": normalized_event,
            "resolved_prompt": resolved_prompt,
        }
        direct_reply = self._direct_reply(
            current=current,
            prompt=resolved_prompt,
            code=code,
            run_output=run_output,
            event_type=normalized_event,
            run_returncode=run_returncode,
        )
        if direct_reply:
            prepared["mode"] = "direct"
            prepared["reply"] = direct_reply
            prepared["model"] = "nova-lecturer-rules"
        return prepared

    def store_reply(
        self,
        session: Any,
        project: dict[str, Any],
        *,
        prompt: str,
        reply: str,
        model: str | None = None,
        event_type: str = "message",
    ) -> dict[str, Any]:
        current = self.session(session, project)
        if current is None:
            raise FileNotFoundError("Es gibt noch keine aktive Dozenten-Sitzung fuer dieses Projekt.")
        room_key = str(current["room_key"])
        cleaned_reply = self._sanitize_reply(reply)
        self.repository.add_chat_message(
            room_key,
            session.username,
            session.user["display_name"],
            str(prompt or "")[:4000],
            metadata={
                "role": "user",
                "mode": "lecturer",
                "event_type": event_type,
                "project_id": project["project_id"],
                "course_id": current["course_id"],
                "module_id": current["module_id"],
            },
        )
        self.repository.add_chat_message(
            room_key,
            "lecturer.bot",
            "Nova Dozent",
            cleaned_reply[:8000],
            metadata={
                "role": "assistant",
                "mode": "lecturer",
                "event_type": event_type,
                "project_id": project["project_id"],
                "course_id": current["course_id"],
                "module_id": current["module_id"],
                "model": str(model or ""),
            },
        )
        self._touch_session(str(project["project_id"]), session.username)
        return {
            "reply": cleaned_reply,
            "model": str(model or ""),
            "session": self.session(session, project),
            "thread": self.thread(session, project),
        }

    def _session_row(self, project_id: str, username: str) -> dict[str, Any] | None:
        with self.repository._lock:
            row = self.repository._conn.execute(
                "SELECT * FROM virtual_lecturer_sessions WHERE project_id=? AND username=?",
                (project_id, username),
            ).fetchone()
        return dict(row) if row is not None else None

    @staticmethod
    def _session_payload(row: dict[str, Any]) -> dict[str, Any]:
        metadata = json.loads(row.get("metadata_json") or "{}")
        return {
            "session_id": row["session_id"],
            "project_id": row["project_id"],
            "username": row["username"],
            "room_key": row["room_key"],
            "course_id": row["course_id"],
            "module_id": row["module_id"],
            "status": row["status"],
            "started_at": row["started_at"],
            "updated_at": row["updated_at"],
            **metadata,
        }

    def _touch_session(self, project_id: str, username: str) -> None:
        with self.repository._lock, self.repository._conn:
            self.repository._conn.execute(
                "UPDATE virtual_lecturer_sessions SET updated_at=? WHERE project_id=? AND username=?",
                (time.time(), project_id, username),
            )

    def _resolve_course_state(self, session: Any, *, course_id: str, module_id: str) -> dict[str, Any]:
        if self.curriculum_service is None:
            raise RuntimeError("Virtueller Dozent braucht einen Curriculum-Service.")
        dashboard = self.curriculum_service.dashboard(session)
        courses = list(dashboard.get("courses") or [])
        resolved_course_id = str(course_id or "").strip()
        if not resolved_course_id:
            raise ValueError("course_id fehlt.")
        course = next((item for item in courses if str(item.get("course_id") or "") == resolved_course_id), None)
        if course is None:
            raise FileNotFoundError("Kurs nicht gefunden.")
        if not bool(course.get("release", {}).get("enabled")) and not getattr(session, "is_teacher", False):
            raise PermissionError("Dieser Kurs ist fuer diese Sitzung noch nicht freigeschaltet.")

        requested_module_id = str(module_id or "").strip() or AUTO_MODULE_ID
        is_final = requested_module_id == FINAL_MODULE_ID
        module: dict[str, Any] | None = None
        if requested_module_id == AUTO_MODULE_ID:
            module = next((item for item in list(course.get("modules") or []) if str(item.get("status") or "") != "locked"), None)
            if module is None and getattr(session, "is_teacher", False):
                module = (list(course.get("modules") or []) or [None])[0]
            if module is None and bool(course.get("final_assessment", {}).get("unlocked")):
                is_final = True
        elif is_final:
            if not bool(course.get("final_assessment", {}).get("unlocked")) and not getattr(session, "is_teacher", False):
                raise PermissionError("Die Abschlusspruefung ist noch nicht freigeschaltet.")
        else:
            module = next((item for item in list(course.get("modules") or []) if str(item.get("module_id") or "") == requested_module_id), None)
            if module is None:
                raise FileNotFoundError("Modul nicht gefunden.")
            if str(module.get("status") or "") == "locked" and not getattr(session, "is_teacher", False):
                raise PermissionError("Dieses Modul ist noch nicht freigeschaltet.")

        if is_final:
            final_assessment = dict(course.get("final_assessment") or {})
            if not final_assessment:
                raise FileNotFoundError("Abschlusspruefung nicht gefunden.")
            module = {
                "module_id": FINAL_MODULE_ID,
                "title": str(final_assessment.get("title") or "Abschlusspruefung"),
                "objectives": [],
                "lesson_markdown": str(final_assessment.get("instructions") or ""),
                "status": "available" if bool(final_assessment.get("unlocked")) or getattr(session, "is_teacher", False) else "locked",
                "index": len(list(course.get("modules") or [])) + 1,
            }

        if module is None:
            raise FileNotFoundError("Es konnte kein passendes Modul fuer die Dozenten-Sitzung aufgeloest werden.")

        practice = self._practice_payload(course, module, is_final=is_final)
        return {
            "course": course,
            "module": module,
            "is_final": is_final,
            "practice": practice,
        }

    def _session_metadata(self, course_state: dict[str, Any]) -> dict[str, Any]:
        course = dict(course_state["course"])
        module = dict(course_state["module"])
        practice = dict(course_state["practice"])
        lesson_focus = self._lesson_focus(str(module.get("lesson_markdown") or ""))
        history = COURSE_HISTORY.get(str(course.get("course_id") or ""), f"{course.get('title') or 'Dieser Kurs'} vermittelt zentrale Grundlagen fuer den Einstieg.")
        return {
            "course_id": str(course.get("course_id") or ""),
            "course_title": str(course.get("title") or ""),
            "course_summary": str(course.get("summary") or ""),
            "course_subject_area": str(course.get("subject_area") or ""),
            "module_id": str(module.get("module_id") or ""),
            "module_title": str(module.get("title") or ""),
            "module_status": str(module.get("status") or ""),
            "module_index": int(module.get("index") or 0),
            "module_objectives": [str(item).strip() for item in list(module.get("objectives") or []) if str(item).strip()],
            "lesson_focus": lesson_focus,
            "course_history": history,
            "task_title": str(practice.get("title") or ""),
            "task_instructions": str(practice.get("instructions") or ""),
            "task_hint": str(practice.get("hint") or ""),
            "success_checks": [str(item).strip() for item in list(practice.get("success_checks") or []) if str(item).strip()],
            "language_label": str(practice.get("language_label") or ""),
        }

    def _practice_payload(self, course: dict[str, Any], module: dict[str, Any], *, is_final: bool) -> dict[str, Any]:
        module_id = str(module.get("module_id") or "")
        course_id = str(course.get("course_id") or "")
        language_label = COURSE_LANGUAGES.get(course_id, "der passenden Sprache")
        objectives = [str(item).strip() for item in list(module.get("objectives") or []) if str(item).strip()]
        primary_objective = objectives[0] if objectives else "die Kernidee des Moduls sichtbar macht"

        if course_id == "python-grundlagen" and module_id in {"m01_einstieg_python", "p01_einstieg"}:
            return {
                "language_label": "Python",
                "title": "Aufgabe 1: Erste Ausgabe mit Python",
                "instructions": (
                    "Schreibe in `main.py` ein kleines Python-Programm mit mindestens zwei `print()`-Ausgaben. "
                    "Die erste Ausgabe soll eine Begruessung zeigen, die zweite ein kurzer Satz darueber sein, dass Python gut lesbarer Quelltext ist."
                ),
                "hint": "Starte klein: zuerst nur eine Ausgabe, danach eine zweite Zeile ergaenzen und erneut ausfuehren.",
                "success_checks": [
                    "Das Programm laeuft ohne Fehler.",
                    "Im Lauf erscheint eine sichtbare Begruessung.",
                    "Es gibt mindestens zwei Ausgaben mit `print()`.",
                ],
            }

        if is_final:
            return {
                "language_label": language_label,
                "title": "Transferaufgabe zur Abschlussphase",
                "instructions": (
                    f"Erstelle ein kurzes Beispiel in {language_label}, das Inhalte aus mehreren Modulen kombiniert und nachvollziehbar kommentiert ist."
                ),
                "hint": "Nutze zuerst eine kleine Kernfunktion und erweitere sie dann schrittweise.",
                "success_checks": [
                    "Der Code laeuft oder ist fachlich nachvollziehbar aufgebaut.",
                    "Mehrere Kursideen werden sichtbar kombiniert.",
                    "Du kannst deinen Aufbau kurz begruenden.",
                ],
            }

        return {
            "language_label": language_label,
            "title": f"Praxisauftrag: {module.get('title') or 'Modul'}",
            "instructions": (
                f"Schreibe im Editor ein kurzes Beispiel in {language_label}, das zeigt, wie du {primary_objective}."
            ),
            "hint": "Arbeite in kleinen Schritten und pruefe nach jedem Schritt die Ausgabe.",
            "success_checks": [
                "Der Code laeuft ohne ungeklaerten Fehler.",
                f"Im Code oder in der Ausgabe wird sichtbar, dass du {primary_objective}.",
                "Du kannst den naechsten Verbesserungsschritt benennen.",
            ],
        }

    def _opening_message(self, session: Any, project: dict[str, Any], metadata: dict[str, Any]) -> str:
        objective_text = "\n".join(f"- {item}" for item in metadata["module_objectives"][:4]) or "- Wir arbeiten die Kernideen dieses Moduls praktisch heraus."
        success_text = "\n".join(f"- {item}" for item in metadata["success_checks"][:4]) or "- Der Code soll nachvollziehbar und lauffaehig sein."
        hint = str(metadata.get("task_hint") or "").strip()
        hint_block = f"### Start-Hinweis\n{hint}\n\n" if hint else ""
        return (
            "## Willkommen\n"
            f"Hallo {session.user['display_name']}. Ich bin dein virtueller Dozent fuer **{metadata['course_title']}**.\n\n"
            f"Wir arbeiten im Projekt **{project['name']}** und starten mit dem Modul **{metadata['module_title']}**.\n\n"
            "### Fachlicher Kontext\n"
            f"{metadata['course_history']}\n\n"
            "### Modulfokus\n"
            f"{metadata['lesson_focus'] or metadata['course_summary']}\n\n"
            "### Lernziele\n"
            f"{objective_text}\n\n"
            "### Praxisauftrag\n"
            f"**{metadata['task_title']}**\n\n"
            f"{metadata['task_instructions']}\n\n"
            f"{hint_block}"
            "### Erfolgskriterien\n"
            f"{success_text}\n\n"
            "### Naechster Schritt\n"
            "Schreibe deinen Code im Editor und starte ihn mit `Datei ausfuehren`. "
            "Ich werte deinen aktuellen Stand aus und fuehre dich dann gezielt zum naechsten Schritt."
        ).strip()

    def _compose_prompt(
        self,
        *,
        current: dict[str, Any],
        project: dict[str, Any],
        prompt: str,
        code: str,
        path_hint: str,
        run_output: str,
        history: str,
        event_type: str,
        run_returncode: int | None,
    ) -> str:
        sections = [
            f"Projekt: {project['name']}",
            f"Kurs: {current.get('course_title') or current.get('course_id')}",
            f"Modul: {current.get('module_title') or current.get('module_id')}",
            f"Aktive Aufgabe: {current.get('task_title') or 'Praxisauftrag'}",
            f"Aufgabenbeschreibung:\n{current.get('task_instructions') or ''}",
        ]
        if current.get("course_history"):
            sections.append(f"Didaktischer Kontext:\n{current['course_history']}")
        if current.get("lesson_focus"):
            sections.append(f"Modulfokus:\n{current['lesson_focus']}")
        if current.get("module_objectives"):
            sections.append(
                "Lernziele:\n" + "\n".join(f"- {item}" for item in list(current.get("module_objectives") or [])[:4])
            )
        if current.get("success_checks"):
            sections.append(
                "Erfolgskriterien:\n" + "\n".join(f"- {item}" for item in list(current.get("success_checks") or [])[:4])
            )
        sections.append(f"Ereignis: {event_type}")
        if run_returncode is not None:
            sections.append(f"Letzter Returncode: {run_returncode}")
        sections.append(f"Aktuelle Nachricht des Lernenden:\n{prompt}")
        sections.append(f"Datei: {path_hint or project.get('main_file') or 'unbekannt'}")
        if run_output.strip():
            sections.append(f"Letzte Lauf-Ausgabe oder Fehlermeldung:\n```text\n{run_output}\n```")
        if code.strip():
            sections.append(f"Aktueller Code:\n```text\n{code}\n```")
        if history.strip():
            sections.append(f"Bisheriger Dozenten-Verlauf:\n{history}")
        sections.append(
            "Antwortauftrag: Reagiere als virtueller Dozent. "
            "1) Werte den Stand knapp bezogen auf die Aufgabe aus. "
            "2) Lobe konkrete Fortschritte oder benenne das Hauptproblem. "
            "3) Gib 1 bis 3 naechste Schritte. "
            "4) Schliesse mit genau einer Kontrollfrage. "
            "Formatiere die Antwort als gut lesbaren Unterrichtstext in Markdown mit kurzen Absaetzen, "
            "klaren `###`-Ueberschriften und Listen fuer Ziele oder naechste Schritte. "
            "Vermeide Textwaende. "
            "Keine komplette Musterloesung, ausser wenn der Lernende sie ausdruecklich verlangt."
        )
        prepared_prompt, _, _ = _prepare_prompt_with_budget(
            "\n\n".join(sections),
            system_prompt=LECTURER_SYSTEM_PROMPT,
            input_budget=LECTURER_INPUT_TOKEN_BUDGET,
            reserved_tokens=1024,
        )
        return prepared_prompt

    def _direct_reply(
        self,
        *,
        current: dict[str, Any],
        prompt: str,
        code: str,
        run_output: str,
        event_type: str,
        run_returncode: int | None,
    ) -> str | None:
        if event_type != "run_result" and not self._prompt_requests_state_review(prompt):
            return None
        course_id = str(current.get("course_id") or "")
        module_id = str(current.get("module_id") or "")
        if course_id == "python-grundlagen" and module_id in {"m01_einstieg_python", "p01_einstieg"}:
            return self._python_intro_run_feedback(
                prompt=prompt,
                code=code,
                run_output=run_output,
                run_returncode=run_returncode,
            )
        if course_id == "web-frontend-grundlagen" and module_id == "w01_html_struktur":
            return self._web_frontend_intro_feedback(
                prompt=prompt,
                code=code,
                run_output=run_output,
                run_returncode=run_returncode,
            )
        return None

    def _python_intro_run_feedback(
        self,
        *,
        prompt: str,
        code: str,
        run_output: str,
        run_returncode: int | None,
    ) -> str:
        visible_lines = self._visible_output_lines(run_output)
        folded_lines = [self._fold_text(line) for line in visible_lines]
        print_count = self._count_print_calls(code)
        has_greeting = any(any(token in line for token in ("hallo", "willkommen", "begruss", "gruss")) for line in folded_lines)
        has_python_readability = any("python" in line and ("lesbar" in line or "quelltext" in line) for line in folded_lines)
        run_ok = (run_returncode in (None, 0)) and not self._contains_runtime_error(run_output)
        fulfilled = run_ok and print_count >= 2 and len(visible_lines) >= 2 and has_greeting and has_python_readability

        strengths: list[str] = []
        missing: list[str] = []
        next_steps: list[str] = []

        if run_ok:
            strengths.append("Dein Programm laeuft ohne Fehler.")
        else:
            missing.append("Der aktuelle Lauf endet noch nicht fehlerfrei.")
            next_steps.append("Lies zuerst die Fehlermeldung und korrigiere den ersten gemeldeten Fehler.")

        if print_count >= 2:
            strengths.append(f"Du verwendest {print_count} `print()`-Ausgaben und erfuellst damit die Mindestanforderung.")
        else:
            missing.append("Es sind noch weniger als zwei `print()`-Ausgaben im Code sichtbar.")
            next_steps.append("Ergaenze mindestens eine weitere `print()`-Zeile in `main.py`.")

        if has_greeting:
            strengths.append("In der Ausgabe ist eine Begruessung klar erkennbar.")
        else:
            missing.append("In der sichtbaren Ausgabe fehlt noch eine klare Begruessung.")
            next_steps.append("Formuliere die erste Ausgabe als Begruessung, zum Beispiel mit `Hallo` oder `Willkommen`.")

        if has_python_readability:
            strengths.append("Du beschreibst bereits, dass Python fuer gut lesbaren Quelltext bekannt ist.")
        else:
            missing.append("Die Ausgabe ueber Python und gut lesbaren Quelltext ist noch nicht klar genug.")
            next_steps.append("Ergaenze eine Ausgabe, in der `Python` und `gut lesbarer Quelltext` deutlich genannt werden.")

        if fulfilled and len(visible_lines) > 2:
            strengths.append(f"Die zusaetzlichen {len(visible_lines) - 2} Ausgaben sind eine sinnvolle Erweiterung und kein Fehler.")

        if fulfilled and not next_steps:
            next_steps.append("Erklaere kurz, welche zwei Ausgaben die Pflichtteile der Aufgabe abdecken.")
            next_steps.append("Behalte die beiden zusaetzlichen Ausgaben als eigene Erweiterung bewusst im Blick.")
        elif not next_steps:
            next_steps.append("Pruefe nach der Anpassung den Lauf erneut und vergleiche ihn mit dem Arbeitsauftrag.")

        summary = (
            "Die Aufgabe ist inhaltlich erfuellt."
            if fulfilled
            else "Die Aufgabe ist schon teilweise erfuellt, aber noch nicht ganz vollstaendig."
        )
        control_question = (
            "Welche zwei Ausgaben gehoeren direkt zur Pflicht der Aufgabe, und welche Ausgaben hast du zusaetzlich sinnvoll erweitert?"
            if fulfilled
            else "Welche konkrete Ausgabe oder Codezeile willst du als naechstes anpassen, damit die Aufgabe vollstaendig passt?"
        )

        strengths_block = "\n".join(f"- {item}" for item in strengths) or "- Du hast bereits einen ersten lauffaehigen Ansatz."
        missing_block = "\n".join(f"- {item}" for item in missing)
        next_steps_block = "\n".join(f"1. {item}" if index == 0 else f"{index + 1}. {item}" for index, item in enumerate(next_steps[:3]))

        parts = [
            "## Rueckmeldung zum aktuellen Lauf",
            summary,
            "",
            "### Was schon gut passt",
            strengths_block,
        ]
        if missing_block:
            parts.extend([
                "",
                "### Was noch fehlt",
                missing_block,
            ])
        parts.extend([
            "",
            "### Naechster Schritt",
            next_steps_block,
            "",
            "### Kontrollfrage",
            control_question,
        ])
        return "\n".join(parts).strip()

    def _web_frontend_intro_feedback(
        self,
        *,
        prompt: str,
        code: str,
        run_output: str,
        run_returncode: int | None,
    ) -> str:
        prompt_folded = self._fold_text(prompt)
        tag_names = self._extract_html_tags(code)
        semantic_tags = sorted(tag_names & {"header", "main", "section", "article", "nav", "footer", "aside"})
        heading_tags = sorted(tag for tag in tag_names if re.fullmatch(r"h[1-6]", tag))
        has_list = bool({"ul", "ol"} & tag_names) and "li" in tag_names
        has_structure = {"html", "head", "body"} <= tag_names
        has_title = "title" in tag_names
        has_html_focus = bool(semantic_tags) or ("main" in tag_names)
        has_button = "button" in tag_names
        has_script = "script" in tag_names and bool(re.search(r"addEventListener|getElementById|querySelector", code, flags=re.IGNORECASE))
        has_style = "style" in tag_names or bool(re.search(r"\bbody\s*\{|#[a-z0-9_-]+\s*\{|[.][a-z0-9_-]+\s*\{", code, flags=re.IGNORECASE))
        run_ok = (run_returncode in (None, 0)) and not self._contains_runtime_error(run_output)
        fulfilled = run_ok and has_structure and has_title and bool(heading_tags) and has_list and has_html_focus

        strengths: list[str] = []
        missing: list[str] = []
        next_steps: list[str] = []

        if "alles drin" in prompt_folded or "naechste schritte" in prompt_folded:
            strengths.append("Du hast recht: Die zuvor genannten Punkte zu Ueberschriften, Abschnitten und Listen sind in deinem aktuellen Code bereits sichtbar umgesetzt.")

        if run_ok:
            strengths.append("Dein aktueller Stand ist technisch stimmig und ohne erkennbaren Lauf- oder Strukturfehler.")
        else:
            missing.append("Im aktuellen Stand ist noch ein Lauf- oder Strukturfehler erkennbar.")
            next_steps.append("Pruefe zuerst die erste Fehlermeldung oder das erste ungueltige HTML-Element und korrigiere genau diesen Punkt.")

        if has_structure and has_title:
            strengths.append("Du nutzt ein vollstaendiges HTML-Grundgeruest mit `html`, `head`, `body` und `title`.")
        else:
            missing.append("Das HTML-Grundgeruest mit `html`, `head`, `body` und `title` ist noch nicht vollstaendig.")
            next_steps.append("Ergaenze das vollstaendige HTML-Grundgeruest mit `html`, `head`, `body` und `title`.")

        if heading_tags:
            strengths.append(f"Die Seite hat bereits eine klare Ueberschriftenstruktur mit `{heading_tags[0]}`{' und weiteren Ueberschriften' if len(heading_tags) > 1 else ''}.")
        else:
            missing.append("Eine klare Ueberschrift ist im Dokument noch nicht sichtbar.")
            next_steps.append("Ergaenze mindestens eine passende Ueberschrift wie `h1` oder `h2`.")

        if has_list:
            strengths.append("Listen werden bereits korrekt eingesetzt.")
        else:
            missing.append("Eine Liste mit `ul` oder `ol` und `li` fehlt noch.")
            next_steps.append("Baue eine kurze Liste mit `ul` oder `ol` und passenden `li`-Eintraegen ein.")

        if semantic_tags:
            strengths.append(f"Du verwendest semantische Elemente wie {', '.join(f'`{tag}`' for tag in semantic_tags[:4])}.")
        else:
            missing.append("Semantische HTML-Elemente wie `header`, `main` oder `section` sind noch nicht klar erkennbar.")
            next_steps.append("Strukturiere die Seite mit semantischen Elementen wie `header`, `main` und `section`.")

        if has_style:
            strengths.append("Das CSS ist eine sinnvolle Erweiterung ueber den Pflichtteil des Moduls hinaus.")
        if has_button or has_script:
            strengths.append("Interaktive Elemente mit JavaScript sind ebenfalls eine freiwillige Erweiterung und kein fehlender Punkt.")

        if fulfilled and not next_steps:
            next_steps.append("Erklaere kurz, welche HTML-Elemente in deinem Beispiel semantisch sind und warum.")
            next_steps.append("Trenne fuer dich bewusst zwischen Pflichtteil dieses Moduls und deinen zusaetzlichen Erweiterungen mit CSS und JavaScript.")
        elif not next_steps:
            next_steps.append("Vergleiche deinen Code noch einmal direkt mit den drei Modulzielen und schliesse den ersten fehlenden Punkt.")

        summary = (
            "Dein Code erfuellt den Praxisauftrag fuer dieses Modul."
            if fulfilled
            else "Dein Code geht in die richtige Richtung, erfuellt den Praxisauftrag aber noch nicht vollstaendig."
        )
        control_question = (
            "Welche Elemente in deinem Code gehoeren direkt zum HTML-Struktur-Modul, und welche Teile hast du bereits als Erweiterung mit CSS oder JavaScript hinzugefuegt?"
            if fulfilled
            else "Welcher der drei Modulpunkte fehlt in deinem Dokument noch am deutlichsten: Ueberschrift, Liste oder semantische Struktur?"
        )

        strengths_block = "\n".join(f"- {item}" for item in strengths) or "- Du hast bereits einen erkennbaren HTML-Ansatz aufgebaut."
        missing_block = "\n".join(f"- {item}" for item in missing)
        next_steps_block = "\n".join(f"1. {item}" if index == 0 else f"{index + 1}. {item}" for index, item in enumerate(next_steps[:3]))
        parts = [
            "## Rueckmeldung zum aktuellen Stand",
            summary,
            "",
            "### Was schon gut passt",
            strengths_block,
        ]
        if missing_block:
            parts.extend([
                "",
                "### Was noch fehlt",
                missing_block,
            ])
        parts.extend([
            "",
            "### Naechster Schritt",
            next_steps_block,
            "",
            "### Kontrollfrage",
            control_question,
        ])
        return "\n".join(parts).strip()

    @staticmethod
    def _fold_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(text or ""))
        return normalized.encode("ascii", "ignore").decode("ascii").lower()

    @classmethod
    def _visible_output_lines(cls, run_output: str) -> list[str]:
        lines = []
        in_notes = False
        for raw in str(run_output or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            folded = cls._fold_text(line)
            if folded == "hinweise:":
                in_notes = True
                continue
            if in_notes and line.startswith("-"):
                continue
            in_notes = False
            lines.append(line)
        return lines

    @staticmethod
    def _count_print_calls(code: str) -> int:
        count = 0
        for raw in str(code or "").splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if re.search(r"\bprint\s*\(", stripped):
                count += 1
        return count

    @classmethod
    def _contains_runtime_error(cls, run_output: str) -> bool:
        folded = cls._fold_text(run_output)
        error_markers = (
            "traceback",
            "syntaxerror",
            "nameerror",
            "typeerror",
            "valueerror",
            "indexerror",
            "attributeerror",
            "zerodivisionerror",
            "exception",
        )
        return any(marker in folded for marker in error_markers)

    @staticmethod
    def _extract_html_tags(code: str) -> set[str]:
        return {
            str(match.group(1) or "").strip().lower()
            for match in re.finditer(r"<\s*([a-zA-Z][a-zA-Z0-9-]*)\b", str(code or ""))
            if str(match.group(1) or "").strip()
        }

    @classmethod
    def _prompt_requests_state_review(cls, prompt: str) -> bool:
        folded = cls._fold_text(prompt)
        markers = (
            "bewert",
            "bewerte",
            "mein stand",
            "aktuellen stand",
            "naechste schritte",
            "alles drin",
            "vollstaendig",
            "passt doch",
            "doch alles",
        )
        return any(marker in folded for marker in markers)

    @staticmethod
    def _sanitize_reply(reply: str) -> str:
        text = str(reply or "").strip()
        if not text:
            return ""
        text = re.sub(
            r"(?:\n|^)\s*Antwortauftrag:\s*Reagiere als virtueller Dozent\.[\s\S]*$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        return text

    @staticmethod
    def _lesson_focus(lesson_markdown: str) -> str:
        source = str(lesson_markdown or "").strip()
        if not source:
            return ""
        text = re.sub(r"```[\s\S]*?```", " ", source)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"^[#>\-\*\d\.\s]+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= 260:
            return text
        shortened = text[:257].rsplit(" ", 1)[0].strip()
        return f"{shortened}..."

    @staticmethod
    def _room_key(project_id: str, username: str, session_id: str) -> str:
        return f"lecturer:{project_id}:{username}:{session_id}"

    def _ensure_schema(self) -> None:
        with self.repository._lock, self.repository._conn:
            self.repository._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS virtual_lecturer_sessions (
                    session_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    room_key TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_virtual_lecturer_project_user
                ON virtual_lecturer_sessions(project_id, username);
                """
            )
