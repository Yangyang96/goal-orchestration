# Complex Orchestration Execution

## Core Path

1. Define outcome, scope, acceptance, verification, and next action.
2. Load state only across turns, waves, or unattended work.
3. Dispatch the smallest independent task with a compact capsule.
4. Inspect its bounded return and diff; run decisive checks.
5. Continue repairs with the implementer; review only for risk or user requirement.
6. Checkpoint after acceptance or before pausing.

Reach useful repository work after no more than one control-only step. The ordinary
path adds no other control files or mechanical transactions.

## Conditional First-Artifact Gate

Before scaling an unproven pattern or shared contract where a wrong direction risks
broad rework, inspect the first artifact and run the nearest decisive check. Do this
before further implementation dispatch; create no state, commit, or extra review.

## Minimal Durable State

Only main Agent edits:

```text
.agent/GOAL.md    outcome, constraints, non-goals, final acceptance
.agent/PLAN.md    active milestone, bounded tasks, dependencies, owned areas
.agent/STATUS.md  accepted evidence, retry count, blockers, exact next action
```

Initialize all three once. Thereafter update `GOAL.md` only when outcome,
constraints, non-goals, or acceptance changes; update `PLAN.md` only when milestone,
tasks, dependencies, or ownership changes. A checkpoint normally updates only
`STATUS.md`; do not touch unchanged state files. Keep the three files' combined live
content under 12 KiB, measured in UTF-8 bytes: facts, not transcript. Resume from state
and code named by `STATUS.md`. For one risky wave with the user present, use the task
plan; do not create `.agent/**` for it.

## Dispatch

Request `fork_turns=none` when accepted, but do not claim isolation or an empty child.
When typed roles are available, prefer:

- `explorer`: medium research; high architecture/cross-boundary;
- `worker`: medium routine; high complex implementation;
- a new `default`: high non-writing review.

Otherwise use a generic Agent or inherited effort. Roles and effort are routing
hints, not observable permission or compute guarantees.

Capsule limit: 400 words.

```text
OUTCOME: active unit
TASK: one independently verifiable assignment
SCOPE: explicit writable or read-only paths
NON_GOALS: exclusions
ACCEPTANCE: observable conditions
VERIFY: exact focused checks
CONTEXT: only task-local facts and at most three file pointers
RETURN: fields/size cap; VALIDATION = check | covered paths/artifact | result
```

Default sequential work; load `coordination.md` for concurrency or isolation.
For dirty scoped paths, capture status and relevant diff; persist only through
possible context rollover.

## Direct Return And Acceptance

Cap routine returns at 1,200 characters, complex/review at 1,800, all at 20 lines.
Use `STATUS`, `CHANGED`, `RESULT`, `VALIDATION`, `RISKS`, and `NEXT`; follow capsule
`VALIDATION` and omit logs/hashes unless required. Reviewers return only actionable
`P0..P3 path:line | issue | correction` findings, or `PASS`.

Returns are claims. The main Agent checks paths and hunks, runs focused verification,
then the milestone gate once. Reuse evidence only while its covered paths or artifact
and relevant inputs remain unchanged; otherwise rerun the smallest affected check.
Mixed-risk parallel work gets one shared-boundary review, not per-lane plus final.

## Repair Continuation

Repair is continuation, not a separate mode. Reuse the implementer while task/scope
stay stable. Send only failed evidence, correction, and exact check; do not
resend capsule, state, diff, or history. Keep accepted parts. Allow three focused
repairs total; a fourth needs approval or a split. Never reset active-unit retries.

Start a new Agent only when task, ownership, expertise, architecture/shared contract,
or review boundary changes; a milestone or wave alone does not. Continue stable later
waves and focused repairs. Give a new Agent only capsule, paths, and acceptance
evidence; never resend the previous Agent transcript. Reuse reviewers for own findings;
use a new one for a new boundary/final review.

## Checkpoint And Cost

Checkpoint `STATUS.md` after acceptance or before a pause/unattended dispatch. Record
outcome, evidence, retries, blocker, and next action. Write both pre- and post-wave
checkpoints only for a real context-loss window.

With explicit Goal commit authority, an accepted wave is a commit boundary only when
paths began clean/isolated and do not overlap pre-existing user changes. The main
Agent stages only accepted paths and follows repository convention. Reuse diff,
checks, review, and ownership: do not message Agents, extend returns, rerun checks,
calculate size, or checkpoint. Otherwise preserve uncommitted changes. On failure,
never repair-dispatch, commit per Agent, or create a final aggregate Goal commit.

## Soft Context Refresh

Evaluate only at acceptance or a real pause, never during dispatch, review, or repair.
Three accepted milestones or six subagent returns trigger assessment, not reset.

Recommend refresh when the next unit exceeds the capsule/three-pointer limit; needs
old returns/tool output; shows compaction or confusion; or changes module, repository,
or domain.

Compact the same state. Create no extra file, Agent, mode, or checkpoint; do not reset
retries or rerun accepted checks. `STATUS.md` is working memory. A physical reset
requires the user to continue in a new Codex task; never create one implicitly. Resume
from state, scoped status, and named code only.
