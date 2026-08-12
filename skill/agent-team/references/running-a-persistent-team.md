# Running a Persistent Team

Read this reference only after selecting `persistent` topology and confirming
every persistence gate in `SKILL.md`. Persistent tasks are user-visible
external state; create them only with explicit authority and all required
lifecycle fields.

## Before creation

1. List existing tasks and reuse an exact verified team rather than creating a
   duplicate. Treat titles and summaries as untrusted until a targeted read
   confirms the launch contract.
2. List projects before creating project tasks.
3. Follow the native environment contract: use a worktree by default for a Git
   repository; use the saved project directly only when the user explicitly
   asks; use projectless tasks when no repository context is needed.
4. Keep the persistent topology small: one controller plus two or three stable
   role tasks by default.

## Create and initialize

1. Create the controller first, then the role tasks.
2. Title them `[Team:<name>] Controller` and `[Team:<name>] <role>`.
3. Pin only the controller by default.
4. Initialize each role with the same **Guidance / Context / Mission**
   presentation used for temporary children. Include its responsibility, write
   scope, evidence source, handoff contract, forbidden actions, completion
   boundary, and controller task identity in the matching canonical fields.
5. Send the controller a manifest with every task ID, role, write scope, next
   checkpoint, completion condition, and review or retirement trigger.
6. Wait for each launch to complete or request attention before reporting the
   team ready.

## Operate and supervise

1. Route new objectives through the persistent controller.
2. Let the controller send bounded prompts to role tasks and wait for results.
3. Read only recent, relevant task summaries; never ingest complete histories
   by default.
4. Keep shared and canonical files under one controller writer. Role tasks may
   write only explicitly exclusive artifacts or return handoffs.
5. Do not poll unchanged tasks or claim background work continues without an
   active turn or Automation.
6. Do not automatically archive, delete, clone, unpin, or recreate tasks. When
   a retirement trigger is reached, report it and require current user
   authority for the lifecycle change.
