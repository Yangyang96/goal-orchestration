---
name: goal-orchestration
description: "Orchestrate Codex development that needs controls beyond native execution: concurrent-writer ownership or isolation, cross-task recovery, shared-contract integration across Agents or repositories, unattended multi-wave repair, or high-risk independent review with repair. Explicit invocation always applies. Do not use for focused work, one bounded subagent, ordinary same-task Goals, independent read-only parallelism, or simple sequential cross-repository work."
---

# Goal Orchestration

## Objective

Maximize accepted work per unit of time and context. Add controls only for concrete
risks. Activation creates no files.

## Activation Boundary

Apply when explicitly invoked. Otherwise activate only when native execution lacks a
control the task actually needs:

- concurrent writers require ownership boundaries or worktree isolation;
- state must recover across a task or runtime boundary;
- multiple Agents or repositories share a contract and require an integration gate;
- unattended work requires multiple checkpoint-and-repair waves; or
- high-risk implementation requires independent review followed by enforced repair.

Durable, parallel, unattended, cross-repository, and high-risk are signals, not
triggers by themselves. Do not activate for focused work, one bounded subagent,
ordinary same-task Goals, independent read-only parallelism, simple sequential
cross-repository work, or a standalone review; use native Codex.

## Load Minimally

- Read `references/unattended.md` after activation.
- Add `references/coordination.md` only for concurrent writers or isolation.
- Add `references/returns.md` only when a direct return cannot fit or cross context.

Do not reload a reference in unchanged context. The ordinary path requires
only this file plus `references/unattended.md`.

## Route Work

Label each delegation candidate:

- **Independent:** no unstated main-Agent decision.
- **Parallelizable:** main can continue useful, non-overlapping work.
- **Local:** bounded scope, acceptance, and verification.

Keep the critical decision chain in the main thread: work that determines the next
action, resolves requirements or architecture ambiguity, or integrates acceptance
evidence. Even if independent and local, do not delegate when dispatch would leave
the main Agent waiting. Delegate work satisfying all three labels and continue
non-overlapping critical-path work. Exceptions require user request or a concrete
subagent capability advantage; the main Agent still owns the consuming decision.

## Shared Execution Rules

- Resolve root from user path, project, then cwd; never silently use a nested repo.
- Reach the first useful project action after at most one orchestration-only step.
- Use Codex built-ins; never create custom Agent configuration automatically.
- If supported, set `fork_turns=none`; it limits turns, not bootstrap context.
  Otherwise make the capsule authoritative and tell the subagent to ignore unrelated
  inherited context. Context control is never a security boundary.
- Use high reasoning in the main thread for critical decisions. Use medium for
  routine delegated work and high for complex delegated work. Raise the main thread
  above high only for unresolved cross-boundary ambiguity, contradictory evidence,
  or a high-consequence security, migration, concurrency, or release decision. A
  fresh `default` reviewer must not write; hard read-only needs a user-configured
  sandbox or custom Agent.
- The main Agent alone accepts work; subagent `DONE` is evidence.
- Prefer bounded direct returns; use an inbox pointer only for the cross-context trigger.

## Conditional Controls

| Trigger | Add only this control |
|---|---|
| Work must survive another turn or run unattended | Three small state files described in `unattended.md` |
| Concurrent writers or high-risk isolation | Ownership map and sibling worktrees from `coordination.md` |
| Scoped paths are already dirty | Capture scoped status/diff before dispatch |
| Return cannot fit directly or may cross context | Pointer return from `returns.md` |
| Security, migration, shared contract, concurrency, or release risk | One consolidated independent review |
| User supplies a token budget | Track a coarse remaining estimate at accepted checkpoints |
| Explicit Goal commit authority; attributable paths | Commit accepted wave |

These controls are independent. Activation does not imply all of them.

## Cost Guardrails

Capsules are at most 400 words. Return limits: routine 1,200 Unicode characters;
complex/reviewer 1,800; context/blocker 600. Run at most three concurrent Agents and
one consolidated reviewer per risky boundary. After one implementation dispatch,
allow at most three focused repairs; a fourth requires approval or a task split.

Do not perform exact token accounting by default. Avoid repeated context, duplicate
reviews, duplicate checkpoints, and controls costlier than the failure they prevent.

## Acceptance

Inspect actual changes, preserve pre-existing work, and run the smallest decisive
verification. For repair, reuse the implementer and send only new findings plus
changed acceptance evidence. Do not re-bootstrap, replay history, or add a repair mode.

For durable work, apply accepted-wave autocommit from `unattended.md`, then checkpoint
once after acceptance or before a real pause. At accepted milestones, apply its soft
context-refresh rule; counts trigger assessment, never forced reset.
Conclude with the result, verification, residual risk, and executable next action.
