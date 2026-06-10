# Yoda Extractor

A streaming metadata extractor for large structured data files. Processes records one at a time (O(1) memory) and produces metadata summaries without loading the full file into memory.

## Profile support
HealthDCAT-AP: https://healthdataeu.pages.code.europa.eu/healthdcat-ap/releases/release-7/

## Example of output

```json
{
  "purpose": "Datos de presencia de Culex pipiens en España obtenidos mediante distintas técnicas de muestreo: Centre for Disease Control and Prevention (CDC), BG-Sentinel, Encephalitis Vector Survey (EVS), trampas de oviposición, aspiradores para muestreo de mosquitos adultos, y dippers para muestreo de larvas. Se indican las coordenadas (latitud y longitud, grados decimales) de cada punto de muestreo (N= 6,755), así como el Municipio, Provincia, Comunidad Autónoma, periodo/s y año correspondientes. Se indica también la persona responsable de los datos de cada muestreo. Los datos fueron utilizados para determinar la distribucion de Culex pipiens, una espcie vectora del virus West Nile en España y analizar el posible impacto del cambio climatico sobre su distribución",
  "language": "http://publications.europa.eu/resource/authority/language/ENG",
  "number_of_unique_individuals": 1,
  "number_of_records": 6755,
  "hdab": {
    "special_opening_hours_description": "08:00-15:00",
    "special_opening_hours_frequency": "http://publications.europa.eu/resource/authority/frequency/ANNUAL",
    "name": "CSIC - Estación Biológica de Doñana",
    "type": "http://13.81.34.152:1101/resource/authority/publisher-type/research-academic-org",
    "contact": "https://www.ebd.csic.es/",
    "email": "jordi@ebd.csic.es",
    "telephone": "954232340",
    "opening_hours_description": "08:00-15:00",
    "opening_hours_frequency": "http://publications.europa.eu/resource/authority/frequency/DAILY"
  },
  "access_rights": "http://publications.europa.eu/resource/authority/access-right/PUBLIC",
  "title": "Distribución del mosquito Culex pipiens en España peninsular y Baleares",
  "identifier": "http://hdl.handle.net/10261/215542",
  "notes": "Datos de presencia de Culex pipiens en España obtenidos mediante distintas técnicas de muestreo: Centre for Disease Control and Prevention (CDC), BG-Sentinel, Encephalitis Vector Survey (EVS), trampas de oviposición, aspiradores para muestreo de mosquitos adultos, y dippers para muestreo de larvas. Se indican las coordenadas (latitud y longitud, grados decimales) de cada punto de muestreo (N= 6,755), así como el Municipio, Provincia, Comunidad Autónoma, periodo/s y año correspondientes. Se indica también la persona responsable de los datos de cada muestreo.",
  "health_category": "http://13.81.34.152:1101/resource/authority/healthcategories/RPDG",
  "theme": "http://publications.europa.eu/resource/authority/data-theme/ENVI",
  "dcat_type": "http://publications.europa.eu/resource/authority/dataset-type/HVD",
  "provenance": "Recopilamos datos sobre la presencia de Cx. pipiens (que abarca los biotipos pipiens y molestus) en España de diferentes grupos de investigación españoles y agencias nacionales de vigilancia y control de mosquitos. La información sobre la presencia de esta especie se basó en capturas realizadas utilizando métodos que incluyen el Centro para el Control y la Prevención de Enfermedades (CDC), BG-Sentinel, Encephalitis Vector Survey (EVS), trampas grávidas y de oviposición, aspiradores para muestreo de mosquitos adultos y \\\"dippers\\\" para muestreo de larvas. El muestreo incluyó un total de 6.755 registros recopilados entre 1995 y 2019 de todas las provincias españolas excepto las Islas Canarias. Los registros de las Islas Canarias (N = 116) se excluyeron debido a su distancia (unos 940 km) del continente europeo y los diferentes patrones climáticos. Cada registro fue georreferenciado utilizando coordenadas de longitud y latitud con al menos cinco decimales.",
  "keyword": "Climate change; Culicidae; Habitat suitability; Species distribution model; Vector-borne pathogens",
  "population_coverage": "Todos",
  "min_typical_age": 0,
  "max_typical_age": 99,
  "personal_data": "https://w3id.org/dpv/pd#Country",
  "legal_basis": {
    "description": "http://data.europa.eu/eli/reg/2016/679/oj",
    "source": "http://data.europa.eu/eli/reg/2016/679/oj"
  },
  "retention_period": {
    "start": "1995-01-01",
    "end": "2026-12-31"
  },
  "health_theme": "http://13.81.34.152:1101/resource/authority/health-theme/CLIMATE_HEALTH",
  "code_values": "SNOMED CT",
  "coding_system": {
    "label": "RxNorm",
    "uri": "https://hdeu-dcat.acceptance.data.health.europa.eu/resource/authority/coding-system/RXNORM"
  },
  "contact": {
    "email": "jordi@ebd.csic.es",
    "url": "https://www.ebd.csic.es/"
  },
  "distribution_access_url": "http://hdl.handle.net/10261/215542",
  "publisher": {
    "name": " J Figuerola ",
    "type": "http://13.81.34.152:1101/resource/authority/publisher-type/university",
    "contact_page": "https://www.ebd.csic.es/",
    "email": "jordi@ebd.csic.es",
    "telephone": "954232340",
    "opening_hours_description": "08:00-15:00",
    "opening_hours_frequency": "http://publications.europa.eu/resource/authority/frequency/DAILY",
    "special_opening_hours_description": "08:00-15:00",
    "special_opening_hours_frequency": "http://publications.europa.eu/resource/authority/frequency/ANNUAL"
  },
  "publisher_note": "No aplica",
  "creator": {
    "name": " J Figuerola ",
    "email": "jordi@ebd.csic.es",
    "url": "http://hdl.handle.net/10261/215542",
    "type": "http://13.81.34.152:1101/resource/authority/publisher-type/university"
  },
  "qualified_attribution": {
    "qualified_attribution_agent_name": " J Figuerola ",
    "qualified_attribution_agent_type": "http://13.81.34.152:1101/resource/authority/publisher-type/research-infra",
    "qualified_attribution_agent_contact_page": "https://www.ebd.csic.es/",
    "qualified_attribution_agent_email": "jordi@ebd.csic.es",
    "qualified_attribution_role": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#owner"
  },
  "was_generated_by": "http://13.81.34.152:1101/resource/authority/health-activity/BIOBANK_COLLECTION",
  "spatial": "http://publications.europa.eu/resource/authority/country/ESP",
  "temporal_coverage": {
    "start": "1995-01-01",
    "end": "2019-12-31"
  },
  "temporal_resolution": "24 años",
  "spatial_resolution_in_meters": "4",
  "frequency": "http://publications.europa.eu/resource/authority/frequency/DAILY",
  "issued": "2020-06-30",
  "modified": "2020-06-30",
  "alternate_identifier": "10.1016/j.envres.2020.109837",
  "conforms_to": {
    "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
    "label": "GDPR"
  },
  "related_resource": {
    "uri": "http://hdl.handle.net/10261/215542",
    "label": "Dataset Culex pipiens"
  },
  "is_referenced_by": "Gangoso L, Aragonés D, Martínez-de la Puente J, Lucientes J, Delacour-Estrella S, Estrada Peña R, Montalvo T, Bueno-Marí R, Bravo-Barriga D, Frontera E, Marqués E, Ruiz-Arrondo I, Muñoz A, Oteo JA, Miranda MA, Barceló C, Arias Vázquez MS, Silva-Torres MI, Ferraguti M, Magallanes S, Muriel J, Marzal A, Aranda C, Ruiz S, González MA, Morchón R, Gómez-Barroso D, Figuerola J. Determinants of the current and future distribution of the West Nile virus mosquito vector Culex pipiens in Spain. Environ Res. 2020 Sep;188:109837. doi: 10.1016/j.envres.2020.109837. Epub 2020 Jun 23. PMID: 32798954.",
  "url": "http://hdl.handle.net/10261/215542",
  "documentation": {
    "uri": "http://hdl.handle.net/10261/215542",
    "label": "Documentation y datos"
  },
  "version": "1",
  "has_version": "No",
  "version_notes": "No aplica",
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


## Supported formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | |
| JSON | `.json` | |
| XML | `.xml` | Nested elements flattened to dot-notation; simple leaf text uses the tag name directly (no `._text` suffix) |
| Excel | `.xlsx`, `.xls` | |
| Parquet | `.parquet` | |

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py <file> [--output json|text] [--log-level LEVEL] [--log-file PATH]
```

