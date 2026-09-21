# Native Delegation Restriction: Configured-Host Reproduction

Observed on 2026-09-05 with Codex CLI 0.153.4 and the user's configured tool
host. This is a local reproduction, not a claim about every Codex client.
No credentials, hook changes, OS rights, account settings, or global feature
settings were changed. Invocation-only overrides expired with each process.

## Bounded test

The read-only prompt asked the model to inspect actual native declarations.
If `spawn_agent` was exposed, the root expressly authorized exactly one child
returning `PROBE_OK`, with no tools or descendants. It prohibited CLI emulation,
file edits, credentials, services, and user-owned tasks. This tests tool
availability rather than whether a behavioral prohibition is followed.

Representative invocation, with output captured outside the read-only work:

```powershell
codex exec --ephemeral --skip-git-repo-check --sandbox read-only --disable multi_agent --model gpt-5.6-sol -c model_reasoning_effort=medium -C '<absolute-test-workspace>' '<bounded test prompt>'
```

The exact issued prompt and all observed output remain in the local traces
listed below. The second invocation additionally used `--disable code_mode_host`.

## Results

| Configuration | Observed result |
| --- | --- |
| Native `bounded_executor`, per-role `multi_agent=false`, requested Sol/medium | Worker reported visible collaboration tools; configuration alone did not prove removal |
| Native `spark_worker`, per-role `multi_agent=false`, requested low | Worker reported no visible collaboration tools; no baseline established causation by the flag |
| Direct Sol/medium, `--disable multi_agent` | `spawn_agent` exposed and accepted; actual child returned `PROBE_OK` |
| Direct Sol/medium, both disable flags | `spawn_agent` still accepted and returned `PROBE_OK`; local `exec_command` was rejected because code-mode host was disabled |

All driver processes exited 0. That does not mean all requested operations
succeeded: the last run could not read its fixture, and both direct probes
failed the intended no-native-delegation criterion.

## Disposition

The ineffective feature blocks were removed from the installed roles. Spark's
original configuration was restored. `bounded_executor` remains an explicitly
instruction-scoped role with no pinned model/effort and no isolation claim.
No unsupported flag combination is recommended. A host-provided effective
tool restriction is required before claiming native subdelegation is prevented.

Requested model/effort and observed worker output are preserved separately.
The native dispatch interface did not return effective model/effort attestations
or a complete descendant call trace; those fields remain unavailable rather
than being fabricated from configuration.

Local evidence is retained by the maintainer and is not shipped in this repository.
Files: `native.stdout.log`, `native.stderr.log`, `direct-disabled.stdout.log`,
`direct-disabled.stderr.log`, `native-mode.stdout.log`, `native-mode.stderr.log`.
The real legacy fixture read by the successful tasks is test input, not an
execution receipt. No report or issue was published externally.
