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
from extractors.static import normalize_array_fields, normalize_language
from utils.logger import get_logger, setup_logging

log = get_logger(__name__)


def _load_dataframe(file_path: str) -> pd.DataFrame | None:
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".csv" or ext in (".json", ".xml"):
            records = list(get_reader(file_path).stream_records())
            return pd.DataFrame(records) if records else None
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(file_path)
        if ext == ".parquet":
            return pd.read_parquet(file_path)
    except Exception as exc:
        log.warning("Could not load DataFrame for stats — %s", exc)
    return None


def _has_content(val) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, (list, dict)):
        return len(val) > 0
    return True


def _load_input_json(input_json_arg: str | None) -> dict:
    if not input_json_arg:
        return {}
    if os.path.exists(input_json_arg):
        try:
            with open(input_json_arg, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning("Could not read input JSON file %s: %s", input_json_arg, e)
    try:
        return json.loads(input_json_arg)
    except Exception as e:
        log.warning("Could not parse input JSON string: %s", e)
    return {}


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
    parser.add_argument(
        "--input-json",
        default=None,
        help="Path to a JSON file containing pre-filled metadata, or an inline JSON string.",
    )
    parser.add_argument(
        "--include-tmpt",
        action="store_true",
        default=None,
        help="Include internal *_tmpt fields in the output. Defaults to true when --log-level DEBUG, false otherwise.",
    )
    return parser.parse_args()


DEFAULT_OUTPUT_DIR = Path(__file__).parent / "tests-output"


def run(file_path: str, output_format: str = "json", output_dir: Path | None = None, input_json: dict | None = None, include_tmpt: bool | None = None) -> None:
    input_dict = normalize_array_fields(dict(input_json or {}))
    reader = get_reader(file_path)
    extractors = [cls(file_path=file_path, input_json=input_dict) for cls in ALL_EXTRACTORS]

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

    stats_fields = ("number_of_records", "number_of_unique_individuals", "min_typical_age", "max_typical_age", "temporal_coverage")
    all_stats_present = all(f in input_dict for f in stats_fields)
    prefilled_stats = {f: input_dict[f] for f in stats_fields if f in input_dict and _has_content(input_dict[f])}

    df = None
    if all_stats_present or len(prefilled_stats) == len(stats_fields):
        log.info("All statistics fields present or prefilled in input_json, skipping DataFrame loading.")
    else:
        df = _load_dataframe(file_path)
    for extractor in extractors:
        finalized = extractor.finalize(results, df)
        if finalized:
            results[extractor.name] = {**results.get(extractor.name, {}), **finalized}

    output = _merge_output(results)
    output = normalize_array_fields(output)
    output = _strip_tmpt_fields(output, include_tmpt=include_tmpt)

    _static_managed = {"version", "has_version"}
    for k, v in input_dict.items():
        if k in _static_managed:
            log.debug("[input_json override] skipping static-managed field %r (value: %r)", k, v)
            continue
        if k not in output:
            log.debug("[input_json override] adding missing field %r = %r", k, v)
            output[k] = v
        elif _has_content(v):
            log.debug("[input_json override] overriding %r: %r → %r", k, output[k], v)
            output[k] = v

    pretty = json.dumps(output, indent=2, ensure_ascii=False)
    if output_format == "json":
        print(pretty)
    else:
        _print_text(output)
    _save_output(file_path, pretty, output_dir)


_PIPELINE_ORDER = [
    "llm_metadata",
    "static",
    "structure_tmpt",
    "dataframe_statistics",
    "vocabulary",
]


def _merge_output(results: dict) -> dict:
    """Merge all extractor results into a single output dict in pipeline order.

    All extractors are spread at the top level.
    Later steps overwrite earlier ones for duplicate keys.
    'errors' lists are accumulated rather than overwritten.
    """
    output: dict = {}

    for key in _PIPELINE_ORDER:
        data = results.get(key)
        if not data:
            continue
        errors = []
        if key == "structure_tmpt":
            output["structure_tmpt"] = {k: v for k, v in data.items() if k != "errors"}
            errors = data.get("errors", [])
        else:
            for k, v in data.items():
                if k in ("errors", "_vocabulary_errors"):
                    errors += v if isinstance(v, list) else ([str(v)] if v else [])
                else:
                    output[k] = v
        output.setdefault("errors", [])
        if isinstance(errors, list):
            output["errors"].extend(errors)

    return output


def _strip_tmpt_fields(output: dict, include_tmpt: bool | None = None) -> dict:
    """Remove all *_tmpt fields unless explicitly included or DEBUG logging is active."""
    import logging
    keep = include_tmpt if include_tmpt is not None else logging.getLogger().isEnabledFor(logging.DEBUG)
    if keep:
        return output
    return {k: v for k, v in output.items() if not k.endswith("_tmpt")}


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
    input_json = _load_input_json(args.input_json)
    include_tmpt = args.include_tmpt if args.include_tmpt else None
    run(args.file, args.output, out_dir, input_json=input_json, include_tmpt=include_tmpt)
