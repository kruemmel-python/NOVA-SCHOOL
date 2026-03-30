from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from nova_school_server.code_runner import CodeRunner, RunResult, _RawResult
from nova_school_server.config import ServerConfig
from nova_school_server.workspace import WorkspaceManager


class _FakeToolSandbox:
    def authorize(self, *_args, **_kwargs):  # pragma: no cover
        return {}


class _FakeRepository:
    def __init__(self, settings: dict[str, str]) -> None:
        self.settings = settings

    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)


class _ObservedCodeRunner(CodeRunner):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.last_command: list[str] | None = None
        self.last_env: dict[str, str] | None = None

    def _execute(self, run_id, language, command, cwd, stdin_text, env, tool_session, permissions):
        self.last_command = command
        self.last_env = dict(env)
        return RunResult(run_id=run_id, language=language, command=command)


class _ContainerObservedRunner(CodeRunner):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.raw_commands: list[list[str]] = []
        self.last_container_command: list[str] | None = None
        self.last_container_env: dict[str, str] | None = None

    def _execute_raw(self, command, cwd, stdin_text, env, *, timeout_seconds=None):
        self.raw_commands.append(list(command))
        command_text = " ".join(command)
        if "pip install" in command_text:
            deps_root = Path(cwd) / ".nova-python" / "site-packages"
            deps_root.mkdir(parents=True, exist_ok=True)
            (deps_root / "demo.py").write_text("value = 1\n", encoding="utf-8")
        return _RawResult("", "", 0, 1, list(command))

    def _execute_container(self, run_id, language, runtime_executable, image, inner_command, project_root, container_workspace, stdin_text, env, tool_session, permissions):
        self.last_container_command = list(inner_command)
        self.last_container_env = dict(env)
        if "python_gui_snapshot.sh" in " ".join(inner_command):
            preview = Path(container_workspace) / ".nova-build" / "gui-preview.png"
            preview.parent.mkdir(parents=True, exist_ok=True)
            preview.write_bytes(b"PNG")
        return RunResult(run_id=run_id, language=language, command=list(inner_command), stdout="", stderr="", notes=self._backend_notes(permissions, "container", runtime_executable, image))


class _Session:
    username = "student"
    role = "student"
    is_teacher = False
    permissions = {
        "run.python": True,
        "run.html": True,
        "web.access": False,
    }


class _TeacherSession(_Session):
    username = "teacher"
    role = "teacher"
    is_teacher = True


