"""Tests for Agent Team task-packet completion invariants."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import validate_task_packet
from validate_task_packet import validate_packet, validate_template


def handoff() -> str:
    return """<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>"""


def packet(
    *,
    contract_version: str = "1",
    status: str = "in_progress",
    topology: str = "temporary",
    wakeup: str = "heartbeat",
    convergence: str = "phase-gated",
    review_gate: str = "not-required",
    review_status: str = "not-applicable",
    user_complete: str = "false",
    phases_complete: str = "false",
    whole_complete: str = "false",
    gaps: str = "visual approval",
    checked: bool = False,
    completed_at: str = "pending",
    remaining_risks: str = "visual approval",
) -> str:
    mark = "x" if checked else " "
    return f"""# Task

- `contract_version`: `{contract_version}`
- `task_id`: `case`
- `status`: `{status}`
- `execution_topology`: `{topology}`
- `wakeup_mode`: `{wakeup}`
- `convergence_strategy`: `{convergence}`
- `independent_review_gate`: `{review_gate}`
- `independent_review_status`: `{review_status}`
- `current_phase`: `verification`
- `user_visible_objective_complete`: `{user_complete}`
- `all_required_phases_verified`: `{phases_complete}`
- `whole_task_verified`: `{whole_complete}`
- `blocking_core_gaps`: `{gaps}`

## Intent Ledger

Canonical objective.

## Routing Decision

Independent routing evidence.

## Phase Gates

Phase evidence.

## Objective

Deliver the objective.

## Completion Criteria

- [{mark}] Whole-task verification passed.

## Integration Checklist

- [{mark}] The user-visible objective is actually complete.

## Final State

- `status`: `{status}`
- `completed_at`: `{completed_at}`
- `remaining_risks`: `{remaining_risks}`

{handoff()}
"""


def template() -> str:
    return """# Task

- `contract_version`: `1`
- `task_id`: `case`
- `status`: `pending`
- `execution_topology`: `temporary`
- `wakeup_mode`: `none`
- `convergence_strategy`: `single-pass`
- `independent_review_gate`: `not-required`
- `independent_review_status`: `not-applicable`
- `current_phase`: `execution`
- `user_visible_objective_complete`: `false`
- `all_required_phases_verified`: `false`
- `whole_task_verified`: `false`
- `blocking_core_gaps`: `execution`

## Intent Ledger
## Routing Decision
## Phase Gates
## Objective
## Completion Criteria

### Guidance
### Context
### Mission

## Integration Checklist
## Final State

