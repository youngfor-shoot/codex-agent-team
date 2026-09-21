# `<task_handoff>` Schema

Every delegated handoff requires normal human-readable Markdown first, then
exactly one fixed `<task_handoff>` block. The block is not inside a code fence,
and no text follows `</task_handoff>`.

## Rules

- Exactly one opening `<task_handoff>` tag and one closing `</task_handoff>`
  tag per handoff; nested or stray tags are invalid.
- Every required field appears exactly once as its own field line inside the
  block; duplicate field names are invalid.
- Field names use lowercase letters and underscores.
- Empty values are `none`.
- The block lives at the end of the handoff; nothing follows the closing tag.
- A field name in surrounding prose or a prefix heading such as `### Missionary`
  does not satisfy the contract.

## Required fields

| Field | Meaning | Example |
| --- | --- | --- |
| `finding_severity` | Highest reported finding severity, or `none` | `none` / `BLOCKER` / `MAJOR` / `MINOR` |
| `goal_alignment` | Whether the executor stayed on the canonical objective | `aligned` / `drifted` |
| `scope_delta` | Any change to approved scope | `none` / description |
| `new_assumptions` | Any assumption not already approved | `none` / description |
| `next_authorized_step` | The next step the executor is authorized to take | `none` / description |

## Example

```text
<task_handoff>
finding_severity: none
goal_alignment: aligned
scope_delta: none
new_assumptions: none
next_authorized_step: none
</task_handoff>
```
