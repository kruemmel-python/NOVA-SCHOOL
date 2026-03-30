from __future__ import annotations

import json
import stat
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PACKAGE_FLAVORS = {
    "distribution",
    "windows-server-package",
    "linux-server-package",
    "linux-project",
}

SKIP_NAMES = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    ".nova",
    "LIT",
    "node_modules",
    "dist",
    "build",
}
SKIP_FILE_SUFFIXES = {".pyc", ".pyo", ".pyd", ".db", ".shm", ".wal", ".zip", ".litertlm", ".gguf", ".task"}
SKIP_FILE_NAMES = {
    "analysis_dump.md",
    "Projektcode_analysis_dump.md",
    "info.png",
}


@dataclass(slots=True)
class DistributionBuildResult:
    version: str
    flavor: str
    archive_path: Path
    staging_root: Path


@dataclass(slots=True)
class DistributionMaterializeResult:
    version: str
    flavor: str
    target_root: Path


@dataclass(slots=True)
class LinuxProjectBuildResult:
    version: str
    archive_path: Path
    staging_root: Path


def detect_project_version(base_path: Path) -> str:
    pyproject = (base_path / "pyproject.toml").read_text(encoding="utf-8")
    for line in pyproject.splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            return stripped.split("=", 1)[1].strip().strip("\"'")
    return "0.1.0"


def build_distribution_archive(
    base_path: Path,
    output_dir: Path | None = None,
    version: str | None = None,
    flavor: str = "distribution",
) -> DistributionBuildResult:
    base_path = base_path.resolve(strict=False)
    version_text = version or detect_project_version(base_path)
    output_dir = (output_dir or base_path).resolve(strict=False)
    flavor_text = _normalize_flavor(flavor)
    package_name = f"Nova-School-Server-v{version_text}-{flavor_text}"
    archive_path = output_dir / f"{package_name}.zip"

    with tempfile.TemporaryDirectory(prefix="nova-school-distribution-") as tmp:
        staging_root = Path(tmp) / package_name
        staging_root.mkdir(parents=True, exist_ok=True)
        _copy_project_tree(base_path, staging_root)
        _create_distribution_scaffold(staging_root, version_text, flavor_text)
        _prune_for_flavor(staging_root, flavor_text)
        _copy_optional_linux_runtime_binaries(
            base_path,
            staging_root,
            flavor_text,
            include_for_linux_server_package=False,
        )
        if archive_path.exists():
            archive_path.unlink()
        _zip_tree(staging_root, archive_path)
    return DistributionBuildResult(version=version_text, flavor=flavor_text, archive_path=archive_path, staging_root=Path(package_name))


def build_linux_project_archive(
    base_path: Path,
    output_dir: Path | None = None,
    version: str | None = None,
) -> LinuxProjectBuildResult:
    result = build_distribution_archive(
        base_path,
        output_dir=output_dir,
        version=version,
        flavor="linux-project",
    )
    return LinuxProjectBuildResult(
        version=result.version,
        archive_path=result.archive_path,
        staging_root=result.staging_root,
    )


def materialize_distribution_directory(
    base_path: Path,
    target_root: Path,
    *,
    version: str | None = None,
    flavor: str = "distribution",
) -> DistributionMaterializeResult:
    base_path = base_path.resolve(strict=False)
    target_root = target_root.resolve(strict=False)
    version_text = version or detect_project_version(base_path)
    flavor_text = _normalize_flavor(flavor)

    with tempfile.TemporaryDirectory(prefix="nova-school-distribution-materialize-") as tmp:
        staging_root = Path(tmp) / "materialized"
        staging_root.mkdir(parents=True, exist_ok=True)
        excluded_relative = []
        try:
            relative_target = target_root.relative_to(base_path)
            excluded_relative.append(relative_target)
        except ValueError:
            pass
        _copy_project_tree(base_path, staging_root, excluded_relative_paths=excluded_relative)
        _create_distribution_scaffold(staging_root, version_text, flavor_text)
        _prune_for_flavor(staging_root, flavor_text)
        _copy_optional_linux_runtime_binaries(
            base_path,
            staging_root,
            flavor_text,
            include_for_linux_server_package=True,
        )
        if target_root.exists():
            shutil.rmtree(target_root, ignore_errors=True)
        target_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staging_root, target_root, dirs_exist_ok=True)
    return DistributionMaterializeResult(version=version_text, flavor=flavor_text, target_root=target_root)


