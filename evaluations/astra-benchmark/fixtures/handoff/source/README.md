# NoteBatch
A small local note-export utility using Python's standard library.

Run `python3 -m notebatch notes.json` to emit a JSON array.
Run `python3 -m unittest -v` to test the package.
Public functions: `normalize_entries(entries)`, `read_entries(text)`,
`render_json(entries)`.

## Input normalization
Input is a list of objects. Each object has a nonempty string title after
stripping whitespace. Tags are an optional list of strings, defaulting to [].
Strip each tag, discard empty tags, deduplicate exactly and sort by Python string
order. Tag matching is case-sensitive. Output contains only title and tags;
unknown fields are ignored. Preserve entry order, and never mutate input data.
Invalid entry collections, titles, or tags raise ValueError. read_entries parses
JSON and applies normalization. Legacy CLI accepts a file and emits a JSON array.
