# Controller Routing Acceptance

## Objective and authority

The user explicitly requested durable controller-led analysis, planning, model
and effort selection, delegated execution, and controller-owned acceptance.
The user also requested a working GPT-5.3 Codex Spark route and reconciliation
with Agent Team. This is personal installed Skill maintenance, without a public
package release or provider-backed Yao evaluation.

Canonical policy: `../SKILL.md`. Global discovery: `~/.codex/AGENTS.md`.
Execution procedure: the installed `orchestrate-parallel-work` Skill.
The configured controller, credentials, permissions, hooks, and providers remain
outside the behavioral change. No user-owned tasks or automations are created.

## Completion criteria

- Global instructions load one canonical controller/executor policy.
- Skill and temporary orchestration rules agree on delegation and constraints.
- Model and effort are selected separately; fixed custom roles are respected.
- Spark completes useful bounded work through a supported runtime.
- A fresh session checks policy discovery and the native Spark role if installed.
- Existing regressions and focused Skill checks are reported accurately.

## Observed Spark CLI execution

On 2026-09-05, Codex CLI 0.153.4 executed an ephemeral read-only task using
`--model gpt-5.3-codex-spark -c model_reasoning_effort=low` with the explicit cwd
a maintainer-local test workspace. The runtime header reported Spark, OpenAI provider, read-only sandbox,
and low effort. The task read the actual installed implementation-lanes.md and
identified its Luna/Terra fixed-role statements. The process exited 0.

This is runtime configuration and successful execution evidence, not an
independent attestation of the backend model implementation. The worker's
suggestion to override pinned role settings was rejected by the controller;
generic supported role overrides are the correct adaptive-effort route.

The runtime omitted unsupported `priority` service tier automatically. Existing
MCP initialization warnings and a Skill-description budget warning did not
prevent this bounded file task. No MCP credentials were inspected or changed.
No latency, price, quality, or token-efficiency comparison was established.

## References examined

