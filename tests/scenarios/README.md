# Routing Conformance Suite

Two layers verify that `agent-team` routing rules produce the correct
decisions.

## Static layer (CI, no API calls)

- Fixtures: `tests/scenarios/fixtures.py` — each scenario declares a `request`,
  an `authority`, and an `expect` block.
- Rules: `scripts/routing_rules.py` encodes the cross-field invariants from
  `SKILL.md` as executable checks:

  - an `evidence-loop` convergence requires `independent_review_gate=required`;
  - a required review gate needs a named `review_trigger` and a
    `review_stop_condition`;
  - `persistent` topology requires every persistence gate plus lifecycle
    fields, and explicit `explicit-invocation` / `auto-lifetime` authority;
  - `temporary` topology never creates user-owned tasks;
  - the documented `$agent-team preview:` directive is read-only: it declares
    `creates_agents`, `creates_user_owned_tasks`, and `creates_automations` as
    `false`, with `side_effects: []`; planned topology and wakeup remain
    separate from those action declarations;
  - `heartbeat` / `cron` wakeups require a stop condition;
  - documented English (`daily`, `every week`, `keep monitoring`) and Chinese
    (`每天`, `每周`, `持续监控`) recurring wording requires a wakeup;
  - human gates must be from the allowed set.

- Test: `scripts/test_routing_rules.py` validates every fixture's `expect`
  block; CI runs it on every PR.
- Adding a scenario is the standard way to lock in a new routing behavior
  before refactoring `SKILL.md`.

## Model layer (manual / nightly, not in CI)

For each fixture, start a fresh Codex session with the Skill loaded, feed the
`request`, parse the emitted preview, diff it against `expect`, and report an
accuracy score. This layer is intentionally not in CI: it needs a live Codex
runtime and is a quality measurement, not a gate. Static checks validate the
fixture contract only; they cannot prove a live model emitted the declared
preview or avoided runtime side effects.
