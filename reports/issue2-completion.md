# Issue #2 completion plan and evidence

## Scope and ownership

Owner: repository maintainer, with Codex responsible for implementation and acceptance.
Baseline: v0.5.5, source commit `009b30399d62d5b1d9d119ce5a110335a593c975`.
Issue: https://github.com/youngfor-shoot/codex-agent-team/issues/2

Complete the seven findings from the follow-up audit and replace the missing
worked-run evidence with a reproducible local walkthrough. Preserve the original
dirty checkout and independently updated installed Skill. Multi-host adapters,
hosting, marketing, and a new orchestration framework remain out of scope.

## Ordered acceptance gates

Each stage adds effective regression tests, demonstrates the relevant old failure,
repairs the cause, and passes its affected suite before the next stage starts.

1. **Installer boundaries:** exclude hidden paths before reading content; preserve
   unrelated files and empty directories during install, restore, and uninstall;
   report PowerShell deletion failures accurately. Verify both implementations,
   clean-target installation, and existing restoration recovery behavior.
2. **Cancellation:** clean up the running child and propagate interruption so no
   later check executes. Verify handler restoration and representative signal
   execution where the platform supports it.
3. **Contracts and minimal routing:** validate handoff control values; reject
   preview side effects; allow direct work when delegation has no independent
   benefit. Check positive, negative, and near-neighbor cases and instruction
   consistency against the explicitly bounded source changes.
4. **Worked evidence and delivery:** execute a real fail-to-pass verification
   sequence and record a separate review with honest attribution; retain a
   reproducible harness and sanitized output. Run full regression, packaging,
   lint, typing, CI, and a bounded review before GitHub delivery.

## Stage evidence

### Stage 1: installer boundaries (passed)

The initial 21-test installer run failed on both implementations: hidden files
were removed, and Install/Restore/Uninstall removed unrelated empty directories.
A PowerShell fault-injection wrapper initially failed before reaching the
installer. After correcting its argument transport, the old implementation
returned success despite the injected deletion failure. The regression now
asserts the injection marker, error, preserved file, and absence of success.
A separate trailing-separator regression reproduced deletion of the empty
destination root; normalizing the root fixed it.

Final installer suite: 22 tests, 21 passed, one Windows symlink-privilege skip.
Both implementations preserve hidden contents and unrelated empty directories;
Python also exercises undecodable hidden bytes. Existing clean-target install,
verification, restore, and failed-restore recovery regressions pass. Ruff passed
and strict mypy passed for the affected Python installer.

### Stage 2: cancellation (passed locally)

New regressions first reproduced swallowed SIGINT/SIGTERM and missing process
reaping on cancellation. Cleanup now terminates the child process tree, restores
the previous signal handlers, and propagates interruption to the caller. The
focused tests and complete evidence-loop suite passed on Windows, as did Ruff,
strict mypy, and whitespace checks. A real subprocess signal regression checks
that the following check is never reached; it is skipped on Windows and remains
a required Linux/macOS CI gate.

### Stage 3: contracts and routing (passed locally)

Malformed severity/alignment values and empty required handoff text reproduced
four failures before repair. Packet validation now enforces the documented
values while templates retain placeholders. Preview fixtures require explicit
false action flags and an empty side-effect list, covering absent values, wrong
types, mutation, a weekly planned wakeup, and a preview-button near neighbor.
All 37 packet and 19 routing tests passed, plus two entrypoint/link checks,
Ruff and strict typing. A bounded independent reading probe confirmed direct
execution for one typo, read-only weekly preview, and disjoint temporary work.
It found one optional-packet wording contradiction, which was corrected.
This is instruction-conformance evidence, not a model benchmark.

Stage 4 remains pending. A generated Ruff cache was moved outside the checkout
after verification accounting detected it; subsequent lint uses no cache.

## Delegation evidence

Stage 1 uses one bounded executor for the two installers and their tests while
the controller owns this plan and acceptance. Requested lane: Terra, high effort,
because preservation and failure handling span two platform implementations.
Effective model and effort are unknown without runtime attestation.

## Release and maintenance boundary

Review cadence: reassess these contracts whenever installation, cancellation,
preview, handoff schema, or model-routing behavior changes. Keep future review
evidence tied to the exact candidate commit; a past green run is not fresh proof.
Retain the v0.5.5 tag and local lifecycle checkpoints for source recovery. Any
runtime update must use the synchronizer and its backup/verification path.
This report does not authorize overriding unrelated installed adaptations.

No model benchmark, native-tool isolation, or operating-system sandbox guarantee
is claimed. Public release readiness remains pending until stage 4 is complete.
