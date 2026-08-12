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
  only for a named residual risk, using a zero-dependency native verifier by
  default with an optional AgentParliament adapter.
- Optionally routes specification-determined temporary implementation to a
  Luna worker and context-heavy or higher-risk implementation to a Terra
  worker while Codex retains architecture and acceptance.
- Preserves human gates around publication, deployment, deletion, payment,
  permissions, and other consequential actions.
- Validates task packets and can freeze an isolated Git-worktree evidence loop.

An implicit trigger may recommend collaboration, but it never creates Agents,
tasks, or Automations. Persistent user-visible tasks require explicit authority
and lifecycle evidence.

## The five decisions

`agent-team` separates five decisions that are often mixed together. Choose
each independently; do not let one answer dictate the others.

```text
Decision        Question                          Typical answers
--------        --------                          ---------------
Topology        Who works, and how long?          one Agent | temporary team | persistent team
Wakeup          When does the controller wake?    none | heartbeat | cron
Convergence     How does the objective finish?    single-pass | evidence-loop | phase-gated
Verification    What proves it is done?           deterministic checks + independent review (or not)
Human gates     Which actions need the user?      publication, deployment, deletion, payment, ...
```

Example: a temporary team may still use `none` wakeup and a single pass; a
persistent team may use a heartbeat and phase gates. Topology is not lifetime
by itself.

## Glossary

- **Topology** — how many Agents work and whether roles survive past the
  objective (`single`, `temporary`, `persistent`).
- **Wakeup** — when the controller receives a new turn (`none`, `heartbeat`,
  `cron`). Separate from topology.
- **Convergence** — how the current objective reaches verified completion
  (`single-pass`, `evidence-loop`, `phase-gated`).
- **Verification** — deterministic checks plus, only for a named residual
  risk, one independent review with a single recorded backend.
- **Human gates** — user-authority boundaries around consequential actions
  (publish, deploy, delete, pay, permission changes).
- **Task packet** — the canonical control document for a delegated task;
  validated by `scripts/validate_task_packet.py`.
- **`<task_handoff>`** — the fixed block at the end of every handoff carrying
  `finding_severity`, `goal_alignment`, `scope_delta`, `new_assumptions`, and
  `next_authorized_step`.
- **Evidence loop** — a bounded, frozen-check iteration in an isolated linked
  Git worktree, gated by contract/state hashes and a required review.
- **Native verifier** — the default independent-review backend; a separate
  read-only Codex context with zero external dependencies.
- **AgentParliament / Reasonix** — an optional review adapter, never required
  for Agent Team to operate.
- **Luna / Terra lanes** — optional implementation profiles for temporary
  delegation: `luna_worker` for specification-determined work, `terra_worker`
  for context-heavy or higher-risk implementation.

## Requirements

- Codex with Skills support
- Python 3.10 or newer for the bundled validators and the cross-platform
  installer
- Git for the optional evidence-loop workflow
- Windows PowerShell 5.1 or newer only when using the PowerShell helpers

The Skill and Python helpers use the standard library only.

## Install

Clone the repository, then install the managed Skill surface. On any platform
with Python 3.10+ (the preferred, cross-platform path):

```bash
git clone https://github.com/youngfor-shoot/codex-agent-team.git
cd codex-agent-team
python scripts/sync-agent-team.py --mode Install --yes
python scripts/sync-agent-team.py --mode Verify
```

On Windows you may use the PowerShell helpers instead:

```powershell
git clone https://github.com/youngfor-shoot/codex-agent-team.git
Set-Location codex-agent-team
& .\scripts\sync-agent-team.ps1 -Mode Install -Confirm:$false
& .\scripts\sync-worker-agents.ps1 -Mode Install -Confirm:$false
```

The helper installs to `~/.codex/skills/agent-team` by default, backs up the
currently managed files, preserves unknown files, and verifies hashes after the
copy. Pass `--destination <path>` (Python) or `-Destination <path>`
(PowerShell) to use another runtime location.

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
contract. Evidence-loop, verification-backend, roundtable, and implementation
lane details use progressive disclosure under
[`skill/agent-team/references/`](skill/agent-team/references/). Worked
examples — preview output, a temporary-team transcript, an evidence-loop
session, persistent-team setup, and refusal cases — live under
[`examples/`](examples/). See the [`CHANGELOG.md`](CHANGELOG.md) for version
history.

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
python skill/agent-team/scripts/validate_task_packet.py skill/agent-team/templates/task-packet.md --template
python skill/agent-team/scripts/validate_task_packet.py examples/in-progress-task-packet.md
python skill/agent-team/scripts/validate_task_packet.py examples/completed-task-packet.md --require-complete
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-worker-agents.ps1 -Mode Verify
```

The first three commands are portable. The structural validator requires a
local Codex installation, and the PowerShell synchronization checks verify the
current user-level runtime copy on Windows; use
`python scripts/sync-agent-team.py --mode Verify` on other platforms. CI runs
the portable tests on Linux, macOS, and Windows and exercises a fresh
install/verify cycle on Windows.

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
