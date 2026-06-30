"""
Run main.py against every file in every dataset folder under tests/datasets/.
Prints JSON to stdout and saves results to tests-output/<dataset>/ with a timestamp.

Usage:
    python tests/test.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT))
from utils.logger import get_logger, setup_logging  # noqa: E402

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

DATASETS_DIR = ROOT / "tests" / "integration" / "datasets"
OUTPUT_DIR = Path(__file__).parent / "pipeline-output"


def verify_idempotency(first_data: dict, second_data: dict) -> list[str]:
    errors = []
    
    # 1. Compare version increments
    v1 = first_data.get("version")
    v2 = second_data.get("version")
    if v1 is None or v2 is None:
        errors.append(f"Missing version fields: first={v1!r}, second={v2!r}")
    else:
        try:
            if float(v2) != float(v1) + 1.0:
                errors.append(f"version did not increment by 1: first={v1!r}, second={v2!r}")
        except ValueError:
            if v1 != v2:
                errors.append(f"non-numeric version changed: first={v1!r}, second={v2!r}")

    hv1 = first_data.get("has_version")
    hv2 = second_data.get("has_version")
    if hv1 is None or hv2 is None:
        errors.append(f"Missing has_version fields: first={hv1!r}, second={hv2!r}")
    elif not isinstance(hv1, list) or not isinstance(hv2, list):
        if hv1 != hv2:
            errors.append(f"non-list has_version changed: first={hv1!r}, second={hv2!r}")
    else:
        expected_hv2 = list(hv1) + [v2]
        if hv2 != expected_hv2:
            errors.append(f"has_version did not accumulate version correctly: expected={expected_hv2!r}, got={hv2!r}")

    # 2. Compare all other keys
    ignored_keys = {"version", "has_version"}
    all_keys = set(first_data.keys()) | set(second_data.keys())
    for k in all_keys:
        if k in ignored_keys:
            continue
        if k not in first_data:
            errors.append(f"Key '{k}' present in second output but missing in first output")
        elif k not in second_data:
            errors.append(f"Key '{k}' present in first output but missing in second output")
        else:
            val1 = first_data[k]
            val2 = second_data[k]
            if val1 != val2:
                errors.append(f"Value for '{k}' differs: first={val1!r}, second={val2!r}")
            
    return errors


def run_file(path: Path, dataset_name: str, input_json: str | None = None) -> dict | None:
    log.info("Processing [%s]: %s", dataset_name, path.name)
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    out_dir = OUTPUT_DIR / dataset_name

    # First run: regular execution (forwarding input_json if any)
    cmd_args1 = [
        sys.executable, str(ROOT / "main.py"), str(path),
        "--log-level", log_level,
        "--output-dir", str(out_dir),
    ]
    if input_json:
        cmd_args1.extend(["--input-json", input_json])
        log.info("  [First Run] Forwarding --input-json to main.py")

    result1 = subprocess.run(
        cmd_args1,
        capture_output=True,
        text=True,
    )
    if result1.returncode != 0:
        log.error("First run of main.py failed for %s:\n%s", path.name, result1.stderr.strip())
        return None

    try:
        first_data = json.loads(result1.stdout)
    except json.JSONDecodeError as exc:
        log.error("Invalid JSON output in first run for %s — %s", path.name, exc)
        return None

    # Second run: pass the first run's output as --input-json (idempotency check)
    log.info("  [Second Run] Re-running with first run output as input-json for %s", path.name)
    cmd_args2 = [
        sys.executable, str(ROOT / "main.py"), str(path),
        "--log-level", log_level,
        "--output-dir", str(out_dir),
        "--input-json", json.dumps(first_data),
    ]

    result2 = subprocess.run(
        cmd_args2,
        capture_output=True,
        text=True,
    )
    if result2.returncode != 0:
        log.error("Second run of main.py failed for %s:\n%s", path.name, result2.stderr.strip())
        return None

    try:
        second_data = json.loads(result2.stdout)
    except json.JSONDecodeError as exc:
        log.error("Invalid JSON output in second run for %s — %s", path.name, exc)
        return None

    # Verify that they are equal (modulo version increments)
    idempotency_errors = verify_idempotency(first_data, second_data)
    if idempotency_errors:
        log.error("Idempotency check FAILED for %s:\n%s", path.name, "\n".join(idempotency_errors))
        return None

    log.info("Idempotency check PASSED for %s", path.name)
    return first_data



def generate_errors_summary(output_dir: Path) -> None:
    import re
    summary = {}
    if not output_dir.exists():
        log.warning("Output directory %s does not exist, skipping summary generation", output_dir)
        return

    # Sort dataset directories to process in order
    dataset_dirs = sorted(output_dir.iterdir())
    for d in dataset_dirs:
        if not d.is_dir() or not d.name.startswith("dataset_"):
            continue
        
        match = re.match(r"dataset_(\d+)", d.name)
        if not match:
            continue
        dataset_num = str(int(match.group(1)))
        
        json_files = list(d.glob("*.json"))
        if not json_files:
            continue
        
        # Sort by modification time to get the latest output
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            errors = data.get("errors", [])
            if not isinstance(errors, list):
                errors = [errors] if errors else []
            summary[dataset_num] = errors
        except Exception as e:
            log.error("Error reading %s: %s", latest_file.name, e)
            summary[dataset_num] = [f"Failed to read output: {e}"]

    summary_file = output_dir / "errors_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    log.info("Summary successfully generated at %s", summary_file)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Run extractor tests against all datasets.")
    parser.add_argument("--input-json", dest="input_json", default=None,
                        help="JSON string or path to JSON file forwarded to main.py as --input-json")
    args = parser.parse_args()

    dataset_dirs = sorted(p for p in DATASETS_DIR.iterdir() if p.is_dir())
    if not dataset_dirs:
        log.error("No dataset folders found in tests/datasets/")
        sys.exit(1)

    tasks = []
    supported_extensions = {".csv", ".json", ".xml", ".xlsx", ".xls", ".parquet"}
    for dataset_dir in dataset_dirs:
        files = sorted(p for p in dataset_dir.iterdir() if not p.name.startswith("."))
        for path in files:
            ext = path.suffix.lower()
            if ext in supported_extensions or (path.is_dir() and path.name.endswith(".parquet")):
                tasks.append((path, dataset_dir.name))

    if not tasks:
        log.info("No files to process.")
        return

    # Clear output directories beforehand to avoid race conditions during concurrent runs
    unique_datasets = sorted(set(dataset_name for _, dataset_name in tasks))
    for dataset_name in unique_datasets:
        out_dir = OUTPUT_DIR / dataset_name
        if out_dir.exists():
            shutil.rmtree(out_dir)
            log.debug("Cleared %s", out_dir)

    run_parallel = os.environ.get("TEST_PARALLEL", "true").lower() in ("true", "1", "yes")

    if run_parallel:
        max_workers = int(os.environ.get("MAX_WORKERS", "10"))
        log.info("Starting parallel execution of %d tasks using %d workers...", len(tasks), max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_file, path, dataset_name, args.input_json): (path, dataset_name)
                for path, dataset_name in tasks
            }
            
            for future in as_completed(futures):
                path, dataset_name = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        log.info("Completed [%s]: %s", dataset_name, path.name)
                    else:
                        log.error("Failed [%s]: %s", dataset_name, path.name)
                except Exception as exc:
                    log.error("Exception during execution of [%s] %s: %s", dataset_name, path.name, exc)
    else:
        log.info("Starting sequential execution of %d tasks...", len(tasks))
        for path, dataset_name in tasks:
            try:
                result = run_file(path, dataset_name, args.input_json)
                if result is not None:
                    log.info("Completed [%s]: %s", dataset_name, path.name)
                else:
                    log.error("Failed [%s]: %s", dataset_name, path.name)
            except Exception as exc:
                log.error("Exception during execution of [%s] %s: %s", dataset_name, path.name, exc)

    generate_errors_summary(OUTPUT_DIR)


if __name__ == "__main__":
    main()
