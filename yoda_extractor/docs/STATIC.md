# Static Extractor

Produces fields whose values are fixed at extraction time and require no record inspection.

## Output

```json
{
  "issued": "2024-06-01T10:23:45.123Z",
  "modified": "2024-06-01T10:23:45.123Z"
}
```

Both values are set to the **current UTC datetime** when `result()` is called, formatted as ISO-8601 with millisecond precision (`YYYY-MM-DDTHH:MM:SS.mmmZ`).

## Fields

| Field | Description |
|-------|-------------|
| `issued` | UTC datetime when the metadata was first generated |
| `modified` | UTC datetime when the metadata was last generated (same as `issued` on first run) |

## Post-processing: language normalization

`static.py` also exports `normalize_language(output)`, called by `main.py` after all extractors are merged. It expands a bare ISO 639-3 code produced by `llm_metadata` into the EU Publications Office URI:

```
"ENG"  →  "http://publications.europa.eu/resource/authority/language/ENG"
"spa"  →  "http://publications.europa.eu/resource/authority/language/SPA"
```

The function is a no-op if `language` is already a URI or empty.

## Notes

- No LLM call, no record sampling — `update()` is a no-op.
- Values are always overwritten on each run; update `modified` manually if you need to preserve a previous issue date.
