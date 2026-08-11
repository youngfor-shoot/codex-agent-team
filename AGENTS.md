# Codex Agent Team Repository Instructions

## Purpose

This repository is the canonical source for the `agent-team` Codex Skill.
The installed copy at `~/.codex/skills/agent-team` is a runtime artifact, not a
second source of truth.

## Scope

- Keep the Skill under `skill/agent-team/`.
- Keep versioned companion custom-agent profiles under `agents/`.
- Keep repository-only installation and verification helpers under `scripts/`.
- Keep canonical task-packet template and `<task_handoff>` schema under
  `skill/agent-team/templates/`.
- Keep project decisions in `MEMORY.md` and current behavior in `Tech-Spec.md`.
- Keep public setup and usage guidance in the repository-root `README.md`, not
  inside the Skill folder.
- Do not store credentials, machine secrets, caches, bytecode, or generated test
  artifacts.

## Change Rules

- Make all durable Skill edits in `skill/agent-team/` first.
- Use `scripts/sync-agent-team.ps1` (Windows) or `scripts/sync-agent-team.py`
  (cross-platform) to compare, install, or verify the runtime copy. Never
  hand-maintain both trees.
- Preserve concise progressive disclosure: core routing belongs in `SKILL.md`;
  detailed variants belong in one-level `references/` files; canonical
  templates live in `templates/`.
- Do not add independent review as a default phase. It remains a named
  residual-risk gate.
- Keep changes focused and avoid new dependencies when the Python standard
  library or PowerShell can cover the need.

## Verification

Run from the repository root:

```powershell
python -m unittest discover -s skill/agent-team/scripts -p "test_*.py"
python -m unittest discover -s scripts -p "test_*.py"
python skill/agent-team/scripts/validate_task_packet.py skill/agent-team/templates/task-packet.md --template
python skill/agent-team/scripts/validate_task_packet.py examples/in-progress-task-packet.md
python skill/agent-team/scripts/validate_task_packet.py examples/completed-task-packet.md --require-complete
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-worker-agents.ps1 -Mode Verify
```

On POSIX hosts, replace the two PowerShell verify commands with
`python scripts/sync-agent-team.py --mode Verify`. Use Install mode only when
the repository version is ready to replace the managed runtime files. The
helpers must not read or copy credentials.

## Git

- Preserve unrelated work.
- Do not commit generated `__pycache__`, `.pyc`, or local scratch files.
- Commit messages and repository documentation use English.
- Do not claim adoption, usage, or compatibility without public evidence.
