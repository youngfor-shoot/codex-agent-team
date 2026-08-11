from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import evidence_loop


class EvidenceLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("git") is None:
            raise unittest.SkipTest("git is required")
        cls.root = Path(tempfile.mkdtemp(prefix="codex-evidence-loop-tests-"))
        cls.repo = cls.root / "repo"
        cls.worktree = cls.root / "worktree"
        cls.repo.mkdir()
        cls._git(cls.repo, "init")
        cls._git(cls.repo, "config", "user.email", "test@example.invalid")
        cls._git(cls.repo, "config", "user.name", "Evidence Loop Test")
        (cls.repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        cls._git(cls.repo, "add", "seed.txt")
        cls._git(cls.repo, "commit", "-m", "seed")
        cls._git(cls.repo, "worktree", "add", str(cls.worktree), "-b", "test-worktree")

    @classmethod
    def _git(cls, cwd: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def setUp(self) -> None:
        self.case_dir = Path(tempfile.mkdtemp(prefix="case-", dir=self.root))
        self.state = self.case_dir / "state.json"

    def harness(self, body: str = "pass\n") -> Path:
        path = self.case_dir / "harness.py"
        path.write_text(body, encoding="utf-8")
        return path

    def init_args(
        self,
        *,
        command: list[str] | None = None,
        worktree: Path | None = None,
        max_iterations: int = 4,
        max_minutes: int = 45,
        same_failure_limit: int = 2,
        protected_paths: list[str] | None = None,
    ):
        if command is None:
            script = self.harness()
            command = [sys.executable, str(script)]
        harnesses = [
            token
            for token in command
            if Path(token).is_absolute()
            and Path(token).is_file()
            and Path(token).parent == self.case_dir
        ]
        return mock.Mock(
            run_id=self.case_dir.name,
            objective="test objective",
            worktree=str(worktree or self.worktree),
            state_file=str(self.state),
            check_json=[json.dumps(command)],
            frozen_path=[],
            controller_harness=harnesses,
            protected_path=protected_paths or [],
            env_passthrough=[],
            max_iterations=max_iterations,
            max_minutes=max_minutes,
            command_timeout=2,
            same_failure_limit=same_failure_limit,
        )

    def state_args(self, **values):
        defaults = {
            "state_file": str(self.state),
            "expected_contract_hash": self.load()["contract_hash"],
            "expected_state_hash": self.load()["state_hash"],
        }
        defaults.update(values)
        return mock.Mock(**defaults)

    def load(self) -> dict:
        return json.loads(self.state.read_text(encoding="utf-8"))

    def test_pass_requires_review_then_completes(self) -> None:
        self.assertEqual(evidence_loop.init_run(self.init_args()), 0)
        self.assertEqual(
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-pass-1")
            ),
            0,
        )
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 0)
        self.assertEqual(self.load()["status"], "verification_passed")
        self.assertEqual(
            evidence_loop.record_review(
                self.state_args(
                    result="pass",
                    reason_code=None,
                    reviewer_run_id="review-pass-1",
                    reviewer_backend="native-verifier",
                    artifact_hash="a" * 64,
                )
            ),
            0,
        )
        self.assertEqual(self.load()["status"], "completed")

    def test_review_failure_reopens_without_changing_checks(self) -> None:
        evidence_loop.init_run(self.init_args())
        initial_hash = self.load()["contract_hash"]
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-review-fail")
        )
        evidence_loop.verify_iteration(self.state_args())
        self.assertEqual(
            evidence_loop.record_review(
                self.state_args(
                    result="fail",
                    reason_code="confirmed_review_finding",
                    reviewer_run_id="review-fail-1",
                    reviewer_backend="native-verifier",
                    artifact_hash="b" * 64,
                )
            ),
            2,
        )
        state = self.load()
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["contract_hash"], initial_hash)

    def test_same_failure_twice_stops_no_progress(self) -> None:
        script = self.harness("raise SystemExit(7)\n")
        command = [sys.executable, str(script)]
        evidence_loop.init_run(
            self.init_args(command=command, same_failure_limit=2)
        )
        evidence_loop.next_iteration(self.state_args(worker_run_id="worker-fail-1"))
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 2)
        evidence_loop.next_iteration(self.state_args(worker_run_id="worker-fail-2"))
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 3)
        self.assertEqual(self.load()["status"], "stopped_no_progress")

    def test_iteration_budget_stops_before_new_iteration(self) -> None:
        script = self.harness("raise SystemExit(1)\n")
        command = [sys.executable, str(script)]
        evidence_loop.init_run(
            self.init_args(
                command=command, max_iterations=1, same_failure_limit=3
            )
        )
        evidence_loop.next_iteration(self.state_args(worker_run_id="worker-limit-1"))
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 2)
        self.assertEqual(
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-limit-2")
            ),
            3,
        )
        self.assertEqual(self.load()["status"], "stopped_iteration")

    def test_elapsed_time_stops(self) -> None:
        evidence_loop.init_run(self.init_args())
        future = evidence_loop.utc_now() + evidence_loop.timedelta(days=1)
        with mock.patch.object(evidence_loop, "utc_now", return_value=future):
            self.assertEqual(
                evidence_loop.next_iteration(
                    self.state_args(worker_run_id="worker-time-1")
                ),
                3,
            )
        self.assertEqual(self.load()["status"], "stopped_time")

    def test_rejects_main_checkout_and_non_git_directory(self) -> None:
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.init_run(self.init_args(worktree=self.repo))
        non_git = self.case_dir / "plain"
        non_git.mkdir()
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.init_run(self.init_args(worktree=non_git))

    def test_rejects_protected_worktree_and_state_inside_worktree(self) -> None:
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.init_run(
                self.init_args(protected_paths=[str(self.worktree)])
            )
        self.state = self.worktree / f"{self.case_dir.name}.json"
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.init_run(self.init_args())

    def test_rejects_worktree_inside_obsidian_vault(self) -> None:
        marker = self.root / ".obsidian"
        marker.mkdir()
        try:
            with self.assertRaisesRegex(
                evidence_loop.LoopError,
                "cannot target an Obsidian vault",
            ):
                evidence_loop.init_run(self.init_args())
        finally:
            marker.rmdir()

    def test_rejects_control_files_inside_obsidian_vault(self) -> None:
        vault = self.case_dir / "vault"
        (vault / ".obsidian").mkdir(parents=True)

        self.state = vault / "state.json"
        with self.assertRaisesRegex(
            evidence_loop.LoopError,
            "Control files must be outside Obsidian vaults",
        ):
            evidence_loop.init_run(self.init_args())

        self.state = self.case_dir / "state.json"
        harness = vault / "acceptance.py"
        harness.write_text("pass\n", encoding="utf-8")
        args = self.init_args(command=[sys.executable, str(harness)])
        args.controller_harness = [str(harness)]
        with self.assertRaisesRegex(
            evidence_loop.LoopError,
            "Controller harness must be outside writable/protected paths",
        ):
            evidence_loop.init_run(args)

    def test_rejects_direct_shell_and_network_executables(self) -> None:
        for executable in ("powershell.exe", "cmd.exe", "curl"):
            with self.subTest(executable=executable):
                with self.assertRaises(evidence_loop.LoopError):
                    evidence_loop.init_run(
                        self.init_args(command=[executable, "ignored"])
                    )

    def test_detects_immutable_configuration_tampering(self) -> None:
        evidence_loop.init_run(self.init_args())
        state = self.load()
        contract_path = Path(state["contract_file"])
        os.chmod(contract_path, stat.S_IWRITE | stat.S_IWUSR)
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["checks"] = [["fake-test-runner"]]
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-tamper-1")
            )

    def test_detects_mutable_state_tampering_against_pinned_hash(self) -> None:
        evidence_loop.init_run(self.init_args())
        pinned_state_hash = self.load()["state_hash"]
        state = self.load()
        state["status"] = "completed"
        state["state_hash"] = evidence_loop.state_hash(state)
        self.state.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.next_iteration(
                self.state_args(
                    expected_state_hash=pinned_state_hash,
                    worker_run_id="worker-state-tamper",
                )
            )

    def test_abort_is_terminal(self) -> None:
        evidence_loop.init_run(self.init_args())
        self.assertEqual(
            evidence_loop.abort_run(
                self.state_args(reason_code="permission_boundary")
            ),
            0,
        )
        self.assertEqual(self.load()["status"], "aborted")
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-aborted")
            )

    def test_output_is_redacted_and_capped(self) -> None:
        secret = "sk-" + "a" * 24
        script = self.harness(
            f"print('{secret}')\nprint('x' * 5000)\nraise SystemExit(1)\n"
        )
        command = [sys.executable, str(script)]
        evidence_loop.init_run(
            self.init_args(command=command, same_failure_limit=3)
        )
        evidence_loop.next_iteration(self.state_args(worker_run_id="worker-secret-1"))
        evidence_loop.verify_iteration(self.state_args())
        stdout = self.load()["last_verification"]["checks"][0]["stdout"]
        self.assertNotIn(secret, stdout)
        self.assertLessEqual(len(stdout), evidence_loop.MAX_CAPTURE_CHARS + 32)

    def test_frozen_harness_tampering_hard_stops(self) -> None:
        script = self.harness()
        evidence_loop.init_run(self.init_args(command=[sys.executable, str(script)]))
        script.write_text("raise SystemExit(1)\n", encoding="utf-8")
        self.assertEqual(
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-asset-tamper")
            ),
            3,
        )
        self.assertEqual(self.load()["status"], "stopped_acceptance_tampered")

    def test_rejects_reused_worker_and_worker_as_reviewer(self) -> None:
        evidence_loop.init_run(self.init_args())
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-identity-1")
        )
        evidence_loop.verify_iteration(self.state_args())
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.record_review(
                self.state_args(
                    result="pass",
                    reason_code=None,
                    reviewer_run_id="worker-identity-1",
                    reviewer_backend="native-verifier",
                    artifact_hash="c" * 64,
                )
            )

    def test_git_identity_change_is_rejected(self) -> None:
        evidence_loop.init_run(self.init_args())
        changed = evidence_loop.git_identity(self.worktree)
        changed["branch"] = "unexpected-branch"
        with mock.patch.object(evidence_loop, "git_identity", return_value=changed):
            with self.assertRaises(evidence_loop.LoopError):
                evidence_loop.next_iteration(
                    self.state_args(worker_run_id="worker-git-change")
                )

    def test_review_after_deadline_hard_stops(self) -> None:
        evidence_loop.init_run(self.init_args())
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-review-time")
        )
        evidence_loop.verify_iteration(self.state_args())
        future = evidence_loop.utc_now() + evidence_loop.timedelta(days=1)
        with mock.patch.object(evidence_loop, "utc_now", return_value=future):
            self.assertEqual(
                evidence_loop.record_review(
                    self.state_args(
                        result="pass",
                        reason_code=None,
                        reviewer_run_id="review-after-time",
                        reviewer_backend="native-verifier",
                        artifact_hash="d" * 64,
                    )
                ),
                3,
            )
        self.assertEqual(self.load()["status"], "stopped_time")

    def test_source_change_after_verification_requires_reverification(self) -> None:
        evidence_loop.init_run(self.init_args())
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-source-change")
        )
        evidence_loop.verify_iteration(self.state_args())
        seed = self.worktree / "seed.txt"
        original = seed.read_text(encoding="utf-8")
        try:
            seed.write_text("changed after verification\n", encoding="utf-8")
            self.assertEqual(
                evidence_loop.record_review(
                    self.state_args(
                        result="pass",
                        reason_code=None,
                        reviewer_run_id="review-stale-source",
                        reviewer_backend="native-verifier",
                        artifact_hash="e" * 64,
                    )
                ),
                2,
            )
            self.assertEqual(self.load()["status"], "active")
        finally:
            seed.write_text(original, encoding="utf-8")

    def test_frozen_asset_change_after_verification_hard_stops(self) -> None:
        script = self.harness()
        evidence_loop.init_run(self.init_args(command=[sys.executable, str(script)]))
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-late-asset-change")
        )
        evidence_loop.verify_iteration(self.state_args())
        script.write_text("raise SystemExit(1)\n", encoding="utf-8")
        self.assertEqual(
            evidence_loop.record_review(
                self.state_args(
                    result="pass",
                    reason_code=None,
                    reviewer_run_id="review-late-asset-change",
                    reviewer_backend="native-verifier",
                    artifact_hash="f" * 64,
                )
            ),
            3,
        )
        self.assertEqual(self.load()["status"], "stopped_acceptance_tampered")

    @unittest.skipUnless(sys.platform == "win32", "Windows Job Object test")
    def test_windows_job_kills_lingering_descendant(self) -> None:
        pid_file = self.case_dir / "descendant.pid"
        script = self.harness(
            "import subprocess, sys\n"
            f"pid_file = {str(pid_file)!r}\n"
            "child = subprocess.Popen([sys.executable, '-c', "
            "'import time; time.sleep(30)'])\n"
            "open(pid_file, 'w', encoding='utf-8').write(str(child.pid))\n"
        )
        evidence_loop.init_run(self.init_args(command=[sys.executable, str(script)]))
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-descendant")
        )
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 0)
        pid = int(pid_file.read_text(encoding="utf-8"))
        for _ in range(20):
            if not self._process_is_running(pid):
                break
            time.sleep(0.05)
        self.assertFalse(self._process_is_running(pid))

    @staticmethod
    def _process_is_running(pid: int) -> bool:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = (
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        )
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == 259
        finally:
            kernel32.CloseHandle(handle)

    def test_command_timeout_is_recorded(self) -> None:
        script = self.harness("import time\ntime.sleep(5)\n")
        args = self.init_args(command=[sys.executable, str(script)])
        args.command_timeout = 1
        evidence_loop.init_run(args)
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-timeout-1")
        )
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 2)
        self.assertTrue(
            self.load()["last_verification"]["checks"][0]["timed_out"]
        )

    def test_contract_file_is_read_only_after_init(self) -> None:
        evidence_loop.init_run(self.init_args())
        contract_path = Path(self.load()["contract_file"])
        mode = stat.S_IMODE(contract_path.stat().st_mode)
        self.assertEqual(mode & stat.S_IWRITE, 0)

    def test_contract_file_write_after_readonly_raises(self) -> None:
        evidence_loop.init_run(self.init_args())
        contract_path = Path(self.load()["contract_file"])
        with self.assertRaises(OSError):
            with contract_path.open("a", encoding="utf-8"):
                pass

    def test_sanitized_environment_includes_posix_variables(self) -> None:
        previous = {
            name: evidence_loop.os.environ.get(name) for name in ("HOME", "LANG", "LOGNAME")
        }
        evidence_loop.os.environ["HOME"] = "/home/test"
        evidence_loop.os.environ["LANG"] = "en_US.UTF-8"
        evidence_loop.os.environ["LOGNAME"] = "test"
        try:
            sanitized = evidence_loop.sanitized_environment()
        finally:
            for name, value in previous.items():
                if value is None:
                    evidence_loop.os.environ.pop(name, None)
                else:
                    evidence_loop.os.environ[name] = value
        self.assertEqual(sanitized.get("HOME"), "/home/test")
        self.assertEqual(sanitized.get("LANG"), "en_US.UTF-8")
        self.assertEqual(sanitized.get("LOGNAME"), "test")

    def test_env_passthrough_adds_named_variables(self) -> None:
        previous = {
            name: evidence_loop.os.environ.get(name)
            for name in ("AGENT_TEAM_CUSTOM", "AGENT_TEAM_BLOCKED")
        }
        evidence_loop.os.environ["AGENT_TEAM_CUSTOM"] = "allowed"
        evidence_loop.os.environ["AGENT_TEAM_BLOCKED"] = "blocked"
        try:
            sanitized = evidence_loop.sanitized_environment(("AGENT_TEAM_CUSTOM",))
        finally:
            for name, value in previous.items():
                if value is None:
                    evidence_loop.os.environ.pop(name, None)
                else:
                    evidence_loop.os.environ[name] = value
        self.assertEqual(sanitized.get("AGENT_TEAM_CUSTOM"), "allowed")
        self.assertNotIn("AGENT_TEAM_BLOCKED", sanitized)

    def test_env_passthrough_is_frozen_into_contract(self) -> None:
        args = self.init_args()
        args.env_passthrough = ["AGENT_TEAM_CUSTOM"]
        evidence_loop.init_run(args)
        contract_path = Path(self.load()["contract_file"])
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["env_passthrough"], ["AGENT_TEAM_CUSTOM"])

    def test_env_passthrough_rejects_invalid_name(self) -> None:
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.validate_env_passthrough(("NOT A VALID NAME",))

    def test_run_check_passes_frozen_environment(self) -> None:
        script = self.harness(
            "import os\n"
            "print('CUSTOM=' + os.environ.get('AGENT_TEAM_CUSTOM', 'unset'))\n"
        )
        args = self.init_args(command=[sys.executable, str(script)])
        args.env_passthrough = ["AGENT_TEAM_CUSTOM"]
        evidence_loop.os.environ["AGENT_TEAM_CUSTOM"] = "frozen-value"
        try:
            evidence_loop.init_run(args)
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-env-pass")
            )
            evidence_loop.verify_iteration(self.state_args())
        finally:
            evidence_loop.os.environ.pop("AGENT_TEAM_CUSTOM", None)
        stdout = self.load()["last_verification"]["checks"][0]["stdout"]
        self.assertIn("CUSTOM=frozen-value", stdout)


if __name__ == "__main__":
    unittest.main()
