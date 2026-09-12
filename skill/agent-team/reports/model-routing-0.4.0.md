# Model Routing 0.4.0 Acceptance

Date: 2026-09-05
Scope: installed personal Skill instruction update; no release packaging,
global agent configuration, or evidence-loop implementation changes.

## Decision and evidence

Keep controller responsibility and select worker models from live tool
declarations. Preserve Luna/Terra fixed roles; use a supported default role
override for Astra. Local sources: live collaboration tool declarations,
implementation-lanes.md, supervision-and-handoffs.md, verification-backends.md.
Do not import provider infrastructure or comparative benchmark claims.

Native acceptance ran in a fresh read-only child alongside controller tests.
Requested: default / gpt-6-astra / high / fork_turns none. Tool returned a child
task identifier but no effective model attestation: effective_model unknown.
The child reported no blocking conflict and correctly applied the installed
rules to this maintenance task. Six counterfactuals were instruction checks,
not six additional model executions: local typo, independent mechanical work,
difficult independent investigation, explicitly required but unavailable Astra,
unavailable required native review, and an invalid pinned-role override.

Topology: temporary. Wakeup: none. Convergence: single-pass. Human gates: none.
One native acceptance pass; controller retains final acceptance. The child
implemented none of the reviewed files. All handoff fields were supplied.

## Deterministic checks

- PASS: frontmatter version and identity, existing native agents/openai.yaml
  interface fields, and Markdown file links.
- Existing regression suite: 92 tests, 90 passed, 1 skipped, 1 error.
  The error is FileNotFoundError for the pre-existing legacy fixture reference
  C:/Users/wxdev/.codex/tests/fixtures/v0.1.0/evidence-loop-contract.json in
  test_v010_verification_passed_fixture_uses_recorded_review_grace. No script
  was changed. Full-suite success is not claimed.
- Yao package-format validation was not used as a native Codex compatibility
  result: its inspected validator requires agents/interface.yaml, whereas
  this package retains the existing native agents/openai.yaml interface.

## Limits and rollback boundary

This validates current-host routing and instruction compatibility, not model
quality, speed, cost, effective backend identity, or every future host. Legacy
fixture availability remains missing evidence for that regression only.
Rollback is limited to the 0.4.0 instruction sections and new maintenance
documents; no external state or global model configuration was changed.
