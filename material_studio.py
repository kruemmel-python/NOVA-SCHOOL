from __future__ import annotations

import ast
import json
import math
import re
import textwrap
from typing import Any

from .code_runner import CodeRunner
from .curriculum_catalog import get_course
from .database import SchoolRepository


SUPPORTED_LANGUAGES: dict[str, str] = {
    "python": "Python",
    "javascript": "JavaScript",
    "cpp": "C++",
    "java": "Java",
    "rust": "Rust",
    "html": "HTML",
    "node": "Node.js",
}

DEFAULT_MAIN_FILES: dict[str, str] = {
    "python": "main.py",
    "javascript": "main.js",
    "cpp": "main.cpp",
    "java": "Main.java",
    "rust": "main.rs",
    "html": "index.html",
    "node": "main.js",
}

MATERIAL_STUDIO_PROFILES: tuple[dict[str, str], ...] = (
    {
        "key": "example-code",
        "label": "Beispielcode",
        "description": "Erzeugt ein kompaktes, lauffaehiges und kommentiertes Unterrichtsbeispiel mit Fokus auf Erklaerbarkeit.",
        "planner_focus": "Plane ein knappes, sofort einsetzbares Unterrichtsbeispiel mit klar sichtbarem Ergebnis.",
        "author_focus": "Erstelle vor allem kommentierten Beispielcode plus kurze Unterrichtseinbettung.",
        "pedagogy_focus": "Formuliere eine kurze Lehrkraft-Moderation und eine kompakte Schuelererklaerung.",
    },
    {
        "key": "worksheet",
        "label": "Arbeitsblatt",
        "description": "Erzeugt Material fuer eine gelenkte Uebungsphase mit Arbeitsauftrag, Hilfen und kommentierter Musterloesung.",
        "planner_focus": "Plane ein Artefakt fuer eine Unterrichtsphase mit Erarbeitung, Uebung und kurzer Sicherung.",
        "author_focus": "Erstelle Arbeitsauftrag, Hilfestellungen und eine kommentierte Musterloesung fuer die Lehrkraft.",
        "pedagogy_focus": "Formuliere den Ablauf als Arbeitsblattstruktur mit Einstieg, Bearbeitung und Reflexion.",
    },
    {
        "key": "assessment",
        "label": "Klassenarbeit",
        "description": "Erzeugt pruefungsnahe Aufgabenstruktur mit Erwartungshorizont, Referenzcode und Lehrkraft-Hinweisen.",
        "planner_focus": "Plane eine pruefungsnahe Aufgabe mit klaren Kriterien, erwarteter Teilleistung und sauberem Referenzergebnis.",
        "author_focus": "Erstelle aufgabenorientiertes Material, Referenzloesungscode und klare Bewertungshinweise fuer Lehrkraefte.",
        "pedagogy_focus": "Formuliere Lehrkraft-Hinweise als Erwartungshorizont und das Schueler-Material als pruefungsnahe Aufgabenstellung.",
    },
    {
        "key": "board-lesson",
        "label": "Tafelbild",
        "description": "Erzeugt ein stark strukturiertes Unterrichtsbeispiel fuer Lehrervortrag, gemeinsame Entwicklung und Tafelbild.",
        "planner_focus": "Plane ein Artefakt fuer gelenkte Unterrichtserarbeitung an Tafel, Beamer oder gemeinsamem Editor.",
        "author_focus": "Erstelle einen besonders schrittweisen, gut vorfuehrbaren Codeaufbau mit klaren Zwischenstationen.",
        "pedagogy_focus": "Formuliere ein Tafelbild- bzw. Vortragsgeruest mit Impulsfragen und Merksaetzen.",
    },
    {
        "key": "differentiation",
        "label": "Differenzierung",
        "description": "Erzeugt Material mit abgestuften Niveaus, Hilfen und Erweiterungen fuer heterogene Lerngruppen.",
        "planner_focus": "Plane ein Artefakt mit Basisniveau, Unterstuetzung fuer schwachere Lernende und Erweiterung fuer starke Lernende.",
        "author_focus": "Erstelle differenziertes Material mit Kernaufgabe, Hilfestufe und Erweiterungsimpuls samt passendem Code.",
        "pedagogy_focus": "Formuliere die Lehrkraft-Hinweise explizit differenzierend und das Schueler-Material mit Niveaustufen.",
    },
)

PROFILE_BY_KEY: dict[str, dict[str, str]] = {item["key"]: dict(item) for item in MATERIAL_STUDIO_PROFILES}
MATERIAL_STUDIO_LANGUAGE_PRESET_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "language": "python",
        "course_id": "python-grundlagen",
        "course_label": "Python-Grundkurs",
    },
    {
        "language": "cpp",
        "course_id": "cpp-grundlagen",
        "course_label": "C++-Grundkurs",
    },
    {
        "language": "java",
        "course_id": "java-oop-grundlagen",
        "course_label": "Java-OOP-Grundkurs",
    },
    {
        "language": "html",
        "course_id": "web-frontend-grundlagen",
        "course_label": "HTML- und Frontend-Grundkurs",
        "module_ids": (
            "w01_html_struktur",
            "w02_css_layout_und_farben",
            "w03_formulare_und_zugaenglichkeit",
            "w05_frontend_projekte_und_qualitaet",
        ),
    },
    {
        "language": "javascript",
        "course_id": "javascript-grundlagen",
        "course_label": "JavaScript-Grundkurs",
        "modules": (
            {
                "module_id": "js01_einstieg_ausgabe",
                "title": "Einstieg, Ausgabe und Datentypen in JavaScript",
                "objectives": [
                    "console.log() als Ausgabekanal verstehen",
                    "Strings, Numbers und Booleans unterscheiden",
                    "Quelltext, Laufzeit und sichtbare Ausgabe einordnen",
                ],
            },
            {
                "module_id": "js02_variablen_operatoren",
                "title": "Variablen, Operatoren und Vergleiche",
                "objectives": [
                    "let und const sinnvoll einsetzen",
                    "arithmetische Operatoren und Vergleiche anwenden",
                    "Werte mit typeof einordnen",
                ],
            },
            {
                "module_id": "js03_bedingungen_schleifen_arrays",
                "title": "Bedingungen, Schleifen und Arrays",
                "objectives": [
                    "if und else fuer Entscheidungen einsetzen",
                    "for-Schleifen und for...of lesen und schreiben",
                    "Arrays mit einfachen Iterationen verarbeiten",
                ],
            },
            {
                "module_id": "js04_funktionen_und_objekte",
                "title": "Funktionen, Parameter und Objekte",
                "objectives": [
                    "eigene Funktionen mit Parametern und Rueckgabewerten erstellen",
                    "Objekte als strukturierte Daten lesen",
                    "kompakten und erklaerbaren JavaScript-Code schreiben",
                ],
            },
            {
                "module_id": "js05_json_und_fehlerbehandlung",
                "title": "JSON, einfache Fehlerbehandlung und Modularisierung",
                "objectives": [
                    "JSON als Datenformat erkennen und nutzen",
                    "try und catch als Grundmuster der Fehlerbehandlung einordnen",
                    "Hilfsfunktionen zur Strukturierung eines Skripts einsetzen",
                ],
            },
            {
                "module_id": "js06_konsolenprojekte_qualitaet",
                "title": "Kleine Konsolenprojekte und Codequalitaet",
                "objectives": [
                    "kleine JavaScript-Programme in sinnvolle Schritte zerlegen",
                    "Ausgabe, Berechnung und Eingabe logisch verbinden",
                    "Lesbarkeit, Kommentare und saubere Namen als Qualitaetsmerkmale anwenden",
                ],
            },
        ),
    },
    {
        "language": "node",
        "course_id": "nodejs-grundlagen",
        "course_label": "Node.js-Grundkurs",
        "modules": (
            {
                "module_id": "n01_einstieg_konsole",
                "title": "Node.js Einstieg, Konsole und erste Skripte",
                "objectives": [
                    "Node.js als serverseitige JavaScript-Laufzeit einordnen",
                    "console.log() fuer sichtbare Ergebnisse nutzen",
                    "den Ablauf eines einfachen Skripts Schritt fuer Schritt erklaeren",
                ],
            },
            {
                "module_id": "n02_variablen_input_typen",
                "title": "Variablen, Eingaben und Datentypen",
                "objectives": [
                    "Strings, Numbers und Booleans unterscheiden",
                    "Eingaben ueber stdin oder argv grundlegend verarbeiten",
                    "Werte mit typeof pruefen und erklaeren",
                ],
            },
            {
                "module_id": "n03_logik_arrays_schleifen",
                "title": "Logik, Arrays und Schleifen in Node.js",
                "objectives": [
                    "if und else fuer Entscheidungslogik einsetzen",
                    "Arrays mit Schleifen oder for...of verarbeiten",
                    "Programmausgabe und Eingabedaten nachvollziehbar verbinden",
                ],
            },
            {
                "module_id": "n04_funktionen_module",
                "title": "Funktionen, Module und Wiederverwendung",
                "objectives": [
                    "Funktionen mit Parametern und return-Werten einsetzen",
                    "Code in Hilfsfunktionen oder kleine Module gliedern",
                    "klare Verantwortlichkeiten in Node.js-Skripten planen",
                ],
            },
            {
                "module_id": "n05_json_dateien",
                "title": "JSON, Dateien und strukturierte Daten",
                "objectives": [
                    "JSON als Austauschformat verstehen",
                    "einfache Dateien mit der Node.js-Standardbibliothek lesen oder schreiben",
                    "Datenfluss zwischen Eingabe, Verarbeitung und Ausgabe beschreiben",
                ],
            },
            {
                "module_id": "n06_cli_projekte_fehlerbehandlung",
                "title": "Kleine CLI-Projekte und Fehlerbehandlung",
                "objectives": [
                    "ein kleines Kommandozeilenprogramm in Teilschritte zerlegen",
                    "Fehlerfaelle mit klaren Meldungen behandeln",
                    "lesbaren und robusten Node.js-Code formulieren",
                ],
            },
        ),
    },
    {
        "language": "rust",
        "course_id": "rust-grundlagen",
        "course_label": "Rust-Grundkurs",
        "modules": (
            {
                "module_id": "r01_einstieg_ausgabe",
                "title": "Rust Einstieg, println! und einfache Programme",
                "objectives": [
                    "Rust als kompilierte Programmiersprache einordnen",
                    "println! fuer sichtbare Ausgabe nutzen",
                    "Quelltext, Kompilierung und Programmlauf unterscheiden",
                ],
            },
            {
                "module_id": "r02_variablen_typen_mut",
                "title": "Variablen, Datentypen, mut und Shadowing",
                "objectives": [
                    "let und mut richtig einordnen",
                    "ganze Zahlen, Gleitkommazahlen, bool und String unterscheiden",
                    "Werteaenderung und Shadowing auf Grundniveau erklaeren",
                ],
            },
            {
                "module_id": "r03_bedingungen_schleifen_match",
                "title": "Bedingungen, Schleifen und match",
                "objectives": [
                    "if und else fuer Entscheidungen einsetzen",
                    "loop, while und for unterscheiden",
                    "match als geordnete Fallunterscheidung auf Grundniveau verstehen",
                ],
            },
            {
                "module_id": "r04_funktionen_ownership",
                "title": "Funktionen, Rueckgabewerte und Ownership-Basis",
                "objectives": [
                    "eigene Funktionen mit Parametern und Rueckgabewerten schreiben",
                    "Ownership als Schutz vor unklaren Speicherzustaenden grob einordnen",
                    "Borrowing auf einfache Beispiele beziehen",
                ],
            },
            {
                "module_id": "r05_structs_enums_vektoren",
                "title": "Structs, Enums, Strings und Vektoren",
                "objectives": [
                    "Structs als eigene Datentypen verstehen",
                    "Enums fuer Variantenmodelle einordnen",
                    "String und Vec fuer einfache Datensammlungen einsetzen",
                ],
            },
            {
                "module_id": "r06_result_option_projekte",
                "title": "Result, Option und kleine Rust-Projekte",
                "objectives": [
                    "Option und Result als sichere Rueckgabeformen unterscheiden",
                    "kleine Kommandozeilenprogramme in Teilschritte zerlegen",
                    "lesbaren und robusten Rust-Code formulieren",
                ],
            },
        ),
    },
)
STRUCTURED_PAYLOAD_WRAPPERS: tuple[str, ...] = (
    "payload",
    "data",
    "result",
    "response",
    "plan",
    "bundle",
    "artifact",
    "material",
    "output",
)
SMART_QUOTES_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00ab": '"',
        "\u00bb": '"',
    }
)
INFERENCE_IDLE_TIMEOUT_MS: dict[str, int] = {
    "plan": 35_000,
    "plan_json_repair": 18_000,
    "author": 60_000,
    "author_json_repair": 20_000,
    "author_code": 45_000,
    "author_code_repair": 18_000,
    "repair": 60_000,
    "repair_json_repair": 20_000,
    "repair_code": 45_000,
    "repair_code_repair": 18_000,
    "pedagogy": 35_000,
    "pedagogy_json_repair": 18_000,
}
PARTIAL_TIMEOUT_PHASES: frozenset[str] = frozenset(INFERENCE_IDLE_TIMEOUT_MS)
JSON_SCHEMA_PHASES: frozenset[str] = frozenset(
    {
        "plan",
        "plan_json_repair",
        "author",
        "author_json_repair",
        "repair",
        "repair_json_repair",
        "pedagogy",
        "pedagogy_json_repair",
    }
)
PROMPT_TRUNCATION_MARKER = "\n\n[... Prompt gekuerzt, um innerhalb des Modell-Kontextfensters zu bleiben ...]\n\n"
LITERT_PROMPT_INPUT_TOKEN_BUDGETS: dict[str, int] = {
    "plan": 1800,
    "plan_json_repair": 1500,
    "author": 2600,
    "author_json_repair": 1800,
    "author_code": 2400,
    "author_code_repair": 1600,
    "repair": 2800,
    "repair_json_repair": 1800,
    "repair_code": 2500,
    "repair_code_repair": 1600,
    "pedagogy": 2400,
    "pedagogy_json_repair": 1800,
}
DEFAULT_PROMPT_INPUT_TOKEN_BUDGET = 9000


