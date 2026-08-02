# Project Memory

## Purpose

Store durable decisions for the canonical `agent-team` Skill source.

## Durable Decisions

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
