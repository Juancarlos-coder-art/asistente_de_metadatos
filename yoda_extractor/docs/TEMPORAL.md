# Temporal Resolution (`extractors/temporal.py`)

Resolves the  **date fields** — `temporal_coverage`  — into a
single `{"start", "end"}` range each. It is **not** a streaming extractor and does no column
auto-detection: the columns are already chosen and cleaned by the [`structure_tmpt`](STRUCTURE.md)
step. `temporal.py` only does the second half of the job — join the cleaned date parts and
standardize them — and is invoked from [`dataframe_statistics`](DATA_FRAME_STATISTICS.md).

## Input

A date field from `structure_tmpt` is an **array of date-mapping objects**. Each mapping has three
keys (`year`, `month`, `day`); each part is either `null` or `{"column", "transform"}`, already
cleaned on its own by the structure transform (which assigns to `df['<part>_<column>']`):

```json
[
  {
    "year": {
      "column": "Year",
      "transform": [
        {"op": "to_numeric", "params": {}},
        {"op": "to_string", "params": {}}
      ]
    },
    "month": {
      "column": "Month",
      "transform": [
        {"op": "split", "params": {"sep": "[,/;-]", "index": 0}},
        {"op": "strip", "params": {}}
      ]
    },
    "day": null
  }
]
```

Several mappings appear when different column sets independently express a date (e.g. a
start-date triple and an end-date triple).

## Output

A single global range across every mapping of the field, or `null` when nothing resolves:

```json
{ "start": "1995-01-01", "end": "2019-10-01" }
```

The same shape is returned for both `temporal_coverage`, and merged at
the top level of the final output by `dataframe_statistics`.

---

## How it works

For each date-mapping, in order:

### 1. Resolve each part (`_resolve_part`)

Runs the part's `transform` (a list of DSL step dictionaries) using `evaluate_dsl` on the DataFrame. If the transform list is empty, the raw `column` is used directly. Any exception during execution logs a warning and drops that part (returns `None`).

### 2. Join into one column (`build_date_series`)

The cleaned parts are cast to strings and concatenated into a single `"YYYY-MM-DD"` Series:

- **Year is mandatory** — if it does not resolve, the whole mapping is skipped.
- A missing or blank **month**/**day** defaults to `"01"`, so every row with a year yields a
  parseable date.
- Per-row missing tokens (`<NA>`, `nan`, `none`, `nat`, `null`, empty) are treated as missing —
  rows with a missing year stay missing and are dropped before parsing.

### 3. Standardize each value (`coverage`)

Every joined string is run through [`utils/date_utils.parse_date`](../utils/date_utils.py):

1. **Fast path** — `strptime` against an explicit format list. This now includes month-name
   combinations produced by the join, e.g. `%Y-%B-%d` (`2017-April-01`), `%Y-%b-%d`, `%Y-%B`,
   `%Y-%b`, alongside the numeric `%Y-%m-%d` / `%Y-%m`.
2. **Slow path** — `dateutil.parser.parse` for anything else, returning a timezone-naive
   datetime. Values that are too short, purely numeric, or known non-date tokens are rejected
   before any parse attempt.

The minimum parsed date across all mappings becomes `start`, the maximum becomes `end`.

---

## Why parts are cleaned separately

Combining `year`/`month`/`day` inside a single structure transform (with `pd.to_datetime`) was
fragile: one bad cast — e.g. `df['Year'].astype(int)` on a column with `NaN` — raises
`IntCastingNaNError` and discards the **entire** date, even the valid rows. Splitting the work so
each part is cleaned independently and joined here keeps a failure in one part from sinking the
others, and isolates the date-standardization logic in one place.

---

## Edge cases

| Situation | Behaviour |
|-----------|-----------|
| Field has no mappings (`[]`) | Returns `null` |
| A mapping has no `year` part | That mapping is skipped |
| `month`/`day` absent or blank | Defaults to `"01"` |
| A part's transform raises | Warning logged; that part dropped |
| Cell holds multiple values (`"May, June"`) | First token taken during structure cleaning |
| Month given as a name (`April`) | Parsed via `%Y-%B-%d` / dateutil |
| Mixed formats across rows/mappings | All handled; global min/max computed across them |
| Timezone-aware values | Timezone info stripped; comparison uses naive datetimes |
