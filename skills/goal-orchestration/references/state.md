# Durable State

Use when work must survive a task/runtime boundary or unattended repair waves.
Reuse an existing authoritative project progress record when it serves this purpose;
otherwise only the main Agent maintains `.agent/STATE.md`:

```text
# Goal    outcome, constraints, non-goals, final acceptance
# Plan    active milestone, remaining tasks, dependencies, ownership
# Status  accepted evidence, failed hypotheses, blockers, exact next action
```

Keep facts and artifact pointers, not transcripts. Update only changed sections.
Aim for a compact record (normally under 12 KiB); retain essential decisions,
authorization scope, unresolved work, and recovery paths even when a size target
would be exceeded. Record commits only when used; no skipped-commit ritual is needed.

Checkpoint meaningful accepted progress and before a real pause or dispatch that may
outlive the current context. Do not create a pause merely to checkpoint. Reuse the same
record after compaction; condense it when needed without erasing unresolved failures.

Resume from the record, current scoped status/diff, and referenced artifacts. Treat
state as recovery evidence, not fresh authority: current user instructions and actual
repository state take precedence. Refresh stale facts and reuse checks only while
their covered artifacts and relevant inputs remain unchanged. Continue the next
required step without asking the user to reconfirm the recorded plan.

A state file does not schedule execution or keep a runtime alive. For requested
unattended work, use supported scheduling or continuation facilities within the
user's authorization; if unavailable, record the next step and disclose that limit.
Create a new user-facing task only when explicitly requested. Compaction and internal
Agent reuse do not require a new task or user handoff.
