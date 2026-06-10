# LLM Metadata Extractor

Uses Gemini to infer high-level metadata from the filename and a random sample of records. Runs once after the full stream is consumed.

## Output

```json
{
  "llm_metadata": {
    "purpose": "To record and track mosquito presence across sampling points in Spain.",
    "language": "spa",
    "title": "Distribución del mosquito Culex pipiens en España",
    "notes": "Dataset containing georeferenced records of Culex pipiens presence collected between 1995 and 2019 across Spanish provinces.",
    "keyword": "mosquito; Culex pipiens; Spain; species distribution; vector",
    "population_coverage": "Datos de presencia de mosquitos recopilados en todas las provincias españolas excepto las Islas Canarias, entre 1995 y 2019.",
    "purpose_en": "To record and track mosquito presence across sampling points in Spain.",
    "title_en": "Distribution of the mosquito Culex pipiens in peninsular Spain and the Balearic Islands",
    "notes_en": "Dataset containing georeferenced records of Culex pipiens presence collected between 1995 and 2019 across Spanish provinces.",
    "keyword_en": "mosquito; Culex pipiens; Spain; species distribution; vector",
    "errors": []
  }
}
```

If a field cannot be determined it is set to `""` and an entry is added to `errors`:

```json
{
  "llm_metadata": {
    "purpose": "",
    "language": "eng",
    "title": "Unknown dataset",
    "notes": "...",
    "keyword": "...",
    "population_coverage": "",
    "purpose_en": "",
    "title_en": "",
    "notes_en": "",
    "keyword_en": "",
    "errors": ["Could not determine purpose from the available sample"]
  }
}
```

---

## How it works

### 1. Reservoir sampling (during streaming)

While records stream through, the extractor maintains a random sample of at most `SAMPLE_SIZE` (default **20**) records using **Algorithm R**:

- The first 20 records are kept directly.
- For every subsequent record `i`, a random index `j` in `[0, i)` is drawn. If `j < 20`, the new record replaces the one at position `j`.

This guarantees a uniform random sample with O(1) memory regardless of dataset size.

### 2. Sample truncation (at result time)

Before sending to the LLM, the sample is serialised to JSON lines and truncated so the total does not exceed `MAX_CHARS` (default **30 000** characters). Records are included in order until the limit is reached; the rest are dropped silently.

### 3. Prompt construction

The prompt sent to Gemini includes:

- The **filename** (basename only, no path)
- The **number of records** in the sample
- The **serialised sample** (one JSON object per line)
- Explicit instructions to return a valid JSON object with the ten target fields and an `errors` array

### 4. Gemini call

The call is made via the `google-genai` SDK using the model `gemini-3.1-flash-lite`. The API key is read from the `GEMINI_API_KEY` environment variable at call time — never stored in code or files.

### 5. Response parsing

The raw response is stripped of any markdown code fences (` ```json ... ``` `) that Gemini may add, then parsed as JSON. If parsing fails, all fields are returned as `""` and the parse error is reported in `errors`.

---

## Configuration constants (`extractors/llm.py`)

| Constant | Default | Description |
|----------|---------|-------------|
| `SAMPLE_SIZE` | `20` | Maximum number of records in the sample |
| `MAX_CHARS` | `30 000` | Maximum total characters sent to the LLM |

---

## Setup

```bash
export GEMINI_API_KEY=your_key_here
```

The extractor raises a clear error at result time if the variable is not set.

---

## Edge cases

| Situation | Behaviour |
|-----------|-----------|
| No records in the dataset | Returns all fields as `""` with error `"No records to sample"` |
| Sample exceeds `MAX_CHARS` | Records truncated until the limit is met |
| Gemini returns markdown fences | Fences stripped before JSON parse |
| Gemini returns unparseable text | All fields `""`, parse error in `errors` |
| API key not set | All fields `""`, error `"GEMINI_API_KEY environment variable not set"` |
| Network or API error | All fields `""`, exception message in `errors` |
