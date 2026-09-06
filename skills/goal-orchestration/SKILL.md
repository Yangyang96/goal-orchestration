---
name: goal-orchestration
description: "Use only when the user explicitly invokes goal-orchestration. Coordinate complex Codex development requiring concurrent writer ownership, worktree isolation, recovery across tasks or runtimes, or sustained implementation and repair."
---

# Goal Orchestration

Activate only when the user explicitly chooses this Skill.

Support GPT-6 Astra's judgment with clear outcomes, authority, and evidence. Use only
controls that help finish the requested project work; invocation alone requires no
Agents, state files, worktrees, commits, or model-setting changes.

## Outcome And Authority

Infer the outcome, constraints, non-goals, and observable acceptance from the user's
request and project context. Keep a concise plan only when dependencies or duration
justify it. Choose implementation details autonomously within that scope; do not add
features, abstractions, migrations, or process unless needed for the outcome.

Carry forward the user's decisions and authorization across turns. A status question
or correction normally steers ongoing work; it does not cancel unfinished work.
Update the outcome when the user changes it, without silently weakening acceptance.

Distinguish missing information from missing permission:

- Clarify only when available context cannot resolve a choice that materially changes
  the outcome, public contract, scope, or reversibility. For ordinary reversible
  choices, use project conventions and proceed; state consequential assumptions.
- Ask for approval only at an actual authorization boundary under applicable user,
  project, or runtime rules. Reuse existing authorization; neither Skill invocation
  nor a retry count adds or removes it. Before asking, complete authorized preparation
  so the proposed action is concrete and reviewable.
- Ask the smallest necessary question, identify what depends on it, and continue
  independent authorized work. Silence is not an answer to a required question.

## Select Controls And Delegate

Keep focused or tightly coupled work local. Delegate when a bounded independent
workstream improves speed or quality, including a useful independent review. The main
Agent owns scope, shared contracts, integration, and final acceptance; implementers
may make local design decisions within their assigned contract.

Read only the relevant reference when needed; refresh it if changed or unavailable
in the current context:

| Need | Reference |
|---|---|
| Recovery across tasks/runtimes or unattended waves | [Durable state](references/state.md) |
| Concurrent writers or worktree isolation | [Coordination](references/coordination.md) |

Give each Agent enough authoritative context to decide correctly:

```text
TASK: outcome, constraints, non-goals
SCOPE: owned paths, shared interfaces, dependencies; other writers must be preserved
ACCEPT: observable conditions; known focused checks
CONTEXT: relevant decisions, authorization limits, facts, artifact paths
RETURN: result, changes, validation (check / covered artifact / result), unresolved work
```

Use available roles and context controls only when useful. Preserve the configured
model and reasoning settings unless instructed otherwise. Context trimming must not
omit relevant decisions or authorization limits; tool availability does not expand
permissions. Reviewers inspect without modifying the implementation.

## Verify And Continue

Inspect delegated changes and supporting evidence before accepting them. Reuse valid
checks for unchanged artifacts and relevant inputs; run the smallest missing or
affected checks, including combined integration checks where needed. Do not rerun
checks merely because another Agent ran them. Add independent review where requested
or where concrete consequences or uncertainty justify it; do not make every unit pass
through a review ceremony. Inspect an unproven shared contract before scaling it.

Reuse an implementer while context remains useful. On failure, preserve accepted work
and revise the hypothesis using the failed evidence. Continue while a justified next
step can advance the outcome within scope and user limits. Repeated identical failure
calls for diagnosis or a different approach, not a fixed-count approval gate or task
split to reset retries. If no productive authorized step remains, describe the actual
blocker and minimum input needed; finish unaffected work first.

Keep returns concise, but retain evidence, blockers, and unmet acceptance. Review
findings should name the affected artifact, consequence, and actionable correction;
state limitations when verification is incomplete.

## Finish The User's Task

An accepted unit, Agent return, checkpoint, or local commit is progress. Continue to
the next required step until the requested outcome is integrated and verified.
Completion requires all in-scope acceptance conditions to be met, relevant checks to
pass, and required delivery actions to succeed. A blocked check or delivery step is
unfinished work; report it explicitly rather than claiming completion or ending with
an offer to do already-authorized work.

Commit, push, PR, and deployment actions follow the user's request and existing
authorization, regardless of how this Skill was activated. Prepare and perform them
when authorized and required; otherwise a reviewed working-tree change can be the
complete deliverable. Include only attributable task changes; keep orchestration
state out of product commits unless the project intentionally versions it. Report a
failed optional checkpoint and continue; a failed required delivery remains pending.

Finish with the outcome, decisive validation, and any remaining limitations or
required user action. Remove disposable artifacts created by this task when they are
no longer needed, preserving user work and recovery evidence for unfinished work.
