# Changelog

All notable changes to the `agent-team` Skill and this repository.

## [Unreleased]

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
- `--env-passthrough` on the evidence-loop `init` command: pass specific
  environment variables by name, frozen into the run contract.
- Cross-platform environment allowlist for `sanitized_environment()`: POSIX
  variables (`HOME`, `LANG`, `USER`, `TMPDIR`, etc.) join the existing Windows
  set.
- Read-only marking of the evidence-loop contract file after `init`.
- CI matrix now includes macOS (`macos-latest`) alongside Linux and Windows.

### Changed

- Independent review defaults to `native-verifier`; AgentParliament is an
  optional adapter, no longer the default review path.
- SKILL.md frontmatter now carries `version: 0.2.0`.

## [v0.1.0] - 2026-08-02

Initial public release of the `agent-team` Codex Skill with:

- Five-decision routing: topology, wakeup, convergence, verification, human
  gates.
- Native subagent and persistent-team coordination.
- Task-packet validation and the bounded evidence-loop helper.
- Windows synchronization helpers and pinned GitHub Actions.
