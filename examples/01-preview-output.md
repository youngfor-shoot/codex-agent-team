# Example 01 — Preview output

The exact read-only output of `$agent-team preview:` for a medium task. No
Agents, tasks, or Automations are created; nothing is mutated.

## Request

```text
Use $agent-team preview: add import validation to the authentication migration
and verify it.
```

## Preview

```text
Task size: medium
  - two independent bounded outcomes (import validation, migration verification)
  - crosses a data-integrity boundary (record parsing in a migration)

Recommended topology: temporary
  - one objective, bounded handoffs, no role state that must survive checkpoints

Recommended wakeup: none
  - one-shot request; ordinary progress messages need no Automation

Recommended convergence: phase-gated
  - implementation completes first, then a visual review of error wording

Recommended verification gate: required
  - residual risk: data-integrity in record parsing survives deterministic checks
  - review backend: native-verifier (default; no external integration)
  - review scope: parse and error handling of the import path

Human gates: none for the change itself; deployment stays behind its normal gate

Proposed workstreams:
  - Lane: implement import validation (luna_worker preferred; bounded, spec-determined)
  - Integration: Codex integrates and runs focused checks

Proposed execution boundary after authorization: auth/migrate/import.py, its unit tests, fixtures
Current preview mutation boundary: none

Deterministic verification:
  - python -m unittest discover -s tests/migrate -p "test_import*.py"

Execution budget: 4 iterations / 45 minutes / 900s command timeout
Stop conditions: acceptance assets changed, same failure twice, budget exhausted

Monitoring: none; ordinary in-task progress reports phase, verification, review
```

Machine-checkable form of the same request and decisions:

```json
{
  "id": "example-01-preview",
  "request": "Use $agent-team preview: add import validation to the authentication migration and verify it.",
  "authority": "explicit-invocation",
  "expect": {
    "topology": "temporary",
    "wakeup": "none",
    "convergence": "phase-gated",
    "independent_review_gate": "required",
    "review_trigger": "data-migration-overwrite-loss",
    "review_stop_condition": "One read-only pass and at most one focused recheck",
    "creates_agents": false,
    "creates_user_owned_tasks": false,
    "creates_automations": false,
    "side_effects": [],
    "human_gates": ["none"]
  }
}
```

## Notes

- `preview` must not spawn Agents, create user-owned tasks, write a task
  packet, start an Automation, or call any review backend.
- The backend line reports a *preferred* backend; the backend that actually ran
  is reported only after runtime evidence returns.