class CodeRunnerTests(unittest.TestCase):
    def test_execute_container_python_hides_bootstrap_frames_from_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({}),
            )
            raw_stderr = (
                "Traceback (most recent call last):\n"
                "  File \"/workspace/.nova-build/python_entry.py\", line 25, in <module>\n"
                "    runpy.run_path(str(entry), run_name=\"__main__\")\n"
                "  File \"<frozen runpy>\", line 287, in run_path\n"
                "  File \"<frozen runpy>\", line 98, in _run_module_code\n"
                "  File \"<frozen runpy>\", line 88, in _run_code\n"
                "  File \"/workspace/main.py\", line 15, in <module>\n"
                "    print(greet(read_name() or \"Nova School\"))\n"
                "                ^^^^^^^^^\n"
                "NameError: name 'read_name' is not defined. Did you mean: 'read_nam'?\n"
            )
            raw_result = _RawResult("", raw_stderr, 1, 12, ["docker", "run"])

            with patch.object(runner, "_execute_container_raw", return_value=raw_result):
                result = runner._execute_container(
                    "run123",
                    "python",
                    "docker",
                    "python:3.12-slim",
                    ["python", "/workspace/.nova-build/python_entry.py"],
                    Path(tmp),
                    Path(tmp),
                    "",
                    {},
                    {},
                    {"web.access": False},
                )

            self.assertEqual(result.returncode, 1)
            self.assertIn('/workspace/main.py", line 15', result.stderr)
            self.assertIn("NameError", result.stderr)
            self.assertNotIn(".nova-build/python_entry.py", result.stderr)
            self.assertNotIn("<frozen runpy>", result.stderr)

    def test_execute_python_process_hides_bootstrap_frames_from_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            raw_stderr = (
                "Traceback (most recent call last):\n"
                "  File \"C:\\\\tmp\\\\.nova-build\\\\python_entry.py\", line 25, in <module>\n"
                "    runpy.run_path(str(entry), run_name=\"__main__\")\n"
                "  File \"<frozen runpy>\", line 287, in run_path\n"
                "  File \"<frozen runpy>\", line 98, in _run_module_code\n"
                "  File \"<frozen runpy>\", line 88, in _run_code\n"
                "  File \"C:\\\\tmp\\\\main.py\", line 15, in <module>\n"
                "    print(greet(read_name() or \"Nova School\"))\n"
                "                ^^^^^^^^^\n"
                "NameError: name 'read_name' is not defined. Did you mean: 'read_nam'?\n"
            )
            raw_result = _RawResult("", raw_stderr, 1, 9, [r"C:\Python312\python.exe", "-I", "python_entry.py"])

            with patch.object(runner, "_execute_raw", return_value=raw_result):
                result = runner._execute(
                    "run123",
                    "python",
                    [r"C:\Python312\python.exe", "-I", "python_entry.py"],
                    Path(tmp),
                    "",
                    {},
                    {},
                    {"web.access": True},
                )

            self.assertEqual(result.returncode, 1)
            self.assertIn('C:\\\\tmp\\\\main.py", line 15', result.stderr)
            self.assertIn("NameError", result.stderr)
            self.assertNotIn(".nova-build\\python_entry.py", result.stderr)
            self.assertNotIn("<frozen runpy>", result.stderr)

    def test_run_bundle_executes_python_without_project_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )

            result = runner.run_bundle(
                _TeacherSession(),
                {
                    "language": "python",
                    "main_file": "main.py",
                    "files": [{"path": "main.py", "content": "print('Hallo')\n"}],
                },
            )

            self.assertEqual(result["language"], "python")
            self.assertEqual(result["returncode"], 0)
            self.assertIsNotNone(runner.last_command)
            self.assertIn("NOVA_SCHOOL_ENTRYPOINT", runner.last_env)

    def test_run_bundle_returns_python_syntax_error_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )

            result = runner.run_bundle(
                _TeacherSession(),
                {
                    "language": "python",
                    "main_file": "main.py",
                    "files": [{"path": "main.py", "content": "def broken(:\n    pass\n"}],
                },
            )

            self.assertEqual(result["returncode"], 1)
            self.assertIn("SyntaxError", result["stderr"])

    def test_runner_backend_uses_valid_repository_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({"runner_backend": "container"}))
            self.assertEqual(runner._runner_backend({}), "container")

    def test_runner_backend_falls_back_for_invalid_repository_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({"runner_backend": "blob"}))
            self.assertEqual(runner._runner_backend({}), "container")

    def test_process_backend_requires_explicit_unsafe_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": False}),
            )
            with self.assertRaises(PermissionError):
                runner.resolve_backend(_Session(), {"runner_backend": "process"}, purpose="Test")

    def test_html_preview_bypasses_process_backend_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            workspace = WorkspaceManager(config)
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                workspace,
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": False}),
            )
            project = {
                "project_id": "proj-html",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "html-labor",
                "template": "frontend-lab",
                "runtime": "html",
                "main_file": "index.html",
            }
            project_root = workspace.materialize_project(project)
            original_css = (project_root / "src" / "app.css").read_text(encoding="utf-8")

            result = runner.run(
                _Session(),
                project,
                {
                    "path": "src/app.css",
                    "language": "python",
                    "code": "body { color: rgb(1, 2, 3); }\n",
                },
            )

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["language"], "html")
            self.assertEqual(result["command"], ["preview"])
            self.assertTrue(result["preview_path"])
            self.assertTrue(result["preview_path"].endswith("/workspace/index.html"))
            preview_index = project_root / Path(result["preview_path"])
            preview_root = preview_index.parent
            self.assertTrue(preview_index.exists())
            self.assertIn('src="src/main.js"', preview_index.read_text(encoding="utf-8"))
            self.assertEqual((preview_root / "src" / "app.css").read_text(encoding="utf-8"), "body { color: rgb(1, 2, 3); }\n")
            self.assertTrue((preview_root / "src" / "main.js").exists())
            self.assertEqual((project_root / "src" / "app.css").read_text(encoding="utf-8"), original_css)

    def test_python_project_run_uses_main_file_even_when_helper_is_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            workspace = WorkspaceManager(config)
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                workspace,
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-python-main",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "python-main-run",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }
            root = workspace.materialize_project(project)
            (root / "lib").mkdir(parents=True, exist_ok=True)
            (root / "lib" / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")

            with patch("nova_school_server.code_runner.shutil.which", side_effect=[r"C:\Python312\python.exe"]):
                result = runner.run(
                    _TeacherSession(),
                    project,
                    {
                        "path": "lib/helper.py",
                        "language": "javascript",
                        "code": "VALUE = 2\n",
                    },
                )

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["language"], "python")
            assert runner.last_env is not None
            entrypoint = runner.last_env["NOVA_SCHOOL_ENTRYPOINT"].replace("\\", "/")
            self.assertTrue(entrypoint.endswith("/workspace/main.py"))
            self.assertFalse(entrypoint.endswith("/workspace/lib/helper.py"))

    def test_javascript_project_run_uses_main_file_even_when_helper_is_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            workspace = WorkspaceManager(config)
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                workspace,
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-js-main",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "javascript-main-run",
                "template": "javascript",
                "runtime": "javascript",
                "main_file": "main.js",
            }
            root = workspace.materialize_project(project)
            (root / "lib").mkdir(parents=True, exist_ok=True)
            (root / "lib" / "helper.js").write_text("export const value = 1;\n", encoding="utf-8")

            with patch("nova_school_server.code_runner.shutil.which", side_effect=[r"C:\Program Files\nodejs\node.exe"]):
                result = runner.run(
                    type("JsTeacherSession", (), {"username": "teacher", "role": "teacher", "is_teacher": True, "permissions": {"run.javascript": True, "web.access": False}})(),
                    project,
                    {
                        "path": "lib/helper.js",
                        "language": "python",
                        "code": "export const value = 2;\n",
                    },
                )

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["language"], "javascript")
            assert runner.last_command is not None
            command_path = runner.last_command[-1].replace("\\", "/")
            self.assertTrue(command_path.endswith("/workspace/main.js"))
            self.assertFalse(command_path.endswith("/workspace/lib/helper.js"))

    def test_cpp_project_run_compiles_all_project_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            workspace = WorkspaceManager(config)
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                workspace,
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-cpp-main",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "cpp-main-run",
                "template": "cpp",
                "runtime": "cpp",
                "main_file": "main.cpp",
            }
            root = workspace.materialize_project(project)
            (root / "math.cpp").write_text("int add(int a, int b) { return a + b; }\n", encoding="utf-8")
            compile_commands: list[list[str]] = []

            def fake_execute_raw(command, cwd, stdin_text, env, *, timeout_seconds=None):
                compile_commands.append(list(command))
                return _RawResult("", "", 0, 1, list(command))

            with patch("nova_school_server.code_runner.shutil.which", side_effect=[r"C:\mingw\bin\g++.exe"]), patch.object(runner, "_execute_raw", side_effect=fake_execute_raw):
                result = runner.run(
                    type("CppTeacherSession", (), {"username": "teacher", "role": "teacher", "is_teacher": True, "permissions": {"run.cpp": True, "web.access": False}})(),
                    project,
                    {
                        "path": "notes.txt",
                        "language": "python",
                        "code": "nur notizen",
                    },
                )

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["language"], "cpp")
            compile_command = [item.replace("\\", "/") for item in compile_commands[0]]
            self.assertTrue(any(item.endswith("/workspace/main.cpp") for item in compile_command))
            self.assertTrue(any(item.endswith("/workspace/math.cpp") for item in compile_command))

    def test_java_project_run_compiles_all_sources_and_uses_main_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            workspace = WorkspaceManager(config)
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                workspace,
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-java-main",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "java-main-run",
                "template": "java",
                "runtime": "java",
                "main_file": "app/Main.java",
            }
            root = workspace.project_root(project)
            root.mkdir(parents=True, exist_ok=True)
            (root / ".nova-school").mkdir(parents=True, exist_ok=True)
            (root / "app").mkdir(parents=True, exist_ok=True)
            (root / "app" / "Main.java").write_text(
                "package app;\npublic class Main {\n  public static void main(String[] args) {\n    Helper.say();\n  }\n}\n",
                encoding="utf-8",
            )
            (root / "app" / "Helper.java").write_text(
                "package app;\npublic class Helper {\n  static void say() {\n    System.out.println(\"hi\");\n  }\n}\n",
                encoding="utf-8",
            )
            compile_commands: list[list[str]] = []

            def fake_execute_raw(command, cwd, stdin_text, env, *, timeout_seconds=None):
                compile_commands.append(list(command))
                return _RawResult("", "", 0, 1, list(command))

            with patch("nova_school_server.code_runner.shutil.which", side_effect=[r"C:\Java\bin\javac.exe", r"C:\Java\bin\java.exe"]), patch.object(runner, "_execute_raw", side_effect=fake_execute_raw):
                result = runner.run(
                    type("JavaTeacherSession", (), {"username": "teacher", "role": "teacher", "is_teacher": True, "permissions": {"run.java": True, "web.access": False}})(),
                    project,
                    {
                        "path": "app/Helper.java",
                        "language": "python",
                        "code": "package app;\npublic class Helper {}\n",
                    },
                )

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["language"], "java")
            compile_command = [item.replace("\\", "/") for item in compile_commands[0]]
            self.assertTrue(any(item.endswith("/workspace/app/Main.java") for item in compile_command))
            self.assertTrue(any(item.endswith("/workspace/app/Helper.java") for item in compile_command))
            assert runner.last_command is not None
            self.assertEqual(runner.last_command[-1], "app.Main")

    def test_scheduler_serializes_same_student_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"scheduler_max_concurrent_global": 2, "scheduler_max_concurrent_student": 1}),
            )
            lease_one = runner.scheduler.acquire("student", "student")
            acquired: list[object] = []

            def worker() -> None:
                acquired.append(runner.scheduler.acquire("student", "student"))

            thread = threading.Thread(target=worker)
            thread.start()
            time.sleep(0.15)
            self.assertEqual(len(acquired), 0)
            runner.scheduler.release(lease_one)
            thread.join(timeout=2)
            self.assertEqual(len(acquired), 1)
            runner.scheduler.release(acquired[0])

    def test_container_base_command_disables_network_without_web_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            command = runner._container_base_command("docker", "python:3.12-slim", Path(tmp), Path(tmp) / "container-workspace", {"web.access": False})
            self.assertIn("none", command)
            self.assertNotIn("bridge", command)
            self.assertIn("--read-only", command)
            if os.name == "nt":
                self.assertNotIn("seccomp=", " ".join(command))
            else:
                self.assertIn("seccomp=", " ".join(command))

    def test_container_base_command_enables_bridge_with_web_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            command = runner._container_base_command("docker", "python:3.12-slim", Path(tmp), Path(tmp) / "container-workspace", {"web.access": True})
            self.assertIn("bridge", command)

    def test_container_base_command_includes_configured_oci_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({"container_oci_runtime": "runsc"}))
            command = runner._container_base_command("docker", "python:3.12-slim", Path(tmp), Path(tmp) / "container-workspace", {"web.access": False})
            self.assertIn("--runtime", command)
            self.assertIn("runsc", command)

    def test_container_base_command_converts_file_size_limit_from_kb_to_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({"container_file_size_limit_kb": 65536}))
            command = runner._container_base_command("docker", "python:3.12-slim", Path(tmp), Path(tmp) / "container-workspace", {"web.access": False})
            self.assertIn("fsize=67108864:67108864", command)

    def test_execution_env_requires_proxy_when_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({"web_proxy_required": True}))
            with self.assertRaises(PermissionError):
                runner._execution_env(Path(tmp), web_access=True)

    def test_containerized_env_does_not_forward_windows_host_path(self) -> None:
        env = {
            "PATH": r"C:\Windows\System32;C:\Python312",
            "SystemRoot": r"C:\Windows",
            "NOVA_SCHOOL_NETWORK": "off",
        }
        payload = CodeRunner._containerized_env(env)
        self.assertNotIn("PATH", payload)
        self.assertNotIn("SystemRoot", payload)
        self.assertEqual(payload["NOVA_SCHOOL_NETWORK"], "off")

    def test_container_runtime_error_message_explains_missing_docker_desktop_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            message = runner._container_runtime_error_message(
                "docker",
                "python:3.12-slim",
                "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.",
            )
            self.assertIn("Docker Desktop", message)
            self.assertIn("Linux-Container-Engine", message)
            self.assertIn("python:3.12-slim", message)

    def test_container_runtime_error_message_explains_internal_server_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            message = runner._container_runtime_error_message(
                "docker",
                "python:3.12-slim",
                "request returned 500 Internal Server Error for API route and version http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/_ping",
            )
            self.assertIn("500-Fehler", message)
            self.assertIn("Linux-Worker", message)
            self.assertIn("python:3.12-slim", message)

    def test_container_runtime_error_message_explains_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            message = runner._container_runtime_error_message(
                "docker",
                "python:3.12-slim",
                "Zeitlimit erreicht.",
            )
            self.assertIn("antwortet auf diesem Rechner nicht rechtzeitig", message)
            self.assertIn("Linux-Worker", message)
            self.assertIn("python:3.12-slim", message)

    def test_container_runtime_error_message_explains_linux_docker_socket_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            message = runner._container_runtime_error_message(
                "docker",
                "python:3.12-slim",
                'permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get "http://%2Fvar%2Frun%2Fdocker.sock/v1.24/info": dial unix /var/run/docker.sock: connect: permission denied',
            )
            self.assertIn("/var/run/docker.sock", message)
            self.assertIn("usermod -aG docker", message)
            self.assertIn("docker ps", message)
            self.assertIn("python:3.12-slim", message)

    def test_container_runtime_health_fails_fast_before_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            project = {
                "project_id": "proj-runtime-health",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "runtime-health",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }
            session = type("GuiSession", (), {"username": "student", "role": "student", "is_teacher": False, "permissions": {"run.python": True, "web.access": False}})()

            def fake_execute_raw(command, cwd, stdin_text, env, *, timeout_seconds=None):
                if len(command) >= 2 and command[1] == "info":
                    return _RawResult("", "request returned 500 Internal Server Error for API route and version http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/_ping", 1, 10, list(command))
                return _RawResult("[]", "", 0, 1, list(command))

            with patch.object(runner, "_execute_raw", side_effect=fake_execute_raw):
                result = runner.run(
                    session,
                    project,
                    {
                        "path": "main.py",
                        "language": "python",
                        "code": "print('ok')\n",
                    },
                )

            self.assertEqual(result["returncode"], 2)
            self.assertIn("Docker Desktop", result["stderr"])
            self.assertIn("500-Fehler", result["stderr"])

    def test_container_runtime_health_uses_generous_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            observed: dict[str, object] = {}

            def fake_execute_raw(command, cwd, stdin_text, env, *, timeout_seconds=None):
                observed["command"] = list(command)
                observed["timeout_seconds"] = timeout_seconds
                return _RawResult("24.0|linux", "", 0, 5, list(command))

            with patch.object(runner, "_execute_raw", side_effect=fake_execute_raw):
                healthy, message = runner._container_runtime_health("docker", "gcc:14")

            self.assertTrue(healthy)
            self.assertEqual(message, "")
            self.assertEqual(observed["command"], ["docker", "info", "--format", "{{.ServerVersion}}|{{.OSType}}"])
            self.assertEqual(observed["timeout_seconds"], 30)

    def test_run_bundle_auto_pulls_missing_container_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "container", "container_image_cpp": "gcc:14"}),
            )
            session = type(
                "CppTeacherSession",
                (),
                {
                    "username": "teacher",
                    "role": "teacher",
                    "is_teacher": True,
                    "permissions": {"run.cpp": True, "web.access": False},
                },
            )()
            commands: list[list[str]] = []

            def fake_execute_raw(command, cwd, stdin_text, env, *, timeout_seconds=None):
                commands.append(list(command))
                if len(command) >= 2 and command[1] == "info":
                    return _RawResult("24.0|linux", "", 0, 5, list(command))
                if len(command) >= 3 and command[1] == "image" and command[2] == "inspect":
                    return _RawResult("", "Error response from daemon: No such image: gcc:14", 1, 8, list(command))
                if len(command) >= 2 and command[1] == "pull":
                    return _RawResult("Pulled", "", 0, 120, list(command))
                return _RawResult("", "", 0, 6, list(command))

            with patch.object(runner, "_execute_raw", side_effect=fake_execute_raw):
                result = runner.run_bundle(
                    session,
                    {
                        "language": "cpp",
                        "main_file": "main.cpp",
                        "files": [{"path": "main.cpp", "content": "#include <iostream>\nint main(){ std::cout << 42; return 0; }\n"}],
                    },
                )

            self.assertEqual(result["returncode"], 0)
            self.assertTrue(any(command[1:] == ["pull", "gcc:14"] for command in commands))
            self.assertTrue(any("automatisch nachgeladen: gcc:14" in note for note in result["notes"]))

    def test_student_run_hides_operational_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            project = {
                "project_id": "proj-student-notes",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "student-notes",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }

            result = runner.run(
                _Session(),
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "print('ok')\n",
                },
            )

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["notes"], [])

    def test_teacher_run_keeps_operational_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            project = {
                "project_id": "proj-teacher-notes",
                "owner_type": "user",
                "owner_key": "teacher",
                "slug": "teacher-notes",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }

            result = runner.run(
                _TeacherSession(),
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "print('ok')\n",
                },
            )

            self.assertEqual(result["returncode"], 0)
            self.assertTrue(any("Container-Isolation aktiv" in note for note in result["notes"]))
            self.assertTrue(any("Run-Scheduler aktiv" in note for note in result["notes"]))

    def test_student_live_run_hides_operational_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            project = {
                "project_id": "proj-live-notes",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "live-notes",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }

            prepared = runner.prepare_live_run(
                _Session(),
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "print('ok')\n",
                },
            )

            self.assertIsNone(prepared.failed_returncode)
            self.assertEqual(prepared.notes, [])

    def test_backend_notes_omit_default_image_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            notes = runner._backend_notes({"web.access": False}, "container", "docker", "")
            self.assertTrue(notes)
            self.assertIn("Container-Isolation aktiv (docker).", notes[0])
            self.assertNotIn("default", notes[0])

    def test_python_executable_does_not_receive_py_launcher_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ObservedCodeRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            source = Path(tmp) / "main.py"
            source.write_text("print('ok')", encoding="utf-8")
            with patch("nova_school_server.code_runner.shutil.which", side_effect=[r"C:\Python312\python.exe"]):
                runner._run_python("run123", source, Path(tmp), "", {}, {}, {"web.access": True})
            self.assertIsNotNone(runner.last_command)
            assert runner.last_command is not None
            self.assertEqual(runner.last_command[0], r"C:\Python312\python.exe")
            self.assertNotIn("-3", runner.last_command)

    def test_run_python_supports_stdin_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-stdin",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "stdin-labor",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }

            result = runner.run(
                _TeacherSession(),
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "name = input('Name: ')\nprint(f'Hallo {name}!')\n",
                    "stdin": "Nova School\n",
                },
            )

            self.assertEqual(result["returncode"], 0)
            self.assertIn("Name:", result["stdout"])
            self.assertIn("Hallo Nova School!", result["stdout"])

    def test_run_python_reports_syntax_error_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-syntax",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "syntax-labor",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }

            result = runner.run(
                _TeacherSession(),
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "def greet(name) -> str:\n    return name\n\ndef broken) -> str:\n    return ''\n",
                },
            )

            self.assertEqual(result["returncode"], 1)
            self.assertIn("SyntaxError", result["stderr"])
            self.assertIsNone(runner.last_command)

    def test_prepare_live_python_reports_syntax_error_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = CodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            project = {
                "project_id": "proj-live-syntax",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "live-syntax-labor",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }

            prepared = runner.prepare_live_run(
                _TeacherSession(),
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "def broken) -> str:\n    return ''\n",
                },
            )

            self.assertEqual(prepared.failed_returncode, 1)
            self.assertIn("SyntaxError", prepared.prelude_stderr)

    def test_run_python_uses_bootstrap_and_dependency_env_with_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ObservedCodeRunner(
                config,
                _FakeToolSandbox(),
                WorkspaceManager(config),
                _FakeRepository({"runner_backend": "process", "unsafe_process_backend_enabled": True}),
            )
            source = Path(tmp) / "main.py"
            source.write_text("import demo\nprint(demo.value)\n", encoding="utf-8")
            (Path(tmp) / "requirements.txt").write_text("demo-package==1.0\n", encoding="utf-8")

            def fake_execute_raw(command, cwd, stdin_text, env, *, timeout_seconds=None):
                if "-m" in command and "pip" in command:
                    deps_root = Path(cwd) / ".nova-python" / "site-packages"
                    deps_root.mkdir(parents=True, exist_ok=True)
                    (deps_root / "demo.py").write_text("value = 1\n", encoding="utf-8")
                return _RawResult("", "", 0, 1, list(command))

            with patch("nova_school_server.code_runner.shutil.which", side_effect=[r"C:\Python312\python.exe", r"C:\Python312\python.exe"]), patch.object(runner, "_execute_raw", side_effect=fake_execute_raw):
                runner._run_python("run123", source, Path(tmp), "", {}, {}, {"web.access": True})

            self.assertIsNotNone(runner.last_command)
            self.assertIsNotNone(runner.last_env)
            assert runner.last_command is not None
            assert runner.last_env is not None
            self.assertTrue(runner.last_command[-1].endswith("python_entry.py"))
            self.assertEqual(runner.last_env["NOVA_SCHOOL_ENTRYPOINT"], str(source))
            self.assertTrue(runner.last_env["NOVA_SCHOOL_PYTHON_DEPS"].endswith(str(Path(".nova-python") / "site-packages")))

    def test_containerized_python_gui_returns_preview_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            project = {
                "project_id": "proj-gui",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "gui-labor",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }
            session = type("GuiSession", (), {"username": "student", "role": "student", "is_teacher": False, "permissions": {"run.python": True, "web.access": True}})()

            result = runner.run(
                session,
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "import tkinter as tk\nroot = tk.Tk()\nroot.mainloop()\n",
                },
            )

            self.assertEqual(result["returncode"], 0)
            self.assertTrue(result["preview_path"].endswith("/gui-preview.png"))
            self.assertIsNotNone(runner.last_container_command)
            assert runner.last_container_command is not None
            self.assertIn("python_gui_snapshot.sh", " ".join(runner.last_container_command))
            self.assertEqual(result["notes"], [])

    def test_containerized_python_mainloop_without_direct_import_uses_gui_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ServerConfig.from_base_path(Path(tmp))
            runner = _ContainerObservedRunner(config, _FakeToolSandbox(), WorkspaceManager(config), _FakeRepository({}))
            project = {
                "project_id": "proj-mainloop",
                "owner_type": "user",
                "owner_key": "student",
                "slug": "mainloop-labor",
                "template": "python",
                "runtime": "python",
                "main_file": "main.py",
            }
            session = type("GuiSession", (), {"username": "student", "role": "student", "is_teacher": False, "permissions": {"run.python": True, "web.access": True}})()

            result = runner.run(
                session,
                project,
                {
                    "path": "main.py",
                    "language": "python",
                    "code": "from appkit import build_view\nview = build_view()\nview.mainloop()\n",
                },
            )

            self.assertEqual(result["returncode"], 0)
            self.assertTrue(result["preview_path"].endswith("/gui-preview.png"))
            self.assertIsNotNone(runner.last_container_command)
            assert runner.last_container_command is not None
            self.assertIn("python_gui_snapshot.sh", " ".join(runner.last_container_command))


if __name__ == "__main__":
    unittest.main()
