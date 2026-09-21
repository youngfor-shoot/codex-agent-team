# Runtime-aware implementation lanes

Use these lanes only when runtime provenance identifies the current agent as
`ROOT` and Agent Team has authority for temporary native
delegation and the controller has frozen the objective, ownership, interfaces,
constraints, and verification. The GPT-6 controller owns analysis, planning,
scope, integration, review selection, and final acceptance. Under standing
execution-first authorization, prefer a bounded executor when it can run
alongside useful controller analysis, validation, or acceptance.

A bounded parent assignment is `EXECUTOR`, including with `fork_turns: none`.
An executor does not use this matrix to select a model, change effort, dispatch
another agent, create a task or Automation, or invoke a helper or CLI fallback
to bypass that boundary. It never promotes itself to `ROOT`. It executes the
controller-selected assignment and returns evidence. An exact root grant
permits only named-scope subdelegation; the original controller remains `ROOT`.

Dispatch assigns only the named scope to that executor. ROOT may retain a
disjoint implementation scope and perform analysis, validation, and acceptance
alongside it. Keep one writer per file or shared external state. A small or
sequential task with no useful independent outcome can remain entirely local;
no lane selection or invented blocker is needed for that direct route.

## Preflight and authority

Inspect live tool declarations for callable agent types, supported models,
reasoning efforts, inheritance rules, and any pinned roles. They are
authoritative for the current host. Do not create filler work, user-owned
tasks, persistent tasks, or Automations to make a team look busy.

For a generic runtime-supported role, prefer `agent_type: bounded_executor`
when exposed, otherwise use `agent_type: default`. Both are policy-scoped,
not native-tool or operating-system isolation. Use
`fork_turns: none`, and the controller-selected supported `model` and
`reasoning_effort`. `fork_turns: none` is required for a bounded assignment.
Custom roles can pin their model and effort: do not override them. In the
current declared native roles, `luna_worker` and `terra_worker` pin maximum
effort; use their fixed contract or choose another explicitly supported lane.

Record `agent_type`, `requested_model`, `requested_effort`, and
`selection_reason` in Mission. After dispatch, record identity evidence
separately as `effective_model` and `effective_effort`; use `unknown` when the
runtime does not attest them. A request or accepted dispatch is not identity
evidence.

Keep dispatch parameters, returned task identity, observed runtime fields,
verification output, and their source locations in the same task's existing
Mission or evidence record. Do not fill unavailable model/effort fields from
configuration or worker self-identification, and do not infer a complete child
tree from a CLI trace that omits collaboration events. Claims about execution
attribution must remain partial when those receipts are missing.

On the configured 2026-09-05 host, `multi_agent=false` did not reliably remove
native collaboration tools; a direct invocation with that flag successfully
created a probe child. Disabling `code_mode_host` also broke local reads without
blocking that call. Do not use these flags as an isolation guarantee or weaken
the working tool setup to simulate one. If native-call prevention is a required
acceptance criterion, keep that criterion blocked until the host exposes and
verifies a working restriction. See
[reproduction evidence](../reports/runtime-boundary-repro.md).

If an otherwise useful action has no runtime-supported child lane, needs
controller-only authority, or has a hard dependency that prevents lawful child
execution, disclose that narrow constraint and keep the smallest necessary step
local. Do not turn that constraint into a reason to broaden authority or invent a fallback.

## Model and effort matrix

Choose the smallest supported lane that matches the bounded task. These are
selection expectations, not comparative quality, speed, cost, or benchmark
claims.

| Model | Default effort | Use for |
| --- | --- | --- |
| Spark (`gpt-5.3-codex-spark`) | low or medium | Tiny precise edits or fast, bounded read-only inspection. |
| Luna (`gpt-5.6-luna`) | medium or high | Routine implementation with an exact scope, settled interface, and observable acceptance. |
| Sol (`gpt-5.6-sol`) | medium or high | General bounded execution that needs more judgment than the routine lane. |
| Terra (`gpt-5.6-terra`) | high or xhigh | Cross-module correctness, difficult debugging, concurrency, persistence, or security-sensitive implementation. |
| Astra (`gpt-6-astra`) | high or xhigh | A separately justified difficult analysis or investigation that can run independently; the controller normally keeps this work. |

Request `max` only from evidence such as a named task risk or complexity, a
contract that requires it, or lower effort proving insufficient for the same
bounded outcome. Do not require every difficult task to fail at lower effort
first. Never infer `max` from task length, model name, or a custom role.

## Spark route and portable fallback

Check live tools on every dispatch. On 2026-09-05 the installed personal
`~/.codex/agents/spark-worker.toml` registered `spark_worker`, fixing only
`model = "gpt-5.3-codex-spark"`. A fresh native session discovered that role,
spawned it with explicit `reasoning_effort: low` and `fork_turns: none`, and
received its completed read-only file inspection. When the role is exposed,
select `agent_type: spark_worker`, omit a model override, and explicitly select
a supported effort (normally low or medium). The role does not pin effort or
change sandbox, approvals, or provider settings.

Existing sessions may retain an older tool declaration. A separate ephemeral
`codex exec --model gpt-5.3-codex-spark` read-only task also completed. For that
supported fallback, use explicit task cwd, effort, and an equal or stricter
sandbox, preserve hooks and rules, and prohibit recursive delegation. Never
create a user-owned desktop task solely to reach Spark. Native receipts did
not attest actual model/effort fields; record those as unknown rather than
using the worker's self-description as proof. Writable execution and hot
reload of existing sessions were not tested. See
[runtime evidence](../reports/controller-routing-2026-09-05.md).

For `ROOT`, native delegation is preferred. A CLI or custom-agent fallback requires an
explicitly supported route confirmed at dispatch time, the task's cwd, and the
same project, security, write-scope, and human-gate restrictions. It must not
create a user-owned task, bypass a child limitation, change global
configuration, weaken sandboxing, or imply a model identity that the runtime
did not return. Helpers and CLI routes receive the same `EXECUTOR` prefix and
non-recursive boundary. If those conditions are absent, retain the work locally
or use an explicitly available native lane and disclose the substitution.

## Escalation and acceptance

`ROOT` does not repeat an unchanged failed assignment. Inspect the evidence, correct
the specification, and make at most one evidence-based reassignment to a
supported lane. Unresolved work returns to the controller. Lane selection never
activates independent review; apply Agent Team's existing named residual-risk
gate after deterministic verification.

Examples: a precise mechanical edit can use Luna; a general bounded fix can
use Sol; a known cross-module correctness fix can use Terra; an independent
difficult investigation can use Astra. A required reviewer keeps a separate
scope; model diversity alone is not verification.
