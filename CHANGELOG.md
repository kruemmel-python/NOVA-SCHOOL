# Changelog

## v0.1.10 - 2026-03-29

### Added

- structured admin JSON export for user master data, projects, chats, assistant and mentor histories, audits, and related school records
- admin-only hard-delete workflow for users including associated chat histories, selected school data records, and owned workspace paths under the configured Nova roots
- configurable chat and audit retention plus a manual admin retention run action in the UI
- explicit privacy notices for students in chat and local AI areas explaining teacher/admin visibility of stored communication

### Changed

- direct local AI helper conversations are now stored server-side so export, deletion, and retention cover the same KI support flows as the rest of the platform
- retention maintenance now runs automatically during server startup
- admin management screens now expose export, hard-delete, and retention actions directly in the browser

## v0.1.9 - 2026-03-29

### Changed

- Python runner tracebacks shown to students now strip internal wrapper frames from `.nova-build/python_entry.py` and `runpy`, leaving only the relevant student-code locations such as `main.py`
- LiteRT-LM direct-help prompts now enforce a stricter input budget so large code contexts no longer crash the local runtime on Windows laptops
- the Sokratischer Mentor now trims oversized code, run output, and conversation context before invoking LiteRT-LM, reducing XNNPACK reshape/runtime failures
- harmless TensorFlow Lite/XNNPACK info-only lines are no longer surfaced as user-facing local AI errors

### Added

- regression coverage for sanitized Python tracebacks in `tests/test_code_runner.py`
- regression coverage for LiteRT prompt-budget trimming in `tests/test_ai_service.py` and `tests/test_mentor.py`

## v0.1.8 - 2026-03-29

### Added

- admin-only signed curriculum bundle import, validation, activation, rollback, and bundle listing APIs
- curriculum-aware mentor context with active bundle mentor rules and course/module-aware guidance
- curriculum bundle integration for Material Studio presets, plus new regression coverage in `tests/test_curriculum.py`, `tests/test_material_studio.py`, `tests/test_mentor.py`, and `tests/test_seed.py`

### Changed

- teacher defaults are now explicitly defined for a usable school start profile instead of relying on implicit broad grants
- bootstrap seeding now normalizes the demo users and demo group on server start so broken legacy overrides do not leave the system without essential rights
- the admin UI now includes a curriculum bundle management flow for validate/import/activate/rollback operations

## v0.1.7 - 2026-03-29

### Changed

- the WebSocket parser now rejects reserved RSV bits, oversized control frames, and invalid UTF-8 text frames with explicit connection errors
- the HTML companion documents in `Docs/` were rewritten to match the current product, service, security, and hardware guidance instead of the stale v0.1.5 analysis text

### Added

- a deterministic fuzz/regression harness for `realtime.py` in `tests/test_realtime.py`

## v0.1.6 - 2026-03-29

### Added

- a new service technician guide in `Docs/Service.md` with minimum hardware profiles for `60-90` students
- a full Linux production runbook for Ubuntu, Docker, LiteRT-LM, TLS, and systemd-based autostart

### Changed

- repository documentation indexes now link the new service guide from the root README and docs guides

## v0.1.5 - 2026-03-29

### Changed

- worker ZIP artifacts are now extracted through a safe path validator that blocks traversal and symlink entries
- downloaded worker artifacts are now verified against a signed SHA-256 before extraction
- downloaded llama.cpp runtime archives now use the same safe ZIP extraction path
- realtime WebSocket handling now rejects oversized, unmasked, and fragmented client frames

### Added

- shared archive hardening helpers in `archive_utils.py`
- regression coverage for safe ZIP extraction, worker artifact integrity checks, and WebSocket frame limits

## v0.1.4 - 2026-03-29

### Changed

- the legacy browser on-device AI helper no longer references external JavaScript CDNs
- the server now emits `Secure` session cookies when HTTPS is detected via `server_public_host` or reverse-proxy headers
- repository-level reverse-proxy templates for Caddy and Nginx were added for TLS-first deployments

### Added

- reverse-proxy deployment templates under `deploy/reverse-proxy/`
- regression coverage for HTTPS-aware cookie handling and external verification URLs

## v0.1.3 - 2026-03-29

### Changed

- student run output no longer exposes operational container, hardening, network, or scheduler notes
- teacher and admin sessions continue to receive detailed runner diagnostics for project, bundle, and live runs

### Added

- regression coverage for note visibility in normal and live execution paths

## v0.1.2 - 2026-03-29

### Changed

- the embedded runtime is now the only supported default path for security and sandbox services
- all remaining `Nova-shell` legacy configuration fields and UI controls were removed
- installation and `LIT/` documentation now reference the official LiteRT-LM repository as the source of the `lit` binary

### Added

- embedded local implementations for the security plane and tool sandbox in `embedded_nova.py`
- regression coverage for the embedded bridge path

### Notes

- the server no longer reads or stores `nova_shell_path`
- LiteRT-LM remains the primary local AI stack, with the model still documented as an external download

## v0.1.1 - 2026-03-29

### Changed

- LiteRT-LM is now documented and configured as the primary local AI path
- automatic LiteRT discovery now prefers the project-local `LIT/` folder before legacy paths
- server settings placeholders and UI copy now point to `C:\nova_school_server\LIT`
- release packaging now scaffolds `LIT/` while excluding local model blobs from ZIP archives
- the server no longer depends on an external `Nova-shell` checkout for its default runtime path

### Added

- tracked `LIT/README.md` with the expected runtime layout
- root `server_config.json.example` for repository installs
- regression tests for project-local LiteRT discovery and release packaging of the `LIT/` scaffold

### Notes

- `llama.cpp` remains available as a fallback provider
- local `.litertlm` model files stay outside normal Git history and server ZIP packages

## v0.1.0 - 2026-03-29

### Added

- initial GitHub repository structure for NOVA SCHOOL
- cross-platform launchers and start scripts for Windows and Linux
- release packaging for generic, Windows, and Linux server bundles
- root-level README, pyproject metadata, requirements file, and repository hygiene files

### Changed

- distribution archives now exclude local model blobs and machine-local runtime data
- documentation links were normalized for GitHub-friendly relative paths

### Notes

- optional AI models are published as separate release assets instead of being committed into the repository
- container runtimes and Python remain external prerequisites
