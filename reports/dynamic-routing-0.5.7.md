# Dynamic routing 0.5.7 validation

## Accepted behavior

The policy defaults to GPT-6.1 Terra and selects GPT-6.1 Sol for the seven
explicit complexity or failure signals. External blockers are separated from
reasoning failure. Handoffs carry only relevant constraints and evidence.
Routine work returns to Terra when worthwhile; a short finish avoids another
handoff. Explicit user model choices and live runtime support take precedence.

The existing GPT-5.6 worker profiles retain their legacy identities. The default
install instructions no longer install them as if they were GPT-6.1 routes.
No Python behavior, global agent configuration, or permission boundary changes.

## Instruction evidence

An independent native read-only probe applied the same dynamic routing policy
to 17 cases before source publication. Requested model: gpt-6.1-terra, medium
effort, default role, no inherited history. Dispatch returned a task identity,
but no effective-model attestation; actual identity remains unknown.

| Cases | Expected and observed interpretation |
| --- | --- |
| Bulk fixed-format translation; proven local typo | Terra; volume alone is insufficient |
| Competing roots; cross-module concurrency; material conflicts; formal proof | Sol |
| One failed repair with useful new evidence | Terra unless another signal appears |
| Two distinct-evidence failed repairs | Sol |
| Two identical retries | Stop repetition; not two distinct-evidence attempts |
| Permission or network failure | Resolve external blocker |
| New evidence invalidates a potentially damaging plan | Sol |
| Root cause solved with substantial mechanical work left | Return to Terra |
| Two-sentence finish | Current model finishes |
| Explicit other-model choice | Follow supported user choice |
| Only an old pinned Terra role, Sol needed | No silent substitution or false switch |
| Weekly persistent-team preview | Plan only; no created agents/tasks/automations |
| Product preview-button repair | Ordinary direct route |

The controller checked these interpretations against the source policy.
The source retains the repository entrypoint's existing collaboration boundaries;
the new model-routing section matches the validated installed section.
Historical model reports remain historical, not current routing instructions.
This is instruction-level evidence, not a quota-saving benchmark or proof that
the active session can automatically change its model.

## Regression

The installed package's unchanged Python contracts passed 109 tests
(106 passed, 3 Windows/environment skips) on 2026-10-27. Repository validation
and remote CI are checked separately for this source change before integration.

The repository suite found one outdated worker-documentation assertion requiring
the retired matrix. The updated test retains pinned-profile and authority
assertions and checks the new policy link and exact model IDs. Its two focused
tests pass; the other repository cases had no failures. Skill metadata and
whitespace checks pass. Remote CI remains the branch integration gate.
