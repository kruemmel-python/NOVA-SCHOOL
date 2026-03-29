# Changelog

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
