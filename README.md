# Goal Orchestration

Goal Orchestration supports GPT-6 Astra with clear outcomes, persistent authorization,
proportionate verification, and optional coordination for complex project work.
It leaves implementation choices to the model within the user's scope.

This Skill activates only when the user explicitly chooses it, such as by invoking
`$goal-orchestration`. Automatic invocation is disabled.

Explicit invocation applies without forcing Agents, worktrees,
state files, or commits. Focused work stays local; concurrent writers, recovery across
tasks or runtimes, and sustained repair use only the controls they need.

## Design

The [entry contract](skills/goal-orchestration/SKILL.md) defines autonomy, clarification,
approval, delegation, verification, and completion. It loads conditional controls:

| Need | Contract |
|---|---|
| Recovery across tasks/runtimes or unattended waves | [Durable state](skills/goal-orchestration/references/state.md) |
| Concurrent writers or worktree isolation | [Coordination](skills/goal-orchestration/references/coordination.md) |

The main Agent owns scope and final acceptance. Routine reversible choices proceed
without confirmation. Questions are reserved for consequential unresolved choices or
actual authorization boundaries, using decisions and permissions already given.
Repairs continue with new evidence, within scope and user limits; there is no fixed
retry-count approval gate. Accepted milestones lead to the next required step until
the complete requested outcome is integrated, verified, and delivered.

Git and external delivery actions follow existing user authorization.
Skill invocation alone does not authorize them.
Configured model and reasoning settings are preserved. This is an instruction design
for capable models, not a claim of measured model-specific performance gains.

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
Use $goal-orchestration to implement this migration with concurrent writers,
preserve my dirty changes, and keep the work resumable.
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
compared native execution, the previous Skill, and this revision. Native Astra and
this revision completed all six primary tasks and both handoff cases; the previous
Skill missed one required local commit. This small pilot found no completion-rate
advantage over native Astra. Use the Skill selectively for coordination needs;
resource measurements, retained failures, and scope limits are in the report.

## License

MIT