Always saves a timestamped copy to `tests-output/<file>_<YYYYMMDD_HHMMSS>.json` regardless of output format.

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--output` | Output format: `json` or `text` | `json` |
| `--log-level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` or `LOG_LEVEL` env var |
| `--log-file` | Additional path to write logs to a file | — |

### Log levels

| Level | What you see |
|-------|-------------|
| `ERROR` | LLM call failures, JSON parse errors |
| `WARNING` | Transform failures, unknown vocabulary codes, date parse issues |
| `INFO` | Pipeline progress, extractor names, record count, LLM calls, matched URIs |
| `DEBUG` | Full LLM prompt and response for every call, reservoir sampling details |

### Configuring via `.env`

Add `LOG_LEVEL` to your `.env` file (priority: `--log-level` flag > `.env` > `INFO`):

```env
GEMINI_API_KEY=your_key_here
LOG_LEVEL=DEBUG
```

### Examples

```bash
# Default run — JSON output, INFO level, saved to tests-output/
python main.py data.csv

# Human-readable text output
python main.py data.csv --output text

# See full LLM prompts (also adds structure to JSON output)
python main.py data.csv --log-level DEBUG

# Write logs to file
python main.py data.csv --log-file run.log

# Set level via environment variable
LOG_LEVEL=WARNING python main.py data.csv
```

## Pipeline

All extractors run together and their results are merged in order into a single JSON object:

| Step | Extractor | Contributes |
|------|-----------|-------------|
| 1 | `llm_metadata` | `purpose`, `language`, `title`, `notes`, `keyword`, `population_coverage` — top level |
| 2 | `static` | `issued`, `modified` — top level |
| 3 | `structure` | column mappings kept as-is under the `structure` key |
| 4 | `dataframe_statistics` | `number_of_records`, `number_of_unique_individuals`, `min_typical_age`, `max_typical_age` — top level |
| 5 | `vocabulary` | `health_category`, `dcat_type`, `health_theme`, `coding_system`, `conforms_to` — top level |
| 6 | `geospatial` | geospatial fields — top level |

All fields are merged at the top level; later steps overwrite earlier ones for duplicate keys. `errors` are accumulated from all steps. `structure` is **only included when `LOG_LEVEL=DEBUG`** — it holds internal column path mappings used by downstream extractors, not final metadata values. When present it is always the last key.

## Available extractors

### `llm_metadata`

Calls Gemini to infer high-level metadata from the filename and a random sample of up to 20 records (capped at 30 000 chars). Uses reservoir sampling so memory stays O(1) regardless of dataset size.

**Output fields:**

| Field | Description |
|-------|-------------|
| `purpose` | Purpose for which the data is processed (free text) |
| `language` | ISO 639-3 alpha-3 language code (e.g. `eng`, `spa`) |
| `title` | Concise dataset title |
| `notes` | Brief description (2–4 sentences) |
| `keyword` | Keywords separated by `;` |
| `population_coverage` | Free-text description of the population within the dataset |
| `purpose_en` | `purpose` in English |
| `title_en` | `title` in English |
| `notes_en` | `notes` in English |
| `keyword_en` | `keyword` in English |
| `errors` | Array of error messages for fields that could not be determined |

See [`docs/LLM.md`](docs/LLM.md) for full details.

### `static`

Returns fields fixed at extraction time — no record inspection, no LLM call. Also applies post-processing to the merged output (language normalization).

| Field | Description |
|-------|-------------|
| `issued` | UTC datetime when the metadata was first generated (`YYYY-MM-DDTHH:MM:SS.mmmZ`) |
| `modified` | UTC datetime when the metadata was last generated (same as `issued` on first run) |

**Post-processing:** expands the `language` field from a bare ISO 639-3 code to the EU Publications Office URI (e.g. `"ENG"` → `"http://publications.europa.eu/resource/authority/language/ENG"`). No-op if already a URI.

See [`docs/STATIC.md`](docs/STATIC.md) for full details.

### `structure`

Maps the dataset's column paths to predefined metadata fields using Gemini. Returns arrays of column paths — never the values themselves.

Fields come in **two output shapes**:

**Value fields** (`number_of_unique_individuals`, `min_typical_age`, `max_typical_age`, `spatial`) return an **array of mapping objects** `[{"columns": [...], "transform": [...]}, ...]`. Multiple objects when different column combinations independently satisfy the same field. `transform` is always an array of pandas expressions (empty `[]` for a direct single-column mapping). When multiple columns are combined, individual-column preparation steps come first, then the final combination last. Each expression targets `df['<field>_mod_1']`, `df['<field>_mod_2']`… (auto-numbered per field).

**Date fields** (`temporal_coverage` return an **array of date-mapping objects** `[{"year": ..., "month": ..., "day": ...}, ...]`. Each part is either `null` (absent) or `{"column": "<src>", "transform": [...]}`, and is **cleaned on its own** — the transform cleans that single column and assigns to `df['<part>_<column>']` (e.g. `df['year_Year']`). The structure step does **not** combine the parts or call `pd.to_datetime`; joining and date standardization happen in [`extractors/temporal.py`](extractors/temporal.py) (see [`temporal_coverage`](#temporal_coverage) below).

The LLM is instructed to detect European/Spanish number formatting (`.` thousands separator, `,` decimal) from sample values and emit the appropriate parse expression, and to take the first token (`str.split(r'[,/;-]').str[0]`) when a single cell holds multiple values (e.g. a `Month` column with `"May, June"`).

| Field | Description |
|-------|-------------|
| `number_of_unique_individuals` | Column(s) identifying a unique individual/entity |
| `min_typical_age` | Column(s) with minimum age |
| `max_typical_age` | Column(s) with maximum age |
| `spatial` | Column(s) with geographic information |
| `temporal_coverage` | Column(s) with date/time of data collection |
| `errors` | Array of error/ambiguity messages |

Nested records are flattened to dot-notation paths (e.g. `patient.demographics.age`).

See [`docs/STRUCTURE.md`](docs/STRUCTURE.md) for full details.

### `dataframe_statistics`

Computes concrete statistics from a loaded pandas DataFrame using the column mappings from the `structure` extractor. **Not a streaming extractor** — requires a full DataFrame and the `structure` result.

Registered in `ALL_EXTRACTORS` — runs automatically via `finalize()` after the streaming pass, receiving the loaded DataFrame and the `structure` result.

**Output fields:**

| Field | Description |
|-------|-------------|
| `number_of_records` | Total row count (`len(df)`) |
| `number_of_unique_individuals` | Count of distinct values in the identifier column(s); applies transform if needed |
| `min_typical_age` | Min numeric value from the age column(s); applies transform if needed |
| `max_typical_age` | Max numeric value from the age column(s); applies transform if needed |
| `temporal_coverage` | `{"start", "end"}` global min/max date, resolved via `extractors/temporal.py` |

Returns `null` for any field whose structure mapping is empty or fails. See [`docs/DATA_FRAME_STATISTICS.md`](docs/DATA_FRAME_STATISTICS.md) for full details.

### `temporal_coverage` /`

