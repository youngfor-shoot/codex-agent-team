#!/usr/bin/env python3
"""Cross-platform synchronizer for the agent-team Skill runtime copy.

Mirrors scripts/sync-agent-team.ps1 so POSIX hosts can verify or install the
canonical Skill surface without PowerShell. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


def normalized_hash(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def managed_relative_path(relative_path: str) -> bool:
    if relative_path == "SKILL.md":
        return True
    parts = relative_path.split("/")
    if len(parts) < 2:
        return False
    extension = Path(relative_path).suffix.lower()
    root = parts[0].lower()
    if root == "agents":
        return extension in {".yaml", ".yml"}
    if root in {"references", "templates"}:
        return extension == ".md"
    if root == "scripts":
        return extension == ".py"
    return False


def managed_files(root: Path) -> list[dict]:
    if not root.is_dir():
        return []
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root).as_posix()
        if managed_relative_path(relative_path):
            files.append(
                {
                    "relative_path": relative_path,
                    "full_name": str(path),
                    "hash": normalized_hash(path),
                }
            )
    return sorted(files, key=lambda item: item["relative_path"])


def compare_managed(source_files: list[dict], destination_files: list[dict]) -> dict:
    source_by_path = {item["relative_path"]: item for item in source_files}
    destination_by_path = {item["relative_path"]: item for item in destination_files}
    missing = sorted(set(source_by_path) - set(destination_by_path))
    changed = sorted(
        path
        for path in source_by_path
        if path in destination_by_path
        and source_by_path[path]["hash"] != destination_by_path[path]["hash"]
    )
    stale = sorted(set(destination_by_path) - set(source_by_path))
    return {
        "missing": missing,
        "changed": changed,
        "stale": stale,
        "has_drift": bool(missing or changed or stale),
    }


def write_drift(drift: dict) -> None:
    groups = (
        ("Missing from runtime", drift["missing"]),
        ("Changed in runtime", drift["changed"]),
        ("Stale in runtime", drift["stale"]),
    )
    for label, paths in groups:
        if not paths:
            continue
        print(f"{label}:")
        for path in paths:
            print(f"  - {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify or install the agent-team Skill runtime copy."
    )
    parser.add_argument(
        "--mode", choices=("Verify", "Install"), default="Verify"
    )
    parser.add_argument(
        "--destination",
        default=str(Path.home() / ".codex" / "skills" / "agent-team"),
        help="Runtime destination (default: ~/.codex/skills/agent-team)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Proceed without an interactive confirmation prompt",
    )
    args = parser.parse_args()

    repository_root = Path(__file__).resolve().parents[1]
    source_root = (repository_root / "skill" / "agent-team").resolve()
    destination_root = Path(args.destination).expanduser().resolve()

    if not source_root.is_dir():
        print(f"Canonical Skill source is missing: {source_root}", file=sys.stderr)
        return 1

    try:
        source_root.relative_to(destination_root)
        overlap = True
    except ValueError:
        overlap = False
    try:
        destination_root.relative_to(source_root)
        overlap = True
    except ValueError:
        overlap = False
    if overlap:
        print("Source and destination must not overlap.", file=sys.stderr)
        return 1

    source_files = managed_files(source_root)
    if not source_files:
        print("Canonical Skill source contains no managed files.", file=sys.stderr)
        return 1
    destination_files = managed_files(destination_root)
    drift = compare_managed(source_files, destination_files)

    if args.mode == "Verify":
        if drift["has_drift"]:
            write_drift(drift)
            print(
                "agent-team runtime copy differs from canonical source.",
                file=sys.stderr,
            )
            return 1
        print(
            f"agent-team source and runtime copy match ({len(source_files)} managed files)."
        )
        return 0

    if not drift["has_drift"]:
        print(
            f"agent-team runtime copy is already current ({len(source_files)} managed files)."
        )
        return 0

    write_drift(drift)
    if not args.yes:
        answer = input(
            f"Back up and synchronize {len(source_files)} managed agent-team files to "
            f"{destination_root}? [y/N] "
        ).strip().lower()
        if answer not in {"y", "yes"}:
            print("Install canceled.")
            return 2

    backup_path: Path | None = None
    if destination_files:
        backup_base = destination_root.parent / ".agent-team-backups"
        backup_name = (
            __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
            + "-"
            + os.urandom(4).hex()
        )
        backup_path = backup_base / backup_name
        for item in destination_files:
            backup_file = backup_path / item["relative_path"]
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item["full_name"], backup_file)

    destination_root.mkdir(parents=True, exist_ok=True)
    for item in source_files:
        destination_file = destination_root / item["relative_path"]
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["full_name"], destination_file)

    for relative_path in drift["stale"]:
        stale_path = destination_root / relative_path
        if stale_path.is_file():
            stale_path.unlink()

    post_files = managed_files(destination_root)
    post_drift = compare_managed(source_files, post_files)
    if post_drift["has_drift"]:
        write_drift(post_drift)
        print(
            "agent-team installation did not converge to canonical source.",
            file=sys.stderr,
        )
        return 1

    print(f"Installed agent-team runtime copy ({len(source_files)} managed files).")
    if backup_path is not None:
        print(f"Backup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
