# Strict Orchestration Execution

Strict is a durable execution loop. Use its core path and only triggered controls.

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

## Minimal Durable State

Only the main Agent edits these files:

```text
.agent/GOAL.md    outcome, constraints, non-goals, final acceptance
.agent/PLAN.md    active milestone, bounded tasks, dependencies, owned areas
.agent/STATUS.md  accepted evidence, retry count, blockers, exact next action
```

Update all three in one edit batch, the single control step before useful work.

Keep combined live content under 12 KiB and store facts, not transcript. On resume
read these files and code named by `STATUS.md`, not history, broad diffs, or returns.

For one user-present high-risk wave, keep state in the task plan; do not create
`.agent/**` solely for Strict.

## Dispatch

Use `fork_turns=none`. Select:

- `explorer` medium for research, high for architecture or cross-boundary work;
- `worker` medium for routine work, high for complex implementation;
- fresh `default` high, read-only, for required independent review.

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

Sequential work is the default. For concurrency or isolation, load `coordination.md`.
If scoped paths are dirty, capture `git status --short` plus the relevant pre-dispatch
diff in main context. Persist that snapshot only when a context rollover could lose it.

## Direct Return And Acceptance

Use Light return fields. Cap routine returns at 1,200 characters and complex or
review returns at 1,800; all at 20 lines. Reviewer returns only actionable
`P0..P3 path:line | issue | correction` findings, or `PASS`.

Treat the return as a claim. The main Agent checks actual changed paths, inspects
hunks, runs focused verification, and then runs the milestone gate once. Mixed-risk
parallel work gets one consolidated review of the shared boundary, not one review per
lane plus another final review.

## Strict Repair Continuation

Repair is not a fourth mode. Reuse the original implementer while its task and owned
scope remain stable. Send only failed evidence, required correction, and the exact
check to rerun; do not resend the capsule, state files, diff, or history. Keep accepted
parts. Allow three focused repairs total; the fourth needs user approval or a split.
Count any repair already performed in Light before escalation; never reset retries.

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

Use behavioral cost limits instead of exact token accounting: bounded capsules and
returns, no repeated context or review, three concurrent Agents maximum, and three
automatic repairs. For a user-supplied token budget, record only a coarse remaining
estimate at accepted checkpoints and ask before a dispatch that may exceed it.

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