def material_studio_profile_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in MATERIAL_STUDIO_PROFILES]


def _material_studio_preset_technical_lines(language: str) -> list[str]:
    label = SUPPORTED_LANGUAGES.get(language, language.title())
    if language == "html":
        return [
            "Technische Vorgaben:",
            "- nur eine Hauptdatei index.html, direkt im Schulserver nutzbar",
            "- keine externen CDNs, Frameworks oder Build-Tools",
            "- wenn CSS oder JavaScript noetig ist, dann eingebettet und knapp halten",
            "- liefere ein sichtbares Ergebnis, das in der HTML-Vorschau sofort erkennbar ist",
        ]
    if language == "javascript":
        return [
            "Technische Vorgaben:",
            "- nur eine Hauptdatei main.js, direkt lauffaehig im Schulserver",
            "- nutze console.log() fuer sichtbare Ausgabe",
            "- keine DOM- oder Browser-APIs, weil serverseitiges JavaScript ausgefuehrt wird",
            "- nur Standardfunktionen, keine externen Bibliotheken",
            "- wenn Input sinnvoll ist, liefere passendes stdin oder baue einen sicheren Fallback ein",
        ]
    if language == "node":
        return [
            "Technische Vorgaben:",
            "- nur eine Hauptdatei main.js, direkt als Node.js-Skript lauffaehig",
            "- nutze nur die Node.js-Standardbibliothek, keine Paketinstallationen",
            "- keine DOM- oder Browser-APIs",
            "- wenn Input sinnvoll ist, liefere passendes stdin oder argv-Fallbacks mit",
            "- sichtbare Ergebnisse ueber console.log() ausgeben",
        ]
    if language == "rust":
        return [
            "Technische Vorgaben:",
            "- nur eine Hauptdatei main.rs, direkt lauffaehig im Schulserver",
            "- keine externen Crates oder Cargo-Abhaengigkeiten voraussetzen",
            "- nutze die Standardbibliothek und klare println!-Ausgaben",
            "- wenn Input sinnvoll ist, liefere passendes stdin oder einen sicheren Fallback ein",
            "- erklaere Ownership, Borrowing oder Result nur so weit, wie es fuer das Beispiel noetig ist",
        ]
    main_file = DEFAULT_MAIN_FILES.get(language, "main.txt")
    return [
        "Technische Vorgaben:",
        f"- nur eine Hauptdatei {main_file}, direkt lauffaehig im Schulserver",
        f"- nur die {label}-Standardbibliothek verwenden",
        "- keine externen Bibliotheken oder Build-Schritte voraussetzen",
        "- wenn Input sinnvoll ist, liefere passendes stdin oder baue einen sicheren EOF-Default ein",
    ]


def _material_studio_preset_modules(source: dict[str, Any]) -> list[dict[str, Any]]:
    modules = source.get("modules")
    if isinstance(modules, (list, tuple)):
        return [dict(item) for item in modules]
    course = get_course(str(source.get("course_id") or "")) or {}
    allowed_module_ids = {str(item).strip() for item in (source.get("module_ids") or []) if str(item).strip()}
    resolved_modules: list[dict[str, Any]] = []
    for module in course.get("modules") or []:
        module_id = str(module.get("module_id") or "").strip()
        if allowed_module_ids and module_id not in allowed_module_ids:
            continue
        resolved_modules.append(dict(module))
    return resolved_modules


def material_studio_instruction_preset_catalog() -> list[dict[str, Any]]:
    presets: list[dict[str, Any]] = []
    for source in MATERIAL_STUDIO_LANGUAGE_PRESET_SOURCES:
        language = str(source.get("language") or "").strip().lower()
        course_id = str(source.get("course_id") or f"{language}-grundlagen").strip()
        course_label = str(source.get("course_label") or course_id).strip()
        modules = _material_studio_preset_modules(source)
        for module in modules:
            module_id = str(module.get("module_id") or "").strip()
            title = str(module.get("title") or "").strip()
            objectives = [str(item).strip() for item in (module.get("objectives") or []) if str(item).strip()]
            if not module_id or not title or not objectives:
                continue
            language_label = SUPPORTED_LANGUAGES.get(language, language.title())
            shared_intro = [
                f"Thema: {title}.",
                "Nutze diese Lernziele als Pflichtanker:",
                *[f"- {item}" for item in objectives[:3]],
                *_material_studio_preset_technical_lines(language),
            ]
            worksheet_prompt_lines = [
                f"Erstelle ein Arbeitsblatt fuer den {course_label}.",
                *shared_intro,
                "Arbeitsblattstruktur:",
                "- kurze Einfuehrung in Alltagssprache",
                "- drei Aufgaben mit steigender Schwierigkeit",
                f"- eine kompakte Musterloesung mit kommentiertem {language_label}-Code",
                "- eine kurze Reflexionsfrage am Ende",
            ]
            presets.append(
                {
                    "key": f"{language}-worksheet:{module_id}",
                    "label": title,
                    "summary": f"Arbeitsblatt-Anweisung fuer {title.lower()} im {course_label} mit klarer Aufgabenfolge und Musterloesung.",
                    "objectives": objectives,
                    "language": language,
                    "profile": "worksheet",
                    "course_id": course_id,
                    "course_label": course_label,
                    "module_id": module_id,
                    "prompt": "\n".join(worksheet_prompt_lines),
                }
            )
            example_code_prompt_lines = [
                f"Erstelle kommentierten Beispielcode fuer den {course_label}.",
                *shared_intro,
                "Beispielcode-Struktur:",
                "- kurze alltagsnahe Problemstellung als Einstieg",
                f"- ein kompaktes, direkt ausfuehrbares {language_label}-Beispiel mit klar sichtbarem Ergebnis",
                "- Kommentare an jeder wichtigen Code-Stelle",
                "- nach dem Code eine sehr kurze Erklaerung, wie das Beispiel die Lernziele zeigt",
                "- keine Arbeitsblatt-Aufgaben und keine pruefungsnahe Form",
            ]
            presets.append(
                {
                    "key": f"{language}-example-code:{module_id}",
                    "label": title,
                    "summary": f"Beispielcode-Anweisung fuer {title.lower()} im {course_label} mit kompaktem Demo-Skript und Erklaerfokus.",
                    "objectives": objectives,
                    "language": language,
                    "profile": "example-code",
                    "course_id": course_id,
                    "course_label": course_label,
                    "module_id": module_id,
                    "prompt": "\n".join(example_code_prompt_lines),
                }
            )
    return presets


def resolve_material_studio_instruction_preset(preset_key: str, *, profile: str, language: str) -> dict[str, Any] | None:
    key = str(preset_key or "").strip()
    if not key:
        return None
    resolved_profile = str(profile or "").strip().lower()
    resolved_language = str(language or "").strip().lower()
    for item in material_studio_instruction_preset_catalog():
        if str(item.get("key") or "") != key:
            continue
        if str(item.get("profile") or "").strip().lower() != resolved_profile:
            return None
        if str(item.get("language") or "").strip().lower() != resolved_language:
            return None
        return dict(item)
    return None


