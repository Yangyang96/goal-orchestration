# Durable-Task Evaluation Record

Use one record for one baseline/candidate comparison over exactly two accepted
waves. Fill thresholds before either run. Replace every blank with a value or `U`.

## Evidence notation

- `O` — observed directly for the named measure; enter values as `value [O]` and
  cite their log, command, or artifact.
- `P` — the observed measure is only a proxy for token cost; never convert it into
  tokens. The tables identify this relation separately from observation status.
- `U` — unknown or unavailable; enter `U`, not zero or an estimate.
- Byte counts are UTF-8 bytes. Counts are non-negative integers. IDs, fingerprints,
  pointers, and notes are one line and at most 200 characters. Validation tables
  contain at most five rows per variant/wave.

## Setup identity

| Field | Baseline A | Candidate B | Match? |
|---|---|---|---|
| Repository root and `HEAD` | ___ | ___ | YES/NO/U |
| Initial scoped-diff fingerprint | ___ | ___ | YES/NO/U |
| Task, scope, and acceptance fingerprint | ___ | ___ | YES/NO/U |
| Model, role, and requested effort | ___ | ___ | YES/NO/U |
| Runtime/tool version | ___ | ___ | YES/NO/U |
| Implementer identity | ___ | ___ | SAME/DIFFERENT/U |
| Contract/control fingerprint (treatment) | ___ | ___ | EXPECTED DIFFERENCE |
| Run ID and UTC start | ___ | ___ | n/a |

Excluded or interrupted runs (ID + reason, maximum 3): ___

### Pre-registered gates

- Correctness: `2/2` waves must pass for each variant.
- Stable-wave identity: repository, task, acceptance, model/role, and scope must
  match across variants; only the named treatment may differ.
- Maximum candidate wall-time regression: ___% (0–100%).
- Maximum candidate Agent-turn increase: ___ turns (0–20).
- Maximum repair turns: `3` per wave.
- Exact-token improvement required for a savings claim: ___% (0–100%).
- Primary non-token P2 measure and target: ___ (one listed measure; numeric target).

## Counting rules

- Accepted-milestone wall time is elapsed seconds from first wave dispatch through
  main-Agent acceptance, including review, repair, and acceptance checks.
- An Agent turn is one completed subagent response. Report total Agent turns and
  `implement/review` composition. Repair turns are the subset requested to correct
  failed evidence and are reported separately.
- Validation coverage is `acceptance requirements with passing evidence / total
  acceptance requirements`; name the check and covered paths/artifact.
- Direct-return bytes are `sum/max` across all completed subagent responses.
- Durable state is `.agent/GOAL.md`, `PLAN.md`, and `STATUS.md`: report
  `start/end/peak` total bytes. A rewrite is a write to an already-existing state
  file; report rewrite counts as `GOAL/PLAN/STATUS` (initial creation is not one).
- Rereads are repeated reads of an unchanged revision after its first read; reruns
  are repeated identical checks. Report `total/with no relevant input change`.
- Exact tokens are input, output, cache-read, and cache-write tokens from runtime
  telemetry only. If any required value is unavailable, exact total is `U`.

## Wave 1

Wave unit and acceptance ID: ___

Stable setup: YES/NO/U; variance (one line): ___

| Measure | Baseline A | Candidate B | Token relation |
|---|---:|---:|---|
| Accepted-milestone wall time (s) | ___ [O]/U | ___ [O]/U | P |
| Agent turns (`total; implement/review`) | ___ [O]/U | ___ [O]/U | P |
| Repair turns (subset of Agent turns; 0–3) | ___ [O]/U | ___ [O]/U | P |
| Validation coverage (`passing/total`) | ___ [O]/U | ___ [O]/U | n/a |
| Direct-return bytes (`sum/max`) | ___ [O]/U | ___ [O]/U | P |
| Durable-state bytes (`start/end/peak`) | ___ [O]/U | ___ [O]/U | P |
| Durable-state rewrites (`GOAL/PLAN/STATUS`) | ___ [O]/U | ___ [O]/U | P |
| Rereads (`total/unchanged-input`) | ___ [O]/U | ___ [O]/U | P |
| Reruns (`total/unchanged-input`) | ___ [O]/U | ___ [O]/U | P |
| Correctness (`PASS/FAIL`; unmet count) | ___ [O]/U | ___ [O]/U | n/a |
| Exact-token availability (`COMPLETE/PARTIAL/NONE`) | ___ [O]/U | ___ [O]/U | n/a |
| Exact tokens (`in/out/cache-read/cache-write/total`) | ___ [O]/U | ___ [O]/U | O |

