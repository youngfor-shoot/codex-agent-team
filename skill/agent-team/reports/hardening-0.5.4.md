# Installed Skill Hardening 0.5.4

Status: local defects repaired; native delegation isolation remains blocked by
the configured host's observed tool behavior. Do not report all concerns solved.

## Completed repairs

- Restored the two original v0.1.0 JSON fixtures inside the installed Skill and
  made the test path package-relative. Original bytes and SHA-256 match the
  source directory recorded in `tests/fixtures/v0.1.0/README.md`; no assertion
  was weakened and the missing test was not skipped.
- Added Yao's `agents/interface.yaml` adapter with display fields identical to
  native `agents/openai.yaml`. Native metadata remains intact.
- Moved detailed policy into an explicitly required reference. Initial-load
  estimation is 969 tokens against the unmodified 1,000-token check budget.
- Added the unpinned `bounded_executor` role with explicit instruction/contract
  scope and no native-tool or OS-isolation claim. Spark retains its working
  configuration. Ineffective feature overrides were removed after testing.
- Dispatch evidence guidance now separates requested parameters, observed
  runtime fields, actual results, and incomplete trace attribution.

## Verification

| Check | Result |
| --- | --- |
| Controller-owned complete regression run | Exit 0; 92 tests, 91 passed, 1 skipped |
| Skip | File-symlink creation unavailable for this Windows account, WinError 1314; no privilege change made |
| Yao package validator | Passed, no failures or warnings |
| Resource-boundary validator | Passed, no failures or warnings; 969/1000 initial tokens |
| Native/Yao interface parity | Passed |
| Original fixture byte comparison | Passed for both files |
| Catalog trigger heuristic | 10/10; not a native behavioral benchmark |
| Independent scoped review | No introduced policy, compatibility, or weakened-test blocker found |
| Native role acceptance | Both requested roles completed real fixture reads; runtime field and tool-surface limits recorded separately |

The worker's first full-suite run lacked a final receipt. The controller ran a
separate final suite and retained complete stdout/stderr and exit status; that
is the full-suite evidence used above. No runtime Python engine changed.

## Host boundary: not repaired locally

`multi_agent=false` did not reliably remove exposed host collaboration tools.
A direct Sol invocation with the flag actually spawned a permitted probe child.
Disabling `code_mode_host` also broke local file reads while the probe spawn
still succeeded. These configurations were rejected as an isolation solution.
See [minimal reproduction](runtime-boundary-repro.md).

The native dispatch interface also did not supply effective worker model/effort
attestation or a complete descendant trace. Configuration and worker statements
must not be substituted for those missing fields. A host-supported tool-level
restriction and runtime receipts are required to close these stronger claims.
No private API, new provider, hook rewrite, or weakened control was introduced.

## Evidence and scope

Current-run traces remain in a maintainer-local evidence directory (not shipped), including the complete
regression logs and the three native probe outputs. The legacy JSON fixtures
are compatibility test inputs, not proof of current execution. Prior ordinary
workflow acceptance remains limited to its recorded file-backed fixture.

This installed directory is not Git-backed; no Git version, remote backup,
publication, universal reliability, or comparative speed/cost improvement is
claimed. The reduced entry estimate is a structural measurement only.
