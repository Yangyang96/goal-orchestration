# Parallel Coordination And Worktrees

Load only for concurrent writable Agents or a worktree-isolation decision. Keep Fast,
Light, ordinary sequential Strict, and read-only Agents in the current worktree.

## Isolation Triggers

Require one isolated worktree per writable implementer when:

- two or more implementers write concurrently;
- the user requests isolation; or
- security, migration, shared-contract, concurrency, or release-critical changes must
  be reviewed and integrated before touching the user's working copy.

If lanes share writable paths, a moving interface, or an implementation dependency,
run them sequentially; separate directories do not make coupled work independent.

## Location And Ownership

Place worktrees outside the repository, under this default sibling directory:

```text
<repo-parent>/<repo-name>-worktrees/<task-id>/
```

Use a dedicated `codex/<task-id>` branch and put the absolute worktree path in the
capsule. Do not place worktrees in `.worktree/`, `.worktrees/`, or another directory
inside the repository. Verify the target with `git worktree list` before dispatch.

Record one compact map in the current plan or durable `STATUS.md`:

```text
agent-id | task | worktree | branch | writable paths | depends on
```

Paths must be disjoint. Ownership attributes changes but is not a sandbox. The main
worktree remains the integration and acceptance location.

## Dirty Working Tree

Before a writable dispatch, inspect `git status --short` and the scoped diff.

- Clean source: create the worktree from the current `HEAD`.
- Dirty but unrelated, disjoint paths: a worktree from `HEAD` is allowed; record the
  dirty paths so acceptance does not attribute or overwrite them.
- Dirty changes required by, or overlapping, the task: do not create from `HEAD`
  because those changes would be missing. Continue sequentially in the current
  worktree, or ask the user to approve a temporary commit or patch transfer.
- Dirty changes overlapping multiple proposed lanes: do not dispatch them in
  parallel. Serialize the lanes or obtain a user-approved snapshot strategy.

Never stash, commit, reset, clean, relocate, or copy user changes without explicit
approval. Never silently change the task base.

## Communication And Acceptance

The main Agent brokers communication. Two implementers meeting at a declared
interface may exchange one note of at most 500 characters, copied to the main Agent,
containing only the interface decision and affected paths.

Accept once: inspect each branch diff, integrate deliberately, run the combined gate,
and use one reviewer only for a risky shared boundary. Remove a worktree only after
its changes are accepted and its working tree is clean; otherwise preserve it and
report its path.
