# Vollständige Systemdokumentation


# 1. Strategische Architektur

## Design-Philosophie
Zero-Dependency:
- maximale Stabilität
- minimale Angriffsfläche (CVE)
- deterministisches Verhalten

## Technologie-Stack
- Python 3.12 → Orchestrierung
- C++ / Rust → Performance & Sicherheit

## Datenbank
- SQLite (WAL-Modus)
- kein externer Server notwendig

## Skalierung
- Thread-basiert
- optimiert für lokale Hardware


# 2. Sicherheits-Framework

## Sandbox
- Docker / Podman Isolation

## Seccomp
- deny-by-default

## Resource Guards
- PID Limits
- Memory Caps
- Read-only Filesystem

## Netzwerk
--network none


# 3. KI-Inferenz & Ressourcenmanagement

## Lifecycle
- Subprozess Start
- Monitoring
- Idle Kill

## Modelle
- GGUF
- LiteRTLM

## Ziel
stabile Offline-Inferenz


# 4. Operative Roadmap

## Build
Source → Container

## Tests
- Unit
- Integration

## Troubleshooting
- Docker Rechte
- RAM Limits

## API
Frontend ↔ Backend sauber getrennt

# Code Overview


## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\ai_service.py
Imports:
- __future__
- json
- os
- re
- shutil
- socket
- subprocess
- threading
- time
- zipfile
- pathlib
- typing
- urllib.error
- urllib.parse
- urllib.request
- archive_utils
- database

Class LlamaCppService
- __init__(self, repository)
- model_roots(self)
- model_root(self)
- explicit_model_path(self)
- model_label(self)
- max_tokens(self)
- top_k(self)
- temperature(self)
- random_seed(self)
- backend(self)
- ctx_size(self)
- gpu_layers(self)
- threads(self)
- sleep_idle_seconds(self)
- port(self)
- server_url(self)
- explicit_binary_path(self)
- generation_options(self)
- local_model_files(self)
- resolved_model_path(self)
- resolved_model_label(self)
- _discover_binary_candidates(self)
- _request_json(self, url)
- _latest_release(self)
- _download_binary(self)
- _ensure_binary_path(self)
- _desired_process_key(self)
- _build_command(self, binary_path, model_path)
- _poll_health(self)
- _read_failure_details(self, fallback)
- _stop_process_locked(self)
- close(self)
- _cancel_idle_timer_locked(self)
- _schedule_idle_shutdown(self)
- ensure_server_ready(self)
- complete(self)
- prepare_direct_completion(self)
- complete_direct_completion(self)
- status(self)

Class LiteRTLmService
- __init__(self, repository)
- model_roots(self)
- explicit_model_path(self)
- model_label(self)
- backend(self)
- max_tokens(self)
- top_k(self)
- temperature(self)
- random_seed(self)
- sleep_idle_seconds(self)
- port(self)
- server_url(self)
- explicit_binary_path(self)
- explicit_home_path(self)
- generation_options(self)
- local_model_files(self)
- resolved_model_path(self)
- resolved_model_label(self)
- resolved_model_id(self)
- resolved_home_root(self)
- lit_root(self)
- model_registry_dir(self)
- registry_model_path(self)
- registry_cache_path(self)
- _explicit_binary_directory(self)
- _discover_binary_candidates(self)
- _ensure_binary_path(self)
- _register_model_file(self, target, source)
- ensure_model_registered(self)
- _desired_process_key(self)
- _build_command(self, binary_path)
- _request_json(self, url)
- _probe_server(self)
- _read_failure_details(self, fallback)
- _stop_process_locked(self)
- close(self)
- _cancel_idle_timer_locked(self)
- _schedule_idle_shutdown(self)
- ensure_server_ready(self)
- _compose_prompt(self)
- _build_run_command(self, binary_path, model_path, prompt_file)
- _cli_environment(self)
- _prompt_file_path(self)
- _extract_cli_response_text(self, raw_output)
- _clean_cli_output(self, raw_output)
- _extract_response_text(self, response)
- _request_completion(self, payload)
- complete(self)
- prepare_direct_completion(self)
- complete_direct_completion(self)
- status(self)

Class LocalAIService
- __init__(self, repository)
- __getattr__(self, name)
- provider_id(self)
- engine_id(self)
- _provider_preference(self)
- _active_service(self)
- close(self)
- complete(self)
- prepare_direct_completion(self)
- complete_direct_completion(self)
- status(self)

Function _clamp_int
Args: ['value', 'default', 'minimum', 'maximum']

Function _clamp_float
Args: ['value', 'default', 'minimum', 'maximum']

Function _sanitize_model_text
Args: ['value']

Function _normalize_prompt_text
Args: ['text']

Function _estimate_token_count
Args: ['text']

Function _trim_text_middle
Args: ['text']

Function _prepare_prompt_with_budget
Args: ['prompt']

Function _unwrap_short_reply
Args: ['value']

Function _extract_exact_short_reply_target
Args: ['prompt']

Function _normalize_model_label
Args: ['value']

Function _sanitize_model_id
Args: ['value']

Function _same_drive
Args: ['left', 'right']

Function _first_existing_path
Args: ['candidates']

Function __init__
Args: ['self', 'repository']

Function model_roots
Args: ['self']

Function model_root
Args: ['self']

Function explicit_model_path
Args: ['self']

Function model_label
Args: ['self']

Function max_tokens
Args: ['self']

Function top_k
Args: ['self']

Function temperature
Args: ['self']

Function random_seed
Args: ['self']

Function backend
Args: ['self']

Function ctx_size
Args: ['self']

Function gpu_layers
Args: ['self']

Function threads
Args: ['self']

Function sleep_idle_seconds
Args: ['self']

Function port
Args: ['self']

Function server_url
Args: ['self']

Function explicit_binary_path
Args: ['self']

Function generation_options
Args: ['self']

Function local_model_files
Args: ['self']

Function resolved_model_path
Args: ['self']

Function resolved_model_label
Args: ['self']

Function _discover_binary_candidates
Args: ['self']

Function _request_json
Args: ['self', 'url']

Function _latest_release
Args: ['self']

Function _download_binary
Args: ['self']

Function _ensure_binary_path
Args: ['self']

Function _desired_process_key
Args: ['self']

Function _build_command
Args: ['self', 'binary_path', 'model_path']

Function _poll_health
Args: ['self']

Function _read_failure_details
Args: ['self', 'fallback']

Function _stop_process_locked
Args: ['self']

Function close
Args: ['self']

Function _cancel_idle_timer_locked
Args: ['self']

Function _schedule_idle_shutdown
Args: ['self']

Function ensure_server_ready
Args: ['self']

Function complete
Args: ['self']

Function prepare_direct_completion
Args: ['self']

Function complete_direct_completion
Args: ['self']

Function status
Args: ['self']

Function __init__
Args: ['self', 'repository']

Function model_roots
Args: ['self']

Function explicit_model_path
Args: ['self']

Function model_label
Args: ['self']

Function backend
Args: ['self']

Function max_tokens
Args: ['self']

Function top_k
Args: ['self']

Function temperature
Args: ['self']

Function random_seed
Args: ['self']

Function sleep_idle_seconds
Args: ['self']

Function port
Args: ['self']

Function server_url
Args: ['self']

Function explicit_binary_path
Args: ['self']

Function explicit_home_path
Args: ['self']

Function generation_options
Args: ['self']

Function local_model_files
Args: ['self']

Function resolved_model_path
Args: ['self']

Function resolved_model_label
Args: ['self']

Function resolved_model_id
Args: ['self']

Function resolved_home_root
Args: ['self']

Function lit_root
Args: ['self']

Function model_registry_dir
Args: ['self']

Function registry_model_path
Args: ['self']

Function registry_cache_path
Args: ['self']

Function _explicit_binary_directory
Args: ['self']

Function _discover_binary_candidates
Args: ['self']

Function _ensure_binary_path
Args: ['self']

Function _register_model_file
Args: ['self', 'target', 'source']

Function ensure_model_registered
Args: ['self']

Function _desired_process_key
Args: ['self']

Function _build_command
Args: ['self', 'binary_path']

Function _request_json
Args: ['self', 'url']

Function _probe_server
Args: ['self']

Function _read_failure_details
Args: ['self', 'fallback']

Function _stop_process_locked
Args: ['self']

Function close
Args: ['self']

Function _cancel_idle_timer_locked
Args: ['self']

Function _schedule_idle_shutdown
Args: ['self']

Function ensure_server_ready
Args: ['self']

Function _compose_prompt
Args: ['self']

Function _build_run_command
Args: ['self', 'binary_path', 'model_path', 'prompt_file']

Function _cli_environment
Args: ['self']

Function _prompt_file_path
Args: ['self']

Function _extract_cli_response_text
Args: ['self', 'raw_output']

Function _clean_cli_output
Args: ['self', 'raw_output']

Function _extract_response_text
Args: ['self', 'response']

Function _request_completion
Args: ['self', 'payload']

Function complete
Args: ['self']

Function prepare_direct_completion
Args: ['self']

Function complete_direct_completion
Args: ['self']

Function status
Args: ['self']

Function __init__
Args: ['self', 'repository']

Function __getattr__
Args: ['self', 'name']

Function provider_id
Args: ['self']

Function engine_id
Args: ['self']

Function _provider_preference
Args: ['self']

Function _active_service
Args: ['self']

Function close
Args: ['self']

Function complete
Args: ['self']

Function prepare_direct_completion
Args: ['self']

Function complete_direct_completion
Args: ['self']

Function status
Args: ['self']

Function sort_key
Args: ['path']

Function shutdown
Args: []

Function sort_key
Args: ['path']

Function shutdown
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\analysis_archive_builder.py
Imports:
- __future__
- argparse
- subprocess
- zipfile
- dataclasses
- pathlib

Class SourceAnalysisArchiveBuildResult

Function detect_project_version
Args: ['base_path']

Function build_source_analysis_archive
Args: ['base_path']

Function _iter_source_analysis_files
Args: ['base_path']

Function _git_tracked_files
Args: ['base_path']

Function _should_skip_source_analysis_file
Args: ['relative_path']

Function _is_allowed_source_file
Args: ['relative_path']

Function _is_probably_text_file
Args: ['path']

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\archive_utils.py
Imports:
- __future__
- os
- stat
- zipfile
- pathlib

Function extract_zip_safely
Args: ['archive', 'destination']

Function _validated_zip_member_path
Args: ['member']

Function _zip_entry_is_symlink
Args: ['member']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\auth.py
Imports:
- __future__
- base64
- hashlib
- hmac
- os
- dataclasses
- typing
- database
- permissions

Class SessionContext
- username(self)
- role(self)
- is_teacher(self)
- is_admin(self)
- group_ids(self)
- to_dict(self)

Class AuthService
- __init__(self, repository, security_plane, tenant_id, session_ttl_seconds)
- ensure_user(self, username, password, role, display_name, permissions)
- create_user(self, username, password, role, display_name, permissions)
- login(self, username, password)
- session_from_token(self, token)
- logout(self, token_id)

Function hash_password
Args: ['password']

Function verify_password
Args: ['password', 'salt_text', 'hash_text']

Function username
Args: ['self']

Function role
Args: ['self']

Function is_teacher
Args: ['self']

Function is_admin
Args: ['self']

Function group_ids
Args: ['self']

Function to_dict
Args: ['self']

Function __init__
Args: ['self', 'repository', 'security_plane', 'tenant_id', 'session_ttl_seconds']

Function ensure_user
Args: ['self', 'username', 'password', 'role', 'display_name', 'permissions']

Function create_user
Args: ['self', 'username', 'password', 'role', 'display_name', 'permissions']

Function login
Args: ['self', 'username', 'password']

Function session_from_token
Args: ['self', 'token']

Function logout
Args: ['self', 'token_id']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\codedump_tools.py
Imports:
- __future__
- dataclasses
- pathlib
- typing
- zipfile
- argparse

Class DumpConfig

Class DumpEntry

Class DumpResult

Function is_ignored
Args: ['path', 'config']

Function is_code_file
Args: ['path', 'config']

Function detect_language
Args: ['path']

Function generate_tree
Args: ['file_paths']

Function dump_zip_to_markdown
Args: ['zip_path', 'output_md', 'config']

Function dump_target_to_markdown
Args: ['target', 'output_md', 'config']

Function collect_directory_dump
Args: ['project_root']

Function collect_zip_dump
Args: ['zip_path']

Function render_dump_markdown
Args: ['result']

Function _entry_from_path
Args: ['path', 'relative_path', 'config']

Function _entry_from_zip
Args: ['archive', 'info', 'config']

Function _entry_from_bytes
Args: ['relative_path', 'raw', 'size', 'config']

Function _summarize_paths
Args: ['paths']

Function _summary_label_for_path
Args: ['path']

Function _is_dump_artifact
Args: ['path']

Function _is_directory_like_target
Args: ['target']

Function default_output_path
Args: ['target']

Function config_for_profile
Args: ['profile']

Function default_output_path_for_profile
Args: ['target', 'profile']

Function main
Args: []

Function render
Args: ['node', 'prefix']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\code_runner.py
Imports:
- __future__
- hashlib
- os
- re
- shlex
- shutil
- subprocess
- threading
- time
- textwrap
- uuid
- dataclasses
- pathlib
- typing
- config
- container_seccomp
- permissions
- workspace

Class RunResult
- to_dict(self)

Class LivePreparedRun

Class SchedulerLease

Class RunScheduler
- __init__(self, repository)
- acquire(self, owner_username, role)
- release(self, lease)
- _can_activate(self, owner_username, role)
- _global_limit(self)
- _per_owner_limit(self, role)
- _setting_int(self, key, default)
- _priority_for_role(role)

Class CodeRunner
- __init__(self, config, tool_sandbox, workspace_manager, repository)
- run(self, session, project, payload)
- run_bundle(self, session, payload)
- prepare_live_run(self, session, project, payload)
- _resolve_language(self, project, payload)
- _resolve_bundle_language(self, payload)
- _prepare_source_file(self, project, payload, language, run_root)
- _prepare_bundle_workspace(self, payload, language, run_root)
- _prepare_execution_workspace(self, project, payload, language, project_root, run_root)
- _resolve_project_entry_path(self, project, payload, language, runtime_root)
- _resolve_project_entry_relative_path(self, project, payload, language)
- _project_source_files(project_root, suffixes)
- _java_main_class(self, source_path, project_root)
- _copy_project_tree(self, project_root, runtime_root)
- _safe_relative_path(path_text)
- _prepare_html_preview(self, project, payload, project_root, run_root)
- _resolve_html_preview_entry(self, project, payload, preview_root, source_path)
- _detect_python_gui_frameworks(self, language, source_path, payload)
- _read_source_text(path)
- _python_syntax_error(self, source_path)
- _python_requirements_file(workspace_root)
- _python_dependency_cache_dir(self, requirements_path, backend_marker)
- _restore_dependency_cache(target_root, cache_root)
- _store_dependency_cache(source_root, cache_root)
- _write_python_bootstrap(self, workspace_root)
- _is_python_traceback_wrapper_line(line)
- _sanitize_python_stderr(self, stderr)
- _python_entry_env(self, env, entrypoint_path, deps_path)
- _run_containerized(self, run_id, language, source_path, run_root, project_root, stdin_text, env, tool_session, permissions, payload)
- _run_python(self, run_id, source_path, project_root, stdin_text, env, tool_session, permissions)
- _run_node_like(self, run_id, language, source_path, project_root, stdin_text, env, tool_session, permissions)
- _run_cpp(self, run_id, source_path, run_root, project_root, stdin_text, env, tool_session, permissions)
- _run_java(self, run_id, source_path, run_root, project_root, stdin_text, env, tool_session, permissions)
- _run_rust(self, run_id, source_path, run_root, project_root, stdin_text, env, tool_session, permissions)
- _run_npm(self, run_id, project_root, payload, stdin_text, env, tool_session, permissions)
- _ensure_python_dependencies_process(self, workspace_root, env, permissions)
- _ensure_python_dependencies_container(self, runtime_executable, image, container_workspace, env, permissions)
- _container_error_is_missing_image(raw_error)
- _ensure_container_image_available(self, runtime_executable, image, cwd)
- _ensure_python_gui_container_image(self, runtime_executable, base_image, permissions)
- _prepare_python_gui_scripts(self, container_workspace, container_source_path)
- _prepare_live_process(self, session_id, run_id, language, source_path, run_root, project_root, env, tool_session, permissions, payload)
- _prepare_live_containerized(self, session_id, run_id, language, source_path, run_root, project_root, env, tool_session, permissions, payload)
- _execute(self, run_id, language, command, cwd, stdin_text, env, tool_session, permissions)
- _execute_container(self, run_id, language, runtime_executable, image, inner_command, project_root, container_workspace, stdin_text, env, tool_session, permissions)
- _execute_container_raw(self, runtime_executable, image, inner_command, project_root, container_workspace, stdin_text, env, permissions)
- _prepare_container_workspace(self, source_root, run_root)
- _mirror_tree_securely(self, source_root, target_root, ignored_names)
- _copy_tree_entries_securely(self, source_dir, target_dir, ignored_names)
- _is_link_like(path)
- _execution_env(self, project_root, web_access)
- _containerized_env(env)
- _container_file_size_limit_bytes(self)
- _network_notes(self, permissions)
- _backend_notes(self, permissions, backend, runtime, image)
- _runner_backend(self, payload)
- resolve_backend(self, session, payload)
- _session_role(session)
- _session_can_view_operational_notes(self, session)
- _visible_notes_for_session(self, session, notes)
- _finalize_run_result(self, session, result, lease)
- _finalize_prepared_run(self, session, prepared, lease)
- _container_runtime(self, payload)
- _container_image(self, language, payload)
- _container_base_command(self, runtime_executable, image, source_root, workspace_root, permissions, tty)
- _container_wrapped_command(base_command, inner_command)
- _container_path(self, project_root, target)
- _setting(self, key, default)
- _setting_bool(self, key, default)
- _unsafe_process_backend_enabled(self)
- _container_seccomp_option(self, runtime_name)
- _scheduler_notes(lease)
- _default_filename(language)
- _execute_raw(self, command, cwd, stdin_text, env)
- _container_runtime_error_message(self, runtime_executable, image, raw_error)
- _container_runtime_health_timeout_seconds(self)
- _container_runtime_health(self, runtime_executable, image)

Class _RawResult

Function to_dict
Args: ['self']

Function __init__
Args: ['self', 'repository']

