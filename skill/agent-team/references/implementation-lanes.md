# Runtime-aware implementation lanes

Use these lanes only when runtime provenance identifies the current agent as
`ROOT` and Agent Team has authority for temporary native
delegation and the controller has frozen the objective, ownership, interfaces,
constraints, and verification. The ROOT controller owns analysis, planning,
scope, integration, review selection, and final acceptance. Read this reference only for an authorized delegated implementation scope.
Direct execution needs no lane selection. Delegate only for concrete independent
benefit alongside useful controller work.

A bounded parent assignment is `EXECUTOR`, including with `fork_turns: none`.
An executor does not use this policy to select a model, change effort, dispatch
another agent, create a task or Automation, or invoke a helper or CLI fallback
to bypass that boundary. It never promotes itself to `ROOT`. It executes the
controller-selected assignment and returns evidence. An exact root grant
permits only named-scope subdelegation; the original controller remains `ROOT`.

Each dispatched executor owns only its assigned files and deliverable.
Keep one writer per file or shared state. ROOT may implement a disjoint
owned scope while retaining analysis, validation and final acceptance.

## Preflight and authority

Inspect live tool declarations for callable agent types, supported models,
reasoning efforts, inheritance rules, and any pinned roles. They are
authoritative for the current host. Do not create filler work, user-owned
tasks, persistent tasks, or Automations to make a team look busy.

For a generic runtime-supported role, prefer `agent_type: bounded_executor`
when exposed, otherwise use `agent_type: default`. Both are policy-scoped,
not native-tool or operating-system isolation. Use
`fork_turns: none`, and the controller-selected supported `model` and
`reasoning_effort`. `fork_turns: none` is required for a bounded assignment.
Custom roles can pin their model and effort: do not override them. Inspect
their current declarations; choose an unpinned supported role when a pinned
role cannot satisfy the requested GPT-6.1 model.

The bundled `luna_worker` and `terra_worker` profiles remain optional legacy
GPT-5.6 roles with pinned maximum effort. They are not GPT-6.1 aliases and are
used only for explicitly selected compatible legacy workflows.

Record `agent_type`, `requested_model`, `requested_effort`, and
`selection_reason` in Mission. After dispatch, record identity evidence
separately as `effective_model` and `effective_effort`; use `unknown` when the
runtime does not attest them. A request or accepted dispatch is not identity
evidence.

Keep dispatch parameters, returned task identity, observed runtime fields,
verification output, and their source locations in the same task's existing
Mission or evidence record. Do not fill unavailable model/effort fields from
configuration or worker self-identification, and do not infer a complete child
tree from a CLI trace that omits collaboration events. Claims about execution
attribution must remain partial when those receipts are missing.

On the configured 2026-09-05 host, `multi_agent=false` did not reliably remove
native collaboration tools; a direct invocation with that flag successfully
created a probe child. Disabling `code_mode_host` also broke local reads without
blocking that call. Do not use these flags as an isolation guarantee or weaken
the working tool setup to simulate one. If native-call prevention is a required
acceptance criterion, keep that criterion blocked until the host exposes and
verifies a working restriction. See
[reproduction evidence](../reports/runtime-boundary-repro.md).

If an otherwise useful action has no runtime-supported child lane, needs
controller-only authority, or has a hard dependency that prevents lawful child
execution, disclose that narrow constraint and keep the smallest necessary step
local. Do not turn that constraint into a reason to broaden authority or invent a fallback.

## Model selection and effort

Use [dynamic model routing](dynamic-model-routing.md) as the current selection
policy: GPT-6.1 Terra by default, GPT-6.1 Sol for its explicit escalation
signals, and a return to Terra for worthwhile routine follow-through. An
explicit user model choice takes precedence. Earlier Spark/Luna/Sol/Terra/Astra
matrices in historical reports are not current routing instructions.

Live declarations control supported model IDs and effort levels. Preserve the
configured effort unless the bounded task justifies a supported adjustment;
never infer maximum effort from length, file count, model name, or role name.
Do not claim measured usage savings from the policy alone.

## Dispatch and fallback

For ROOT, native delegation is preferred when authorized and independently
useful. Use an unpinned supported role to request gpt-6.1-terra or gpt-6.1-sol.
Never substitute a pinned GPT-5.6 worker merely because its role includes Terra.
An executor reports a newly discovered escalation signal to ROOT with the
compact handoff in dynamic-model-routing.md; it cannot switch or redispatch
itself. A reassignment retains exact scope and single-writer ownership.

A CLI or custom-agent fallback requires an explicitly supported route at
dispatch time, the task cwd, and the same project, security, write-scope, and
human-gate restrictions. It must not create a user-owned task, bypass child
limitations, alter global configuration, weaken sandboxing, or imply an
unattested model identity. Historical Spark probes are not present-day
availability guarantees. If no supported route exists, follow the dynamic
routing policy's switch guidance without repeated model retries.

## Escalation and acceptance

Never repeat an unchanged failed assignment. Inspect failure evidence and
separate external blockers from reasoning difficulty. Two Terra repairs based
on distinct evidence that still fail validation trigger Sol; an earlier
complexity signal triggers Sol immediately. This supersedes the old single
reassignment limit; it does not authorize unlimited retries. Return unresolved
work and evidence to ROOT, which owns the next decision and final acceptance.

Model selection never activates independent review. Apply the existing named
residual-risk gate after deterministic verification. A required reviewer keeps
a separate scope; model diversity alone is not verification.
