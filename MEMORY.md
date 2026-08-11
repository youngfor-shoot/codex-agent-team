# Project Memory

## Purpose

Store durable decisions for the canonical `agent-team` Skill source.

## Durable Decisions

### 2026-08-12: v0.2 adoption round (issue #2 triage)

- `native-verifier` is the default independent-review backend: a separate
  read-only Codex context, zero external dependencies. AgentParliament/Reasonix
  is an optional adapter documented in
  `skill/agent-team/references/verification-backends.md`; it is never required
  for Agent Team to operate and falls back to `native-verifier` when
  unavailable.
- The evidence-loop child environment is cross-platform: the allowlist now
  includes POSIX variables (`HOME`, `LANG`, `USER`, `TMPDIR`, etc.) alongside
  the Windows set. `--env-passthrough <NAME>` freezes variable names into the
  contract; values are read from the current process at check time.
- The contract file is marked read-only after `init` (best effort; contract
  hashes remain the integrity guarantee).
- Canonical task-packet template and `<task_handoff>` schema live in
  `skill/agent-team/templates/`; two validated worked examples live in
  `examples/`; CI validates all three.
- `scripts/sync-agent-team.py` mirrors the PowerShell helper on POSIX
  (`--mode Verify|Install`, `--destination`, `--yes`); both tools manage
  `SKILL.md`, `agents/*.{yaml,yml}`, `references/*.md`, `templates/*.md`, and
  `scripts/*.py`.
- CI matrix is ubuntu/macos/windows for Python tests and template/example
  validation; the Python installer is smoke-tested on ubuntu/macos.
- SKILL.md frontmatter now carries `version: 0.2.0`; `CHANGELOG.md` added.
- PR #1 (Luna/Terra lanes) merged to main at `853d1ac`.

### 2026-08-11: Validation is structural and evidence claims are scoped

- Task-template validation matches exact Markdown heading lines and requires
  exactly one `<task_handoff>` block. Required handoff fields must be field
  lines inside that block; prose substrings and prefix headings do not count.
- A successful worker-profile install explicitly exits zero after the final
  hash check so an earlier drift probe cannot leak a stale failure status.
- Static tests cover the profile, synchronization, and template contracts, and
  CI is configured to re-run them. Runtime discovery, child spawning, selected
  model, reasoning effort, and timing require separate fresh-task evidence.

### 2026-08-03: Temporary implementation uses optional Luna and Terra lanes

- The repository versions `luna-worker.toml` and `terra-worker.toml` as
  optional implementation profiles. `luna_worker` owns bounded work whose
  objective, interfaces, constraints, and verification are explicit;
  `terra_worker` owns implementation that requires substantial contextual
  judgment, such as concurrency, persistence, security, or broad blast radius.
- Task size alone does not select Terra. A failed Luna attempt is inspected and
  corrected in the same lane unless the controller finds that the work was
  genuinely misclassified; escalation is allowed once and must be explicit.
- Agent Team remains the controller and owns topology, architecture, scope,
  integration, deterministic verification, review gates, and final acceptance.
  The two workers are not persistent team roles and are spawned with isolated
  context (`fork_turns = "none"`).
- Independent review remains risk-matched and separate from model routing.
  Selecting Terra does not automatically require review, and selecting Luna
  does not waive a named residual-risk review gate.
- `scripts/sync-worker-agents.ps1` manages only the two named runtime profiles,
  preserves unrelated agent files, backs up conflicting managed copies, and
  verifies normalized SHA-256 hashes after installation.
- Maintainer-local forward testing was reported for Luna/Terra routing,
  correction, escalation, and review-gate separation, but this repository does
  not contain a reproducible public trace of those runs. Public verification
  therefore contains reproducible evidence for the static profile contract,
  synchronization behavior, and task-packet validation only; do not claim
  runtime discovery, selected model, reasoning effort, or elapsed-time
  compatibility from repository evidence alone.
- Terra and independent review remain bounded tools for justified complexity
  or residual risk, not default phases for routine implementation.

### 2026-08-02: Dispatch presentation and finding severity are additive

- Child assignments present the existing canonical contract as `Guidance`,
  `Context`, and `Mission`; these headings do not create a second task schema.
- Independent reviewers label candidate findings `BLOCKER`, `MAJOR`, or
  `MINOR`, and every handoff carries `finding_severity`; executors and reviews
  with no findings use `none`.
- The controller remains responsible for source-checking, accepting, rejecting,
  or reclassifying every finding. Severity does not activate review or replace
  the residual-risk gate.
- Task-packet tests, structural Skill validation, the Jarvis template check,
  and the canonical-to-runtime hash verification passed after installation.

### 2026-08-02: Public source is separate from the installed runtime copy

- The repository is the public canonical source for the `agent-team` Skill.
- Runtime installations remain derived copies under
  `~/.codex/skills/agent-team` for Codex discovery.
- Synchronization is one-way from the repository to the runtime copy and is
  verified by content hashes.
- The repository owns the executable Skill, references, validators, tests, and
  public distribution contract. A consuming project may add stricter local
  orchestration policy without changing this source.
- Apache-2.0 is the public license because it is permissive and includes an
  explicit patent grant.
- Public documentation must not depend on a maintainer's machine paths or make
  unsupported adoption claims.

### 2026-08-02: Public GitHub distribution starts at v0.1.0

- The canonical public remote is
  `https://github.com/youngfor-shoot/codex-agent-team`.
- The first public release is `v0.1.0`, created only after Python tests passed
  on Linux and Windows and the Windows install/verify smoke test passed.
- GitHub Actions are pinned to full commit SHAs and have read-only repository
  contents permission.
- GitHub private vulnerability reporting is enabled for sensitive findings.
- Stars, downloads, and external adoption remain unknown until public evidence
  exists; release or application copy must not imply otherwise.
