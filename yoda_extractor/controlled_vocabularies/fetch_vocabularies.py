"""
Orchestrate vocabulary extraction for all rows in list_vocabularies.csv.

Dispatches each row to the right fetcher based on Mode_extracted_JSON:

  Iterative    → fetchers/iterative.py
                 Fetches the RDF endpoint concept-by-concept over the network.

  Personal_data → fetchers/personal_data.py
                 Parses the bundled personal_data.rdf file locally (no network).

Usage:
    python controlled_vocabularies/fetch_vocabularies.py
"""

import csv
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parent))          # make project root importable

from fetchers import iterative as iterative_fetcher      # noqa: E402
from fetchers import personal_data as personal_data_fetcher  # noqa: E402

_CSV = _HERE / "list_vocabularies.csv"


def main() -> None:
    with open(_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = [{k.strip(): v.strip() for k, v in row.items() if k} for row in reader]

    for row in rows:
        name    = row.get("Name", "")
        url     = row.get("URL", "")
        feature = row.get("Feature", "")
        mode    = row.get("Mode_extracted_JSON", "").lower()

        if not feature:
            print(f"Skipping row with no Feature: {row}")
            continue

        print(f"\n{'─' * 60}")

        if mode == "iterative":
            if not url:
                print(f"Skipping '{name}': mode=iterative but no URL")
                continue
            iterative_fetcher.fetch_vocabulary(name, url, feature)

        elif mode == "personal_data":
            print(f"[{feature}] {name}  (local RDF)")
            personal_data_fetcher.extract()
        
        elif mode == "none":
            print(f"Skipping '{name}': mode=none. Manually extracted.")

        else:
            print(f"Skipping '{name}': unknown mode '{mode}'")

    print(f"\n{'─' * 60}")
    print("Done.")


if __name__ == "__main__":
    # Run from project root: python controlled_vocabularies/fetch_vocabularies.py
    sys.path.insert(0, str(_HERE))             # make fetchers/ importable
    main()
