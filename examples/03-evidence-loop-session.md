# Example 03 — Evidence-loop session

The money shot: a real `init → next → verify(fail) → next → verify(pass) →
review → completed` session, with the JSON summaries the helper prints at each
transition. This is the artifact that makes the abstract state machine
concrete.

## Setup

- Repository: a real linked Git worktree, never the main checkout.
- State/contract files live outside the worktree and Git metadata.
- Checks frozen: `["python", "acceptance.py"]`; harness outside the worktree.
- Budget: 4 iterations / 45 minutes / 900s command timeout / same-failure 2.

## init

```powershell
python evidence_loop.py init `
  --run-id auth-migration-001 `
  --objective 'Add import validation and verify it' `
  --worktree C:\worktrees\auth-migration `
  --state-file C:\state\auth-migration-001\state.json `
  --check-json '["python","C:\\harness\\acceptance.py"]' `
  --controller-harness C:\harness\acceptance.py `
  --protected-path C:\protected-knowledge `
  --env-passthrough GIT_AUTHOR_NAME `
  --max-iterations 4 --max-minutes 45 --command-timeout 900 --same-failure-limit 2
```

```json
{
  "run_id": "auth-migration-001",
  "status": "active",
  "contract_hash": "3f9c...",
  "state_hash": "7a1e..."
}
```

The controller pins both hashes. The contract file is read-only; the state file
is mutable and re-hashed on every transition.

## next (iteration 1)

```powershell
python evidence_loop.py next --state-file ... --expected-contract-hash 3f9c... --expected-state-hash 7a1e... --worker-run-id worker-1
```

```json
{ "status": "running", "iteration": 1, "current_worker_run_id": "worker-1" }
```

The controller starts a fresh bounded worker with the objective, worktree,
exact write scope, latest redacted failure evidence, and stop conditions.

## verify (fail)

```powershell
python evidence_loop.py verify --state-file ... --expected-contract-hash 3f9c... --expected-state-hash <new>
```

```json
{
  "status": "active",
  "iteration": 1,
  "last_verification": { "passed": false, "evidence_hash": "5b2d..." }
}
```

Exit code 2. The failure fingerprint is stored; repeated identical failures hit
the same-failure limit and stop the run.

## next (iteration 2) → verify (pass)

```powershell
python evidence_loop.py next --state-file ... --worker-run-id worker-2
python evidence_loop.py verify --state-file ...
```

```json
{
  "status": "verification_passed",
  "iteration": 2,
  "last_verification": { "passed": true, "evidence_hash": "c81a..." }
}
```

Exit code 0. The source fingerprint is recorded; any change before review
invalidates this verification.

## review

```powershell
python evidence_loop.py review `
  --state-file ... --result pass `
  --reviewer-run-id review-1 `
  --reviewer-backend native-verifier `
  --artifact-hash <sha256>
```

```json
{
  "status": "completed",
  "iteration": 2,
  "last_review": {
    "result": "pass",
    "reviewer_run_id": "review-1",
    "reviewer_backend": "native-verifier"
  }
}
```

Exit code 0. The controller inspects and integrates the worktree; the helper
never merges or deploys.

## What this proves

- Frozen checks and acceptance assets outside worker ownership.
- Contract/state hashes pinned by the controller, never rediscovered from disk.
- Linked-worktree isolation and protected-path enforcement.
- One independent review before `completed`, with backend and artifact hash
  recorded as controller assertions.

## What it does not prove

- Runtime discovery, child spawning, selected model, reasoning effort, or
  timing. Those require a separate fresh-task observation.
