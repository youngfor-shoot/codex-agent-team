# Example 03 — Observed evidence-loop session

This run was executed on Windows with Python 3.12 on 2026-09-22 (Asia/Shanghai).
It records actual CLI output for
`init → next → verify(fail) → next → verify(pass) → independent review → completed`.
It replaces the earlier representative example with a reproducible execution.
The helper makes the one-line repair; this is not a model implementation benchmark.

## Reproduce

From the repository root, choose a new output directory outside this checkout:

```text
python -B scripts/evidence_walkthrough.py prepare --directory ../agent-team-walkthrough
```

The helper creates its own disposable Git repository and linked worktree.
The original checkout retains `answer = 41`; the worktree changes to
`answer = 42`. The external frozen harness checks that exact answer.
The five real CLI calls return `0, 0, 2, 0, 0`, ending at
`verification_passed`. Each transition passes the prior returned hashes.

Have a separate reviewer inspect the worktree, frozen harness, state and
transcript. Save its actual review outside the worktree, then, only after a
passing review, record the real reviewer run identity:

```text
python -B scripts/evidence_walkthrough.py complete --directory ../agent-team-walkthrough --review-artifact ../actual-review.md --reviewer-run-id actual-review-run
```

`complete` hashes the supplied artifact; it does not spawn a reviewer or
prove their identity. The controller is responsible for accurate attribution.
Missing review artifacts, changed source, or stale state cannot produce a
successful completion. Existing output directories are never overwritten.
The raw local evidence remains in the chosen directory; reruns generate
different timestamps, paths and hashes. No cleanup or deployment is performed.

## Captured output

The JSON below is the actual transcript, without local absolute paths.
Hashes are complete, not sample values. UTC timestamps are retained as emitted.

```json
{
  "provenance": "Real CLI execution in a disposable linked worktree; source repair by this helper, not an agent benchmark.",
  "helper_sha256": "24d3488c0836c608f924e5d16b2bb8e43a5488874be3e0f95674fe675b6d57e2",
  "acceptance_sha256": "37da481615dc9fdd8e2b7afff1a2e2075ba4b6133277b7e4ae0d30bfb11a3841",
  "steps": [
    {
      "command": "init",
      "returncode": 0,
      "summary": {
        "run_id": "issue2-walkthrough",
        "status": "active",
        "revision": 1,
        "contract_hash": "622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c",
        "state_hash": "78360c44bbda0f66a466f249b87337641234fc41e2c2924a3c5e4b8d87b8d6f4",
        "iteration": 0,
        "current_worker_run_id": null,
        "max_iterations": 3,
        "deadline": "2026-09-22T01:03:47.574815Z",
        "same_failure_streak": 0,
        "stop_reason": null
      }
    },
    {
      "command": "next",
      "returncode": 0,
      "summary": {
        "run_id": "issue2-walkthrough",
        "status": "running",
        "revision": 2,
        "contract_hash": "622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c",
        "state_hash": "1b5624350dec01c5d0e41ba3ff20f05fbccea3e2a01c6d94282d34d435b3dac7",
        "iteration": 1,
        "current_worker_run_id": "scripted-baseline",
        "max_iterations": 3,
        "deadline": "2026-09-22T01:03:47.574815Z",
        "same_failure_streak": 0,
        "stop_reason": null
      }
    },
    {
      "command": "verify",
      "returncode": 2,
      "summary": {
        "run_id": "issue2-walkthrough",
        "status": "active",
        "revision": 3,
        "contract_hash": "622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c",
        "state_hash": "3b02a394cf2b91405fa52c91ff2d931be7f828fcffa7d31acd6d1490e16b5a9c",
        "iteration": 1,
        "current_worker_run_id": "scripted-baseline",
        "max_iterations": 3,
        "deadline": "2026-09-22T01:03:47.574815Z",
        "same_failure_streak": 1,
        "stop_reason": null,
        "last_verification": {
          "passed": false,
          "evidence_hash": "bb30f79f7efa7812846e898a92c2d1f594d8477f52f87736e86b47a94e77e332"
        }
      }
    },
    {
      "command": "next",
      "returncode": 0,
      "summary": {
        "run_id": "issue2-walkthrough",
        "status": "running",
        "revision": 4,
        "contract_hash": "622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c",
        "state_hash": "78fc7eac21d854dc31fe73728be0f52e845570ef16b0f8ff4196be33fede9ac9",
        "iteration": 2,
        "current_worker_run_id": "scripted-repair",
        "max_iterations": 3,
        "deadline": "2026-09-22T01:03:47.574815Z",
        "same_failure_streak": 1,
        "stop_reason": null,
        "last_verification": {
          "passed": false,
          "evidence_hash": "bb30f79f7efa7812846e898a92c2d1f594d8477f52f87736e86b47a94e77e332"
        }
      }
    },
    {
      "command": "verify",
      "returncode": 0,
      "summary": {
        "run_id": "issue2-walkthrough",
        "status": "verification_passed",
        "revision": 5,
        "contract_hash": "622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c",
        "state_hash": "e2e1c8fa139bdcd4cb01ddee0a8f387c55bd1c4521dc6c2a97eb092de6bbc5bb",
        "iteration": 2,
        "current_worker_run_id": "scripted-repair",
        "max_iterations": 3,
        "deadline": "2026-09-22T01:03:47.574815Z",
        "same_failure_streak": 0,
        "stop_reason": null,
        "last_verification": {
          "passed": true,
          "evidence_hash": "eb70ee890090955aeca4158f5ecb741c8d2493bd07c89d171e5ec52ec7d7cc47"
        }
      }
    },
    {
      "command": "review",
      "returncode": 0,
      "summary": {
        "run_id": "issue2-walkthrough",
        "status": "completed",
        "revision": 6,
        "contract_hash": "622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c",
        "state_hash": "3ec9bd7475cc8ebbf10b857f3d6c99c9fb9a0ba6b58c5f9affba8df3aae03939",
        "iteration": 2,
        "current_worker_run_id": "scripted-repair",
        "max_iterations": 3,
        "deadline": "2026-09-22T01:03:47.574815Z",
        "same_failure_streak": 0,
        "stop_reason": null,
        "last_verification": {
          "passed": true,
          "evidence_hash": "eb70ee890090955aeca4158f5ecb741c8d2493bd07c89d171e5ec52ec7d7cc47"
        },
        "last_review": {
          "at": "2026-09-21T17:05:50.727660Z",
          "result": "pass",
          "reason_code": null,
          "reviewer_run_id": "root-audit_issue_spec",
          "reviewer_backend": "native-verifier",
          "artifact_hash": "14c87081787768834fdf7ecd224f994859b2a133c31c099f4d3df183dc2cbaf7",
          "verification_evidence_hash": "eb70ee890090955aeca4158f5ecb741c8d2493bd07c89d171e5ec52ec7d7cc47"
        }
      }
    }
  ]
}
```

