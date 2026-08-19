---
name: goal-orchestration
description: "Choose and run a low-overhead development loop: direct main-Agent work, one bounded subagent, or durable/unattended/parallel orchestration. Use for implementation work that may need delegation, resumable milestones, parallel ownership, independent review, or repair continuation while keeping startup time and token cost small."
---

# Goal Orchestration

## Objective

Maximize accepted work per unit of time and context. Add controls only for concrete
risks; activation creates no files.

## Load Minimally

- Fast Path: read `references/interactive.md`.
- Light Delegation: read `references/lightweight.md`.
- Strict Orchestration: read `references/unattended.md`.
- In Strict, read `references/coordination.md` only for concurrent writers or
  worktree isolation.
- Read `references/returns.md` only when a direct return cannot safely fit or survive a
  context boundary.

Do not reload a reference in unchanged context. The ordinary Strict path requires
only this file plus `references/unattended.md`.

## Select Mode Automatically

Evaluate the current independent unit, not the whole repository history.

| Condition | Mode |
|---|---|
| User present; focused task; main Agent can implement and verify | Fast |
| User present; exactly one bounded subagent; one repair is likely enough | Light |
| Unattended/resumable work, parallel Agents, cross-repository coordination, high-risk boundary, required independent review, or Light overflow | Strict |

User choice overrides automatic selection. During an active unit, only upgrade
Fast -> Light -> Strict. After acceptance, select again for the next unit.

## Shared Execution Rules

- Resolve the root from the user path, project, then cwd; never silently switch to a
  nested repository.
- Reach the first useful project action after at most one orchestration-only step.
- Use Codex built-ins; never create custom Agent configuration automatically.
- Spawn subagents with `fork_turns=none`. Give task-local capsules, not chat history.
- Use medium reasoning for routine exploration or implementation, high for complex
  cross-boundary work, and a fresh read-only `default` reviewer with high reasoning.
- The main Agent alone accepts work. A subagent's `DONE` is evidence.
- Prefer direct bounded returns. Use an inbox pointer only for the explicit
  cross-context condition below.

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

These controls are independent. Strict does not imply all of them.

## Cost Guardrails

Capsules are at most 400 words. Routine direct returns are at most 1,200 Unicode
characters; complex or reviewer returns at most 1,800; context/blocker returns at
most 600. Run at most three concurrent Agents and one consolidated reviewer per
risky boundary. Use one initial implementation dispatch plus at most three focused
repairs; a fourth repair requires user approval or a task split.

Do not perform exact token accounting by default. Avoid repeated context, duplicate
reviews, pre/post checkpoints for the same wave, and mechanical controls whose cost
exceeds the failure they prevent.

## Acceptance

Inspect the actual changed surface, preserve pre-existing work, and run the smallest
decisive verification. For a repair, reuse the original implementer and send only
new findings plus changed acceptance evidence. Do not re-bootstrap, replay history,
or create a separate repair mode.

For durable work, apply accepted-wave autocommit from `unattended.md`, then
checkpoint once after an accepted wave or before a real pause.
At accepted milestone boundaries, apply the soft context-refresh rule in
`unattended.md`; milestone or return counts trigger an assessment, never a forced
reset.
Conclude with the result, verification, residual risk, and executable next action.
