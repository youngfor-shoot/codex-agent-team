# Example 05 — When not to use this

`agent-team` is a policy for *deciding* whether to use Agents at all. Its most
common correct answer is "don't." These are tasks the Skill should decline or
route back to a single Agent.

## Small, sequential, low-risk

```text
Use $agent-team to complete: rename the local variable in this one function
```

The task has one bounded outcome, is mainly sequential, has a low-risk mutation
boundary, and can be verified directly. The Skill should not suggest or invoke
Agent Team; it completes directly.

## Implicit trigger without delegation authority

```text
This migration touches three services; maybe we should have agents look at it.
```

An ordinary medium/large request without explicit invocation authorizes only a
recommendation. The Skill makes one concise, nonblocking recommendation and
continues within existing authority. It must not create an Agent, task, task
packet, or Automation.

## Speculative multi-agent work

```text
Use $agent-team to complete: write a blog post AND research competitors AND
refactor the build. (no further detail)
```

Never invent work merely to involve every backend. If the outcomes are not
independently bounded with concrete ownership, the controller asks for the
objective, write authority, target path, and acceptance criteria before
proceeding.

## Anything crossing a human gate

```text
Use $agent-team to complete: publish the release notes, deploy to prod, and
delete the old accounts.
```

Deletion, publication, deployment, purchases, account changes, and permission
expansion stay behind their normal user-authority boundaries. The Skill
preserves the gates and does not auto-execute them.

## Persistent-team requests without authority

```text
Use $agent-team with a persistent team to keep monitoring this project.
```

Persistence requires every gate (authority, future reuse, stable
responsibilities, role continuity, direct re-entry value, lifecycle). Without
explicit lifetime wording, only single-Agent or temporary is chosen.

## Evidence loop in the wrong place

```text
Use $agent-team to complete: keep retrying the flaky test until it passes.
```

The evidence loop requires frozen deterministic acceptance, a linked worktree,
and protected-path discipline. It never runs in a main checkout, a non-Git
directory, a protected path, or with state inside the worker's writable scope.
It never merges, deploys, or publishes.

## Obsidian or protected knowledge as writable target

```text
Use $agent-team to complete: clean up the vault and fix its links.
```

Obsidian vaults and protected knowledge stores are rejected automatically for
writable verification; write to the vault only when the user explicitly asks
and project governance permits the exact destination.
