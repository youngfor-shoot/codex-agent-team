# Controller-led routing acceptance

This is the instruction worker's local-check record. The controller's later
native Spark acceptance and final limitations are recorded in
[controller-routing-2026-09-05.md](controller-routing-2026-09-05.md), which
supersedes the pending runtime gaps below.

## Accepted instruction changes

- The GPT-6 controller owns analysis, planning, scope, integration, and final
  acceptance. Execution is preferred for one bounded executor when useful
  controller analysis, validation, or acceptance continues in parallel; only
  narrow runtime, authority, or hard-dependency constraints retain work local.
- Generic native execution uses a live-supported `default` role with
  `fork_turns: none` and a selected model and effort. Pinned `luna_worker` and
  `terra_worker` roles retain their fixed maximum-effort contracts.
- The routing matrix names Spark, Luna, Sol, Terra, and Astra model slugs
  without quality, price, speed, or benchmark claims. `max` requires named
  task risk or complexity, a contract requirement, or evidence that lower
  effort was insufficient for the same bounded outcome.
- Spark's only recorded 2026-09-05 evidence is a read-only task-cwd CLI probe;
  native role hot reload, writable Spark execution, and pinned-role overrides
  remain unaccepted.
- A fallback needs a current, explicit supported route and preserves task cwd,
  security, write scope, and gates. It cannot create user-owned tasks,
  Automations, or widened authority.

## Local checks

- `trigger_eval.py` with the focused fixture and semantic configuration: pass
  (4 trigger, 3 non-trigger, 3 near-neighbor cases; 0 false positives and 0
  false negatives). This is a local heuristic route check, not a model or
  runtime acceptance test.
- `validate_skill.py`: failed because the pre-existing package has
  `agents/openai.yaml` while the generic validator requires
  `agents/interface.yaml`. No unowned compatibility file was added.
- The existing resource-boundary check estimates 2,210 tokens against its
  generic 1,000-token entry threshold. This personal orchestration Skill keeps
  its routing contract and referenced safety boundaries; no unrelated
  shortening was made for that incompatible generic threshold.
- `validate_task_packet.py --help`: confirmed the available packet validator;
  no task packet changed in this documentation-only upgrade.

## Remaining evidence gap

These checks do not accept a live native Spark route, a writable CLI fallback,
or any model identity beyond runtime attestation. Full regression and a fresh
native acceptance remain with the controller task.
