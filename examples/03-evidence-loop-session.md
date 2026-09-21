# Example 03 — Evidence-loop session

This is a representative, contract-valid sequence for
`init → next → verify(fail) → next → verify(pass) → review → completed`.
The paths, run IDs, and JSON values are illustrative; this page is not a claim
that the commands were executed against a published repository.

## Setup

- Repository: a linked Git worktree, never the main checkout.
- State and contract files: outside the worktree and Git metadata.
- Frozen check: `["python", "C:\\harness\\acceptance.py"]`.
- Budget: 4 iterations, 45 minutes, 900-second command timeout, and a
  same-failure limit of 2.

```powershell
$stateFile = 'C:\state\auth-migration-001\state.json'
$initSummary = python evidence_loop.py init `
  --run-id auth-migration-001 `
  --objective 'Add import validation and verify it' `
  --worktree C:\worktrees\auth-migration `
  --state-file $stateFile `
  --check-json '["python","C:\\harness\\acceptance.py"]' `
  --controller-harness C:\harness\acceptance.py `
  --protected-path C:\protected-knowledge `
  --env-passthrough GIT_AUTHOR_NAME `
  --max-iterations 4 `
  --max-minutes 45 `
  --command-timeout 900 `
  --same-failure-limit 2 | ConvertFrom-Json
$contractHash = $initSummary.contract_hash
$stateHash = $initSummary.state_hash
```

Representative output shape:

```json
{
  "run_id": "auth-migration-001",
  "status": "active",
  "contract_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "state_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

The controller retains each returned hash before the next transition. The
contract file is read-only; the mutable state file is re-hashed on every
transition.

## Iteration 1 fails verification

```powershell
$nextSummary = python evidence_loop.py next `
  --state-file $stateFile `
  --expected-contract-hash $contractHash `
  --expected-state-hash $stateHash `
  --worker-run-id worker-1 | ConvertFrom-Json
$stateHash = $nextSummary.state_hash

$verifySummary = python evidence_loop.py verify `
  --state-file $stateFile `
  --expected-contract-hash $contractHash `
  --expected-state-hash $stateHash | ConvertFrom-Json
$stateHash = $verifySummary.state_hash
```

Representative failed-verification shape:

```json
{
  "status": "active",
  "iteration": 1,
  "last_verification": {
    "passed": false,
    "evidence_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  }
}
```

The verify command exits with code 2. The failure fingerprint is stored;
repeating the same failure reaches the configured no-progress stop condition.

## Iteration 2 passes verification

```powershell
$nextSummary = python evidence_loop.py next `
  --state-file $stateFile `
  --expected-contract-hash $contractHash `
  --expected-state-hash $stateHash `
  --worker-run-id worker-2 | ConvertFrom-Json
$stateHash = $nextSummary.state_hash

$verifySummary = python evidence_loop.py verify `
  --state-file $stateFile `
  --expected-contract-hash $contractHash `
  --expected-state-hash $stateHash | ConvertFrom-Json
$stateHash = $verifySummary.state_hash
```

Representative passing-verification shape:

```json
{
  "status": "verification_passed",
  "iteration": 2,
  "last_verification": {
    "passed": true,
    "evidence_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
  }
}
```

The source fingerprint is recorded. Any source change before review invalidates
the verification.

## Independent review completes the run

```powershell
$artifactHash = (Get-FileHash `
  -Algorithm SHA256 `
  -LiteralPath C:\reviews\auth-migration-review.md).Hash.ToLowerInvariant()
$reviewSummary = python evidence_loop.py review `
  --state-file $stateFile `
  --expected-contract-hash $contractHash `
  --expected-state-hash $stateHash `
  --result pass `
  --reviewer-run-id review-1 `
  --reviewer-backend native-verifier `
  --artifact-hash $artifactHash | ConvertFrom-Json
$stateHash = $reviewSummary.state_hash
```

Representative completed shape:

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

The controller may now inspect and integrate the worktree. The helper itself
never merges or deploys.

## What the sequence demonstrates

- Frozen checks and acceptance assets remain outside worker ownership.
- The controller passes forward the contract and state hashes returned by the
  immediately preceding transition.
- Linked-worktree isolation and protected-path enforcement remain active.
- A required independent review records its backend and artifact hash before
  the run reaches `completed`.

## What the sequence does not demonstrate

- Runtime discovery, child spawning, selected model, reasoning effort, or
  timing. Those require a separate observed run.
