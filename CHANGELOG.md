# Changelog

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
