import json
from typing import Generator
from .base import BaseReader


def _flatten(obj: dict, prefix: str = "", sep: str = ".") -> dict:
    """Recursively flatten a nested dict into a single-level dict."""
    out = {}
    for k, v in obj.items():
        key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key, sep))
        elif isinstance(v, list):
            # Represent lists as JSON string to preserve content
            out[key] = json.dumps(v, ensure_ascii=False)
        else:
            out[key] = str(v) if v is not None else None
    return out


class JSONReader(BaseReader):
    def stream_records(self) -> Generator[dict, None, None]:
        try:
            import ijson
            yield from self._stream_with_ijson(ijson)
        except ImportError:
            yield from self._stream_fallback()

    def _stream_with_ijson(self, ijson) -> Generator[dict, None, None]:
        with open(self.path, "rb") as f:
            # Try to detect if top-level is an array or object
            first_byte = f.read(1)
            while first_byte in (b" ", b"\t", b"\n", b"\r"):
                first_byte = f.read(1)
            f.seek(0)

            if first_byte == b"[":
                # Array of objects
                for item in ijson.items(f, "item"):
                    if isinstance(item, dict):
                        yield _flatten(item)
                    else:
                        yield {"value": str(item)}
            elif first_byte == b"{":
                # Could be a single object or NDJSON
                f.seek(0)
                content = f.read(1024)
                f.seek(0)
                # Heuristic: NDJSON has newline-separated JSON objects
                if b"\n{" in content or b"\n{" in content:
                    yield from self._stream_ndjson()
                else:
                    # Wrapped object: try to find an inner array field
                    try:
                        for prefix, event, value in ijson.parse(f):
                            pass
                    except Exception:
                        pass
                    f.seek(0)
                    obj = json.load(f)
                    yield from self._unwrap_object(obj)
            else:
                # NDJSON fallback
                yield from self._stream_ndjson()

    def _stream_ndjson(self) -> Generator[dict, None, None]:
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield _flatten(obj)
                except json.JSONDecodeError:
                    continue

    def _stream_fallback(self) -> Generator[dict, None, None]:
        """Full-file load fallback when ijson is unavailable."""
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield _flatten(item)
        elif isinstance(data, dict):
            yield from self._unwrap_object(data)

    def _unwrap_object(self, obj: dict) -> Generator[dict, None, None]:
        """BFS through nested dicts to locate records.

        At each node, checks in order:
        1. Keyed collection: all values are dicts with the same keys →
           yields each value flattened with '_key' injected.
        2. Wrapped array: a value is a non-empty list of dicts →
           yields its items flattened.
        3. Otherwise enqueues nested dicts and continues.
        Falls back to yielding the root object flattened if nothing matches.
        """
        queue = [obj]
        while queue:
            current = queue.pop(0)
            if not isinstance(current, dict):
                continue
            # 1. Keyed collection: ≥2 entries, every value is a dict, all share the same keys.
            # Requiring ≥2 avoids treating single-key wrapper dicts as collections.
            values = list(current.values())
            if len(current) >= 2 and all(isinstance(v, dict) for v in values):
                key_sets = [frozenset(v.keys()) for v in values]
                if len(set(key_sets)) == 1:
                    for k, v in current.items():
                        yield _flatten({"_key": k, **v})
                    return
            # 2. Wrapped array
            for v in current.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    for item in v:
                        yield _flatten(item)
                    return
                if isinstance(v, dict):
                    queue.append(v)
        yield _flatten(obj)