def _normalize_flavor(flavor: str) -> str:
    text = str(flavor or "distribution").strip().lower()
    aliases = {
        "distribution": "distribution",
        "windows": "windows-server-package",
        "windows-server": "windows-server-package",
        "windows-server-package": "windows-server-package",
        "linux": "linux-server-package",
        "linux-server": "linux-server-package",
        "linux-server-package": "linux-server-package",
        "linux-project": "linux-project",
        "pure-linux": "linux-project",
        "linux-standalone": "linux-project",
    }
    normalized = aliases.get(text)
    if normalized not in PACKAGE_FLAVORS:
        raise ValueError(f"unsupported distribution flavor: {flavor}")
    return normalized


def _copy_project_tree(source_root: Path, target_root: Path, *, excluded_relative_paths: Iterable[Path] | None = None) -> None:
    excluded = [_normalize_relative_path(path) for path in (excluded_relative_paths or []) if str(path)]
    for item in source_root.iterdir():
        relative_path = _normalize_relative_path(item.relative_to(source_root))
        if _is_excluded_relative_path(relative_path, excluded):
            continue
        if _should_skip_root_entry(item, relative_path):
            continue
        destination = target_root / item.name
        if item.is_dir():
            _copy_directory(item, destination, source_root=source_root, excluded_relative_paths=excluded)
        elif item.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def _copy_directory(source_dir: Path, target_dir: Path, *, source_root: Path, excluded_relative_paths: list[Path]) -> None:
    for item in source_dir.iterdir():
        relative_path = _normalize_relative_path(item.relative_to(source_root))
        if _is_excluded_relative_path(relative_path, excluded_relative_paths):
            continue
        if _should_skip_entry(item, relative_path):
            continue
        destination = target_dir / item.name
        if item.is_dir():
            _copy_directory(item, destination, source_root=source_root, excluded_relative_paths=excluded_relative_paths)
        elif item.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def _should_skip_root_entry(path: Path, relative_path: Path) -> bool:
    if path.name == "data":
        return True
    if path.name == "Model":
        return True
    return _should_skip_entry(path, relative_path)


