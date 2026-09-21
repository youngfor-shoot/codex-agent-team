#!/usr/bin/env python3
"""Cross-platform synchronizer for the agent-team Skill runtime copy.

Mirrors scripts/sync-agent-team.ps1 so POSIX hosts can verify or install the
canonical Skill surface without PowerShell. Standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

__version__ = "0.5.6"
SAFE_BACKUP_NAME_RE = re.compile(r"^(?!\.{1,2}$)[A-Za-z0-9._-]{1,128}$")
MANAGED_DIRECTORIES = ("agents", "references", "scripts", "templates", "evals", "reports", "tests")


def normalized_hash(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def managed_relative_path(relative_path: str) -> bool:
    if any(part.startswith(".") for part in relative_path.split("/")):
        return False
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
    if root == "evals":
        return extension == ".json"
    if root == "reports":
        return extension == ".md"
    if root == "tests":
        return len(parts) >= 3 and parts[1] == "fixtures" and extension in {".json", ".md"}
    return False


def is_link_like(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(attributes & reparse_flag)


def assert_managed_surface_safe(root: Path) -> None:
    if not root.exists():
        return
    candidates = [root / "SKILL.md", *(root / name for name in MANAGED_DIRECTORIES)]
    for candidate in candidates:
        if not candidate.exists() and not candidate.is_symlink():
            continue
        if is_link_like(candidate):
            raise OSError(f"Managed path must not be a link or reparse point: {candidate}")
        if candidate.is_dir():
            for descendant in candidate.rglob("*"):
                relative_path = descendant.relative_to(root).as_posix()
                if any(part.startswith(".") for part in relative_path.split("/")):
                    continue
                if is_link_like(descendant):
                    raise OSError(
                        "Managed path must not be a link or reparse point: "
                        f"{descendant}"
                    )


def managed_files(root: Path) -> list[dict[str, str]]:
    if not root.is_dir():
        return []
    files = []
    for path in root.rglob("*"):
        relative_path = path.relative_to(root).as_posix()
        if not managed_relative_path(relative_path):
            continue
        if not path.is_file():
            continue
        files.append(
            {
                "relative_path": relative_path,
                "full_name": str(path),
                "hash": normalized_hash(path),
            }
        )
    return sorted(files, key=lambda item: item["relative_path"])


class Drift(TypedDict):
    missing: list[str]
    changed: list[str]
    stale: list[str]
    has_drift: bool


def compare_managed(
    source_files: list[dict[str, str]], destination_files: list[dict[str, str]]
) -> Drift:
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


def write_drift(drift: Drift) -> None:
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


def copy_managed_files(files: list[dict[str, str]], destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    for item in files:
        destination_file = destination_root / item["relative_path"]
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["full_name"], destination_file)


def prune_empty_ancestors(root: Path, removed_files: list[Path]) -> None:
    for removed_file in removed_files:
        try:
            removed_file.relative_to(root)
        except ValueError:
            continue
        directory = removed_file.parent
        while directory != root:
            if not directory.is_dir():
                break
            try:
                directory.rmdir()
            except OSError:
                break
            directory = directory.parent


def converge_managed_surface(
    source_files: list[dict[str, str]], destination_root: Path
) -> Drift:
    copy_managed_files(source_files, destination_root)
    current_files = managed_files(destination_root)
    drift = compare_managed(source_files, current_files)
    removed_files = []
    for relative_path in drift["stale"]:
        stale_path = destination_root / relative_path
        if stale_path.is_file():
            stale_path.unlink()
            removed_files.append(stale_path)
    prune_empty_ancestors(destination_root, removed_files)
    return compare_managed(source_files, managed_files(destination_root))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify, install, uninstall, or restore the agent-team Skill runtime copy."
    )
    parser.add_argument(
        "--mode",
        choices=("Verify", "Install", "Uninstall", "Restore"),
        default="Verify",
    )
    parser.add_argument(
        "--destination",
        default=str(Path.home() / ".codex" / "skills" / "agent-team"),
        help="Runtime destination (default: ~/.codex/skills/agent-team)",
    )
    parser.add_argument(
        "--backup-name",
        default="",
        help="Backup directory name to restore from (Restore mode)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Proceed without an interactive confirmation prompt",
    )
    parser.add_argument(
        "--keep-backups",
        type=int,
        default=5,
        help="Number of backup directories to retain (default: 5)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()

    repository_root = Path(__file__).resolve().parents[1]
    source_root = (repository_root / "skill" / "agent-team").resolve()
    destination_root = Path(args.destination).expanduser().resolve()

    if not source_root.is_dir():
        print(f"Canonical Skill source is missing: {source_root}", file=sys.stderr)
        return 1

    overlap = False
    try:
        source_root.relative_to(destination_root)
        overlap = True
    except ValueError:
        pass
    try:
        destination_root.relative_to(source_root)
        overlap = True
    except ValueError:
        pass
    if overlap:
        print("Source and destination must not overlap.", file=sys.stderr)
        return 1

    try:
        assert_managed_surface_safe(source_root)
        assert_managed_surface_safe(destination_root)
        source_files = managed_files(source_root)
        destination_files = managed_files(destination_root)
    except (OSError, UnicodeError) as exc:
        print(f"Cannot inspect managed Skill surface: {exc}", file=sys.stderr)
        return 1
    if not source_files:
        print("Canonical Skill source contains no managed files.", file=sys.stderr)
        return 1
    drift = compare_managed(source_files, destination_files)

    if args.mode == "Verify":
        if drift["has_drift"]:
            write_drift(drift)
            print(
                "agent-team runtime copy differs from canonical source.",
                file=sys.stderr,
            )
            return 2
        print(
            f"agent-team source and runtime copy match ({len(source_files)} managed files)."
        )
        return 0

    if args.mode == "Uninstall":
        if not destination_files:
            print("No managed agent-team files installed; nothing to uninstall.")
            return 0
        if not args.yes:
            answer = input(
                f"Remove {len(destination_files)} managed agent-team files from "
                f"{destination_root}? [y/N] "
            ).strip().lower()
            if answer not in {"y", "yes"}:
                print("Uninstall canceled.")
                return 2
        removed_files = []
        for item in destination_files:
            stale_path = destination_root / item["relative_path"]
            if stale_path.is_file():
                stale_path.unlink()
                removed_files.append(stale_path)
        remaining_files = managed_files(destination_root)
        if remaining_files:
            print("Uninstall did not remove every managed file.", file=sys.stderr)
            return 1
        prune_empty_ancestors(destination_root, removed_files)
        print(f"Uninstalled agent-team runtime copy ({len(destination_files)} managed files).")
        return 0

    if args.mode == "Restore":
        if not args.backup_name:
            print("Restore requires --backup-name.", file=sys.stderr)
            return 1
        if not SAFE_BACKUP_NAME_RE.fullmatch(args.backup_name):
            print("Restore backup name must be a single safe directory name.", file=sys.stderr)
            return 1
        backup_base = (destination_root.parent / ".agent-team-backups").resolve()
        backup_root = (backup_base / args.backup_name).resolve()
        try:
            backup_root.relative_to(backup_base)
        except ValueError:
            print("Restore backup path escapes the backup directory.", file=sys.stderr)
            return 1
        if not backup_root.is_dir():
            print(f"Backup does not exist: {backup_root}", file=sys.stderr)
            return 1
        try:
            assert_managed_surface_safe(backup_root)
            backup_files = managed_files(backup_root)
        except (OSError, UnicodeError) as exc:
            print(f"Cannot inspect backup surface: {exc}", file=sys.stderr)
            return 1
        if not backup_files:
            print(f"Backup contains no managed files: {backup_root}", file=sys.stderr)
            return 1
        if not args.yes:
            answer = input(
                f"Restore {len(backup_files)} managed agent-team files from "
                f"{backup_root}? [y/N] "
            ).strip().lower()
            if answer not in {"y", "yes"}:
                print("Restore canceled.")
                return 2
        destination_root.parent.mkdir(parents=True, exist_ok=True)
        current_files = managed_files(destination_root)
        transaction_root = Path(
            tempfile.mkdtemp(
                prefix=".agent-team-restore-", dir=destination_root.parent
            )
        )
        preserve_transaction = False
        try:
            staged_root = transaction_root / "staged"
            rollback_root = transaction_root / "rollback"
            try:
                copy_managed_files(backup_files, staged_root)
                staged_files = managed_files(staged_root)
                staged_drift = compare_managed(backup_files, staged_files)
                if staged_drift["has_drift"]:
                    raise OSError("staged backup verification failed")
                copy_managed_files(current_files, rollback_root)
                rollback_files = managed_files(rollback_root)
                rollback_drift = compare_managed(current_files, rollback_files)
                if rollback_drift["has_drift"]:
                    raise OSError("rollback snapshot verification failed")
            except (OSError, UnicodeError) as exc:
                print(f"agent-team restore preflight failed: {exc}", file=sys.stderr)
                return 1

            try:
                restored_drift = converge_managed_surface(
                    staged_files, destination_root
                )
                if restored_drift["has_drift"]:
                    raise OSError("restore did not converge to the backup")
            except (OSError, UnicodeError) as exc:
                try:
                    rollback_drift = converge_managed_surface(
                        rollback_files, destination_root
                    )
                except (OSError, UnicodeError) as rollback_exc:
                    preserve_transaction = True
                    print(
                        "agent-team restore failed and rollback could not complete: "
                        f"{exc}; rollback error: {rollback_exc}. "
                        f"Recovery files: {transaction_root}",
                        file=sys.stderr,
                    )
                    return 1
                if rollback_drift["has_drift"]:
                    preserve_transaction = True
                    write_drift(rollback_drift)
                    print(
                        "agent-team restore failed and rollback did not converge. "
                        f"Recovery files: {transaction_root}",
                        file=sys.stderr,
                    )
                    return 1
                print(
                    f"agent-team restore failed and was rolled back: {exc}",
                    file=sys.stderr,
                )
                return 1
        finally:
            if not preserve_transaction:
                shutil.rmtree(transaction_root, ignore_errors=True)
        print(
            f"Restored agent-team runtime copy from {args.backup_name} "
            f"({len(backup_files)} managed files)."
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
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
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

    removed_files = []
    for relative_path in drift["stale"]:
        stale_path = destination_root / relative_path
        if stale_path.is_file():
            stale_path.unlink()
            removed_files.append(stale_path)
    prune_empty_ancestors(destination_root, removed_files)

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

    backup_base = destination_root.parent / ".agent-team-backups"
    if backup_base.is_dir():
        backup_dirs = sorted(backup_base.iterdir(), key=lambda p: p.name, reverse=True)
        for stale_backup in backup_dirs[args.keep_backups :]:
            shutil.rmtree(stale_backup, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
