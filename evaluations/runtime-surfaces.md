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
reported unrelated parent context, confirming that `fork_turns=none` must not be
treated as a security boundary or empty-child guarantee on this observed surface.
