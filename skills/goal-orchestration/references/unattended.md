# Strict Orchestration Execution

Strict is a durable execution loop, not a filesystem transaction protocol. Use its
core path first; add only the triggered controls named in `SKILL.md`.

## Core Path

1. Define the active outcome, scope, acceptance, verification, and next action.
2. Create or load durable state only if work must survive another turn, contains
   multiple waves, or runs unattended.
3. Dispatch the smallest independent task with a compact capsule.
4. Receive a direct bounded return, inspect the real diff, and run decisive checks.
5. Repair with the same implementer when appropriate.
6. Run one independent review only when a high-risk boundary or the user requires it.
7. Persist one checkpoint after acceptance or before pausing.

The first useful repository action should follow no more than one control-only step.
The ordinary path adds no other control files or mechanical transactions.

## Minimal Durable State

Only the main Agent edits these files:

```text
.agent/GOAL.md    outcome, constraints, non-goals, final acceptance
.agent/PLAN.md    active milestone, bounded tasks, dependencies, owned areas
.agent/STATUS.md  accepted evidence, retry count, blockers, exact next action
```

Create or update all three in one edit batch; that batch is the single allowed
control step before useful repository work.

Keep their combined live content under 12 KiB. Store current facts, not transcript.
On resume read only these three files, then inspect the exact code named by
`STATUS.md`. Do not preload history, broad diffs, or old Agent returns.

For a single user-present high-risk wave, the current task plan may hold this state;
do not create `.agent/**` solely because the mode is Strict.

## Dispatch

Use `fork_turns=none`. Select:

- `explorer` medium for bounded research, high for architecture or cross-boundary work;
- `worker` medium for routine implementation, high for complex implementation;
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

Use the Light return fields. Cap routine returns at 1,200 characters and complex or
review returns at 1,800; all at 20 lines. A reviewer reports only actionable findings
as `P0..P3 path:line | issue | correction`, or `PASS`.

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

Use behavioral cost limits instead of exact token accounting: bounded capsules and
returns, no repeated context, no duplicate review, maximum three concurrent Agents,
and at most three automatic repairs. If the user supplies a token budget, record only a
coarse remaining estimate in `STATUS.md` at accepted checkpoints and ask before the
next dispatch that may exceed it.

## Soft Context Refresh

Evaluate only at an accepted milestone or real pause, never during dispatch, review,
or repair. Three accepted milestones or six subagent returns since the last refresh
trigger an assessment, not an automatic reset.

Recommend refresh when the next unit cannot fit the capsule and three-pointer limit,
continuation requires rereading old returns or tool output, context compaction or
fact confusion appears, or the next milestone changes module, repository, or domain.

Use the existing checkpoint: compact the same three state files. Create no extra
file, Agent, mode, or checkpoint; do not reset retries or rerun accepted checks. In
the same task, treat `STATUS.md` as working memory and ignore older conversational
detail. If a physical context reset is needed, ask the user to continue in a new
Codex task; never create one implicitly. Resume by reading the three state files,
one scoped `git status --short`, and only the code named by `STATUS.md`.
