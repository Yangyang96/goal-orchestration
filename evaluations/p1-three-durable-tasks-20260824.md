# P1 Three Durable Tasks — 2026-08-24

> Historical snapshot of the previous three-file durable-state and pointer-return
> contract. Counts and “current” wording below describe the evaluated revision.

## Decision Question

Does the refined P1 contract improve accepted-work efficiency without adding Agent
bootstrap or repair churn, and is total-token direction supported strongly enough to
justify P2?

## Method

- Three useful repository changes run in isolated copies of the same working tree.
- Each task has two accepted waves with unchanged outcome, task, scope, and expertise.
- Wave 2 must continue the Wave 1 implementer. Only the main Agent updates durable
  state, normally `STATUS.md` alone.
- Every return must use
  `VALIDATION = check | covered paths/artifact | result` and remain within 1,200
  characters and 20 lines.
- Record wall time, implementation and repair turns, validation coverage, durable
  state bytes and rewrites, repeated reads/checks, correctness, and exact-token
  availability. Bytes and turns are proxies, not token telemetry.

## Tasks

| ID | Useful outcome | Wave 1 | Wave 2 |
|---|---|---|---|
| T1 | Pointer-return contract coverage | Protect trigger, path, size, digest, retry, cleanup, and no-scan rules | Expose the bounded workflow in README and protect alignment |
| T2 | Reusable durable-task evaluation record | Create a bounded metrics and decision template | Add focused contract coverage for required fields |
| T3 | Measurable durable-state recovery contract | Define 12 KiB as combined UTF-8 bytes and test it | Protect minimal resume inputs and unchanged-state behavior |

## Starting State

| ID | Live state bytes | Stable `GOAL.md` / `PLAN.md` digest recorded |
|---|---:|---|
| T1 | 618 | yes |
| T2 | 631 | yes |
| T3 | 596 | yes |

## Results

| ID | Wall time | Agent turns | Repairs | Return bytes | State bytes | Stable rewrites | Result |
|---|---:|---:|---:|---:|---:|---|---|
| T1 | 403 s | 2 | 0 | 1,635 | 618 → 729 | GOAL 0 / PLAN 0 / STATUS 2 | PASS |
| T2 | 723 s | 2 | 0 | 1,430 | 631 → 735 | GOAL 0 / PLAN 0 / STATUS 2 | PASS |
| T3 | 621 s | 2 | 0 | 1,359 | 596 → 737 | GOAL 0 / PLAN 0 / STATUS 2 | PASS |

The tasks ran concurrently, so campaign wall time was 723 seconds rather than the
sum of task durations. All three Wave 2 calls used the Wave 1 task identity. Stable
`GOAL.md` and `PLAN.md` digests were unchanged; only `STATUS.md` was checkpointed.

All six direct returns stayed below 1,200 characters, named the covered
paths/artifact, and reported the result. Main-Agent acceptance repeated the decisive
checks without rereading old returns. T1 ended at 33 focused tests, T2 at 27, and T3
at 30 plus a 1,595/1,600-word default-context check.

Return-byte counts were computed and reported by each implementer; they were not
independently available from runtime telemetry.

Exact input, output, cache-read, and cache-write token telemetry was unavailable.
Return bytes, state bytes, turns, and wall time remain proxies and are not converted
to tokens.

## Decision

**Keep refined P1; hold P2.** The original candidate's two behavioral regressions did
not recur across six real waves: stable waves reused implementers, validation
coverage was complete, no repair turn was needed, and durable state remained
differential. This supports an operational-efficiency improvement over the original
candidate behavior.

Token direction remains `UNKNOWN`. The proxy signals are favorable but cannot prove
net savings. None of these tasks produced main-Agent tool output large enough to
require a spooler, so the evidence does not meet P2's trigger. Reconsider P2 only
after a real task crosses the direct-return/context boundary or runtime token
telemetry becomes available.

## Integrated Outputs

- T1's pointer workflow, reference contract coverage, and README alignment are in the
  working tree.
- T2's reusable `evaluations/durable-task-template.md` and contract guard are in the
  working tree.
- T3's combined UTF-8 state budget and recovery guards are in the working tree.

The integrated repository passes all 37 contract tests and `git diff --check`; its
default loaded context is 1,595 words against the 1,600-word cap.
