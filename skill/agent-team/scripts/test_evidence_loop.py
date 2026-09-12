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

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
V01_FIXTURE_ROOT = PACKAGE_ROOT / "tests" / "fixtures" / "v0.1.0"


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
            review_grace_minutes=15,
            active_budget_seconds=None,
            max_capture_chars=4_000,
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

    def test_failed_init_preserves_preexisting_lock_file(self) -> None:
        lock_path = self.state.with_name(f"{self.state.name}.lock")
        lock_path.write_bytes(b"existing-lock")
        evidence_loop.contract_path_for(self.state).write_text(
            "{}\n", encoding="utf-8"
        )

        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.init_run(self.init_args())

        self.assertEqual(lock_path.read_bytes(), b"existing-lock")

    def test_failed_init_lock_namespace_is_reusable(self) -> None:
        contract_path = evidence_loop.contract_path_for(self.state)
        contract_path.write_text("{}\n", encoding="utf-8")

        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.init_run(self.init_args())

        lock_path = self.state.with_name(f"{self.state.name}.lock")
        self.assertTrue(lock_path.is_file())
        contract_path.unlink()
        self.assertEqual(evidence_loop.init_run(self.init_args()), 0)

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
            with (
                self.subTest(executable=executable),
                self.assertRaises(evidence_loop.LoopError),
            ):
                evidence_loop.init_run(
                    self.init_args(command=[executable, "ignored"])
                )

    def test_detects_immutable_configuration_tampering(self) -> None:
        evidence_loop.init_run(self.init_args())
        state = self.load()
        contract_path = Path(state["contract_file"])
        os.chmod(contract_path, stat.S_IRUSR | stat.S_IWUSR)
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

    def test_redacts_extended_secret_shapes(self) -> None:
        samples = {
            "aws": "AKIAIOSFODNN7EXAMPLE",
            "github": "ghp_" + "a" * 36,
            "github_pat": "github_pat_" + "b" * 30,
            "slack": "xoxb-" + "c" * 24,
            "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            "pem": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFA\n-----END PRIVATE KEY-----",
        }
        for label, value in samples.items():
            with self.subTest(label=label):
                redacted = evidence_loop.redact(value)
                self.assertNotIn(value, redacted, msg=f"{label} not redacted")
                self.assertNotEqual(redacted, value)

    def test_redact_keeps_plain_text(self) -> None:
        self.assertEqual(evidence_loop.redact("ordinary build output"), "ordinary build output")

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
        with (
            mock.patch.object(evidence_loop, "git_identity", return_value=changed),
            self.assertRaises(evidence_loop.LoopError),
        ):
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

    def test_active_budget_exceeds_stops(self) -> None:
        # A slow check accumulates active_seconds past a tiny budget.
        script = self.harness("import time\ntime.sleep(3)\n")
        args = self.init_args(command=[sys.executable, str(script)])
        args.active_budget_seconds = 1
        args.command_timeout = 5
        evidence_loop.init_run(args)
        evidence_loop.next_iteration(self.state_args(worker_run_id="worker-active-1"))
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 3)
        state = self.load()
        self.assertEqual(state["status"], "stopped_time")
        self.assertEqual(state["stop_reason"], "active_budget_exceeded")

    def test_active_budget_limits_each_check_timeout(self) -> None:
        args = self.init_args()
        args.active_budget_seconds = 1
        args.command_timeout = 5
        evidence_loop.init_run(args)
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-active-timeout")
        )
        result = {
            "command": args.check_json,
            "returncode": 0,
            "timed_out": False,
            "duration_seconds": 0.5,
            "stdout": "",
            "stderr": "",
        }

        with mock.patch.object(
            evidence_loop, "run_check", return_value=result
        ) as run_check:
            self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 0)

        self.assertEqual(run_check.call_args.args[2], 1.0)

    def test_review_grace_window_allows_late_review(self) -> None:
        # Verification passed; review within grace succeeds even past the
        # original wall-clock deadline.
        evidence_loop.init_run(self.init_args(max_minutes=1))
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-grace-1")
        )
        evidence_loop.verify_iteration(self.state_args())
        later = evidence_loop.utc_now() + evidence_loop.timedelta(minutes=10)
        with mock.patch.object(evidence_loop, "utc_now", return_value=later):
            self.assertEqual(
                evidence_loop.record_review(
                    self.state_args(
                        result="pass",
                        reason_code=None,
                        reviewer_run_id="review-grace-1",
                        reviewer_backend="native-verifier",
                        artifact_hash="a" * 64,
                    )
                ),
                0,
            )
        self.assertEqual(self.load()["status"], "completed")

    def test_review_grace_expired_stops(self) -> None:
        evidence_loop.init_run(self.init_args())
        evidence_loop.next_iteration(
            self.state_args(worker_run_id="worker-grace-expire")
        )
        evidence_loop.verify_iteration(self.state_args())
        # 1 hour is inside the 8x wall-clock backstop but beyond the 15-minute
        # review grace window, so the run stops for grace expiry, not time.
        far_future = evidence_loop.utc_now() + evidence_loop.timedelta(hours=1)
        with mock.patch.object(evidence_loop, "utc_now", return_value=far_future):
            self.assertEqual(
                evidence_loop.record_review(
                    self.state_args(
                        result="pass",
                        reason_code=None,
                        reviewer_run_id="review-grace-expired",
                        reviewer_backend="native-verifier",
                        artifact_hash="b" * 64,
                    )
                ),
                3,
            )
        self.assertEqual(self.load()["status"], "stopped_time")
        self.assertEqual(self.load()["stop_reason"], "review_grace_expired")

    def test_inspect_requires_acknowledgement(self) -> None:
        evidence_loop.init_run(self.init_args())
        args = mock.Mock(
            state_file=str(self.state),
            acknowledge_unpinned=False,
            verbose=False,
        )
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.inspect_run(args)

    def test_inspect_unpinned_records_event(self) -> None:
        evidence_loop.init_run(self.init_args())
        args = mock.Mock(
            state_file=str(self.state),
            acknowledge_unpinned=True,
            verbose=True,
        )
        self.assertEqual(evidence_loop.inspect_run(args), 0)
        events = [item["event"] for item in self.load()["history"]]
        self.assertIn("unpinned_inspection", events)

    def test_abort_unpinned_allowed(self) -> None:
        evidence_loop.init_run(self.init_args())
        args = mock.Mock(
            state_file=str(self.state),
            expected_contract_hash="",
            expected_state_hash="",
            acknowledge_unpinned=True,
            reason_code="pin_lost",
        )
        self.assertEqual(evidence_loop.abort_run(args), 0)
        self.assertEqual(self.load()["status"], "aborted")

    def test_abort_without_hashes_rejected(self) -> None:
        evidence_loop.init_run(self.init_args())
        args = mock.Mock(
            state_file=str(self.state),
            expected_contract_hash="",
            expected_state_hash="",
            acknowledge_unpinned=False,
            reason_code="pin_lost",
        )
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.abort_run(args)

    def test_list_runs_enumerates_state_files(self) -> None:
        evidence_loop.init_run(self.init_args())
        args = mock.Mock(root=str(self.case_dir))
        self.assertEqual(evidence_loop.list_runs(args), 0)

    def test_list_runs_rejects_missing_root(self) -> None:
        args = mock.Mock(root=str(self.case_dir / "does-not-exist"))
        with self.assertRaises(evidence_loop.LoopError):
            evidence_loop.list_runs(args)

    def test_cli_returns_nonzero_for_missing_list_root(self) -> None:
        result = evidence_loop.main(
            ["list", "--root", str(self.case_dir / "does-not-exist")]
        )

        self.assertEqual(result, 1)

    def test_cli_lists_runs_from_existing_root(self) -> None:
        result = evidence_loop.main(["list", "--root", str(self.case_dir)])

        self.assertEqual(result, 0)

    def test_show_status_reads_a_pinned_run(self) -> None:
        evidence_loop.init_run(self.init_args())

        result = evidence_loop.show_status(
            self.state_args(verbose=True)
        )

        self.assertEqual(result, 0)

    def test_list_runs_skips_corrupt_json(self) -> None:
        (self.case_dir / "not-a-state.json").write_text("{", encoding="utf-8")

        result = evidence_loop.list_runs(mock.Mock(root=str(self.case_dir)))

        self.assertEqual(result, 0)

    def test_path_fingerprint_hashes_a_directory(self) -> None:
        asset_directory = self.case_dir / "assets"
        asset_directory.mkdir()
        (asset_directory / "one.txt").write_text("one\n", encoding="utf-8")

        fingerprint = evidence_loop.path_fingerprint(asset_directory)

        self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")

    def test_path_fingerprint_rejects_sensitive_and_missing_paths(self) -> None:
        sensitive = self.case_dir / ".env"
        sensitive.write_text("not-a-secret\n", encoding="utf-8")

        with self.subTest(case="sensitive"), self.assertRaisesRegex(
            evidence_loop.LoopError, "Sensitive-looking"
        ):
            evidence_loop.path_fingerprint(sensitive)
        with self.subTest(case="missing"), self.assertRaisesRegex(
            evidence_loop.LoopError, "does not exist"
        ):
            evidence_loop.path_fingerprint(self.case_dir / "missing")

    def test_source_fingerprint_accounts_for_untracked_files(self) -> None:
        baseline = evidence_loop.source_fingerprint(
            self.worktree, evidence_loop.git_identity(self.worktree)["base_commit"]
        )
        plain = self.worktree / "coverage-untracked.txt"
        sensitive = self.worktree / ".env.coverage"
        try:
            plain.write_text("plain\n", encoding="utf-8")
            sensitive.write_text("not-a-secret\n", encoding="utf-8")

            changed = evidence_loop.source_fingerprint(
                self.worktree,
                evidence_loop.git_identity(self.worktree)["base_commit"],
            )
        finally:
            plain.unlink(missing_ok=True)
            sensitive.unlink(missing_ok=True)

        self.assertNotEqual(changed, baseline)

    def test_source_fingerprint_accounts_for_untracked_symlink_target(self) -> None:
        first_target = self.case_dir / "first-target.txt"
        second_target = self.case_dir / "second-target.txt"
        first_target.write_text("first\n", encoding="utf-8")
        second_target.write_text("second\n", encoding="utf-8")
        link = self.worktree / "coverage-untracked-link.txt"
        try:
            os.symlink(first_target, link)
        except OSError as error:
            self.skipTest(f"file symlinks unavailable: {error}")
        try:
            first = evidence_loop.source_fingerprint(
                self.worktree,
                evidence_loop.git_identity(self.worktree)["base_commit"],
            )
            link.unlink()
            os.symlink(second_target, link)
            second = evidence_loop.source_fingerprint(
                self.worktree,
                evidence_loop.git_identity(self.worktree)["base_commit"],
            )
        finally:
            link.unlink(missing_ok=True)

        self.assertNotEqual(second, first)

    def test_run_check_reports_missing_executable(self) -> None:
        result = evidence_loop.run_check(
            ["codex-agent-team-missing-executable"],
            self.worktree,
            timeout_seconds=1,
        )

        self.assertNotEqual(result["returncode"], 0)
        self.assertFalse(result["timed_out"])

    def test_parse_command_rejects_invalid_and_inline_evaluation(self) -> None:
        cases = (
            ("not-json", "not valid JSON"),
            ("[]", "non-empty JSON string array"),
            ('["node", "--eval", "1"]', "Inline Node.js"),
            ('["python", "-c", "pass"]', "Inline Python"),
        )
        for raw, message in cases:
            with self.subTest(raw=raw), self.assertRaisesRegex(
                evidence_loop.LoopError, message
            ):
                evidence_loop.parse_command(raw)

    def test_bounded_int_rejects_out_of_range_values(self) -> None:
        parse = evidence_loop.bounded_int(1, 2)

        with self.assertRaisesRegex(
            evidence_loop.argparse.ArgumentTypeError, "between 1 and 2"
        ):
            parse("3")

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
        with self.assertRaises(OSError), contract_path.open("a", encoding="utf-8"):
            pass

    def test_schema_v1_files_without_additive_fields_remain_usable(self) -> None:
        evidence_loop.init_run(self.init_args())
        state = self.load()
        contract_path = Path(state["contract_file"])
        os.chmod(contract_path, stat.S_IRUSR | stat.S_IWUSR)
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract.pop("env_passthrough")
        for field in (
            "active_budget_seconds",
            "review_grace_minutes",
            "max_capture_chars",
        ):
            contract["limits"].pop(field)
        contract_path.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        state.pop("active_seconds")
        state["contract_hash"] = evidence_loop.contract_hash(contract)
        state["state_hash"] = evidence_loop.state_hash(state)
        self.state.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        self.assertEqual(
            evidence_loop.next_iteration(
                self.state_args(worker_run_id="worker-schema-v1")
            ),
            0,
        )
        self.assertEqual(evidence_loop.verify_iteration(self.state_args()), 0)
        self.assertEqual(
            evidence_loop.record_review(
                self.state_args(
                    result="pass",
                    reason_code=None,
                    reviewer_run_id="review-schema-v1",
                    reviewer_backend="native-verifier",
                    artifact_hash="c" * 64,
                )
            ),
            0,
        )

    def test_v010_verification_passed_fixture_uses_recorded_review_grace(self) -> None:
        harness = self.harness()
        contract = json.loads(
            (V01_FIXTURE_ROOT / "evidence-loop-contract.json").read_text(
                encoding="utf-8"
            )
        )
        identity = evidence_loop.git_identity(self.worktree)
        contract.update(
            {
                "worktree": str(self.worktree),
                "checks": [[sys.executable, str(harness)]],
                "controller_harnesses": [str(harness)],
                "git_identity": identity,
            }
        )
        contract_path = evidence_loop.contract_path_for(self.state)
        contract_path.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        state = json.loads(
            (
                V01_FIXTURE_ROOT
                / "evidence-loop-state-verification-passed.json"
            ).read_text(encoding="utf-8")
        )
        state["contract_file"] = str(contract_path)
        state["contract_hash"] = evidence_loop.contract_hash(contract)
        state["last_verification"]["source_fingerprint"] = (
            evidence_loop.source_fingerprint(
                self.worktree, identity["base_commit"]
            )
        )
        state["state_hash"] = evidence_loop.state_hash(state)
        self.state.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with mock.patch.object(
            evidence_loop,
            "utc_now",
            return_value=evidence_loop.parse_time("2026-08-02T00:10:00Z"),
        ):
            result = evidence_loop.record_review(
                self.state_args(
                    result="pass",
                    reason_code=None,
                    reviewer_run_id="v0-review-1",
                    reviewer_backend="native-verifier",
                    artifact_hash="d" * 64,
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(self.load()["status"], "completed")

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

    def test_posix_env_passthrough_preserves_exact_case(self) -> None:
        environment = {
            "AGENT_TEAM_CUSTOM": "upper",
            "agent_team_custom": "lower",
            "PATH": "/usr/bin",
        }
        with (
            mock.patch.object(evidence_loop.os, "name", "posix"),
            mock.patch.object(evidence_loop.os, "environ", environment),
        ):
            names = evidence_loop.validate_env_passthrough(
                ("AGENT_TEAM_CUSTOM",)
            )
            sanitized = evidence_loop.sanitized_environment(names)

        self.assertEqual(names, ["AGENT_TEAM_CUSTOM"])
        self.assertEqual(sanitized["AGENT_TEAM_CUSTOM"], "upper")
        self.assertNotIn("agent_team_custom", sanitized)

    def test_posix_environment_does_not_inherit_parent_pwd(self) -> None:
        environment = {"PATH": "/usr/bin", "PWD": "/wrong/worktree"}
        with (
            mock.patch.object(evidence_loop.os, "name", "posix"),
            mock.patch.object(evidence_loop.os, "environ", environment),
        ):
            sanitized = evidence_loop.sanitized_environment()

        self.assertNotIn("PWD", sanitized)

    def test_posix_env_passthrough_keeps_mixed_case_name(self) -> None:
        with mock.patch.object(evidence_loop.os, "name", "posix"):
            names = evidence_loop.validate_env_passthrough(
                ("Agent_Team_Custom",)
            )

        self.assertEqual(names, ["Agent_Team_Custom"])

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
