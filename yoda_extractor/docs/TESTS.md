# Testing System (`tests/`)

The project contains a comprehensive validation and testing pipeline designed to run metadata extraction over all dataset samples. The test runners ensure both the execution stability and the semantic correctness of the output format.

All datasets are located in `tests/datasets/` organized by subfolders (`dataset_0000/`, `dataset_0001/`, etc.).

---

## Test Runners

There are two main entry points for running tests:

### 1. Structure and Idempotency Validation (`tests/test_otuput_structure.py`)

This is the primary validation script. It tests both the structural validity of the JSON output and the idempotency of the extractor.

#### How It Works:
For every supported dataset, the script performs a **two-pass execution**:
1. **First Pass (Regular Extraction)**: It runs `main.py` normally against the dataset and validates that the output JSON conforms to the strict domain schema (required fields, expected data types, lists/objects nesting).
2. **Second Pass (Idempotency Check)**: It re-runs `main.py` using the first pass's output as the `--input-json` argument. It then verifies that the output remains structurally identical, except for the controlled `version` increment (+1.0) and the accumulation of history in the `has_version` array.

#### Strict Schema Validations:
* **Required fields present**: `title`, `notes`, `description`, `name`, `format`, `mimetype`, `version`, `size`, `number_of_records`, `temporal_coverage`, `applicable_legislation`.
* **String fields**: `title`, `notes`, `description`, `name`, `format`, `mimetype`, `hash`, `hash_algorithm`, `dcat_type`, `version`.
* **Integer fields**: `size`, `number_of_records`.
* **Numeric/Nullable fields**: `number_of_unique_individuals`, `min_typical_age`, `max_typical_age`.
* **Lists of strings**: `purpose`, `language`, `health_category`, `theme`, `keyword`, `population_coverage`, `personal_data`, `health_theme`, `code_values`, `was_generated_by`, `spatial`.
* **Nested object structures**: `legal_basis` (containing `description`, `source`), `applicable_legislation` (containing `description`, `official_journal`).

---

### 2. General Integration Suite (`tests/test.py`)

A general runner that executes the extractor against all test datasets in parallel to verify that no uncaught exceptions are thrown during run time.

#### How It Works:
* Clears the directories in `tests-output/` to prevent concurrency conflicts.
* Dispatches extraction tasks in parallel.
* Generates a consolidated summary of any metadata errors at the end of the run in `tests-output/errors_summary.json`.

---

## Execution and Configurations

Both test runners support configuration via command-line arguments and environment variables.

### Command Line Options

#### For `tests/test.py`:
* `--input-json INPUT_JSON`: Pass a pre-filled JSON string or path to a JSON file to forward to all extractor runs as `--input-json`.

### Environment Variables

You can customize the test execution behavior by defining the following environment variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `MAX_WORKERS` | `10` | The maximum number of concurrent threads to spawn during test execution. |
| `TEST_PARALLEL` | `true` | Set to `false` or `0` to run tests sequentially instead of in parallel. |
| `LOG_LEVEL` | `INFO` | Set logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Use `DEBUG` to view full LLM payloads. |

#### Usage Examples:
```bash
# Run structure/idempotency tests sequentially with debug logging
TEST_PARALLEL=false LOG_LEVEL=DEBUG python tests/test_otuput_structure.py

# Run general integration tests with fewer workers
MAX_WORKERS=4 python tests/test.py
```

---

## File Filtering

To avoid parsing unsupported auxiliary files (such as `.zip` packages or hidden files) that might exist in dataset directories, both test runners filter the queue to only include files matching the following criteria:
* **Supported file extensions**: `.csv`, `.json`, `.xml`, `.xlsx`, `.xls`, `.parquet`.
* **Parquet directories**: Folders ending in `.parquet` containing partitioned parquet fragments.
