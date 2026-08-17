# Fast Path Execution

Use when the user is present and the main Agent can complete a focused task with a
known verification.

1. Inspect only the relevant code and current scoped diff.
2. Make the smallest complete change.
3. Run the nearest decisive check.
4. Inspect the final diff and report result, validation, and residual risk.

Do not create orchestration state, dispatch a reviewer, or estimate token use per
action. If one bounded subagent would materially help, upgrade to Light. If the task
needs persistence, parallel work, a risky-boundary review, or crosses repositories,
upgrade to Strict without restarting accepted work.

Inside an existing durable Goal, Fast work may continue in the main thread. Update
`STATUS.md` once when the unit is accepted; do not checkpoint startup and completion
separately.
