from __future__ import annotations

import argparse
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path


SKIP_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".nova",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "data",
    "Model",
}

SKIP_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".shm",
    ".wal",
    ".zip",
    ".litertlm",
    ".gguf",
    ".task",
    ".xnnpack_cache",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".class",
    ".jar",
}

ALLOWED_SUFFIXES = {
    ".py",
    ".js",
    ".cjs",
    ".mjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".ps1",
    ".sh",
    ".bat",
    ".cmd",
    ".ini",
    ".cfg",
    ".conf",
    ".sql",
    ".java",
    ".rs",
    ".cpp",
    ".cc",
    ".cxx",
    ".c",
    ".h",
    ".hpp",
    ".hh",
    ".xml",
    ".svg",
}

ALLOWED_FILE_NAMES = {
    ".gitignore",
    ".gitattributes",
    "Dockerfile",
    "Caddyfile",
    "LICENSE",
    "Cargo.lock",
    "requirements.txt",
}


@dataclass(slots=True)
class SourceAnalysisArchiveBuildResult:
    version: str
    archive_path: Path
    file_count: int


def detect_project_version(base_path: Path) -> str:
    pyproject_path = base_path / "pyproject.toml"
    if not pyproject_path.exists():
        return "0.1.0"
    pyproject = pyproject_path.read_text(encoding="utf-8")
    for line in pyproject.splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            return stripped.split("=", 1)[1].strip().strip("\"'")
    return "0.1.0"


def build_source_analysis_archive(
    base_path: Path,
    *,
    output_dir: Path | None = None,
    version: str | None = None,
) -> SourceAnalysisArchiveBuildResult:
    base_path = base_path.resolve(strict=False)
    output_dir = (output_dir or (base_path / "dist")).resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    version_text = version or detect_project_version(base_path)
    archive_path = output_dir / f"NovaSchoolAnalyzer-v{version_text}.zip"
    root_prefix = Path(f"NovaSchoolAnalyzer-v{version_text}")
    included_files = 0

    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative_path in _iter_source_analysis_files(base_path):
            archive.write(base_path / relative_path, root_prefix / relative_path)
            included_files += 1
    return SourceAnalysisArchiveBuildResult(version=version_text, archive_path=archive_path, file_count=included_files)


def _iter_source_analysis_files(base_path: Path) -> list[Path]:
    files = []
    for relative_path in _git_tracked_files(base_path):
        candidate = base_path / relative_path
        if not candidate.is_file():
            continue
        if _should_skip_source_analysis_file(relative_path):
            continue
        if not _is_allowed_source_file(relative_path):
            continue
        if not _is_probably_text_file(candidate):
            continue
        files.append(relative_path)
    return sorted(files)


def _git_tracked_files(base_path: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=base_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git ls-files failed"
        raise RuntimeError(message)
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def _should_skip_source_analysis_file(relative_path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in relative_path.parts[:-1]):
        return True
    if relative_path.parts[:2] == ("Linux", "project"):
        return True
    name = relative_path.name
    suffix = relative_path.suffix.lower()
    if name.startswith("_tmp_") or name.startswith("tmp_"):
        return True
    if any(name.endswith(marker) for marker in ("_analysis_dump.md", ".codedump.md")):
        return True
    if suffix in SKIP_FILE_SUFFIXES:
        return True
    if relative_path.parts and relative_path.parts[0] == "Docs" and suffix == ".html":
        return True
    return False


def _is_allowed_source_file(relative_path: Path) -> bool:
    if relative_path.name in ALLOWED_FILE_NAMES:
        return True
    if relative_path.suffix.lower() in ALLOWED_SUFFIXES:
        return True
    return False


def _is_probably_text_file(path: Path) -> bool:
    sample = path.read_bytes()[:8192]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        try:
            sample.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-only ZIP archive for AI analysis.")
    parser.add_argument("base_path", nargs="?", default=".", help="Projektwurzel")
    parser.add_argument("--output-dir", default="dist", help="Ausgabeordner fuer das ZIP-Archiv")
    parser.add_argument("--version", default="", help="Optionale Versionsueberschreibung")
    args = parser.parse_args()

    base_path = Path(args.base_path).resolve(strict=False)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = base_path / output_dir
    result = build_source_analysis_archive(base_path, output_dir=output_dir, version=args.version or None)
    print(result.archive_path)


if __name__ == "__main__":
    main()
