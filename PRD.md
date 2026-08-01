# Agent Team Source Repository PRD

## Problem

The `agent-team` Skill coordinates Codex collaboration and risk-matched
verification, but a machine-local installation cannot be inspected, installed,
or improved reliably by other maintainers.

## Outcome

Publish one portable, versioned canonical source for the Skill while keeping
Codex discovery through a derived user-level installation.

## Requirements

1. The repository contains every durable `agent-team` Skill file and excludes
   runtime caches.
2. The installed global directory is treated as a derived runtime copy.
3. A deterministic tool can verify source/runtime equality without mutation.
4. Installation is an explicit operation, backs up managed destination files,
   and changes only the Skill's managed surface.
5. Existing Skill unit tests and structural validation pass from the repository.
6. No secret, credential, `.env`, cache, or unrelated global Skill file is read
   or copied.
7. Public documentation explains purpose, installation, safety boundaries, and
   verification without exposing maintainer-specific paths.
8. Continuous integration runs the portable Python tests and the Windows
   synchronization smoke test.
9. The repository uses an explicit open-source license and provides a private
   security-reporting path.

## Acceptance

- `Verify` exits zero when canonical source and runtime copy match.
- `Verify` exits nonzero and lists relative paths when a managed file is missing,
  changed, or stale.
- All Python unit tests pass.
- Skill structural validation passes.
- A fresh temporary destination can be installed and then verified on Windows.
- A tracked-file scan finds no credential signatures or maintainer-specific
  absolute paths.

## Non-goals

- Moving the global Codex Skill discovery root.
- Changing the `agent-team` routing contract beyond the already-approved
  risk-matched review policy.
- Claiming ecosystem adoption before public evidence exists.
- Adding a package manager, telemetry, hosted service, or new runtime dependency.
