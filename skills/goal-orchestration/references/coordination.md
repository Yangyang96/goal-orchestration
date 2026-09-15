# Concurrent Writers

Track each lane's writable paths, shared interfaces, dependencies and workspace in
the existing plan. File ownership alone does not isolate Git indexes, generated
outputs, test databases or services; assign or isolate those shared resources too.

Use a shared worktree for disjoint edits with coordinated shared resources and no
competing Git mutations. Use separate worktrees when lanes need independent branches,
indexes or validation environments. If isolation is unavailable, serialize dependent
work; if the user requires isolation, resolve that prerequisite first.

Give each delegate its absolute worktree path and source base. A worktree created from
HEAD excludes uncommitted input: if a lane needs that input, keep it sequential in
place or transfer a scoped patch and record its provenance. Verify that the destination
contains the intended input before dispatch.

Merge accepted lane changes before checking the combined result. Clean up temporary
worktrees only after integration or explicit abandonment, with no unpreserved changes;
otherwise retain their paths in the recovery record.
