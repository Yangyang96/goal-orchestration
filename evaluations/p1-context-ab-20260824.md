# P1 Context Contract A/B — 2026-08-24

## Decision

Keep differential durable state. Keep evidence coverage only after moving its exact
form into the dispatched capsule. Narrow freshness so a milestone or wave change alone
does not create a fresh implementer. Do not claim total-token savings from this run.

## Setup

- Same repository `HEAD`, task request, acceptance, model role, and isolated temp clone.
- Baseline read the committed skill; candidate read the working-tree P1 skill.
- Task: a durable two-wave pointer-return contract change with focused tests and one
  independent review.
- Exact model token telemetry was unavailable. Proxies were wall time, Agent turns,
  durable-state bytes, repeated checks/rereads, and final correctness.
- An interrupted first candidate run stopped before implementation and was excluded.

## Results

| Measure | Baseline | P1 candidate | Direction |
|---|---:|---:|---|
| Final result | PASS | PASS after review repair | neutral |
| Wall time | 1,086 s | 1,114 s | candidate +2.6% |
| Implementation turns | 2, same implementer | 2, fresh per wave | candidate added bootstrap |
| Repair turns | 0 | 2 | candidate higher |
| Review turns | 2 on one reviewer | 1 | candidate lower |
| Total reported Agent turns | 4 | 5 | candidate +25% |
| Initial durable state | 1,797 B | 1,163 B | candidate -35% |
| Final durable state | 1,840 B | 1,615 B | candidate -12% |
| Final changed target bytes | 14,343 B | 13,615 B | candidate -5% |
| Implementer returns satisfying coverage form | 0/1 observed | 0/2 | no improvement |

Both outputs passed their focused tests and `git diff --check`. The candidate's
review found two actionable contract/test issues and repaired them. The baseline
review initially read the wrong checkout, then reread the correct root and passed.

## Findings

1. **Differential state is directionally supported, not proven.** The candidate
   checkpoint updated `STATUS.md` without rewriting stable `GOAL.md` or `PLAN.md` and
   ended with 12% fewer state bytes. One stochastic run cannot attribute all of that
   difference to the rule.
2. **Evidence coverage was placed too far from the consumer.** Implementers receive a
   capsule, not the main Agent's loaded reference. Both candidate returns omitted the
   required covered paths/artifact. The exact `VALIDATION` form therefore belongs in
   the capsule template.
3. **“New active unit starts fresh” was too broad.** The candidate treated Wave 2 of
   the same outcome and scope as fresh; the baseline continued the original
   implementer. This added a bootstrap/read boundary and one net Agent turn without a
   measured wall-time win.
4. **Total token direction remains unknown.** Candidate state and artifact proxies
   decreased, but Agent turns increased and the loaded default contract grew from
   1,586 to 1,596 words. These signals conflict.

## Applied Correction

- Capsule `RETURN` now carries
  `VALIDATION = check | covered paths/artifact | result`.
- Freshness now changes only with delegated task, ownership, expertise,
  architecture/shared-contract, or independent-review boundary.
- Later waves and focused repairs continue the implementer while outcome, task, and
  scope remain stable.
- Differential state remains unchanged.

## Limitations

- One completed run per variant; model sampling was not controlled.
- Exact input/output/cache token telemetry was unavailable.
- Test-count and implementation-shape differences make changed-file bytes only a
  weak context proxy.
- The interrupted candidate ignored its requested work root and wrote a partial
  experiment into the source repository. Those changes were removed. This confirms
  that capsule/workdir instructions are not an isolation boundary.

## Next Gate

Run a smaller forward test that checks only two behavioral invariants: a stable Wave 2
must reuse the implementer, and its return must include the capsule's validation
coverage. Do not repeat the full baseline unless either invariant still fails.

### Refined-gate result

PASS. A two-wave README task with unchanged outcome, task, scope, and expertise used
the same `/root/refined_forward_eval/readme_validation_implementer` task for both
waves. Both returns used the required form:

```text
VALIDATION: unittest suite | README.md and goal-orchestration contract tests | 21 tests passed
```

Each wave passed 21 focused tests and required no repair. The refined rules therefore
fix the two observed behavioral failures. This gate validates routing and return
shape, not total-token reduction.

## Final Repository Verification

- The current contract suite passes (26 tests at the final run).
- Default loaded context is 1,588 words: 792 in `SKILL.md` plus
  `references/unattended.md`, below the 1,600-word contract.
- Frontmatter parsing and `git diff --check` pass.
- The bundled Python validator could not run without PyYAML; Ruby's YAML parser
  validated the required `name` and `description` frontmatter instead.
