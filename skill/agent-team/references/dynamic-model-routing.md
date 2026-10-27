# Dynamic Model Routing

Goal: reduce model usage while meeting correctness and delivery requirements.
This is the user's selection policy, not a measured savings or quality claim.
An explicit user model choice takes precedence. Model choice is separate from
team topology, authority, review requirements, and acceptance.

## Default: GPT-6.1 Terra

Use `gpt-6.1-terra` for factual lookup, extraction, summaries, translation,
editing, format conversion, well-defined operations with observable results,
localized fixes with known causes, small features following existing patterns,
configuration changes, routine browser work, screenshot interpretation, and
file organization. Long tasks and many files do not by themselves imply
complexity. First obtain evidence through search, official documentation, logs,
or tests when those can settle the question directly.

## Escalate: GPT-6.1 Sol

Use `gpt-6.1-sol` when any of these signals is present:

- Multiple plausible explanations compete and existing evidence cannot settle
  the root cause.
- Interactions between modules require tracing a complete causal chain.
- Architecture tradeoffs, concurrency, state consistency, data integrity, or
  complex compatibility require judgment.
- Requirements materially conflict and several constraints must be reconciled.
- Complex derivation, rigorous argument, or subtle logical defects are central.
- Terra has made two repair attempts based on different evidence and validation
  still fails. Repeating an unchanged attempt does not count as new evidence.
- New evidence overturns the original judgment and continuing the plan could
  expand the problem.

If a signal is present initially, start with Sol. Do not require Terra to fail
first. Record actual attempts and results in existing task evidence, without
creating a new process solely to count attempts.

## Separate external blockers

Missing permission, credentials, required files or user-only information;
unavailable networks or services; missing dependencies; and unsupported tool
operations are external blockers. Resolve or obtain an authorized alternative
for the actual blocker. Model escalation is not a retry strategy for them.
Never request or transfer unnecessary secrets.

## Handoff and return

Pass only the goal and acceptance criteria; relevant files, modules, and
environment versions; confirmed facts, errors, and key evidence; attempted
methods, validation results, and excluded causes; and the exact unresolved
problem for Sol. Preserve critical constraints and original evidence; omit
unrelated history and unnecessary sensitive data.

Sol resolves the root cause, key decision, or complex part. Once remaining
work is specified and readily verifiable, return routine implementation,
checks, documentation, and delivery notes to Terra. Avoid rapid switching for
a short finish: the current model completes it when handoff costs more than
the remaining work. Preserve single-writer ownership across each handoff.

## Runtime execution and reporting

Inspect live capabilities. When supported and authorized, select the exact
model through the exposed switch or task-routing mechanism. Existing child
contexts cannot be assumed to change models through a follow-up message.
Delegation requires its own authority and useful bounded outcome; a model
preference alone never authorizes spawning children or user-owned tasks.
Executors report escalation evidence to ROOT rather than self-dispatching.

Do not override roles with pinned models. The name `terra_worker` does not
establish GPT-6.1 Terra availability. Use an unpinned supported role for exact
model requests; follow implementation-lanes.md for delegated execution.
Do not silently substitute an older model or change global configuration.

When the environment cannot perform a needed switch, report only then:
"建议切换至 Sol：〔具体原因〕。" or
"难点已解决，可切回 Terra 完成后续工作。"
Do not claim a switch, including a return to Terra, without runtime evidence.
Requested model and effective model are distinct; missing attestation stays
unknown. Do not output routine routing analysis or repeatedly ask for model
confirmation. Regardless of model, answer from evidence and verify the final
result against the user's acceptance criteria.
