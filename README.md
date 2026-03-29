# NOVA SCHOOL

Local school server for programming classes, project work, isolated code execution, and local AI-assisted teaching workflows.

## Overview

NOVA SCHOOL combines:

- browser-based project and notebook workspaces
- isolated execution for `Python`, `JavaScript`, `Node.js`, `C++`, `Java`, `Rust`, and `HTML`
- local AI support via `LiteRT-LM` or `llama.cpp`
- Material Studio for teacher-facing lesson preparation
- Socratic mentoring, peer review, curriculum modules, and reference docs

The codebase is designed for school networks, teacher notebooks, and controlled offline or low-cloud environments.

## Repository Layout

| Path | Purpose |
|---|---|
| `server.py` | HTTP server, API routing, session handling |
| `code_runner.py` | isolated code execution, container hardening, scheduler |
| `ai_service.py` | local AI providers for LiteRT-LM and llama.cpp |
| `material_studio.py` | multi-step teaching-material generation |
| `static/` | browser frontend |
| `tests/` | regression and unit tests |
| `Docs/` | installation, security, and project documentation |

## Quick Start

Preferred cross-platform start path:

- Windows: `./start_server.ps1`
- Linux: `./start_server.sh`

The start scripts bootstrap the package correctly even if the cloned folder is not named `nova_school_server`.

Manual start is still possible when the package folder is named `nova_school_server` and started from its parent directory:

```powershell
python -m nova_school_server
```

Default local URL:

```text
http://127.0.0.1:8877
```

## Requirements

- Python `3.12`
- Nova-shell runtime or `NOVA_SHELL_PATH`
- optional Docker or Podman for isolated runners
- optional local AI model for LiteRT-LM or llama.cpp

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Demo Accounts

| User | Password | Role |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Teacher |
| `student` | `NovaSchool!student` | Demo student |

Change these passwords immediately in any non-demo environment.

## Release Assets

The GitHub release is intended to contain:

- Windows server package ZIP
- Linux server package ZIP
- one or more optional local model assets

The core server packages do not embed local databases, cached workspaces, or machine-specific runtime state.

## Documentation

- [Installation Guide](Docs/Installation.md)
- [Security Guide](Docs/Secure.md)
- [Project Readme (extended)](Docs/Readme.md)

## Security Notes

- run behind a TLS-capable reverse proxy in institutional environments
- keep the container runner as the default execution backend
- restrict public share/export features if policy requires it
- prewarm models and container images before class

Detailed controls and current limitations are documented in [Docs/Secure.md](Docs/Secure.md).
