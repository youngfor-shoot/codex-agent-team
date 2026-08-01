# Agent Team Source Repository Technical Specification

## Source-of-truth Contract

- Canonical source: `skill/agent-team/`
- Runtime copy: `~/.codex/skills/agent-team`
- Synchronization direction: canonical source to runtime copy only
- Repository-only helper: `scripts/sync-agent-team.ps1`

The Skill folder keeps the standard Codex layout:

```text
skill/agent-team/
  SKILL.md
  agents/openai.yaml
  references/*.md
  scripts/*.py
```

## Managed Surface

The synchronizer considers only:

- `SKILL.md`
- Markdown files below `references/`
- YAML files below `agents/`
- Python files below `scripts/`

It ignores bytecode, `__pycache__`, dotfiles, credentials, and every other file.

## Public Distribution

- `README.md` owns public setup, usage, and verification guidance.
- `LICENSE` contains the Apache-2.0 terms.
- `SECURITY.md` routes sensitive reports away from public issues.
- `.github/workflows/ci.yml` runs Python unit tests on Linux and Windows, then
  installs and verifies the managed Skill surface in a temporary Windows path.
- Public history and tracked files must not contain maintainer-specific absolute
  paths, credentials, caches, or scratch artifacts.

## Modes

### Verify

Enumerate both managed surfaces, compare relative paths and SHA-256 hashes, print
one concise drift report, and exit nonzero on any difference. Never write.

### Install

1. Compute the exact add/change/stale plan.
2. Back up every currently managed destination file to a timestamped sibling
   backup directory.
3. Copy canonical managed files to the runtime directory.
4. Remove only exact stale managed paths that appeared in the plan.
5. Re-run the same hash comparison and fail if equality was not reached.

PowerShell `ShouldProcess` protects the mutation boundary. Unknown and ignored
destination files remain untouched.

## Failure Behavior

- Reject a missing canonical Skill root.
- Reject source and destination resolving to the same path.
- Do not start installation if backup creation fails.
- Return a nonzero exit code on drift, copy failure, or post-install mismatch.
- Return zero after a successful install even when an earlier command in the
  caller reported drift.
- Print relative paths, never file contents.

## Evidence-loop Portability Boundary

- Detect an Obsidian vault by finding a `.obsidian` directory in the target or
  any ancestor and reject that target automatically.
- Require callers to pass every other sensitive root through
  `--protected-path`; freeze those paths into the run contract.
- Keep state, contracts, and controller harnesses outside the writable worktree,
  Git metadata, Obsidian vaults, and explicit protected paths.
- Keep verification commands dependency-free and execute them with
  `shell=False`; this is not an operating-system sandbox.

## Verification Commands

```powershell
python -m unittest discover -s skill/agent-team/scripts -p "test_*.py"
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
```
