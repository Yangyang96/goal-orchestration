# Recovery Across Contexts

Before a handoff that may outlive the current context, add the recovery-specific facts
to the project's existing progress record:

- Delegate identity and how to retrieve its result; owned paths and dependencies.
- Worktree path, branch/base and any transferred uncommitted patch provenance.
- Returned artifact and check locations; what has been integrated and what remains.
- The next consumer action, including any shared-interface decision still pending.

On recovery, reconcile these entries with the actual Agent, worktree and integration
state before redispatching. An existing output may need integration rather than a
replacement implementation. Retain recoverable artifacts while their work is pending.
