# Invoice ledger
Python standard library only. Run `python3 -m unittest -v`.

The public functions are `summarize(text)` and `render(totals)`.
CSV fields may have surrounding whitespace, including header names and status.
A leading UTF-8 BOM is accepted. Customer names are stripped, but case is preserved.
Status comparison is case-insensitive. Only paid rows need amount validation.
Monetary values must be finite decimal numbers. Round EACH row to cents with
ROUND_HALF_UP, including refunds; do not sum floating-point amounts.
Blank amounts are zero. Duplicate customer rows aggregate. Reports sort by name.
Malformed paid values raise ValueError containing `row N`, where N is the
physical ending line of that CSV record (header is line 1). Quoted multiline
customer names are supported by the CSV reader. The renderer keeps its API.
