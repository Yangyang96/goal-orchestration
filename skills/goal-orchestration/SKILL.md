---
name: goal-orchestration
description: "Orchestrate Codex development when concurrent writers need ownership or worktree isolation, work must resume across tasks or runtimes, unattended repair spans multiple waves, or high-risk implementation needs independent review and repair. Explicit invocation always applies. Use native Codex for focused work, one bounded subagent, read-only parallelism, standalone review, or sequential cross-repository work."
---

# Goal Orchestration

Add only the missing controls. Activation alone creates no files or authority.

## Select Controls

Read each triggered reference once:

| Need | Reference |
|---|---|
| Cross-task/runtime recovery or unattended waves | `references/state.md` |
| Concurrent writers or requested worktree isolation | `references/coordination.md` |

Keep requirements, architecture choices, next-action decisions, and final acceptance
in the main thread. Delegate only scoped, verifiable work while the main Agent can
continue non-overlapping work. Inspect the first artifact before scaling an unproven
pattern or shared contract.

## Dispatch

Give each Agent an authoritative capsule:

```text
TASK: outcome and non-goals
SCOPE: writable or read-only paths
ACCEPT: observable conditions and exact focused checks
CONTEXT: task-local facts and paths only
RETURN: RESULT; CHANGED; VALIDATION = check | covered paths/artifact | result; RISKS/NEXT if relevant
```

Before writable dispatch on dirty scoped paths, capture relevant status and diff.
Default to sequential work; read `coordination.md` before concurrent writes.

When supported, request `fork_turns=none`; it is a history preference, not isolation,
an empty-child guarantee, or a security boundary. Otherwise rely on the capsule and
tell the child to ignore unrelated inherited context.

When exposed, use `explorer` for investigation, `worker` for implementation, and a
new `default` Agent for independent review; otherwise use a generic Agent. Request
child reasoning only when supported; otherwise inherit the runtime setting. These
options route work but do not prove permissions or effective compute. A reviewer must
not write; hard read-only requires a user-configured sandbox or custom Agent.

## Accept, Commit, And Continue

Keep direct returns within 1,200 characters. Point to task artifacts when detail does
not fit. Reviewers return actionable `P0..P3 path:line | issue | correction` findings,
or `PASS`.

Agent returns are claims. The main Agent alone inspects changes, preserves pre-existing
work, runs the smallest decisive check, and accepts. Reuse evidence only while its
covered artifact and relevant inputs remain unchanged; otherwise rerun the smallest
affected check. Use one consolidated reviewer at a risky shared seam.

Explicit writable invocation defaults to one local commit after each accepted coherent
unit unless the user opts out. Commit only attributable task paths after the decisive
check, with the repository usable; exclude `.agent/**` and pre-existing user changes.
Implicit activation commits only with user authorization. Never push, open a PR,
amend, or rewrite history without explicit authorization. If attribution is unsafe or
commit fails, preserve the changes and report the skipped checkpoint.

Reuse the implementer while task and scope stay stable, including later waves and
repairs. Send only the failed evidence and correction needed. Keep accepted work and
allow three focused repairs per active unit; a fourth needs approval or a task split.
Start a new Agent only when task, ownership, expertise, architecture/shared contract,
or review independence changes.
