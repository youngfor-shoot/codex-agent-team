# Issue #2 output quality scorecard

Baseline: v0.5.5. Candidate: v0.5.6. Owner: repository maintainer.
This is a regression-based output evaluation, not a comparative model benchmark.

| Output contract | Baseline evidence | Candidate acceptance |
| --- | --- | --- |
| Preserve unowned installer contents | Hidden files and unrelated empty directories lost in reproduced tests | 22 installer tests; 21 pass, one Windows symlink privilege skip |
| Honest uninstall result | Injected PowerShell deletion failure returned success | Failure marker, error, remaining file and absence of success asserted |
| Propagate cancellation | Signal handler returned; canceled process not reaped | Focused failure-to-pass tests; real POSIX exit-code checks in CI |
| Reject malformed handoffs | Undefined controls and empty text accepted | 37 packet tests pass; templates retain placeholders |
| Read-only preview | Action proof not checked | 19 routing tests cover mutation, missing values, wrong types and near neighbor |
| Smallest useful setup | Entrypoint mandated delegation before any write | Independent three-case instruction probe; direct small task accepted |
| Reproducible example | Illustrative values only | Three integration regressions; standalone CLI run independently reviewed and completed; full captured transcript with artifact-hash check |

Fixture sources: repository Python regression files and the three concrete
requests recorded in `issue2-completion.md`. They are file-backed fixtures,
not sampled production usage. Static conformance cannot prove model behavior
or runtime isolation. Reassess on changed contracts; retain v0.5.5 for rollback.
