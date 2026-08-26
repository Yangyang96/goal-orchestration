# Writable-Agent Coordination

Use for concurrent writable Agents or requested worktree isolation. Keep sequential
and read-only work in the current worktree.

Use one worktree per writable implementer when writers run concurrently, the user
requests isolation, or high-risk changes need review before touching the user's
working copy. If lanes share writable paths, a moving interface, or an implementation
dependency, run them sequentially.

Place worktrees in a sibling directory outside the repository on dedicated
`codex/<task-id>` branches. Put the absolute worktree path in the capsule and verify it
with `git worktree list`; a worktree separates changes but is not a security sandbox.

Record one ownership map in the current plan or State's Plan section:

```text
agent-id | task | worktree | branch | writable paths | depends on
```

Writable paths must be disjoint. The main Agent brokers interface decisions and
integrates in the main worktree.

Before dispatch, inspect `git status --short` and the scoped diff:

- For clean source, branch from current `HEAD`.
- For unrelated dirty paths, record them and proceed only when ownership is disjoint.
- For required or overlapping dirty changes, work sequentially or obtain explicit
  approval for a temporary commit or patch transfer.

Never stash, commit, reset, clean, relocate, copy, or overwrite user changes without
explicit approval, and never silently change the task base.

Accept once after inspecting each branch diff and running the combined decisive gate.
Remove a worktree only after acceptance and a clean working tree; otherwise preserve
it and report its path.
