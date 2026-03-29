# Changelog

## v0.1.1 - 2026-03-29

### Changed

- LiteRT-LM is now documented and configured as the primary local AI path
- automatic LiteRT discovery now prefers the project-local `LIT/` folder before legacy paths
- server settings placeholders and UI copy now point to `C:\nova_school_server\LIT`
- release packaging now scaffolds `LIT/` while excluding local model blobs from ZIP archives

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
- container runtimes, Python, and Nova-shell remain external prerequisites