Function acquire
Args: ['self', 'owner_username', 'role']

Function release
Args: ['self', 'lease']

Function _can_activate
Args: ['self', 'owner_username', 'role']

Function _global_limit
Args: ['self']

Function _per_owner_limit
Args: ['self', 'role']

Function _setting_int
Args: ['self', 'key', 'default']

Function _priority_for_role
Args: ['role']

Function __init__
Args: ['self', 'config', 'tool_sandbox', 'workspace_manager', 'repository']

Function run
Args: ['self', 'session', 'project', 'payload']

Function run_bundle
Args: ['self', 'session', 'payload']

Function prepare_live_run
Args: ['self', 'session', 'project', 'payload']

Function _resolve_language
Args: ['self', 'project', 'payload']

Function _resolve_bundle_language
Args: ['self', 'payload']

Function _prepare_source_file
Args: ['self', 'project', 'payload', 'language', 'run_root']

Function _prepare_bundle_workspace
Args: ['self', 'payload', 'language', 'run_root']

Function _prepare_execution_workspace
Args: ['self', 'project', 'payload', 'language', 'project_root', 'run_root']

Function _resolve_project_entry_path
Args: ['self', 'project', 'payload', 'language', 'runtime_root']

Function _resolve_project_entry_relative_path
Args: ['self', 'project', 'payload', 'language']

Function _project_source_files
Args: ['project_root', 'suffixes']

Function _java_main_class
Args: ['self', 'source_path', 'project_root']

Function _copy_project_tree
Args: ['self', 'project_root', 'runtime_root']

Function _safe_relative_path
Args: ['path_text']

Function _prepare_html_preview
Args: ['self', 'project', 'payload', 'project_root', 'run_root']

Function _resolve_html_preview_entry
Args: ['self', 'project', 'payload', 'preview_root', 'source_path']

Function _detect_python_gui_frameworks
Args: ['self', 'language', 'source_path', 'payload']

Function _read_source_text
Args: ['path']

Function _python_syntax_error
Args: ['self', 'source_path']

Function _python_requirements_file
Args: ['workspace_root']

Function _python_dependency_cache_dir
Args: ['self', 'requirements_path', 'backend_marker']

Function _restore_dependency_cache
Args: ['target_root', 'cache_root']

Function _store_dependency_cache
Args: ['source_root', 'cache_root']

Function _write_python_bootstrap
Args: ['self', 'workspace_root']

Function _is_python_traceback_wrapper_line
Args: ['line']

Function _sanitize_python_stderr
Args: ['self', 'stderr']

Function _python_entry_env
Args: ['self', 'env', 'entrypoint_path', 'deps_path']

Function _run_containerized
Args: ['self', 'run_id', 'language', 'source_path', 'run_root', 'project_root', 'stdin_text', 'env', 'tool_session', 'permissions', 'payload']