## Independent review artifact

Actual reviewer: `/root/audit_issue_spec`, normalized to
`root-audit_issue_spec` for the CLI identifier grammar. The reviewer was a
separate native context and did not implement this surface. Effective model
and effort were not attested. The following artifact was hashed with its
final newline and recorded by the controller:

```text
# Final walkthrough independent review

Result: PASS. Actual reviewer: /root/audit_issue_spec. Backend: native-verifier.
Effective model and effort: unknown. No implementation, mutation or rerun by reviewer.

Focused recheck after cancellation hardening confirmed the final helper hash
24d3488c0836c608f924e5d16b2bb8e43a5488874be3e0f95674fe675b6d57e2,
contract 622d83ef6bd9564506da21900571e68a0b655a4ca9cd88d554a74ece15352e7c,
and state e2e1c8fa139bdcd4cb01ddee0a8f387c55bd1c4521dc6c2a97eb092de6bbc5bb.
Linked-worktree identity, frozen harness, current source fingerprint, and
verification evidence hash match. Baseline remains answer 41 with no tracked
changes; the repaired worktree contains answer 42. Captured CLI exits are
[0, 0, 2, 0, 0]. Status is verification_passed at revision 5, before review.

No findings. The controller may record this review against the unchanged
capsule. It demonstrates normal fail/scripted-repair/pass on the final helper,
not cancellation itself, model performance, explicit protected-path rejection,
or OS isolation. Synthetic unit-test review fixtures are not this review.
```

## Limits

This demonstrates real command execution, hash propagation, failure, repair,
passing verification, and a separately observed review. The unit tests use
explicitly synthetic review fixtures; those are not this review.
The run has no protected paths configured and does not demonstrate
protected-path rejection, hostile-code isolation, model selection quality,
aggregate cost enforcement, merge, or deployment.
