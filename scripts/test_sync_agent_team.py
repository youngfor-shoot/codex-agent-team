from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SYNC = REPOSITORY_ROOT / "scripts" / "sync-agent-team.py"
POWERSHELL_SYNC = REPOSITORY_ROOT / "scripts" / "sync-agent-team.ps1"


def load_python_sync():
    spec = importlib.util.spec_from_file_location("sync_agent_team", PYTHON_SYNC)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonSyncTests(unittest.TestCase):
    def test_rejects_repository_destination_overlap(self) -> None:
        sync = load_python_sync()
        argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Verify",
                "--destination",
                str(REPOSITORY_ROOT),
        ]
        with mock.patch.object(sys, "argv", argv):
            result = sync.main()

        self.assertEqual(result, 1)

    def test_restore_removes_managed_files_absent_from_backup(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            backup = root / ".agent-team-backups" / "old"
            (destination / "templates").mkdir(parents=True)
            backup.mkdir(parents=True)
            (destination / "SKILL.md").write_text("current\n", encoding="utf-8")
            stale_file = destination / "templates" / "new.md"
            stale_file.write_text("new\n", encoding="utf-8")
            ignored_file = destination / "notes.txt"
            ignored_file.write_text("keep\n", encoding="utf-8")
            (backup / "SKILL.md").write_text("old\n", encoding="utf-8")

            argv = [
                    str(PYTHON_SYNC),
                    "--mode",
                    "Restore",
                    "--destination",
                    str(destination),
                    "--backup-name",
                    "old",
                    "--yes",
            ]
            with mock.patch.object(sys, "argv", argv):
                result = sync.main()

            self.assertEqual(result, 0)
            self.assertEqual(
                (destination / "SKILL.md").read_text(encoding="utf-8"), "old\n"
            )
            self.assertFalse(stale_file.exists())
            self.assertEqual(ignored_file.read_text(encoding="utf-8"), "keep\n")

    def test_install_verify_uninstall_lifecycle_preserves_unknown_files(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "agent-team"
            destination.mkdir()
            unknown_file = destination / "notes.txt"
            unknown_file.write_text("keep\n", encoding="utf-8")

            install_argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Install",
                "--destination",
                str(destination),
                "--yes",
            ]
            with mock.patch.object(sys, "argv", install_argv):
                self.assertEqual(sync.main(), 0)

            verify_argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Verify",
                "--destination",
                str(destination),
            ]
            with mock.patch.object(sys, "argv", verify_argv):
                self.assertEqual(sync.main(), 0)

            with mock.patch.object(sys, "argv", install_argv):
                self.assertEqual(sync.main(), 0)

            uninstall_argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Uninstall",
                "--destination",
                str(destination),
                "--yes",
            ]
            with mock.patch.object(sys, "argv", uninstall_argv):
                self.assertEqual(sync.main(), 0)

            self.assertEqual(unknown_file.read_text(encoding="utf-8"), "keep\n")

    def test_uninstall_without_managed_files_is_a_noop(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Uninstall",
                "--destination",
                str(Path(temporary_directory) / "agent-team"),
                "--yes",
            ]

            with mock.patch.object(sys, "argv", argv):
                result = sync.main()

            self.assertEqual(result, 0)

    def test_restore_requires_a_named_existing_backup(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "agent-team"
            cases = (
                [],
                ["--backup-name", "missing"],
            )
            for extra_arguments in cases:
                with self.subTest(arguments=extra_arguments):
                    argv = [
                        str(PYTHON_SYNC),
                        "--mode",
                        "Restore",
                        "--destination",
                        str(destination),
                        "--yes",
                        *extra_arguments,
                    ]
                    with mock.patch.object(sys, "argv", argv):
                        self.assertEqual(sync.main(), 1)

    def test_restore_rejects_backup_name_path_traversal(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            outside = root / "outside"
            destination.mkdir()
            outside.mkdir()
            current_file = destination / "SKILL.md"
            current_file.write_text("current\n", encoding="utf-8")
            (outside / "SKILL.md").write_text("outside\n", encoding="utf-8")
            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Restore",
                "--destination",
                str(destination),
                "--backup-name",
                "../outside",
                "--yes",
            ]

            with mock.patch.object(sys, "argv", argv):
                result = sync.main()

            self.assertEqual(result, 1)
            self.assertEqual(current_file.read_text(encoding="utf-8"), "current\n")

    def test_install_rejects_symlinked_managed_directory(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            external = root / "external"
            destination.mkdir()
            external.mkdir()
            try:
                os.symlink(
                    external,
                    destination / "references",
                    target_is_directory=True,
                )
            except OSError as error:
                self.skipTest(f"directory symlinks unavailable: {error}")
            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Install",
                "--destination",
                str(destination),
                "--yes",
            ]

            with mock.patch.object(sys, "argv", argv):
                result = sync.main()

            self.assertEqual(result, 1)
            self.assertEqual(list(external.iterdir()), [])

    def test_install_backs_up_current_surface_and_applies_retention(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            destination.mkdir()
            (destination / "SKILL.md").write_text(
                "pre-install\n", encoding="utf-8"
            )
            backup_base = root / ".agent-team-backups"
            for name in ("20000101-000000-oldone", "20000102-000000-oldtwo"):
                old_backup = backup_base / name
                old_backup.mkdir(parents=True)
                (old_backup / "SKILL.md").write_text("older\n", encoding="utf-8")

            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Install",
                "--destination",
                str(destination),
                "--keep-backups",
                "1",
                "--yes",
            ]
            with mock.patch.object(sys, "argv", argv):
                result = sync.main()

            backups = sorted(backup_base.iterdir())
            self.assertEqual(result, 0)
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                (backups[0] / "SKILL.md").read_text(encoding="utf-8"),
                "pre-install\n",
            )

    def test_verify_reports_drift_with_exit_code_two(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "agent-team"
            destination.mkdir()
            (destination / "SKILL.md").write_text("drift\n", encoding="utf-8")
            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Verify",
                "--destination",
                str(destination),
            ]

            with mock.patch.object(sys, "argv", argv):
                result = sync.main()

            self.assertEqual(result, 2)

    def test_restore_copy_failure_rolls_back_managed_surface(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            backup = root / ".agent-team-backups" / "old"
            (destination / "templates").mkdir(parents=True)
            backup.mkdir(parents=True)
            current_file = destination / "SKILL.md"
            current_file.write_text("current\n", encoding="utf-8")
            stale_file = destination / "templates" / "new.md"
            stale_file.write_text("new\n", encoding="utf-8")
            ignored_file = destination / "notes.txt"
            ignored_file.write_text("keep\n", encoding="utf-8")
            (backup / "SKILL.md").write_text("old\n", encoding="utf-8")

            real_copy2 = shutil.copy2
            commit_failed = False

            def fail_first_commit(source, target, *args, **kwargs):
                nonlocal commit_failed
                if (
                    Path(target).resolve() == current_file.resolve()
                    and not commit_failed
                ):
                    commit_failed = True
                    raise OSError("injected restore commit failure")
                return real_copy2(source, target, *args, **kwargs)

            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Restore",
                "--destination",
                str(destination),
                "--backup-name",
                "old",
                "--yes",
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(sync.shutil, "copy2", side_effect=fail_first_commit),
            ):
                result = sync.main()

            self.assertEqual(result, 1)
            self.assertTrue(commit_failed)
            self.assertEqual(current_file.read_text(encoding="utf-8"), "current\n")
            self.assertEqual(stale_file.read_text(encoding="utf-8"), "new\n")
            self.assertEqual(ignored_file.read_text(encoding="utf-8"), "keep\n")

    def test_restore_rollback_failure_preserves_recovery_snapshot(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            backup = root / ".agent-team-backups" / "old"
            destination.mkdir(parents=True)
            backup.mkdir(parents=True)
            current_file = destination / "SKILL.md"
            current_file.write_text("current\n", encoding="utf-8")
            (backup / "SKILL.md").write_text("old\n", encoding="utf-8")

            real_copy2 = shutil.copy2
            destination_attempts = 0

            def fail_commit_and_rollback(source, target, *args, **kwargs):
                nonlocal destination_attempts
                if Path(target).resolve() == current_file.resolve():
                    destination_attempts += 1
                    if destination_attempts <= 2:
                        raise OSError("injected destination copy failure")
                return real_copy2(source, target, *args, **kwargs)

            argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Restore",
                "--destination",
                str(destination),
                "--backup-name",
                "old",
                "--yes",
            ]
            stderr = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    sync.shutil, "copy2", side_effect=fail_commit_and_rollback
                ),
                contextlib.redirect_stderr(stderr),
            ):
                result = sync.main()

            recovery_roots = list(root.glob(".agent-team-restore-*"))
            self.assertEqual(result, 1)
            self.assertEqual(destination_attempts, 2)
            self.assertEqual(len(recovery_roots), 1)
            self.assertIn(str(recovery_roots[0].resolve()), stderr.getvalue())
            self.assertEqual(
                (recovery_roots[0] / "rollback" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "current\n",
            )

    def test_hidden_components_are_ignored_during_install_and_uninstall(self) -> None:
        sync = load_python_sync()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            hidden_file = destination / "references" / ".private.md"
            hidden_file.parent.mkdir(parents=True)
            hidden_file.write_bytes(b"\xffhidden bytes must not be read\n")

            install_argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Install",
                "--destination",
                str(destination),
                "--yes",
            ]
            with mock.patch.object(sys, "argv", install_argv):
                self.assertEqual(sync.main(), 0)

            backup_files = list((root / ".agent-team-backups").rglob("*"))
            self.assertEqual(
                hidden_file.read_bytes(), b"\xffhidden bytes must not be read\n"
            )
            self.assertNotIn(hidden_file, backup_files)

            uninstall_argv = [
                str(PYTHON_SYNC),
                "--mode",
                "Uninstall",
                "--destination",
                str(destination),
                "--yes",
            ]
            with mock.patch.object(sys, "argv", uninstall_argv):
                self.assertEqual(sync.main(), 0)

            self.assertEqual(
                hidden_file.read_bytes(), b"\xffhidden bytes must not be read\n"
            )

    def test_prunes_only_ancestors_of_files_removed_by_each_operation(self) -> None:
        sync = load_python_sync()
        for mode in ("Install", "Restore", "Uninstall"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                destination = root / "agent-team"
                stale_file = destination / "templates" / "obsolete" / "old.md"
                stale_file.parent.mkdir(parents=True)
                stale_file.write_text("stale\n", encoding="utf-8")
                unrelated_empty = destination / "unrelated-empty"
                unrelated_empty.mkdir()

                argv = [
                    str(PYTHON_SYNC),
                    "--mode",
                    mode,
                    "--destination",
                    str(destination),
                    "--yes",
                ]
                if mode == "Restore":
                    backup = root / ".agent-team-backups" / "old"
                    backup.mkdir(parents=True)
                    (backup / "SKILL.md").write_text("old\n", encoding="utf-8")
                    argv.extend(["--backup-name", "old"])

                with mock.patch.object(sys, "argv", argv):
                    self.assertEqual(sync.main(), 0)

                self.assertFalse(stale_file.exists())
                self.assertFalse(stale_file.parent.exists())
                self.assertTrue(unrelated_empty.is_dir())


class PowerShellSyncTests(unittest.TestCase):
    def test_script_avoids_recursive_remove_item(self) -> None:
        text = POWERSHELL_SYNC.read_text(encoding="utf-8")

        self.assertNotRegex(text, r"Remove-Item[^\r\n]*-Recurse")

    def test_uninstall_removal_does_not_suppress_errors(self) -> None:
        text = POWERSHELL_SYNC.read_text(encoding="utf-8")
        uninstall_block = text.split('if ($Mode -eq "Uninstall")', 1)[1].split(
            'if ($Mode -eq "Restore")', 1
        )[0]

        self.assertNotIn("SilentlyContinue", uninstall_block)

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_restore_removes_managed_files_absent_from_backup(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            backup = root / ".agent-team-backups" / "old"
            (destination / "templates").mkdir(parents=True)
            backup.mkdir(parents=True)
            (destination / "SKILL.md").write_text("current\n", encoding="utf-8")
            stale_file = destination / "templates" / "new.md"
            stale_file.write_text("new\n", encoding="utf-8")
            ignored_file = destination / "notes.txt"
            ignored_file.write_text("keep\n", encoding="utf-8")
            (backup / "SKILL.md").write_text("old\n", encoding="utf-8")

            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(POWERSHELL_SYNC),
                    "-Mode",
                    "Restore",
                    "-Destination",
                    str(destination),
                    "-BackupName",
                    "old",
                    "-Confirm:$false",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (destination / "SKILL.md").read_text(encoding="utf-8"), "old\n"
            )
            self.assertFalse(stale_file.exists())
            self.assertEqual(ignored_file.read_text(encoding="utf-8"), "keep\n")

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_restore_copy_failure_rolls_back_managed_surface(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            backup = root / ".agent-team-backups" / "old"
            (destination / "templates").mkdir(parents=True)
            (backup / "references").mkdir(parents=True)
            current_file = destination / "SKILL.md"
            current_file.write_text("current\n", encoding="utf-8")
            stale_file = destination / "templates" / "new.md"
            stale_file.write_text("new\n", encoding="utf-8")
            blocking_unknown_file = destination / "references"
            blocking_unknown_file.write_text("keep\n", encoding="utf-8")
            (backup / "SKILL.md").write_text("old\n", encoding="utf-8")
            (backup / "references" / "old.md").write_text(
                "old reference\n", encoding="utf-8"
            )

            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(POWERSHELL_SYNC),
                    "-Mode",
                    "Restore",
                    "-Destination",
                    str(destination),
                    "-BackupName",
                    "old",
                    "-Confirm:$false",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(current_file.read_text(encoding="utf-8"), "current\n")
            self.assertEqual(stale_file.read_text(encoding="utf-8"), "new\n")
            self.assertEqual(
                blocking_unknown_file.read_text(encoding="utf-8"), "keep\n"
            )

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_restore_rejects_backup_name_path_traversal(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            outside = root / "outside"
            destination.mkdir()
            outside.mkdir()
            current_file = destination / "SKILL.md"
            current_file.write_text("current\n", encoding="utf-8")
            (outside / "SKILL.md").write_text("outside\n", encoding="utf-8")

            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(POWERSHELL_SYNC),
                    "-Mode",
                    "Restore",
                    "-Destination",
                    str(destination),
                    "-BackupName",
                    "../outside",
                    "-Confirm:$false",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(current_file.read_text(encoding="utf-8"), "current\n")

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_hidden_components_are_ignored_during_install_and_uninstall(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "agent-team"
            hidden_file = destination / "references" / ".private.md"
            hidden_file.parent.mkdir(parents=True)
            hidden_file.write_text("do not manage\n", encoding="utf-8")

            for mode in ("Install", "Uninstall"):
                result = subprocess.run(
                    [
                        executable,
                        "-NoProfile",
                        "-NonInteractive",
                        "-File",
                        str(POWERSHELL_SYNC),
                        "-Mode",
                        mode,
                        "-Destination",
                        str(destination),
                        "-Confirm:$false",
                    ],
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    hidden_file.read_text(encoding="utf-8"), "do not manage\n"
                )

            backup_files = list((root / ".agent-team-backups").rglob("*"))
            self.assertNotIn(hidden_file, backup_files)

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_prunes_only_ancestors_of_files_removed_by_each_operation(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        for mode in ("Install", "Restore", "Uninstall"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                destination = root / "agent-team"
                stale_file = destination / "templates" / "obsolete" / "old.md"
                stale_file.parent.mkdir(parents=True)
                stale_file.write_text("stale\n", encoding="utf-8")
                unrelated_empty = destination / "unrelated-empty"
                unrelated_empty.mkdir()

                command = [
                    executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(POWERSHELL_SYNC),
                    "-Mode",
                    mode,
                    "-Destination",
                    str(destination),
                    "-Confirm:$false",
                ]
                if mode == "Restore":
                    backup = root / ".agent-team-backups" / "old"
                    backup.mkdir(parents=True)
                    (backup / "SKILL.md").write_text("old\n", encoding="utf-8")
                    command.extend(["-BackupName", "old"])

                result = subprocess.run(
                    command,
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(stale_file.exists())
                self.assertFalse(stale_file.parent.exists())
                self.assertTrue(unrelated_empty.is_dir())

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_uninstall_keeps_destination_root_with_a_trailing_separator(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "agent-team"
            stale_file = destination / "templates" / "obsolete" / "old.md"
            stale_file.parent.mkdir(parents=True)
            stale_file.write_text("stale\n", encoding="utf-8")

            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(POWERSHELL_SYNC),
                    "-Mode",
                    "Uninstall",
                    "-Destination",
                    str(destination) + os.sep,
                    "-Confirm:$false",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(destination.is_dir())
            self.assertEqual(list(destination.iterdir()), [])

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_uninstall_fails_for_a_locked_managed_file(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        assert executable is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "agent-team"
            blocked_file = destination / "SKILL.md"
            marker_file = Path(temporary_directory) / "remove-item-reached"
            destination.mkdir()
            blocked_file.write_text("managed\n", encoding="utf-8")
            harness = r'''
$scriptPath = $env:SYNC_AGENT_TEAM_SCRIPT
$destination = $env:SYNC_AGENT_TEAM_DESTINATION
$blockedPath = $env:SYNC_AGENT_TEAM_BLOCKED_FILE
$markerPath = $env:SYNC_AGENT_TEAM_MARKER_FILE
function global:Remove-Item {
    param([string]$LiteralPath, [switch]$Force, [string]$ErrorAction)
    if ($LiteralPath -eq $blockedPath) {
        [IO.File]::WriteAllText($markerPath, "Remove-Item reached")
        if ($ErrorAction -eq "SilentlyContinue") { return }
        throw "simulated locked managed file"
    }
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $LiteralPath -Force:$Force
}
& $scriptPath -Mode Uninstall -Destination $destination -Confirm:$false
exit $LASTEXITCODE
'''
            environment = os.environ.copy()
            environment["SYNC_AGENT_TEAM_SCRIPT"] = str(POWERSHELL_SYNC)
            environment["SYNC_AGENT_TEAM_DESTINATION"] = str(destination)
            environment["SYNC_AGENT_TEAM_BLOCKED_FILE"] = str(blocked_file)
            environment["SYNC_AGENT_TEAM_MARKER_FILE"] = str(marker_file)
            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    harness,
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )

            self.assertNotEqual(result.returncode, 0, result.stderr)
            self.assertEqual(marker_file.read_text(encoding="utf-8"), "Remove-Item reached")
            self.assertIn("simulated locked managed file", result.stderr)
            self.assertNotIn("Uninstalled agent-team runtime copy", result.stdout)
            self.assertTrue(blocked_file.exists())


if __name__ == "__main__":
    unittest.main()
