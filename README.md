# Goal Orchestration

Goal Orchestration is an **AI coding agent harness** and **agent skill** for
**OpenAI Codex**. It provides graph-engineered **multi-agent orchestration** for
development that needs coordination, recovery, integration, or review-and-repair
controls beyond native execution while keeping their overhead small.

```text
Ordinary task or one subagent  → Native Codex; do not load this skill
Extra orchestration controls   → Goal Orchestration
```

The skill stays out of ordinary work. It adds Git worktree isolation, persistent
state, independent review, repair continuation, and context recovery only when a
complex task needs them.

## Activation

Explicit `$goal-orchestration` invocation always applies. Implicit activation is
reserved for tasks that actually require one of these controls:

- ownership or worktree isolation for concurrent writers;
- recovery across a task or runtime boundary;
- a shared-contract integration gate across Agents or repositories;
- multiple unattended checkpoint-and-repair waves; or
- independent review followed by enforced repair for high-risk implementation.

Durable, parallel, unattended, cross-repository, and high-risk are only signals.
Focused work, one bounded subagent, ordinary same-task Goals, independent read-only
parallelism, simple sequential cross-repository work, and standalone review use native
Codex.

Controls remain conditional: persistence, parallel ownership, pointer returns, and
independent review are enabled only when the active task needs them.

## Highlights

- Uses Codex built-in `worker`, `explorer`, and `default` subagents.
- Uses `fork_turns=none` when available, with compact task-local capsules and an
  explicit fallback when history controls are unavailable.
- Creates no custom Agent configuration.
- Keeps routine returns and repair prompts bounded.
- Keeps the critical decision chain in the main thread and delegates independent,
  parallelizable, local side work.
- Invalidates stale evidence only when its covered artifact or inputs change.
- Uses a conditional Strict first-artifact gate before copying an unproven pattern.
- Allows three focused automatic repairs per active unit.
- Supports limited implementer-to-implementer interface coordination.
- Isolates concurrent writers and high-risk changes in sibling Git worktrees.
- Provides context management through soft refreshes for long-running Goals.
- Adds durable `.agent/` state only for work that must survive across turns.

## Install

Requires a Codex environment with Skills support. Orchestrated work uses Codex's
built-in `worker`, `explorer`, and `default` subagents; no custom Agent definitions
are required.

Ask Codex to install the `goal-orchestration` skill from this repository at:

```text
skills/goal-orchestration
```

Or, after cloning or downloading this repository, copy the skill manually:

```sh
mkdir -p "$HOME/.agents/skills/goal-orchestration"
cp -R skills/goal-orchestration/. "$HOME/.agents/skills/goal-orchestration/"
```

On Windows, copy `skills/goal-orchestration` to
`%USERPROFILE%\.agents\skills\goal-orchestration`.

For a repository-scoped installation, copy it to
`<repository>/.agents/skills/goal-orchestration`. Standalone skill folders target
local Codex use; package the skill as a plugin when you need universal ChatGPT and
Codex distribution.

## Use

Invoke it explicitly:

```text
Use $goal-orchestration to implement this feature and keep the work resumable.
```

For parallel development:

```text
Use $goal-orchestration to implement this migration with two parallel workers,
preserve my dirty changes, and keep the work resumable.
```

The included metadata permits implicit activation only when the narrow complex-work
description matches; explicit `$goal-orchestration` invocation remains available.

`fork_turns=none` limits inherited conversation turns; it does not guarantee an
empty child context. Codex may still supply system, developer, bootstrap, or runtime
context, so capsules remain authoritative and history control is not a security
boundary.

Typical execution uses isolated sibling Git worktrees, compact
`fork_turns=none` task capsules when supported, a fresh reviewer instructed not to
write, and up to three focused repair continuations. A preconfigured read-only
sandbox or custom Agent is required when review must be technically prevented from
writing.

## Repository Layout

```text
skills/goal-orchestration/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── tests/
```

## Test

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s skills/goal-orchestration/tests -v
```

The skill has no external runtime dependencies.

Maintainer-only runtime observations and the repeatable context probe live in
`evaluations/runtime-surfaces.md`; they are not loaded by the skill.

## Contributing

Focused issues and pull requests are welcome. Keep the default path lightweight and
run the test command before submitting changes.

## License

MIT
