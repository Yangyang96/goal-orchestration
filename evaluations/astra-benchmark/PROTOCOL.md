# Astra Skill controlled pilot — preregistered protocol

Registered 2026-09-07, before task execution. This is a small within-task comparison,
not a statistical certification of GPT-6 Astra performance.

## Question and treatments

Does goal-orchestration improve actual outcomes relative to native Astra execution?
Does the revision improve outcomes relative to the previous Skill?

- `native`: no goal-orchestration instructions.
- `old`: Skill and references at repository commit `7845565`.
- `new`: working-tree Skill and references frozen before the first task run.

Use fresh processes, identical task source and prompts, model `gpt-6-astra`, and
reasoning effort `xhigh` (the user's current local setting). Record the installed CLI
version, requested model/settings and any returned usage/runtime metadata. Do not
claim provider-internal model attestation or compute equality from model self-report.

Disable other user skills and unrelated user configuration for all groups, with only
per-invocation options; never modify the user's installed skills or global config.
Common sandbox: workspace-write; no bypass. No network-dependent task, production
service, credential operation or actual remote publication. Model inference uses the
existing logged-in Codex connection. Keep standalone execution and tool availability
identical across groups; this initial pilot does not evaluate parallel Agent scaling.

Inject the selected Skill entrypoint as an explicitly invoked instruction, with
unchanged reference files available at the supplied path. Record exact input hashes.
No candidate receives another candidate's output, prior review, task validator, or
intended reference solution. Do not repair outputs between execution and grading.

## Tasks and ordering

Three small standard-library Python repositories, authored by an independent Agent
without reading either Skill or prior review. They cover focused repair, integration
with compatible APIs and authorized local delivery, and recovery from failed work.
Two fresh repetitions of each task/treatment: 18 measured runs total.

Use a seeded random treatment permutation per task/repetition, with two execution
slots. Time cap: 360 seconds per run. A timeout is an incomplete run, not a silent
exclusion. Infrastructure failures are recorded separately and may be retried on a
fresh copy, with the failed attempt retained. Do not answer unnecessary questions or
send "continue" to rescue any treatment during a measured run.

Verify that hidden behavioral checks fail for the initial bugs and pass for reference
repairs before freezing the fixtures. Record fixture and Skill hashes before runs.

## Scoring

Primary: all task acceptance checks pass, including Git delivery when requested,
compatibility, preservation of pre-existing edits and required artifacts.

Secondary, from actual outputs and action logs:
- unnecessary clarification/approval questions and premature stopping;
- false completion and scope expansion;
- unauthorized or incorrectly attributed Git changes;
- number of executed tool commands, changed paths, commits, failed/repeated checks;
- wall-clock duration and actual token usage when returned by the runtime.

Code and Git state outrank the Agent's completion statement. A blinded read-only
review of logs resolves qualitative behavior; mechanical substring matching is not
an evaluator of whether a question was necessary. Valid clarification is not a
failure. The supplied tasks should be executable without missing user decisions.

Correctness and authorization are gates: efficiency gains cannot compensate for
wrong behavior. Report both repetitions and all failed runs. Do not convert bytes,
wall time, cached tokens, or Agent turns into estimated money or token savings.
Report medians and paired differences as descriptive statistics, not significance.

## Decision rules and limits

- Improved completion or fewer concrete workflow errors without new correctness or
  authorization failures supports a task-local benefit.
- Equal outcomes with lower interaction or resource cost supports an efficiency
  hypothesis; two repetitions are insufficient to attribute small differences.
- Equal outcomes and no consistent cost advantage means no demonstrated extra value.
- A regression against native is evidence to narrow or revise Skill activation.

Report limitations: small tasks, limited repetitions, a controlled CLI surface,
no real external delivery, no multi-agent scaling, no actual multi-day continuation,
and no guarantee that the same differences hold in the user's full desktop setup.
Do not change Skill instructions until this frozen campaign is scored.

## Calibration before measured runs

The initial CLI probe timed out over WebSockets, then succeeded after automatic HTTPS
fallback. A second attempt to override the built-in provider was rejected by config
validation. A separate per-invocation provider using the same official
`https://chatgpt.com/backend-api/codex` endpoint, existing OpenAI auth, Responses wire
format, and `supports_websockets=false` succeeded. It changes transport, not the
requested model. All measured groups use this exact configuration.

Host task-routing variables are removed from the child process environment; sandbox
controls are retained. Disable skill paths using their actual `SKILL.md` file paths
(as this installed CLI expects), along with skip-host-discovery and disabled plugins.
The successful final probe did not emit the prior skill-catalog budget warning and
reported actual token usage. Task prompts also forbid reading globally installed
skills or files outside the supplied fixture and selected Skill. These are controlled
execution instructions, not proof of hard read isolation. Audit the tool logs for
cross-treatment/global-skill reads. Shared system and developer instructions remain.

A desktop-subagent fallback was considered but not used for measured task execution.
The CLI logs a shared SessionEnd hook timeout-clamping diagnostic even with hooks
disabled; record it as an environment diagnostic, not a treatment failure.

## Scope amendment, before inspecting measured outcomes

Independent method review identified that the three original fixtures cover ordinary
single-agent execution; database recovery is not context recovery. Therefore they
cannot establish the Skill's value for its primary recovery/coordination use cases.
Keep the frozen 18-run campaign intact and add a separately reported handoff cohort:
three treatments × two repeats × two fresh process waves, 12 invocations.

Wave 1 receives a realistic complete two-stage request, implements the first stage,
and is explicitly asked to leave enough information for a new task to continue later.
Wave 2 gets the unchanged resulting working tree but no conversation history and only
a short continuation request. Important stage-two contracts are supplied in wave 1,
not prewritten into the fixture. Agents choose their own recovery-record format.
Grade actual phase-two functionality against those original contracts; no mandatory
state filename or keyword scoring. No model run receives grader or reference code.
Report this cohort separately from ordinary-task results. It still does not test
parallel writers or real multi-day scheduling. The author of this additional fixture
also has not read either Skill or any candidate results.

## Delivery permission correction

The first completed delivery run reached the requested commit but the CLI's default
non-interactive approval policy prevented writing `.git/index.lock`. This is a known
infrastructure limitation, not evidence against a treatment. Preserve and report all
original delivery runs with their code checks and denied-commit evidence. Repeat the
entire delivery stratum (all three treatments, both repeats) on fresh copies using
Codex's `--approve-for-me` mode, which retains workspace-write and permits automatic
review of required escalations. The CLI does not allow combining that flag with
`--sandbox`; remove only the redundant sandbox argument. No bypass mode is used.

Compare corrected delivery runs only against each other. Primary valid-task totals
use ordinary/recovery from the original cohort and delivery from the corrected
cohort. Original infrastructure-blocked delivery runs remain in the report and raw
archive, separately labeled; they are never silently omitted or counted as a model
failure. The new permission setting is uniform across the entire repeated stratum.
Token usage is that reported for the executing Agent; separate guardian/approval
compute, if any, is not guaranteed to be included and is not claimed as total cost.

Interpretation note after the first two corrected results, without changing the
recorded mandatory-delivery scoring: an individual failure in the corrected stratum is not automatically excluded as an
infrastructure failure. The approval-enabled calibration established a permitted Git
completion path. Record whether each candidate actually delivers the commit and any
visible escalation or rejection evidence. A remaining sandbox denial alone does not
establish that completion was impossible; missing CLI events also do not prove that
an escalation was never attempted. Keep incomplete corrected deliveries in the valid
outcome comparison and distinguish observed outcome from uncertain causal attribution.

## Interpretation and maintenance notes

The independent reviewer confirmed that the basic within-task treatment comparison
is defensible, but identified limited scope, dynamic concurrent partners, lack of
hard read isolation, and the need to inspect behavior beyond mechanical acceptance.
These remain explicit limitations. Review packets remove run/treatment labels and
absolute cohort paths; narration or a read reference can still reveal the treatment,
so describe this as label-hidden independent review, not a fully double-blind study.

The runner's result-collection code was hardened after review to retain execution
metadata if a validator times out or Git inspection fails. This does not alter
prompts, workspaces, acceptance criteria, or the already-running Python process.
The original cohort uses the initially loaded collector; any missing records must
be recovered from its retained logs rather than excluded. Later cohorts use the
hardened collector. `commands` counts completed shell-command events, not all tools.

Configuration was checked against [Codex's configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The motivation to audit ambiguous Skill instructions is consistent with
[OpenAI's Astra behavior guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra),
which discusses instruction sensitivity and follow-through. This is background for
the hypothesis, not empirical evidence that this particular Skill helps.

The treatment is explicitly supplied Skill content. This pilot does not measure
whether automatic discovery selects the Skill at the right time or whether its UI
default prompt is helpful. The runtime files used by both revisions consist of the
entrypoint and its two referenced Markdown files; UI metadata is not an experimental
input. Cache-hit input tokens are a subset of reported input tokens and are not added
again. Raw input/output counts are not converted into currency or account quota.

The review packet exporter was amended to include actual text artifacts, including
untracked files. Git diff alone omitted new handoff records. Wave-one artifacts come
from the frozen phase-one snapshot, never from the subsequently modified workspace.
Previously reviewed wave-one packets were refreshed without changing their sample
labels and the reviewer checked the added evidence. Binary fixture data remains in
the raw workspaces and is assessed by the validators.

## Recomputing the result

The final evidence archive retains `campaign/`, `handoff/`, and `delivery-corrected/`
with frozen inputs, options, prompts, event logs, workspaces, and validation results.
After extracting it into an otherwise empty directory, recompute descriptive totals:

```sh
python3 evaluations/astra-benchmark/compare.py /absolute/extracted/evidence \
  --output /absolute/extracted/comparison.json
```

The comparison keeps all six permission-limited delivery attempts in a separate
field and requires equal hashes for shared frozen inputs. Handoff counts as one
end-to-end case per pair, not two independent successes. Mechanical acceptance must
be read together with the independent scope/behavior grades. To execute new model
runs, first adapt the recorded CLI options to the local installation, skill paths,
and disposable log/state directories; the archived machine-specific options are an
audit record, not a portable configuration or an instruction to change global files.
