# Example 04 — Persistent team setup

A persistent team is user-visible external state. Create it only after every
persistence gate passes with explicit authority.

## Gates check

- **Authority:** user said "use $agent-team with a persistent team to operate"
  — explicit invocation.
- **Future reuse:** at least two concrete future objectives will return to the
  same roles (e.g., monthly release prep and quarterly dependency audits).
- **Stable responsibilities:** each role contract remains useful after the
  current objective.
- **Role continuity:** roles need distinct history or state across user
  checkpoints; reloading canonical files alone is insufficient.
- **Direct re-entry value:** the user benefits from messaging the same role
  task again.
- **Lifecycle:** team name, persistent controller, exact write scopes, next
  checkpoint, completion condition, and review/retirement trigger are defined.

## Manifest

```text
[Team:release] Controller        — pins objectives, routes work, owns integration
[Team:release] Prep Worker       — owns release prep checklist and artifacts
[Team:release] Dependency Auditor — owns dependency audits and risk write-ups
```

- Only the Controller is pinned.
- Each role is initialized with the same Guidance / Context / Mission
  presentation: responsibility, write scope, evidence source, handoff
  contract, forbidden actions, completion boundary, controller task identity.
- Shared and canonical files stay under one controller writer; roles write only
  their explicitly exclusive artifacts or return handoffs.

## Operation

1. Route new objectives through the persistent controller.
2. The controller sends bounded prompts to role tasks and waits.
3. Read only recent, relevant task summaries; never ingest complete histories
   by default.
4. Do not poll unchanged tasks or claim background work without an active turn
   or Automation.
5. Retirement trigger reached → report it; the lifecycle change requires
   current user authority. Never auto-archive, delete, clone, unpin, or
   recreate tasks.

## When not to use this

- One objective, no future reuse → temporary team.
- Roles need no distinct history → temporary team.
- No explicit persistence authority → temporary or single Agent.