Function _run_python
Args: ['self', 'run_id', 'source_path', 'project_root', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _run_node_like
Args: ['self', 'run_id', 'language', 'source_path', 'project_root', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _run_cpp
Args: ['self', 'run_id', 'source_path', 'run_root', 'project_root', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _run_java
Args: ['self', 'run_id', 'source_path', 'run_root', 'project_root', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _run_rust
Args: ['self', 'run_id', 'source_path', 'run_root', 'project_root', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _run_npm
Args: ['self', 'run_id', 'project_root', 'payload', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _ensure_python_dependencies_process
Args: ['self', 'workspace_root', 'env', 'permissions']

Function _ensure_python_dependencies_container
Args: ['self', 'runtime_executable', 'image', 'container_workspace', 'env', 'permissions']

Function _container_error_is_missing_image
Args: ['raw_error']

Function _ensure_container_image_available
Args: ['self', 'runtime_executable', 'image', 'cwd']

Function _ensure_python_gui_container_image
Args: ['self', 'runtime_executable', 'base_image', 'permissions']

Function _prepare_python_gui_scripts
Args: ['self', 'container_workspace', 'container_source_path']

Function _prepare_live_process
Args: ['self', 'session_id', 'run_id', 'language', 'source_path', 'run_root', 'project_root', 'env', 'tool_session', 'permissions', 'payload']

Function _prepare_live_containerized
Args: ['self', 'session_id', 'run_id', 'language', 'source_path', 'run_root', 'project_root', 'env', 'tool_session', 'permissions', 'payload']

Function _execute
Args: ['self', 'run_id', 'language', 'command', 'cwd', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _execute_container
Args: ['self', 'run_id', 'language', 'runtime_executable', 'image', 'inner_command', 'project_root', 'container_workspace', 'stdin_text', 'env', 'tool_session', 'permissions']

Function _execute_container_raw
Args: ['self', 'runtime_executable', 'image', 'inner_command', 'project_root', 'container_workspace', 'stdin_text', 'env', 'permissions']

Function _prepare_container_workspace
Args: ['self', 'source_root', 'run_root']

Function _mirror_tree_securely
Args: ['self', 'source_root', 'target_root', 'ignored_names']

Function _copy_tree_entries_securely
Args: ['self', 'source_dir', 'target_dir', 'ignored_names']

Function _is_link_like
Args: ['path']

Function _execution_env
Args: ['self', 'project_root', 'web_access']

Function _containerized_env
Args: ['env']

Function _container_file_size_limit_bytes
Args: ['self']

Function _network_notes
Args: ['self', 'permissions']

Function _backend_notes
Args: ['self', 'permissions', 'backend', 'runtime', 'image']

Function _runner_backend
Args: ['self', 'payload']

Function resolve_backend
Args: ['self', 'session', 'payload']

Function _session_role
Args: ['session']

Function _session_can_view_operational_notes
Args: ['self', 'session']

Function _visible_notes_for_session
Args: ['self', 'session', 'notes']

Function _finalize_run_result
Args: ['self', 'session', 'result', 'lease']

Function _finalize_prepared_run
Args: ['self', 'session', 'prepared', 'lease']

Function _container_runtime
Args: ['self', 'payload']

Function _container_image
Args: ['self', 'language', 'payload']

Function _container_base_command
Args: ['self', 'runtime_executable', 'image', 'source_root', 'workspace_root', 'permissions', 'tty']

Function _container_wrapped_command
Args: ['base_command', 'inner_command']

Function _container_path
Args: ['self', 'project_root', 'target']

Function _setting
Args: ['self', 'key', 'default']

Function _setting_bool
Args: ['self', 'key', 'default']

Function _unsafe_process_backend_enabled
Args: ['self']

Function _container_seccomp_option
Args: ['self', 'runtime_name']

Function _scheduler_notes
Args: ['lease']

Function _default_filename
Args: ['language']

Function _execute_raw
Args: ['self', 'command', 'cwd', 'stdin_text', 'env']

Function _container_runtime_error_message
Args: ['self', 'runtime_executable', 'image', 'raw_error']

Function _container_runtime_health_timeout_seconds
Args: ['self']

Function _container_runtime_health
Args: ['self', 'runtime_executable', 'image']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\collaboration.py
Imports:
- __future__
- json
- time
- uuid
- typing
- database
- workspace

Class NotebookCollaborationService
- __init__(self, repository, workspace_manager)
- snapshot(self, project)
- heartbeat(self, session, project, cursor)
- sync(self, session, project, cells, base_revision, cursor)
- _init_schema(self)
- _ensure_state(self, project)
- _store_state(self, project, revision, cells, updated_by, base_revision)
- _snapshot_at(self, project_id, revision)
- _active_presence(self, project_id)
- _normalize_cell(cell, index)
- _merge_cells(cls, base_cells, current_cells, incoming_cells)

Function __init__
Args: ['self', 'repository', 'workspace_manager']

Function snapshot
Args: ['self', 'project']

Function heartbeat
Args: ['self', 'session', 'project', 'cursor']

Function sync
Args: ['self', 'session', 'project', 'cells', 'base_revision', 'cursor']

Function _init_schema
Args: ['self']

Function _ensure_state
Args: ['self', 'project']

Function _store_state
Args: ['self', 'project', 'revision', 'cells', 'updated_by', 'base_revision']

Function _snapshot_at
Args: ['self', 'project_id', 'revision']

Function _active_presence
Args: ['self', 'project_id']

Function _normalize_cell
Args: ['cell', 'index']

Function _merge_cells
Args: ['cls', 'base_cells', 'current_cells', 'incoming_cells']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\config.py
Imports:
- __future__
- json
- os
- dataclasses
- pathlib
- typing

Class ServerConfig
- from_base_path(cls, base_path)

Function resolve_package_path
Args: ['base_path']

Function load_server_config_payload
Args: ['base_path']

Function save_server_config_payload
Args: ['base_path', 'updates']

Function active_runtime_config
Args: ['config']

Function stored_runtime_config
Args: ['base_path', 'config']

Function runtime_config_requires_restart
Args: ['active', 'stored']

Function from_base_path
Args: ['cls', 'base_path']

Function env_or_payload
Args: ['name', 'key', 'default']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\container_seccomp.py
Imports:
- __future__
- os
- pathlib

Function resolve_seccomp_profile_option
Args: ['profile_path', 'runtime_name']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\curriculum.py
Imports:
- __future__
- copy
- hashlib
- html
- hmac
- io
- json
- re
- time
- uuid
- zipfile
- typing
- curriculum_catalog
- curriculum_certificate_pdf
- material_studio
- material_studio
- material_studio

Class CurriculumService
- __init__(self, repository)
- _catalog_courses(self)
- _catalog_course(self, course_id)
- active_bundle_id(self)
- _active_bundle_row(self)
- active_bundle(self)
- _active_bundle_courses(self)
- _active_bundle_course(self, course_id)
- _active_bundle_material_presets(self)
- _active_bundle_mentor_rules(self)
- _resolve_mentor_rule(self, course_id, module_id)
- _custom_courses(self)
- _custom_course(self, course_id)
- _slug(value)
- _listify(value)
- _normalize_question(self, raw)
- _normalize_course_definition(self, payload)
- save_custom_course(self, session, payload)
- validate_bundle_archive(self, archive_bytes)
- import_bundle_archive(self, session)
- activate_bundle(self, session, bundle_id)
- rollback_bundle(self, session)
- list_bundles(self)
- _bundle_payload(self, bundle_id)
- _bundle_row_payload(self, row)
- _bundle_preview_payload(self, bundle)
- _parse_bundle_archive(self, archive_bytes)
- _decode_bundle_json(archive, member)
- _load_bundle_section(self, archive, folder_name, normalizer)
- _load_bundle_raw_section(self, archive, folder_name)
- _ensure_unique_bundle_entries(items)
- _normalize_bundle_course(self, payload)
- _normalize_material_preset(payload)
- _normalize_mentor_rule(payload)
- _verify_bundle_signature(self, manifest, courses, material_presets, mentor_rules, signature)
- _canonical_bundle_payload(manifest, courses, material_presets, mentor_rules)
- dashboard(self, session)
- material_studio_instruction_preset_catalog(self)
- resolve_material_studio_instruction_preset(self, preset_key)
- mentor_context(self, session)
- attempt_history(self, course_id, username)
- set_release(self, session, course_id, scope_type, scope_key, enabled, note)
- submit_assessment(self, session, course_id, module_id, assessment_kind, answers)
- build_certificate_pdf(self, session, course_id, school_name)
- prepare_certificate_metadata(self, username, course_id)
- certificate_by_id(self, certificate_id)
- render_certificate_verification_page(self, certificate_id, school_name)
- _ensure_schema(self)
- _sanitize_user(user)
- _resolve_release(self, session, course_id)
- _query_releases(self, course_id, scope_type, scope_keys)
- _list_releases(self)
- _release_payload(self, release_id)
- _release_row_payload(self, row)
- _latest_attempts(self, username, course_id)
- _certificate_for(self, username, course_id)
- _course_payload(self, session, course)
- _attempt_count(self, username, course_id, module_id, assessment_kind)
- _resolve_module(course, module_id, assessment_kind)
- _grade_assessment(module, answers, pass_ratio)
- _refresh_certificate(self, username, course_id, final_grading)
- _learner_overview(self)

Function __init__
Args: ['self', 'repository']

Function _catalog_courses
Args: ['self']

Function _catalog_course
Args: ['self', 'course_id']

Function active_bundle_id
Args: ['self']

Function _active_bundle_row
Args: ['self']

Function active_bundle
Args: ['self']

Function _active_bundle_courses
Args: ['self']

Function _active_bundle_course
Args: ['self', 'course_id']

Function _active_bundle_material_presets
Args: ['self']

Function _active_bundle_mentor_rules
Args: ['self']

Function _resolve_mentor_rule
Args: ['self', 'course_id', 'module_id']

Function _custom_courses
Args: ['self']

Function _custom_course
Args: ['self', 'course_id']

Function _slug
Args: ['value']

Function _listify
Args: ['value']

Function _normalize_question
Args: ['self', 'raw']

Function _normalize_course_definition
Args: ['self', 'payload']

Function save_custom_course
Args: ['self', 'session', 'payload']

Function validate_bundle_archive
Args: ['self', 'archive_bytes']

Function import_bundle_archive
Args: ['self', 'session']

Function activate_bundle
Args: ['self', 'session', 'bundle_id']

Function rollback_bundle
Args: ['self', 'session']

Function list_bundles
Args: ['self']

Function _bundle_payload
Args: ['self', 'bundle_id']

Function _bundle_row_payload
Args: ['self', 'row']

Function _bundle_preview_payload
Args: ['self', 'bundle']

Function _parse_bundle_archive
Args: ['self', 'archive_bytes']

Function _decode_bundle_json
Args: ['archive', 'member']

Function _load_bundle_section
Args: ['self', 'archive', 'folder_name', 'normalizer']

Function _load_bundle_raw_section
Args: ['self', 'archive', 'folder_name']

Function _ensure_unique_bundle_entries
Args: ['items']

Function _normalize_bundle_course
Args: ['self', 'payload']

Function _normalize_material_preset
Args: ['payload']

Function _normalize_mentor_rule
Args: ['payload']

Function _verify_bundle_signature
Args: ['self', 'manifest', 'courses', 'material_presets', 'mentor_rules', 'signature']

Function _canonical_bundle_payload
Args: ['manifest', 'courses', 'material_presets', 'mentor_rules']

Function dashboard
Args: ['self', 'session']

Function material_studio_instruction_preset_catalog
Args: ['self']

Function resolve_material_studio_instruction_preset
Args: ['self', 'preset_key']

Function mentor_context
Args: ['self', 'session']

Function attempt_history
Args: ['self', 'course_id', 'username']

Function set_release
Args: ['self', 'session', 'course_id', 'scope_type', 'scope_key', 'enabled', 'note']

Function submit_assessment
Args: ['self', 'session', 'course_id', 'module_id', 'assessment_kind', 'answers']

Function build_certificate_pdf
Args: ['self', 'session', 'course_id', 'school_name']

Function prepare_certificate_metadata
Args: ['self', 'username', 'course_id']

Function certificate_by_id
Args: ['self', 'certificate_id']

Function render_certificate_verification_page
Args: ['self', 'certificate_id', 'school_name']

Function _ensure_schema
Args: ['self']

Function _sanitize_user
Args: ['user']

Function _resolve_release
Args: ['self', 'session', 'course_id']

Function _query_releases
Args: ['self', 'course_id', 'scope_type', 'scope_keys']

Function _list_releases
Args: ['self']

Function _release_payload
Args: ['self', 'release_id']

Function _release_row_payload
Args: ['self', 'row']

Function _latest_attempts
Args: ['self', 'username', 'course_id']

Function _certificate_for
Args: ['self', 'username', 'course_id']

Function _course_payload
Args: ['self', 'session', 'course']

Function _attempt_count
Args: ['self', 'username', 'course_id', 'module_id', 'assessment_kind']

Function _resolve_module
Args: ['course', 'module_id', 'assessment_kind']

Function _grade_assessment
Args: ['module', 'answers', 'pass_ratio']

Function _refresh_certificate
Args: ['self', 'username', 'course_id', 'final_grading']

Function _learner_overview
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\curriculum_catalog.py
Imports:
- __future__
- typing

Function _single
Args: ['question_id', 'prompt', 'options', 'correct', 'explanation']

Function _multi
Args: ['question_id', 'prompt', 'options', 'correct', 'explanation']

Function _text
Args: ['question_id', 'prompt', 'accepted', 'explanation']

Function list_courses
Args: []

Function get_course
Args: ['course_id']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\curriculum_certificate_pdf.py
Imports:
- __future__
- hashlib
- math
- unicodedata
- zlib
- datetime
- pathlib
- PIL

Function _normalize_text
Args: ['value']

Function _pdf_string
Args: ['value']

Function _rgb
Args: ['r', 'g', 'b']

Function _estimate_width
Args: ['text', 'font_size']

Function _text_command
Args: ['x', 'y', 'text']

Function _centered_text_command
Args: ['y', 'text']

Function _rect_command
Args: ['x', 'y', 'width', 'height']

Function _line_command
Args: ['x1', 'y1', 'x2', 'y2']

Function _image_draw_command
Args: ['x', 'y', 'width', 'height', 'resource_name']

Function _format_date
Args: ['timestamp']

Function _hex_to_rgb
Args: ['value', 'fallback']

Function _initials
Args: ['value']

Function _wrap_text
Args: ['text']

Function _load_rgb_image
Args: ['path']

Function _build_verification_matrix
Args: ['seed']

Function build_curriculum_certificate_pdf
Args: []

Function bit
Args: ['index']

Function draw_finder
Args: ['origin_x', 'origin_y']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\database.py
Imports:
- __future__
- json
- sqlite3
- threading
- time
- uuid
- pathlib
- typing
- permissions

Class SchoolRepository
- __init__(self, database_path)
- close(self)
- _init_schema(self)
- _encode_json(value)
- _decode_json(value)
- create_user(self, username, display_name, password_hash, password_salt, role, permissions, status)
- set_user_password(self, username, password_hash, password_salt)
- get_user(self, username)
- list_users(self)
- update_user_permissions(self, username, permissions)
- update_user_account(self, username, display_name, role, status)
- set_user_status(self, username, status)
- create_group(self, group_id, display_name, description, permissions)
- get_group(self, group_id)
- list_groups(self)
- update_group_permissions(self, group_id, permissions)
- add_membership(self, username, group_id)
- remove_membership(self, username, group_id)
- list_memberships(self)
- list_user_groups(self, username)
- create_project(self, owner_type, owner_key, name, slug, template, runtime, main_file, description, created_by)
- find_project_by_owner_and_slug(self, owner_type, owner_key, slug)
- get_project(self, project_id)
- list_projects(self)
- list_accessible_projects(self, username, role, group_ids)
- update_project_main_file(self, project_id, main_file)
- put_setting(self, key, value)
- get_setting(self, key, default)
- list_settings(self)
- upsert_worker_node(self, worker_id, display_name, token_secret_name)
- get_worker_node(self, worker_id)
- list_worker_nodes(self)
- create_dispatch_job(self)
- get_dispatch_job(self, job_id)
- list_dispatch_jobs(self)
- list_latest_dispatch_jobs_for_project(self, project_id)
- claim_next_dispatch_job(self, worker_id)
- update_dispatch_job_status(self, job_id)
- append_dispatch_job_log(self, job_id, chunk)
- request_dispatch_job_stop(self, job_id)
- register_worker_nonce(self, worker_id, nonce)
- add_chat_message(self, room_key, author_username, author_display_name, message, metadata)
- list_chat_messages(self, room_key, since, limit)
- set_mute(self, room_key, target_username, duration_minutes, reason, created_by)
- get_active_mute(self, room_key, target_username)
- list_mutes(self, active_only)
- add_audit(self, actor_username, action, target_type, target_id, payload)
- list_audit_logs(self)
- _row_to_user(row)
- _row_to_group(row)
- _row_to_project(row)
- _row_to_worker_node(row)
- _row_to_dispatch_job(row)

Function __init__
Args: ['self', 'database_path']

Function close
Args: ['self']

Function _init_schema
Args: ['self']

Function _encode_json
Args: ['value']

Function _decode_json
Args: ['value']

Function create_user
Args: ['self', 'username', 'display_name', 'password_hash', 'password_salt', 'role', 'permissions', 'status']

Function set_user_password
Args: ['self', 'username', 'password_hash', 'password_salt']

Function get_user
Args: ['self', 'username']

Function list_users
Args: ['self']

Function update_user_permissions
Args: ['self', 'username', 'permissions']

Function update_user_account
Args: ['self', 'username', 'display_name', 'role', 'status']

Function set_user_status
Args: ['self', 'username', 'status']

Function create_group
Args: ['self', 'group_id', 'display_name', 'description', 'permissions']

Function get_group
Args: ['self', 'group_id']

Function list_groups
Args: ['self']

Function update_group_permissions
Args: ['self', 'group_id', 'permissions']

Function add_membership
Args: ['self', 'username', 'group_id']

Function remove_membership
Args: ['self', 'username', 'group_id']

Function list_memberships
Args: ['self']

Function list_user_groups
Args: ['self', 'username']

Function create_project
Args: ['self', 'owner_type', 'owner_key', 'name', 'slug', 'template', 'runtime', 'main_file', 'description', 'created_by']

Function find_project_by_owner_and_slug
Args: ['self', 'owner_type', 'owner_key', 'slug']

Function get_project
Args: ['self', 'project_id']

Function list_projects
Args: ['self']

Function list_accessible_projects
Args: ['self', 'username', 'role', 'group_ids']

Function update_project_main_file
Args: ['self', 'project_id', 'main_file']

Function put_setting
Args: ['self', 'key', 'value']

Function get_setting
Args: ['self', 'key', 'default']

Function list_settings
Args: ['self']

Function upsert_worker_node
Args: ['self', 'worker_id', 'display_name', 'token_secret_name']

Function get_worker_node
Args: ['self', 'worker_id']

Function list_worker_nodes
Args: ['self']

Function create_dispatch_job
Args: ['self']

Function get_dispatch_job
Args: ['self', 'job_id']

Function list_dispatch_jobs
Args: ['self']

Function list_latest_dispatch_jobs_for_project
Args: ['self', 'project_id']

Function claim_next_dispatch_job
Args: ['self', 'worker_id']

Function update_dispatch_job_status
Args: ['self', 'job_id']

Function append_dispatch_job_log
Args: ['self', 'job_id', 'chunk']

Function request_dispatch_job_stop
Args: ['self', 'job_id']

Function register_worker_nonce
Args: ['self', 'worker_id', 'nonce']

Function add_chat_message
Args: ['self', 'room_key', 'author_username', 'author_display_name', 'message', 'metadata']

Function list_chat_messages
Args: ['self', 'room_key', 'since', 'limit']

Function set_mute
Args: ['self', 'room_key', 'target_username', 'duration_minutes', 'reason', 'created_by']

Function get_active_mute
Args: ['self', 'room_key', 'target_username']

Function list_mutes
Args: ['self', 'active_only']

Function add_audit
Args: ['self', 'actor_username', 'action', 'target_type', 'target_id', 'payload']

Function list_audit_logs
Args: ['self']

Function _row_to_user
Args: ['row']

Function _row_to_group
Args: ['row']

Function _row_to_project
Args: ['row']

Function _row_to_worker_node
Args: ['row']

Function _row_to_dispatch_job
Args: ['row']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\deployments.py
Imports:
- __future__
- json
- os
- shutil
- subprocess
- tempfile
- time
- uuid
- zipfile
- pathlib
- typing
- config
- database
- project_files
- workspace

Class DeploymentService
- __init__(self, repository, workspace_manager, security_plane, config)
- list_artifacts(self, session)
- create_share(self, session, project)
- create_export(self, session, project)
- resolve_share_path(self, artifact_id, relative_path)
- resolve_download_path(self, artifact_id)
- _prepare_bundle(self, runtime, project, source_root, bundle_root)
- _write_runtime_guides(self, runtime, project, bundle_root)
- _store_artifact(self)
- _init_schema(self)
- _artifact_row(self, artifact_id)
- _artifact_payload(self, artifact_id)
- _enforce_quota(self, quota_key)

Function __init__
Args: ['self', 'repository', 'workspace_manager', 'security_plane', 'config']

Function list_artifacts
Args: ['self', 'session']

Function create_share
Args: ['self', 'session', 'project']

Function create_export
Args: ['self', 'session', 'project']

Function resolve_share_path
Args: ['self', 'artifact_id', 'relative_path']

Function resolve_download_path
Args: ['self', 'artifact_id']

Function _prepare_bundle
Args: ['self', 'runtime', 'project', 'source_root', 'bundle_root']

Function _write_runtime_guides
Args: ['self', 'runtime', 'project', 'bundle_root']

Function _store_artifact
Args: ['self']

Function _init_schema
Args: ['self']

Function _artifact_row
Args: ['self', 'artifact_id']

Function _artifact_payload
Args: ['self', 'artifact_id']

Function _enforce_quota
Args: ['self', 'quota_key']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\distributed.py
Imports:
- __future__
- json
- os
- shutil
- socket
- subprocess
- time
- dataclasses
- pathlib
- typing
- code_runner
- config
- database
- worker_dispatch
- workspace

Class _ManagedWorker

Class DistributedPlaygroundService
- __init__(self, repository, workspace_manager, security_plane, config, runner)
- close(self)
- status(self, project)
- _status_local(self, project)
- start(self, session, project)
- _start_local(self, session, project)
- stop(self, session, project)
- _stop_local(self, session, project)
- _status_remote(self, project)
- _start_remote(self, session, project)
- _stop_remote(self, session, project)
- stop_project(self, project_id)
- _ensure_security_assets(self, project_id, topology)
- _load_topology(self, project)
- _service_env(self, session, project, service_map, service, resolved_ports, worker_id)
- _service_command(self, project, service)
- _stop_worker(self, worker)
- _find_free_port()
- _resolve_ports(self, services, cluster)
- _log_path(self, project, service_name)
- _prepare_service_workspace(self, project, service_name)
- _service_runtime_root(self, project, service_name)
- _ensure_network(self, project_id)
- _remove_network(self, project_id)
- _resolved_backend(self, session)
- _dispatch_mode(self)
- _container_name(worker_id)
- _network_name(project_id)
- _service_language(runtime)
- _container_path(runtime_root, target)
- _tail_log(path, max_chars)
- _ca_name(project_id)
- _policy_name(project_id)

Function __init__
Args: ['self', 'repository', 'workspace_manager', 'security_plane', 'config', 'runner']

Function close
Args: ['self']

Function status
Args: ['self', 'project']

Function _status_local
Args: ['self', 'project']

Function start
Args: ['self', 'session', 'project']

Function _start_local
Args: ['self', 'session', 'project']

Function stop
Args: ['self', 'session', 'project']

Function _stop_local
Args: ['self', 'session', 'project']

Function _status_remote
Args: ['self', 'project']

Function _start_remote
Args: ['self', 'session', 'project']

Function _stop_remote
Args: ['self', 'session', 'project']

Function stop_project
Args: ['self', 'project_id']

Function _ensure_security_assets
Args: ['self', 'project_id', 'topology']

Function _load_topology
Args: ['self', 'project']

Function _service_env
Args: ['self', 'session', 'project', 'service_map', 'service', 'resolved_ports', 'worker_id']

Function _service_command
Args: ['self', 'project', 'service']

Function _stop_worker
Args: ['self', 'worker']

Function _find_free_port
Args: []

Function _resolve_ports
Args: ['self', 'services', 'cluster']

Function _log_path
Args: ['self', 'project', 'service_name']

Function _prepare_service_workspace
Args: ['self', 'project', 'service_name']

Function _service_runtime_root
Args: ['self', 'project', 'service_name']

Function _ensure_network
Args: ['self', 'project_id']

Function _remove_network
Args: ['self', 'project_id']

Function _resolved_backend
Args: ['self', 'session']

Function _dispatch_mode
Args: ['self']

Function _container_name
Args: ['worker_id']

Function _network_name
Args: ['project_id']

Function _service_language
Args: ['runtime']

Function _container_path
Args: ['runtime_root', 'target']

Function _tail_log
Args: ['path', 'max_chars']

Function _ca_name
Args: ['project_id']

Function _policy_name
Args: ['project_id']

Function ignore
Args: ['_directory', 'names']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\distribution_builder.py
Imports:
- __future__
- json
- stat
- shutil
- tempfile
- zipfile
- dataclasses
- pathlib
- typing
- argparse

Class DistributionBuildResult

Class DistributionMaterializeResult

Class LinuxProjectBuildResult

Function detect_project_version
Args: ['base_path']

Function build_distribution_archive
Args: ['base_path', 'output_dir', 'version', 'flavor']

Function build_linux_project_archive
Args: ['base_path', 'output_dir', 'version']

Function materialize_distribution_directory
Args: ['base_path', 'target_root']

Function _normalize_flavor
Args: ['flavor']

Function _copy_project_tree
Args: ['source_root', 'target_root']

Function _copy_directory
Args: ['source_dir', 'target_dir']

Function _should_skip_root_entry
Args: ['path', 'relative_path']

Function _should_skip_entry
Args: ['path', 'relative_path']

Function _normalize_relative_path
Args: ['path']

Function _is_excluded_relative_path
Args: ['relative_path', 'excluded_relative_paths']

Function _create_distribution_scaffold
Args: ['staging_root', 'version', 'flavor']

Function _prune_for_flavor
Args: ['staging_root', 'flavor']

Function _write_platform_installation_guide
Args: ['staging_root', 'flavor', 'version']

Function _remove_if_exists
Args: ['path']

Function _ensure_placeholder
Args: ['path']

Function _write_lit_scaffold
Args: ['staging_root']

Function _copy_optional_linux_runtime_binaries
Args: ['source_root', 'target_root', 'flavor']

Function _zip_tree
Args: ['root', 'archive_path']

Function _iter_files
Args: ['root']

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\docs_catalog.py
Imports:
- __future__
- pathlib
- templates

Class DocumentationCatalog
- __init__(self, docs_path)
- ensure_seed_docs(self)
- list_docs(self)
- get_doc(self, slug)

Function __init__
Args: ['self', 'docs_path']

Function ensure_seed_docs
Args: ['self']

Function list_docs
Args: ['self']

Function get_doc
Args: ['self', 'slug']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\embedded_nova.py
Imports:
- __future__
- json
- secrets
- threading
- time
- uuid
- dataclasses
- pathlib
- typing

Class EmbeddedPrincipal

Class EmbeddedSecurityPlane
- __init__(self, base_path)
- register_tenant(self, tenant_id)
- get_tenant(self, tenant_id)
- issue_token(self, tenant_id, subject)
- authenticate(self, token)
- revoke_token(self, token_id)
- store_secret(self, tenant_id, name, secret_value, metadata)
- resolve_secret(self, tenant_id, name)
- create_certificate_authority(self, name)
- get_certificate_authority(self, name)
- set_trust_policy(self, name)
- get_trust_policy(self, name)
- onboard_worker(self, worker_id, tenant_id)
- list_worker_enrollments(self, tenant_id)
- snapshot(self)
- close(self)
- _load_state(self)
- _save_state(self)
- _empty_state()
- _secret_key(tenant_id, name)

Class EmbeddedToolSandbox
- __init__(self)
- authorize(self, principal)
- snapshot(self)

Class EmbeddedNovaAIProviderRuntime
- snapshot(self)

Function _json_safe
Args: ['value']

Function __init__
Args: ['self', 'base_path']

Function register_tenant
Args: ['self', 'tenant_id']

Function get_tenant
Args: ['self', 'tenant_id']

Function issue_token
Args: ['self', 'tenant_id', 'subject']

Function authenticate
Args: ['self', 'token']

Function revoke_token
Args: ['self', 'token_id']

Function store_secret
Args: ['self', 'tenant_id', 'name', 'secret_value', 'metadata']

Function resolve_secret
Args: ['self', 'tenant_id', 'name']

Function create_certificate_authority
Args: ['self', 'name']

Function get_certificate_authority
Args: ['self', 'name']

Function set_trust_policy
Args: ['self', 'name']

Function get_trust_policy
Args: ['self', 'name']

Function onboard_worker
Args: ['self', 'worker_id', 'tenant_id']

Function list_worker_enrollments
Args: ['self', 'tenant_id']

Function snapshot
Args: ['self']

Function close
Args: ['self']

Function _load_state
Args: ['self']

Function _save_state
Args: ['self']

Function _empty_state
Args: []

Function _secret_key
Args: ['tenant_id', 'name']

Function __init__
Args: ['self']

Function authorize
Args: ['self', 'principal']

Function snapshot
Args: ['self']

Function snapshot
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\material_studio.py
Imports:
- __future__
- ast
- json
- math
- re
- textwrap
- typing
- code_runner
- curriculum_catalog
- database

Class TeacherMaterialStudioService
- __init__(self, repository, runner)
- _ai_provider_id(self)
- _requires_visible_output(self, state, bundle, run_result)
- _python_has_missing_main_invocation(code)
- start_generation(self)
- continue_generation(self, session)
- generate(self, session)
- run_current(self, session, payload)
- _coerce_generation_state(self, generation_state)
- _complete_inference_payload(self, payload)
- _inference_step(self, state)
- _profile_from_state(self, state)
- _instruction_preset_from_state(self, state)
- _normalize_instruction_preset(preset_key, profile_key, language)
- _normalize_compare_text(value)
- _instruction_preset_lines(self, instruction_preset)
- _prompt_input_token_budget(self, phase)
- _normalize_prompt_text(text)
- _estimate_token_count(text)
- _trim_text_middle(text)
- _is_model_input_too_long_error(error)
- _prepare_inference_prompt(self, prompt)
- _generation_options_for_phase(self, phase)
- _timeout_seconds_for_phase(self, phase)
- _agent_summary(summary, instruction_preset)
- _state_plan(self, state)
- _state_bundle(self, state)
- _state_run_result(self, state, language)
- _issue_json_repair_step(self, state)
- _issue_code_repair_step(self, state)
- _issue_plan_step(self, state)
- _consume_plan_response(self, state, raw_text, model)
- _consume_plan_repair_response(self, state, raw_text, model)
- _issue_author_step(self, state)
- _consume_author_response(self, session, state, raw_text, model)
- _consume_author_repair_response(self, session, state, raw_text, model)
- _issue_author_code_step(self, state)
- _consume_author_code_response(self, session, state, raw_text, model)
- _consume_author_code_repair_response(self, session, state, raw_text, model)
- _accept_author_code(self, session, state, code_text, model)
- _run_working_bundle(self, session, state)
- _issue_debugger_step(self, state)
- _consume_debugger_response(self, session, state, raw_text, model)
- _consume_debugger_repair_response(self, session, state, raw_text, model)
- _issue_debugger_code_step(self, state)
- _consume_debugger_code_response(self, session, state, raw_text, model)
- _consume_debugger_code_repair_response(self, session, state, raw_text, model)
- _accept_debugger_code(self, session, state, repaired_code, model)
- _issue_pedagogy_step(self, state)
- _consume_pedagogy_response(self, state, raw_text, model)
- _consume_pedagogy_repair_response(self, state, raw_text, model)
- _finalize_generation(self, state)
- _replace_main_file(self, bundle, repaired_code, plan)
- _fallback_pedagogy(self, payload, profile, run_result)
- _bundle_prompt_snapshot(self, bundle)
- _run_result_snapshot(run_result)
- _pedagogy_payload_snapshot(self, payload)
- _bundle_response(self, bundle, run_result, trace)
- _json_completion(self, prompt)
- _code_completion(self, prompt)
- _normalize_language(language)
- _normalize_profile(profile)
- _normalize_plan(payload, fallback_language)
- _normalize_bundle(self, payload, fallback_language, plan)
- _main_file_content(files, main_file)
- _sanitize_relative_path(path_text)
- _stringify_text(value)
- _clean_text(value)
- _has_meaningful_value(value)
- _structured_json_payload(cls, text)
- _validate_schema_payload(cls, payload, schema_name)
- _candidate_objects(cls, payload)
- _lookup_path(payload, dotted_key)
- _lookup_alias(cls, objects)
- _looks_like_file_path(value)
- _normalize_files_value(cls, value)
- _canonicalize_plan_payload(cls, payload)
- _canonicalize_bundle_payload(cls, payload)
- _canonicalize_pedagogy_payload(cls, payload)
- _extract_json_object(text)
- _parse_json_candidate(candidate)
- _json_candidates(raw)
- _json_candidate_variants(text)
- _strip_jsonish_comments(text)
- _remove_trailing_commas(text)
- _quote_bare_keys(text)
- _scan_top_level_json_objects(text)
- _jsonish_to_python_literal(text)
- _extract_code_block(text)
- _looks_like_instructional_prose(text)
- _looks_like_source_code(cls, text)
- _json_repair_prompt(raw_text)
- _parse_json_response(cls, raw_text)
- _parse_code_response(cls, raw_text)
- _code_repair_prompt(raw_text)
- _planner_prompt(self, prompt, language, profile)
- _fallback_plan(self, prompt, language, profile)
- _author_prompt(self, prompt, plan, profile)
- _author_code_prompt(self, prompt, plan, profile)
- _pedagogy_json_repair_prompt(self, raw_text, payload, profile, run_result)
- _repair_prompt(self, prompt, plan, profile, bundle, run_result, next_attempt, instruction_preset)
- _repair_code_prompt(self, prompt, plan, profile, bundle, run_result, next_attempt, instruction_preset)
- _pedagogy_prompt(self, payload, profile, run_result, instruction_preset)

Class _MainCallVisitor
- __init__(self)
- visit_Call(self, node)

Function material_studio_profile_catalog
Args: []

Function _material_studio_preset_technical_lines
Args: ['language']

Function _material_studio_preset_modules
Args: ['source']

Function material_studio_instruction_preset_catalog
Args: []

Function resolve_material_studio_instruction_preset
Args: ['preset_key']

Function __init__
Args: ['self', 'repository', 'runner']

Function _ai_provider_id
Args: ['self']

Function _requires_visible_output
Args: ['self', 'state', 'bundle', 'run_result']

Function _python_has_missing_main_invocation
Args: ['code']

Function start_generation
Args: ['self']

Function continue_generation
Args: ['self', 'session']

Function generate
Args: ['self', 'session']

Function run_current
Args: ['self', 'session', 'payload']

Function _coerce_generation_state
Args: ['self', 'generation_state']

Function _complete_inference_payload
Args: ['self', 'payload']

Function _inference_step
Args: ['self', 'state']

Function _profile_from_state
Args: ['self', 'state']

Function _instruction_preset_from_state
Args: ['self', 'state']

Function _normalize_instruction_preset
Args: ['preset_key', 'profile_key', 'language']

Function _normalize_compare_text
Args: ['value']

Function _instruction_preset_lines
Args: ['self', 'instruction_preset']

Function _prompt_input_token_budget
Args: ['self', 'phase']

Function _normalize_prompt_text
Args: ['text']

Function _estimate_token_count
Args: ['text']

Function _trim_text_middle
Args: ['text']

Function _is_model_input_too_long_error
Args: ['error']

Function _prepare_inference_prompt
Args: ['self', 'prompt']

Function _generation_options_for_phase
Args: ['self', 'phase']

Function _timeout_seconds_for_phase
Args: ['self', 'phase']

Function _agent_summary
Args: ['summary', 'instruction_preset']

Function _state_plan
Args: ['self', 'state']

Function _state_bundle
Args: ['self', 'state']

Function _state_run_result
Args: ['self', 'state', 'language']

Function _issue_json_repair_step
Args: ['self', 'state']

Function _issue_code_repair_step
Args: ['self', 'state']

Function _issue_plan_step
Args: ['self', 'state']

Function _consume_plan_response
Args: ['self', 'state', 'raw_text', 'model']

Function _consume_plan_repair_response
Args: ['self', 'state', 'raw_text', 'model']

Function _issue_author_step
Args: ['self', 'state']

Function _consume_author_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _consume_author_repair_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _issue_author_code_step
Args: ['self', 'state']

Function _consume_author_code_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _consume_author_code_repair_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _accept_author_code
Args: ['self', 'session', 'state', 'code_text', 'model']

Function _run_working_bundle
Args: ['self', 'session', 'state']

Function _issue_debugger_step
Args: ['self', 'state']

Function _consume_debugger_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _consume_debugger_repair_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _issue_debugger_code_step
Args: ['self', 'state']

Function _consume_debugger_code_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _consume_debugger_code_repair_response
Args: ['self', 'session', 'state', 'raw_text', 'model']

Function _accept_debugger_code
Args: ['self', 'session', 'state', 'repaired_code', 'model']

Function _issue_pedagogy_step
Args: ['self', 'state']

Function _consume_pedagogy_response
Args: ['self', 'state', 'raw_text', 'model']

Function _consume_pedagogy_repair_response
Args: ['self', 'state', 'raw_text', 'model']

Function _finalize_generation
Args: ['self', 'state']

Function _replace_main_file
Args: ['self', 'bundle', 'repaired_code', 'plan']

Function _fallback_pedagogy
Args: ['self', 'payload', 'profile', 'run_result']

Function _bundle_prompt_snapshot
Args: ['self', 'bundle']

Function _run_result_snapshot
Args: ['run_result']

Function _pedagogy_payload_snapshot
Args: ['self', 'payload']

Function _bundle_response
Args: ['self', 'bundle', 'run_result', 'trace']

Function _json_completion
Args: ['self', 'prompt']

Function _code_completion
Args: ['self', 'prompt']

Function _normalize_language
Args: ['language']

Function _normalize_profile
Args: ['profile']

Function _normalize_plan
Args: ['payload', 'fallback_language']

Function _normalize_bundle
Args: ['self', 'payload', 'fallback_language', 'plan']

Function _main_file_content
Args: ['files', 'main_file']

Function _sanitize_relative_path
Args: ['path_text']

Function _stringify_text
Args: ['value']

Function _clean_text
Args: ['value']

Function _has_meaningful_value
Args: ['value']

Function _structured_json_payload
Args: ['cls', 'text']

Function _validate_schema_payload
Args: ['cls', 'payload', 'schema_name']

Function _candidate_objects
Args: ['cls', 'payload']

Function _lookup_path
Args: ['payload', 'dotted_key']

Function _lookup_alias
Args: ['cls', 'objects']

Function _looks_like_file_path
Args: ['value']

Function _normalize_files_value
Args: ['cls', 'value']

Function _canonicalize_plan_payload
Args: ['cls', 'payload']

Function _canonicalize_bundle_payload
Args: ['cls', 'payload']

Function _canonicalize_pedagogy_payload
Args: ['cls', 'payload']

Function _extract_json_object
Args: ['text']

Function _parse_json_candidate
Args: ['candidate']

Function _json_candidates
Args: ['raw']

Function _json_candidate_variants
Args: ['text']

Function _strip_jsonish_comments
Args: ['text']

Function _remove_trailing_commas
Args: ['text']

Function _quote_bare_keys
Args: ['text']

Function _scan_top_level_json_objects
Args: ['text']

Function _jsonish_to_python_literal
Args: ['text']

Function _extract_code_block
Args: ['text']

Function _looks_like_instructional_prose
Args: ['text']

Function _looks_like_source_code
Args: ['cls', 'text']

Function _json_repair_prompt
Args: ['raw_text']

Function _parse_json_response
Args: ['cls', 'raw_text']

Function _parse_code_response
Args: ['cls', 'raw_text']

Function _code_repair_prompt
Args: ['raw_text']

Function _planner_prompt
Args: ['self', 'prompt', 'language', 'profile']

Function _fallback_plan
Args: ['self', 'prompt', 'language', 'profile']

Function _author_prompt
Args: ['self', 'prompt', 'plan', 'profile']

Function _author_code_prompt
Args: ['self', 'prompt', 'plan', 'profile']

Function _pedagogy_json_repair_prompt
Args: ['self', 'raw_text', 'payload', 'profile', 'run_result']

Function _repair_prompt
Args: ['self', 'prompt', 'plan', 'profile', 'bundle', 'run_result', 'next_attempt', 'instruction_preset']

Function _repair_code_prompt
Args: ['self', 'prompt', 'plan', 'profile', 'bundle', 'run_result', 'next_attempt', 'instruction_preset']

Function _pedagogy_prompt
Args: ['self', 'payload', 'profile', 'run_result', 'instruction_preset']

Function __init__
Args: ['self']

Function visit_Call
Args: ['self', 'node']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\mentor.py
Imports:
- __future__
- typing
- ai_service
- database

Class SocraticMentorService
- __init__(self, repository)
- thread(self, session, project)
- prepare(self, session, project)
- store_reply(self, session, project)
- _room_key(project_id, username)
- _compose_prompt(project, prompt, code, path_hint, run_output, history)

Function __init__
Args: ['self', 'repository']

Function thread
Args: ['self', 'session', 'project']

Function prepare
Args: ['self', 'session', 'project']

Function store_reply
Args: ['self', 'session', 'project']

Function _room_key
Args: ['project_id', 'username']

Function _compose_prompt
Args: ['project', 'prompt', 'code', 'path_hint', 'run_output', 'history']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\nova_bootstrap.py
Imports:
- __future__
- importlib.util
- sys
- pathlib

Function bootstrap_package
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\nova_bridge.py
Imports:
- __future__
- dataclasses
- embedded_nova

Class NovaBridge

Function load_nova_bridge
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\nova_launch.py
Imports:
- __future__
- nova_bootstrap
- nova_school_server.__main__

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\nova_product_docs.py
Imports:
- __future__
- json
- shutil
- pathlib
- typing
- permissions

Class NovaSchoolProductDocsBuilder
- __init__(self, source_root, pack_root)
- ensure_built(self)
- is_stale(self)
- build(self)
- _build_index(self, documents)
- _expand_tokens(self, content)
- _permission_table(self)
- _role_defaults_table(self)
- _bool_label(value)
- _has_sources(self)
- _source_files(self)
- _source_signature(self)
- _extract_title(content, path)
- _extract_summary(content)

Function main
Args: []

Function __init__
Args: ['self', 'source_root', 'pack_root']

Function ensure_built
Args: ['self']

Function is_stale
Args: ['self']

Function build
Args: ['self']

Function _build_index
Args: ['self', 'documents']

Function _expand_tokens
Args: ['self', 'content']

Function _permission_table
Args: ['self']

Function _role_defaults_table
Args: ['self']

Function _bool_label
Args: ['value']

Function _has_sources
Args: ['self']

Function _source_files
Args: ['self']

Function _source_signature
Args: ['self']

Function _extract_title
Args: ['content', 'path']

Function _extract_summary
Args: ['content']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\nova_test_launch.py
Imports:
- __future__
- sys
- unittest
- pathlib
- nova_bootstrap

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\nova_worker_launch.py
Imports:
- __future__
- nova_bootstrap
- nova_school_server.worker_agent

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\permissions.py
Imports:
- __future__
- typing

Function normalize_permission_overrides
Args: ['raw']

Function resolve_permissions
Args: ['role', 'group_overrides', 'user_overrides']

Function permission_catalog
Args: []

Function allowed_tool_names
Args: ['permissions']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\project_files.py
Imports:
- __future__
- shutil
- pathlib

Function copy_project_snapshot
Args: ['project_root', 'target_root']

Function list_snapshot_files
Args: ['snapshot_root']

Function read_text_preview
Args: ['snapshot_root', 'preferred_path', 'max_chars']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\pty_host.py
Imports:
- __future__
- os
- signal
- subprocess
- threading
- time
- pathlib
- typing
- ctypes
- ctypes
- errno
- fcntl
- pty
- struct
- termios
- winpty
- winpty

Class PtyProcess
- read(self, size)
- write(self, data)
- resize(self, cols, rows)
- poll(self)
- wait(self, timeout)
- terminate(self, force)
- close(self)

Class COORD

Class STARTUPINFOW

Class STARTUPINFOEXW

Class PROCESS_INFORMATION

Class _PyWinPtyProcess
- __init__(self, command, cwd, env, cols, rows)
- _capture_output(self)
- read(self, size)
- write(self, data)
- resize(self, cols, rows)
- poll(self)
- wait(self, timeout)
- terminate(self, force)
- close(self)

Class _WindowsConPtyProcess
- __init__(self, command, cwd, env, cols, rows)
- read(self, size)
- write(self, data)
- resize(self, cols, rows)
- poll(self)
- wait(self, timeout)
- terminate(self, force)
- _capture_output(self)
- close(self)

Class _PosixPtyProcess
- __init__(self, command, cwd, env, cols, rows)
- read(self, size)
- write(self, data)
- resize(self, cols, rows)
- poll(self)
- wait(self, timeout)
- terminate(self, force)
- close(self)

Function normalize_terminal_size
Args: ['cols', 'rows']

Function create_pty_process
Args: ['command', 'cwd', 'env', 'cols', 'rows']

Function read
Args: ['self', 'size']

Function write
Args: ['self', 'data']

Function resize
Args: ['self', 'cols', 'rows']

Function poll
Args: ['self']

Function wait
Args: ['self', 'timeout']

Function terminate
Args: ['self', 'force']

Function close
Args: ['self']

Function _raise_last_error
Args: ['message']

Function _raise_hresult
Args: ['message', 'code']

Function _close_handle
Args: ['handle']

Function _set_no_inherit
Args: ['handle']

Function _create_pipe
Args: []

Function _build_environment_block
Args: ['env']

Function _build_attribute_list
Args: ['hpc']

Function _normalize_windows_input
Args: ['data']

Function __init__
Args: ['self', 'command', 'cwd', 'env', 'cols', 'rows']

Function _capture_output
Args: ['self']

Function read
Args: ['self', 'size']

Function write
Args: ['self', 'data']

Function resize
Args: ['self', 'cols', 'rows']

Function poll
Args: ['self']

Function wait
Args: ['self', 'timeout']

Function terminate
Args: ['self', 'force']

Function close
Args: ['self']

Function __init__
Args: ['self', 'command', 'cwd', 'env', 'cols', 'rows']

Function read
Args: ['self', 'size']

Function write
Args: ['self', 'data']

Function resize
Args: ['self', 'cols', 'rows']

Function poll
Args: ['self']

Function wait
Args: ['self', 'timeout']

Function terminate
Args: ['self', 'force']

Function _capture_output
Args: ['self']

Function close
Args: ['self']

Function __init__
Args: ['self', 'command', 'cwd', 'env', 'cols', 'rows']

Function read
Args: ['self', 'size']

Function write
Args: ['self', 'data']

Function resize
Args: ['self', 'cols', 'rows']

Function poll
Args: ['self']

Function wait
Args: ['self', 'timeout']

Function terminate
Args: ['self', 'force']

Function close
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\realtime.py
Imports:
- __future__
- base64
- codecs
- hashlib
- json
- socket
- struct
- subprocess
- threading
- time
- uuid
- dataclasses
- http
- typing
- auth
- code_runner
- database
- pty_host

Class WebSocketConnection
- __init__(self, sock)
- send_json(self, payload)
- send_text(self, text)
- recv_json(self)
- recv_text(self)
- close(self, code, reason)
- accept_key(key)
- _recv_frame(self)
- _send_frame(self, opcode, payload)
- _recv_exact(self, size)

Class RealtimeClient

Class ActiveLiveRun

Class LiveRunManager
- __init__(self, runner, repository)
- close(self)
- stop_for_client(self, client_id)
- start(self, client, payload)
- send_input(self, actor, session_id, text)
- resize(self, actor, session_id, cols, rows)
- stop(self, actor, session_id)
- _pump_stream(self, session_id, stream_name, stream)
- _pump_terminal(self, session_id)
- _watch_process(self, session_id)
- _emit_chunk(self, session_id, stream_name, chunk)
- _emit_exit_from_handle(self, handle, returncode, duration_ms)
- _emit_exit(self, prepared, actor_username, returncode, duration_ms, timed_out, emitter, client_meta, terminal, notes)
- _session(self, session_id)
- _ensure_control(actor, handle)
- _terminate(self, session_id)
- _terminal_payload(payload)
- _poll_handle(handle)
- _wait_handle(handle)

Class RealtimeService
- __init__(self, application)
- close(self)
- handle_project_socket(self, connection, session, project)
- _handle_message(self, client, message)
- _broadcast_project(self, project_id, payload)
- _register(self, client)
- _unregister(self, client)
- _require_permission(session, key)

Function upgrade_websocket
Args: ['handler']

Function __init__
Args: ['self', 'sock']

Function send_json
Args: ['self', 'payload']

Function send_text
Args: ['self', 'text']

Function recv_json
Args: ['self']

Function recv_text
Args: ['self']

Function close
Args: ['self', 'code', 'reason']

Function accept_key
Args: ['key']

Function _recv_frame
Args: ['self']

Function _send_frame
Args: ['self', 'opcode', 'payload']

Function _recv_exact
Args: ['self', 'size']

Function __init__
Args: ['self', 'runner', 'repository']

Function close
Args: ['self']

Function stop_for_client
Args: ['self', 'client_id']

Function start
Args: ['self', 'client', 'payload']

Function send_input
Args: ['self', 'actor', 'session_id', 'text']

Function resize
Args: ['self', 'actor', 'session_id', 'cols', 'rows']

Function stop
Args: ['self', 'actor', 'session_id']

Function _pump_stream
Args: ['self', 'session_id', 'stream_name', 'stream']

Function _pump_terminal
Args: ['self', 'session_id']

Function _watch_process
Args: ['self', 'session_id']

Function _emit_chunk
Args: ['self', 'session_id', 'stream_name', 'chunk']

Function _emit_exit_from_handle
Args: ['self', 'handle', 'returncode', 'duration_ms']

Function _emit_exit
Args: ['self', 'prepared', 'actor_username', 'returncode', 'duration_ms', 'timed_out', 'emitter', 'client_meta', 'terminal', 'notes']

Function _session
Args: ['self', 'session_id']

Function _ensure_control
Args: ['actor', 'handle']

Function _terminate
Args: ['self', 'session_id']

Function _terminal_payload
Args: ['payload']

Function _poll_handle
Args: ['handle']

Function _wait_handle
Args: ['handle']

Function __init__
Args: ['self', 'application']

Function close
Args: ['self']

Function handle_project_socket
Args: ['self', 'connection', 'session', 'project']

Function _handle_message
Args: ['self', 'client', 'message']

Function _broadcast_project
Args: ['self', 'project_id', 'payload']

Function _register
Args: ['self', 'client']

Function _unregister
Args: ['self', 'client']

Function _require_permission
Args: ['session', 'key']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\reference_import_cpp.py
Imports:
- __future__
- argparse
- html
- json
- re
- shutil
- sys
- time
- urllib.request
- collections
- dataclasses
- hashlib
- pathlib
- typing
- urllib.parse

Class ReferenceTarget

Class CppReferenceMirrorBuilder
- __init__(self)
- build(self)
- _prepare_output(self)
- _seed_urls(self)
- _mirror_page(self, remote_url)
- _mirror_asset(self, remote_url)
- _fetch(self, remote_url)
- _rewrite_html(self, html_text, current_url)
- _rewrite_srcset(self, match, current_url, current_local_path)
- _rewrite_css(self, css_text, current_url, current_local_path)
- _rewrite_reference(self, raw_value)
- classify_reference(raw_value)
- _normalize_cpp_page_path(path)
- local_page_path(remote_url)
- local_asset_path(remote_url)
- _relative_href(current_local_path, target_local_path, fragment)
- _is_css_asset(remote_url)
- _strip_external_noise(html_text)
- _write_landing_page(self)

Function build_argument_parser
Args: []

Function main
Args: ['argv']

Function __init__
Args: ['self']

Function build
Args: ['self']

Function _prepare_output
Args: ['self']

Function _seed_urls
Args: ['self']

Function _mirror_page
Args: ['self', 'remote_url']

Function _mirror_asset
Args: ['self', 'remote_url']

Function _fetch
Args: ['self', 'remote_url']

Function _rewrite_html
Args: ['self', 'html_text', 'current_url']

Function _rewrite_srcset
Args: ['self', 'match', 'current_url', 'current_local_path']

Function _rewrite_css
Args: ['self', 'css_text', 'current_url', 'current_local_path']

Function _rewrite_reference
Args: ['self', 'raw_value']

Function classify_reference
Args: ['raw_value']

Function _normalize_cpp_page_path
Args: ['path']

Function local_page_path
Args: ['remote_url']

Function local_asset_path
Args: ['remote_url']

Function _relative_href
Args: ['current_local_path', 'target_local_path', 'fragment']

Function _is_css_asset
Args: ['remote_url']

Function _strip_external_noise
Args: ['html_text']

Function _write_landing_page
Args: ['self']

Function replace_attr
Args: ['match']

Function replace_url
Args: ['match']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\reference_import_web.py
Imports:
- __future__
- argparse
- html
- json
- re
- shutil
- subprocess
- sys
- time
- dataclasses
- pathlib
- typing
- urllib.parse

Class MirrorSource

Class MirrorPack

Class ReferenceWebMirrorBuilder
- __init__(self)
- build(self)
- finalize_existing_site(self)
- _build_wget_command(self, source)
- _rewrite_mirror_html(self)
- _rewrite_attr(self, current_path, match)
- _rewrite_srcset(self, current_path, match)
- _rewrite_url(self, current_path, raw_value)
- _is_absolute_or_root_relative(value)
- resolve_local_target(self, raw_value)
- _relative_href(current_path, target_path)
- _write_landing_page(self)

Function build_argument_parser
Args: []

Function main
Args: ['argv']

Function __init__
Args: ['self']

Function build
Args: ['self']

Function finalize_existing_site
Args: ['self']

Function _build_wget_command
Args: ['self', 'source']

Function _rewrite_mirror_html
Args: ['self']

Function _rewrite_attr
Args: ['self', 'current_path', 'match']

Function _rewrite_srcset
Args: ['self', 'current_path', 'match']

Function _rewrite_url
Args: ['self', 'current_path', 'raw_value']

Function _is_absolute_or_root_relative
Args: ['value']

Function resolve_local_target
Args: ['self', 'raw_value']

Function _relative_href
Args: ['current_path', 'target_path']

Function _write_landing_page
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\reference_library.py
Imports:
- __future__
- html
- json
- re
- pathlib
- typing
- urllib.parse
- nova_product_docs
- templates

Class ReferenceLibraryService
- __init__(self, library_root, docs_source_root)
- catalog(self)
- render_portal(self)
- resolve_asset(self, area, relative_path)
- documents(self, area, limit)
- resolve_document(self, area, doc_id)
- search(self, query)
- _catalog_entry(self, slug)
- _load_documents(self, slug)
- _build_index(self, slug)
- _builtin_document(self, slug)
- _has_mirrored_pack(self, slug)
- _pack_root(self, slug)
- _site_root(self, slug)
- _index_path(self, slug)
- _content_root(self, slug)
- _contains_documents(self, root)
- _iter_doc_files(self, root)
- _build_document_entry(self, slug, path, rel_path, content)
- _pack_signature(self, root)
- _default_docs_source_root(self)
- _ensure_managed_pack(self, slug)
- _status_for_slug(slug, installed)
- _index_is_stale(self, slug)
- _extract_document_data(path, content)
- _strip_tags(value)
- _collapse_ws(value)
- _markdown_plain_text(value)
- _snippet(text, terms)
- _render_shell(self)
- _active_document_markup(self, selected_area, active_doc)
- _reference_url(area, doc_id, query)
- _asset_url(area, rel_path)
- _markdown_to_html(self, source)
- _is_table_header(lines, index)
- _render_table(self, lines, index)
- _parse_table_row(row)
- _render_plain_inline(text)
- _render_inline(self, text)
- _strip_duplicate_first_heading(source, title)
- _normalize_cpp_markdown(self, rel_path, source)
- _cpp_primary_title(self, rel_path, parts)
- _cpp_intro_blocks(self, intro)
- _split_cpp_section_heading(self, section)
- _find_repeated_prefix_index(text)
- _cleanup_cpp_block(text)

Function __init__
Args: ['self', 'library_root', 'docs_source_root']

Function catalog
Args: ['self']

Function render_portal
Args: ['self']

Function resolve_asset
Args: ['self', 'area', 'relative_path']

Function documents
Args: ['self', 'area', 'limit']

Function resolve_document
Args: ['self', 'area', 'doc_id']

Function search
Args: ['self', 'query']

Function _catalog_entry
Args: ['self', 'slug']

Function _load_documents
Args: ['self', 'slug']

Function _build_index
Args: ['self', 'slug']

Function _builtin_document
Args: ['self', 'slug']

Function _has_mirrored_pack
Args: ['self', 'slug']

Function _pack_root
Args: ['self', 'slug']

Function _site_root
Args: ['self', 'slug']

Function _index_path
Args: ['self', 'slug']

Function _content_root
Args: ['self', 'slug']

Function _contains_documents
Args: ['self', 'root']

Function _iter_doc_files
Args: ['self', 'root']

Function _build_document_entry
Args: ['self', 'slug', 'path', 'rel_path', 'content']

Function _pack_signature
Args: ['self', 'root']

Function _default_docs_source_root
Args: ['self']

Function _ensure_managed_pack
Args: ['self', 'slug']

Function _status_for_slug
Args: ['slug', 'installed']

Function _index_is_stale
Args: ['self', 'slug']

Function _extract_document_data
Args: ['path', 'content']

Function _strip_tags
Args: ['value']

Function _collapse_ws
Args: ['value']

Function _markdown_plain_text
Args: ['value']

Function _snippet
Args: ['text', 'terms']

Function _render_shell
Args: ['self']

Function _active_document_markup
Args: ['self', 'selected_area', 'active_doc']

Function _reference_url
Args: ['area', 'doc_id', 'query']

Function _asset_url
Args: ['area', 'rel_path']

Function _markdown_to_html
Args: ['self', 'source']

Function _is_table_header
Args: ['lines', 'index']

Function _render_table
Args: ['self', 'lines', 'index']

Function _parse_table_row
Args: ['row']

Function _render_plain_inline
Args: ['text']

Function _render_inline
Args: ['self', 'text']

Function _strip_duplicate_first_heading
Args: ['source', 'title']

Function _normalize_cpp_markdown
Args: ['self', 'rel_path', 'source']

Function _cpp_primary_title
Args: ['self', 'rel_path', 'parts']

Function _cpp_intro_blocks
Args: ['self', 'intro']

Function _split_cpp_section_heading
Args: ['self', 'section']

Function _find_repeated_prefix_index
Args: ['text']

Function _cleanup_cpp_block
Args: ['text']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\release_notes.py
Imports:
- __future__
- re
- subprocess
- dataclasses
- pathlib
- typing
- argparse

Class ReleaseCommit

Class ReleaseVersion

Class ReleaseHistory

Function build_release_history
Args: ['base_path']

Function list_git_tags
Args: ['base_path']

Function list_git_commits
Args: ['base_path', 'revision_range']

Function categorize_commit_subject
Args: ['subject']

Function render_changelog
Args: ['history']

Function render_release_notes
Args: ['history', 'tag']

Function write_changelog
Args: ['base_path', 'target_path']

Function write_release_notes
Args: ['base_path', 'tag', 'target_path']

Function _render_commit_groups
Args: ['commits']

Function _run_git
Args: ['base_path', 'args']

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\reviews.py
Imports:
- __future__
- hashlib
- hmac
- json
- os
- time
- uuid
- pathlib
- typing
- database
- project_files
- workspace

Class ReviewService
- __init__(self, repository, security_plane, workspace_manager, tenant_id, review_root)
- dashboard(self, session)
- submit(self, session, project)
- submit_feedback(self, session, assignment_id, feedback)
- _init_schema(self)
- _select_reviewers(self, session, project)
- _list_submissions_for(self, session)
- _list_assignments_for(self, session)
- _submission_row(self, submission_id)
- _assignment_row(self, assignment_id)
- _submission_payload(self, submission_id)
- _assignment_payload(self, assignment_id)
- _refresh_submission_status(self, submission_id)
- _analytics(self)
- _project_run_analytics(self, project_id)
- _alias(self, prefix, seed)

Function __init__
Args: ['self', 'repository', 'security_plane', 'workspace_manager', 'tenant_id', 'review_root']

Function dashboard
Args: ['self', 'session']

Function submit
Args: ['self', 'session', 'project']

Function submit_feedback
Args: ['self', 'session', 'assignment_id', 'feedback']

Function _init_schema
Args: ['self']

Function _select_reviewers
Args: ['self', 'session', 'project']

Function _list_submissions_for
Args: ['self', 'session']

Function _list_assignments_for
Args: ['self', 'session']

Function _submission_row
Args: ['self', 'submission_id']

Function _assignment_row
Args: ['self', 'assignment_id']

Function _submission_payload
Args: ['self', 'submission_id']

Function _assignment_payload
Args: ['self', 'assignment_id']

Function _refresh_submission_status
Args: ['self', 'submission_id']

Function _analytics
Args: ['self']

Function _project_run_analytics
Args: ['self', 'project_id']

Function _alias
Args: ['self', 'prefix', 'seed']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\seed.py
Imports:
- __future__
- auth
- code_runner
- database
- docs_catalog
- permissions
- workspace

Function bootstrap_application
Args: ['repository', 'auth_service', 'docs_catalog', 'workspace_manager']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\server.py
Imports:
- __future__
- atexit
- base64
- json
- mimetypes
- re
- socket
- shutil
- http
- http.cookies
- http.server
- pathlib
- typing
- urllib.parse
- auth
- collaboration
- code_runner
- config
- curriculum
- database
- deployments
- docs_catalog
- distributed
- ai_service
- material_studio
- mentor
- nova_bridge
- permissions
- realtime
- reviews
- reference_library
- seed
- templates
- user_admin
- virtual_lecturer
- wiki_manual
- workspace

Class NovaSchoolApplication
- __init__(self, config)
- close(self)
- session_from_token(self, token)
- accessible_projects(self, session)
- project_payload(self, project)
- rooms_for(self, session, projects)
- public_settings(self, session)
- bootstrap_payload(self, session)
- template_catalog(self)
- get_project_for_session(self, session, project_id)
- can_access_project(self, session, project)
- can_manage_project_data(self, session, project)
- can_access_room(self, session, room_key)
- admin_overview(self)
- runtime_config_payload(self)
- server_settings_overview(self)
- model_root(self)
- local_model_files(self)
- default_llamacpp_model_path(self)
- default_llamacpp_model_label(self)
- default_litertlm_model_path(self)
- default_litertlm_model_label(self)
- default_litertlm_binary_path(self)
- default_ai_provider(self)

Class NovaSchoolRequestHandler
- do_GET(self)
- do_POST(self)
- do_PUT(self)
- do_DELETE(self)
- log_message(self, format)
- _dispatch(self, method)
- _handle_api(self, method, path, parsed)
- _handle_worker_api(self, method, path, segments)
- _serve_websocket(self, path)
- _serve_preview(self, path)
- _serve_share(self, path)
- _serve_download(self, path)
- _serve_manual(self, parsed)
- _serve_reference(self, parsed)
- _serve_certificate_verify(self, parsed)
- _serve_reference_asset(self, path)
- _serve_model_asset(self, path)
- _resolve_relative_file(root, relative_path)
- _serve_file(self, path, content_type)
- _current_session(self)
- _require_session(self)
- _require_worker(self)
- _require_permission(session, permission_key)
- _can_manage_server_settings(session)
- _require_server_settings_access(self, session)
- _certificate_verification_url(self, certificate_id)
- _configured_public_host(self)
- _request_scheme(self)
- _request_host(self)
- _request_origin(self)
- _external_base_url(self)
- _request_uses_tls(self)
- _read_json_body(self)
- _decode_uploaded_bundle(body)
- _read_raw_body(self)
- _send_json(self, status, payload)
- _send_bytes(self, status, payload)
- _send_html(self, status, content)
- _redirect(self, location)
- _token_from_request(self)
- _cookie_header(self, token)
- _clear_cookie_header(self)

Class Handler

Function create_application
Args: ['config']

Function run_server
Args: ['application']

Function _guess_lan_ipv4
Args: []

Function __init__
Args: ['self', 'config']

Function close
Args: ['self']

Function session_from_token
Args: ['self', 'token']

Function accessible_projects
Args: ['self', 'session']

Function project_payload
Args: ['self', 'project']

Function rooms_for
Args: ['self', 'session', 'projects']

Function public_settings
Args: ['self', 'session']

Function bootstrap_payload
Args: ['self', 'session']

Function template_catalog
Args: ['self']

Function get_project_for_session
Args: ['self', 'session', 'project_id']

Function can_access_project
Args: ['self', 'session', 'project']

Function can_manage_project_data
Args: ['self', 'session', 'project']

Function can_access_room
Args: ['self', 'session', 'room_key']

Function admin_overview
Args: ['self']

Function runtime_config_payload
Args: ['self']

Function server_settings_overview
Args: ['self']

Function model_root
Args: ['self']

Function local_model_files
Args: ['self']

Function default_llamacpp_model_path
Args: ['self']

Function default_llamacpp_model_label
Args: ['self']

Function default_litertlm_model_path
Args: ['self']

Function default_litertlm_model_label
Args: ['self']

Function default_litertlm_binary_path
Args: ['self']

Function default_ai_provider
Args: ['self']

Function do_GET
Args: ['self']

Function do_POST
Args: ['self']

Function do_PUT
Args: ['self']

Function do_DELETE
Args: ['self']

Function log_message
Args: ['self', 'format']

Function _dispatch
Args: ['self', 'method']

Function _handle_api
Args: ['self', 'method', 'path', 'parsed']

Function _handle_worker_api
Args: ['self', 'method', 'path', 'segments']

Function _serve_websocket
Args: ['self', 'path']

Function _serve_preview
Args: ['self', 'path']

Function _serve_share
Args: ['self', 'path']

Function _serve_download
Args: ['self', 'path']

Function _serve_manual
Args: ['self', 'parsed']

Function _serve_reference
Args: ['self', 'parsed']

Function _serve_certificate_verify
Args: ['self', 'parsed']

Function _serve_reference_asset
Args: ['self', 'path']

Function _serve_model_asset
Args: ['self', 'path']

Function _resolve_relative_file
Args: ['root', 'relative_path']

Function _serve_file
Args: ['self', 'path', 'content_type']

Function _current_session
Args: ['self']

Function _require_session
Args: ['self']

Function _require_worker
Args: ['self']

Function _require_permission
Args: ['session', 'permission_key']

Function _can_manage_server_settings
Args: ['session']

Function _require_server_settings_access
Args: ['self', 'session']

Function _certificate_verification_url
Args: ['self', 'certificate_id']

Function _configured_public_host
Args: ['self']

Function _request_scheme
Args: ['self']

Function _request_host
Args: ['self']

Function _request_origin
Args: ['self']

Function _external_base_url
Args: ['self']

Function _request_uses_tls
Args: ['self']

Function _read_json_body
Args: ['self']

Function _decode_uploaded_bundle
Args: ['body']

Function _read_raw_body
Args: ['self']

Function _send_json
Args: ['self', 'status', 'payload']

Function _send_bytes
Args: ['self', 'status', 'payload']

Function _send_html
Args: ['self', 'status', 'content']

Function _redirect
Args: ['self', 'location']

Function _token_from_request
Args: ['self']

Function _cookie_header
Args: ['self', 'token']

Function _clear_cookie_header
Args: ['self']

Function sort_key
Args: ['path']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\templates.py
Imports:
- __future__

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\user_admin.py
Imports:
- __future__
- hashlib
- io
- json
- shutil
- time
- zipfile
- pathlib
- typing
- auth
- config
- database
- workspace

Class UserAdministrationService
- __init__(self, repository, workspace_manager, config)
- sanitize_user(user)
- sanitize_users(self, users)
- update_user(self)
- permission_audit_payload(self, before, after)
- audit_entries(self, username, limit)
- retention_policy(self)
- export_user_data(self, username)
- hard_delete_user(self)
- export_project_archive(self)
- archive_project(self)
- hard_delete_project(self)
- apply_retention(self)
- _retention_days(self, key, default)
- _artifact_fs_path(self, row)
- _remove_path(self, path)
- _rows_to_dicts(self, query, params)
- _rows_to_dicts_optional(self, table_name, query, params)
- _execute_optional(self, table_name, query, params)
- _table_exists(self, table_name)
- _json_row(row, json_fields)
- _chat_export_payload(row)
- _project_export_payload(project)
- _group_chat_threads(self, rows)
- _group_mentor_threads(self, rows)
- _build_project_archive_bundle(self, project)

Function __init__
Args: ['self', 'repository', 'workspace_manager', 'config']

Function sanitize_user
Args: ['user']

Function sanitize_users
Args: ['self', 'users']

Function update_user
Args: ['self']

Function permission_audit_payload
Args: ['self', 'before', 'after']

Function audit_entries
Args: ['self', 'username', 'limit']

Function retention_policy
Args: ['self']

Function export_user_data
Args: ['self', 'username']

Function hard_delete_user
Args: ['self']

Function export_project_archive
Args: ['self']

Function archive_project
Args: ['self']

Function hard_delete_project
Args: ['self']

Function apply_retention
Args: ['self']

Function _retention_days
Args: ['self', 'key', 'default']

Function _artifact_fs_path
Args: ['self', 'row']

Function _remove_path
Args: ['self', 'path']

Function _rows_to_dicts
Args: ['self', 'query', 'params']

Function _rows_to_dicts_optional
Args: ['self', 'table_name', 'query', 'params']

Function _execute_optional
Args: ['self', 'table_name', 'query', 'params']

Function _table_exists
Args: ['self', 'table_name']

Function _json_row
Args: ['row', 'json_fields']

Function _chat_export_payload
Args: ['row']

Function _project_export_payload
Args: ['project']

Function _group_chat_threads
Args: ['self', 'rows']

Function _group_mentor_threads
Args: ['self', 'rows']

Function _build_project_archive_bundle
Args: ['self', 'project']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\virtual_lecturer.py
Imports:
- __future__
- json
- re
- time
- unicodedata
- uuid
- typing
- ai_service
- database

Class VirtualLecturerService
- __init__(self, repository)
- session(self, session, project)
- thread(self, session, project)
- start(self, session, project)
- prepare(self, session, project)
- store_reply(self, session, project)
- _session_row(self, project_id, username)
- _session_payload(row)
- _touch_session(self, project_id, username)
- _resolve_course_state(self, session)
- _session_metadata(self, course_state)
- _practice_payload(self, course, module)
- _opening_message(self, session, project, metadata)
- _compose_prompt(self)
- _direct_reply(self)
- _python_intro_run_feedback(self)
- _web_frontend_intro_feedback(self)
- _fold_text(text)
- _visible_output_lines(cls, run_output)
- _count_print_calls(code)
- _contains_runtime_error(cls, run_output)
- _extract_html_tags(code)
- _prompt_requests_state_review(cls, prompt)
- _sanitize_reply(reply)
- _lesson_focus(lesson_markdown)
- _room_key(project_id, username, session_id)
- _ensure_schema(self)

Function __init__
Args: ['self', 'repository']

Function session
Args: ['self', 'session', 'project']

Function thread
Args: ['self', 'session', 'project']

Function start
Args: ['self', 'session', 'project']

Function prepare
Args: ['self', 'session', 'project']

Function store_reply
Args: ['self', 'session', 'project']

Function _session_row
Args: ['self', 'project_id', 'username']

Function _session_payload
Args: ['row']

Function _touch_session
Args: ['self', 'project_id', 'username']

Function _resolve_course_state
Args: ['self', 'session']

Function _session_metadata
Args: ['self', 'course_state']

Function _practice_payload
Args: ['self', 'course', 'module']

Function _opening_message
Args: ['self', 'session', 'project', 'metadata']

Function _compose_prompt
Args: ['self']

Function _direct_reply
Args: ['self']

Function _python_intro_run_feedback
Args: ['self']

Function _web_frontend_intro_feedback
Args: ['self']

Function _fold_text
Args: ['text']

Function _visible_output_lines
Args: ['cls', 'run_output']

Function _count_print_calls
Args: ['code']

Function _contains_runtime_error
Args: ['cls', 'run_output']

Function _extract_html_tags
Args: ['code']

Function _prompt_requests_state_review
Args: ['cls', 'prompt']

Function _sanitize_reply
Args: ['reply']

Function _lesson_focus
Args: ['lesson_markdown']

Function _room_key
Args: ['project_id', 'username', 'session_id']

Function _ensure_schema
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\wiki_manual.py
Imports:
- __future__
- html
- re
- pathlib
- typing
- urllib.parse

Class WikiManualService
- __init__(self, wiki_root)
- ensure_seed_manuals(self)
- allowed_scopes(self, session)
- default_scope(self, session)
- render_page(self, session, requested_scope, requested_page)
- documents(self, scope)
- _resolve_scope(self, session, requested_scope)
- _scope_folder(self, scope)
- _document_sort_key(path)
- _extract_title(content, path)
- _collect_toc(self, content)
- _markdown_to_html(self, source)
- _is_table_header(lines, index)
- _render_table(self, lines, index, scope)
- _parse_table_row(row)
- _render_inline(self, text)
- _render_plain_inline(text)
- _resolve_link(self, current_scope, target)
- _anchor_id(title, seen)
- _render_shell(self)

Function __init__
Args: ['self', 'wiki_root']

Function ensure_seed_manuals
Args: ['self']

Function allowed_scopes
Args: ['self', 'session']

Function default_scope
Args: ['self', 'session']

Function render_page
Args: ['self', 'session', 'requested_scope', 'requested_page']

Function documents
Args: ['self', 'scope']

Function _resolve_scope
Args: ['self', 'session', 'requested_scope']

Function _scope_folder
Args: ['self', 'scope']

Function _document_sort_key
Args: ['path']

Function _extract_title
Args: ['content', 'path']

Function _collect_toc
Args: ['self', 'content']

Function _markdown_to_html
Args: ['self', 'source']

Function _is_table_header
Args: ['lines', 'index']

Function _render_table
Args: ['self', 'lines', 'index', 'scope']

Function _parse_table_row
Args: ['row']

Function _render_inline
Args: ['self', 'text']

Function _render_plain_inline
Args: ['text']

Function _resolve_link
Args: ['self', 'current_scope', 'target']

Function _anchor_id
Args: ['title', 'seen']

Function _render_shell
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\worker_agent.py
Imports:
- __future__
- argparse
- hashlib
- hmac
- json
- os
- queue
- secrets
- shutil
- socket
- subprocess
- threading
- time
- urllib.request
- urllib.parse
- zipfile
- pathlib
- typing
- archive_utils
- container_seccomp
- worker_dispatch

Class WorkerAgent
- __init__(self)
- run_forever(self)
- _run_job(self, job)
- _pump_stdout(process, log_queue)
- _drain_logs(self, job_id, log_queue, buffer)
- _heartbeat(self)
- _request_json(self, method, path, payload)
- _download(self, url, target)
- _verify_artifact_integrity(job, artifact_path)
- _verify_job(self, job)
- _signed_headers(self, method, path, body)
- _build_command(self, job, runtime_root)
- _service_url(self, payload)
- _wrap_container_command(base_command, inner_command)
- _mirror_tree_securely(self, source_root, target_root)
- _copy_tree_entries_securely(self, source_dir, target_dir, ignored_names)
- _is_link_like(path)
- _container_seccomp_option(runtime_name)

Function _container_file_size_limit_bytes
Args: ['raw_value']

Function _default_advertise_host
Args: []

Function main
Args: []

Function __init__
Args: ['self']

Function run_forever
Args: ['self']

Function _run_job
Args: ['self', 'job']

Function _pump_stdout
Args: ['process', 'log_queue']

Function _drain_logs
Args: ['self', 'job_id', 'log_queue', 'buffer']

Function _heartbeat
Args: ['self']

Function _request_json
Args: ['self', 'method', 'path', 'payload']

Function _download
Args: ['self', 'url', 'target']

Function _verify_artifact_integrity
Args: ['job', 'artifact_path']

Function _verify_job
Args: ['self', 'job']

Function _signed_headers
Args: ['self', 'method', 'path', 'body']

Function _build_command
Args: ['self', 'job', 'runtime_root']

Function _service_url
Args: ['self', 'payload']

Function _wrap_container_command
Args: ['base_command', 'inner_command']

Function _mirror_tree_securely
Args: ['self', 'source_root', 'target_root']

Function _copy_tree_entries_securely
Args: ['self', 'source_dir', 'target_dir', 'ignored_names']

Function _is_link_like
Args: ['path']

Function _container_seccomp_option
Args: ['runtime_name']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\worker_dispatch.py
Imports:
- __future__
- hashlib
- hmac
- json
- secrets
- shutil
- socket
- time
- zipfile
- pathlib
- typing
- config
- database
- workspace

Class RemoteWorkerDispatchService
- __init__(self, repository, workspace_manager, security_plane, config)
- issue_bootstrap(self)
- authenticate_worker(self, worker_id, token)
- verify_worker_request(self, worker_id, token)
- heartbeat(self, worker_id)
- list_workers(self)
- eligible_workers(self, runtime)
- assign_workers(self, services)
- create_playground_job(self)
- claim_next_job(self, worker_id)
- resolve_job_artifact(self, job_id)
- append_job_log(self, worker_id, job_id, chunk)
- update_job_status(self, worker_id, job_id)
- request_stop(self, job_id)
- latest_jobs_for_project(self, project_id)
- sign_job_payload(self, worker_id, payload)
- build_worker_signature()
- server_base_url(self)
- _present_worker(self, worker)
- _is_online(self, worker)
- _worker_loads(self)
- _ensure_worker_enrollment(self, worker_id)
- _worker_enrollment(self, worker_id)
- _resolve_secret(self, secret_name)
- _require_job_owner(self, worker_id, job_id)
- _job_signature_payload(payload)
- _write_artifact(self, job_id, runtime_root)
- _artifact_sha256(self, job_id)
- _job_root(self, job_id)
- _secret_name(worker_id)
- _guess_lan_ipv4()

Function __init__
Args: ['self', 'repository', 'workspace_manager', 'security_plane', 'config']

Function issue_bootstrap
Args: ['self']

Function authenticate_worker
Args: ['self', 'worker_id', 'token']

Function verify_worker_request
Args: ['self', 'worker_id', 'token']

Function heartbeat
Args: ['self', 'worker_id']

Function list_workers
Args: ['self']

Function eligible_workers
Args: ['self', 'runtime']

Function assign_workers
Args: ['self', 'services']

Function create_playground_job
Args: ['self']

Function claim_next_job
Args: ['self', 'worker_id']

Function resolve_job_artifact
Args: ['self', 'job_id']

Function append_job_log
Args: ['self', 'worker_id', 'job_id', 'chunk']

Function update_job_status
Args: ['self', 'worker_id', 'job_id']

Function request_stop
Args: ['self', 'job_id']

Function latest_jobs_for_project
Args: ['self', 'project_id']

Function sign_job_payload
Args: ['self', 'worker_id', 'payload']

Function build_worker_signature
Args: []

Function server_base_url
Args: ['self']

Function _present_worker
Args: ['self', 'worker']

Function _is_online
Args: ['self', 'worker']

Function _worker_loads
Args: ['self']

Function _ensure_worker_enrollment
Args: ['self', 'worker_id']

Function _worker_enrollment
Args: ['self', 'worker_id']

Function _resolve_secret
Args: ['self', 'secret_name']

Function _require_job_owner
Args: ['self', 'worker_id', 'job_id']

Function _job_signature_payload
Args: ['payload']

Function _write_artifact
Args: ['self', 'job_id', 'runtime_root']

Function _artifact_sha256
Args: ['self', 'job_id']

Function _job_root
Args: ['self', 'job_id']

Function _secret_name
Args: ['worker_id']

Function _guess_lan_ipv4
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\workspace.py
Imports:
- __future__
- json
- re
- shutil
- pathlib
- typing
- config
- templates

Class WorkspaceManager
- __init__(self, config)
- ensure_profile_folder(self, owner_type, owner_key)
- owner_root(self, owner_type, owner_key)
- project_root(self, project)
- materialize_project(self, project)
- list_tree(self, project)
- read_file(self, project, relative_path)
- write_file(self, project, relative_path, content)
- create_directory(self, project, relative_path)
- delete_file(self, project, relative_path)
- delete_entry(self, project, relative_path)
- rename_entry(self, project, relative_path, new_relative_path)
- load_notebook(self, project)
- save_notebook(self, project, cells)
- resolve_project_path(self, project, relative_path)
- _normalize_relative_path(relative_path)
- _path_matches_or_contains(prefix, candidate)
- _renamed_path(candidate, old_path, new_path)
- _notebook_path(self, project)
- _prune_empty_parent_dirs(start, stop_root)
- _normalize_legacy_notebook_cell(cell)

Function slugify
Args: ['value']

Function __init__
Args: ['self', 'config']

Function ensure_profile_folder
Args: ['self', 'owner_type', 'owner_key']

Function owner_root
Args: ['self', 'owner_type', 'owner_key']

Function project_root
Args: ['self', 'project']

Function materialize_project
Args: ['self', 'project']

Function list_tree
Args: ['self', 'project']

Function read_file
Args: ['self', 'project', 'relative_path']

Function write_file
Args: ['self', 'project', 'relative_path', 'content']

Function create_directory
Args: ['self', 'project', 'relative_path']

Function delete_file
Args: ['self', 'project', 'relative_path']

Function delete_entry
Args: ['self', 'project', 'relative_path']

Function rename_entry
Args: ['self', 'project', 'relative_path', 'new_relative_path']

Function load_notebook
Args: ['self', 'project']

Function save_notebook
Args: ['self', 'project', 'cells']

Function resolve_project_path
Args: ['self', 'project', 'relative_path']

Function _normalize_relative_path
Args: ['relative_path']

Function _path_matches_or_contains
Args: ['prefix', 'candidate']

Function _renamed_path
Args: ['candidate', 'old_path', 'new_path']

Function _notebook_path
Args: ['self', 'project']

Function _prune_empty_parent_dirs
Args: ['start', 'stop_root']

Function _normalize_legacy_notebook_cell
Args: ['cell']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\__init__.py
Imports:
- __future__

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\__main__.py
Imports:
- __future__
- os
- pathlib
- config
- server

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\Linux\materialize_linux_project.py
Imports:
- __future__
- sys
- pathlib
- nova_bootstrap
- nova_school_server.distribution_builder

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\Linux\nova_linux_launch.py
Imports:
- __future__
- os
- sys
- pathlib
- nova_bootstrap
- nova_school_server.config
- nova_school_server.server

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\Linux\nova_linux_worker_launch.py
Imports:
- __future__
- sys
- pathlib
- nova_bootstrap
- nova_school_server.worker_agent

Function main
Args: []

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_ai_service.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- unittest.mock
- nova_school_server.ai_service
- nova_school_server.database

Class LlamaCppServiceTests
- setUp(self)
- tearDown(self)
- test_status_prefers_local_gguf_model(self)
- test_status_uses_explicit_model_override(self)
- test_prepare_direct_completion_builds_server_prompt(self)

Class LiteRTLmServiceTests
- setUp(self)
- tearDown(self)
- test_status_prefers_local_litert_model(self)
- test_status_auto_discovers_project_local_lit_folder(self)
- test_status_auto_discovers_linux_lit_binary(self)
- test_auto_provider_prefers_litert_when_binary_and_model_exist(self)
- test_local_ai_service_proxies_max_tokens_to_active_provider(self)
- test_prepare_direct_completion_builds_server_prompt(self)
- test_prepare_direct_completion_trims_large_code_context(self)
- test_complete_ignores_xnnpack_info_only_error_output(self)

Class _Result

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_status_prefers_local_gguf_model
Args: ['self']

Function test_status_uses_explicit_model_override
Args: ['self']

Function test_prepare_direct_completion_builds_server_prompt
Args: ['self']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_status_prefers_local_litert_model
Args: ['self']

Function test_status_auto_discovers_project_local_lit_folder
Args: ['self']

Function test_status_auto_discovers_linux_lit_binary
Args: ['self']

Function test_auto_provider_prefers_litert_when_binary_and_model_exist
Args: ['self']

Function test_local_ai_service_proxies_max_tokens_to_active_provider
Args: ['self']

Function test_prepare_direct_completion_builds_server_prompt
Args: ['self']

Function test_prepare_direct_completion_trims_large_code_context
Args: ['self']

Function test_complete_ignores_xnnpack_info_only_error_output
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_analysis_archive_builder.py
Imports:
- __future__
- subprocess
- tempfile
- unittest
- zipfile
- pathlib
- nova_school_server.analysis_archive_builder

Class SourceAnalysisArchiveBuilderTests
- test_build_source_analysis_archive_keeps_text_source_and_skips_binaries(self)
- _git(repo)

Function test_build_source_analysis_archive_keeps_text_source_and_skips_binaries
Args: ['self']

Function _git
Args: ['repo']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_archive_utils.py
Imports:
- __future__
- stat
- tempfile
- unittest
- zipfile
- pathlib
- nova_school_server.archive_utils

Class ArchiveUtilsTests
- test_extract_zip_safely_writes_normal_files(self)
- test_extract_zip_safely_rejects_traversal(self)
- test_extract_zip_safely_rejects_symlink_entries(self)

Function test_extract_zip_safely_writes_normal_files
Args: ['self']

Function test_extract_zip_safely_rejects_traversal
Args: ['self']

Function test_extract_zip_safely_rejects_symlink_entries
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_codedump_tools.py
Imports:
- __future__
- tempfile
- unittest
- zipfile
- pathlib
- nova_school_server.codedump_tools

Class CodeDumpToolsTests
- test_directory_dump_ignores_runtime_data_and_writes_markdown(self)
- test_zip_dump_keeps_zip_support(self)
- test_directory_collect_marks_large_files_with_placeholder(self)
- test_compact_profile_excludes_docs_wiki_and_tests(self)
- test_deep_profile_includes_docs_wiki_and_tests(self)
- test_default_output_path_uses_profile_suffix_for_non_standard_profiles(self)
- test_existing_dump_artifacts_are_not_reincluded(self)

Function test_directory_dump_ignores_runtime_data_and_writes_markdown
Args: ['self']

Function test_zip_dump_keeps_zip_support
Args: ['self']

Function test_directory_collect_marks_large_files_with_placeholder
Args: ['self']

Function test_compact_profile_excludes_docs_wiki_and_tests
Args: ['self']

Function test_deep_profile_includes_docs_wiki_and_tests
Args: ['self']

Function test_default_output_path_uses_profile_suffix_for_non_standard_profiles
Args: ['self']

Function test_existing_dump_artifacts_are_not_reincluded
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_code_runner.py
Imports:
- __future__
- os
- tempfile
- threading
- time
- unittest
- pathlib
- unittest.mock
- nova_school_server.code_runner
- nova_school_server.config
- nova_school_server.workspace

Class _FakeToolSandbox
- authorize(self)

Class _FakeRepository
- __init__(self, settings)
- get_setting(self, key, default)

Class _ObservedCodeRunner
- __init__(self)
- _execute(self, run_id, language, command, cwd, stdin_text, env, tool_session, permissions)

Class _ContainerObservedRunner
- __init__(self)
- _execute_raw(self, command, cwd, stdin_text, env)
- _execute_container(self, run_id, language, runtime_executable, image, inner_command, project_root, container_workspace, stdin_text, env, tool_session, permissions)

Class _Session

Class _TeacherSession

Class CodeRunnerTests
- test_execute_container_python_hides_bootstrap_frames_from_traceback(self)
- test_execute_python_process_hides_bootstrap_frames_from_traceback(self)
- test_run_bundle_executes_python_without_project_record(self)
- test_run_bundle_returns_python_syntax_error_before_execution(self)
- test_runner_backend_uses_valid_repository_setting(self)
- test_runner_backend_falls_back_for_invalid_repository_setting(self)
- test_process_backend_requires_explicit_unsafe_enablement(self)
- test_html_preview_bypasses_process_backend_block(self)
- test_python_project_run_uses_main_file_even_when_helper_is_open(self)
- test_javascript_project_run_uses_main_file_even_when_helper_is_open(self)
- test_cpp_project_run_compiles_all_project_sources(self)
- test_java_project_run_compiles_all_sources_and_uses_main_class(self)
- test_scheduler_serializes_same_student_user(self)
- test_container_base_command_disables_network_without_web_access(self)
- test_container_base_command_enables_bridge_with_web_access(self)
- test_container_base_command_includes_configured_oci_runtime(self)
- test_container_base_command_converts_file_size_limit_from_kb_to_bytes(self)
- test_execution_env_requires_proxy_when_enforced(self)
- test_containerized_env_does_not_forward_windows_host_path(self)
- test_container_runtime_error_message_explains_missing_docker_desktop_engine(self)
- test_container_runtime_error_message_explains_internal_server_error(self)
- test_container_runtime_error_message_explains_timeout(self)
- test_container_runtime_error_message_explains_linux_docker_socket_permissions(self)
- test_container_runtime_health_fails_fast_before_run(self)
- test_container_runtime_health_uses_generous_timeout(self)
- test_run_bundle_auto_pulls_missing_container_image(self)
- test_student_run_hides_operational_notes(self)
- test_teacher_run_keeps_operational_notes(self)
- test_student_live_run_hides_operational_notes(self)
- test_backend_notes_omit_default_image_placeholder(self)
- test_python_executable_does_not_receive_py_launcher_flag(self)
- test_run_python_supports_stdin_input(self)
- test_run_python_reports_syntax_error_before_execution(self)
- test_prepare_live_python_reports_syntax_error_before_launch(self)
- test_run_python_uses_bootstrap_and_dependency_env_with_requirements(self)
- test_containerized_python_gui_returns_preview_path(self)
- test_containerized_python_mainloop_without_direct_import_uses_gui_path(self)

Function authorize
Args: ['self']

Function __init__
Args: ['self', 'settings']

Function get_setting
Args: ['self', 'key', 'default']

Function __init__
Args: ['self']

Function _execute
Args: ['self', 'run_id', 'language', 'command', 'cwd', 'stdin_text', 'env', 'tool_session', 'permissions']

Function __init__
Args: ['self']

Function _execute_raw
Args: ['self', 'command', 'cwd', 'stdin_text', 'env']

Function _execute_container
Args: ['self', 'run_id', 'language', 'runtime_executable', 'image', 'inner_command', 'project_root', 'container_workspace', 'stdin_text', 'env', 'tool_session', 'permissions']

Function test_execute_container_python_hides_bootstrap_frames_from_traceback
Args: ['self']

Function test_execute_python_process_hides_bootstrap_frames_from_traceback
Args: ['self']

Function test_run_bundle_executes_python_without_project_record
Args: ['self']

Function test_run_bundle_returns_python_syntax_error_before_execution
Args: ['self']

Function test_runner_backend_uses_valid_repository_setting
Args: ['self']

Function test_runner_backend_falls_back_for_invalid_repository_setting
Args: ['self']

Function test_process_backend_requires_explicit_unsafe_enablement
Args: ['self']

Function test_html_preview_bypasses_process_backend_block
Args: ['self']

Function test_python_project_run_uses_main_file_even_when_helper_is_open
Args: ['self']

Function test_javascript_project_run_uses_main_file_even_when_helper_is_open
Args: ['self']

Function test_cpp_project_run_compiles_all_project_sources
Args: ['self']

Function test_java_project_run_compiles_all_sources_and_uses_main_class
Args: ['self']

Function test_scheduler_serializes_same_student_user
Args: ['self']

Function test_container_base_command_disables_network_without_web_access
Args: ['self']

Function test_container_base_command_enables_bridge_with_web_access
Args: ['self']

Function test_container_base_command_includes_configured_oci_runtime
Args: ['self']

Function test_container_base_command_converts_file_size_limit_from_kb_to_bytes
Args: ['self']

Function test_execution_env_requires_proxy_when_enforced
Args: ['self']

Function test_containerized_env_does_not_forward_windows_host_path
Args: ['self']

Function test_container_runtime_error_message_explains_missing_docker_desktop_engine
Args: ['self']

Function test_container_runtime_error_message_explains_internal_server_error
Args: ['self']

Function test_container_runtime_error_message_explains_timeout
Args: ['self']

Function test_container_runtime_error_message_explains_linux_docker_socket_permissions
Args: ['self']

Function test_container_runtime_health_fails_fast_before_run
Args: ['self']

Function test_container_runtime_health_uses_generous_timeout
Args: ['self']

Function test_run_bundle_auto_pulls_missing_container_image
Args: ['self']

Function test_student_run_hides_operational_notes
Args: ['self']

Function test_teacher_run_keeps_operational_notes
Args: ['self']

Function test_student_live_run_hides_operational_notes
Args: ['self']

Function test_backend_notes_omit_default_image_placeholder
Args: ['self']

Function test_python_executable_does_not_receive_py_launcher_flag
Args: ['self']

Function test_run_python_supports_stdin_input
Args: ['self']

Function test_run_python_reports_syntax_error_before_execution
Args: ['self']

Function test_prepare_live_python_reports_syntax_error_before_launch
Args: ['self']

Function test_run_python_uses_bootstrap_and_dependency_env_with_requirements
Args: ['self']

Function test_containerized_python_gui_returns_preview_path
Args: ['self']

Function test_containerized_python_mainloop_without_direct_import_uses_gui_path
Args: ['self']

Function fake_execute_raw
Args: ['command', 'cwd', 'stdin_text', 'env']

Function fake_execute_raw
Args: ['command', 'cwd', 'stdin_text', 'env']

Function worker
Args: []

Function fake_execute_raw
Args: ['command', 'cwd', 'stdin_text', 'env']

Function fake_execute_raw
Args: ['command', 'cwd', 'stdin_text', 'env']

Function fake_execute_raw
Args: ['command', 'cwd', 'stdin_text', 'env']

Function fake_execute_raw
Args: ['command', 'cwd', 'stdin_text', 'env']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_config.py
Imports:
- __future__
- os
- tempfile
- unittest
- pathlib
- nova_school_server.config
- nova_school_server.config

Class ConfigTests
- test_default_host_binds_for_lan(self)
- test_env_host_override_is_respected(self)
- test_server_config_payload_is_saved_and_loaded(self)
- test_stored_runtime_config_falls_back_to_active_values(self)
- test_runtime_config_requires_restart_when_stored_values_differ(self)
- test_static_path_falls_back_to_real_package_root_for_flat_repo_layout(self)

Function test_default_host_binds_for_lan
Args: ['self']

Function test_env_host_override_is_respected
Args: ['self']

Function test_server_config_payload_is_saved_and_loaded
Args: ['self']

Function test_stored_runtime_config_falls_back_to_active_values
Args: ['self']

Function test_runtime_config_requires_restart_when_stored_values_differ
Args: ['self']

Function test_static_path_falls_back_to_real_package_root_for_flat_repo_layout
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_container_seccomp.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- unittest.mock
- nova_school_server.container_seccomp

Class ContainerSeccompTests
- test_resolve_seccomp_profile_option_returns_native_path_for_non_docker_runtime(self)
- test_resolve_seccomp_profile_option_uses_builtin_profile_for_windows_docker(self)

Function test_resolve_seccomp_profile_option_returns_native_path_for_non_docker_runtime
Args: ['self']

Function test_resolve_seccomp_profile_option_uses_builtin_profile_for_windows_docker
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_curriculum.py
Imports:
- __future__
- hashlib
- hmac
- io
- json
- tempfile
- time
- unittest
- zipfile
- pathlib
- PIL
- nova_school_server.curriculum
- nova_school_server.curriculum_catalog
- nova_school_server.database

Class _Session
- __init__(self, username)

Class CurriculumServiceTests
- setUp(self)
- tearDown(self)
- test_course_is_available_by_default_for_student(self)
- test_explicit_user_disable_locks_course_for_student(self)
- test_dashboard_exposes_multiple_courses(self)
- test_group_release_enables_course_for_group_member(self)
- test_module_progression_unlocks_next_module(self)
- test_final_exam_issues_certificate_after_all_modules(self)
- test_attempt_history_returns_all_submissions_for_teacher_view(self)
- test_certificate_pdf_is_generated_with_school_branding(self)
- test_course_specific_certificate_design_renders_subject_label(self)
- test_cpp_course_can_be_completed_and_renders_subject_label(self)
- test_java_course_can_be_completed_and_renders_subject_label(self)
- test_verification_page_renders_certificate_details(self)
- test_custom_course_is_persisted_and_visible_in_dashboard(self)
- test_custom_course_uses_final_exam_threshold_and_issues_certificate(self)
- test_bundle_import_activation_and_rollback_switch_course_definition(self)
- test_dashboard_manager_exposes_bundle_controls_only_for_update_permission(self)
- test_bundle_material_preset_and_mentor_rule_are_resolved_from_active_bundle(self)

Function _correct_answers
Args: ['questions']

Function _custom_course_payload
Args: []

Function _bundle_archive_bytes
Args: []

Function __init__
Args: ['self', 'username']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_course_is_available_by_default_for_student
Args: ['self']

Function test_explicit_user_disable_locks_course_for_student
Args: ['self']

Function test_dashboard_exposes_multiple_courses
Args: ['self']

Function test_group_release_enables_course_for_group_member
Args: ['self']

Function test_module_progression_unlocks_next_module
Args: ['self']

Function test_final_exam_issues_certificate_after_all_modules
Args: ['self']

Function test_attempt_history_returns_all_submissions_for_teacher_view
Args: ['self']

Function test_certificate_pdf_is_generated_with_school_branding
Args: ['self']

Function test_course_specific_certificate_design_renders_subject_label
Args: ['self']

Function test_cpp_course_can_be_completed_and_renders_subject_label
Args: ['self']

Function test_java_course_can_be_completed_and_renders_subject_label
Args: ['self']

Function test_verification_page_renders_certificate_details
Args: ['self']

Function test_custom_course_is_persisted_and_visible_in_dashboard
Args: ['self']

Function test_custom_course_uses_final_exam_threshold_and_issues_certificate
Args: ['self']

Function test_bundle_import_activation_and_rollback_switch_course_definition
Args: ['self']

Function test_dashboard_manager_exposes_bundle_controls_only_for_update_permission
Args: ['self']

Function test_bundle_material_preset_and_mentor_rule_are_resolved_from_active_bundle
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_distribution_builder.py
Imports:
- __future__
- tempfile
- unittest
- zipfile
- pathlib
- nova_school_server.distribution_builder

Class DistributionBuilderTests
- test_distribution_archive_excludes_runtime_data_and_adds_scaffold(self)
- test_windows_server_package_excludes_linux_scripts_and_adds_windows_guide(self)
- test_linux_server_package_excludes_windows_scripts_and_adds_linux_guide(self)
- test_materialize_distribution_directory_skips_generated_linux_project_recursion(self)
- test_materialized_linux_project_copies_linux_lit_binary_but_not_models(self)
- test_linux_project_archive_includes_linux_runtime_binary_and_pure_linux_guide(self)

Function test_distribution_archive_excludes_runtime_data_and_adds_scaffold
Args: ['self']

Function test_windows_server_package_excludes_linux_scripts_and_adds_windows_guide
Args: ['self']

Function test_linux_server_package_excludes_windows_scripts_and_adds_linux_guide
Args: ['self']

Function test_materialize_distribution_directory_skips_generated_linux_project_recursion
Args: ['self']

Function test_materialized_linux_project_copies_linux_lit_binary_but_not_models
Args: ['self']

Function test_linux_project_archive_includes_linux_runtime_binary_and_pure_linux_guide
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_docs.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.docs_catalog

Class DocumentationTests
- test_seed_docs_and_read_python_doc(self)

Function test_seed_docs_and_read_python_doc
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_gold_features.py
Imports:
- __future__
- json
- tempfile
- time
- unittest
- zipfile
- pathlib
- unittest.mock
- nova_school_server.collaboration
- nova_school_server.code_runner
- nova_school_server.config
- nova_school_server.database
- nova_school_server.deployments
- nova_school_server.distributed
- nova_school_server.mentor
- nova_school_server.reviews
- nova_school_server.workspace

Class _FakeSecurityPlane
- __init__(self)
- resolve_secret(self, tenant_id, name)
- store_secret(self, tenant_id, name, secret_value, metadata)
- get_tenant(self, tenant_id)
- create_certificate_authority(self, name, common_name)
- get_certificate_authority(self, name)
- set_trust_policy(self, name)
- get_trust_policy(self, name)
- onboard_worker(self, worker_id, tenant_id)
- list_worker_enrollments(self, tenant_id)

Class _Session
- __init__(self, username, role)
- is_teacher(self)
- group_ids(self)

Class _FakeToolSandbox
- authorize(self)

Class GoldFeatureTests
- setUp(self)
- tearDown(self)
- _create_user(self, username, role)
- _create_project(self)
- test_collaboration_merges_parallel_cell_changes(self)
- test_mentor_persists_thread_and_teacher_can_inspect(self)
- test_review_submission_feedback_and_deployment_artifacts_work(self)
- test_distributed_playground_starts_and_stops_template_services(self)
- test_distributed_playground_dispatches_remote_jobs_to_registered_workers(self)
- test_worker_request_signature_rejects_replay(self)

Function __init__
Args: ['self']

Function resolve_secret
Args: ['self', 'tenant_id', 'name']

Function store_secret
Args: ['self', 'tenant_id', 'name', 'secret_value', 'metadata']

Function get_tenant
Args: ['self', 'tenant_id']

Function create_certificate_authority
Args: ['self', 'name', 'common_name']

Function get_certificate_authority
Args: ['self', 'name']

Function set_trust_policy
Args: ['self', 'name']

Function get_trust_policy
Args: ['self', 'name']

Function onboard_worker
Args: ['self', 'worker_id', 'tenant_id']

Function list_worker_enrollments
Args: ['self', 'tenant_id']

Function __init__
Args: ['self', 'username', 'role']

Function is_teacher
Args: ['self']

Function group_ids
Args: ['self']

Function authorize
Args: ['self']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function _create_user
Args: ['self', 'username', 'role']

Function _create_project
Args: ['self']

Function test_collaboration_merges_parallel_cell_changes
Args: ['self']

Function test_mentor_persists_thread_and_teacher_can_inspect
Args: ['self']

Function test_review_submission_feedback_and_deployment_artifacts_work
Args: ['self']

Function test_distributed_playground_starts_and_stops_template_services
Args: ['self']

Function test_distributed_playground_dispatches_remote_jobs_to_registered_workers
Args: ['self']

Function test_worker_request_signature_rejects_replay
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_material_studio.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.database
- nova_school_server.material_studio

Class _FakeRunner
- __init__(self, results)
- run_bundle(self, _session, payload)

Class _FakeAI
- __init__(self, responses)
- complete(self)

Class _FakeCurriculumService
- __init__(self, preset)
- resolve_material_studio_instruction_preset(self, preset_key)

Class _TeacherSession

Class MaterialStudioTests
- setUp(self)
- tearDown(self)
- test_profile_catalog_contains_specialized_teacher_profiles(self)
- test_instruction_preset_catalog_contains_python_course_entries_for_worksheet_and_example_code(self)
- test_instruction_preset_catalog_covers_every_supported_language_with_both_profiles(self)
- test_curriculum_service_can_override_instruction_preset_resolution(self)
- test_extract_json_object_merges_multiple_fenced_objects(self)
- test_extract_json_object_accepts_jsonish_string_concatenation(self)
- test_extract_code_block_prefers_nested_language_block_over_outer_text_wrapper(self)
- test_extract_code_block_recovers_trailing_code_from_unclosed_fence(self)
- test_parse_code_response_accepts_plain_python_code_without_fence(self)
- test_parse_code_response_rejects_self_evaluation_prose(self)
- test_parse_code_response_rejects_python_main_without_invocation(self)
- test_generation_flow_runs_planning_authoring_and_pedagogy(self)
- test_generation_flow_falls_back_from_invalid_author_json_to_code_block(self)
- test_quality_pipeline_starts_with_real_plan_then_author_json(self)
- test_generation_flow_repairs_invalid_pedagogy_json(self)
- test_generation_flow_repairs_failed_run_via_debugger_code_fallback(self)
- test_attempt_limit_counts_repair_rounds_after_initial_run(self)
- test_author_prompt_requires_stdin_or_eof_safe_input(self)
- test_litert_plan_prompt_is_trimmed_to_budget(self)
- test_complete_inference_payload_retries_with_stricter_budget_after_litert_token_error(self)
- test_direct_generate_uses_one_repair_round_when_attempt_limit_is_one(self)
- test_direct_generate_uses_example_code_instruction_preset(self)
- test_run_current_builds_bundle_from_code_only(self)

Function __init__
Args: ['self', 'results']

Function run_bundle
Args: ['self', '_session', 'payload']

Function __init__
Args: ['self', 'responses']

Function complete
Args: ['self']

Function __init__
Args: ['self', 'preset']

Function resolve_material_studio_instruction_preset
Args: ['self', 'preset_key']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_profile_catalog_contains_specialized_teacher_profiles
Args: ['self']

Function test_instruction_preset_catalog_contains_python_course_entries_for_worksheet_and_example_code
Args: ['self']

Function test_instruction_preset_catalog_covers_every_supported_language_with_both_profiles
Args: ['self']

Function test_curriculum_service_can_override_instruction_preset_resolution
Args: ['self']

Function test_extract_json_object_merges_multiple_fenced_objects
Args: ['self']

Function test_extract_json_object_accepts_jsonish_string_concatenation
Args: ['self']

Function test_extract_code_block_prefers_nested_language_block_over_outer_text_wrapper
Args: ['self']

Function test_extract_code_block_recovers_trailing_code_from_unclosed_fence
Args: ['self']

Function test_parse_code_response_accepts_plain_python_code_without_fence
Args: ['self']

Function test_parse_code_response_rejects_self_evaluation_prose
Args: ['self']

Function test_parse_code_response_rejects_python_main_without_invocation
Args: ['self']

Function test_generation_flow_runs_planning_authoring_and_pedagogy
Args: ['self']

Function test_generation_flow_falls_back_from_invalid_author_json_to_code_block
Args: ['self']

Function test_quality_pipeline_starts_with_real_plan_then_author_json
Args: ['self']

Function test_generation_flow_repairs_invalid_pedagogy_json
Args: ['self']

Function test_generation_flow_repairs_failed_run_via_debugger_code_fallback
Args: ['self']

Function test_attempt_limit_counts_repair_rounds_after_initial_run
Args: ['self']

Function test_author_prompt_requires_stdin_or_eof_safe_input
Args: ['self']

Function test_litert_plan_prompt_is_trimmed_to_budget
Args: ['self']

Function test_complete_inference_payload_retries_with_stricter_budget_after_litert_token_error
Args: ['self']

Function test_direct_generate_uses_one_repair_round_when_attempt_limit_is_one
Args: ['self']

Function test_direct_generate_uses_example_code_instruction_preset
Args: ['self']

Function test_run_current_builds_bundle_from_code_only
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_mentor.py
Imports:
- __future__
- hashlib
- hmac
- io
- json
- tempfile
- time
- unittest
- zipfile
- pathlib
- nova_school_server.ai_service
- nova_school_server.curriculum
- nova_school_server.database
- nova_school_server.mentor

Class _Session
- __init__(self, username)

Class MentorTests
- setUp(self)
- tearDown(self)
- test_prepare_includes_curriculum_context_and_bundle_mentor_rules(self)
- test_prepare_trims_large_runtime_context(self)

Function _bundle_archive
Args: ['secret']

Function __init__
Args: ['self', 'username']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_prepare_includes_curriculum_context_and_bundle_mentor_rules
Args: ['self']

Function test_prepare_trims_large_runtime_context
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_nova_bridge.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.nova_bridge

Class EmbeddedNovaBridgeTests
- test_embedded_bridge_handles_token_flow_without_external_dependency(self)
- test_embedded_tool_sandbox_authorizes_requests(self)

Function test_embedded_bridge_handles_token_flow_without_external_dependency
Args: ['self']

Function test_embedded_tool_sandbox_authorizes_requests
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_nova_product_docs.py
Imports:
- __future__
- json
- tempfile
- unittest
- pathlib
- nova_school_server.nova_product_docs
- nova_school_server.reference_library

Class NovaProductDocsTests
- test_builder_generates_index_and_expands_permission_tokens(self)
- test_reference_library_marks_nova_school_as_official_local(self)

Function test_builder_generates_index_and_expands_permission_tokens
Args: ['self']

Function test_reference_library_marks_nova_school_as_official_local
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_permissions.py
Imports:
- __future__
- unittest
- nova_school_server.permissions

Class PermissionTests
- test_student_defaults_enable_ai_but_disable_web(self)
- test_teacher_defaults_do_not_gain_curriculum_update(self)
- test_user_override_wins_over_group_false(self)
- test_admin_role_keeps_core_permissions_even_if_user_override_disables_them(self)

Function test_student_defaults_enable_ai_but_disable_web
Args: ['self']

Function test_teacher_defaults_do_not_gain_curriculum_update
Args: ['self']

Function test_user_override_wins_over_group_false
Args: ['self']

Function test_admin_role_keeps_core_permissions_even_if_user_override_disables_them
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_pty_host.py
Imports:
- __future__
- importlib.util
- os
- shutil
- time
- unittest
- pathlib
- nova_school_server.pty_host

Class PtyHostTests
- test_pty_process_handles_prompt_input_and_resize(self)

Function test_pty_process_handles_prompt_input_and_resize
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_realtime.py
Imports:
- __future__
- importlib.util
- os
- random
- struct
- tempfile
- threading
- time
- unittest
- pathlib
- nova_school_server.code_runner
- nova_school_server.config
- nova_school_server.database
- nova_school_server.realtime
- nova_school_server.workspace

Class _FakeToolSandbox
- authorize(self)

Class _Session

Class _TeacherSession

Class _RecordingConnection
- __init__(self)
- send_json(self, payload)
- snapshot(self)

Class _FakeSocket
- __init__(self, chunks)
- settimeout(self, value)
- recv(self, size)
- sendall(self, data)
- shutdown(self, _how)
- close(self)

Class RealtimeTests
- test_websocket_accept_key_matches_reference(self)
- test_websocket_connection_is_long_lived_without_idle_timeout(self)
- test_websocket_timeout_is_reported_as_connection_close(self)
- test_websocket_rejects_unmasked_client_frames(self)
- test_websocket_rejects_oversized_frames_before_payload_read(self)
- test_websocket_rejects_reserved_bits(self)
- test_websocket_rejects_oversized_control_frame_payloads(self)
- test_websocket_invalid_utf8_is_reported_as_connection_error(self)
- test_websocket_parser_fuzz_harness_only_returns_text_or_connection_error(self)
- test_live_run_manager_streams_prompt_and_accepts_input(self)

Function _build_masked_frame
Args: []

Function _chunk_bytes
Args: ['data', 'seed']

Function _random_frame
Args: ['seed']

Function authorize
Args: ['self']

Function __init__
Args: ['self']

Function send_json
Args: ['self', 'payload']

Function snapshot
Args: ['self']

Function __init__
Args: ['self', 'chunks']

Function settimeout
Args: ['self', 'value']

Function recv
Args: ['self', 'size']

Function sendall
Args: ['self', 'data']

Function shutdown
Args: ['self', '_how']

Function close
Args: ['self']

Function test_websocket_accept_key_matches_reference
Args: ['self']

Function test_websocket_connection_is_long_lived_without_idle_timeout
Args: ['self']

Function test_websocket_timeout_is_reported_as_connection_close
Args: ['self']

Function test_websocket_rejects_unmasked_client_frames
Args: ['self']

Function test_websocket_rejects_oversized_frames_before_payload_read
Args: ['self']

Function test_websocket_rejects_reserved_bits
Args: ['self']

Function test_websocket_rejects_oversized_control_frame_payloads
Args: ['self']

Function test_websocket_invalid_utf8_is_reported_as_connection_error
Args: ['self']

Function test_websocket_parser_fuzz_harness_only_returns_text_or_connection_error
Args: ['self']

Function test_live_run_manager_streams_prompt_and_accepts_input
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_reference_import_cpp.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.reference_import_cpp

Class CppReferenceImportTests
- test_cpp_page_urls_are_normalized_to_local_html_paths(self)
- test_cpp_assets_are_classified_and_localized(self)
- test_mediawiki_edit_links_and_form_actions_are_ignored(self)
- test_html_rewriter_keeps_internal_links_local_and_disables_external_links(self)

Function test_cpp_page_urls_are_normalized_to_local_html_paths
Args: ['self']

Function test_cpp_assets_are_classified_and_localized
Args: ['self']

Function test_mediawiki_edit_links_and_form_actions_are_ignored
Args: ['self']

Function test_html_rewriter_keeps_internal_links_local_and_disables_external_links
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_reference_import_web.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.reference_import_web

Class ReferenceWebImportTests
- test_resolve_local_target_finds_html_and_assets(self)
- test_html_rewrite_localizes_absolute_pack_urls(self)
- test_landing_page_links_to_mirrored_sources(self)

Function test_resolve_local_target_finds_html_and_assets
Args: ['self']

Function test_html_rewrite_localizes_absolute_pack_urls
Args: ['self']

Function test_landing_page_links_to_mirrored_sources
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_reference_library.py
Imports:
- __future__
- tempfile
- time
- unittest
- pathlib
- nova_school_server.reference_library

Class ReferenceLibraryTests
- test_builtin_fallback_catalog_and_search_work(self)
- test_mirrored_pack_is_indexed_and_asset_path_is_resolved(self)
- test_plain_text_pack_directly_in_area_root_is_used(self)
- test_index_is_rebuilt_when_pack_changes(self)
- test_cpp_markdown_mirror_is_sanitized_for_rendering(self)

Function test_builtin_fallback_catalog_and_search_work
Args: ['self']

Function test_mirrored_pack_is_indexed_and_asset_path_is_resolved
Args: ['self']

Function test_plain_text_pack_directly_in_area_root_is_used
Args: ['self']

Function test_index_is_rebuilt_when_pack_changes
Args: ['self']

Function test_cpp_markdown_mirror_is_sanitized_for_rendering
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_release_notes.py
Imports:
- __future__
- subprocess
- tempfile
- unittest
- pathlib
- nova_school_server.release_notes

Class ReleaseNotesTests
- test_build_release_history_and_render_outputs(self)
- _git(repo)

Function test_build_release_history_and_render_outputs
Args: ['self']

Function _git
Args: ['repo']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_seed.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.auth
- nova_school_server.database
- nova_school_server.docs_catalog
- nova_school_server.embedded_nova
- nova_school_server.seed
- nova_school_server.workspace
- nova_school_server.config

Class SeedBootstrapTests
- setUp(self)
- tearDown(self)
- test_bootstrap_resets_demo_accounts_to_role_defaults_even_when_old_overrides_exist(self)

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_bootstrap_resets_demo_accounts_to_role_defaults_even_when_old_overrides_exist
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_server.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.server

Class _Repo
- __init__(self, settings)
- get_setting(self, key, default)

Class _App
- __init__(self, settings, port)

Class RequestHandlerTlsTests
- _handler(self, settings, headers)
- test_cookie_header_uses_secure_when_public_host_is_https(self)
- test_cookie_header_uses_secure_when_forwarded_proto_is_https(self)
- test_clear_cookie_header_uses_secure_when_forwarded_proto_is_https(self)
- test_certificate_verification_url_prefers_https_public_host(self)
- test_certificate_verification_url_uses_forwarded_https_for_bare_public_host(self)
- test_resolve_relative_file_rejects_traversal(self)
- test_default_litertlm_binary_path_accepts_linux_lit_binary(self)

Function __init__
Args: ['self', 'settings']

Function get_setting
Args: ['self', 'key', 'default']

Function __init__
Args: ['self', 'settings', 'port']

Function _handler
Args: ['self', 'settings', 'headers']

Function test_cookie_header_uses_secure_when_public_host_is_https
Args: ['self']

Function test_cookie_header_uses_secure_when_forwarded_proto_is_https
Args: ['self']

Function test_clear_cookie_header_uses_secure_when_forwarded_proto_is_https
Args: ['self']

Function test_certificate_verification_url_prefers_https_public_host
Args: ['self']

Function test_certificate_verification_url_uses_forwarded_https_for_bare_public_host
Args: ['self']

Function test_resolve_relative_file_rejects_traversal
Args: ['self']

Function test_default_litertlm_binary_path_accepts_linux_lit_binary
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_user_admin.py
Imports:
- __future__
- tempfile
- time
- unittest
- zipfile
- pathlib
- nova_school_server.config
- nova_school_server.database
- nova_school_server.user_admin
- nova_school_server.workspace

Class UserAdministrationTests
- setUp(self)
- tearDown(self)
- _create_personal_project(self)
- test_update_user_changes_status_role_and_logs_audit(self)
- test_permission_audit_payload_only_contains_changed_keys(self)
- test_cannot_deactivate_own_current_account(self)
- test_export_user_data_includes_projects_groups_and_ai_threads(self)
- test_hard_delete_user_removes_projects_files_and_histories(self)
- test_export_project_archive_contains_manifest_and_project_files(self)
- test_hard_delete_project_removes_workspace_and_project_chats(self)
- test_apply_retention_deletes_old_chat_and_audits(self)

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function _create_personal_project
Args: ['self']

Function test_update_user_changes_status_role_and_logs_audit
Args: ['self']

Function test_permission_audit_payload_only_contains_changed_keys
Args: ['self']

Function test_cannot_deactivate_own_current_account
Args: ['self']

Function test_export_user_data_includes_projects_groups_and_ai_threads
Args: ['self']

Function test_hard_delete_user_removes_projects_files_and_histories
Args: ['self']

Function test_export_project_archive_contains_manifest_and_project_files
Args: ['self']

Function test_hard_delete_project_removes_workspace_and_project_chats
Args: ['self']

Function test_apply_retention_deletes_old_chat_and_audits
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_virtual_lecturer.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.curriculum
- nova_school_server.database
- nova_school_server.virtual_lecturer

Class _Session
- __init__(self, username)

Class VirtualLecturerTests
- setUp(self)
- tearDown(self)
- test_start_creates_session_and_opening_message(self)
- test_prepare_includes_task_and_runtime_context(self)
- test_prepare_direct_feedback_accepts_valid_extended_python_intro_run(self)
- test_prepare_direct_feedback_accepts_web_intro_with_semantics_lists_and_extensions(self)
- test_student_cannot_start_explicitly_disabled_course(self)
- test_store_reply_persists_thread_entries(self)
- test_store_reply_strips_internal_answer_instructions(self)

Function __init__
Args: ['self', 'username']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_start_creates_session_and_opening_message
Args: ['self']

Function test_prepare_includes_task_and_runtime_context
Args: ['self']

Function test_prepare_direct_feedback_accepts_valid_extended_python_intro_run
Args: ['self']

Function test_prepare_direct_feedback_accepts_web_intro_with_semantics_lists_and_extensions
Args: ['self']

Function test_student_cannot_start_explicitly_disabled_course
Args: ['self']

Function test_store_reply_persists_thread_entries
Args: ['self']

Function test_store_reply_strips_internal_answer_instructions
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_wiki_manual.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- nova_school_server.wiki_manual

Class _Session
- __init__(self, role)
- is_teacher(self)

Class WikiManualTests
- test_service_seeds_manuals_when_scope_folders_are_missing(self)
- test_student_gets_student_manual_and_markdown_is_rendered(self)
- test_teacher_can_switch_to_teacher_scope(self)

Function __init__
Args: ['self', 'role']

Function is_teacher
Args: ['self']

Function test_service_seeds_manuals_when_scope_folders_are_missing
Args: ['self']

Function test_student_gets_student_manual_and_markdown_is_rendered
Args: ['self']

Function test_teacher_can_switch_to_teacher_scope
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_worker_agent.py
Imports:
- __future__
- hashlib
- tempfile
- unittest
- pathlib
- unittest.mock
- nova_school_server.worker_agent

Class WorkerAgentTests
- test_container_command_uses_materialized_workspace_without_copy_wrapper(self)
- test_container_command_preserves_image_path_and_converts_file_limit(self)
- test_verify_artifact_integrity_rejects_hash_mismatch(self)
- test_verify_artifact_integrity_accepts_matching_hash(self)

Function test_container_command_uses_materialized_workspace_without_copy_wrapper
Args: ['self']

Function test_container_command_preserves_image_path_and_converts_file_limit
Args: ['self']

Function test_verify_artifact_integrity_rejects_hash_mismatch
Args: ['self']

Function test_verify_artifact_integrity_accepts_matching_hash
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_worker_dispatch.py
Imports:
- __future__
- hashlib
- tempfile
- unittest
- pathlib
- nova_school_server.config
- nova_school_server.database
- nova_school_server.worker_dispatch
- nova_school_server.workspace

Class _FakeSecurityPlane
- __init__(self)
- store_secret(self, tenant_id, name, secret_value, metadata)
- resolve_secret(self, tenant_id, name)
- onboard_worker(self)
- list_worker_enrollments(self)

Class WorkerDispatchTests
- setUp(self)
- tearDown(self)
- test_claim_next_job_includes_signed_artifact_hash(self)

Function __init__
Args: ['self']

Function store_secret
Args: ['self', 'tenant_id', 'name', 'secret_value', 'metadata']

Function resolve_secret
Args: ['self', 'tenant_id', 'name']

Function onboard_worker
Args: ['self']

Function list_worker_enrollments
Args: ['self']

Function setUp
Args: ['self']

Function tearDown
Args: ['self']

Function test_claim_next_job_includes_signed_artifact_hash
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\test_workspace.py
Imports:
- __future__
- tempfile
- unittest
- pathlib
- json
- nova_school_server.config
- nova_school_server.workspace

Class WorkspaceTests
- test_materialize_project_and_block_path_escape(self)
- test_load_notebook_normalizes_legacy_starter_cells(self)
- test_delete_file_removes_secondary_file_and_blocks_main_file(self)
- test_directory_operations_support_create_delete_and_main_path_rename(self)

Function test_materialize_project_and_block_path_escape
Args: ['self']

Function test_load_notebook_normalizes_legacy_starter_cells
Args: ['self']

Function test_delete_file_removes_secondary_file_and_blocks_main_file
Args: ['self']

Function test_directory_operations_support_create_delete_and_main_path_rename
Args: ['self']

## C:\Users\ralfk\AppData\Local\Temp\tmpz8syt5ct\Nova-School-Server-v0.1.14-linux-project\tests\__init__.py
Imports:
- __future__

# 5. Main Request Flows

User → Server → Runner → Sandbox(Container)

1. User startet Aktion
2. Server verarbeitet Request
3. Runner/Scheduler übernimmt
4. Container führt Code isoliert aus


# 6. Architectural Deep Dives


## Deep Dive A: Sandbox Lifecycle

1. Request
2. Container Start
3. Code Execution
4. Output Capture
5. Container Destroy

→ Keine Persistenz


## Deep Dive B: AI Budgeting

Token-Schätzung:
1 Token ≈ 4 Zeichen

Strategie:
- Anfang behalten
- Ende behalten
- Mitte kürzen

→ stabil + deterministisch


## Deep Dive C: Security Hardening

Blockierte Syscalls:
- ptrace → Prozesskontrolle
- mount → Filesystem Zugriff
- clone → Namespace Escape

Prinzip:
Default Deny


## Deep Dive D: Zero Dependency Build

### Ziel
Keine externen Abhängigkeiten:
- keine pip installs
- keine system packages
- keine instabilen Drittanbieter-Libraries

### Build Pipeline

1. Source Code
2. statische Analyse
3. Packaging Script (distribution_builder.py)
4. Erstellung:
   - Linux Binary
   - Container Image

### PDF-Generierung

Zertifikate werden nicht über externe Libraries erzeugt.

Stattdessen:
- direkte Konstruktion von PDF 1.4 Byte-Streams
- manuelle Definition von:
  - Header
  - Objekten
  - Cross-Reference Table
  - Trailer

Warum?

- keine Abhängigkeit von PDF-Libraries
- keine Breaking Changes durch Updates
- vollständige Kontrolle über Output

### Vorteil

- reproduzierbare Builds
- vollständig offline-fähig
- immun gegen Supply-Chain-Probleme
- langfristige Stabilität über Jahre hinweg


## Deep Dive E: Curriculum System

course_id Struktur:

- metadata.json
- tasks/
- languages/

Ein Konzept → mehrere Sprachen
