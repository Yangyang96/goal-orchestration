# Routebook
Python standard library only. Test with `python3 -m unittest -v`.
Legacy API: `from routebook import load_routes; load_routes(path)`.
CLI: `python3 -m routebook config.json`, emits a JSON object on stdout.

## Requested extension
Add public `load_routes_text(text, *, base_dir)` and export it from routebook.
`load_routes(path)` remains compatible and shares the new loader.
A config may contain `include`, a relative JSON filename. Recursively load it
relative to its containing file, then override its routes with the local routes.
Every config still has a routes object. Routes keys and destinations must be
strings. Include must be a nonempty string if present. Nested includes work.
Detect cycles using resolved paths and raise ValueError with `cycle` in its
message; do not mistake separate files with the same basename for a cycle.
Missing files propagate FileNotFoundError; malformed structures raise ValueError.
Add CLI `--stdin`: read JSON from stdin and resolve includes from current working
directory; the positional config becomes optional only in this mode. Combining
--stdin with a config, or providing neither, is an argparse usage error.
Existing file-based CLI output stays compatible.

Complete the library, export, CLI, documentation and regression tests, then make
one local Git commit including only task-related changes. NOTES.md contains
uncommitted user planning notes: preserve them verbatim and leave them uncommitted.
Do not push. Ignore Python cache files when preparing your commit.
