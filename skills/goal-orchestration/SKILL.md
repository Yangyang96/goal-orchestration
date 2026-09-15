---
name: goal-orchestration
description: Use when the user explicitly invokes goal-orchestration for complex work needing durable state, coordination, worktree isolation, recovery, or sustained implementation. Do not use for ordinary tasks.
---

# Goal Orchestration

Coordinate complex implementation while keeping scope, authorization, ownership and
completion evidence explicit. Invocation alone does not require Agents, state files,
worktrees, commits or model changes.

## Establish the goal

- State the requested outcome, constraints, non-goals and observable acceptance.
- Keep a concise plan only when dependencies or duration justify it. Use project
  conventions and existing decisions; do not add abstractions or process without a
  concrete benefit.
- Carry user decisions and authorization across turns. A correction or status request
  normally steers unfinished work; it does not cancel it.
- Clarify only when an unresolved choice materially changes scope, public behavior,
  reversibility or authorization. Ask at the actual boundary, after preparing the
  authorized result; silence is not approval.

## Choose controls

Keep focused or coupled work local. Delegate only bounded independent work or a useful
independent review. The main Agent owns scope, shared contracts, integration and final
acceptance; reviewers are read-only.

Read only the relevant reference:

- [Durable state](references/state.md) for recovery across tasks/runtimes or unattended waves.
- [Coordination](references/coordination.md) for concurrent writers or worktree isolation.

Dispatch with a compact capsule:

```text
TASK: outcome, constraints, non-goals
SCOPE: owned paths, interfaces and dependencies
ACCEPT: observable result and focused checks
CONTEXT: decisions, authorization and evidence paths
RETURN: changes, checks, evidence and unresolved work
```

Do not overlap writable paths. Preserve unrelated changes. Tool availability never
expands permission, and configured model/reasoning settings remain unchanged unless
explicitly requested.

## Verify and continue

- Inspect delegated changes and evidence before accepting them. Reuse checks when inputs
  are unchanged; run the smallest missing checks and add integration checks at contract
  boundaries.
- On failure, update the hypothesis from evidence and continue while a productive,
  authorized step remains. Do not use fixed retry counts or task splits to reset retries.
- Keep standards, spec, security and user acceptance findings distinct when reviewing.
- Record actual modifications, validation, failures, blockers and next steps in the
  project's single state entry. Do not rewrite historical evidence.

## Complete

Continue through all required in-scope steps: integrate changes, run relevant checks,
fix failures caused by the task, and deliver the requested result. An accepted unit,
checkpoint or Agent return is progress, not completion. A required blocked check or
required delivery remains unfinished; report it explicitly.

Commit, push, PR and deployment follow the user's request and existing authorization.
Keep orchestration state out of product commits unless the project versions it. Finish
with the outcome, decisive evidence and remaining limitations. Remove disposable test
artifacts while retaining recovery evidence for unfinished work.
