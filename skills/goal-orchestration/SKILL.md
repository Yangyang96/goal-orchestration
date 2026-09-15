---
name: goal-orchestration
description: Use when explicitly invoked to find useful subagent work and coordinate parallel implementation or cross-session recovery for a complex goal.
---

# Goal Orchestration

Explicit invocation expresses a preference for useful delegation. Actively look for
work to delegate and dispatch it when the expected benefit outweighs briefing,
waiting and integration costs. Do not impose an Agent count.

## Find useful delegation

- During initial scoping, identify a concrete candidate, what benefit it provides,
  and what useful work stays with the main Agent. If none is worthwhile, give a brief
  reason and proceed locally; reconsider when a dependency or uncertainty changes.
- Favor substantial disjoint implementation lanes, a bounded investigation alongside
  implementation, or an independent review of a consequential assumption or result.
- Keep shared-interface decisions and tightly coupled edits local until a stable
  boundary emerges. A short task whose result blocks all other work rarely benefits
  from dispatch. Judge saved elapsed time or independent scrutiny, not task size alone.

## Coordinate the handoff

Alongside the normal task and file ownership, give each delegate the shared interface
it must preserve, dependency readiness, acceptance evidence to return, and the result
the main Agent will consume. Resolve proposed changes to shared interfaces centrally.

For an independent review, provide the requirements and artifacts before the main
Agent's preferred explanation, so the reviewer can form its own assessment.

Read the relevant reference only when needed:

- [Coordination](references/coordination.md) for concurrent writers or worktree isolation.
- [Recovery](references/state.md) when a handoff may outlive the current context or runtime.

## Integrate the result

Check that returned artifacts satisfy the consumer's interface, not merely the
delegate's local tests. Validate the combined behavior where lanes meet. If a split
creates repeated coordination or rework, merge the dependent lanes instead of adding
more dispatches. Mention material delegation gains or costs in the existing delivery
summary when observed; Agent activity alone is not evidence of benefit.
