"""Integration tests: run main.py against every dataset and validate the output."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
DATASETS_DIR = Path(__file__).parent / "datasets"
EXAMPLE_OUTPUT = Path(__file__).parent / "expected_output.json"
OUTPUT_DIR = Path(__file__).parent / "tests-output"

# Minimum required fields — derived from what the pipeline must always produce
_REQUIRED_FIELDS = {
    "purpose", "language", "title", "notes", "keyword", "population_coverage",  # LLM
    "errors",                                                                     # LLM
    "health_theme", "spatial",                                                    # Vocabulary
    "issued", "modified", "applicable_legislation",                               # Static
}

# Fields provided by the user and not extracted by the system
_SKIP_FIELDS = {
    "number_of_records", "number_of_unique_individuals",
    "min_typical_age", "max_typical_age", "temporal_coverage",
    "purpose_en_tmpt", "title_en_tmpt", "notes_en_tmpt", "keyword_en_tmpt", "structure",
    "theme", "legal_basis", "version", "has_version",
    "hdab", "access_rights", "identifier", "provenance", "retention_period",
    "contact", "publisher", "creator", "qualified_attribution",
    "temporal_resolution", "spatial_resolution_in_meters", "frequency",
    "alternate_identifier", "related_resource", "is_referenced_by", "url",
    "documentation", "version_notes", "quality_annotation",
    "access_url", "status", "compress_format", "package_format",
    "rights", "availability", "license", "download_url", "publisher_note"
}

with open(EXAMPLE_OUTPUT) as _f:
    _example = json.load(_f)

# Type reference for required fields
_EXPECTED_TYPES = {k: type(v) for k, v in _example.items() if k in _REQUIRED_FIELDS}

# Possible fields from the example (not required, not skipped) — tracked in _missing.json
_POSSIBLE_FIELDS = [k for k in _example if k not in _REQUIRED_FIELDS and k not in _SKIP_FIELDS]


def _collect_datasets():
    params = []
    for dataset_dir in sorted(DATASETS_DIR.iterdir()):
        if not dataset_dir.is_dir():
            continue
        for f in sorted(dataset_dir.iterdir()):
            if not f.name.startswith("."):
                params.append(pytest.param(f, id=f"{dataset_dir.name}/{f.name}"))
    return params


@pytest.mark.integration
@pytest.mark.parametrize("dataset_file", _collect_datasets())
def test_pipeline(dataset_file):
    out_dir = OUTPUT_DIR / dataset_file.parent.name
    out_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), str(dataset_file),
         "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"main.py exited with {result.returncode}:\n{result.stderr.strip()}"
    )

    data = json.loads(result.stdout)

    # Find the output file main.py just saved
    output_files = sorted(out_dir.glob("*.json"))
    output_file = output_files[-1] if output_files else None

    all_expected = list(_REQUIRED_FIELDS) + _POSSIBLE_FIELDS
    missing = [f for f in all_expected if f not in data]
    wrong_type = [
        f"{f} (expected {_EXPECTED_TYPES[f].__name__}, got {type(data[f]).__name__})"
        for f in _REQUIRED_FIELDS
        if f in data and f in _EXPECTED_TYPES and not isinstance(data[f], _EXPECTED_TYPES[f])
    ]

    if (missing or wrong_type) and output_file:
        missing_file = output_file.with_name(output_file.stem + "_missing.json")
        missing_file.write_text(
            json.dumps({"missing": missing, "wrong_type": wrong_type}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    required_missing = [f for f in _REQUIRED_FIELDS if f not in data]
    assert not required_missing, f"missing required fields: {required_missing}"
    assert not wrong_type, f"wrong types: {wrong_type}"
    assert data["issued"], "'issued' must not be empty"
    assert data["modified"], "'modified' must not be empty"
