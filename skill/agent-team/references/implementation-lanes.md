# Optional implementation lanes

Use these lanes only after Agent Team selects temporary native delegation and
the controller has frozen the objective, ownership, interfaces, constraints,
and verification. The controller keeps architecture, integration, review
selection, and final acceptance.

## Preflight

Inspect callable native agent types before assignment. The optional preferred
types are `luna_worker` and `terra_worker`. Always spawn either custom type with
`fork_turns: none` and record the selected `agent_type` in Mission.

If the preferred type is unavailable, report the unavailable lane and select
an explicitly identified available native implementation type under the same
bounded contract. Never claim that Luna or Terra ran without runtime evidence.

## Select Luna

Prefer `luna_worker` when the specification largely determines the result:

- objective and acceptance are observable;
- file or module ownership is exact;
- interfaces and compatibility constraints are settled;
- implementation is mechanical, repeatable, or narrowly bounded;
- deterministic verification is available.

Typical work includes wiring, CRUD, routine tests, mechanical refactors, and
bounded bug fixes. Work volume alone does not make a task complex.

## Select Terra

Use `terra_worker` when correctness depends on substantial context or judgment:

- concurrency or a non-trivial algorithm;
- security-sensitive or data-integrity paths;
- cross-module or persistence contracts;
- difficult debugging with multiple plausible causes;
- broad refactors or a wider technical blast radius.

Task size alone does not select Terra. Neither lane may change the parent
objective, replace settled architecture, or broaden ownership.

## Escalate once

Do not repeat an unchanged failed Luna assignment. Inspect the evidence,
correct the specification, and escalate one corrected attempt to Terra only
when the failure shows the original task was misclassified. Otherwise keep the
fix with Luna or return the unresolved decision to the controller.

Lane selection never activates independent review. Apply Agent Team's existing
named residual-risk gate after deterministic verification.