def _should_skip_entry(path: Path, relative_path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return True
    if relative_path.parts[:2] == ("Linux", "project"):
        return True
    if path.is_file():
        if path.name in SKIP_FILE_NAMES:
            return True
        if path.name.startswith("_tmp_") or path.name.startswith("tmp_"):
            return True
        if any(path.name.endswith(marker) for marker in ("_analysis_dump.md", ".codedump.md")):
            return True
        if path.suffix.lower() in SKIP_FILE_SUFFIXES:
            return True
    return False


def _normalize_relative_path(path: Path) -> Path:
    return Path(*[part for part in path.parts if part not in {"", "."}])


def _is_excluded_relative_path(relative_path: Path, excluded_relative_paths: list[Path]) -> bool:
    for excluded in excluded_relative_paths:
        if not excluded.parts:
            continue
        if relative_path == excluded or relative_path.parts[: len(excluded.parts)] == excluded.parts:
            return True
    return False


def _create_distribution_scaffold(staging_root: Path, version: str, flavor: str) -> None:
    _ensure_placeholder(staging_root / "LIT" / ".gitkeep")
    _ensure_placeholder(staging_root / "Model" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "workspaces" / "users" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "workspaces" / "groups" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "reference_library" / "packs" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "reference_library" / "index" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "public_shares" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "exports" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "review_submissions" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "worker_dispatch" / "artifacts" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "container_build" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "python_package_cache" / ".gitkeep")
    _ensure_placeholder(staging_root / "data" / "docs" / ".gitkeep")

    server_config_example = {
        "host": "0.0.0.0",
        "port": 8877,
        "session_ttl_seconds": 43200,
        "run_timeout_seconds": 20,
        "live_run_timeout_seconds": 300,
        "tenant_id": "nova-school",
        "school_name": "Nova School Server",
    }
    (staging_root / "server_config.json.example").write_text(
        json.dumps(server_config_example, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest = {
        "package_type": flavor,
        "version": version,
        "includes_runtime_data": False,
        "includes_reference_mirrors": False,
        "includes_workspaces": False,
    }
    (staging_root / "release_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    notes = """# Nova School Server Distribution

Dieses Paket ist fuer Schulen als sauberes Distributionspaket gedacht.

Enthaelt:
- vollstaendigen Quellcode
- Startskripte fuer Windows und Linux
- Wiki- und Produktdokumentation
- leere Datenordner fuer den Erststart
- leerer `LIT`-Ordner fuer den primären LiteRT-LM-Betrieb
- Beispielkonfiguration `server_config.json.example`

Nicht enthalten:
- lokale Datenbanken
- bestehende Benutzer- oder Projektdaten
- Laufzeit-Workspaces
- PKI-/Secret-Artefakte
- lokale Referenz-Mirror-Caches
- lokale KI-Modelle und grosse Runtime-Binaries

Start:
- Windows: `start_server.ps1`
- Linux: `start_server.sh`

Vor dem ersten produktiven Einsatz:
1. `requirements.txt` installieren
2. `server_config.json.example` nach `server_config.json` kopieren und anpassen
3. optionale Offline-Referenzbibliotheken importieren
4. `LIT/` mit `lit`-Binary und `.litertlm`-Modell befuellen oder alternative lokale KI konfigurieren
"""
    (staging_root / "DISTRIBUTION_README.md").write_text(notes, encoding="utf-8")
    _write_lit_scaffold(staging_root)
    _write_platform_installation_guide(staging_root, flavor, version)


def _prune_for_flavor(staging_root: Path, flavor: str) -> None:
    if flavor == "windows-server-package":
        for relative in ("start_server.sh", "start_worker.sh", "run_tests.sh"):
            _remove_if_exists(staging_root / relative)
    elif flavor in {"linux-server-package", "linux-project"}:
        for relative in ("start_server.ps1", "start_worker.ps1", "run_tests.ps1"):
            _remove_if_exists(staging_root / relative)


def _write_platform_installation_guide(staging_root: Path, flavor: str, version: str) -> None:
    if flavor == "windows-server-package":
        guide_name = "WINDOWS_SERVER_PACKAGE.md"
        title = f"# Nova School Server Windows Server Package v{version}"
        body = """

Dieses Paket ist fuer einen Windows-Hauptserver gedacht.

Empfohlene Voraussetzungen:
- Windows 11 oder Windows Server
- Python 3.12
- Docker Desktop fuer den Containerbetrieb
- LiteRT-LM als primäre lokale KI in `LIT\\`

Installation:
1. Paket entpacken
2. PowerShell als Benutzer mit Schreibrechten im Zielordner oeffnen
3. `py -3 -m pip install -r requirements.txt`
4. `server_config.json.example` nach `server_config.json` kopieren und anpassen
5. `LIT\\lit.windows_x86_64.exe` und eine `.litertlm`-Datei in `LIT\\` ablegen
6. optional Docker Desktop fuer isolierte Runner starten
7. `./start_server.ps1`

Wichtige Betriebsaspekte:
- Windows-Firewall fuer Port 8877 freigeben
- fuer produktive Container-Ausfuehrung Docker Desktop mit Linux-Containern nutzen
- fuer robuste Schuelerlaeufe langfristig Linux-Worker oder einen Linux-Hauptserver bevorzugen
"""
    elif flavor == "linux-server-package":
        guide_name = "LINUX_SERVER_PACKAGE.md"
        title = f"# Nova School Server Linux Server Package v{version}"
        body = """

Dieses Paket ist fuer einen Ubuntu- oder Linux-Hauptserver gedacht.

Empfohlene Voraussetzungen:
- Ubuntu 24.04 LTS oder vergleichbare Distribution
- Python 3.12
- Docker oder Podman
- LiteRT-LM als primäre lokale KI in `LIT/`

Installation:
1. Paket entpacken
2. im Projektordner ein virtuelles Environment anlegen
3. `python3 -m venv .venv`
4. `. .venv/bin/activate`
5. `python3 -m pip install -r requirements.txt`
6. `cp server_config.json.example server_config.json`
7. native `lit`-Binary und eine `.litertlm`-Datei in `LIT/` ablegen
8. `./start_server.sh`

Empfehlungen fuer den produktiven Betrieb:
- Reverse Proxy oder internes Schulnetz fuer den Zugriff verwenden
- Port 8877 per Firewall nur im benoetigten Netz freigeben
- Docker/Podman fuer Schuelerlaeufe aktivieren
- optional systemd-Service fuer automatischen Start anlegen
"""
    elif flavor == "linux-project":
        guide_name = "PURE_LINUX_RELEASE.md"
        title = f"# Nova School Server Pure Linux Release v{version}"
        body = """

Dieses Archiv enthaelt den Linux-bereinigten, direkt startbaren Stand fuer Ubuntu und vergleichbare Distributionen.

Enthaelt zusaetzlich:
- Linux-Startskripte als primären Startpfad
- Linux-taugliche Pfadauflösung fuer Daten, `static/`, `Docs/` und `LIT/`
- falls im Quellprojekt vorhanden: `LIT/lit.linux_x86_64`

Empfohlene Inbetriebnahme:
1. Archiv entpacken
2. `python3 -m venv .venv`
3. `. .venv/bin/activate`
4. `python3 -m pip install -r requirements.txt`
5. `cp server_config.json.example server_config.json`
6. optional eine `.litertlm`-Modelldatei nach `LIT/` kopieren
7. `./start_server.sh`

Hinweise:
- dieses Release ist fuer Linux-Systeme gedacht und ersetzt keine Windows-Installation
- grosse Modell-Dateien bleiben weiterhin absichtlich ausserhalb des Repositories und der Standardpakete
"""
    else:
        return
    (staging_root / guide_name).write_text(f"{title}\n{body.lstrip()}", encoding="utf-8")


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def _ensure_placeholder(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def _write_lit_scaffold(staging_root: Path) -> None:
    notes = """# LIT Runtime

Der Nova School Server nutzt standardmaessig LiteRT-LM aus diesem Ordner.

Offizielle Herkunft der `lit`-Binary:
- `https://github.com/google-ai-edge/LiteRT-LM`

Erwartete Inhalte:
- Windows: `lit.windows_x86_64.exe`
- Linux/macOS: eine passende native `lit`-Binary
- ein lokales `.litertlm`-Modell, z. B. `gemma-3n-E4B-it-int4.litertlm`

Externer Downloadpfad fuer das empfohlene Modell:
- `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`

Hinweis:
- das Hugging-Face-Repository ist gated
- vor dem Download muessen Anmeldung und Gemma-Lizenzfreigabe erfolgt sein

Die Release-Pakete enthalten diesen Ordner absichtlich leer, damit keine mehrgigabytegrossen Modelle oder maschinenspezifischen Binaries in jedem ZIP mitgeliefert werden.
"""
    (staging_root / "LIT" / "README.md").write_text(notes, encoding="utf-8")


def _copy_optional_linux_runtime_binaries(
    source_root: Path,
    target_root: Path,
    flavor: str,
    *,
    include_for_linux_server_package: bool,
) -> None:
    if flavor == "linux-project":
        pass
    elif flavor == "linux-server-package" and include_for_linux_server_package:
        pass
    else:
        return
    binary_source = source_root / "LIT" / "lit.linux_x86_64"
    if not binary_source.exists() or not binary_source.is_file():
        return
    binary_target = target_root / "LIT" / "lit.linux_x86_64"
    binary_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary_source, binary_target)
    if hasattr(stat, "S_IXUSR"):
        try:
            mode = binary_target.stat().st_mode
            binary_target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass


def _zip_tree(root: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file_path in sorted(_iter_files(root)):
            archive.write(file_path, file_path.relative_to(root.parent))


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build a clean Nova School Server distribution archive.")
    parser.add_argument("base_path", nargs="?", default=".", help="Projektwurzel")
    parser.add_argument("--output-dir", default=".", help="Zielordner fuer das Archiv")
    parser.add_argument("--version", default="", help="Optionale Versionsnummer")
    parser.add_argument(
        "--flavor",
        default="distribution",
        choices=sorted(PACKAGE_FLAVORS),
        help="Pakettyp: distribution, windows-server-package, linux-server-package oder linux-project",
    )
    args = parser.parse_args()

    result = build_distribution_archive(
        Path(args.base_path),
        output_dir=Path(args.output_dir),
        version=args.version or None,
        flavor=args.flavor,
    )
    print(result.archive_path)


if __name__ == "__main__":
    main()
