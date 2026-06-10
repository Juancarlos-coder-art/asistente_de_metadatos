"""
Preload the LanceDB vector database for the RAG vocabulary matcher.

Reads list_vocabularies.csv and, for every vocabulary, builds one LanceDB table
from its vocabs/<feature>.json file:

  - text:   all entry fields except 'uri' joined into one string (the searchable text)
  - vector: the all-MiniLM-L6-v2 embedding (384 dims) of that text
  - uri:    stored in plain text so matches resolve straight to the linked-data URI
  - code:   the concept code (JSON key)

The database is stored under controlled_vocabularies/db/. Run once (or whenever a
vocab JSON changes) to (re)build the tables:

    python controlled_vocabularies/build_vector_db.py
"""

import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parent))          # make project root importable

load_dotenv(_HERE.parent / ".env")

from utils.vector_store import connect, embed, entry_text  # noqa: E402
from utils.logger import get_logger, setup_logging          # noqa: E402

log = get_logger(__name__)

_CSV = _HERE / "list_vocabularies.csv"
_JSON_DIR = _HERE / "vocabs"


def _read_csv() -> list[dict]:
    with open(_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        return [{k.strip(): v.strip() for k, v in row.items() if k and k.strip()} for row in reader]


def build_table(feature: str, name: str) -> int:
    json_path = _JSON_DIR / f"{feature}.json"
    if not json_path.exists():
        log.warning("[%s] vocab JSON not found at %s — skipping", feature, json_path)
        return 0

    vocab = json.loads(json_path.read_text(encoding="utf-8"))
    if not vocab:
        log.warning("[%s] vocab JSON is empty — skipping", feature)
        return 0

    codes, texts, uris = [], [], []
    for code, entry in vocab.items():
        text = entry_text(entry)
        if not text:
            continue
        codes.append(code)
        texts.append(text)
        uris.append(entry.get("uri", ""))

    if not texts:
        log.warning("[%s] no embeddable text found — skipping", feature)
        return 0

    log.info("[%s] %s — embedding %d entries ...", feature, name, len(texts))
    for code, text in zip(codes, texts):
        log.debug("[%s] embed text for '%s': %s", feature, code, text)
    vectors = embed(texts)

    rows = [
        {"code": c, "text": t, "uri": u, "vector": v}
        for c, t, u, v in zip(codes, texts, uris, vectors)
    ]

    db = connect()
    db.create_table(feature, data=rows, mode="overwrite")
    log.info("[%s] table built with %d rows", feature, len(rows))
    return len(rows)


def main() -> None:
    import os
    setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))

    total_tables = total_rows = 0
    for row in _read_csv():
        feature = row.get("Feature", "")
        name = row.get("Name", "")
        if not feature:
            continue
        n = build_table(feature, name)
        if n:
            total_tables += 1
            total_rows += n

    log.info("Done. %d tables, %d rows → %s", total_tables, total_rows, _HERE / "db")


if __name__ == "__main__":
    main()
