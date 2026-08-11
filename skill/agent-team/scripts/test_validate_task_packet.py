"""Tests for Agent Team task-packet completion invariants."""

from __future__ import annotations

import unittest

from validate_task_packet import validate_packet, validate_template


def packet(
    *,
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
"""


def template() -> str:
    return """# Task

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

<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>

## Integration Checklist
## Final State
"""


class TaskPacketValidatorTests(unittest.TestCase):
    def test_valid_in_progress_packet(self) -> None:
        self.assertEqual(validate_packet(packet(), require_complete=False), [])

    def test_rejects_automation_as_execution_topology(self) -> None:
        errors = validate_packet(
            packet(topology="automation"), require_complete=False
        )
        self.assertTrue(
            any("execution_topology must be one of" in error for error in errors)
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


if __name__ == "__main__":
    unittest.main()