| Variant | Check | Covered paths/artifact | Result |
|---|---|---|---|
| A | ___ | ___ | PASS/FAIL |
| B | ___ | ___ | PASS/FAIL |

Wave 1 accepted: YES/NO; evidence pointer: ___

Wave 1 notes (maximum 200 characters): ___

## Wave 2

Wave unit and acceptance ID: ___

Stable setup: YES/NO/U; variance (one line): ___

| Measure | Baseline A | Candidate B | Token relation |
|---|---:|---:|---|
| Accepted-milestone wall time (s) | ___ [O]/U | ___ [O]/U | P |
| Agent turns (`total; implement/review`) | ___ [O]/U | ___ [O]/U | P |
| Repair turns (subset of Agent turns; 0–3) | ___ [O]/U | ___ [O]/U | P |
| Validation coverage (`passing/total`) | ___ [O]/U | ___ [O]/U | n/a |
| Direct-return bytes (`sum/max`) | ___ [O]/U | ___ [O]/U | P |
| Durable-state bytes (`start/end/peak`) | ___ [O]/U | ___ [O]/U | P |
| Durable-state rewrites (`GOAL/PLAN/STATUS`) | ___ [O]/U | ___ [O]/U | P |
| Rereads (`total/unchanged-input`) | ___ [O]/U | ___ [O]/U | P |
| Reruns (`total/unchanged-input`) | ___ [O]/U | ___ [O]/U | P |
| Correctness (`PASS/FAIL`; unmet count) | ___ [O]/U | ___ [O]/U | n/a |
| Exact-token availability (`COMPLETE/PARTIAL/NONE`) | ___ [O]/U | ___ [O]/U | n/a |
| Exact tokens (`in/out/cache-read/cache-write/total`) | ___ [O]/U | ___ [O]/U | O |

| Variant | Check | Covered paths/artifact | Result |
|---|---|---|---|
| A | ___ | ___ | PASS/FAIL |
| B | ___ | ___ | PASS/FAIL |

Wave 2 accepted: YES/NO; evidence pointer: ___

Wave 2 notes (maximum 200 characters): ___

## Final decision

Aggregate each count or byte measure by summing both waves; aggregate wall time and
exact token categories the same way. Do not average ratios: sum their numerators and
denominators. Record `U` if a required component is `U`.

| Gate | Result | Evidence |
|---|---|---|
| Both waves stable and accepted | PASS/FAIL/U | ___ |
| Correctness `2/2` for A and B | PASS/FAIL/U | ___ |
| Wall-time guardrail | PASS/FAIL/U | ___ |
| Agent-turn guardrail | PASS/FAIL/U | ___ |
| Repair-turn guardrail | PASS/FAIL/U | ___ |
| Primary non-token P2 target | PASS/FAIL/U | ___ |
| Exact-token telemetry complete | YES/NO | ___ |
| Exact-token improvement threshold | PASS/FAIL/U | ___ |

Token conclusion: `SAVINGS THRESHOLD MET` / `SAVINGS THRESHOLD NOT MET` / `UNKNOWN`

Operational P2 decision: `ADVANCE` / `HOLD` / `REJECT`

Decision evidence (maximum 3 bullets):

- ___

### Decision rule

Claim `SAVINGS THRESHOLD MET` only when both variants have complete exact-token telemetry
for both stable, correct waves and B meets the pre-registered token threshold. Claim
`SAVINGS THRESHOLD NOT MET` only when that telemetry is complete but B misses the
threshold. Otherwise token direction is `UNKNOWN`.

Wall time, turns, return/state bytes, rewrites, rereads, and reruns are independent
proxies. Never sum, weight, or translate them into token savings. If any proxy improves
while another worsens, record proxies as conflicting and keep token direction
`UNKNOWN`; aligned proxies may support a hypothesis, never a token-savings claim.

Choose `ADVANCE` only if both stability and correctness gates pass, no guardrail
fails, and the pre-registered primary P2 target passes. Choose `REJECT` for a
correctness failure or guardrail breach; otherwise choose `HOLD`. This operational
decision does not change the separate token conclusion.