Both date fields are resolved by [`extractors/temporal.py`](extractors/temporal.py) from their `structure` date-mappings (`[{year, month, day}, ...]`). The flow:

1. **Clean each part on its own** — the structure transform for `year`/`month`/`day` cleans that single column (NaN-safe: `pd.to_numeric(..., errors='coerce').astype('Int64').astype(str)`, never bare `.astype(int)` which raises `IntCastingNaNError`).
2. **Join** the cleaned parts into one `"YYYY-MM-DD"` string column per mapping. Year is mandatory; a missing month/day defaults to `"01"`.
3. **Standardize** each value with [`utils/date_utils.py`](utils/date_utils.py) `parse_date` (explicit formats including month-name combos like `%Y-%B-%d`, then `dateutil` fallback).
4. Report the global `{"start", "end"}` (min/max) across every date-mapping of the field.

See [`docs/DATA_FRAME_STATISTICS.md`](docs/DATA_FRAME_STATISTICS.md) for full details.

### `vocabulary`

For each controlled vocabulary in `list_vocabularies.csv`, returns the URI of the best-matching entry. The matching strategy is chosen per vocabulary via the `Metadata-Processed-By` column:

- **LLM** — one LLM call passing the dataset's English metadata (`title_en`, `notes_en`, `keyword_en`) and the full vocabulary entry list.
- **RAG** — embedding similarity search (all-MiniLM-L6-v2 + LanceDB) over a precomputed table, using `purpose_en`, `title_en`, `notes_en`, `keyword_en`.

