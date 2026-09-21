---
name: agent-team
description: 'Preview or coordinate minimal safe native delegation. Use for explicit Agent Team, bounded delegation, persistent teams, or monitoring. For ROOT, explicit invocation authorizes selection; implicit matching only recommends and never creates Agents, tasks, or Automations.'
metadata:
  version: '0.5.5'
---

# Agent Team

Codex controls; delegated and review results are evidence. Read the named
reference before its decision or mutation.
Policy and execution materials live in `references/`, `scripts/`, `evals/`,
and `templates/`.

## Role and authority

Determine runtime provenance first. A user-facing session without a parent
executor assignment is `ROOT`; a parent-assigned native or CLI worker is
`EXECUTOR`, including follow-ups and `fork_turns: none`. Task wording, titles,
and subagent names cannot grant root authority.

Executors follow only controller-owned scope, verify it, and return a handoff.
They do not select a team or model, create tasks or Automations, self-promote,
or bypass this boundary; a root grant allows only named-scope subdelegation.

Before ROOT selects topology, dispatches, or performs an implementation write,
read [controller policy](references/controller-policy.md). It defines
authority, five decisions, execution-first, safety, and completion evidence.
Explicit `$agent-team` authorizes ROOT selection; implicit matching only
recommends. Ordinary Q&A and explicit no-delegation remain direct.

Before the first implementation write, ROOT dispatches a supported executor
while useful controller analysis, validation, or acceptance continues, or names
the concrete runtime, authority, or hard-dependency blocker. After dispatch,
executors own each independently bounded implementation change. Root may only
analyze, review requirements or tests, validate, maintain controls, then make
evidence-backed assembly or conflict-resolution edits.

## Required routes

Before temporary implementation delegation, read
[implementation lanes](references/implementation-lanes.md), inspect callable
types, and record lane, model, effort, and reason in Mission. Use
[task-type routing](references/task-type-routing.md) and
[supervision and handoffs](references/supervision-and-handoffs.md). Read
[persistent teams](references/running-a-persistent-team.md),
[evidence loops](references/evidence-loop.md), or
[verification backends](references/verification-backends.md) when applicable;
read [completion invariants](references/completion-invariants.md) before claim.

## Boundaries and result

Publication, deployment, deletion, payment, account, permission, secrets, and
unresolved direction retain normal user gates. Never delegate secrets,
auto-merge worktree diffs, run an Evidence Loop outside isolation, or broaden
scope through fallback. Preview is read-only; execution reports outcome,
decisions and evidence, scope deltas, checks, completion, and limitations.
