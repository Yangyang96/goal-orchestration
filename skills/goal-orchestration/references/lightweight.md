# Light Delegation Execution

Use for one bounded, independently verifiable subtask while the user is present.
Create no `.agent/**` state and use no independent reviewer.

Before dispatch, note the scoped `git status --short` and relevant diff when those
paths are already dirty. Spawn one built-in Agent with `fork_turns=none`:

- routine implementation: `worker`, medium reasoning;
- complex but bounded implementation: `worker`, high reasoning;
- bounded read-only research: `explorer`, medium or high reasoning by complexity.

Keep the prompt within 350 words and include:

```text
TASK: one outcome
SCOPE: explicit paths
NON_GOALS: exclusions
ACCEPTANCE: observable conditions
VERIFY: exact focused command or check
RETURN: use the contract below
```

The direct return is at most 1,200 Unicode characters and 16 lines:

```text
STATUS: DONE | NEEDS_CONTEXT | BLOCKED
CHANGED: repo-relative paths | none
RESULT: completed behavior or blocker
VALIDATION: exact check + PASS | FAIL
RISKS: concrete residual risk | none
NEXT: one action
```

The main Agent compares `CHANGED` with the actual diff, inspects the changed hunks,
and independently runs the decisive check. If one narrow defect remains, reuse the
same Agent for one delta-only repair of at most 200 words.

Upgrade the same active unit to Strict if scope expands, a second repair is needed,
another Agent must run, a risky boundary appears, or independent review becomes
necessary. Preserve accepted work and current diffs; do not redo the Light dispatch.
The Light repair counts as the first of Strict's three automatic repairs for that
active unit; upgrading never resets the count.
