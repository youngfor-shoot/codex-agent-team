# Task

- `contract_version`: `1`
- `task_id`: `auth-migration-import-validation`
- `status`: `completed`
- `execution_topology`: `temporary`
- `wakeup_mode`: `none`
- `convergence_strategy`: `phase-gated`
- `independent_review_gate`: `required`
- `independent_review_status`: `passed`
- `current_phase`: `final`
- `user_visible_objective_complete`: `true`
- `all_required_phases_verified`: `true`
- `whole_task_verified`: `true`
- `blocking_core_gaps`: `none`

## Intent Ledger

Original request: "Use $agent-team with a temporary team to complete: add
import validation to the authentication migration and verify it."

Canonical objective: add input validation to the auth migration import path so
malformed records fail fast, and verify the change with the existing test
suite.

Approved scope: `auth/migrate/import.py`, its unit tests, and the migration
fixtures. No changes to the auth service public API or storage schema.

Accepted scope delta: none.

## Routing Decision

Topology: `temporary` — one bounded outcome, no role state that must survive
future checkpoints.

Wakeup: `none` — this was a one-shot task with no recurring follow-up request.

Convergence: `phase-gated` — implementation completes first, then a visual
review of the error messages before final verification.

Review gate: `required` — the import path touches record parsing used by a
data migration, so an independent read-only review of the parse and error
handling was recorded for the residual data-integrity risk. Review passed with
`finding_severity: none` after one focused recheck.

## Phase Gates

- [x] Gate 1: freeze the objective, ownership, and acceptance.
- [x] Gate 2: implementation passes its focused unit tests.
- [x] Gate 3: controller approves the user-visible error wording.
- [x] Gate 4: whole-task regression suite passes.

## Objective

Deliver import validation for the auth migration path with clear user-facing
error messages, verified by the existing test suite.

## Completion Criteria

- [x] Whole-task verification passed.

## Integration Checklist

- [x] The user-visible objective is actually complete.

## Final State

- `status`: `completed`
- `completed_at`: `2026-08-11T18:00:00Z`
- `remaining_risks`: `none`

<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>
