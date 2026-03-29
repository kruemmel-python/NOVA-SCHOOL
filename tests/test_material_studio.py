from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nova_school_server.database import SchoolRepository
from nova_school_server.material_studio import (
    SUPPORTED_LANGUAGES,
    TeacherMaterialStudioService,
    material_studio_instruction_preset_catalog,
    material_studio_profile_catalog,
    resolve_material_studio_instruction_preset,
)


class _FakeRunner:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = list(results)
        self.payloads: list[dict[str, object]] = []

    def run_bundle(self, _session, payload: dict[str, object]) -> dict[str, object]:
        self.payloads.append(dict(payload))
        if not self.results:
            raise AssertionError("Kein Runner-Ergebnis mehr vorbereitet.")
        return dict(self.results.pop(0))


class _FakeAI:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def complete(self, **kwargs) -> tuple[str, str]:
        self.calls.append(dict(kwargs))
        if not self.responses:
            raise AssertionError("Keine KI-Antwort mehr vorbereitet.")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, tuple) or len(response) != 2:
            raise AssertionError("KI-Antwort muss ein (text, model)-Tuple oder eine Exception sein.")
        return response


class _TeacherSession:
    username = "teacher"
    role = "teacher"
    is_teacher = True
    permissions = {
        "ai.use": True,
        "teacher.materials.use": True,
        "run.python": True,
        "web.access": False,
    }


class MaterialStudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repository = SchoolRepository(Path(self.tmp.name) / "school.db")

    def tearDown(self) -> None:
        self.repository.close()
        self.tmp.cleanup()

    def test_profile_catalog_contains_specialized_teacher_profiles(self) -> None:
        profiles = material_studio_profile_catalog()
        keys = {item["key"] for item in profiles}
        self.assertIn("example-code", keys)
        self.assertIn("worksheet", keys)
        self.assertIn("assessment", keys)
        self.assertIn("board-lesson", keys)
        self.assertIn("differentiation", keys)

    def test_instruction_preset_catalog_contains_python_course_entries_for_worksheet_and_example_code(self) -> None:
        presets = material_studio_instruction_preset_catalog()
        self.assertTrue(presets)
        worksheet_presets = [item for item in presets if item["profile"] == "worksheet"]
        example_code_presets = [item for item in presets if item["profile"] == "example-code"]
        self.assertTrue(worksheet_presets)
        self.assertTrue(example_code_presets)
        languages = {item["language"] for item in presets}
        self.assertEqual(languages, set(SUPPORTED_LANGUAGES))
        resolved = resolve_material_studio_instruction_preset(
            next(item for item in worksheet_presets if item["language"] == "python")["key"],
            profile="worksheet",
            language="python",
        )
        self.assertEqual(resolved["language"], "python")
        self.assertIsNone(
            resolve_material_studio_instruction_preset(
                next(item for item in worksheet_presets if item["language"] == "python")["key"],
                profile="example-code",
                language="python",
            )
        )
        example_code_resolved = resolve_material_studio_instruction_preset(
            next(item for item in example_code_presets if item["language"] == "python")["key"],
            profile="example-code",
            language="python",
        )
        self.assertEqual(example_code_resolved["language"], "python")
        self.assertIn("kompaktes, direkt ausfuehrbares Python-Beispiel", example_code_resolved["prompt"])
        self.assertIsNone(
            resolve_material_studio_instruction_preset(
                next(item for item in example_code_presets if item["language"] == "python")["key"],
                profile="worksheet",
                language="python",
            )
        )

    def test_instruction_preset_catalog_covers_every_supported_language_with_both_profiles(self) -> None:
        presets = material_studio_instruction_preset_catalog()
        for language in SUPPORTED_LANGUAGES:
            language_presets = [item for item in presets if item["language"] == language]
            self.assertTrue(language_presets, language)
            self.assertIn("worksheet", {item["profile"] for item in language_presets}, language)
            self.assertIn("example-code", {item["profile"] for item in language_presets}, language)

        rust_example = next(
            item for item in presets
            if item["language"] == "rust" and item["profile"] == "example-code"
        )
        self.assertIn("Rust-Grundkurs", rust_example["prompt"])
        self.assertIn("println!", rust_example["prompt"])

        node_worksheet = next(
            item for item in presets
            if item["language"] == "node" and item["profile"] == "worksheet"
        )
        self.assertIn("Node.js-Grundkurs", node_worksheet["prompt"])
        self.assertIn("keine DOM- oder Browser-APIs", node_worksheet["prompt"])

    def test_extract_json_object_merges_multiple_fenced_objects(self) -> None:
        raw = """```json
{"teacher_notes_markdown": "Lehrkraft"}
```

```json
{"student_material_markdown": "Schueler"}
```"""

        payload = TeacherMaterialStudioService._extract_json_object(raw)

        self.assertEqual(payload["teacher_notes_markdown"], "Lehrkraft")
        self.assertEqual(payload["student_material_markdown"], "Schueler")

    def test_extract_json_object_accepts_jsonish_string_concatenation(self) -> None:
        raw = """```json
{
  "title": "Dictionary und Tuple",
  "student_material_markdown": [
    "**Definition:**"
    "Dictionary ist veraenderbar.",
    "Tuple ist immutable."
  ]
}
```"""

        payload = TeacherMaterialStudioService._extract_json_object(raw)

        self.assertEqual(payload["title"], "Dictionary und Tuple")
        self.assertEqual(
            payload["student_material_markdown"],
            ["**Definition:**Dictionary ist veraenderbar.", "Tuple ist immutable."],
        )

    def test_extract_code_block_prefers_nested_language_block_over_outer_text_wrapper(self) -> None:
        raw = """Hier ist das Snippet:

```text
```python
print("Hallo")
```
```"""

        code = TeacherMaterialStudioService._extract_code_block(raw)

        self.assertEqual(code, 'print("Hallo")')

    def test_extract_code_block_recovers_trailing_code_from_unclosed_fence(self) -> None:
        raw = """Hier ist der Fix:

```python
print("Hallo")
print("Welt")
"""

        code = TeacherMaterialStudioService._extract_code_block(raw)

        self.assertEqual(code, 'print("Hallo")\nprint("Welt")')

    def test_parse_code_response_accepts_plain_python_code_without_fence(self) -> None:
        raw = 'name = "Nova"\nprint(name)\n'

        code = TeacherMaterialStudioService._parse_code_response(raw, language_hint="python")

        self.assertEqual(code, raw.strip())

    def test_parse_code_response_rejects_self_evaluation_prose(self) -> None:
        raw = (
            "Du hast die Antwort in einem einzigen Codeblock erstellt. Das ist korrekt.\n"
            "Du hast die Anforderung, nur die Python-Standardbibliothek zu verwenden, erfuellt.\n"
            "Du hast die Anforderung, keine externen Bibliotheken zu verwenden, erfuellt.\n"
        )

        with self.assertRaises(ValueError):
            TeacherMaterialStudioService._parse_code_response(raw, language_hint="python")

    def test_parse_code_response_rejects_python_main_without_invocation(self) -> None:
        raw = """```python
def main():
    print("Hallo")
```"""

        with self.assertRaises(ValueError):
            TeacherMaterialStudioService._parse_code_response(raw, language_hint="python")

    def test_generation_flow_runs_planning_authoring_and_pedagogy(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Hallo\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 7,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                }
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner)

        step = service.start_generation(prompt="Erklaere print().", language="python", profile="worksheet", attempt_limit=1)
        self.assertEqual(step["mode"], "infer")
        self.assertEqual(step["phase"], "plan")
        self.assertEqual(step["idle_timeout_ms"], 35000)
        self.assertTrue(step["accept_partial_on_timeout"])

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","language":"python","main_file":"main.py","learning_goal":"print verstehen","execution_goal":"Hallo ausgeben","success_criteria":"Programm laeuft"}',
            model="plan-model",
        )
        self.assertEqual(step["phase"], "author")
        self.assertEqual(step["idle_timeout_ms"], 60000)
        self.assertTrue(step["accept_partial_on_timeout"])

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","summary":"Kurzes Beispiel","language":"python","main_file":"main.py","files":[{"path":"main.py","content":"print(\\"Hallo\\")\\n"}]}',
            model="author-model",
        )
        self.assertEqual(step["phase"], "pedagogy")

        payload = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"teacher_notes_markdown":"Lehrkraft-Hinweis","student_material_markdown":"Arbeitsauftrag"}',
            model="pedagogy-model",
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["attempts_used"], 1)
        self.assertEqual(payload["code"], 'print("Hallo")\n')
        self.assertEqual(payload["teacher_notes_markdown"], "Lehrkraft-Hinweis")
        self.assertEqual(payload["student_material_markdown"], "Arbeitsauftrag")

    def test_generation_flow_falls_back_from_invalid_author_json_to_code_block(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Hallo\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 9,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                }
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner)

        step = service.start_generation(prompt="Erklaere print().", language="python", profile="worksheet", attempt_limit=1)
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","language":"python","main_file":"main.py","learning_goal":"print verstehen","execution_goal":"Hallo ausgeben","success_criteria":"Programm laeuft"}',
            model="plan-model",
        )
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","summary":"kaputt"',
            model="author-model",
        )
        self.assertEqual(step["phase"], "author_json_repair")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","summary":"immer noch kaputt"',
            model="repair-model",
        )
        self.assertEqual(step["phase"], "author_code")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='```python\nprint("Hallo")\n```',
            model="code-model",
        )
        self.assertEqual(step["phase"], "pedagogy")

        payload = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"teacher_notes_markdown":"Lehrkraft","student_material_markdown":"Schueler"}',
            model="pedagogy-model",
        )

        self.assertTrue(payload["passed"])
        self.assertTrue(any(item["agent"] == "Autor" and item["status"] == "warning" for item in payload["agent_trace"]))

    def test_quality_pipeline_starts_with_real_plan_then_author_json(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Hallo\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 5,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                }
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner, ai_service=_FakeAI([]))
        service.ai_service.provider_id = "server-litert-lm"

        step = service.start_generation(
            prompt="Erstelle ein Arbeitsblatt fuer Python.",
            language="python",
            profile="worksheet",
            attempt_limit=1,
        )

        self.assertEqual(step["phase"], "plan")
        self.assertEqual(step["generation_options"]["max_tokens"], 480)
        self.assertEqual(step["timeout_seconds"], 240.0)
        self.assertEqual(step["agent_trace"], [])

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Python Einstieg","language":"python","main_file":"main.py","learning_goal":"print verstehen","execution_goal":"sichtbare Ausgabe","success_criteria":"Programm laeuft"}',
            model="litert-plan",
        )

        self.assertEqual(step["phase"], "author")
        self.assertEqual(step["generation_options"]["max_tokens"], 1400)

    def test_generation_flow_repairs_invalid_pedagogy_json(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Hallo\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 5,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                }
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner)

        step = service.start_generation(prompt="Erklaere print().", language="python", profile="worksheet", attempt_limit=1)
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","language":"python","main_file":"main.py","learning_goal":"print verstehen","execution_goal":"Hallo ausgeben","success_criteria":"Programm laeuft"}',
            model="plan-model",
        )
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Print","summary":"Kurzes Beispiel","language":"python","main_file":"main.py","files":[{"path":"main.py","content":"print(\\"Hallo\\")\\n"}]}',
            model="author-model",
        )

        self.assertEqual(step["phase"], "pedagogy")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"teacher_notes_markdown":"Lehrkraft"',
            model="pedagogy-model",
        )
        self.assertEqual(step["phase"], "pedagogy_json_repair")

        payload = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"teacher_notes_markdown":"Lehrkraft","student_material_markdown":"Schueler"}',
            model="pedagogy-repair-model",
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["teacher_notes_markdown"], "Lehrkraft")
        self.assertEqual(payload["student_material_markdown"], "Schueler")

    def test_generation_flow_repairs_failed_run_via_debugger_code_fallback(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "",
                    "stderr": "NameError: name 'total' is not defined",
                    "returncode": 1,
                    "duration_ms": 10,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                },
                {
                    "run_id": "r2",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "1.5\n4.0\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 12,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                },
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner)

        step = service.start_generation(prompt="Berechne zwei Durchschnitte.", language="python", profile="worksheet", attempt_limit=3)
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Durchschnitt","language":"python","main_file":"main.py","learning_goal":"Listen","execution_goal":"Mittelwerte","success_criteria":"Programm laeuft"}',
            model="plan-model",
        )
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Durchschnitt","summary":"Kurz","language":"python","main_file":"main.py","files":[{"path":"main.py","content":"values = [1, 2]\\nprint(total)\\n"}]}',
            model="author-model",
        )
        self.assertEqual(step["phase"], "repair")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Durchschnitt","summary":"kaputt"',
            model="debugger-model",
        )
        self.assertEqual(step["phase"], "repair_json_repair")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Durchschnitt","summary":"immer noch kaputt"',
            model="debugger-repair-model",
        )
        self.assertEqual(step["phase"], "repair_code")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text="```python\na = [1, 2]\nb = [3, 5]\nprint(sum(a) / len(a))\nprint(sum(b) / len(b))\n```",
            model="debugger-code-model",
        )
        self.assertEqual(step["phase"], "pedagogy")

        payload = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"teacher_notes_markdown":"Lehrkraft","student_material_markdown":"Schueler"}',
            model="pedagogy-model",
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["attempts_used"], 2)
        self.assertTrue(any(item["agent"] == "Debugger" and item["status"] == "warning" for item in payload["agent_trace"]))

    def test_attempt_limit_counts_repair_rounds_after_initial_run(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "",
                    "stderr": "EOFError: EOF when reading a line",
                    "returncode": 1,
                    "duration_ms": 10,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                },
                {
                    "run_id": "r2",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "OK\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 8,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                },
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner)

        step = service.start_generation(prompt="Erkläre input().", language="python", profile="worksheet", attempt_limit=1)
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Input","language":"python","main_file":"main.py","learning_goal":"input verstehen","execution_goal":"Eingabe zeigen","success_criteria":"Programm laeuft"}',
            model="plan-model",
        )
        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Input","summary":"Kurz","language":"python","main_file":"main.py","stdin":"","files":[{"path":"main.py","content":"name = input(\\"Name: \\")\\nprint(name)\\n"}]}',
            model="author-model",
        )
        self.assertEqual(step["phase"], "repair")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Input","summary":"kaputt"',
            model="debugger-model",
        )
        self.assertEqual(step["phase"], "repair_json_repair")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"title":"Input","summary":"immer noch kaputt"',
            model="debugger-repair-model",
        )
        self.assertEqual(step["phase"], "repair_code")

        step = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text="```python\ntry:\n    name = input(\"Name: \")\nexcept EOFError:\n    name = \"Nova\"\nprint(name)\n```",
            model="debugger-code-model",
        )
        self.assertEqual(step["phase"], "pedagogy")

        payload = service.continue_generation(
            _TeacherSession(),
            generation_state=step["generation_state"],
            response_text='{"teacher_notes_markdown":"Lehrkraft","student_material_markdown":"Schueler"}',
            model="pedagogy-model",
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["attempts_used"], 2)

    def test_author_prompt_requires_stdin_or_eof_safe_input(self) -> None:
        service = TeacherMaterialStudioService(self.repository, _FakeRunner([]))
        prompt = service._author_prompt(
            "Erklaere input().",
            {
                "title": "Input",
                "language": "python",
                "main_file": "main.py",
                "learning_goal": "input verstehen",
                "execution_goal": "Eingabe zeigen",
                "success_criteria": "Programm laeuft",
            },
            {
                "key": "worksheet",
                "label": "Arbeitsblatt",
                "author_focus": "Erstelle Arbeitsauftrag, Hilfestellungen und eine kommentierte Musterloesung fuer die Lehrkraft.",
            },
            seed_code="",
            seed_path="",
        )

        self.assertIn("stdin", prompt)
        self.assertIn("EOFError", prompt)

    def test_litert_plan_prompt_is_trimmed_to_budget(self) -> None:
        ai = _FakeAI([])
        ai.provider_id = "server-litert-lm"
        service = TeacherMaterialStudioService(self.repository, _FakeRunner([]), ai_service=ai)
        long_prompt = ("Sehr lange Lehrkraft-Anweisung mit Details zu Tabellen, Reflexion, Diagnose und Vergleichen. " * 320).strip()

        step = service.start_generation(
            prompt=long_prompt,
            language="python",
            profile="worksheet",
            attempt_limit=1,
        )

        self.assertEqual(step["phase"], "plan")
        self.assertTrue(step["prompt_truncated"])
        self.assertLessEqual(step["prompt_token_estimate"], step["prompt_token_budget"])
        self.assertIn("Aufgabe der Lehrkraft:", step["prompt"])
        self.assertIn("Gib ausschliesslich JSON", step["prompt"])
        self.assertIn("Prompt gekuerzt", step["prompt"])

    def test_complete_inference_payload_retries_with_stricter_budget_after_litert_token_error(self) -> None:
        ai = _FakeAI(
            [
                RuntimeError(
                    "INFO: Created TensorFlow Lite XNNPACK delegate for CPU. "
                    "Error: stream error: INVALID_ARGUMENT: Input token ids are too long. "
                    "Exceeding the maximum number of tokens allowed: 4427 >= 4096"
                ),
                ('{"title":"Python Einstieg","language":"python","main_file":"main.py","learning_goal":"print verstehen","execution_goal":"sichtbare Ausgabe","success_criteria":"Programm laeuft"}', "litert-plan"),
            ]
        )
        ai.provider_id = "server-litert-lm"
        service = TeacherMaterialStudioService(self.repository, _FakeRunner([]), ai_service=ai)
        oversized_prompt = ("Lehrkraft-Prompt mit sehr viel Kontext und Zusatzmaterial. " * 420).strip()

        payload = service._inference_step(
            {"prompt": oversized_prompt, "trace": []},
            phase="plan",
            status="Planer strukturiert das Unterrichtsartefakt...",
            prompt=service._planner_prompt(
                oversized_prompt,
                "python",
                {
                    "key": "worksheet",
                    "label": "Arbeitsblatt",
                    "planner_focus": "Plane ein Artefakt fuer eine Unterrichtsphase mit Erarbeitung, Uebung und kurzer Sicherung.",
                },
                seed_code="",
                seed_path="",
            ),
            system_prompt="Du bist Nova Studio Planner. Antworte ausschliesslich als JSON.",
        )

        raw_text, model = service._complete_inference_payload(payload)

        self.assertEqual(model, "litert-plan")
        self.assertIn("Python Einstieg", raw_text)
        self.assertEqual(len(ai.calls), 2)
        self.assertLess(len(str(ai.calls[1]["prompt"] or "")), len(str(ai.calls[0]["prompt"] or "")))

    def test_direct_generate_uses_one_repair_round_when_attempt_limit_is_one(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "",
                    "stderr": "EOFError: EOF when reading a line",
                    "returncode": 1,
                    "duration_ms": 10,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                },
                {
                    "run_id": "r2",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Nova\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 8,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                },
            ]
        )
        ai = _FakeAI(
            [
                (
                    '{"title":"Input","language":"python","main_file":"main.py","learning_goal":"input verstehen","execution_goal":"Eingabe zeigen","success_criteria":"Programm laeuft"}',
                    "plan-model",
                ),
                (
                    '{"title":"Input","summary":"Kurz","language":"python","main_file":"main.py","stdin":"","files":[{"path":"main.py","content":"name = input(\\"Name: \\")\\nprint(name)\\n"}]}',
                    "author-model",
                ),
                (
                    '{"title":"Input","summary":"Kurz","language":"python","main_file":"main.py","stdin":"","files":[{"path":"main.py","content":"try:\\n    name = input(\\"Name: \\\")\\nexcept EOFError:\\n    name = \\"Nova\\"\\nprint(name)\\n"}]}',
                    "repair-model",
                ),
                (
                    '{"teacher_notes_markdown":"Lehrkraft","student_material_markdown":"Schueler"}',
                    "pedagogy-model",
                ),
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner, ai_service=ai)

        preset = next(
            item
            for item in material_studio_instruction_preset_catalog()
            if item["profile"] == "worksheet" and item["language"] == "python"
        )

        payload = service.generate(
            _TeacherSession(),
            prompt="Erklaere input().",
            language="python",
            profile="worksheet",
            instruction_preset_key=preset["key"],
            attempt_limit=1,
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["attempts_used"], 2)
        self.assertTrue(any(item["agent"] == "Debugger" for item in payload["agent_trace"]))
        self.assertEqual(payload["instruction_preset_key"], preset["key"])
        self.assertIn("Verbindliche Kursvorgabe", str(ai.calls[0].get("prompt") or ""))
        self.assertIn(preset["label"], str(ai.calls[0].get("prompt") or ""))

    def test_direct_generate_uses_example_code_instruction_preset(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Hallo\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 4,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                }
            ]
        )
        ai = _FakeAI(
            [
                (
                    '{"title":"Print Demo","language":"python","main_file":"main.py","learning_goal":"print verstehen","execution_goal":"Hallo ausgeben","success_criteria":"Programm laeuft"}',
                    "plan-model",
                ),
                (
                    '{"title":"Print Demo","summary":"Kurzbeispiel","language":"python","main_file":"main.py","files":[{"path":"main.py","content":"print(\\"Hallo\\")\\n"}]}',
                    "author-model",
                ),
                (
                    '{"teacher_notes_markdown":"Lehrkraft","student_material_markdown":"Schueler"}',
                    "pedagogy-model",
                ),
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner, ai_service=ai)
        preset = next(
            item
            for item in material_studio_instruction_preset_catalog()
            if item["profile"] == "example-code" and item["language"] == "python"
        )

        payload = service.generate(
            _TeacherSession(),
            prompt="Erklaere print().",
            language="python",
            profile="example-code",
            instruction_preset_key=preset["key"],
            attempt_limit=1,
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["instruction_preset_key"], preset["key"])
        self.assertIn("Verbindliche Kursvorgabe", str(ai.calls[0].get("prompt") or ""))
        self.assertIn(preset["label"], str(ai.calls[0].get("prompt") or ""))
        self.assertIn("Pflichtanker", str(ai.calls[0].get("prompt") or ""))

    def test_run_current_builds_bundle_from_code_only(self) -> None:
        runner = _FakeRunner(
            [
                {
                    "run_id": "r1",
                    "language": "python",
                    "command": ["python", "main.py"],
                    "stdout": "Hallo\n",
                    "stderr": "",
                    "returncode": 0,
                    "duration_ms": 4,
                    "preview_path": "",
                    "notes": [],
                    "tool_session": {},
                }
            ]
        )
        service = TeacherMaterialStudioService(self.repository, runner)

        payload = service.run_current(
            _TeacherSession(),
            {
                "title": "Testlauf",
                "language": "python",
                "main_file": "main.py",
                "code": "print('Hallo')\n",
                "stdin": "",
            },
        )

        self.assertTrue(payload["passed"])
        self.assertEqual(payload["files"][0]["path"], "main.py")
        self.assertEqual(payload["code"], "print('Hallo')\n")


if __name__ == "__main__":
    unittest.main()
