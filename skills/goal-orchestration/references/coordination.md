# Parallel Coordination

Load only when two or more subagents will run concurrently. Default to sequential
work when tasks share files, a schema is still moving, or one task depends on another.

Use at most three concurrent Agents. Before spawning, record one compact ownership
map in the current plan or durable `STATUS.md`:

```text
agent-id | task | writable paths | depends on
```

Writable paths must be disjoint. Read-only Agents use `none`. Ownership is an
attribution rule, not a sandbox; the main Agent verifies actual diffs after return.
For high-risk changes, use isolated worktrees. Avoid per-Agent checkpoints.

The main Agent normally brokers communication. Two implementers meeting at a
declared interface may exchange one note of at most 500 characters, copied to the
main Agent, containing only the interface decision and affected paths. Further
coordination becomes sequential main-Agent mediation.

Accept the wave once: combine changed-path checks, run integration verification, and
perform one reviewer pass only if the shared boundary is high risk or explicitly
requires independent review.
