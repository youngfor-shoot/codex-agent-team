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
agents/
  luna-worker.toml
  terra-worker.toml
```

## Optional Implementation Lanes

Agent Team remains the sole owner of topology, scope, architecture,
integration, verification, review selection, and final acceptance. The two
companion roles apply only to bounded native subagent implementation inside a
temporary workflow:

- `luna_worker` is the preferred lane when objective, ownership, interfaces,
  constraints, and verification are explicit and the result is largely
  determined by the specification.
- `terra_worker` is selected when correctness depends on substantial
  repository context, non-trivial implementation judgment, concurrency,
  security-sensitive paths, cross-module contracts, difficult debugging, or a
  wider blast radius. Task size alone does not select Terra.

Every spawn uses `fork_turns: none` and the existing Guidance / Context /
Mission assignment. Record the selected `agent_type` in Mission. A Luna result
may escalate once to Terra only after the controller inspects the failure,
corrects the specification, and records why the original route was wrong.

At task creation, inspect callable native agent types. If a preferred companion
role is unavailable, report that routing limitation and use an explicitly
identified available native implementation role under the same ownership and
verification contract. Never claim that Luna or Terra ran without runtime
evidence.

Companion roles are not persistent-team identities and never activate an
independent review. The existing named residual-risk gate remains unchanged.

## Dispatch And Review-Finding Contract

Present every delegated assignment with three human-readable sections backed
by the existing canonical child fields:

- `Guidance`: execution method, constraints, quality standard, and applicable
  Skill scope;
- `Context`: canonical objective, current phase, exact inputs, upstream
  evidence, user preferences, and dependencies;
- `Mission`: bounded goal, ownership, deliverable, acceptance, next authorized
  step, and stop conditions.

These headings are a presentation layer, not a second state model. The task
packet remains authoritative when wording conflicts or becomes stale.

In an independent review, label each candidate finding `BLOCKER`, `MAJOR`, or
`MINOR` in the human-readable response and set `finding_severity` in the fixed
handoff block to the highest reported severity. Use `none` for executors and
reviews with no findings. The controller validates every finding and may
accept, reject, or reclassify it before integration:

- `BLOCKER`: an accepted finding makes safe or correct delivery impossible or
  leaves a required gate incomplete; resolve it or keep the task blocked.
- `MAJOR`: an accepted finding materially affects correctness, usability, or a
  contract; resolve it before completion unless the user explicitly changes
  scope or acceptance without bypassing a safety or authority invariant.
- `MINOR`: a non-blocking improvement; record it without automatically
  expanding scope or consuming the focused-recheck budget.

Finding severity does not activate independent review and does not replace the
risk-matched review gate.

## Managed Surface

The synchronizer considers only:

- `SKILL.md`
- Markdown files below `references/`
- YAML files below `agents/`
- Python files below `scripts/`

It ignores bytecode, `__pycache__`, dotfiles, credentials, and every other file.

The separate `scripts/sync-worker-agents.ps1` helper manages exactly:

- canonical `agents/luna-worker.toml` to `~/.codex/agents/luna-worker.toml`;
- canonical `agents/terra-worker.toml` to `~/.codex/agents/terra-worker.toml`.

It supports the same `Verify` and explicit `Install` modes, creates a backup of
existing managed destinations before replacement, compares normalized SHA-256
hashes, and leaves every unrelated global Agent file untouched.

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
python -m unittest discover -s scripts -p "test_*.py"
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-worker-agents.ps1 -Mode Verify
```
