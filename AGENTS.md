# Codex Agent Team Repository Instructions

## Purpose

This repository is the canonical source for the `agent-team` Codex Skill.
The installed copy at `~/.codex/skills/agent-team` is a runtime artifact, not a
second source of truth.

## Scope

- Keep the Skill under `skill/agent-team/`.
- Keep versioned companion custom-agent profiles under `agents/`.
- Keep repository-only installation and verification helpers under `scripts/`.
- Keep project decisions in `MEMORY.md` and current behavior in `Tech-Spec.md`.
- Keep public setup and usage guidance in the repository-root `README.md`, not
  inside the Skill folder.
- Do not store credentials, machine secrets, caches, bytecode, or generated test
  artifacts.

## Change Rules

- Make all durable Skill edits in `skill/agent-team/` first.
- Use `scripts/sync-agent-team.ps1` to compare, install, or verify the runtime
  copy. Never hand-maintain both trees.
- Preserve concise progressive disclosure: core routing belongs in `SKILL.md`;
  detailed variants belong in one-level `references/` files.
- Do not add independent review as a default phase. It remains a named
  residual-risk gate.
- Keep changes focused and avoid new dependencies when the Python standard
  library or PowerShell can cover the need.

## Verification

Run from the repository root:

```powershell
python -m unittest discover -s skill/agent-team/scripts -p "test_*.py"
python -m unittest discover -s scripts -p "test_*.py"
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-worker-agents.ps1 -Mode Verify
```

Use `-Mode Install` only when the repository version is ready to replace the
managed runtime files. The script must not read or copy credentials.

## Git

- Preserve unrelated work.
- Do not commit generated `__pycache__`, `.pyc`, or local scratch files.
- Commit messages and repository documentation use English.
- Do not claim adoption, usage, or compatibility without public evidence.
