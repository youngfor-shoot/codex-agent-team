# Agent Team Source Repository PRD

## Problem

The `agent-team` Skill coordinates Codex collaboration and risk-matched
verification, but a machine-local installation cannot be inspected, installed,
or improved reliably by other maintainers. Its complete child contract also
needs a concise dispatch presentation, and reviewer findings need a consistent
severity vocabulary without making review mandatory. Temporary implementation
delegation also lacks an explicit routine-versus-complex lane contract, while
the matching custom-agent profiles currently have no versioned rollback path.

## Outcome

Publish one portable, versioned canonical source for the Skill while keeping
Codex discovery through a derived user-level installation. Keep delegated work
easy to scan and review findings easy to triage without creating a second task
schema or changing the residual-risk review gate. Add optional, versioned Luna
and Terra implementation lanes that preserve Codex as controller and remain
portable when the companion roles are unavailable.

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
10. Child assignments present the canonical contract as `Guidance`, `Context`,
    and `Mission` without duplicating task authority.
11. Reviewer findings use `BLOCKER`, `MAJOR`, or `MINOR`; executors and reviews
    with no findings use `none`, and the controller remains the acceptance
    authority.
12. The repository versions companion `luna_worker` and `terra_worker` profiles
    and synchronizes only their two exact global Agent files.
13. Temporary implementation work prefers `luna_worker` when the specification
    largely determines the result and selects `terra_worker` only when
    correctness depends on substantial context, implementation judgment, or a
    wider technical blast radius.
14. Both custom roles use `fork_turns: none`, preserve the parent objective and
    settled architecture, and never expand their delegated ownership.
15. One Luna attempt may escalate to Terra only after evidence shows the work
    was misclassified and the controller corrects the specification.
16. Missing companion roles do not disable Agent Team. The controller reports
    the unavailable preferred lane and uses an explicitly identified available
    native implementation role under the same bounded contract.

## Acceptance

- `Verify` exits zero when canonical source and runtime copy match.
- `Verify` exits nonzero and lists relative paths when a managed file is missing,
  changed, or stale.
- All Python unit tests pass.
- Skill structural validation passes.
- A fresh temporary destination can be installed and then verified on Windows.
- A tracked-file scan finds no credential signatures or maintainer-specific
  absolute paths.
- Template validation requires the three exact dispatch headings and exactly
  one handoff block, with every required handoff field inside that block.
- Companion Agent profiles contain the expected names, models, reasoning
  efforts, descriptions, and developer instructions.
- A temporary Agent destination can install and verify both profiles without
  modifying unrelated files.
- A fresh Codex task can discover and run both companion roles with
  `fork_turns: none`; static tests and CI do not substitute for this runtime
  evidence.
- Static contract tests preserve the Skill-to-reference route, the
  specification-determined versus context-heavy lane boundary, corrected
  one-time escalation, and independence from the risk-matched review gate.

## Non-goals

- Moving the global Codex Skill discovery root.
- Changing execution topology, wakeup, convergence, review-trigger, or human-
  gate policy beyond the already-approved risk-matched review policy.
- Making Luna or Terra persistent-team roles, architecture owners, reviewers,
  or mandatory dependencies for environments that do not expose them.
- Claiming ecosystem adoption before public evidence exists.
- Adding a package manager, telemetry, hosted service, or new runtime dependency.