<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>
"""


class TaskPacketValidatorTests(unittest.TestCase):
    def test_valid_in_progress_packet(self) -> None:
        self.assertEqual(validate_packet(packet(), require_complete=False), [])

    def test_packet_requires_handoff_block(self) -> None:
        errors = validate_packet(
            packet().replace(handoff(), ""), require_complete=False
        )

        self.assertIn(
            "packet requires exactly one <task_handoff> block, found 0",
            errors,
        )

    def test_packet_handoff_block_must_be_final(self) -> None:
        errors = validate_packet(
            packet() + "\nUnexpected trailing text.\n", require_complete=False
        )

        self.assertIn("packet handoff block must be final content", errors)

    def test_packet_requires_contract_version(self) -> None:
        without_version = "\n".join(
            line for line in packet().splitlines() if "`contract_version`" not in line
        )

        errors = validate_packet(without_version, require_complete=False)

        self.assertIn("missing field: contract_version", errors)

    def test_packet_rejects_duplicate_metadata_field(self) -> None:
        duplicate = packet().replace(
            "- `contract_version`: `1`",
            "- `contract_version`: `1`\n- `contract_version`: `1`",
            1,
        )

        errors = validate_packet(duplicate, require_complete=False)

        self.assertIn("packet duplicate metadata field: contract_version", errors)

    def test_packet_rejects_duplicate_final_state_field(self) -> None:
        duplicate = packet().replace(
            "- `remaining_risks`: `visual approval`",
            "- `remaining_risks`: `visual approval`\n"
            "- `remaining_risks`: `none`",
            1,
        )

        errors = validate_packet(duplicate, require_complete=False)

        self.assertIn("packet duplicate final state field: remaining_risks", errors)

    def test_packet_rejects_duplicate_required_heading(self) -> None:
        duplicate = packet().replace(
            "## Objective\n\nDeliver the objective.",
            "## Objective\n\nFirst objective.\n\n## Objective\n\nSecond objective.",
            1,
        )

        errors = validate_packet(duplicate, require_complete=False)

        self.assertIn("packet duplicate heading: ## Objective", errors)

    def test_packet_rejects_conflicting_final_status(self) -> None:
        conflicting = packet().replace(
            "## Final State\n\n- `status`: `in_progress`",
            "## Final State\n\n- `status`: `completed`",
            1,
        )

        errors = validate_packet(conflicting, require_complete=False)

        self.assertIn(
            "final state status must match metadata status, found 'completed'",
            errors,
        )

    def test_packet_rejects_stray_handoff_closing_tag(self) -> None:
        errors = validate_packet(
            packet() + "\n</task_handoff>\n", require_complete=False
        )

        self.assertIn(
            "packet requires exactly one </task_handoff> tag, found 2", errors
        )

    def test_packet_rejects_nested_handoff_opening_tag(self) -> None:
        nested = packet().replace(
            "<task_handoff>", "<task_handoff>\n<task_handoff>", 1
        )

        errors = validate_packet(nested, require_complete=False)

        self.assertIn(
            "packet requires exactly one <task_handoff> tag, found 2", errors
        )

    def test_packet_rejects_duplicate_handoff_field(self) -> None:
        duplicate = packet().replace(
            "finding_severity: none",
            "finding_severity: none\nfinding_severity: MAJOR",
            1,
        )

        errors = validate_packet(duplicate, require_complete=False)

        self.assertIn("packet duplicate handoff field: finding_severity", errors)

    def test_rejects_automation_as_execution_topology(self) -> None:
        errors = validate_packet(
            packet(topology="automation"), require_complete=False
        )
        self.assertTrue(
            any("execution_topology must be one of" in error for error in errors)
        )

    def test_rejects_invalid_routing_and_contract_values(self) -> None:
        contract_errors = validate_packet(
            packet(contract_version="2"), require_complete=False
        )
        errors = validate_packet(
            packet(
                topology="invalid",
                wakeup="invalid",
                convergence="invalid",
                review_gate="invalid",
                review_status="invalid",
            ),
            require_complete=False,
        )

        self.assertTrue(
            any("unsupported contract_version" in error for error in contract_errors)
        )
        self.assertTrue(any("execution_topology must be one of" in error for error in errors))
        self.assertTrue(any("wakeup_mode must be one of" in error for error in errors))
        self.assertTrue(any("convergence_strategy must be one of" in error for error in errors))
        self.assertTrue(any("independent_review_gate must be one of" in error for error in errors))
        self.assertTrue(any("independent_review_status must be one of" in error for error in errors))

    def test_rejects_invalid_boolean_fields(self) -> None:
        errors = validate_packet(
            packet(
                user_complete="pending",
                phases_complete="pending",
                whole_complete="pending",
            ),
            require_complete=False,
        )

        self.assertIn(
            "user_visible_objective_complete must be true or false, found 'pending'",
            errors,
        )
        self.assertIn(
            "all_required_phases_verified must be true or false, found 'pending'",
            errors,
        )
        self.assertIn(
            "whole_task_verified must be true or false, found 'pending'", errors
        )

    def test_rejects_whole_task_completion_with_core_gap(self) -> None:
        errors = validate_packet(
            packet(
                status="completed",
                user_complete="true",
                phases_complete="true",
                whole_complete="true",
                checked=True,
                completed_at="2026-07-27",
                remaining_risks="none",
            ),
            require_complete=True,
        )
        self.assertIn(
            "whole_task_verified=true requires blocking_core_gaps=none", errors
        )

    def test_whole_task_completion_requires_objective_and_phases(self) -> None:
        errors = validate_packet(
            packet(whole_complete="true", gaps="none"), require_complete=False
        )

        self.assertIn(
            "whole_task_verified=true requires user_visible_objective_complete=true",
            errors,
        )
        self.assertIn(
            "whole_task_verified=true requires all_required_phases_verified=true",
            errors,
        )

    def test_evidence_loop_requires_independent_review(self) -> None:
        errors = validate_packet(
            packet(convergence="evidence-loop"), require_complete=False
        )
        self.assertIn(
            "evidence-loop requires independent_review_gate=required", errors
        )

    def test_not_required_review_uses_not_applicable_status(self) -> None:
        errors = validate_packet(
            packet(review_status="pending"), require_complete=False
        )
        self.assertIn(
            "independent_review_gate=not-required requires "
            "independent_review_status=not-applicable",
            errors,
        )

    def test_completed_required_review_must_pass(self) -> None:
        errors = validate_packet(
            packet(
                status="completed",
                review_gate="required",
                review_status="pending",
                user_complete="true",
                phases_complete="true",
                whole_complete="true",
                gaps="none",
                checked=True,
                completed_at="2026-08-02",
                remaining_risks="none",
            ),
            require_complete=True,
        )
        self.assertIn(
            "completed packet with required review requires "
            "independent_review_status=passed",
            errors,
        )

    def test_required_review_rejects_not_applicable_status(self) -> None:
        errors = validate_packet(
            packet(review_gate="required", review_status="not-applicable"),
            require_complete=False,
        )

        self.assertIn(
            "independent_review_gate=required cannot use "
            "independent_review_status=not-applicable",
            errors,
        )

    def test_completion_mode_reports_every_open_invariant(self) -> None:
        errors = validate_packet(packet(), require_complete=True)

        self.assertTrue(any("requires status=completed" in error for error in errors))
        self.assertIn(
            "completed packet requires user_visible_objective_complete=true",
            errors,
        )
        self.assertIn(
            "completed packet requires all_required_phases_verified=true", errors
        )
        self.assertIn("completed packet requires whole_task_verified=true", errors)
        self.assertIn("completed packet requires blocking_core_gaps=none", errors)
        self.assertTrue(any("unchecked item" in error for error in errors))
        self.assertIn(
            "completed packet requires a final completed_at value", errors
        )
        self.assertIn("completed packet requires remaining_risks=none", errors)

    def test_accepts_completed_evidence_loop_after_review_pass(self) -> None:
        errors = validate_packet(
            packet(
                status="completed",
                convergence="evidence-loop",
                review_gate="required",
                review_status="passed",
                user_complete="true",
                phases_complete="true",
                whole_complete="true",
                gaps="none",
                checked=True,
                completed_at="2026-08-02",
                remaining_risks="none",
            ),
            require_complete=True,
        )
        self.assertEqual(errors, [])

    def test_rejects_legacy_completion_contradiction(self) -> None:
        contradictory = packet(checked=True).replace(
            "- [x] The user-visible objective",
            "- [ ] The user-visible objective",
        )
        errors = validate_packet(contradictory, require_complete=False)
        self.assertIn(
            "whole-task verification is checked while the user-visible "
            "objective remains unchecked",
            errors,
        )

    def test_accepts_fully_completed_packet(self) -> None:
        errors = validate_packet(
            packet(
                status="completed",
                user_complete="true",
                phases_complete="true",
                whole_complete="true",
                gaps="none",
                checked=True,
                completed_at="2026-07-27",
                remaining_risks="none",
            ),
            require_complete=True,
        )
        self.assertEqual(errors, [])

    def test_template_requires_alignment_handoff_fields(self) -> None:
        errors = validate_template("## Intent Ledger")
        self.assertIn("template missing handoff field: goal_alignment:", errors)

    def test_accepts_dispatch_and_finding_severity_contract(self) -> None:
        self.assertEqual(validate_template(template()), [])

    def test_template_handoff_block_must_be_final(self) -> None:
        errors = validate_template(template() + "\nUnexpected trailing text.\n")

        self.assertIn("template handoff block must be final content", errors)

    def test_template_requires_dispatch_sections(self) -> None:
        errors = validate_template(template().replace("### Mission", ""))
        self.assertIn(
            "template missing dispatch heading: ### Mission", errors
        )

    def test_template_requires_exact_dispatch_heading(self) -> None:
        errors = validate_template(
            template().replace("### Mission", "### Missionary")
        )
        self.assertIn(
            "template missing dispatch heading: ### Mission", errors
        )

    def test_template_requires_finding_severity(self) -> None:
        errors = validate_template(
            template().replace("finding_severity: none", "")
        )
        self.assertIn(
            "template missing handoff field: finding_severity:", errors
        )

    def test_template_requires_handoff_field_inside_block(self) -> None:
        errors = validate_template(
            template().replace(
                "finding_severity: none", "notes: finding_severity: none"
            )
        )
        self.assertIn(
            "template missing handoff field: finding_severity:", errors
        )

    def test_template_requires_exactly_one_handoff_block(self) -> None:
        duplicate = template() + """
<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>
"""
        errors = validate_template(duplicate)
        self.assertIn(
            "template requires exactly one <task_handoff> block, found 2",
            errors,
        )

    def test_cli_main_covers_success_error_and_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            valid = root / "valid.md"
            invalid = root / "invalid.md"
            valid.write_text(packet(), encoding="utf-8")
            invalid.write_text("# Invalid\n", encoding="utf-8")

            with (
                mock.patch("sys.argv", ["validator", str(valid)]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(validate_task_packet.main(), 0)
            with (
                mock.patch("sys.argv", ["validator", str(invalid)]),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(validate_task_packet.main(), 1)
            with (
                mock.patch("sys.argv", ["validator", str(root / "missing.md")]),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(validate_task_packet.main(), 2)


if __name__ == "__main__":
    unittest.main()
