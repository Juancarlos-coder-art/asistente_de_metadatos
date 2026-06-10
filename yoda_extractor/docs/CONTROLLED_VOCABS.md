# Controlled Vocabularies

Structured reference lists used to map free-text metadata fields to standardized linked-data URIs.

---

## Fetching / updating vocabularies

```bash
python controlled_vocabularies/fetch_vocabularies.py
```

The orchestrator reads `list_vocabularies.csv` and dispatches each row to the right fetcher based on `Mode_extracted_JSON`:

```
controlled_vocabularies/
  fetch_vocabularies.py          ← entry point (orchestrator)
  fetchers/
    iterative.py                 ← Mode = Iterative  (fetches RDF endpoints over the network)
    personal_data.py             ← Mode = Personal_data  (parses bundled RDF locally, no network)
  build_vector_db.py             ← preload script for the RAG vector tables
  vocabs/                        ← generated JSON files (one per vocabulary)
  db/                            ← embedded LanceDB (generated, git-ignored)
  list_vocabularies.csv
  personal_data.rdf              ← bundled RDF for personal data
```

| Mode | Fetcher | Description |
|------|---------|-------------|
| `Iterative` | `fetchers/iterative.py` | Fetches root RDF, discovers concept URIs, then fetches each one individually |
| `Personal_data` | `fetchers/personal_data.py` | Parses the local `personal_data.rdf` — no network required |

---

## Available vocabularies

| Name | Feature field | Fetch mode | Match | Entries | Source | JSON |
|------|--------------|------------|-------|---------|--------|------|
| Health Categories | `health_category` | Iterative | LLM | 17 | [link](https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/healthcategories) | `vocabs/health_category.json` |
| Dataset Type | `dcat_type` | Iterative | LLM | 25 | [link](http://publications.europa.eu/resource/authority/dataset-type) | `vocabs/dcat_type.json` |
| Health Theme | `health_theme` | Iterative | LLM | 20 | [link](http://13.81.34.152:1101/resource/authority/health-theme) | `vocabs/health_theme.json` |
| Coding System | `coding_system` | Iterative | LLM | 21 | [link](https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/coding-system) | `vocabs/coding_system.json` |
| Standard | `conforms_to` | Iterative | LLM | 13 | [link](https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/standard) | `vocabs/conforms_to.json` |
| Personal Data Categories | `personal_data` | Personal_data | RAG | 231 | [link](https://w3id.org/dpv/pd) | `vocabs/personal_data.json` |

---

## JSON format

Each file is a map from concept code to its extracted fields:

```json
{
  "PHDR": {
    "uri": "https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/healthcategories/PHDR",
    "prefLabel": "Data from population-based health data registries such as public health registries"
  },
  "EHCT": {
    "uri": "https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/healthcategories/EHCT",
    "prefLabel": "Data from clinical trials...",
    "definition": "..."
  }
}
```

Fields extracted (English only, duplicates across fields removed — first wins):

| RDF predicate | JSON key |
|---------------|----------|
| `skos:prefLabel` | `prefLabel` |
| `skos:definition` | `definition` |
| `dct:description` | `description` |

If a concept has multiple values for the same predicate they are stored as a list; single values are stored as a string.

---

## Vocabulary Matcher

For each vocabulary in `list_vocabularies.csv`, the `VocabularyMatcher` extractor selects the best-matching URI for the current dataset. The strategy is chosen per vocabulary via the **`Metadata-Processed-By`** column:

| `Metadata-Processed-By` | Strategy |
|-------------------------|----------|
| `LLM` | One LLM call per vocabulary |
| `RAG` | Embedding similarity search over a precomputed LanceDB table |

### LLM strategy

1. Loads the vocab JSON from `controlled_vocabularies/vocabs/<feature>.json`.
2. Calls the LLM with the dataset's `title_en`, `notes_en`, and `keyword_en` plus the **full vocabulary JSON** (all fields per entry, minus `uri`).
3. The LLM returns the single best-matching code (or `"NONE"`).
4. Composes the full URI as `<base_url>/<code>` from the CSV.

LLM prompts are logged at DEBUG level — run with `--log-level DEBUG` to inspect them.

Falls back to `title` / `notes` / `keyword` (Spanish) if the English versions are empty.

### RAG strategy

A local, free embedding model (**all-MiniLM-L6-v2**, 384 dims) plus an embedded **LanceDB** database (`controlled_vocabularies/db/`). One table per vocabulary, built ahead of time:

1. **Preload** (`build_vector_db.py`): for each vocab entry, joins all fields except `uri` into one text, embeds it, and stores `{code, text, uri, vector}` in the table `<feature>`.
2. **Runtime**: embeds the dataset's `purpose_en`, `title_en`, `notes_en`, `keyword_en` into one query vector, runs a nearest-neighbour search, and returns the `uri` stored on the closest entry (plain text — no URI composition needed).

The embedding model is downloaded and cached locally by `sentence-transformers` on first use. The database is rebuildable, so `controlled_vocabularies/db/` is git-ignored.

```bash
# (re)build the vector tables — run once, or whenever a vocab JSON changes
python controlled_vocabularies/build_vector_db.py
```

### Input fields used

| Strategy | Fields | Source |
|----------|--------|--------|
| LLM | `title_en`, `notes_en`, `keyword_en` | `llm_metadata` extractor |
| RAG | `purpose_en`, `title_en`, `notes_en`, `keyword_en` | `llm_metadata` extractor |

### Output example

```json
{
  "health_category": "https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/healthcategories/RPDG",
  "dcat_type": "http://publications.europa.eu/resource/authority/dataset-type/HVD",
  "health_theme": "http://13.81.34.152:1101/resource/authority/health-theme/CLIMATE_HEALTH",
  "coding_system": "https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/coding-system/SNOMED-CT",
  "conforms_to": "https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/standard/FHIR",
  "personal_data": "https://w3id.org/dpv/pd#MentalHealth"
}
```

If no entry fits, the field is omitted. Errors are accumulated into the global `errors` array.

### Edge cases

| Situation | Behaviour |
|-----------|-----------|
| Vocab JSON not found (LLM) | Field skipped, error added to global `errors` |
| LLM returns `NONE` | Field omitted |
| LLM returns unknown code | Field omitted, error added to global `errors` |
| LLM call fails | Field omitted, error added to global `errors` |
| Vector table missing (RAG) | Field skipped, error added — run `build_vector_db.py` |
| RAG search fails | Field omitted, error added to global `errors` |
| No metadata available | Field skipped |

---

## Adding a new vocabulary

1. Add a row to `list_vocabularies.csv` with the appropriate `Mode_extracted_JSON` (fetch mode) and `Metadata-Processed-By` (match strategy) values.
2. Run `python controlled_vocabularies/fetch_vocabularies.py` — the JSON is generated automatically.
3. If the new vocabulary uses `RAG`, run `python controlled_vocabularies/build_vector_db.py` to (re)build its vector table.
4. No code changes needed.
