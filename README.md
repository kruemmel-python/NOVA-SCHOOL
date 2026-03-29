# NOVA SCHOOL

Local school server for programming classes, isolated code execution, and teacher-facing lesson preparation with a primary local `LiteRT-LM` runtime.

## Overview

NOVA SCHOOL combines:

- browser-based project and notebook workspaces
- isolated execution for `Python`, `JavaScript`, `Node.js`, `C++`, `Java`, `Rust`, and `HTML`
- local AI support with `LiteRT-LM` as the primary provider
- `llama.cpp` as an alternative fallback provider
- Material Studio for teacher-facing lesson planning and worksheet generation
- Socratic mentoring, peer review, curriculum modules, and reference docs

The project is built for school networks, teacher notebooks, lab systems, and controlled low-cloud or offline environments.

## Repository Layout

| Path | Purpose |
|---|---|
| `server.py` | HTTP server, API routing, session handling |
| `code_runner.py` | isolated code execution, container hardening, scheduler |
| `ai_service.py` | local AI providers for LiteRT-LM and llama.cpp |
| `material_studio.py` | multi-step teaching-material generation |
| `LIT/` | primary local LiteRT runtime folder for `lit` and `.litertlm` models |
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
- embedded security/runtime components are included in the repository
- Docker or Podman for isolated runners
- `LiteRT-LM` runtime in `LIT/` as the preferred local AI stack

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Primary LiteRT Setup

The server now prefers a project-local `LIT/` folder before older external paths such as `D:\LIT`.

Recommended Windows layout:

```text
C:\nova_school_server\
  LIT\
    lit.windows_x86_64.exe
    gemma-3n-E4B-it-int4.litertlm
```

Official LiteRT-LM source:

- LiteRT-LM repository: `https://github.com/google-ai-edge/LiteRT-LM`
- the Windows `lit.windows_x86_64.exe` binary should come from the official LiteRT-LM project or its published prebuilt desktop artifacts

Recommended Linux layout:

```text
/srv/nova_school_server/
  LIT/
    lit
    gemma-3n-E4B-it-int4.litertlm
```

If no explicit server settings are provided, NOVA SCHOOL automatically looks for:

- `LIT/*.litertlm`
- `LIT/lit.windows_x86_64.exe`, `LIT/lit.exe`, or a native `lit` on `PATH`

External model download path:

- Hugging Face model tree: `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`
- preferred server model file: `gemma-3n-E4B-it-int4.litertlm`

Important:

- the Hugging Face repository is gated
- staff must log in and accept Google's Gemma usage license before downloading files

`llama.cpp` remains supported, but it is no longer the primary documented path.

## Demo Accounts

| User | Password | Role |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Teacher |
| `student` | `NovaSchool!student` | Demo student |

Change these passwords immediately in any non-demo environment.

## Release Assets

The GitHub releases are intended to contain:

- Windows server package ZIP
- Linux server package ZIP
- generic distribution ZIP
- checksums
- Windows `lit` binary as a separate asset when available

The ZIP packages intentionally do **not** embed:

- local databases
- cached workspaces
- machine-local runtime state
- large `.litertlm` or `.gguf` model blobs

This keeps the packages reproducible and avoids shipping multi-gigabyte local model files inside every server archive.

Embedded runtime:

- the repository includes its own local security and sandbox runtime components
- no external `Nova-shell` checkout is required for the default server path

## Documentation

- [Installation Guide](Docs/Installation.md)
- [Security Guide](Docs/Secure.md)
- [Extended Project Readme](Docs/Readme.md)

## Security Notes

- run behind a TLS-capable reverse proxy in institutional environments
- keep the container runner as the default execution backend
- provision the `LIT/` runtime before classes or assessments
- restrict public share/export features if policy requires it

Detailed controls and current limitations are documented in [Docs/Secure.md](Docs/Secure.md).
