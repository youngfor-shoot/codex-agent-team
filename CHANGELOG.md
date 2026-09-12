# Changelog

All notable changes to the `agent-team` Skill and this repository.

## [Unreleased]

### 0.5.5 reconciliation

- Canonical source now carries the accepted controller/executor boundary and
  execution-first route, plus the runtime policy, interface adapter, package
  fixtures, evaluation cases, and evidence reports.
- Synchronizers manage those package artifacts and preserve unowned runtime
  files such as local maintenance metadata.
- Native review availability and model usage are checked from the current host;
  unavailable required review remains pending.

### Added

- `skill/agent-team/references/verification-backends.md`: documents the
  zero-dependency `native-verifier` default backend and the optional
  AgentParliament adapter.
- `skill/agent-team/templates/task-packet.md`: canonical task-packet template,
  validated by `validate_task_packet.py --template`.
- `skill/agent-team/templates/task-handoff-schema.md`: `<task_handoff>` schema
  reference.
- `examples/in-progress-task-packet.md` and
  `examples/completed-task-packet.md`: validated worked examples, wired into CI.
- `examples/01-preview-output.md` through `05-when-not-to-use.md`: five worked
  scenario examples (preview, temporary run, evidence loop, persistent team,
  refusal cases).
- `--env-passthrough` on the evidence-loop `init` command: pass specific
  environment variables by name, frozen into the run contract.
- Cross-platform environment allowlist for `sanitized_environment()`: POSIX
  variables (`HOME`, `LANG`, `USER`, `TMPDIR`, etc.) join the existing Windows
  set.
- Read-only marking of the evidence-loop contract file after `init`.
- CI matrix now includes macOS (`macos-latest`) alongside Linux and Windows,
  plus a Python version matrix (3.10–3.13) and a cross-platform installer job.
- Static routing conformance suite (`tests/scenarios/`, `scripts/routing_rules.py`)
  encoding the cross-field routing invariants; runs in CI with no API calls.
- `references/task-type-routing.md`, `references/running-a-persistent-team.md`,
  `references/supervision-and-handoffs.md`, `references/completion-invariants.md`:
  procedural content moved out of SKILL.md.
- Active-time budget (`--active-budget-seconds`), review grace window
  (`--review-grace-minutes`), and `inspect` / `abort --acknowledge-unpinned`
  recovery paths in the evidence loop.
- `--version` flags and `contract_version` field on the task-packet contract.
- Backup retention (`-KeepBackups` / `--keep-backups`, default 5) and
  Uninstall / Restore modes in both sync helpers.
- Extended redaction patterns (AWS, GitHub, Slack, JWT, PEM).
- `evidence_loop.py list --root` to enumerate runs.
- Published JSON Schemas under `schemas/` for state and contract files.
- `README.zh-CN.md`; community files (CONTRIBUTING, CODE_OF_CONDUCT, issue/PR
  templates); Discussions enabled.
- CI quality gates: ruff, mypy --strict, CodeQL, Dependabot.
- Dependency-free Skill metadata validation, branch-coverage enforcement for
  routing/task-packet contracts, PSScriptAnalyzer, and regression tests for
  installer restore, schema compatibility, routing authority, and examples.

### Changed

- Independent review defaults to `native-verifier`; AgentParliament is an
  optional adapter, no longer the default review path.
- SKILL.md split from 511 to 151 lines; procedures moved to `references/`;
  version recorded as supported `metadata.version: 0.3.0` frontmatter.
- Evidence-loop enforcement measured in active check-execution seconds with an
  8x wall-clock backstop, instead of wall-clock-only deadlines.
- Verify drift exit code is now 2 (1 reserved for hard errors).
- Restore converges exactly to the selected backup's managed-file set while
  preserving unknown files; task packets end with one complete handoff block.
- Schema-version-1 additive fields remain optional with runtime defaults;
  routing fixtures derive authority and recurring wakeup from request text.
- Restore rejects path-traversing backup names and linked managed surfaces,
  rolls back failed commits, and preserves a verified recovery snapshot when
  rollback itself fails.
- Task-packet metadata and Final State fields are scoped independently;
  duplicate headings/fields and conflicting status values are rejected.
- Untracked symlink targets participate in source fingerprints, and POSIX
  verification no longer inherits a potentially stale parent `PWD`.

## [v0.1.0] - 2026-08-02

Initial public release of the `agent-team` Codex Skill with:

- Five-decision routing: topology, wakeup, convergence, verification, human
  gates.
- Native subagent and persistent-team coordination.
- Task-packet validation and the bounded evidence-loop helper.
- Windows synchronization helpers and pinned GitHub Actions.
