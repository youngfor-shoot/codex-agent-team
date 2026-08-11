# Verification Backends

The independent-review gate records exactly one backend. This reference
documents the default backend and the optional adapters. Agent Team works with
no configuration beyond Codex itself; adapters are additive, never required.

## Default: native-verifier

`native-verifier` is the default backend when the review gate is `required`
and no adapter was explicitly configured or requested. It has zero external
dependencies:

- The reviewer is a separate Codex context that has not implemented the
  reviewed surface.
- The reviewer receives the one recorded review question, the exact scope, the
  residual risk, the diff or artifact, relevant sources, tests, and acceptance
  criteria.
- The reviewer returns human-readable findings labelled `BLOCKER`, `MAJOR`, or
  `MINOR` and a `finding_severity` handoff value; the controller remains the
  acceptance authority.
- Everything runs inside Codex's existing read-only tools; no MCP server,
  model quota, or external service is involved.

Because the default backend is available on every Codex installation, a
`required` review gate never depends on an unavailable integration.

## Optional adapter: AgentParliament (Reasonix seats)

AgentParliament is an optional adapter for bounded research, review, or
decision challenge. It is selected only when the user explicitly requests
Reasonix or AgentParliament, or when project configuration names it as the
review backend. Read `reasonix-roundtable.md` before its first call.

When AgentParliament is unavailable, report the bounded blocker and fall back
to `native-verifier` for the same named residual risk; never imitate an MCP
call through a shell command, and never silently broaden scope.

## Recording the backend

- Record the preferred backend as configuration before the run.
- Record the backend that actually ran only after runtime evidence returns.
- The evidence loop stores `reviewer_backend` and `artifact_hash` as controller
  assertions, not cryptographic identity proof.
- A second backend or another full review requires a different named
  unresolved risk or failing check.
