# Durable State

Use only when work must survive another task or runtime boundary, or unattended work
has multiple repair waves.

Only the main Agent edits `.agent/STATE.md`:

```text
# Goal    outcome, constraints, non-goals, final acceptance
# Plan    active milestone, bounded tasks, dependencies, owned areas
# Status  accepted evidence, retries, commits, blockers, exact next action
```

Initialize it once. Edit only the section whose facts changed: Goal for outcome or
acceptance, Plan for milestone or ownership, and Status for checkpoints. A checkpoint
normally changes only Status. Keep the complete file under 12 KiB in UTF-8 bytes and
store facts, not transcript.

Checkpoint after acceptance and before a real pause or unattended dispatch. Record
the outcome, decisive evidence, retry count, commit or skipped-commit reason, blocker,
and exact next action. Write both pre- and post-wave checkpoints only when context may
actually be lost.

Resume from State, scoped status/diff, and code named by Status.

Assess refresh only at acceptance or a real pause. If the next task cannot be stated
in a compact capsule, context is confused, or the module, repository, or domain
changes, compact the same State. Do not create another state file, reset retries, or
rerun accepted checks. A new Codex task requires the user to continue there; never
create one implicitly.
