# Runtime Surface Evaluations

Observations are local to the named surface and become stale after a runtime, tool
schema, or agent-configuration change. This maintainer document is not loaded by the
skill.

## Matrix Schema

| Surface/build | Spawn primitive | History control | Child model/effort | Hard read-only | Native Goal | Plugin/profile | Evidence + observed time |
|---|---|---|---|---|---|---|---|

Use `confirmed`, `observed`, `unsupported`, or `unknown`; absence from documentation
is `unknown`. Inspect the active tool schema and official documentation before probing.

## Repeatable Context Probe

1. Put a unique `GO_PARENT_<random>` canary in an ordinary parent user message,
   outside both probe capsules.
2. Spawn probe A with full-history inheritance and task canary `GO_TASK_A_<random>`.
3. Spawn probe B with the smallest supported inheritance and task canary
   `GO_TASK_B_<random>`. Change no other option.
4. Require exactly:

```text
SURFACE_BUILD: value | unknown
FORK_REQUESTED: value
PARENT_CANARY: visible | not_visible
TASK_CANARY: visible | not_visible
UNRELATED_PARENT_CONTEXT: visible | not_visible | uncertain
WRITE_ATTEMPTED: no
```

Run the pair twice. Record an observation only when both pairs agree; otherwise use
`unknown`. Use only probe canaries and never request hidden instructions. The probe
measures visibility, not security isolation.

## 2026-08-20 — Codex Desktop collaboration runtime

| Surface/build | Spawn primitive | Requested history | Task canary | Parent commentary canary | Unrelated parent context | Result |
|---|---|---|---|---|---|---|
| Desktop / unknown build | `spawn_agent` | `all` | visible 2/2 | not visible 2/2 | visible 2/2 | parent context present; exact full-history behavior unknown |
| Desktop / unknown build | `spawn_agent` | `none` | visible 2/2 | not visible 2/2 | visible 2/2 | not an empty context; difference from `all` unknown |

No writes or tools were attempted by probe agents. The parent canary was placed in
assistant commentary, which this runtime may filter from both fork modes, so its
absence does not establish history isolation. Both `none` probes independently
reported unrelated parent context, so that observed build did not support treating
`fork_turns=none` as a security boundary or empty-child guarantee.

## 2026-08-24 — Current Codex Desktop collaboration runtime

The active `spawn_agent` schema exposed:

- `fork_turns`: `none`, `all`, or a positive turn count;
- `agent_type`: `explorer`, `worker`, `default`, plus runtime-specific specialist roles;
- `reasoning_effort`: a per-child request when `fork_turns` is `none` or bounded;
  full-history forks inherit the parent's model and effort.

Schema presence was checked with no-tool, no-write calls:

| Requested role | Requested fork | Requested effort | Call accepted | Effective effort observable |
|---|---|---|---|---|
| `explorer` | `none` | `medium` | observed 1/1 | no |
| `worker` | `none` | `high` | observed 1/1 | no |
| `default` | `none` | `high` | observed 1/1 | no |

One parent-user visibility pair used an answer not present in either capsule. The
`all` child returned the correct parent-user suffix; the `none` child returned
`NOT_VISIBLE`. An earlier commentary-canary pair was inconclusive because both modes
filtered parent commentary.

| Requested history | Parent user suffix | Result |
|---|---|---|
| `all` | visible 1/1 | parent user turn observed |
| `none` | not visible 1/1 | parent user turn not observed |

This reverses the 2026-08-20 observation and shows why the skill must inspect the
active schema and keep a behavioral fallback. One successful call proves parameter
acceptance, not role semantics or effective reasoning compute. One visibility pair
does not prove an empty child, stable behavior across builds, or security isolation.

A search of official OpenAI documentation found model-level reasoning settings but
no public contract for these Codex Desktop `spawn_agent` fields. The
[model guidance](https://developers.openai.com/api/docs/guides/latest-model) supports
reasoning-effort terminology, not propagation or enforcement by this desktop runtime.
