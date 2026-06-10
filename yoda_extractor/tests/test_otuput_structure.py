"""
Validate extractor output structure for every file in every tests/datasets/ folder.

Usage:
    python tests/test_otuput_structure.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT))
from utils.logger import get_logger, setup_logging  # noqa: E402

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

DATASETS_DIR = Path(__file__).parent / "datasets"

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check_temporal(tc: dict, errors: list[str]) -> None:
    if not tc:
        errors.append("temporal_columns is empty — no date columns found")
        return
    for col, bounds in tc.items():
        for key in ("start", "end"):
            if key not in bounds:
                errors.append(f"temporal_columns['{col}'] missing '{key}'")


def check_geospatial(geo: dict, errors: list[str]) -> None:
    for key in ("geo_columns", "total_records", "mappings"):
        if key not in geo:
            errors.append(f"geospatial missing '{key}'")


def run_file(path: Path, dataset_name: str) -> tuple[bool, str]:
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    out_dir = ROOT / "tests-output" / dataset_name
    result = subprocess.run(
        [
            sys.executable, str(ROOT / "main.py"), str(path),
            "--log-level", log_level,
            "--output-dir", str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = f"non-zero exit ({result.returncode}): {result.stderr.strip()}"
        log.error("[%s] %s", path.name, msg)
        return False, msg

    if result.stderr.strip():
        log.debug("stderr [%s]:\n%s", path.name, result.stderr.strip())

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        msg = f"invalid JSON: {exc}"
        log.error("[%s] %s", path.name, msg)
        return False, msg

    errors: list[str] = []

    if "temporal_columns" not in data:
        errors.append("missing 'temporal_columns'")
    else:
        check_temporal(data["temporal_columns"], errors)

    if "geospatial" not in data:
        errors.append("missing 'geospatial'")
    else:
        check_geospatial(data["geospatial"], errors)

    if errors:
        return False, "; ".join(errors)
    return True, "ok"


def main() -> None:
    dataset_dirs = sorted(p for p in DATASETS_DIR.iterdir() if p.is_dir())
    if not dataset_dirs:
        log.error("No dataset folders found in tests/datasets/")
        sys.exit(1)

    total = failed = 0

    for dataset_dir in dataset_dirs:
        files = sorted(p for p in dataset_dir.iterdir() if not p.name.startswith("."))
        if not files:
            continue

        log.info("Dataset: %s", dataset_dir.name)

        for path in files:
            ok, msg = run_file(path, dataset_dir.name)
            status = PASS if ok else FAIL
            print(f"    [{status}] {path.name}: {msg}")
            if not ok:
                log.warning("[%s] FAIL: %s", path.name, msg)
            else:
                log.debug("[%s] PASS", path.name)
            total += 1
            if not ok:
                failed += 1

    log.info("%d/%d passed", total - failed, total)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
