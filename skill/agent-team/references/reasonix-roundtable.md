# Reasonix Roundtable Contract (Optional Adapter)

Read this file only when the user explicitly requests Reasonix or
AgentParliament, or when the independent-review gate selects AgentParliament as
its single backend. AgentParliament is an optional adapter: the default review
backend is `native-verifier` (see `verification-backends.md`), and this
roundtable is never required for Agent Team to operate. AgentParliament is
read-only evidence, never the canonical writer or final authority.

## Runtime profile and discovery

The active profile contains only Reasonix-backed seats. CodeBuddy is not an
active backend or fallback; the seats are independent processes with different
personas, not different model providers.

Use a narrow discovery path because broad dynamic tool metadata expansion can
crash affected Codex Windows desktop builds:

1. If `mcp__agent_parliament__consensus` is already callable, invoke it.
2. Otherwise perform at most one narrow semantic tool search for
   `AgentParliament 并行让多个模型独立回答同一问题 对比共识与分歧
   consensus`, with one result. Do not search by internal tool name alone.
3. Never enumerate `ALL_TOOLS`, dump AgentParliament schemas, or run synonym
   searches.
4. If the exact tool remains unavailable, report the bounded blocker. Never
   imitate an MCP call through Shell.
5. Never pass an Obsidian vault or protected knowledge store as `project_dir`;
   omit it for text-only review or use only an approved project root.

## Bounded call

Default an authorized consultation to
`consensus(role="roundtable", synthesize=false)`. Evidence, skeptic, and
auditor seats run independently; Codex chairs and synthesizes without a fourth
Reasonix call. Supply the initial judgment, decision criteria, evidence paths,
one review question, and exact scope. Preserve material disagreement and
unsupported assumptions.

Run one opening round plus Codex synthesis. Add a round only for a different
named unresolved contradiction or failing check; never retry for a preferred
answer. The current MCP boundary caps each attempt at 180 seconds and the whole
failure chain at 270 seconds. These limits apply to one MCP call and do not
authorize another full pass.

Before `test_audit`, run its metadata-only preflight. More than two source files
or 100,000 known bytes must return `split_required` without starting a backend.
Run proposed source shards one at a time, pair only relevant tests, and
integrate centrally.

## Observability and cancellation

For a call expected to exceed 60 seconds, use one bounded temporary child only
when it can access the tool; monitor it from the controller. Report only
`queued`, `running`, `fallback`, `completed`, `timed_out`, `cancelled`, or
`blocked`, plus elapsed time, phase, and active attempt/total budget. Do not
invent hidden progress.

If the child cannot access the tool, call it from the controller and report
only start, elapsed time, and terminal result. Client cancellation must
terminate that call's child-process batch before returning. Long duration does
not authorize heartbeat, cron, persistence, repeated polling, or a retry.

After AgentParliament server code or configuration changes, treat existing
Codex task transports as stale. Start a new task or restart the app before the
next real call; do not kill an active server and expect hot reconnect.

Report completed seats, observed usage when returned, elapsed state, timeouts,
and quota failures. Never infer remaining Reasonix quota. Codex validates every
finding against source and requirements before accepting it.
