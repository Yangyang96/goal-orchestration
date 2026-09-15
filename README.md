# Goal Orchestration

Goal Orchestration makes useful subagent delegation an explicit preference for complex
project work. It adds delegation decisions, shared-resource coordination and recovery
details to the user's AGENTS.md and Codex instructions.

This Skill activates only when the user explicitly chooses it, such as by invoking
`$goal-orchestration`. Automatic invocation is disabled.

When invoked, the main Agent looks for a concrete delegation opportunity and dispatches
it when saved elapsed time or independent scrutiny justifies the overhead. There is no
Agent quota. Small or tightly coupled work can stay local with a brief explanation.

## Design

The [entry contract](skills/goal-orchestration/SKILL.md) covers delegation selection,
handoff interfaces and integration. It loads conditional details:

| Need | Contract |
|---|---|
| Handoffs across contexts or runtimes | [Recovery](skills/goal-orchestration/references/state.md) |
| Concurrent writers or worktree isolation | [Coordination](skills/goal-orchestration/references/coordination.md) |

General autonomy, authorization, task persistence, Git delivery and state-file policy
remain in the user's AGENTS.md and Codex instructions. The skill does not duplicate
them or provide a standalone execution runtime.

## Install or Update

From the repository root, synchronize the packaged skill into the current user's
Codex skill directory:

```sh
skill_target="${CODEX_HOME:-$HOME/.codex}/skills/goal-orchestration"
mkdir -p "$skill_target"
rsync -a --delete skills/goal-orchestration/ "$skill_target/"
```

`--delete` removes obsolete files only inside this skill's target directory, which is
required when an update removes or renames a reference. Back up intentional local
edits in that directory before synchronizing.

## Use

```text
Use $goal-orchestration for this migration. Delegate independent work that helps
finish sooner or provides useful independent scrutiny, and integrate the results.
```

## Verify

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s skills/goal-orchestration/tests -v
```

These checks validate package structure and reference integrity, not model behavior.
The skill has no external runtime dependency. Maintainer evaluations under
`evaluations/` are not loaded by the skill; dated records describe their evaluated
revision, not current execution rules.

The [2026-09-07 Astra controlled pilot](evaluations/astra-benchmark/REPORT.md)
compared native execution and two historical Skill revisions. Native Astra and the
then-new revision completed all six primary tasks and both handoff cases; the older
revision missed one required local commit. This small pilot found no completion-rate
advantage over native Astra and disabled subagents in the executing model. It does not
measure the benefit of delegation or validate the current revision. Resource
measurements, retained failures, and scope limits are in the report.

## License

MIT
