# Issue #2 release review

Status: local deterministic acceptance and independent review passed.
The protected final-candidate CI gate remains required before merge/release.

Question: does this bounded candidate satisfy the audited installer, cancellation,
handoff, preview, and direct-routing contracts without introducing data loss,
continuing canceled work, or false completion evidence?

Residual risk: cross-platform file preservation and cancellation behavior cannot
be established by Windows-only deterministic checks or controller self-review.
Backend: native-verifier, separate read-only context with no implementation
ownership of the reviewed surface. Budget: one full pass and at most one focused
recheck for confirmed findings. Controller accepts or rejects findings explicitly.

Actual release reviewer: `/root/audit_issue_quality`. Initial read-only pass
found one MAJOR and one MINOR; the controller accepted both. Cleanup errors
could mask cancellation, and hidden-backup assertions compared incomparable
absolute paths. The new cancellation regression first failed for both
KeyboardInterrupt and SystemExit, then passed after unconditional propagation
of the original exception. Backup tests now require a real managed backup and
exclude the hidden filename from its inventory; both implementations passed.
The single focused recheck passed with no remaining findings. The reviewer
did not execute tests; controller execution and CI are separate evidence.

Walkthrough reviewer `/root/audit_issue_spec` independently inspected the real
capsule and then rechecked a fresh run after cancellation hardening changed the
helper hash. Both passed. The final transcript and complete hashed review
artifact appear in `../examples/03-evidence-loop-session.md`. Effective model
and effort are unknown for both reviewers. This is observed independent native
review, not an assertion derived from configured model names.

Owner: repository maintainer. Recheck after changes to these contracts. Retain
v0.5.5 as the rollback source; do not overwrite independently adapted installs.
Native-agent context separation is not OS isolation. Requested model parameters
do not attest effective model identity. No performance or cost benchmark is claimed.
