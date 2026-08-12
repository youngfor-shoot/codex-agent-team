# Task

- `contract_version`: `1`
- `task_id`: `auth-migration-import-validation`
- `status`: `in_progress`
- `execution_topology`: `temporary`
- `wakeup_mode`: `heartbeat`
- `convergence_strategy`: `phase-gated`
- `independent_review_gate`: `not-required`
- `independent_review_status`: `not-applicable`
- `current_phase`: `execution`
- `user_visible_objective_complete`: `false`
- `all_required_phases_verified`: `false`
- `whole_task_verified`: `false`
- `blocking_core_gaps`: `execution`

## Intent Ledger

Original request: "Use $agent-team with a temporary team to complete: add
import validation to the authentication migration and verify it."

Canonical objective: add input validation to the auth migration import path so
malformed records fail fast, and verify the change with the existing test
suite.

Approved scope: `auth/migrate/import.py`, its unit tests, and the migration
fixtures. No changes to the auth service public API or storage schema.

## Routing Decision

Topology: `temporary` — one bounded outcome, no role state that must survive
future checkpoints.

Wakeup: `heartbeat` — the controller reports back to this task on each phase.

Convergence: `phase-gated` — implementation completes first, then a visual
review of the error messages before final verification.

Review gate: `not-required` — the change is a bounded, well-covered library
path with deterministic tests; no named residual risk remains after the
focused checks.

## Phase Gates

- [x] Gate 1: freeze the objective, ownership, and acceptance.
- [ ] Gate 2: implementation passes its focused unit tests.
- [ ] Gate 3: controller approves the user-visible error wording.
- [ ] Gate 4: whole-task regression suite passes.

## Objective

Deliver import validation for the auth migration path with clear user-facing
error messages, verified by the existing test suite.

## Completion Criteria

- [ ] Whole-task verification passed.

## Integration Checklist

- [ ] The user-visible objective is actually complete.

## Final State

- `status`: `in_progress`
- `completed_at`: `pending`
- `remaining_risks`: `visual approval`
