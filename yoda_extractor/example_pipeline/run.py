"""
Run a complete pipeline experiment against a single input file.

Usage:
    python example_pipeline/run.py <file_path>
    python example_pipeline/run.py <file_path> --input-json '{"title": "My dataset"}'
    python example_pipeline/run.py <file_path> --input-json path/to/metadata.json
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

OUTPUT_DIR = Path(__file__).parent / "pipeline-output"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run a complete pipeline experiment on a single file.")
    parser.add_argument("file_path", help="Path to the input dataset file")
    parser.add_argument("--input-json", dest="input_json", default=None,
                        help="JSON string or path to JSON file with pre-filled metadata")
    parser.add_argument("--log-level", dest="log_level", default=None,
                        help="Log level: DEBUG / INFO / WARNING / ERROR")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    if not file_path.exists():
        log.error("File not found: %s", file_path)
        sys.exit(1)

    out_dir = OUTPUT_DIR / file_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    log_level = args.log_level or os.environ.get("LOG_LEVEL", "INFO")

    cmd = [
        sys.executable, str(ROOT / "main.py"), str(file_path),
        "--log-level", log_level,
        "--output-dir", str(out_dir),
    ]
    if args.input_json:
        cmd.extend(["--input-json", args.input_json])

    log.info("Running pipeline on: %s", file_path.name)
    log.info("Output dir: %s", out_dir)

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        log.error("Pipeline failed with exit code %d", result.returncode)
        sys.exit(result.returncode)

    log.info("Done. Results saved to %s", out_dir)


if __name__ == "__main__":
    main()
