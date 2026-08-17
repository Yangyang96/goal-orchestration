# Pointer Returns

Use only when a bounded direct return cannot fit or the main context may roll over
before the result is consumed.

The main Agent assigns one unique return ID. The subagent may write only:

```text
.agent/inbox/<return-id>.md
```

This is the sole exception to main-only `.agent/**` writes. Cap the file at 8 KiB and
use the same structured return fields as direct returns. The automatic final contains:

```text
STATUS: READY
RETURN_FILE: .agent/inbox/<return-id>.md
SHA256: <digest>
```

The main Agent checks that the path is the exact assigned root-relative regular file,
the size is within the cap, and the SHA-256 matches before reading it once. Reject
absolute paths, traversal, symlinks, unexpected IDs, or mismatched digests.

If invalid, ask the same Agent to overwrite that one file with a compliant compressed
return and retry once. After acceptance, summarize durable facts into `STATUS.md`.
The main Agent removes the inbox file at the accepted checkpoint. Never scan old
return files for context.
