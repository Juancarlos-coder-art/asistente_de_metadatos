"""
Metadata Extractor — entry point.

Usage:
    python main.py <file_path> [--output json|text]

Examples:
    python main.py data.csv
    python main.py data.json --output json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd

load_dotenv(Path(__file__).parent / ".env")

from readers import get_reader
from extractors import ALL_EXTRACTORS
from extractors.static import normalize_language
from utils.logger import get_logger, setup_logging

log = get_logger(__name__)


def _load_dataframe(file_path: str) -> pd.DataFrame | None:
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".csv":
            return pd.read_csv(file_path)
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(file_path)
        if ext == ".parquet":
            return pd.read_parquet(file_path)
        if ext in (".json", ".xml"):
            records = list(get_reader(file_path).stream_records())
            return pd.DataFrame(records) if records else None
    except Exception as exc:
        log.warning("Could not load DataFrame for stats — %s", exc)
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract metadata from large CSV/JSON/XML/Excel files."
    )
    parser.add_argument("file", help="Path to the input file")
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Logging level (default: INFO or LOG_LEVEL env var). Use DEBUG to see LLM prompts.",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional path to write logs to a file in addition to stderr.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where the JSON output file is saved (default: tests-output/).",
    )
    return parser.parse_args()


DEFAULT_OUTPUT_DIR = Path(__file__).parent / "tests-output"


def run(file_path: str, output_format: str = "json", output_dir: Path | None = None) -> None:
    reader = get_reader(file_path)
    extractors = [cls(file_path=file_path) for cls in ALL_EXTRACTORS]

    log.info("Reading: %s", file_path)
    log.info("Extractors: %s", [e.name for e in extractors])

    start = time.perf_counter()
    record_count = 0

    for record in reader.stream_records():
        record_count += 1
        for extractor in extractors:
            extractor.update(record)

        if record_count % 50_000 == 0:
            elapsed = time.perf_counter() - start
            log.info("  ... %s records processed (%.1fs)", f"{record_count:,}", elapsed)

    elapsed = time.perf_counter() - start
    log.info("Done. %s records in %.2fs", f"{record_count:,}", elapsed)

    results = {e.name: e.result() for e in extractors}

    df = _load_dataframe(file_path)
    for extractor in extractors:
        finalized = extractor.finalize(results, df)
        if finalized:
            results[extractor.name] = {**results.get(extractor.name, {}), **finalized}

    output, structure_data = _merge_output(results)
    output = normalize_language(output)
    output = _maybe_add_structure(output, structure_data)

    pretty = json.dumps(output, indent=2, ensure_ascii=False)
    if output_format == "json":
        print(pretty)
    else:
        _print_text(output)
    _save_output(file_path, pretty, output_dir)


_PIPELINE_ORDER = [
    "llm_metadata",
    "static",
    "structure",
    "dataframe_statistics",
    "vocabulary",
    "geospatial",
]


def _merge_output(results: dict) -> tuple[dict, dict | None]:
    """Merge all extractor results into a single output dict in pipeline order.

    Returns (output, structure_data). structure_data is kept separate so the
    caller can decide whether to include it (only at DEBUG level).
    All other extractors are spread at the top level.
    Later steps overwrite earlier ones for duplicate keys.
    'errors' lists are accumulated rather than overwritten.
    """
    sources = {**results}

    output: dict = {}
    structure_data: dict | None = None

    for key in _PIPELINE_ORDER:
        data = sources.get(key)
        if not data:
            continue
        if key == "structure":
            structure_data = data
            errors = data.get("errors", [])
        else:
            errors = []
            for k, v in data.items():
                if k in ("errors", "_vocabulary_errors"):
                    errors += v if isinstance(v, list) else ([str(v)] if v else [])
                else:
                    output[k] = v
        output.setdefault("errors", [])
        if isinstance(errors, list):
            output["errors"].extend(errors)

    return output, structure_data


def _maybe_add_structure(output: dict, structure_data: dict | None) -> dict:
    """Include structure only when DEBUG logging is active."""
    import logging
    if structure_data and logging.getLogger().isEnabledFor(logging.DEBUG):
        output["structure"] = {k: v for k, v in structure_data.items() if k != "errors"}
    return output


def _print_text(output: dict) -> None:
    print(f"\n{'=' * 50}")
    _print_value("", output, indent=0)


def _print_value(key: str, value: object, indent: int = 0) -> None:
    pad = " " * indent
    label = key.replace("_", " ").capitalize() if key else ""
    prefix = f"{pad}{label}: " if label else pad

    if isinstance(value, dict):
        if label:
            print(f"{pad}{label}:")
        for k, v in value.items():
            _print_value(k, v, indent + 2)
    elif isinstance(value, list):
        if not value:
            print(f"{prefix}none")
        elif all(isinstance(i, str) for i in value):
            print(f"{prefix}{'; '.join(value)}")
        else:
            print(f"{prefix}")
            for item in value:
                _print_value("", item, indent + 2)
    elif isinstance(value, float):
        print(f"{prefix}{value:.2f}")
    else:
        print(f"{prefix}{value}")


def _save_output(file_path: str, pretty: str, output_dir: Path | None = None) -> None:
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(file_path).stem
    suffix = Path(file_path).suffix
    dest = output_dir if output_dir is not None else DEFAULT_OUTPUT_DIR
    dest.mkdir(parents=True, exist_ok=True)
    out_file = dest / f"{stem}{suffix}_{timestamp}.json"
    out_file.write_text(pretty, encoding="utf-8")
    log.info("Saved → %s", out_file)


if __name__ == "__main__":
    args = parse_args()
    level = args.log_level or os.environ.get("LOG_LEVEL", "INFO")
    setup_logging(level=level, log_file=args.log_file)
    out_dir = Path(args.output_dir) if args.output_dir else None
    run(args.file, args.output, out_dir)
