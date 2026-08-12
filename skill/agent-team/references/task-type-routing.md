# Task-Type Routing

Read this reference after selecting the five decisions, when the controller
routes work by task type.

## Build, change, or fix software

1. Select `phase-gated` for unresolved visual/product judgment; otherwise
   select `single-pass` or `evidence-loop` from the deterministic acceptance
   and isolation conditions in `SKILL.md`.
2. Let Codex own integration and canonical source changes. When temporary
   delegation is useful, route bounded implementation through the optional
   Luna/Terra contract in `implementation-lanes.md`.
3. Run focused deterministic checks and controller-owned whole-task checks.
4. When the review gate is `required`, send its bounded question and scope to
   exactly one backend: `native-verifier` by default, or one optional adapter
   such as AgentParliament, not both for the same risk.
5. Validate each finding, fix only confirmed issues, and normally close fixes
   through regression checks. Use at most one focused independent recheck.
6. Do not use `verify_implementation` in a Reasonix-only deployment; Reasonix
   has no approved unattended writable mode. Run deterministic checks through
   Codex or a native isolated worker instead.

## Review existing work

1. Preserve a read-only boundary unless the user also asks for fixes.
2. Use `native-verifier` by default. Use the Reasonix roundtable only when
   business context, call chains, or an independent challenge materially
   improves the review and the user requested it or configuration names it.
3. Put the diff, relevant sources, tests, and acceptance criteria into the
   review question; use `test_audit` only as an additional bounded atomic
   audit when deterministic coverage mapping is required.
4. Let Codex reproduce or source-check findings before reporting them.
5. Do not mutate files during a review-only request.

## Make a technical or architectural decision

1. Let Codex form an initial hypothesis and explicit decision criteria.
2. Use `native-verifier` by default. Use the Reasonix roundtable only for an
   explicit user review request, configuration-named use, or a named
   high-impact uncertainty that the available evidence cannot settle directly.
3. Preserve minority objections and unresolved evidence gaps.
4. Use the roundtable only when multiple bounded perspectives justify its
   added cost.
5. Let Codex resolve disagreement and record the final tradeoff.

## Analyze content or Obsidian material

1. Default all review work to read-only.
2. Use `phase-gated` when identity, publication, or factual verification needs
   a human or evidence checkpoint.
3. Use `native-verifier` by default. Use the Reasonix roundtable only when a
   named factual or reasoning blind spot remains, the user requested it or
   configuration names it, and the added perspectives justify the cost.
4. Let Codex synthesize the final recommendation in the user's voice.
5. Never use `verify_implementation` against an Obsidian vault.
6. Write to the vault only when the user explicitly asks and project
   governance permits the exact destination.
