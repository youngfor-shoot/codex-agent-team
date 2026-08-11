# Codex Agent Team

[![CI](https://github.com/youngfor-shoot/codex-agent-team/actions/workflows/ci.yml/badge.svg)](https://github.com/youngfor-shoot/codex-agent-team/actions/workflows/ci.yml)

`agent-team` is a Codex Skill for choosing and coordinating the smallest safe
Agent setup for a task. It separates five decisions that are often mixed
together: topology, wakeups, convergence, verification, and human gates.

This repository ships a Skill and deterministic guardrail scripts, not a
standalone multi-agent runtime. Codex remains the controller and final
authority.

## What it does

- Selects one Agent, a temporary team, or a persistent team from explicit
  evidence and authority.
- Keeps recurring wakeups separate from team lifetime.
- Chooses a single pass, phase gates, or a bounded evidence loop.
- Requires deterministic checks for material work and adds independent review
  only for a named residual risk.
- Optionally routes specification-determined temporary implementation to a
  Luna worker and context-heavy or higher-risk implementation to a Terra
  worker while Codex retains architecture and acceptance.
- Preserves human gates around publication, deployment, deletion, payment,
  permissions, and other consequential actions.
- Validates task packets and can freeze an isolated Git-worktree evidence loop.

An implicit trigger may recommend collaboration, but it never creates Agents,
tasks, or Automations. Persistent user-visible tasks require explicit authority
and lifecycle evidence.

## Requirements

- Codex with Skills support
- Python 3.10 or newer for the bundled validators
- Git for the optional evidence-loop workflow
- Windows PowerShell 5.1 or newer only when using the synchronization helper

The Skill and Python helpers use the standard library only.

## Install

Clone the repository, then install the managed Skill surface:

```powershell
git clone https://github.com/youngfor-shoot/codex-agent-team.git
Set-Location codex-agent-team
& .\scripts\sync-agent-team.ps1 -Mode Install -Confirm:$false
& .\scripts\sync-worker-agents.ps1 -Mode Install -Confirm:$false
```

The helper installs to `~/.codex/skills/agent-team` by default, backs up the
currently managed files, preserves unknown files, and verifies hashes after the
copy. Pass `-Destination <path>` to use another runtime location.

The companion helper installs only `luna-worker.toml` and
`terra-worker.toml` to `~/.codex/agents`, backing up existing managed copies
and preserving every unrelated Agent file. These optional lanes require
runtime access to `gpt-5.6-luna` and `gpt-5.6-terra`; Agent Team remains usable
with explicitly reported native fallback roles when they are unavailable.

On another platform, copy `skill/agent-team/` to
`~/.codex/skills/agent-team/` with the platform's normal file tools.

## Use

Preview a topology without side effects:

```text
Use $agent-team preview: review this authentication migration plan
```

Authorize a temporary team for one objective:

```text
Use $agent-team with a temporary team to complete: add import validation and verify it
```

Let the Skill choose the smallest safe setup:

```text
Use $agent-team to complete: audit and repair this release workflow
```

Read [`skill/agent-team/SKILL.md`](skill/agent-team/SKILL.md) for the full
contract. Evidence-loop and optional roundtable details use progressive
disclosure under [`skill/agent-team/references/`](skill/agent-team/references/).

## Safety model

- The evidence loop runs only in a clean linked Git worktree, never a main
  checkout.
- Acceptance commands and assets are frozen outside worker ownership.
- Obsidian vaults are rejected automatically; callers must declare other
  sensitive roots with `--protected-path`.
- Shell and network launchers, inline interpreter evaluation, unbounded output,
  and secret-like output are blocked or redacted by the helper.
- The helper does not provide an operating-system sandbox, create Agents,
  merge, deploy, publish, or cross a human gate.

See [`SECURITY.md`](SECURITY.md) for private vulnerability reporting.

## Develop and verify

```powershell
python -m unittest discover -s skill/agent-team/scripts -p "test_*.py"
python -m unittest discover -s scripts -p "test_*.py"
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-worker-agents.ps1 -Mode Verify
```

The first command is portable. The structural validator requires a local Codex
installation, and the synchronization check verifies the current user-level
runtime copy. CI runs the portable tests on Linux and Windows and exercises a
fresh install/verify cycle on Windows.

## Repository layout

```text
skill/agent-team/          Canonical Codex Skill
agents/                    Canonical optional worker profiles
scripts/                   Repository installation and verification helpers
PRD.md                     Product requirements and acceptance criteria
Tech-Spec.md               Current technical contract
MEMORY.md                  Durable project decisions
```

## License

Apache-2.0. See [`LICENSE`](LICENSE).
