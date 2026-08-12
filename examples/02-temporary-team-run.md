# Example 02 — Temporary team run

A complete temporary-team transcript: preview → delegation → handoffs →
integration → result. The canonical task packet is authoritative; the
Guidance / Context / Mission sections are a presentation layer over it.

## Request

```text
Use $agent-team with a temporary team to complete: add import validation to the
authentication migration and verify it.
```

## 1. Preview

Same topology decision as `01-preview-output.md` (temporary, phase-gated,
required native review). The controller emits the compact preview in
commentary before the first delegated call.

## 2. Task packet

See `in-progress-task-packet.md` for the canonical packet. Key fields:

- `execution_topology: temporary`
- `convergence_strategy: phase-gated`
- `independent_review_gate: required`
- `blocking_core_gaps: execution`

## 3. Delegation (Guidance / Context / Mission)

### Guidance

Implement input validation on `auth/migrate/import.py` so malformed records
fail fast with a clear user-facing error. Follow the repository's existing
patterns; do not touch the auth service public API or storage schema. Run the
focused unit tests before reporting.

### Context

Canonical objective: add import validation to the auth migration import path
and verify the change with the existing test suite. Current phase: execution.
Exact inputs: `auth/migrate/import.py`, the migration fixtures, and the test
suite under `tests/migrate/`. Constraints: scope is limited to the files above;
architecture and schema are settled. Upstream evidence: the controller's
intent ledger (original request, approved scope, forbidden assumptions).

### Mission

Bounded goal: one passing focused test suite plus the validation change.
Ownership: `auth/migrate/import.py` and its unit tests only. Deliverable: a
diff plus verification evidence. Acceptance: focused tests pass; no public API
or schema change. Next authorized step: return the handoff. Stop conditions:
any scope expansion, architecture change, or unresolved data-integrity
ambiguity.

## 4. Handoff

```text
<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>
```

## 5. Controller integration

1. Codex applied the child diff centrally and re-ran the focused suite.
2. The `required` review gate sent the diff, tests, and acceptance criteria to
   one backend (`native-verifier`), which returned no findings.
3. `finding_severity` recorded as `none`; review recorded as passed.
4. Whole-task checks passed; `whole_task_verified` set true only after every
   phase gate was verified.

## 6. Result

Reported in the evidence-based result format: outcome first, then the selected
topology/wakeup/convergence/gate/human gates with evidence, the review backend
that actually ran, and remaining limitations. See `completed-task-packet.md`
for the final packet.
