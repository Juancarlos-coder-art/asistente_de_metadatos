# Static Extractor

Produces fields whose values are fixed at extraction time and require no record inspection.

## Output

```json
{
  "issued": "2024-06-01T10:23:45.123Z",
  "modified": "2024-06-01T10:23:45.123Z",
  "theme": ["http://publications.europa.eu/resource/authority/data-theme/HEAL"],
  "legal_basis": {
    "description": "RGPD",
    "source": "https://www.boe.es/doue/2016/119/L00001-00088.pdf"
  },
  "version": "1.0",
  "has_version": ["1.0"],
  "applicable_legislation": [
    {
      "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
      "label": "GDPR"
    },
    {
      "uri": "http://data.europa.eu/eli/reg/2025/327/oj",
      "label": "Reglamento EHDS"
    }
  ]
}
```

`issued` and `modified` are set to the **current UTC datetime** when `result()` is called, formatted as ISO-8601 with millisecond precision (`YYYY-MM-DDTHH:MM:SS.mmmZ`). `theme` is a fixed constant.

## Fields

| Field | Description |
|-------|-------------|
| `issued` | UTC datetime when the metadata was first generated |
| `modified` | UTC datetime when the metadata was last generated (same as `issued` on first run) |
| `theme` | Fixed value: `["http://publications.europa.eu/resource/authority/data-theme/HEAL"]` |
| `legal_basis` | Fixed object: `{"description": "RGPD", "source": "https://www.boe.es/doue/2016/119/L00001-00088.pdf"}` |
| `format` | File extension of the input file in lowercase (e.g. `"csv"`, `"json"`). Omitted if the file has no extension. Overridable via `--input-json`. |
| `size` | Size of the input file in bytes. Omitted if the file cannot be stat'd. Overridable via `--input-json`. |
| `hash` | SHA-256 hex digest of the input file contents. Omitted if the file cannot be read. Overridable via `--input-json`. |
| `hash_algorithm` | Fixed value `"SHA-256"`. Set automatically alongside `hash`; preserved from `--input-json` when `hash` is prefilled. |
| `mimetype` | IANA MIME type derived from the input file extension (e.g. `"text/csv"`, `"application/json"`). Omitted if the extension is unknown. Overridable via `--input-json`. |
| `applicable_legislation` | Default array: `[{"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}, {"uri": "http://data.europa.eu/eli/reg/2025/327/oj", "label": "Reglamento EHDS"}]`. Overridable via `--input-json`. |
| `description` | Copy of `notes` from the LLM extractor (or `notes` from `--input-json` if prefilled). Skipped if `description` is already prefilled. |
| `name` | Copy of `title` from the LLM extractor (or `title` from `--input-json` if prefilled). Skipped if `name` is already prefilled. |
| `version` | Auto-incremented version string (e.g. `"1.0"`, `"2.0"`). See versioning rules below. |
| `has_version` | Array of all previous versions plus the new one appended at the end (e.g. `["1.0", "2.0"]`). See versioning rules below. |

## Post-processing: array normalization

`static.py` also exports `normalize_array_fields(output)`, called by `main.py` both on the input JSON and on the final merged output. It ensures the following fields are always arrays:

| Field | Coercion |
|-------|----------|
| `language` | Bare ISO 639-3 code expanded to EU authority URI, wrapped in array |
| `purpose`, `purpose_en_tmpt` | String wrapped in single-element array |
| `keyword`, `keyword_en_tmpt` | Semicolon-separated string split into array elements |
| `has_version` | String wrapped in single-element array |

## Notes

- No LLM call, no record sampling — `update()` is a no-op.
- `issued` and `modified` are always overwritten on each run; pre-fill them via `--input-json` to preserve existing dates.
- `theme` and `legal_basis` default to fixed values but can be overridden via `--input-json` if the provided value has content.
- `mimetype` is resolved from the input file extension via `utils/mime_types.py`, which loads the mapping from `utils/mime.json`. The MIME type data is sourced from [jshttp/mime-db](https://github.com/jshttp/mime-db).
- `description` is derived in `finalize()` (after all extractors run) by copying `notes`. Priority: `notes` from `--input-json` → `notes` from the LLM extractor. Skipped entirely if `description` is already prefilled via `--input-json`.
- `name` is derived the same way by copying `title`. Skipped entirely if `name` is already prefilled via `--input-json`.
- `version` is auto-incremented on each run: if `--input-json` contains a numeric value it is incremented by 1 and formatted as `"X.0"`; if absent or empty it defaults to `"1.0"`; if the value is non-numeric it is preserved unchanged.
- `has_version` accumulates all versions as a sorted array and appends the next one (`max + 1`). If absent or empty it starts at `["1.0"]`. If any element is non-numeric the array is preserved unchanged.
