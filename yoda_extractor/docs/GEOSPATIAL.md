# Geospatial Extraction — How It Works

The geospatial extractor maps free-text geographic values (country codes, region names, city names, etc.) to linked-data URIs in a single streaming pass over the file. It minimises network calls by batching SPARQL queries at the end of the sampling phase, before the full scan begins.

---

**Resolution order (first match wins):**

| Priority | Input | Method | Vocabulary | Example URI |
|----------|-------|--------|------------|-------------|
| 1 | Continent name | built-in dict | `eu_continent` | `…/authority/continent/EUROPE` |
| 2 | ISO 3166-1 alpha-3 | built-in dict | `eu_country` | `…/authority/country/ESP` |
| 3 | ISO 3166-1 alpha-2 | built-in dict | `eu_country` | `…/authority/country/ESP` |
| 4 | Country name (EN/ES) | built-in dict | `eu_country` | `…/authority/country/ESP` |
| 5 | Region / city / place | SPARQL | `eu_atu`, `eu_place` | `…/authority/atu/ES511` |
| 6 | Spanish territory | SPARQL | `datos_territorio` | `datos.gob.es/…/territorio/…` |

**SPARQL endpoints queried:**
- EU Publications Office: `https://publications.europa.eu/webapi/rdf/sparql`
  — searches `country`, `continent`, `atu` (NUTS regions), and `place` schemes
- datos.gob.es: `https://datos.gob.es/virtuoso/sparql`
  — searches the Spanish territory hierarchy

**Query minimisation strategy:**
After the sampling phase, all unique values that the built-in dicts could _not_ resolve are sent to the SPARQL endpoints in a single batch (up to 50 values per request). The full scan then reads from the in-memory cache — no further network calls unless a completely new value appears.

## Four phases

```mermaid
sequenceDiagram
    participant main
    participant GeoExtractor as GeospatialExtractor
    participant geo_utils
    participant sparql_utils
    participant EU as EU Publications Office
    participant datos as datos.gob.es

    Note over main,datos: ── Phase 1 · Sampling (first 200 records) ──

    loop record 1 … 200
        main->>GeoExtractor: update(record)
        GeoExtractor->>geo_utils: is_geo_column_by_name(col)
        geo_utils-->>GeoExtractor: True / False
        GeoExtractor->>GeoExtractor: buffer unique values per candidate column
    end

    Note over main,datos: ── Phase 2 · SPARQL warmup + column confirmation ──

    GeoExtractor->>geo_utils: warm_sparql_cache(all_sample_values)
    geo_utils->>geo_utils: skip values already resolved by dict fast-path

    loop batch of ≤ 50 unknown values
        geo_utils->>sparql_utils: resolve_batch(batch)
        sparql_utils->>EU: POST — country · continent · atu · place schemes
        EU-->>sparql_utils: [{input, uri, scheme}, …]
        sparql_utils->>datos: POST — unresolved values only
        datos-->>sparql_utils: [{input, uri}, …]
        sparql_utils-->>geo_utils: {value → (uri, vocab)}
    end

    geo_utils->>geo_utils: populate _sparql_cache
    geo_utils-->>GeoExtractor: cache warmed
    GeoExtractor->>GeoExtractor: confirm columns where ≥ 30 % of values resolved

    Note over main,datos: ── Phase 3 · Full scan (remaining records) ──

    loop each remaining record
        main->>GeoExtractor: update(record)

        loop each confirmed geo column
            GeoExtractor->>geo_utils: resolve_value(value)

            alt dict fast-path hit  (ISO code, continent name, country name)
                geo_utils-->>GeoExtractor: (uri, vocab)
            else SPARQL cache hit  (pre-warmed in Phase 2)
                geo_utils-->>GeoExtractor: (uri, vocab)
            else cache miss  (value not seen during sampling — rare)
                geo_utils->>sparql_utils: resolve_batch([value])
                sparql_utils->>EU: POST SPARQL
                EU-->>sparql_utils: result
                sparql_utils-->>geo_utils: (uri, vocab) or None
                geo_utils->>geo_utils: store in _sparql_cache
                geo_utils-->>GeoExtractor: (uri, vocab) or None
            end
        end

        GeoExtractor->>GeoExtractor: accumulate per-value counts · track unresolved
    end

    Note over main,datos: ── Phase 4 · Result ──

    main->>GeoExtractor: result()
    GeoExtractor-->>main: geo_columns · mappings · coverage · unresolved · vocabularies_used
```

