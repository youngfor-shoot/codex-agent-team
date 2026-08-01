# Evidence Loop Contract

Use this outer loop only for software work with frozen deterministic
acceptance. It complements Agent topology; it is not a team lifetime.

## Required preconditions

- Use a real linked Git worktree, never the main checkout.
- Start from a clean branch and keep state/contract files outside the worktree,
  Git metadata, Obsidian vaults, and other protected knowledge stores.
- Pass each non-Obsidian sensitive root with `--protected-path`; the helper
  detects Obsidian vault ancestors automatically.
- Freeze checks plus either controller-owned external harnesses or every
  repository acceptance asset that can change test meaning.
- Keep merge, deploy, publish, delete, purchase, account changes, and secret
  handling outside the loop.
- Require independent review for every evidence-loop run.

The helper blocks direct shell/network launchers and inline interpreter
evaluation, sanitizes the child environment, calls commands with `shell=False`,
captures only a bounded output tail, and places Windows checks in a
`KILL_ON_JOB_CLOSE` Job Object so descendants are terminated on timeout or
parent exit. Test and build commands still execute code from the worktree and
can access the current Windows user account. This is a convergence boundary for
trusted code, not an OS sandbox for unknown or malicious repositories.

## Initialize

PowerShell example:

```powershell
$runner = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex\skills\agent-team\scripts\evidence_loop.py'
$state = "$env:LOCALAPPDATA\codex\evidence-loops\my-run\state.json"
$harness = 'C:\path\to\controller-owned\acceptance.py'
$worktree = 'C:\path\to\repo-worktree'
$protected = 'C:\path\to\protected-knowledge'

python $runner init `
  --run-id my-run `
  --objective 'Implement the accepted change' `
  --worktree $worktree `
  --state-file $state `
  --check-json '["python","C:\\path\\to\\controller-owned\\acceptance.py"]' `
  --controller-harness $harness `
  --protected-path $protected `
  --max-iterations 4 `
  --max-minutes 45 `
  --command-timeout 900 `
  --same-failure-limit 2
```

If an external harness is not practical, use one or more `--frozen-path`
arguments for the test directory, package scripts, test configuration, and any
other repository asset that can weaken acceptance. A changed frozen asset
stops the run as `stopped_acceptance_tampered`.

The objective is stored only as a SHA-256 hash. Initialization writes a
read-only contract file and mutable state file, then prints both
`contract_hash` and `state_hash`. The controller must pin both returned values
in its own task context. Never rediscover a changed hash from disk after a
worker runs.

## Controller-owned outer loop

For each iteration:

1. Run:

   ```powershell
   python $runner next `
     --state-file $state `
     --expected-contract-hash $contractHash `
     --expected-state-hash $stateHash `
     --worker-run-id worker-iteration-1
   ```

2. Start a fresh bounded worker. Give it the objective, the worktree, exact
   write scope, the latest redacted failure evidence, and stop conditions. Do
   not give it the state file as writable scope.
3. After the worker returns, run:

   ```powershell
   python $runner verify `
     --state-file $state `
     --expected-contract-hash $contractHash `
     --expected-state-hash $stateHash
   ```

   After every successful state transition, replace the controller's pinned
   `$stateHash` with the new value printed by the helper.

4. If status is `active`, start the next iteration only when the new evidence
   supports a different correction. If status starts with `stopped_`, stop and
   report the evidence.
5. If status is `verification_passed`, run an independent read-only review.
   Record the controller's validated outcome:

   ```powershell
   python $runner review `
     --state-file $state `
     --expected-contract-hash $contractHash `
     --expected-state-hash $stateHash `
     --result pass `
     --reviewer-run-id independent-review-1 `
     --reviewer-backend native-verifier `
     --artifact-hash <sha256>
   ```

For failure, add `--result fail --reason-code confirmed_review_finding`.
Reviewer run ID must differ from every worker ID. The backend and artifact hash
record what actually performed the review; they remain controller assertions,
not cryptographic identity proof. Review failure reopens the run without
changing the frozen checks. Immediately before recording review, the helper
rechecks frozen assets and the exact source fingerprint verified previously.
Any intervening change stops or reopens the run. Only review pass over the
verified source produces `completed`.

## Emergency stop

Use a low-entropy reason code so logs cannot accidentally store secrets:

```powershell
python $runner abort `
  --state-file $state `
  --expected-contract-hash $contractHash `
  --expected-state-hash $stateHash `
  --reason-code permission_boundary
```

Abort immediately for scope drift, permission expansion, sensitive data,
destructive behavior, missing human judgment, or an acceptance contract that
is no longer valid.

## Exit codes

- `0`: command completed; inspect the returned status.
- `1`: contract or state error.
- `2`: verification or review failed but the run may continue.
- `3`: a hard stop condition was reached.

Do not infer success from a worker message or process exit alone. The final
state must be `completed`, and the controller must still inspect and integrate
the worktree. The helper never merges or deploys.
