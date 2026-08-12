# Completion Invariants

Read this reference before reporting whole-task completion and when running a
bounded evidence loop.

## Enforce phase and completion invariants

Keep `phase_verified` separate from `whole_task_verified`. A passing build,
test, screenshot, or child review proves only the phase named by its acceptance
contract.

Before reporting whole-task completion:

1. Re-read the latest explicit user instruction and reconcile the intent
   ledger.
2. Confirm the user-visible objective is complete.
3. Confirm every required phase is `verified`.
4. Confirm no core feature or human gate remains in blocking gaps.
5. Confirm every Completion Criteria and Integration Checklist item is checked.
6. Confirm Final State is `completed`, the timestamp is final, and remaining
   risks are `none`.
7. When available, run
   `scripts/validate_task_packet.py <absolute-task-packet> --require-complete`.

Never set `whole_task_verified=true` and
`user_visible_objective_complete=false`. Treat that state as an error, not a
partial success.

## Run a bounded evidence loop

When `evidence-loop` is selected, read and follow `evidence-loop.md`; do not
reconstruct its contract from memory. The controller owns every transition, and
completion still requires the reference's distinct independent review over the
deterministically verified source.

## Return an evidence-based result

Report:

- the outcome first;
- selected topology, wakeup, convergence, verification gate, and human gates
  with their evidence;
- the canonical objective and any accepted scope delta;
- what Codex changed or decided;
- persistent task titles and re-entry path when a persistent team was created;
- heartbeat or cron identity and stop condition when Automation was created;
- the review question, backend, and pass actually used, or why review was
  `not-required`;
- which review backend and Reasonix seats actually ran, when any;
- which findings Codex accepted or rejected;
- phase status, deterministic verification results, and whole-task invariant
  result;
- remaining limitations or blockers.

Keep orchestration details brief unless they materially affect confidence or
risk.
