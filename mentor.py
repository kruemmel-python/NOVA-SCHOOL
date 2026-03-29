from __future__ import annotations

from typing import Any

from .database import SchoolRepository


MENTOR_SYSTEM_PROMPT = (
    "Du bist Nova Mentor, ein sokratischer KI-Code-Mentor fuer eine Schulumgebung. "
    "Gib niemals sofort die volle Loesung aus. Stelle zuerst 2 bis 4 gezielte Rueckfragen oder "
    "Denkanstoesse, verweise auf relevante Stellen im Code oder auf die Fehlermeldung und erklaere "
    "das zugrunde liegende Konzept knapp. Wenn der Nutzer explizit nach der Loesung fragt, gib eine "
    "kompakte Musterloesung plus Begruendung. Bleibe freundlich, klar und technisch praezise."
)


class SocraticMentorService:
    def __init__(self, repository: SchoolRepository) -> None:
        self.repository = repository

    def thread(self, session: Any, project: dict[str, Any], *, username: str | None = None) -> list[dict[str, Any]]:
        owner = username or session.username
        if owner != session.username and not session.is_teacher:
            raise PermissionError("Mentor-Verlaeufe anderer Nutzer sind nur fuer Lehrkraefte sichtbar.")
        room_key = self._room_key(str(project["project_id"]), owner)
        messages = self.repository.list_chat_messages(room_key, limit=50)
        return [
            {
                "message_id": item["message_id"],
                "role": str(item["metadata"].get("role") or "assistant"),
                "author": item["author_display_name"],
                "text": item["message"],
                "created_at": item["created_at"],
                "mode": item["metadata"].get("mode") or "mentor",
            }
            for item in messages
        ]

    def prepare(
        self,
        session: Any,
        project: dict[str, Any],
        *,
        prompt: str,
        code: str,
        path_hint: str,
        run_output: str,
    ) -> dict[str, str]:
        history = self.thread(session, project)
        compact_history = "\n".join(f"{item['role'].upper()}: {item['text']}" for item in history[-8:])
        return {
            "prompt": self._compose_prompt(project, prompt, code, path_hint, run_output, compact_history),
            "system_prompt": MENTOR_SYSTEM_PROMPT,
        }

    def store_reply(
        self,
        session: Any,
        project: dict[str, Any],
        *,
        prompt: str,
        reply: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        room_key = self._room_key(str(project["project_id"]), session.username)
        self.repository.add_chat_message(
            room_key,
            session.username,
            session.user["display_name"],
            prompt[:4000],
            metadata={"role": "user", "mode": "mentor", "project_id": project["project_id"]},
        )
        self.repository.add_chat_message(
            room_key,
            "mentor.bot",
            "Nova Mentor",
            str(reply or "")[:8000],
            metadata={"role": "assistant", "mode": "mentor", "project_id": project["project_id"], "model": str(model or "")},
        )
        return {"reply": str(reply or ""), "model": str(model or ""), "thread": self.thread(session, project)}

    @staticmethod
    def _room_key(project_id: str, username: str) -> str:
        return f"mentor:{project_id}:{username}"

    @staticmethod
    def _compose_prompt(project: dict[str, Any], prompt: str, code: str, path_hint: str, run_output: str, history: str) -> str:
        sections = [
            f"Projekt: {project['name']}",
            f"Datei: {path_hint or project.get('main_file') or 'unbekannt'}",
            f"Aktuelle Frage:\n{prompt}",
        ]
        if run_output.strip():
            sections.append(f"Letzte Lauf-Ausgabe oder Fehlermeldung:\n```text\n{run_output}\n```")
        if code.strip():
            sections.append(f"Code-Kontext:\n```text\n{code}\n```")
        if history.strip():
            sections.append(f"Bisheriger Mentor-Verlauf:\n{history}")
        sections.append(
            "Aufgabe: Fuehre den Nutzer ueber Fragen und Hinweise zur Ursache oder Verbesserung. "
            "Nutze Debugging-Denken, Clean-Code-Hinweise und moegliche Tests."
        )
        return "\n\n".join(sections)