| Field | Vocabulary | Match |
|-------|-----------|-------|
| `health_category` | Health Categories | LLM |
| `dcat_type` | Dataset Type | LLM |
| `health_theme` | Health Theme | LLM |
| `coding_system` | Coding System | LLM |
| `conforms_to` | Standard | LLM |
| `personal_data` | Personal Data Categories | RAG |

See [`docs/CONTROLLED_VOCABS.md`](docs/CONTROLLED_VOCABS.md) for full details.

### `geospatial`

Detects geographic columns and maps their values to linked-data URIs. No external dependencies required for the built-in vocabularies; GeoNames lookup is opt-in.
See [`docs/GEOSPATIAL.md`](docs/GEOSPATIAL.md) for full details.


## Controlled Vocabularies

Standardized reference lists used to map metadata fields to linked-data URIs. Defined in [`controlled_vocabularies/list_vocabularies.csv`](controlled_vocabularies/list_vocabularies.csv) and cached as JSON under `controlled_vocabularies/vocabs/`.

| Vocabulary | Field | Entries | Fetch mode | Match | JSON |
|------------|-------|---------|------------|-------|------|
| Health Categories | `health_category` | 17 | Iterative | LLM | `vocabs/health_category.json` |
| Dataset Type | `dcat_type` | 25 | Iterative | LLM | `vocabs/dcat_type.json` |
| Health Theme | `health_theme` | 20 | Iterative | LLM | `vocabs/health_theme.json` |
| Coding System | `coding_system` | 21 | Iterative | LLM | `vocabs/coding_system.json` |
| Standard | `conforms_to` | 13 | Iterative | LLM | `vocabs/conforms_to.json` |
| Personal Data Categories | `personal_data` | 231 | Personal_data | RAG | `vocabs/personal_data.json` |

