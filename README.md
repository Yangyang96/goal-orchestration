# Goal Orchestration

Goal Orchestration is an **AI coding agent harness** and **agent skill** for
**OpenAI Codex**. It provides graph-engineered **multi-agent orchestration** for
fast fixes, bounded subagent work, and durable parallel development while keeping
context-engineering and coordination overhead small.

```text
Focused change                 → Fast Path
One bounded Codex subagent     → Light Delegation
Parallel, durable, or risky    → Strict Orchestration
```

Most agentic AI workflows make everyday fixes pay for heavyweight coordination.
This Codex skill keeps the common path fast, then adds Git worktree isolation,
persistent state, independent review, repair loops, and context recovery only when
the task needs them.

## Modes

| Mode | Use it for |
|---|---|
| Fast Path | User-present work the main Agent can implement and verify directly |
| Light Delegation | One bounded Codex subagent and one lightweight repair |
| Strict Orchestration | Resumable, unattended, parallel, cross-repository, or high-risk work |

The skill selects the lightest suitable mode automatically. Strict controls remain
conditional: persistence, parallel ownership, pointer returns, and independent
review are enabled only when the task needs them.

## Highlights

- Uses Codex built-in `worker`, `explorer`, and `default` subagents.
- Uses `fork_turns=none` with compact task-local capsules.
- Creates no custom Agent configuration.
- Keeps routine returns and repair prompts bounded.
- Allows three focused automatic repairs in Strict mode.
- Supports limited implementer-to-implementer interface coordination.
- Isolates concurrent writers and high-risk changes in sibling Git worktrees.
- Provides context management through soft refreshes for long-running Goals.
- Adds durable `.agent/` state only for work that must survive across turns.

## Install

Requires a Codex environment with Skills support. Delegated modes use Codex's
built-in `worker`, `explorer`, and `default` subagents; no custom Agent definitions
are required.

Ask Codex to install the `goal-orchestration` skill from this repository at:

```text
skills/goal-orchestration
```

Or, after cloning or downloading this repository, copy the skill manually:

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/goal-orchestration"
cp -R skills/goal-orchestration/. "${CODEX_HOME:-$HOME/.codex}/skills/goal-orchestration/"
```

On Windows, copy `skills/goal-orchestration` to
`%USERPROFILE%\.codex\skills\goal-orchestration`.

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

The included metadata also permits implicit activation when a development task
benefits from delegation or durable orchestration.

Typical Strict execution uses isolated sibling Git worktrees, compact
`fork_turns=none` task capsules, a fresh read-only reviewer, and up to three focused
repair continuations. Fast and Light work avoid those controls unless a trigger
requires escalation.

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

## Contributing

Focused issues and pull requests are welcome. Keep the default path lightweight and
run the test command before submitting changes.

## License

MIT
