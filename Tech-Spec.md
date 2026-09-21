# Agent Team Source Repository Technical Specification

## Source-of-truth Contract

- Canonical source: `skill/agent-team/`
- Runtime copy: `~/.codex/skills/agent-team`
- Synchronization direction: canonical source to runtime copy only
- Repository helpers: `scripts/sync-agent-team.ps1` (Windows) and
  `scripts/sync-agent-team.py` (cross-platform, Python 3.10+)

The Skill folder keeps the standard Codex layout:

```text
skill/agent-team/
  SKILL.md
  agents/openai.yaml
  references/*.md
  templates/*.md
  scripts/*.py
agents/
  luna-worker.toml
  terra-worker.toml
```

## Optional Implementation Lanes

Agent Team remains the sole owner of topology, scope, architecture,
integration, verification, review selection, and final acceptance. A small or
sequential task stays on the direct ROOT route when delegation has no useful
independent outcome. ROOT may also retain a disjoint implementation scope while
an executor handles another bounded scope.

For a temporary implementation delegation, inspect the live runtime first and
select an available agent type, model, and effort using the canonical
[runtime matrix](skill/agent-team/references/implementation-lanes.md). The
matrix, rather than a forced Luna rule, is the source of truth for choosing a
bounded implementation lane. Record the selected `agent_type`, requested
model, requested effort, and reason in Mission; effective runtime identity
remains `unknown` unless the runtime attests it.

Every native child uses `fork_turns: none` and the existing Guidance / Context /
Mission assignment. Companion roles are not persistent-team identities and
never activate independent review; the named residual-risk gate remains
unchanged.

## Dispatch And Review-Finding Contract

Present every delegated assignment with three human-readable sections backed
by the existing canonical child fields:

- `Guidance`: execution method, constraints, quality standard, and applicable
  Skill scope;
- `Context`: canonical objective, current phase, exact inputs, upstream
  evidence, user preferences, and dependencies;
- `Mission`: bounded goal, ownership, deliverable, acceptance, next authorized
  step, and stop conditions.

These headings are a presentation layer, not a second state model. Create a
task packet when project rules require one; otherwise the controller's scoped
assignment is sufficient. When present, the task packet remains authoritative
if wording conflicts or becomes stale.

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

The main synchronizers manage `SKILL.md` and seven visible directories:
`agents/`, `references/`, `scripts/`, `templates/`, `evals/`, `reports/`, and
`tests/`. Within those directories, the managed surface is deliberately narrow:
YAML in `agents/`; Markdown in `references/`, `templates/`, and `reports/`;
Python in `scripts/`; JSON in `evals/`; and JSON or Markdown only below
`tests/fixtures/`.

Hidden path components and unrecognized paths are outside that surface. They
are neither copied nor removed. Do not place credentials in repository files or
the managed runtime surface. The helper also rejects links and reparse points
on visible managed paths, preserving the managed-surface boundary.

Both `scripts/sync-agent-team.py` and `scripts/sync-agent-team.ps1` support
`Verify`, `Install`, `Restore`, and `Uninstall`. Python accepts `--mode`,
`--destination <path>`, `--backup-name`, and `--yes`; PowerShell uses the
matching `-Mode`, `-Destination`, and `-BackupName` parameters. Both use the
same managed-file set, backups, and normalized-SHA-256 comparison semantics.

The separate `scripts/sync-worker-agents.ps1` helper manages exactly:

- canonical `agents/luna-worker.toml` to `~/.codex/agents/luna-worker.toml`;
- canonical `agents/terra-worker.toml` to `~/.codex/agents/terra-worker.toml`.

It supports `Verify` and explicit `Install`, creates a backup of existing
managed destinations before replacement, compares normalized SHA-256 hashes,
and leaves every unrelated global Agent file untouched.

After a successful worker-profile install and post-copy hash check, the helper
must explicitly return exit code zero so an earlier caller-side drift probe
cannot leak a stale nonzero status into the successful result.

## Task-Template Validation

Template headings are matched as complete Markdown lines, not substrings.
Every valid template contains exactly one `<task_handoff>` block, and each
required handoff field appears as its own field line inside that block. A field
name in surrounding prose or a heading such as `### Missionary` does not
satisfy the contract.

## Public Distribution

- `README.md` owns public setup, usage, and verification guidance.
- `LICENSE` contains the Apache-2.0 terms.
- `SECURITY.md` routes sensitive reports away from public issues.
- `.github/workflows/ci.yml` runs Python unit tests on Linux, macOS, and
  Windows; it also exercises the Python installer on Linux and macOS and the
  PowerShell install/verify smoke cycle on Windows.
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
destination files remain untouched. If managed-file removal creates an empty
ancestor directory, cleanup removes only that empty ancestor and stops as soon
as it encounters a nonempty directory.

### Restore

Validate the requested backup name and managed backup surface before mutation.
Stage and hash-check the backup, retain a rollback snapshot of the current
managed surface, then converge the runtime to the backup's managed files. On a
restore failure, attempt rollback and retain recovery files if rollback cannot
converge. Unrelated and hidden destination content remains outside the restore
surface.

### Uninstall

Prompt unless explicitly confirmed, remove only discovered managed runtime
files, then re-enumerate the managed surface. Report failure if any managed
file remains; do not report an uninstall as successful merely because some
files were removed. Preserve unrelated files and prune only empty ancestors
created by the removal.

## Failure Behavior

- Reject a missing canonical Skill root.
- Reject source and destination resolving to the same path.
- Do not start installation if backup creation fails.
- Return a nonzero exit code on drift, copy failure, or post-install mismatch.
- Return a nonzero exit code when uninstall leaves any managed file behind.
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
- The child environment uses a cross-platform allowlist (Windows and POSIX
  variables) plus any names frozen via `--env-passthrough`; the contract file
  is marked read-only after `init`.

## Verification Commands

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

CI runs Python tests and the template/example validation on Linux, macOS, and
Windows, exercises the cross-platform Python installer on Linux and macOS, and
runs the PowerShell install/verify smoke cycle on Windows.

Runtime discovery, actual child spawning, selected model, reasoning effort,
and elapsed time require a separate fresh-task observation. Static tests and CI
validate the published contract but do not prove those runtime facts.