To regenerate all vocabulary JSON files:

```bash
python controlled_vocabularies/fetch_vocabularies.py
```

For vocabularies matched via **RAG**, also (re)build the vector tables after the JSON changes:

```bash
python controlled_vocabularies/build_vector_db.py
```

The fetch orchestrator dispatches each vocabulary based on `Mode_extracted_JSON`; the matcher dispatches based on `Metadata-Processed-By`:

```
controlled_vocabularies/
  fetch_vocabularies.py        ← entry point (fetch JSON)
  fetchers/
    iterative.py               ← fetches RDF endpoints concept-by-concept (network)
    personal_data.py           ← parses bundled personal_data.rdf locally (no network)
  build_vector_db.py           ← preloads the RAG vector tables
  vocabs/                      ← generated JSON files
  db/                          ← embedded LanceDB (generated, git-ignored)
```

See [`docs/CONTROLLED_VOCABS.md`](docs/CONTROLLED_VOCABS.md) for full details.

## Extending

### Add a new reader

Subclass `readers.base.BaseReader` and implement `stream_records()` as a generator that yields one `dict` per record. Register the extension in `readers/__init__.py`.

### Add a new extractor

Subclass `extractors.base.BaseExtractor`, set a unique `name`, and implement:
- `update(record: dict)` — called once per record
- `result() -> dict` — called after all records are consumed

Register the class in `extractors/__init__.py` by adding it to `ALL_EXTRACTORS`.

## Tests

Run all extractors against every dataset under `tests/datasets/`. Each run calls `main.py` as a subprocess — JSON output is printed to stdout and saved automatically to `tests-output/` by `main.py`:

```bash
python tests/test.py
```

Validate the output structure of each result:

```bash
python tests/test_otuput_structure.py
```

Both test scripts inherit `LOG_LEVEL` from the environment or `.env`.
