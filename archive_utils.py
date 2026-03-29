from __future__ import annotations

import os
import stat
import zipfile
from pathlib import Path


def extract_zip_safely(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve(strict=False)
    for member in archive.infolist():
        relative = _validated_zip_member_path(member)
        target = (root / relative).resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise PermissionError(f"ZIP-Eintrag verlaesst das Zielverzeichnis: {member.filename}") from exc
        if member.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member, "r") as source, target.open("wb") as handle:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)


def _validated_zip_member_path(member: zipfile.ZipInfo) -> Path:
    raw_name = str(member.filename or "").replace("\\", "/").strip()
    if not raw_name:
        raise PermissionError("Leerer ZIP-Eintrag ist nicht erlaubt.")
    if raw_name.startswith("/") or raw_name.startswith("../") or "/../" in raw_name or raw_name.endswith("/.."):
        raise PermissionError(f"Ungueltiger ZIP-Pfad: {member.filename}")
    parts = [part for part in raw_name.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts) or any(":" in part for part in parts):
        raise PermissionError(f"Ungueltiger ZIP-Pfad: {member.filename}")
    if _zip_entry_is_symlink(member):
        raise PermissionError(f"ZIP-Symlink ist nicht erlaubt: {member.filename}")
    return Path(*parts)


def _zip_entry_is_symlink(member: zipfile.ZipInfo) -> bool:
    mode = (member.external_attr >> 16) & 0xFFFF
    if not mode:
        return False
    return stat.S_ISLNK(mode)
