# Complex Orchestration Execution

Use the core path and only triggered controls.

## Core Path

1. Define active outcome, scope, acceptance, verification, and next action.
2. Load durable state only across turns, multiple waves, or unattended work.
3. Dispatch the smallest independent task with a compact capsule.
4. Receive a direct bounded return; inspect the diff and run decisive checks.
5. Repair with the same implementer when appropriate.
6. Review independently only for a high-risk boundary or user requirement.
7. Checkpoint after acceptance or before pausing.

Reach useful repository work after no more than one control-only step. The ordinary
path adds no other control files or mechanical transactions.

## Conditional First-Artifact Gate

Use only before scaling parallel or unattended work that will copy an unproven pattern
or shared contract and a wrong direction would cause broad rework. Inspect the first
artifact against acceptance and run the nearest decisive check before further
implementation dispatch. This gate creates no state, commit, or extra review.

## Minimal Durable State

Only the main Agent edits these files:

```text
.agent/GOAL.md    outcome, constraints, non-goals, final acceptance
.agent/PLAN.md    active milestone, bounded tasks, dependencies, owned areas
.agent/STATUS.md  accepted evidence, retry count, blockers, exact next action
```

Update all three in one batch before useful work. Keep live content under 12 KiB and
store facts, not transcript. Resume from these files and code named by `STATUS.md`.
For one user-present risky wave, use the task plan; do not create `.agent/**` solely
for orchestration.

## Dispatch

Use `fork_turns=none` when supported; otherwise make the capsule authoritative, ignore
unrelated inherited context, and do not claim isolation. Select:

- `explorer`: medium research; high architecture or cross-boundary work;
- `worker`: medium routine; high complex implementation;
- fresh `default` high for non-writing review. Hard enforcement needs a configured
  sandbox or custom Agent. Never create it automatically.

Keep each capsule under 400 words:

```text
OUTCOME: active unit
TASK: one independently verifiable assignment
SCOPE: explicit writable or read-only paths
NON_GOALS: exclusions
ACCEPTANCE: observable conditions
VERIFY: exact focused checks
CONTEXT: only task-local facts and at most three file pointers
RETURN: direct contract and size cap
```

Default to sequential work; load `coordination.md` for concurrency or isolation. For
dirty scoped paths, capture status plus the relevant pre-dispatch diff. Persist it
only across a possible context rollover.

## Direct Return And Acceptance

Cap routine returns at 1,200 characters and complex or review returns at 1,800; all
at 20 lines. Use `STATUS`, `CHANGED`, `RESULT`, `VALIDATION`, `RISKS`, and `NEXT`.
Reviewer returns only actionable `P0..P3 path:line | issue | correction` findings, or
`PASS`.

Treat the return as a claim. The main Agent checks actual paths, inspects hunks, runs
focused verification, then runs the milestone gate once. Reuse evidence only while
its covered artifact and relevant inputs remain unchanged; otherwise rerun the
smallest affected check. Mixed-risk parallel work gets one consolidated review of the
shared boundary, not one review per lane plus another final review.

## Repair Continuation

Repair is continuation, not a separate mode. Reuse the implementer while its task and owned
scope remain stable. Send only failed evidence, required correction, and the exact
check to rerun; do not resend the capsule, state files, diff, or history. Keep accepted
parts. Allow three focused repairs total; the fourth needs user approval or a split.
Never reset retries within the active unit.

Use a fresh implementer only when ownership, task boundary, or required expertise
changes. Reuse the original reviewer for its own findings; use a fresh reviewer for a
new boundary or final independent review.

## Checkpoint And Cost

Checkpoint `STATUS.md` once after an accepted wave or immediately before pausing or
unattended dispatch. Record no more than: outcome state, accepted evidence, retry
count, blocker, and executable next action. Do not write both pre- and post-wave
checkpoints unless a real context-loss window exists.

With explicit Goal-scoped commit authority, an accepted wave is also a commit
boundary only when its paths were clean at wave start or isolated and do not overlap
pre-existing user changes. The main Agent stages only the exact accepted paths and
commits the wave using repository convention and its outcome. Reuse inspected diff,
verification, review, and ownership: do not message Agents, extend returns, rerun
checks, calculate size, or add a checkpoint. Otherwise preserve uncommitted changes.
Handle failure in the main thread; never repair-dispatch, commit per Agent, or create
a final aggregate Goal commit.

## Soft Context Refresh

Evaluate only at an accepted milestone or real pause, never during dispatch, review,
or repair. Three accepted milestones or six subagent returns since the last refresh
trigger an assessment, not an automatic reset.

Recommend refresh when the next unit cannot fit the capsule and three-pointer limit,
continuation requires rereading old returns or tool output, context compaction or
fact confusion appears, or the next milestone changes module, repository, or domain.

Compact the same state files. Create no extra file, Agent, mode, or checkpoint; do
not reset retries or rerun accepted checks. Treat `STATUS.md` as working memory. For
a physical reset, ask the user to continue in a new Codex task; never create one
implicitly. Resume from the state files, scoped status, and named code only.
