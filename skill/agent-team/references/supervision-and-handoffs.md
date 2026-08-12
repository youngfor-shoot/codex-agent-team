# Supervision and Handoffs

Read this reference during execution, after a delegation or review has
returned. Codex remains responsible for classification, planning, mutation,
conflict resolution, correction, and final acceptance.

## Establish the controller contract

Before delegation:

1. Read applicable project instructions and persistent project context.
2. Inspect which native Codex subagent, thread, and optional adapter tools are
   actually callable. Native team selection does not require AgentParliament.
   The default `native-verifier` backend is always available. If the user
   explicitly requests Reasonix or AgentParliament and those tools are missing,
   report that bounded blocker and fall back to `native-verifier` for the same
   named residual risk; never imitate an MCP call with a shell command.
3. Create an intent ledger with the original request, explicit overrides,
   canonical objective, approved scope, pending decisions, forbidden
   assumptions, and evidence status.
4. State whole-task completion criteria, current phase, constraints, human
   gates, and allowed mutation boundary.
5. Inspect enough local evidence to avoid delegating a vague problem.
6. Decide whether multi-agent work adds independent evidence or verification.
7. Continue with Codex alone when the task is small, sequential, or cheaper to
   complete directly.

Before assigning temporary implementation work, read
`implementation-lanes.md`, inspect the callable custom types, and record the
selected implementation `agent_type` in Mission.

Never invent work merely to involve every backend.

When auditing prior tasks, distinguish `confirmed`, `contradicted`, `unknown`,
and `confirmed_by_user_artifact`. Absence from a thread read, summary, or
snapshot is not evidence that the user never gave an instruction. Preserve
contradictory observations and prefer the latest directly confirmed user
evidence.

## Run a temporary team

1. Create a task-scoped control packet when project rules require one.
2. Spawn the smallest set of native child Agents with one bounded outcome each.
   For implementation workstreams, select the optional Luna/Terra lane from
   `implementation-lanes.md` and use `fork_turns: none`.
3. Present every child assignment in three sections backed by the canonical
   task packet:
   - **Guidance:** execution method, constraints, quality standard, and
     applicable Skill scope.
   - **Context:** canonical objective, current phase, exact inputs, upstream
     evidence, user preferences, and dependencies.
   - **Mission:** bounded goal, ownership, deliverable, acceptance, next
     authorized step, and stop conditions.
   Treat these headings as a presentation layer, not a second state model; the
   task packet wins if wording conflicts or becomes stale.
4. Keep one writer per file or shared external state.
5. Route changed constraints through the controller.
6. Require handoffs to report goal alignment, scope delta, new assumptions,
   evidence, and the next authorized step. Treat missing fields as
   `verification_pending`.
7. Collect structured handoffs and integrate centrally. Add a verifier only
   when the independent-review gate is `required`.
8. Let temporary child threads end with the parent task. Do not convert them
   into user-owned tasks after the fact.

## Run a review backend

Select exactly one backend for a `required` review gate: `native-verifier` by
default, or an optional adapter (AgentParliament) when the user explicitly
requested it or configuration names it. Read `verification-backends.md` before
choosing; when AgentParliament is selected, read `reasonix-roundtable.md`, ask
the one recorded review question, and keep Codex as chair and final authority.
Native temporary workstreams still route through `orchestrate-parallel-work`.

## Enforce the supervision loop

For each delegated result:

1. Check that it answered the bounded question.
2. Compare its `goal_alignment` with the intent ledger and current phase.
3. Reject or escalate every non-`none` scope delta or new assumption before
   integration.
4. Compare it with project source of truth and acceptance criteria.
5. Reject unsupported, conflicting, or out-of-scope conclusions.
6. Apply changes centrally through Codex.
7. Run deterministic verification where available.
8. If review was required, request at most one focused recheck while a concrete
   confirmed finding or failing check remains.

When review is required, the reviewer must not have implemented the reviewed
surface. Do not report completion while required verification is pending or
failed.

## Finding severity

Require an independent reviewer to label every candidate finding in the
human-readable response:

- `BLOCKER`: if accepted, safe or correct delivery is impossible or a required
  gate remains incomplete; resolve it or keep the task blocked.
- `MAJOR`: if accepted, correctness, usability, or a contract is materially
  affected; resolve it before completion unless the user explicitly changes
  scope or acceptance without bypassing a safety or authority invariant.
- `MINOR`: a non-blocking improvement; it does not automatically expand scope
  or consume the focused-recheck budget.

Set `finding_severity` in the fixed handoff block to the highest reported
severity. Use `none` for executors and reviews with no findings. Validate each
finding against primary evidence and acceptance criteria; accept, reject,
upgrade, or downgrade it before integration. Finding severity never activates
independent review and never replaces the residual-risk gate.

For every delegated handoff, require normal human-readable Markdown first and
then exactly one fixed `<task_handoff>` block using the project task-packet
schema, including `finding_severity`. Every field must be present, empty values
are `none`, the block is not inside a code fence, and no text follows
`</task_handoff>`.