- User-global AGENTS.md and existing Agent Team AGENTS.md / MEMORY.md.
- Agent Team implementation lanes, supervision, task-type routing, and completion rules.
- Orchestrate Parallel Work and Yao Meta Skill authoring/target/mode rules.
- [Official subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- Installed CLI help and current callable tool schemas.

## Configuration and local verification

The installed `~/.codex/agents/spark-worker.toml` defines `spark_worker` with
model `gpt-5.3-codex-spark`. It does not pin reasoning effort or change sandbox,
approval policy, or provider. Global config.toml and existing roles were not
modified. Python TOML parsing, both Skills' native `agents/openai.yaml`
interfaces, frontmatter, unique global route, and global memory checks passed.

Existing regressions: 92 tests ran; 90 passed, 1 skipped, and 1 errored because
the pre-existing external v0.1.0 fixture is absent. This is not a fully green
suite. No runtime Python code changed in this task.

Yao's generic package validator expects `agents/interface.yaml`, whereas this
installed Codex Skill uses native `agents/openai.yaml`; its check failed on
that pre-existing format mismatch. The generic resource check also failed its
1,000-token entry budget (roughly 2,210 estimated tokens). These are recorded
maintenance limitations, not evidence that native runtime loading failed.
No duplicate interface or unrelated package migration was introduced.

## Final runtime verification

A fresh ephemeral GPT-6 Astra CLI session loaded Agent Team 0.5.0 and observed
the native `spark_worker` type in its live tool declaration. It used native
`spawn_agent` with `agent_type: spark_worker`, `reasoning_effort: low`, and
`fork_turns: none`. The resulting `/root/spark_config_acceptance` child read
the actual role file and returned its field inspection; the parent observed
completed status and independently checked the result. The fresh parent used
no nested CLI fallback to implement that spawn. The outer acceptance process
exited 0.

The fresh parent also verified the installed global route, loaded the updated
Skill, and confirmed controller ownership of model selection, analysis, and
acceptance with bounded worker implementation. It found one outdated Spark
availability sentence; the controller replaced that sentence with the native
role and verified fallback instructions after acceptance.

Native dispatch receipts exposed no effective model or effort fields, so both
remain `unknown`; the fixed role declaration and requested effort are separate
facts. Read-only native execution is verified. Writable Spark work and hot
reload of the already-running desktop conversation were not exercised.

Focused local trigger checks finished at 10/10 (4 positive, 3 negative,
3 near-neighbor). They are heuristic fixtures, not empirical model routing
benchmarks. Native TOML/YAML/frontmatter and global-route checks passed.

Outcome (scope corrected after adversarial audit): persisted instructions and
the explicitly requested read-only Spark route were verified. This run did not
verify automatic routing for an ordinary new-session request or writable Spark
execution. The prompt named the role, effort, and Skill, so it cannot serve as
blind global-policy acceptance. See evals/native-routing-cases.json for the
separate native acceptance contract; follow-up results must be recorded before
claiming that broader workflow is verified.
The pre-existing generic-validator and missing-fixture limitations above remain
disclosed. No independent security review was required: this change adds no
permission, credential, provider, persistence, or external-action capability.

## Audit follow-up: root-only execution routing, version 0.5.3

The user authorized fixing the audit findings. Global loading is now mandatory
for substantive root execution requests, independent of catalog keywords.
Parent-assigned executors remain executors on fresh or resumed turns and may
not self-promote or redelegate without an exact root grant. Before implementation,
root dispatches bounded work or states a genuine runtime/authority/dependency
exception. After dispatch, all independently bounded implementation belongs to
executors; root's parallel work is analysis, control, and validation.

The exact ordinary Chinese prompt is preserved in `../evals/native-routing-cases.json`.
No model, Skill, team, or delegation instruction was included in that prompt.
The input project was explicitly labeled a **file-backed fixture**. Frozen
tests and metadata were stored outside the executor workspace. The same
original defects were restored in separate directories for each attempt;
earlier evidence was preserved without overwriting it.

| Run | Code outcome | Routing outcome |
| --- | --- | --- |
| Attempt 1 / 0.5.1 | Seven tests passed, frozen files preserved | Failed: root directly implemented both fixes without a stated exception |
| Attempt 2 / 0.5.2 | Seven tests passed, frozen files preserved | Failed: root delegated sorting but implemented counting itself |
| Attempt 3 / 0.5.3 | Independent outer run passed all seven tests; only two authorized source files changed | Passed with trace limitations: root assigned both fixes to one executor, reviewed tests/CLI concurrently, and native collaboration waits were observed |
| Ordinary Q&A | Correct one-sentence HTTP 404 answer | Passed: no tool or agent-dispatch items; unchanged Q&A exemption |

The native attempt 3 process exited 0. Task Guard completed with two separate
file scopes, no pending scope deltas, and no human gates. A malformed combined
scope argument was rejected during execution and corrected through the normal
contract operation. The subsequent supervision note documents the verified
repeated-argument syntax; it does not change routing or permission semantics.

The independent reviewer first accepted the root/executor and ordinary-entry
repairs, then separately checked the new root-implementation counterexample.
The final focused rule review found no blocker; it did not substitute for the
outer runtime and file-integrity checks.

Source artifacts remain in a maintainer-local evidence directory (not shipped): the original
baseline, per-attempt baseline hashes, native traces, `attempt-1-result.json`,
`attempt-2-result.json`, `attempt-3-result.json`, and `question-result.json`.
All routing inputs stayed unchanged during attempt 3. Afterward, an unrelated
project-context paragraph in global AGENTS.md changed; an in-memory replacement
of that paragraph reproduced the frozen whole-file hash exactly. That concurrent
change was preserved. Other policy file hashes matched directly.

**Accepted outcome:** both audit findings are repaired, and the ordinary-entry
workflow has bounded native acceptance. **Limits:** this is not a production
project, statistical reliability guarantee, or efficiency comparison. The native
trace does not expose every child tool call or attest effective worker model
and effort. Existing missing-fixture and generic-validator limitations remain
as disclosed above. Catalog keyword checks still pass 10/10, but they are
explicitly separate from this native acceptance.
