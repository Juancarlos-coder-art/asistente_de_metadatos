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

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT))
from utils.logger import get_logger, setup_logging  # noqa: E402

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

DATASETS_DIR = Path(__file__).parent / "datasets"
OUTPUT_DIR = ROOT / "tests-output"


def run_file(path: Path, dataset_name: str) -> dict | None:
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    out_dir = OUTPUT_DIR / dataset_name
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
        log.error("main.py failed for %s:\n%s", path.name, result.stderr.strip())
        return None
    if result.stderr.strip():
        log.debug("stderr from main.py [%s]:\n%s", path.name, result.stderr.strip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        log.error("Invalid JSON output for %s — %s", path.name, exc)
        return None


def main() -> None:
    dataset_dirs = sorted(p for p in DATASETS_DIR.iterdir() if p.is_dir())
    if not dataset_dirs:
        log.error("No dataset folders found in tests/datasets/")
        sys.exit(1)

    for dataset_dir in dataset_dirs:
        files = sorted(p for p in dataset_dir.iterdir() if not p.name.startswith("."))
        if not files:
            continue

        out_dir = OUTPUT_DIR / dataset_dir.name
        if out_dir.exists():
            shutil.rmtree(out_dir)
            log.debug("Cleared %s", out_dir)

        log.info("=" * 60)
        log.info("Dataset: %s", dataset_dir.name)
        log.info("=" * 60)

        for path in files:
            log.info("Processing: %s", path.name)
            run_file(path, dataset_dir.name)


if __name__ == "__main__":
    main()