---

## Resolution pipeline (per value)

```mermaid
flowchart TD
    A([raw string value]) --> B{continent name?}

    B -->|yes| R1[/"eu_continent URI"\]
    B -->|no| C{ISO 3166-1 alpha-3?}

    C -->|yes| R2[/"eu_country URI"\]
    C -->|no| D{ISO 3166-1 alpha-2?}

    D -->|yes| R3[/"eu_country URI"\]
    D -->|no| E{"known country name?\n(EN / ES)"}

    E -->|yes| R4[/"eu_country URI"\]
    E -->|no| F{in _sparql_cache?}

    F -->|yes| G{cache entry is None?}
    G -->|no| R5[/"cached URI"\]
    G -->|yes| NONE([None — unresolved])

    F -->|no| H["individual SPARQL query\n(value not seen during sampling)"]
    H --> I{EU endpoint match?}

    I -->|yes| J{best-priority scheme}
    J --> R6[/"eu_country / eu_continent\neu_atu / eu_place URI"\]

    I -->|no| K{datos.gob.es match?}
    K -->|yes| R7[/"datos_territorio URI"\]
    K -->|no| NONE2([None — unresolved])

    H --> CACHE[store result in _sparql_cache]
```

---

## Vocabularies and scheme priority

When a value matches multiple schemes in the EU endpoint (e.g. "Madrid" appears in both `atu` and `place`), the match with the **lowest priority number** is returned.

| Priority | Vocabulary | Scheme URI | Example |
|----------|------------|------------|---------|
| 1 | `eu_country` | `…/authority/country` | `…/country/ESP` |
| 2 | `eu_continent` | `…/authority/continent` | `…/continent/EUROPE` |
| 3 | `eu_atu` | `…/authority/atu` | `…/atu/ES511` |
| 4 | `eu_place` | `…/authority/place` | `…/place/MADRID` |
| 5 | `datos_territorio` | `datos.gob.es/…/territorio` | `…/territorio/Municipio/28079` |

---

## How queries are limited

| Situation | Queries sent |
|-----------|-------------|
| Value resolves via dict fast-path (ISO code, country name, continent) | **0** |
| Value is unknown — batch warmup during Phase 2 | **1 EU + 1 datos per 50 values** |
| Value appears for the first time during the full scan (cache miss) | **1 EU + 1 datos** |
| Same value seen again anywhere | **0** (cache hit) |

For a typical dataset with 80 unique geographic values where 30 are ISO codes and 50 are region names:
- Phase 2 sends **2 requests** (1 EU + 1 datos for the 50 unknown values)
- Full scan sends **0** additional requests
- Total: **2 HTTP requests** regardless of record count

---

## Column detection

A column is considered geographic if it passes **both** filters:

1. **Name filter** — the column name contains a keyword from the configured list:
   `country`, `region`, `city`, `province`, `state`, `municipality`, `continent`, `territory`, `place`, `pais`, `ciudad`, `provincia`, `municipio`, `localidad`, `pays`, `ville`, `land`, `ort`, …

2. **Value filter** — at least **30 %** of the sampled values (up to 200) resolve to a URI.
   This check runs *after* the SPARQL cache is warmed, so region-name columns (e.g. `region = ["Cataluña", "Andalucía", "Madrid"]`) pass even though the dict fast-path alone would score 0 %.

Columns that pass the name filter but contain non-geographic data (e.g. `state = ["active", "inactive"]`) are rejected at this stage.
