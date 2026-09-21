"""Static routing conformance tests.

Loads scenario fixtures and validates every `expect` block against the
cross-field routing invariants. Runs in CI with no API calls. A separate
manual/nightly model layer feeds the same fixtures to a Codex session and
diffs the emitted preview against `expect`.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from routing_rules import authority_from_request, validate_expect, validate_scenario

ROOT = Path(__file__).resolve().parents[1]


class RoutingConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys_path = __import__("sys")
        fixtures_dir = ROOT / "tests" / "scenarios"
        if str(fixtures_dir) not in sys_path.path:
            sys_path.path.insert(0, str(fixtures_dir))
        from fixtures import SCENARIOS

        cls.scenarios = SCENARIOS

    def test_all_scenarios_validate(self) -> None:
        self.assertGreaterEqual(len(self.scenarios), 8)
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                errors = validate_scenario(scenario)
                self.assertEqual(errors, [], f"{scenario['id']}: {errors}")

    def test_scenario_ids_are_unique(self) -> None:
        ids = [scenario["id"] for scenario in self.scenarios]
        self.assertEqual(len(ids), len(set(ids)))

    def test_evidence_loop_fixture_requires_review(self) -> None:
        loop = next(s for s in self.scenarios if s["id"] == "005-evidence-loop-requires-review")
        self.assertEqual(loop["expect"]["convergence"], "evidence-loop")
        self.assertEqual(loop["expect"]["independent_review_gate"], "required")

    def test_persistent_fixture_has_all_gates(self) -> None:
        persistent = next(s for s in self.scenarios if s["id"] == "003-persistent-explicit-authority")
        expect = persistent["expect"]
        for gate in ("authority", "future_reuse", "stable_responsibilities",
                     "role_continuity", "direct_reentry_value", "lifecycle"):
            self.assertIs(expect[f"persistence_{gate}"], True)

    def test_negative_fixture_downgrades_persistence(self) -> None:
        downgrade = next(s for s in self.scenarios if s["id"] == "004-persistent-missing-gates")
        self.assertEqual(downgrade["expect"]["topology"], "temporary")

    def test_request_derives_explicit_agent_team_authority(self) -> None:
        scenario = {
            "id": "authority-mismatch",
            "request": "Use $agent-team to analyze this report.",
            "authority": "implicit",
            "expect": {
                "topology": "single",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "human_gates": ["none"],
            },
        }

        errors = validate_scenario(scenario)

        self.assertIn(
            "request implies authority=explicit-invocation, found implicit",
            errors,
        )

    def test_one_shot_request_rejects_heartbeat(self) -> None:
        scenario = {
            "id": "one-shot-heartbeat",
            "request": "Add validation and run the tests.",
            "authority": "implicit",
            "expect": {
                "topology": "temporary",
                "wakeup": "heartbeat",
                "wakeup_stop_condition": "task completes",
                "convergence": "phase-gated",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "human_gates": ["none"],
            },
        }

        errors = validate_scenario(scenario)

        self.assertIn(
            "heartbeat wakeup requires a recurring request", errors
        )

    def test_recurring_request_requires_wakeup(self) -> None:
        scenario = {
            "id": "recurring-without-wakeup",
            "request": "Use $agent-team to keep monitoring this project.",
            "authority": "explicit-invocation",
            "expect": {
                "topology": "temporary",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "human_gates": ["none"],
            },
        }

        errors = validate_scenario(scenario)

        self.assertIn("recurring request requires heartbeat or cron wakeup", errors)

    def test_chinese_recurring_request_requires_wakeup(self) -> None:
        scenario = {
            "id": "chinese-recurring-without-wakeup",
            "request": "使用 $agent-team 每天持续监控这个项目。",
            "authority": "explicit-invocation",
            "expect": {
                "topology": "temporary",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "human_gates": ["none"],
            },
        }

        errors = validate_scenario(scenario)

        self.assertIn("recurring request requires heartbeat or cron wakeup", errors)

    def test_chinese_continuous_monitoring_requires_wakeup(self) -> None:
        scenario = {
            "id": "chinese-continuous-monitoring",
            "request": "使用 $agent-team 持续监控这个项目。",
            "authority": "explicit-invocation",
            "expect": {
                "topology": "temporary",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "human_gates": ["none"],
            },
        }

        errors = validate_scenario(scenario)

        self.assertIn("recurring request requires heartbeat or cron wakeup", errors)

    def test_one_time_scheduled_request_does_not_require_wakeup(self) -> None:
        scenario = {
            "id": "one-time-scheduled-request",
            "request": "Run the scheduled migration once tomorrow.",
            "authority": "implicit",
            "expect": {
                "topology": "single",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "human_gates": ["none"],
            },
        }

        self.assertEqual(validate_scenario(scenario), [])

    def test_authority_derivation_variants(self) -> None:
        self.assertEqual(
            authority_from_request("Use auto-lifetime for this operation."),
            "auto-lifetime",
        )
        self.assertEqual(
            authority_from_request("Use a multi-agent team for this task."),
            "plain-multi-agent",
        )
        self.assertEqual(
            authority_from_request("Use a persistent team for this program."),
            "explicit-invocation",
        )
        self.assertEqual(authority_from_request("Fix the test."), "implicit")

    def test_invalid_expect_reports_cross_field_errors(self) -> None:
        errors = validate_expect(
            {
                "topology": "invalid",
                "wakeup": "heartbeat",
                "convergence": "evidence-loop",
                "independent_review_gate": "not-required",
                "review_trigger": "explicit-user-request",
                "independent_review_status": "pending",
                "human_gates": ["invalid"],
            }
        )

        self.assertTrue(any("topology must be one of" in error for error in errors))
        self.assertIn(
            "evidence-loop requires independent_review_gate=required", errors
        )
        self.assertIn(
            "not-required review gate must not declare review_trigger", errors
        )
        self.assertIn("heartbeat wakeup requires wakeup_stop_condition", errors)
        self.assertIn("unknown human gate: invalid", errors)

    def test_required_review_validates_trigger_and_stop_condition(self) -> None:
        missing = validate_expect(
            {
                "topology": "single",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "required",
            }
        )
        unknown = validate_expect(
            {
                "topology": "single",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "required",
                "review_trigger": "unknown",
                "review_stop_condition": "review completes",
            }
        )

        self.assertIn("required review gate requires review_trigger", missing)
        self.assertIn(
            "required review gate requires review_stop_condition", missing
        )
        self.assertIn("unknown review_trigger: unknown", unknown)

    def test_persistent_expect_requires_full_contract_and_authority(self) -> None:
        errors = validate_expect(
            {
                "topology": "persistent",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
            },
            authority="implicit",
        )

        self.assertIn(
            "persistent topology requires persistence_authority=true", errors
        )
        self.assertIn(
            "persistent topology requires lifecycle_team_name", errors
        )
        self.assertIn(
            "persistent topology requires explicit-invocation or auto-lifetime authority",
            errors,
        )

    def test_nonpersistent_expect_rejects_persistence_and_task_ownership(self) -> None:
        errors = validate_expect(
            {
                "topology": "temporary",
                "wakeup": "none",
                "convergence": "single-pass",
                "independent_review_gate": "not-required",
                "independent_review_status": "not-applicable",
                "persistence_authority": False,
                "creates_user_owned_tasks": True,
            }
        )

        self.assertIn(
            "non-persistent topology must not declare persistence gates", errors
        )
        self.assertIn(
            "temporary topology must not create user-owned tasks", errors
        )

    def test_scenario_shape_errors_are_reported(self) -> None:
        self.assertIn(
            "scenario missing required field: request",
            validate_scenario({"id": "case"}),
        )
        scenario = {
            "id": "",
            "request": "Fix the test.",
            "authority": "unknown",
            "expect": {},
        }

        errors = validate_scenario(scenario)

        self.assertIn("scenario id must be non-empty", errors)
        self.assertIn("unknown authority: unknown", errors)
        self.assertIn(
            "scenario expect is missing required field: topology", errors
        )


if __name__ == "__main__":
    unittest.main()
