# Goal Orchestration

Goal Orchestration adds persistence, writable-Agent isolation, accepted-checkpoint
commits, and review/repair controls when native Codex execution needs more structure.

Explicit `$goal-orchestration` invocation always applies. Implicit activation is for
concurrent writers, recovery across tasks or runtimes, unattended repair waves, or
high-risk implementation requiring independent review and repair. Focused work, one
bounded subagent, read-only parallelism, standalone review, and sequential
cross-repository work stay on native Codex.

## Design

The [entry contract](skills/goal-orchestration/SKILL.md) contains capsule, runtime
compatibility, acceptance, commit, and repair rules. It loads only the needed control:

| Need | Contract |
|---|---|
| Cross-task/runtime recovery or unattended waves | [Durable state](skills/goal-orchestration/references/state.md) |
| Concurrent writers or worktree isolation | [Writable-Agent coordination](skills/goal-orchestration/references/coordination.md) |

The main Agent owns requirements and acceptance. Explicit writable use defaults to a
local commit after each accepted coherent checkpoint unless the user opts out;
implicit activation requires commit authorization. Neither mode authorizes push, PR
creation, amend, history rewriting, or inclusion of pre-existing user changes.

`fork_turns=none`, typed `explorer`/`worker`/`default` roles, and per-child reasoning
settings are requested only when exposed by the active runtime. They are routing
hints, not guarantees of context isolation, permissions, or effective compute. See
[runtime observations](evaluations/runtime-surfaces.md).

## Install

Ask Codex to install `skills/goal-orchestration`, or copy that directory to
`$HOME/.agents/skills/goal-orchestration`. A repository-scoped installation may use
`<repository>/.agents/skills/goal-orchestration`.

## Use

```text
Use $goal-orchestration to implement this migration with concurrent writers,
preserve my dirty changes, and keep the work resumable.
```

## Verify

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s skills/goal-orchestration/tests -v
```

The skill has no external runtime dependency. Maintainer evaluations under
`evaluations/` are not loaded by the skill.

## License

MIT