class TeacherMaterialStudioService:
    def __init__(
        self,
        repository: SchoolRepository,
        runner: CodeRunner,
        *,
        ai_service: Any | None = None,
        curriculum_service: Any | None = None,
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.ai_service = ai_service
        self.curriculum_service = curriculum_service

    def _ai_provider_id(self) -> str:
        return str(getattr(self.ai_service, "provider_id", "") or "").strip().lower()

    def _requires_visible_output(self, state: dict[str, Any], bundle: dict[str, Any], run_result: dict[str, Any]) -> bool:
        profile_key = str(state.get("profile_key") or "example-code").strip().lower()
        if profile_key == "assessment":
            return False
        language = self._normalize_language(str(bundle.get("language") or state.get("language") or "python"))
        if language == "html":
            return False
        if str(run_result.get("preview_path") or "").strip():
            return False
        return True

    @staticmethod
    def _python_has_missing_main_invocation(code: str) -> bool:
        candidate = str(code or "").strip()
        if not candidate or "def main" not in candidate:
            return False
        try:
            tree = ast.parse(candidate)
        except Exception:
            return False
        has_main_definition = any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main" for node in tree.body)
        if not has_main_definition:
            return False

        class _MainCallVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.calls_main = False

            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Name) and func.id == "main":
                    self.calls_main = True
                self.generic_visit(node)

        visitor = _MainCallVisitor()
        visitor.visit(tree)
        return not visitor.calls_main

    def start_generation(
        self,
        *,
        prompt: str,
        language: str,
        profile: str = "example-code",
        instruction_preset_key: str = "",
        attempt_limit: int = 3,
        seed_code: str = "",
        seed_path: str = "",
    ) -> dict[str, Any]:
        prompt_text = str(prompt or "").strip()
        if not prompt_text:
            raise ValueError("Prompt fuer das Material-Studio fehlt.")
        resolved_language = self._normalize_language(language)
        resolved_profile = self._normalize_profile(profile)
        state = {
            "prompt": prompt_text,
            "language": resolved_language,
            "profile_key": resolved_profile["key"],
            "instruction_preset_key": str(instruction_preset_key or "").strip(),
            "attempt_limit": max(1, min(int(attempt_limit or 3), 5)),
            "seed_code": str(seed_code or ""),
            "seed_path": str(seed_path or ""),
            "trace": [],
            "runs_used": 0,
            "successful": False,
        }
        return self._issue_plan_step(state)

    def continue_generation(
        self,
        session: Any,
        *,
        generation_state: dict[str, Any],
        response_text: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        state = self._coerce_generation_state(generation_state)
        raw_text = str(response_text or "")
        if not raw_text.strip():
            raise ValueError("Material-Studio Antworttext fehlt.")
        phase = str(state.get("phase") or "").strip()
        if phase == "plan":
            return self._consume_plan_response(state, raw_text, str(model or ""))
        if phase == "plan_json_repair":
            return self._consume_plan_repair_response(state, raw_text, str(model or ""))
        if phase == "author":
            return self._consume_author_response(session, state, raw_text, str(model or ""))
        if phase == "author_json_repair":
            return self._consume_author_repair_response(session, state, raw_text, str(model or ""))
        if phase == "author_code":
            return self._consume_author_code_response(session, state, raw_text, str(model or ""))
        if phase == "author_code_repair":
            return self._consume_author_code_repair_response(session, state, raw_text, str(model or ""))
        if phase == "repair":
            return self._consume_debugger_response(session, state, raw_text, str(model or ""))
        if phase == "repair_json_repair":
            return self._consume_debugger_repair_response(session, state, raw_text, str(model or ""))
        if phase == "repair_code":
            return self._consume_debugger_code_response(session, state, raw_text, str(model or ""))
        if phase == "repair_code_repair":
            return self._consume_debugger_code_repair_response(session, state, raw_text, str(model or ""))
        if phase == "pedagogy":
            return self._consume_pedagogy_response(state, raw_text, str(model or ""))
        if phase == "pedagogy_json_repair":
            return self._consume_pedagogy_repair_response(state, raw_text, str(model or ""))
        raise ValueError("Unbekannte Material-Studio-Phase.")

    def generate(
        self,
        session: Any,
        *,
        prompt: str,
        language: str,
        profile: str = "example-code",
        instruction_preset_key: str = "",
        attempt_limit: int = 3,
        seed_code: str = "",
        seed_path: str = "",
    ) -> dict[str, Any]:
        payload = self.start_generation(
            prompt=prompt,
            language=language,
            profile=profile,
            instruction_preset_key=instruction_preset_key,
            attempt_limit=attempt_limit,
            seed_code=seed_code,
            seed_path=seed_path,
        )
        while isinstance(payload, dict) and payload.get("mode") == "infer":
            raw_text, model = self._complete_inference_payload(payload)
            payload = self.continue_generation(
                session,
                generation_state=dict(payload.get("generation_state") or {}),
                response_text=raw_text,
                model=model,
            )
        if not isinstance(payload, dict):
            raise RuntimeError("Material-Studio hat kein gueltiges Endergebnis geliefert.")
        return payload

    def run_current(self, session: Any, payload: dict[str, Any]) -> dict[str, Any]:
        language = self._normalize_language(str(payload.get("language") or "python"))
        profile = self._normalize_profile(str(payload.get("profile") or "example-code"))
        main_file = str(payload.get("main_file") or DEFAULT_MAIN_FILES[language]).strip() or DEFAULT_MAIN_FILES[language]
        files = payload.get("files")
        if not files:
            files = [{"path": main_file, "content": str(payload.get("code") or "")}]
        normalized = self._normalize_bundle(
            {
                "title": str(payload.get("title") or "Material-Studio Lauf"),
                "summary": str(payload.get("summary") or ""),
                "language": language,
                "main_file": main_file,
                "stdin": str(payload.get("stdin") or ""),
                "teacher_notes_markdown": str(payload.get("teacher_notes_markdown") or ""),
                "student_material_markdown": str(payload.get("student_material_markdown") or ""),
                "files": files,
            },
            language,
            {
                "title": str(payload.get("title") or "Material-Studio Lauf"),
                "learning_goal": "",
                "execution_goal": "",
                "main_file": main_file,
            },
        )
        run_result = self.runner.run_bundle(
            session,
            {
                "language": normalized["language"],
                "main_file": normalized["main_file"],
                "stdin": normalized.get("stdin") or "",
                "files": normalized["files"],
            },
        )
        return self._bundle_response(
            normalized,
            run_result,
            [],
            passed=run_result["returncode"] == 0,
            attempt_limit=1,
            teacher_notes=str(normalized.get("teacher_notes_markdown") or ""),
            student_material=str(normalized.get("student_material_markdown") or ""),
            profile=profile,
        )

    def _coerce_generation_state(self, generation_state: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(generation_state, dict):
            raise ValueError("Material-Studio Zustand fehlt.")
        prompt_text = str(generation_state.get("prompt") or "").strip()
        if not prompt_text:
            raise ValueError("Material-Studio Prompt fehlt im Zustand.")
        state = dict(generation_state)
        state["prompt"] = prompt_text
        state["language"] = self._normalize_language(str(state.get("language") or "python"))
        state["profile_key"] = self._normalize_profile(str(state.get("profile_key") or "example-code"))["key"]
        state["instruction_preset_key"] = str(state.get("instruction_preset_key") or "").strip()
        state["attempt_limit"] = max(1, min(int(state.get("attempt_limit") or 3), 5))
        state["seed_code"] = str(state.get("seed_code") or "")
        state["seed_path"] = str(state.get("seed_path") or "")
        state["trace"] = [dict(item) for item in list(state.get("trace") or []) if isinstance(item, dict)]
        state["runs_used"] = max(0, int(state.get("runs_used") or 0))
        state["successful"] = bool(state.get("successful"))
        if isinstance(state.get("plan"), dict):
            state["plan"] = dict(state["plan"])
        if isinstance(state.get("working_bundle"), dict):
            state["working_bundle"] = dict(state["working_bundle"])
        if isinstance(state.get("run_result"), dict):
            state["run_result"] = dict(state["run_result"])
        return state

    def _complete_inference_payload(self, payload: dict[str, Any]) -> tuple[str, str]:
        if self.ai_service is None:
            raise RuntimeError("Material-Studio-Inferenz ist ohne KI-Service nicht verfuegbar.")
        prompt_text = str(payload.get("prompt") or "")
        system_prompt = str(payload.get("system_prompt") or "")
        response_format = dict(payload.get("response_format") or {}) or None
        generation_options = dict(payload.get("generation_options") or {}) or None
        timeout_seconds = float(payload.get("timeout_seconds") or 120.0)
        phase = str(payload.get("phase") or "").strip().lower()
        try:
            return self.ai_service.complete(
                prompt=prompt_text,
                system_prompt=system_prompt,
                response_format=response_format,
                generation_options=generation_options,
                timeout_seconds=timeout_seconds,
            )
        except RuntimeError as exc:
            if not self._is_model_input_too_long_error(exc):
                raise
            retry_prompt, _, _, retry_truncated = self._prepare_inference_prompt(
                prompt_text,
                system_prompt=system_prompt,
                phase=phase,
                extra_safety_tokens=480,
            )
            if not retry_truncated or retry_prompt == prompt_text:
                raise RuntimeError(
                    "Material-Studio Prompt ueberschreitet weiterhin das Kontextlimit des lokalen Modells. "
                    "Bitte Lehrer-Prompt oder Materialumfang kuerzen."
                ) from exc
            return self.ai_service.complete(
                prompt=retry_prompt,
                system_prompt=system_prompt,
                response_format=response_format,
                generation_options=generation_options,
                timeout_seconds=timeout_seconds,
            )

    def _inference_step(
        self,
        state: dict[str, Any],
        *,
        phase: str,
        status: str,
        prompt: str,
        system_prompt: str,
    ) -> dict[str, Any]:
        next_state = dict(state)
        next_state["phase"] = phase
        prepared_prompt, prompt_token_estimate, prompt_token_budget, prompt_truncated = self._prepare_inference_prompt(
            prompt,
            system_prompt=system_prompt,
            phase=phase,
        )
        return {
            "mode": "infer",
            "phase": phase,
            "status": status,
            "prompt": prepared_prompt,
            "system_prompt": system_prompt,
            "generation_state": next_state,
            "agent_trace": list(next_state.get("trace") or []),
            "idle_timeout_ms": INFERENCE_IDLE_TIMEOUT_MS.get(phase, 0),
            "accept_partial_on_timeout": phase in PARTIAL_TIMEOUT_PHASES,
            "generation_options": self._generation_options_for_phase(phase),
            "response_format": {"type": "json_object"} if phase in JSON_SCHEMA_PHASES else None,
            "timeout_seconds": self._timeout_seconds_for_phase(phase),
            "prompt_token_estimate": prompt_token_estimate,
            "prompt_token_budget": prompt_token_budget,
            "prompt_truncated": prompt_truncated,
        }

    def _profile_from_state(self, state: dict[str, Any]) -> dict[str, str]:
        return self._normalize_profile(str(state.get("profile_key") or "example-code"))

    def _instruction_preset_from_state(self, state: dict[str, Any]) -> dict[str, Any] | None:
        profile = self._profile_from_state(state)
        preset_key = str(state.get("instruction_preset_key") or "")
        language = str(state.get("language") or "python")
        if self.curriculum_service is not None:
            resolved = self.curriculum_service.resolve_material_studio_instruction_preset(
                preset_key,
                profile=profile["key"],
                language=language,
            )
            if resolved is not None:
                return resolved
        return self._normalize_instruction_preset(preset_key, profile["key"], language)

    @staticmethod
    def _normalize_instruction_preset(preset_key: str, profile_key: str, language: str) -> dict[str, Any] | None:
        return resolve_material_studio_instruction_preset(
            preset_key,
            profile=profile_key,
            language=language,
        )

    @staticmethod
    def _normalize_compare_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip()).casefold()

    def _instruction_preset_lines(
        self,
        instruction_preset: dict[str, Any] | None,
        *,
        prompt_text: str = "",
    ) -> list[str]:
        if not instruction_preset:
            return []
        preset_prompt = str(instruction_preset.get("prompt") or "").strip()
        if preset_prompt and prompt_text:
            if self._normalize_compare_text(preset_prompt) in self._normalize_compare_text(prompt_text):
                return []
        objectives = [
            str(item).strip()
            for item in (instruction_preset.get("objectives") or [])
            if str(item).strip()
        ]
        return [
            "",
            "Verbindliche Kursvorgabe:",
            f"Preset: {instruction_preset.get('label')}",
            *([f"Pflichtanker: {item}" for item in objectives[:3]] or [preset_prompt]),
        ]

    def _prompt_input_token_budget(self, phase: str) -> int:
        key = str(phase or "").strip().lower()
        if self._ai_provider_id() == "server-litert-lm":
            return LITERT_PROMPT_INPUT_TOKEN_BUDGETS.get(key, 2200)
        return DEFAULT_PROMPT_INPUT_TOKEN_BUDGET

    @staticmethod
    def _normalize_prompt_text(text: str) -> str:
        normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[ \t]+\n", "\n", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        normalized = TeacherMaterialStudioService._normalize_prompt_text(text)
        if not normalized:
            return 0
        compact = re.sub(r"\s+", " ", normalized).strip()
        word_count = len(re.findall(r"\S+", compact))
        char_based = math.ceil(len(compact) / 2.8)
        word_based = math.ceil(word_count * 1.45)
        return max(char_based, word_based, 1)

    @staticmethod
    def _trim_text_middle(text: str, *, max_chars: int) -> str:
        normalized = TeacherMaterialStudioService._normalize_prompt_text(text)
        if len(normalized) <= max_chars:
            return normalized
        marker = PROMPT_TRUNCATION_MARKER
        if max_chars <= len(marker) + 96:
            return normalized[:max_chars].rstrip()
        head_chars = int(max_chars * 0.56)
        tail_chars = max_chars - head_chars - len(marker)
        if tail_chars < 80:
            tail_chars = 80
            head_chars = max(80, max_chars - tail_chars - len(marker))
        return (
            normalized[:head_chars].rstrip()
            + marker
            + normalized[-tail_chars:].lstrip()
        ).strip()

    @staticmethod
    def _is_model_input_too_long_error(error: Exception) -> bool:
        text = str(error or "")
        if not text:
            return False
        lowered = text.lower()
        return (
            "input token ids are too long" in lowered
            or "maximum number of tokens allowed" in lowered
            or "context limit" in lowered
        )

    def _prepare_inference_prompt(
        self,
        prompt: str,
        *,
        system_prompt: str,
        phase: str,
        extra_safety_tokens: int = 0,
    ) -> tuple[str, int, int, bool]:
        normalized_prompt = self._normalize_prompt_text(prompt)
        if not normalized_prompt:
            return "", 0, self._prompt_input_token_budget(phase), False
        phase_budget = self._prompt_input_token_budget(phase)
        system_tokens = self._estimate_token_count(system_prompt)
        available_tokens = max(256, phase_budget - system_tokens - 96 - max(0, int(extra_safety_tokens or 0)))
        estimated_tokens = self._estimate_token_count(normalized_prompt)
        if estimated_tokens <= available_tokens:
            return normalized_prompt, estimated_tokens, phase_budget, False
        max_chars = min(len(normalized_prompt), max(720, int(available_tokens * 2.35)))
        trimmed_prompt = self._trim_text_middle(normalized_prompt, max_chars=max_chars)
        while self._estimate_token_count(trimmed_prompt) > available_tokens and max_chars > 720:
            next_chars = max(720, int(max_chars * 0.82))
            if next_chars >= max_chars:
                break
            max_chars = next_chars
            trimmed_prompt = self._trim_text_middle(normalized_prompt, max_chars=max_chars)
        return trimmed_prompt, self._estimate_token_count(trimmed_prompt), phase_budget, trimmed_prompt != normalized_prompt

    def _generation_options_for_phase(self, phase: str) -> dict[str, Any]:
        key = str(phase or "").strip().lower()
        if key == "plan":
            return {"max_tokens": 480, "temperature": 0.2}
        if key == "pedagogy":
            return {"max_tokens": 1024, "temperature": 0.38}
        if key.endswith("code") or key.endswith("code_repair"):
            return {"max_tokens": 1280, "temperature": 0.28}
        return {"max_tokens": 1400, "temperature": 0.3}

    def _timeout_seconds_for_phase(self, phase: str) -> float:
        key = str(phase or "").strip().lower()
        if key == "plan":
            return 240.0
        if key == "pedagogy":
            return 240.0
        if key.endswith("code") or key.endswith("code_repair"):
            return 300.0
        return 300.0

    @staticmethod
    def _agent_summary(summary: str, instruction_preset: dict[str, Any] | None) -> str:
        base = str(summary or "").strip()
        if not instruction_preset:
            return base
        label = str(instruction_preset.get("label") or "").strip()
        if not label:
            return base
        return f"{base} | Vorgabe: {label}"

    def _state_plan(self, state: dict[str, Any]) -> dict[str, Any]:
        plan = state.get("plan")
        if not isinstance(plan, dict):
            raise ValueError("Material-Studio Plan fehlt.")
        return dict(plan)

    def _state_bundle(self, state: dict[str, Any]) -> dict[str, Any]:
        bundle = state.get("working_bundle")
        if not isinstance(bundle, dict):
            raise ValueError("Material-Studio Bundle fehlt.")
        return dict(bundle)

    def _state_run_result(self, state: dict[str, Any], language: str) -> dict[str, Any]:
        payload = state.get("run_result")
        if isinstance(payload, dict):
            return dict(payload)
        return {
            "run_id": "",
            "language": language,
            "command": [],
            "stdout": "",
            "stderr": "Keine Ausfuehrung erfolgt.",
            "returncode": 1,
            "duration_ms": 0,
            "preview_path": "",
            "notes": [],
            "tool_session": {},
        }

    def _issue_json_repair_step(self, state: dict[str, Any], *, phase: str, status: str, raw_text: str) -> dict[str, Any]:
        prompt = self._json_repair_prompt(raw_text)
        system_prompt = (
            "Du reparierst Modellantworten fuer einen JSON-Parser. "
            "Gib exakt ein gueltiges JSON-Objekt ohne Markdown-Codebloecke, Kommentare oder Zusatztext aus. "
            "Wenn mehrere JSON-Objekte vorliegen, fuehre ihre Felder in einem einzigen Objekt zusammen. "
            "Escape Zeilenumbrueche und Anfuehrungszeichen in Stringwerten korrekt."
        )
        if phase == "pedagogy_json_repair":
            bundle = self._state_bundle(state)
            run_result = self._state_run_result(state, bundle["language"])
            prompt = self._pedagogy_json_repair_prompt(
                raw_text,
                {
                    "title": bundle["title"],
                    "summary": bundle["summary"],
                    "language": bundle["language"],
                    "main_file": bundle["main_file"],
                    "code": self._main_file_content(bundle["files"], bundle["main_file"]),
                    "prompt": state["prompt"],
                    "profile": self._profile_from_state(state),
                },
                self._profile_from_state(state),
                run_result,
                instruction_preset=self._instruction_preset_from_state(state),
            )
            system_prompt = (
                "Du reparierst Didaktikantworten fuer Unterrichtsmaterial. "
                "Gib exakt ein gueltiges JSON-Objekt mit teacher_notes_markdown und student_material_markdown aus. "
                "Keine Analyse, keine Meta-Erklaerung, kein Markdown-Codeblock."
            )
        return self._inference_step(
            state,
            phase=phase,
            status=status,
            prompt=prompt,
            system_prompt=system_prompt,
        )

    def _issue_code_repair_step(self, state: dict[str, Any], *, phase: str, status: str, raw_text: str) -> dict[str, Any]:
        return self._inference_step(
            state,
            phase=phase,
            status=status,
            prompt=self._code_repair_prompt(raw_text),
            system_prompt="Du extrahierst nur Code. Antworte exakt mit einem einzelnen Markdown-Codeblock.",
        )

    def _issue_plan_step(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        instruction_preset = self._instruction_preset_from_state(state)
        return self._inference_step(
            state,
            phase="plan",
            status="Planer strukturiert das Unterrichtsartefakt...",
            prompt=self._planner_prompt(
                state["prompt"],
                state["language"],
                profile,
                seed_code=state["seed_code"],
                seed_path=state["seed_path"],
                instruction_preset=instruction_preset,
            ),
            system_prompt=(
                f"Du bist Nova Studio Planner fuer das Profil '{profile['label']}'. "
                "Plane fuer eine Lehrkraft lauffaehiges Unterrichtsmaterial. "
                "Antworte ausschliesslich als JSON. Kein Freitext ausserhalb von JSON."
            ),
        )

    def _consume_plan_response(self, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            plan = self._normalize_plan(self._parse_json_response(raw_text, schema_name="plan"), state["language"])
        except Exception:
            return self._issue_json_repair_step(
                state,
                phase="plan_json_repair",
                status="Planerantwort wird in valides JSON ueberfuehrt...",
                raw_text=raw_text,
            )
        state["plan"] = plan
        state["trace"].append(
            {
                "agent": "Planer",
                "stage": "plan",
                "status": "completed",
                "model": model,
                "summary": self._agent_summary(
                    f"{plan['title']} | Profil: {profile['label']} | Hauptdatei: {plan['main_file']}",
                    instruction_preset,
                ),
            }
        )
        return self._issue_author_step(state)

    def _consume_plan_repair_response(self, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            plan = self._normalize_plan(self._parse_json_response(raw_text, schema_name="plan"), state["language"])
            state["trace"].append(
                {
                    "agent": "Planer",
                    "stage": "plan",
                    "status": "completed",
                    "model": model,
                    "summary": self._agent_summary(
                        f"{plan['title']} | Profil: {profile['label']} | Hauptdatei: {plan['main_file']}",
                        instruction_preset,
                    ),
                }
            )
        except Exception:
            plan = self._fallback_plan(state["prompt"], state["language"], profile, seed_path=state["seed_path"])
            state["trace"].append(
                {
                    "agent": "Planer",
                    "stage": "plan",
                    "status": "warning",
                    "model": "fallback",
                    "summary": self._agent_summary(
                        f"Planer-JSON ungueltig, Fallback-Plan verwendet | Hauptdatei: {plan['main_file']}",
                        instruction_preset,
                    ),
                }
            )
        state["plan"] = plan
        return self._issue_author_step(state)

    def _issue_author_step(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        plan = self._state_plan(state)
        instruction_preset = self._instruction_preset_from_state(state)
        return self._inference_step(
            state,
            phase="author",
            status="Autor erzeugt Bundle und Beispielcode...",
            prompt=self._author_prompt(
                state["prompt"],
                plan,
                profile,
                seed_code=state["seed_code"],
                seed_path=state["seed_path"],
                instruction_preset=instruction_preset,
            ),
            system_prompt=(
                f"Du bist Nova Studio Author fuer das Profil '{profile['label']}'. "
                "Erstelle nur das lauffaehige Artefakt-Bundle mit kommentiertem Code. "
                "Didaktische Hinweise werden spaeter separat erzeugt. "
                "Antworte ausschliesslich als JSON. Kein Markdown ausserhalb der JSON-Felder."
            ),
        )

    def _consume_author_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            bundle = self._normalize_bundle(self._parse_json_response(raw_text, schema_name="bundle"), state["language"], plan)
            state["trace"].append(
                {
                    "agent": "Autor",
                    "stage": "author",
                    "status": "completed",
                    "model": model,
                    "summary": self._agent_summary(
                        f"{len(bundle['files'])} Datei(en) erzeugt | Hauptdatei: {bundle['main_file']}",
                        instruction_preset,
                    ),
                }
            )
            state["working_bundle"] = bundle
            return self._run_working_bundle(session, state)
        except Exception:
            return self._issue_json_repair_step(
                state,
                phase="author_json_repair",
                status="Autorenantwort wird in valides JSON ueberfuehrt...",
                raw_text=raw_text,
            )

    def _consume_author_repair_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            bundle = self._normalize_bundle(self._parse_json_response(raw_text, schema_name="bundle"), state["language"], plan)
            state["trace"].append(
                {
                    "agent": "Autor",
                    "stage": "author",
                    "status": "completed",
                    "model": model,
                    "summary": self._agent_summary(
                        f"{len(bundle['files'])} Datei(en) erzeugt | Hauptdatei: {bundle['main_file']}",
                        instruction_preset,
                    ),
                }
            )
            state["working_bundle"] = bundle
            return self._run_working_bundle(session, state)
        except Exception:
            return self._issue_author_code_step(state)

    def _issue_author_code_step(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        plan = self._state_plan(state)
        instruction_preset = self._instruction_preset_from_state(state)
        return self._inference_step(
            state,
            phase="author_code",
            status="Autor wechselt auf Code-Fallback...",
            prompt=self._author_code_prompt(
                state["prompt"],
                plan,
                profile,
                seed_code=state["seed_code"],
                seed_path=state["seed_path"],
                instruction_preset=instruction_preset,
            ),
            system_prompt=(
                f"Du bist Nova Studio Author fuer das Profil '{profile['label']}'. "
                "Erzeuge nur den Inhalt der Hauptdatei als kompakten, lauffaehigen Code. "
                "Antworte nur mit einem einzelnen Markdown-Codeblock."
            ),
        )

    def _consume_author_code_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        try:
            code_text = self._parse_code_response(raw_text, language_hint=plan["language"])
        except Exception:
            return self._issue_code_repair_step(
                state,
                phase="author_code_repair",
                status="Autorenantwort wird zu einem einzelnen Codeblock normalisiert...",
                raw_text=raw_text,
            )
        return self._accept_author_code(session, state, code_text, model)

    def _consume_author_code_repair_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        code_text = self._parse_code_response(raw_text, language_hint=plan["language"])
        return self._accept_author_code(session, state, code_text, model)

    def _accept_author_code(self, session: Any, state: dict[str, Any], code_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        instruction_preset = self._instruction_preset_from_state(state)
        bundle = self._normalize_bundle(
            {
                "title": plan["title"],
                "summary": plan.get("learning_goal") or plan.get("execution_goal") or state["prompt"],
                "language": plan["language"],
                "main_file": plan["main_file"],
                "stdin": "",
                "files": [{"path": plan["main_file"], "content": code_text}],
            },
            state["language"],
            plan,
        )
        state["trace"].append(
            {
                "agent": "Autor",
                "stage": "author",
                "status": "warning",
                "model": model,
                "summary": self._agent_summary(
                    f"JSON-Bundle ungueltig, Hauptdatei per Code-Fallback erzeugt | Hauptdatei: {bundle['main_file']}",
                    instruction_preset,
                ),
            }
        )
        state["working_bundle"] = bundle
        return self._run_working_bundle(session, state)

    def _run_working_bundle(self, session: Any, state: dict[str, Any]) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        run_result = self.runner.run_bundle(
            session,
            {
                "language": bundle["language"],
                "main_file": bundle["main_file"],
                "stdin": bundle.get("stdin") or "",
                "files": bundle["files"],
            },
        )
        attempt = int(state.get("runs_used") or 0) + 1
        state["runs_used"] = attempt
        if run_result["returncode"] == 0 and self._requires_visible_output(state, bundle, run_result):
            if not str(run_result.get("stdout") or "").strip() and not str(run_result.get("stderr") or "").strip():
                run_result = dict(run_result)
                run_result["returncode"] = 1
                run_result["stderr"] = (
                    "Das Programm beendet sich ohne sichtbare Ausgabe. "
                    "Fuer Unterrichtsbeispiele muss beim Direktlauf mindestens ein sichtbares Ergebnis erscheinen."
                )
        state["run_result"] = dict(run_result)
        state["trace"].append(
            {
                "agent": "Pruefer",
                "stage": "run",
                "status": "completed" if run_result["returncode"] == 0 else "failed",
                "attempt": attempt,
                "summary": f"Returncode {run_result['returncode']} | Dauer {run_result['duration_ms']} ms",
            }
        )
        if run_result["returncode"] == 0:
            state["successful"] = True
            return self._issue_pedagogy_step(state)
        state["successful"] = False
        if attempt > int(state.get("attempt_limit") or 1):
            return self._issue_pedagogy_step(state)
        return self._issue_debugger_step(state)

    def _issue_debugger_step(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        plan = self._state_plan(state)
        bundle = self._state_bundle(state)
        run_result = self._state_run_result(state, bundle["language"])
        next_attempt = int(state.get("runs_used") or 0) + 1
        instruction_preset = self._instruction_preset_from_state(state)
        return self._inference_step(
            state,
            phase="repair",
            status="Debugger repariert den fehlgeschlagenen Versuch...",
            prompt=self._repair_prompt(
                state["prompt"],
                plan,
                profile,
                bundle,
                run_result,
                next_attempt,
                instruction_preset=instruction_preset,
            ),
            system_prompt=(
                f"Du bist Nova Studio Debugger fuer das Profil '{profile['label']}'. "
                "Repariere lauffaehigen Unterrichtscode anhand der Fehlermeldung. "
                "Antworte ausschliesslich als vollstaendiges JSON-Bundle."
            ),
        )

    def _consume_debugger_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        bundle = self._state_bundle(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            repaired_bundle = self._normalize_bundle(
                self._parse_json_response(raw_text, schema_name="bundle"),
                bundle["language"],
                plan,
                previous=bundle,
            )
            state["trace"].append(
                {
                    "agent": "Debugger",
                    "stage": "repair",
                    "status": "completed",
                    "attempt": int(state.get("runs_used") or 0) + 1,
                    "model": model,
                    "summary": self._agent_summary(
                        "Code und Material auf Basis der Laufdiagnose ueberarbeitet.",
                        instruction_preset,
                    ),
                }
            )
            state["working_bundle"] = repaired_bundle
            return self._run_working_bundle(session, state)
        except Exception:
            return self._issue_json_repair_step(
                state,
                phase="repair_json_repair",
                status="Debuggerantwort wird in valides JSON ueberfuehrt...",
                raw_text=raw_text,
            )

    def _consume_debugger_repair_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        plan = self._state_plan(state)
        bundle = self._state_bundle(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            repaired_bundle = self._normalize_bundle(
                self._parse_json_response(raw_text, schema_name="bundle"),
                bundle["language"],
                plan,
                previous=bundle,
            )
            state["trace"].append(
                {
                    "agent": "Debugger",
                    "stage": "repair",
                    "status": "completed",
                    "attempt": int(state.get("runs_used") or 0) + 1,
                    "model": model,
                    "summary": self._agent_summary(
                        "Code und Material auf Basis der Laufdiagnose ueberarbeitet.",
                        instruction_preset,
                    ),
                }
            )
            state["working_bundle"] = repaired_bundle
            return self._run_working_bundle(session, state)
        except Exception:
            return self._issue_debugger_code_step(state)

    def _issue_debugger_code_step(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        plan = self._state_plan(state)
        bundle = self._state_bundle(state)
        run_result = self._state_run_result(state, bundle["language"])
        next_attempt = int(state.get("runs_used") or 0) + 1
        instruction_preset = self._instruction_preset_from_state(state)
        return self._inference_step(
            state,
            phase="repair_code",
            status="Debugger wechselt auf Hauptdatei-Fallback...",
            prompt=self._repair_code_prompt(
                state["prompt"],
                plan,
                profile,
                bundle,
                run_result,
                next_attempt,
                instruction_preset=instruction_preset,
            ),
            system_prompt=(
                f"Du bist Nova Studio Debugger fuer das Profil '{profile['label']}'. "
                "Repariere nur den Inhalt der Hauptdatei und antworte mit einem einzelnen Markdown-Codeblock."
            ),
        )

    def _consume_debugger_code_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        try:
            repaired_code = self._parse_code_response(raw_text, language_hint=bundle["language"])
        except Exception:
            return self._issue_code_repair_step(
                state,
                phase="repair_code_repair",
                status="Debuggerantwort wird zu einem einzelnen Codeblock normalisiert...",
                raw_text=raw_text,
            )
        return self._accept_debugger_code(session, state, repaired_code, model)

    def _consume_debugger_code_repair_response(self, session: Any, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        repaired_code = self._parse_code_response(raw_text, language_hint=bundle["language"])
        return self._accept_debugger_code(session, state, repaired_code, model)

    def _accept_debugger_code(self, session: Any, state: dict[str, Any], repaired_code: str, model: str) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        plan = self._state_plan(state)
        instruction_preset = self._instruction_preset_from_state(state)
        repaired_bundle = self._replace_main_file(bundle, repaired_code, plan)
        state["trace"].append(
            {
                "agent": "Debugger",
                "stage": "repair",
                "status": "warning",
                "attempt": int(state.get("runs_used") or 0) + 1,
                "model": model,
                "summary": self._agent_summary(
                    "JSON-Bundle ungueltig, Hauptdatei per Code-Fallback repariert.",
                    instruction_preset,
                ),
            }
        )
        state["working_bundle"] = repaired_bundle
        return self._run_working_bundle(session, state)

    def _issue_pedagogy_step(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_from_state(state)
        bundle = self._state_bundle(state)
        run_result = self._state_run_result(state, bundle["language"])
        instruction_preset = self._instruction_preset_from_state(state)
        pedagogy_input = {
            "title": bundle["title"],
            "summary": bundle["summary"],
            "language": bundle["language"],
            "main_file": bundle["main_file"],
            "code": self._main_file_content(bundle["files"], bundle["main_file"]),
            "prompt": state["prompt"],
            "profile": profile,
        }
        return self._inference_step(
            state,
            phase="pedagogy",
            status="Didaktik-Agent bereitet Hinweise und Schueler-Material auf...",
            prompt=self._pedagogy_prompt(pedagogy_input, profile, run_result, instruction_preset=instruction_preset),
            system_prompt=(
                f"Du bist Nova Studio Didaktik fuer das Profil '{profile['label']}'. "
                "Formuliere knappe, schulgeeignete Lehrkraft-Hinweise und Schueler-Materialien. "
                "Antworte ausschliesslich als JSON."
            ),
        )

    def _consume_pedagogy_response(self, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            payload = self._parse_json_response(raw_text, schema_name="pedagogy")
            teacher_notes = str(payload.get("teacher_notes_markdown") or bundle.get("teacher_notes_markdown") or "").strip()
            student_material = str(payload.get("student_material_markdown") or bundle.get("student_material_markdown") or "").strip()
            state["trace"].append(
                {
                    "agent": "Didaktik",
                    "stage": "pedagogy",
                    "status": "completed",
                    "model": model,
                    "summary": self._agent_summary(
                        "Lehrkraft-Hinweise und Schueler-Material wurden aufbereitet.",
                        instruction_preset,
                    ),
                }
            )
            return self._finalize_generation(state, teacher_notes=teacher_notes, student_material=student_material)
        except Exception:
            return self._issue_json_repair_step(
                state,
                phase="pedagogy_json_repair",
                status="Didaktikantwort wird in valides JSON ueberfuehrt...",
                raw_text=raw_text,
            )

    def _consume_pedagogy_repair_response(self, state: dict[str, Any], raw_text: str, model: str) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        instruction_preset = self._instruction_preset_from_state(state)
        try:
            payload = self._parse_json_response(raw_text, schema_name="pedagogy")
            teacher_notes = str(payload.get("teacher_notes_markdown") or bundle.get("teacher_notes_markdown") or "").strip()
            student_material = str(payload.get("student_material_markdown") or bundle.get("student_material_markdown") or "").strip()
            state["trace"].append(
                {
                    "agent": "Didaktik",
                    "stage": "pedagogy",
                    "status": "completed",
                    "model": model,
                    "summary": self._agent_summary(
                        "Lehrkraft-Hinweise und Schueler-Material wurden aufbereitet.",
                        instruction_preset,
                    ),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            teacher_notes, student_material = self._fallback_pedagogy(
                {
                    "title": bundle["title"],
                    "summary": bundle["summary"],
                    "language": bundle["language"],
                    "main_file": bundle["main_file"],
                    "code": self._main_file_content(bundle["files"], bundle["main_file"]),
                    "prompt": state["prompt"],
                    "profile": self._profile_from_state(state),
                },
                self._profile_from_state(state),
                self._state_run_result(state, bundle["language"]),
            )
            state["trace"].append(
                {
                    "agent": "Didaktik",
                    "stage": "pedagogy",
                    "status": "warning",
                    "summary": self._agent_summary(
                        f"Didaktikantwort ungueltig, kompakter Regel-Fallback verwendet: {exc}",
                        instruction_preset,
                    ),
                }
            )
        return self._finalize_generation(state, teacher_notes=teacher_notes, student_material=student_material)

    def _finalize_generation(self, state: dict[str, Any], *, teacher_notes: str, student_material: str) -> dict[str, Any]:
        bundle = self._state_bundle(state)
        run_result = self._state_run_result(state, bundle["language"])
        instruction_preset = self._instruction_preset_from_state(state)
        return self._bundle_response(
            bundle,
            run_result,
            list(state.get("trace") or []),
            passed=bool(state.get("successful")),
            attempt_limit=int(state.get("attempt_limit") or 1),
            teacher_notes=teacher_notes,
            student_material=student_material,
            profile=self._profile_from_state(state),
            instruction_preset=instruction_preset,
        )

    def _replace_main_file(self, bundle: dict[str, Any], repaired_code: str, plan: dict[str, Any]) -> dict[str, Any]:
        updated_files: list[dict[str, str]] = []
        replaced = False
        for item in bundle["files"]:
            if str(item.get("path") or "") == bundle["main_file"]:
                updated_files.append({"path": bundle["main_file"], "content": repaired_code})
                replaced = True
            else:
                updated_files.append(dict(item))
        if not replaced:
            updated_files.insert(0, {"path": bundle["main_file"], "content": repaired_code})
        return self._normalize_bundle(
            {
                "title": bundle["title"],
                "summary": bundle["summary"],
                "language": bundle["language"],
                "main_file": bundle["main_file"],
                "stdin": bundle.get("stdin") or "",
                "teacher_notes_markdown": bundle.get("teacher_notes_markdown") or "",
                "student_material_markdown": bundle.get("student_material_markdown") or "",
                "files": updated_files,
            },
            bundle["language"],
            plan,
            previous=bundle,
        )

    def _fallback_pedagogy(
        self,
        payload: dict[str, Any],
        profile: dict[str, str],
        run_result: dict[str, Any],
    ) -> tuple[str, str]:
        title = self._clean_text(payload.get("title")) or "Unterrichtsbeispiel"
        summary = self._clean_text(payload.get("summary")) or self._clean_text(payload.get("prompt")) or "Kompaktes Unterrichtsmaterial."
        language = self._normalize_language(str(payload.get("language") or "python"))
        language_label = SUPPORTED_LANGUAGES.get(language, language.title())
        returncode = int(run_result.get("returncode") or 0)
        stderr_line = self._clean_text(str(run_result.get("stderr") or "").splitlines()[0] if str(run_result.get("stderr") or "").strip() else "")
        teacher_lines = [
            f"- **Lernziel:** {summary}",
            f"- **Profil:** {profile['label']} mit {language_label}-Beispiel.",
            f"- **Einsatz:** {title} schrittweise lesen und dann gemeinsam ausfuehren.",
            "- **Moderation:** Vor der Ausfuehrung zuerst Ausgabe oder Verhalten vorhersagen lassen.",
        ]
        if returncode == 0:
            teacher_lines.append("- **Hinweis:** Der aktuelle Code laeuft fehlerfrei im Schulserver.")
        elif stderr_line:
            teacher_lines.append(f"- **Diagnose:** Letzter Lauf hatte noch einen Fehlerhinweis: `{stderr_line}`")
        student_lines = [
            f"- **Thema:** {title}",
            "- **Arbeitsauftrag:** Fuehre das Beispiel aus und beschreibe, welche Schritte im Programm nacheinander passieren.",
            "- **Achte auf:** Ausgabe, Variablenwerte und den Datenfluss zwischen Eingabe und Ausgabe.",
            "- **Reflexion:** Welche Zeile ist fuer das sichtbare Ergebnis am wichtigsten und warum?",
        ]
        return "\n".join(teacher_lines).strip(), "\n".join(student_lines).strip()

    def _bundle_prompt_snapshot(self, bundle: dict[str, Any], *, code_limit: int = 4000) -> dict[str, Any]:
        return {
            "title": str(bundle.get("title") or "").strip(),
            "summary": str(bundle.get("summary") or "").strip(),
            "language": str(bundle.get("language") or "").strip(),
            "main_file": str(bundle.get("main_file") or "").strip(),
            "stdin": str(bundle.get("stdin") or "")[:600],
            "main_code": self._main_file_content(bundle.get("files") or [], str(bundle.get("main_file") or ""))[:code_limit],
            "extra_files": [
                str(item.get("path") or "").strip()
                for item in list(bundle.get("files") or [])
                if str(item.get("path") or "").strip() and str(item.get("path") or "").strip() != str(bundle.get("main_file") or "").strip()
            ][:4],
        }

    @staticmethod
    def _run_result_snapshot(run_result: dict[str, Any], *, text_limit: int = 1500) -> dict[str, Any]:
        return {
            "returncode": run_result.get("returncode"),
            "stdout": str(run_result.get("stdout") or "")[:text_limit],
            "stderr": str(run_result.get("stderr") or "")[:text_limit],
            "command": run_result.get("command"),
        }

    def _pedagogy_payload_snapshot(self, payload: dict[str, Any], *, prompt_limit: int = 2400, code_limit: int = 5000) -> dict[str, Any]:
        return {
            "title": str(payload.get("title") or "").strip(),
            "summary": str(payload.get("summary") or "").strip(),
            "language": str(payload.get("language") or "").strip(),
            "main_file": str(payload.get("main_file") or "").strip(),
            "prompt": str(payload.get("prompt") or "")[:prompt_limit],
            "profile": {
                "key": str((payload.get("profile") or {}).get("key") or "").strip(),
                "label": str((payload.get("profile") or {}).get("label") or "").strip(),
            },
            "main_code": str(payload.get("code") or "")[:code_limit],
        }

    def _bundle_response(
        self,
        bundle: dict[str, Any],
        run_result: dict[str, Any],
        trace: list[dict[str, Any]],
        *,
        passed: bool,
        attempt_limit: int,
        teacher_notes: str,
        student_material: str,
        profile: dict[str, str],
        instruction_preset: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        main_code = self._main_file_content(bundle["files"], bundle["main_file"])
        return {
            "title": bundle["title"],
            "summary": bundle["summary"],
            "profile": dict(profile),
            "instruction_preset": dict(instruction_preset) if isinstance(instruction_preset, dict) else None,
            "instruction_preset_key": str((instruction_preset or {}).get("key") or ""),
            "language": bundle["language"],
            "main_file": bundle["main_file"],
            "stdin": bundle.get("stdin") or "",
            "files": bundle["files"],
            "code": main_code,
            "teacher_notes_markdown": teacher_notes,
            "student_material_markdown": student_material,
            "passed": passed,
            "attempt_limit": attempt_limit,
            "attempts_used": len([item for item in trace if item.get("stage") == "run"]),
            "agent_trace": trace,
            "run": run_result,
        }

    def _json_completion(self, prompt: str, *, system_prompt: str, schema_name: str | None = None) -> tuple[dict[str, Any], str]:
        if self.ai_service is None:
            _ = system_prompt
            return self._parse_json_response(prompt, schema_name=schema_name), ""
        phase = "author"
        schema = str(schema_name or "").strip().lower()
        if schema == "plan":
            phase = "plan"
        elif schema == "pedagogy":
            phase = "pedagogy"
        raw_text, model = self.ai_service.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
            generation_options=self._generation_options_for_phase(phase),
            timeout_seconds=self._timeout_seconds_for_phase(phase),
        )
        return self._parse_json_response(raw_text, schema_name=schema_name), model

    def _code_completion(self, prompt: str, *, system_prompt: str, language_hint: str | None = None) -> tuple[str, str]:
        if self.ai_service is None:
            _ = system_prompt
            return self._parse_code_response(prompt, language_hint=language_hint), ""
        raw_text, model = self.ai_service.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            generation_options=self._generation_options_for_phase("author_code"),
            timeout_seconds=self._timeout_seconds_for_phase("author_code"),
        )
        return self._parse_code_response(raw_text, language_hint=language_hint), model

    @staticmethod
    def _normalize_language(language: str) -> str:
        normalized = str(language or "").strip().lower()
        return normalized if normalized in SUPPORTED_LANGUAGES else "python"

    @staticmethod
    def _normalize_profile(profile: str) -> dict[str, str]:
        normalized = str(profile or "").strip().lower()
        return dict(PROFILE_BY_KEY.get(normalized) or PROFILE_BY_KEY["example-code"])

    @staticmethod
    def _normalize_plan(payload: dict[str, Any], fallback_language: str) -> dict[str, str]:
        title = TeacherMaterialStudioService._clean_text(payload.get("title")) or "Unterrichtsmaterial"
        language = str(payload.get("language") or fallback_language).strip().lower() or fallback_language
        if language not in SUPPORTED_LANGUAGES:
            language = fallback_language
        main_file = str(payload.get("main_file") or DEFAULT_MAIN_FILES[language]).strip() or DEFAULT_MAIN_FILES[language]
        return {
            "title": title,
            "language": language,
            "main_file": main_file,
            "learning_goal": TeacherMaterialStudioService._clean_text(payload.get("learning_goal")),
            "execution_goal": TeacherMaterialStudioService._clean_text(payload.get("execution_goal")),
            "success_criteria": TeacherMaterialStudioService._clean_text(payload.get("success_criteria")),
        }

    def _normalize_bundle(
        self,
        payload: dict[str, Any],
        fallback_language: str,
        plan: dict[str, Any],
        *,
        previous: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        language = self._normalize_language(str(payload.get("language") or fallback_language))
        main_file = str(payload.get("main_file") or plan.get("main_file") or DEFAULT_MAIN_FILES[language]).strip() or DEFAULT_MAIN_FILES[language]
        raw_files = payload.get("files")
        files: list[dict[str, str]] = []
        if isinstance(raw_files, dict):
            files = [{"path": str(path), "content": self._stringify_text(content)} for path, content in raw_files.items()]
        elif isinstance(raw_files, list):
            for item in raw_files:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("path") or "").strip()
                if not path:
                    continue
                files.append({"path": path, "content": self._stringify_text(item.get("content"))})
        if not files and previous:
            files = [dict(item) for item in previous.get("files", [])]
        if not files:
            files = [{"path": main_file, "content": self._stringify_text(payload.get("code"))}]
        if not any(str(item.get("path") or "") == main_file for item in files):
            files.insert(0, {"path": main_file, "content": self._stringify_text(payload.get("code"))})
        normalized_files: list[dict[str, str]] = []
        seen_paths: set[str] = set()
        for item in files:
            path = self._sanitize_relative_path(str(item.get("path") or "").strip() or main_file)
            if path in seen_paths:
                continue
            seen_paths.add(path)
            normalized_files.append({"path": path, "content": self._stringify_text(item.get("content"))})
        return {
            "title": self._clean_text(payload.get("title") or plan.get("title")) or "Unterrichtsmaterial",
            "summary": self._clean_text(payload.get("summary") or plan.get("learning_goal")),
            "language": language,
            "main_file": self._sanitize_relative_path(main_file),
            "stdin": self._clean_text(payload.get("stdin") or (previous or {}).get("stdin")),
            "teacher_notes_markdown": self._clean_text(payload.get("teacher_notes_markdown") or (previous or {}).get("teacher_notes_markdown")),
            "student_material_markdown": self._clean_text(payload.get("student_material_markdown") or (previous or {}).get("student_material_markdown")),
            "files": normalized_files,
        }

    @staticmethod
    def _main_file_content(files: list[dict[str, str]], main_file: str) -> str:
        for item in files:
            if str(item.get("path") or "") == main_file:
                return str(item.get("content") or "")
        return str(files[0].get("content") or "") if files else ""

    @staticmethod
    def _sanitize_relative_path(path_text: str) -> str:
        normalized = str(path_text or "").replace("\\", "/").strip().strip("/")
        if not normalized:
            raise ValueError("Leerer Dateipfad im Material-Studio.")
        parts = [part for part in normalized.split("/") if part not in {"", "."}]
        if any(part == ".." for part in parts):
            raise ValueError("Ungueltiger relativer Dateipfad im Material-Studio.")
        return "/".join(parts)

    @staticmethod
    def _stringify_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            parts = [TeacherMaterialStudioService._stringify_text(item) for item in value]
            return "\n".join(part for part in parts if part)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    @staticmethod
    def _clean_text(value: Any) -> str:
        return TeacherMaterialStudioService._stringify_text(value).strip()

    @staticmethod
    def _has_meaningful_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, dict, set)):
            return bool(value)
        return True

    @classmethod
    def _structured_json_payload(cls, text: str, *, schema_name: str | None) -> dict[str, Any]:
        payload = cls._extract_json_object(text)
        if not schema_name:
            return payload
        return cls._validate_schema_payload(payload, schema_name)

    @classmethod
    def _validate_schema_payload(cls, payload: dict[str, Any], schema_name: str) -> dict[str, Any]:
        schema = str(schema_name or "").strip().lower()
        if schema == "plan":
            return cls._canonicalize_plan_payload(payload)
        if schema == "bundle":
            return cls._canonicalize_bundle_payload(payload)
        if schema == "pedagogy":
            return cls._canonicalize_pedagogy_payload(payload)
        return payload

    @classmethod
    def _candidate_objects(cls, payload: Any) -> list[dict[str, Any]]:
        queue: list[Any] = [payload]
        objects: list[dict[str, Any]] = []
        seen: set[int] = set()
        while queue:
            current = queue.pop(0)
            if not isinstance(current, dict):
                continue
            marker = id(current)
            if marker in seen:
                continue
            seen.add(marker)
            objects.append(current)
            for key in STRUCTURED_PAYLOAD_WRAPPERS:
                nested = current.get(key)
                if isinstance(nested, dict):
                    queue.append(nested)
        return objects or ([payload] if isinstance(payload, dict) else [])

    @staticmethod
    def _lookup_path(payload: dict[str, Any], dotted_key: str) -> Any:
        current: Any = payload
        for part in str(dotted_key or "").split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current.get(part)
        return current

    @classmethod
    def _lookup_alias(cls, objects: list[dict[str, Any]], *aliases: str) -> Any:
        for alias in aliases:
            for payload in objects:
                value = cls._lookup_path(payload, alias)
                if cls._has_meaningful_value(value):
                    return value
        return None

    @staticmethod
    def _looks_like_file_path(value: str) -> bool:
        candidate = str(value or "").strip()
        if not candidate:
            return False
        return "/" in candidate or "\\" in candidate or "." in candidate or candidate.lower() in {"dockerfile", "makefile"}

    @classmethod
    def _normalize_files_value(cls, value: Any) -> list[dict[str, str]]:
        if isinstance(value, list):
            files: list[dict[str, str]] = []
            for item in value:
                files.extend(cls._normalize_files_value(item))
            return files
        if isinstance(value, dict):
            objects = cls._candidate_objects(value)
            path = cls._clean_text(
                cls._lookup_alias(objects, "path", "file", "file_path", "filename", "name", "main_file", "mainFile")
            )
            content_value = cls._lookup_alias(objects, "content", "code", "source", "text", "body", "main_file_content", "mainFileContent")
            if path and cls._has_meaningful_value(content_value):
                return [{"path": path, "content": cls._stringify_text(content_value)}]
            for key in ("files", "artifacts", "output_files", "bundle", "artifact"):
                nested = value.get(key)
                if cls._has_meaningful_value(nested):
                    nested_files = cls._normalize_files_value(nested)
                    if nested_files:
                        return nested_files
            mapped: list[dict[str, str]] = []
            for key, raw in value.items():
                if not isinstance(key, str) or not cls._looks_like_file_path(key):
                    continue
                if isinstance(raw, dict):
                    raw_content = raw.get("content", raw.get("code", raw.get("source", raw)))
                else:
                    raw_content = raw
                mapped.append({"path": key.strip(), "content": cls._stringify_text(raw_content)})
            return mapped
        return []

    @classmethod
    def _canonicalize_plan_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        objects = cls._candidate_objects(payload)
        normalized = {
            "title": cls._clean_text(cls._lookup_alias(objects, "title", "name", "topic", "headline")),
            "language": cls._clean_text(cls._lookup_alias(objects, "language", "lang", "runtime")).lower(),
            "main_file": cls._clean_text(cls._lookup_alias(objects, "main_file", "mainFile", "filename", "file", "path", "entrypoint", "entry_point")),
            "learning_goal": cls._clean_text(cls._lookup_alias(objects, "learning_goal", "learningGoal", "goal", "objective", "learning_objective")),
            "execution_goal": cls._clean_text(cls._lookup_alias(objects, "execution_goal", "executionGoal", "output_goal", "observable_goal")),
            "success_criteria": cls._clean_text(cls._lookup_alias(objects, "success_criteria", "successCriteria", "acceptance_criteria", "done_definition")),
        }
        if not any(cls._has_meaningful_value(value) for value in normalized.values()):
            raise ValueError("Plan-Schema enthielt keine verwertbaren Felder.")
        return normalized

    @classmethod
    def _canonicalize_bundle_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        objects = cls._candidate_objects(payload)
        language = cls._clean_text(cls._lookup_alias(objects, "language", "lang", "runtime")).lower()
        files = cls._normalize_files_value(cls._lookup_alias(objects, "files", "artifacts", "output_files", "bundle", "artifact"))
        main_file = cls._clean_text(cls._lookup_alias(objects, "main_file", "mainFile", "filename", "file", "path", "entrypoint", "entry_point"))
        code_value = cls._lookup_alias(objects, "code", "source", "content", "main_file_content", "mainFileContent")
        if not files and cls._has_meaningful_value(code_value):
            fallback_main_file = main_file or DEFAULT_MAIN_FILES.get(language or "python", "main.py")
            files = [{"path": fallback_main_file, "content": cls._stringify_text(code_value)}]
            main_file = main_file or fallback_main_file
        if not main_file and files:
            main_file = str(files[0].get("path") or "").strip()
        normalized = {
            "title": cls._clean_text(cls._lookup_alias(objects, "title", "name", "headline")),
            "summary": cls._clean_text(cls._lookup_alias(objects, "summary", "description", "overview", "abstract")),
            "language": language,
            "main_file": main_file,
            "stdin": cls._clean_text(cls._lookup_alias(objects, "stdin", "input", "sample_input", "sampleInput")),
            "teacher_notes_markdown": cls._clean_text(
                cls._lookup_alias(
                    objects,
                    "teacher_notes_markdown",
                    "teacherNotesMarkdown",
                    "teacher_notes",
                    "teacherNotes",
                    "teacher_material",
                    "teacherMaterial",
                )
            ),
            "student_material_markdown": cls._clean_text(
                cls._lookup_alias(
                    objects,
                    "student_material_markdown",
                    "studentMaterialMarkdown",
                    "student_material",
                    "studentMaterial",
                    "worksheet_markdown",
                    "worksheetMarkdown",
                )
            ),
            "files": files,
        }
        if not cls._has_meaningful_value(normalized["files"]):
            raise ValueError("Bundle-Schema enthielt keine ausfuehrbaren Dateien.")
        return normalized

    @classmethod
    def _canonicalize_pedagogy_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        objects = cls._candidate_objects(payload)
        normalized = {
            "teacher_notes_markdown": cls._clean_text(
                cls._lookup_alias(
                    objects,
                    "teacher_notes_markdown",
                    "teacherNotesMarkdown",
                    "teacher_notes",
                    "teacherNotes",
                    "notes",
                )
            ),
            "student_material_markdown": cls._clean_text(
                cls._lookup_alias(
                    objects,
                    "student_material_markdown",
                    "studentMaterialMarkdown",
                    "student_material",
                    "studentMaterial",
                    "worksheet",
                    "worksheet_markdown",
                )
            ),
        }
        if not any(cls._has_meaningful_value(value) for value in normalized.values()):
            raise ValueError("Didaktik-Schema enthielt keine verwertbaren Felder.")
        return normalized

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        raw = str(text or "").strip()
        parsed_objects: list[dict[str, Any]] = []
        first_error: Exception | None = None
        for candidate in TeacherMaterialStudioService._json_candidates(raw):
            try:
                parsed = TeacherMaterialStudioService._parse_json_candidate(candidate)
            except Exception as exc:
                if first_error is None:
                    first_error = exc
                continue
            if isinstance(parsed, dict):
                parsed_objects.append(parsed)
        if parsed_objects:
            merged: dict[str, Any] = {}
            for item in parsed_objects:
                merged.update(item)
            return merged
        message = f"Modellantwort lieferte kein gueltiges JSON-Bundle.\n\nAntwort:\n{raw[:1200]}"
        if first_error is not None:
            raise ValueError(message) from first_error
        raise ValueError(message)

    @staticmethod
    def _parse_json_candidate(candidate: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for variant in TeacherMaterialStudioService._json_candidate_variants(candidate):
            try:
                parsed = json.loads(variant)
            except Exception as json_exc:
                last_error = json_exc
                try:
                    parsed = ast.literal_eval(TeacherMaterialStudioService._jsonish_to_python_literal(variant))
                except Exception:
                    continue
            if isinstance(parsed, dict):
                return parsed
        if last_error is not None:
            raise last_error
        raise ValueError("JSON-Kandidat ist kein Objekt.")

    @staticmethod
    def _json_candidates(raw: str) -> list[str]:
        candidates: list[str] = []
        for pattern in (
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
        ):
            for match in re.finditer(pattern, raw, re.IGNORECASE):
                block = str(match.group(1) or "").strip()
                if not block:
                    continue
                candidates.append(block)
                candidates.extend(TeacherMaterialStudioService._scan_top_level_json_objects(block))
        candidates.extend(TeacherMaterialStudioService._scan_top_level_json_objects(raw))
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            candidates.append(raw[start : end + 1])
        unique: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = candidate.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique

    @staticmethod
    def _json_candidate_variants(text: str) -> list[str]:
        base = str(text or "").replace("\ufeff", "").translate(SMART_QUOTES_TRANSLATION).strip()
        variants = [base]
        without_comments = TeacherMaterialStudioService._strip_jsonish_comments(base)
        variants.append(without_comments)
        without_trailing_commas = TeacherMaterialStudioService._remove_trailing_commas(without_comments)
        variants.append(without_trailing_commas)
        quoted_keys = TeacherMaterialStudioService._quote_bare_keys(without_trailing_commas)
        variants.append(quoted_keys)
        variants.append(TeacherMaterialStudioService._remove_trailing_commas(quoted_keys))
        unique: list[str] = []
        seen: set[str] = set()
        for item in variants:
            normalized = str(item or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique

    @staticmethod
    def _strip_jsonish_comments(text: str) -> str:
        parts: list[str] = []
        index = 0
        delimiter = ""
        escape = False
        while index < len(text):
            char = text[index]
            next_char = text[index + 1] if index + 1 < len(text) else ""
            if delimiter:
                parts.append(char)
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == delimiter:
                    delimiter = ""
                index += 1
                continue
            if char in {'"', "'"}:
                delimiter = char
                parts.append(char)
                index += 1
                continue
            if char == "/" and next_char == "/":
                index += 2
                while index < len(text) and text[index] not in "\r\n":
                    index += 1
                continue
            if char == "/" and next_char == "*":
                index += 2
                while index + 1 < len(text) and not (text[index] == "*" and text[index + 1] == "/"):
                    index += 1
                index = min(index + 2, len(text))
                continue
            parts.append(char)
            index += 1
        return "".join(parts)

    @staticmethod
    def _remove_trailing_commas(text: str) -> str:
        parts: list[str] = []
        index = 0
        delimiter = ""
        escape = False
        while index < len(text):
            char = text[index]
            if delimiter:
                parts.append(char)
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == delimiter:
                    delimiter = ""
                index += 1
                continue
            if char in {'"', "'"}:
                delimiter = char
                parts.append(char)
                index += 1
                continue
            if char == ",":
                lookahead = index + 1
                while lookahead < len(text) and text[lookahead].isspace():
                    lookahead += 1
                if lookahead < len(text) and text[lookahead] in "}]":
                    index += 1
                    continue
            parts.append(char)
            index += 1
        return "".join(parts)

    @staticmethod
    def _quote_bare_keys(text: str) -> str:
        parts: list[str] = []
        index = 0
        delimiter = ""
        escape = False
        expect_key = False
        while index < len(text):
            char = text[index]
            if delimiter:
                parts.append(char)
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == delimiter:
                    delimiter = ""
                index += 1
                continue
            if char in {'"', "'"}:
                delimiter = char
                expect_key = False
                parts.append(char)
                index += 1
                continue
            if char == "{":
                expect_key = True
                parts.append(char)
                index += 1
                continue
            if char == ",":
                expect_key = True
                parts.append(char)
                index += 1
                continue
            if expect_key and char.isspace():
                parts.append(char)
                index += 1
                continue
            if expect_key and re.match(r"[A-Za-z_]", char):
                end = index + 1
                while end < len(text) and re.match(r"[A-Za-z0-9_-]", text[end]):
                    end += 1
                lookahead = end
                while lookahead < len(text) and text[lookahead].isspace():
                    lookahead += 1
                if lookahead < len(text) and text[lookahead] == ":":
                    parts.append(f'"{text[index:end]}"')
                    index = end
                    expect_key = False
                    continue
            expect_key = False
            parts.append(char)
            index += 1
        return "".join(parts)

    @staticmethod
    def _scan_top_level_json_objects(text: str) -> list[str]:
        objects: list[str] = []
        start_index: int | None = None
        depth = 0
        in_string = False
        escape = False
        for index, char in enumerate(text):
            if in_string:
                if escape:
                    escape = False
                    continue
                if char == "\\":
                    escape = True
                    continue
                if char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                continue
            if char == "{":
                if depth == 0:
                    start_index = index
                depth += 1
                continue
            if char == "}":
                if depth == 0:
                    continue
                depth -= 1
                if depth == 0 and start_index is not None:
                    objects.append(text[start_index : index + 1])
                    start_index = None
        return objects

    @staticmethod
    def _jsonish_to_python_literal(text: str) -> str:
        parts: list[str] = []
        index = 0
        in_string = False
        escape = False
        length = len(text)
        while index < length:
            char = text[index]
            if in_string:
                parts.append(char)
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                index += 1
                continue
            if char == '"':
                in_string = True
                parts.append(char)
                index += 1
                continue
            matched = False
            for source, target in (("true", "True"), ("false", "False"), ("null", "None")):
                if text.startswith(source, index):
                    previous = text[index - 1] if index > 0 else ""
                    following_index = index + len(source)
                    following = text[following_index] if following_index < length else ""
                    if not previous.isalnum() and previous != "_" and not following.isalnum() and following != "_":
                        parts.append(target)
                        index += len(source)
                        matched = True
                        break
            if matched:
                continue
            parts.append(char)
            index += 1
        return "".join(parts)

    @staticmethod
    def _extract_code_block(text: str) -> str:
        raw = str(text or "").strip()
        if not raw:
            return ""
        preferred_opening = re.search(r"```(?:python|javascript|js|cpp|c\+\+|java|rust|html|node)\b", raw, re.IGNORECASE)
        if preferred_opening and preferred_opening.start() > 0:
            nested_preferred = TeacherMaterialStudioService._extract_code_block(raw[preferred_opening.start() :])
            if nested_preferred.strip():
                return nested_preferred.strip()
        pattern = re.compile(r"```(?P<lang>[a-zA-Z0-9_+#.-]+)?\s*(?P<body>[\s\S]*?)```")
        candidates: list[tuple[int, int, str]] = []
        for match in pattern.finditer(raw):
            language = str(match.group("lang") or "").strip().lower()
            body = str(match.group("body") or "").strip()
            if not body:
                continue
            if "```" in body:
                nested = TeacherMaterialStudioService._extract_code_block(body)
                if nested.strip():
                    body = nested.strip()
                    language = language or "nested"
            score = len(body)
            if language and language not in {"text", "txt", "plain"}:
                score += 1000
            if re.search(r"\b(def |class |print\(|console\.log|#include|fn main|public static void main|import )", body):
                score += 250
            candidates.append((score, len(body), body))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][2].strip()
        opening_markers = list(re.finditer(r"```(?:[a-zA-Z0-9_+#.-]+)?\s*", raw))
        if opening_markers:
            trailing = raw[opening_markers[-1].end() :].strip()
            if trailing:
                return trailing
        return raw.strip()

    @staticmethod
    def _looks_like_instructional_prose(text: str) -> bool:
        lines = [line.strip().lower() for line in str(text or "").splitlines() if line.strip()]
        if not lines:
            return False
        prose_markers = sum(
            1
            for line in lines[:12]
            if (
                line.startswith(("du hast", "erstelle ", "thema:", "nutze diese", "arbeitsblatt", "lehrkraft", "schueler"))
                or "anforderung" in line
                or "das ist korrekt" in line
                or "markdown-codeblock" in line
                or "kurze reflexionsfrage" in line
                or "musterloesung" in line
            )
        )
        sentence_lines = sum(1 for line in lines[:12] if line.endswith((".", "!", "?")))
        code_markers = bool(
            re.search(
                r"\b(def |class |print\(|if __name__|console\.log|#include|int main\s*\(|public static void main|fn main\s*\(|<!doctype html|<html\b)",
                str(text or ""),
                re.IGNORECASE,
            )
        )
        return prose_markers >= 2 and sentence_lines >= 2 and not code_markers

    @classmethod
    def _looks_like_source_code(cls, text: str, *, language_hint: str | None = None) -> bool:
        candidate = str(text or "").strip()
        if not candidate:
            return False
        language = cls._normalize_language(str(language_hint or "python"))
        if cls._looks_like_instructional_prose(candidate):
            return False
        if language == "python":
            try:
                ast.parse(candidate)
                return True
            except Exception:
                return bool(re.search(r"(^|\n)\s*(def |class |if |for |while |try:|print\(|from |import |[A-Za-z_][A-Za-z0-9_]*\s*=)", candidate))
        if language in {"javascript", "node"}:
            return bool(re.search(r"\b(const|let|var|function|console\.log|require\(|process\.argv|if\s*\(|for\s*\(|while\s*\(|=>)\b", candidate))
        if language == "cpp":
            return bool(re.search(r"#include|std::|int\s+main\s*\(|cout|cin|using\s+namespace", candidate))
        if language == "java":
            return bool(re.search(r"\bclass\s+\w+|public\s+static\s+void\s+main|System\.out\.println|import\s+java\.", candidate))
        if language == "rust":
            return bool(re.search(r"\bfn\s+main\s*\(|println!|let\s+mut|use\s+std::|match\s+", candidate))
        if language == "html":
            return bool(re.search(r"<!doctype html>|<html\b|<head\b|<body\b|<main\b|<section\b|<div\b|<p\b|<h1\b", candidate, re.IGNORECASE))
        return bool(re.search(r"[{}();=<>\[\]]", candidate))

    @staticmethod
    def _json_repair_prompt(raw_text: str) -> str:
        return "\n".join(
            [
                "Formatiere die folgende Modellantwort in exakt ein gueltiges JSON-Objekt um.",
                "Regeln:",
                "- Gib genau ein JSON-Objekt aus.",
                "- Keine Markdown-Codebloecke, keine Kommentare, kein Zusatztext.",
                "- Wenn mehrere JSON-Objekte enthalten sind, fuehre ihre Felder in einem Objekt zusammen.",
                "- Behalte den Inhalt der Felder bei.",
                "- Escape Zeilenumbrueche und Anfuehrungszeichen in Stringwerten korrekt.",
                "",
                "Modellantwort:",
                "```text",
                raw_text[:20000],
                "```",
            ]
        )

    @classmethod
    def _parse_json_response(cls, raw_text: str, *, schema_name: str | None = None) -> dict[str, Any]:
        return cls._structured_json_payload(str(raw_text or ""), schema_name=schema_name)

    @classmethod
    def _parse_code_response(cls, raw_text: str, *, language_hint: str | None = None) -> str:
        code = cls._extract_code_block(raw_text)
        language = cls._normalize_language(str(language_hint or "python"))
        if code.strip() and cls._looks_like_source_code(code, language_hint=language_hint):
            if language == "python" and cls._python_has_missing_main_invocation(code):
                raise ValueError(
                    "Python-Code definiert `main()`, ruft die Funktion aber nicht auf. "
                    "Bitte liefere direkt ausfuehrbaren Code mit sichtbarer Ausgabe."
                )
            return code
        language_label = SUPPORTED_LANGUAGES.get(language, "Code")
        raise ValueError(f"Antwort enthaelt keinen verwendbaren {language_label}-Code.\n\nAntwort:\n{str(raw_text or '')[:1200]}")

    @staticmethod
    def _code_repair_prompt(raw_text: str) -> str:
        return "\n".join(
            [
                "Formatiere die folgende Modellantwort zu genau einem Markdown-Codeblock um.",
                "Gib keinen Zusatztext aus.",
                "Wenn die Modellantwort Selbstpruefung, Checklisten oder Saetze wie 'Du hast die Anforderung erfuellt' enthaelt, uebernimm nur den eigentlichen Quellcode.",
                "Wenn gar kein Quellcode enthalten ist, gib keinen Erklaertext dazu aus.",
                "",
                "Modellantwort:",
                "```text",
                raw_text[:20000],
                "```",
            ]
        )

    def _planner_prompt(
        self,
        prompt: str,
        language: str,
        profile: dict[str, str],
        *,
        seed_code: str,
        seed_path: str,
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        sections = [
            "Aufgabe der Lehrkraft:",
            prompt,
            "",
            f"Bevorzugte Zielsprache: {SUPPORTED_LANGUAGES[language]}",
            f"Didaktisches Profil: {profile['label']}",
            profile["planner_focus"],
            "Plane daraus ein kleines, direkt lauffaehiges Unterrichtsartefakt mit Kommentaren.",
            "Beruecksichtige in diesem Schritt nur Thema, Lernziel, Programmidee und Hauptdatei. Reine Formatierungswuensche fuer spaetere Unterrichtstexte sind hier nachrangig.",
            "Falls kein Input gefordert ist, soll das Programm ohne Benutzereingabe durchlaufen.",
            "Wenn eine Eingabe didaktisch sinnvoll ist, liefere spaeter auch sinnvolles stdin mit oder plane einen sicheren Default fuer EOF/leerem Input ein.",
            "Halte jeden JSON-Wert knapp: title maximal 8 Woerter, learning_goal/execution_goal/success_criteria jeweils maximal 18 Woerter.",
            "",
            "Gib ausschliesslich JSON in diesem Format zurueck:",
            '{"title":"Kurzer fachlicher Titel","language":"python","main_file":"main.py","learning_goal":"Knappe Beschreibung des Lernziels","execution_goal":"Was das Programm sichtbar leisten soll","success_criteria":"Woran man erkennt, dass das Artefakt korrekt ist"}',
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=prompt))
        if seed_code.strip():
            sections.extend(
                [
                    "",
                    f"Vorhandener Code in {seed_path or DEFAULT_MAIN_FILES[language]}:",
                    f"```text\n{seed_code[:8000]}\n```",
                    "Plane eine verbesserte, weiterfuehrende Version statt eines komplett unverbundenen Artefakts.",
                ]
            )
        return "\n".join(sections)

    def _fallback_plan(self, prompt: str, language: str, profile: dict[str, str], *, seed_path: str) -> dict[str, str]:
        title_seed = re.sub(r"\s+", " ", str(prompt or "").strip()).strip(" .")
        title = title_seed[:72] if title_seed else f"{profile['label']} ({SUPPORTED_LANGUAGES[language]})"
        return {
            "title": title,
            "language": language,
            "main_file": self._sanitize_relative_path(seed_path.strip() or DEFAULT_MAIN_FILES[language]),
            "learning_goal": str(prompt or "").strip()[:240],
            "execution_goal": "Ein kurzes, direkt lauffaehiges Beispiel erzeugen.",
            "success_criteria": "Das Artefakt laeuft fehlerfrei und zeigt das Lernziel sichtbar.",
        }

    def _author_prompt(
        self,
        prompt: str,
        plan: dict[str, Any],
        profile: dict[str, str],
        *,
        seed_code: str,
        seed_path: str,
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        sections = [
            f"Lehrkraft-Prompt:\n{prompt}",
            "",
            "Umsetzungsplan:",
            json.dumps(plan, ensure_ascii=False, indent=2),
            "",
            f"Didaktisches Profil: {profile['label']}",
            profile["author_focus"],
            "Erstelle jetzt nur das lauffaehige Artefakt-Bundle mit moeglichst kompaktem, kommentiertem Code.",
            "Lehrkraft-Hinweise und Schueler-Material werden spaeter von einem separaten Didaktik-Agenten erzeugt und gehoeren hier nicht in die Antwort.",
            "Der Code soll fuer Schueler nachvollziehbar und ohne externe Cloud-Dienste nutzbar sein.",
            "Nutze nur Dateien, die fuer das Beispiel wirklich noetig sind. Bevorzuge genau eine Datei, wenn keine zweite Datei zwingend erforderlich ist.",
            "Halte title und summary sehr knapp. Begrenze die Hauptdatei auf etwa 80 Zeilen gut erklaerbaren Code.",
            "Das Programm muss beim Direktlauf mindestens eine sichtbare Ausgabe erzeugen.",
            "Wenn du eine main-Funktion anlegst, musst du sie auch explizit starten.",
            "Wenn der Code Benutzereingaben nutzt, musst du passendes stdin im Bundle mitliefern oder den Code mit einem sicheren EOFError-/Leerstring-Default absichern.",
            "",
            "Gib ausschliesslich JSON in diesem Format zurueck:",
            textwrap.dedent(
                """\
                {
                  "title": "Titel",
                  "summary": "Kurze Zusammenfassung",
                  "language": "python",
                  "main_file": "main.py",
                  "stdin": "",
                  "files": [
                    {"path": "main.py", "content": "# kommentierter Code"}
                  ]
                }
                """
            ).strip(),
            "Wichtig: Die Hauptdatei muss direkt ausfuehrbar sein.",
            "Keine zusaetzlichen Felder, keine Markdown-Codebloecke ausserhalb der JSON-Strings.",
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=prompt))
        if seed_code.strip():
            sections.extend(
                [
                    "",
                    f"Vorhandener Ausgangscode in {seed_path or plan['main_file']}:",
                    f"```text\n{seed_code[:10000]}\n```",
                    "Nutze ihn als Ausgangspunkt, verbessere Struktur, Kommentare und Unterrichtstauglichkeit.",
                ]
            )
        return "\n".join(sections)

    def _author_code_prompt(
        self,
        prompt: str,
        plan: dict[str, Any],
        profile: dict[str, str],
        *,
        seed_code: str,
        seed_path: str,
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        sections = [
            f"Lehrkraft-Prompt:\n{prompt}",
            "",
            "Umsetzungsplan:",
            json.dumps(plan, ensure_ascii=False, indent=2),
            "",
            f"Didaktisches Profil: {profile['label']}",
            profile["author_focus"],
            f"Erzeuge ausschliesslich den Inhalt der Hauptdatei {plan['main_file']} als kompakten, direkt lauffaehigen Code.",
            "Maximal 80 Zeilen. Kurze Kommentare sind erlaubt, aber keine Tabellen, keine ausgeschriebenen Unterrichtstexte und keine JSON-Ausgabe.",
            "Wenn der Lehrkraft-Prompt Materialstruktur oder Vergleichstabellen fordert, ignoriere diese hier. Das Didaktik-Modul erzeugt spaeter die Texte.",
            "Das Programm muss beim Direktlauf mindestens eine sichtbare Ausgabe erzeugen.",
            "Wenn du `def main()` schreibst, rufe `main()` auch explizit auf.",
            "Wenn du input(), readline(), scanf oder cin nutzt, muss der Code auch ohne externe Benutzereingabe lauffaehig bleiben, z. B. per EOFError-/Fallback-Default.",
            "Schreibe keine Selbstbewertung, keine Checkliste und keine Saetze wie 'Du hast die Anforderung erfuellt'.",
            f"Antworte nur mit einem einzigen Markdown-Codeblock fuer {SUPPORTED_LANGUAGES[plan['language']]}.",
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=prompt))
        if seed_code.strip():
            sections.extend(
                [
                    "",
                    f"Vorhandener Ausgangscode in {seed_path or plan['main_file']}:",
                    f"```text\n{seed_code[:10000]}\n```",
                    "Verbessere den vorhandenen Code statt komplett neu zu beginnen.",
                ]
            )
        return "\n".join(sections)

    def _pedagogy_json_repair_prompt(
        self,
        raw_text: str,
        payload: dict[str, Any],
        profile: dict[str, str],
        run_result: dict[str, Any],
        *,
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        sections = [
            "Repariere die folgende Didaktikantwort zu exakt einem JSON-Objekt.",
            f"Didaktisches Profil: {profile['label']}",
            "Das Zielobjekt muss genau die Felder teacher_notes_markdown und student_material_markdown enthalten.",
            "Lehrkraft-Hinweise maximal 6 kurze Stichpunkte, Schueler-Material maximal 6 kurze Stichpunkte oder kurze Abschnitte.",
            "",
            "Kontext:",
            json.dumps(self._pedagogy_payload_snapshot(payload, prompt_limit=1600, code_limit=3200), ensure_ascii=False, indent=2),
            "",
            "Laufdiagnose:",
            json.dumps(self._run_result_snapshot(run_result, text_limit=1200), ensure_ascii=False, indent=2),
            "",
            "Fehlerhafte Modellantwort:",
            "```text",
            raw_text[:12000],
            "```",
            "",
            'Schema: {"teacher_notes_markdown":"...","student_material_markdown":"..."}',
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=str(payload.get("prompt") or "")))
        return "\n".join(sections)

    def _repair_prompt(
        self,
        prompt: str,
        plan: dict[str, Any],
        profile: dict[str, str],
        bundle: dict[str, Any],
        run_result: dict[str, Any],
        next_attempt: int,
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        bundle_snapshot = self._bundle_prompt_snapshot(bundle, code_limit=5000)
        run_snapshot = self._run_result_snapshot(run_result, text_limit=2200)
        sections = [
            f"Lehrkraft-Prompt:\n{prompt}",
            "",
            "Plan:",
            json.dumps(plan, ensure_ascii=False, indent=2),
            "",
            f"Fehlgeschlagener Versuch {next_attempt - 1}:",
            json.dumps(run_snapshot, ensure_ascii=False, indent=2),
            "",
            "Aktueller Artefakt-Stand:",
            json.dumps(bundle_snapshot, ensure_ascii=False, indent=2),
            "",
            f"Didaktisches Profil: {profile['label']}",
            profile["author_focus"],
            "Repariere den Code so, dass er lauffaehig wird. Halte Titel, didaktische Ausrichtung und Ziel der Aufgabe stabil.",
            "Das reparierte Programm muss beim Direktlauf sichtbare Ausgabe erzeugen.",
            "Wenn eine main-Funktion existiert, muss sie auch gestartet werden.",
            "Wenn der Fehler auf fehlender Eingabe beruht, liefere sinnvolles stdin mit oder mache den Code per EOFError-/Fallback-Default ohne Benutzereingabe lauffaehig.",
            "Gib ausschliesslich das vollstaendig korrigierte JSON-Bundle mit den Feldern title, summary, language, main_file, stdin und files zurueck.",
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=prompt))
        return "\n".join(sections)

    def _repair_code_prompt(
        self,
        prompt: str,
        plan: dict[str, Any],
        profile: dict[str, str],
        bundle: dict[str, Any],
        run_result: dict[str, Any],
        next_attempt: int,
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        run_snapshot = self._run_result_snapshot(run_result, text_limit=2200)
        sections = [
            f"Lehrkraft-Prompt:\n{prompt}",
            "",
            "Plan:",
            json.dumps(plan, ensure_ascii=False, indent=2),
            "",
            f"Hauptdatei: {bundle['main_file']}",
            "",
            f"Fehlgeschlagener Versuch {next_attempt - 1}:",
            json.dumps(run_snapshot, ensure_ascii=False, indent=2),
            "",
            "Aktueller Code der Hauptdatei:",
            f"```text\n{self._main_file_content(bundle['files'], bundle['main_file'])[:7000]}\n```",
            "",
            f"Didaktisches Profil: {profile['label']}",
            "Repariere nur den Code der Hauptdatei.",
            "Das reparierte Programm muss beim Direktlauf sichtbare Ausgabe erzeugen.",
            "Wenn `def main()` existiert, muss `main()` aufgerufen werden.",
            "Wenn der Fehler auf fehlender Eingabe beruht, baue einen sicheren EOFError-/Fallback-Default ein, damit der Code auch ohne vorbereitete Eingabe laeuft.",
            "Schreibe keine Selbstbewertung, keine Checkliste und keine Saetze wie 'Du hast die Anforderung erfuellt'.",
            "Antworte ausschliesslich mit einem einzelnen Markdown-Codeblock ohne Zusatztext.",
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=prompt))
        return "\n".join(sections)

    def _pedagogy_prompt(
        self,
        payload: dict[str, Any],
        profile: dict[str, str],
        run_result: dict[str, Any],
        instruction_preset: dict[str, Any] | None = None,
    ) -> str:
        payload_snapshot = self._pedagogy_payload_snapshot(payload, prompt_limit=1800, code_limit=4200)
        sections = [
            "Formuliere aus dem funktionierenden Code eine kurze, professionelle Unterrichtsaufbereitung.",
            f"Didaktisches Profil: {profile['label']}",
            profile["pedagogy_focus"],
            "Halte beide Texte kompakt. Lehrkraft-Hinweise maximal 6 kurze Stichpunkte, Schueler-Material maximal 6 kurze Stichpunkte oder kurze Abschnitte.",
            "Beruecksichtige explizite Formatwuensche aus dem Lehrkraft-Prompt nur dort, wo sie fuer die Unterrichtstexte relevant sind.",
            json.dumps(payload_snapshot, ensure_ascii=False, indent=2),
            "",
            "Laufdiagnose:",
            json.dumps(self._run_result_snapshot(run_result, text_limit=1600), ensure_ascii=False, indent=2),
            "",
            "Gib ausschliesslich JSON in diesem Format zurueck:",
            textwrap.dedent(
                """\
                {
                  "teacher_notes_markdown": "Kurze Lehrkraft-Hinweise mit Lernziel, Einsatz im Unterricht und typischen Stolperstellen",
                  "student_material_markdown": "Kurze Schuelererklaerung mit Arbeitsauftrag und Reflexionsfrage"
                }
                """
            ).strip(),
        ]
        sections.extend(self._instruction_preset_lines(instruction_preset, prompt_text=str(payload.get("prompt") or "")))
        return "\n".join(sections)
