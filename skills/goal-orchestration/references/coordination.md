# Writable-Agent Coordination

Use for concurrent writers or worktree isolation. Prefer sequential work for shared
writable paths, unsettled interfaces, or implementation dependencies. Parallel lanes
need stable contracts and disjoint ownership; the main Agent brokers changes to
shared contracts and integrates the results.

Inspect scoped status and diff before writable dispatch. Preserve pre-existing edits
and tell each implementer that other writers' changes must not be reverted. Use the
current working tree for sequential work, including tasks dependent on dirty changes.
Do not discard, stash, or commit pre-existing user changes without authorization.

Use separate worktrees when requested or when concurrent writers need independent
branches, indexes, or validation environments. Shared-worktree parallelism is suitable
only for disjoint edits with coordinated shared resources and no competing Git
mutations. If isolation is unavailable, proceed sequentially unless the user requires
isolation; then resolve that prerequisite before dependent writes.

Choose a writable worktree location consistent with project conventions; a sibling
directory is a preference, not a prerequisite. Use dedicated `codex/<task-id>` branches
unless instructed otherwise. Verify worktrees with `git worktree list` and include the
absolute path in each capsule. Worktrees isolate Git state, not permissions.

For clean source, branch from the agreed base, normally current `HEAD`. If required
changes are uncommitted, use sequential work in place or transfer a scoped patch to
an isolated workspace when existing authorization permits. Record the base and patch
provenance, leave source edits intact, and verify the destination. Do not silently
substitute a clean `HEAD` for the user's intended working-tree base.

Keep one ownership map in the existing plan or durable state when coordinating lanes:

```text
agent-id | task | worktree | branch | writable paths | dependencies
```

Inspect branch diffs and integrate accepted changes before checking the combined
result. Reuse valid component evidence under the entrypoint's verification rules.
Remove task-created worktrees only after their work is integrated or explicitly
abandoned and no unpreserved changes remain. Otherwise retain them and record paths.
