"""Static routing conformance tests.

Loads scenario fixtures and validates every `expect` block against the
cross-field routing invariants. Runs in CI with no API calls. A separate
manual/nightly model layer feeds the same fixtures to a Codex session and
diffs the emitted preview against `expect`.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from routing_rules import validate_scenario

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


if __name__ == "__main__":
    unittest.main()
