---
name: agent-team
description: 'Preview or coordinate minimal safe native delegation. Use for explicit Agent Team, bounded delegation, persistent teams, or monitoring. For ROOT, explicit invocation authorizes selection; implicit matching only recommends and never creates Agents, tasks, or Automations.'
metadata:
  version: '0.5.7'
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

Direct execution is valid for small or sequential work when no independently
bounded outcome provides concrete benefit. ROOT may implement and verify that
route without inventing a blocker, task packet, preview, or reviewer.

Before ROOT selects collaboration or dispatches, read
[controller policy](references/controller-policy.md). Explicit `$agent-team`
authorizes selection; implicit matching only recommends. Delegate when an
independent outcome provides concrete benefit alongside useful controller work.
Keep one writer per file; ROOT may retain disjoint implementation ownership.
Ordinary Q&A and explicit no-delegation remain direct.

## Dynamic model routing

Default to GPT-6.1 Terra (`gpt-6.1-terra`). Escalate to GPT-6.1 Sol
(`gpt-6.1-sol`) for competing explanations, cross-module causal reasoning,
architecture/concurrency/state/integrity/complex compatibility, conflicting
requirements, difficult reasoning, two evidence-distinct failed repairs, or
new evidence invalidating the plan. Resolve external blockers first. Length
and file count alone do not justify escalation. Follow an explicit user model
choice. Read [dynamic model routing](references/dynamic-model-routing.md) when
selecting a model, escalating, or handing work back. Return routine work to
Terra when handoff is worthwhile; never claim a switch without runtime evidence.
Model preference does not grant delegation authority or change the active
session model by itself. Do not narrate routine routing decisions.

## Required routes

Before temporary implementation delegation, read
[implementation lanes](references/implementation-lanes.md), inspect callable
types, and record lane, model, effort, and reason in Mission. Use
[task-type routing](references/task-type-routing.md) when needed and
[supervision and handoffs](references/supervision-and-handoffs.md) for delegated
results. Independent review requires a named residual risk or explicit request
under controller policy, after deterministic checks. Read
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
