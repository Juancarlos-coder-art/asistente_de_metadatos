"""
Shared vector-store helpers for the RAG vocabulary matcher.

Uses a local, free embedding model (all-MiniLM-L6-v2, 384 dims) and an embedded
LanceDB database stored under controlled_vocabularies/db/. One table per
controlled vocabulary; each row stores the concept code, the searchable text
(all vocab fields except 'uri'), the plain-text URI, and the embedding vector.

Both the preload script (controlled_vocabularies/build_vector_db.py) and the
runtime matcher (extractors/vocabulary.py) import from here so the embedding
logic stays identical between indexing and querying.
"""

from pathlib import Path
from typing import Any

from utils.logger import get_logger

log = get_logger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIM = 384

_DB_DIR = Path(__file__).parent.parent / "controlled_vocabularies" / "db"

_model = None
_db = None


def get_model():
    """Lazily load the embedding model once per process."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        log.info("Loading embedding model '%s' ...", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Return normalized embedding vectors for a list of texts."""
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]


def entry_text(entry: dict[str, Any]) -> str:
    """Join all values of a vocabulary entry except 'uri' into one search string.

    Values may be strings or lists of strings; everything is flattened and
    concatenated. The 'uri' key is skipped because it adds no semantic signal.
    """
    parts: list[str] = []
    for key, value in entry.items():
        if key == "uri" or not value:
            continue
        if isinstance(value, list):
            parts.extend(str(v).strip() for v in value if v)
        else:
            parts.append(str(value).strip())
    return " ".join(p for p in parts if p)


def connect():
    """Open (or create) the embedded LanceDB database."""
    global _db
    if _db is None:
        import lancedb
        _DB_DIR.mkdir(parents=True, exist_ok=True)
        _db = lancedb.connect(str(_DB_DIR))
    return _db


def table_names() -> list[str]:
    return list(connect().table_names())


def search(feature: str, query_text: str, limit: int = 1) -> list[dict]:
    """Search the table for `feature`, returning the top `limit` rows.

    Each result row contains at least 'code', 'text', 'uri' and a distance
    score under '_distance'. Returns [] if the table does not exist.
    """
    db = connect()
    if feature not in db.table_names():
        log.warning("No vector table for feature '%s'", feature)
        return []
    table = db.open_table(feature)
    query_vector = embed_one(query_text)
    return table.search(query_vector).limit(limit).to_list()
