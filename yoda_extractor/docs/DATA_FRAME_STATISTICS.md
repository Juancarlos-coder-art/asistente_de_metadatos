# DataFrame Statistics Extractor

Computes concrete statistics from an already-loaded pandas DataFrame using the
column mappings produced by the [Structure Extractor](STRUCTURE.md).

Unlike the streaming extractors, this one operates on a full DataFrame and requires
the `structure` output as a second input.

## Usage

`DataFrameStatisticsExtractor` runs automatically inside `main.py` after the streaming
pass, whenever `structure` is present in `ALL_EXTRACTORS`. No extra configuration needed.

It can also be called directly:

```python
import pandas as pd
from extractors.dataframe_stats import DataFrameStatisticsExtractor

structure_result = {...}   # output of StructureExtractor.result()
df = pd.read_csv("dataset.csv")
stats = DataFrameStatisticsExtractor().extract(df, structure_result)
```

## Output

```json
{
  "number_of_records": 6755,
  "number_of_unique_individuals": 42,
  "min_typical_age": 0,
  "max_typical_age": 99,
  "temporal_coverage": {"start": "1995-01-01", "end": "2019-12-31"}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `number_of_records` | `int` | Total number of rows in the DataFrame. |
| `number_of_unique_individuals` | `int \| null` | Count of distinct values in the identifier column(s). `null` if no valid mapping. |
| `min_typical_age` | `int \| float \| null` | Min numeric value from the age column(s). `null` if no valid mapping. |
| `max_typical_age` | `int \| float \| null` | Max numeric value from the age column(s). `null` if no valid mapping. |
| `temporal_coverage` | `{start, end} \| null` | Global min/max date across **all** `temporal_coverage` mappings. `null` if no parseable dates found. |

## How it works

### 1. `number_of_records`

`len(df)` — straightforward row count.

### 2. `number_of_unique_individuals`

Iterates the structure mappings for this field. Applies the transform if present
(same exec mechanism as the age fields), then calls `df[col_name].nunique()` on
the resulting column. Returns the first successful result.

### 4. `temporal_coverage`

Columns are taken directly from `structure["temporal_coverage"]` — no auto-detection is performed. For each mapping:
1. Resolves the target Series via `_resolve_series`: applies the pandas transform if present (creating a derived column), otherwise uses the first column in `columns` directly.
2. Parses dates vectorially with `pd.to_datetime(series, errors="coerce")`.
3. Tracks min and max per mapping; returns global min (start) and max (end) across all mappings.

Returns `{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}` or `null` if no mappings or no parseable dates.

### 3. Age fields (`min_typical_age`, `max_typical_age`)

For each field the extractor iterates over the array of mapping objects from the
structure output and tries each one in order, returning the first successful result:

1. **Apply transform (if present)** — the pandas expression from `transform` is
   executed on a working copy of the DataFrame. The new derived column (e.g.
   `min_typical_age_mod_1`) is created in that copy.

   ```python
   # example transform from structure output
   "df['min_typical_age_mod_1'] = (pd.Timestamp.now() - pd.to_datetime(df['birth_date'])).dt.days // 365"
   ```

2. **Identify target column** — if a transform was executed, the target column is the
   one assigned by the transform (parsed from `df['<name>'] = ...`). Otherwise the
   first entry in `columns` is used.

3. **Coerce to numeric** — `pd.to_numeric(..., errors='coerce')` so non-numeric
   values are silently dropped.

4. **Aggregate** — `series.min()` for `min_typical_age`, `series.max()` for
   `max_typical_age`. Integer when the result has no fractional part, float otherwise.

5. **Fallback** — if a mapping fails (missing column, transform error, all-NaN series),
   the next mapping in the array is tried. Returns `null` if all mappings fail.

## Edge cases

| Situation | Behaviour |
|-----------|-----------|
| No mapping in structure | Returns `null` |
| Column not found in DataFrame | Skips that mapping, tries next |
| Transform raises an exception | Skips that mapping, tries next |
| All values non-numeric | Skips that mapping, tries next |
| Result is whole number (e.g. `18.0`) | Returned as `int` (`18`) |
| Result has fractional part (e.g. `18.5`) | Returned as `float` |
