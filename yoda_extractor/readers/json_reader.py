import json
from typing import Generator
from .base import BaseReader
from utils.logger import get_logger

log = get_logger(__name__)


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
            # Detect UTF-8 BOM
            lead = f.read(3)
            has_bom = (lead == b"\xef\xbb\xbf")
            if not has_bom:
                f.seek(0)

            # Read first non-whitespace character
            first_byte = f.read(1)
            while first_byte in (b" ", b"\t", b"\n", b"\r"):
                first_byte = f.read(1)
            
            start_pos = 3 if has_bom else 0
            f.seek(start_pos)

            if first_byte == b"[":
                # Array of objects
                for item in ijson.items(f, "item"):
                    if isinstance(item, dict):
                        yield _flatten(item)
                    else:
                        yield {"value": str(item)}
            elif first_byte == b"{":
                # Could be a single object or NDJSON
                content = f.read(1024)
                f.seek(start_pos)
                # Heuristic: NDJSON has newline-separated JSON objects
                if b"\n{" in content:
                    yield from self._stream_ndjson()
                else:
                    # Wrapped object: try to find an inner array field
                    try:
                        for prefix, event, value in ijson.parse(f):
                            pass
                    except Exception as e:
                        log.debug("ijson validation failed (falling back to standard json): %s", e)
                    f.seek(start_pos)
                    with open(self.path, "r", encoding="utf-8-sig") as text_f:
                        obj = json.load(text_f)
                    yield from self._unwrap_object(obj)
            else:
                # NDJSON fallback
                yield from self._stream_ndjson()

    def _stream_ndjson(self) -> Generator[dict, None, None]:
        with open(self.path, "r", encoding="utf-8-sig", errors="replace") as f:
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
        with open(self.path, "r", encoding="utf-8-sig", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield _flatten(item)
        elif isinstance(data, dict):
            yield from self._unwrap_object(data)

    def _unwrap_object(self, obj: dict) -> Generator[dict, None, None]:
        """Find the main dataset candidate inside a nested JSON structure.

        Uses structural heuristics and scoring to identify the best dataset representation:
        - List of dicts
        - List of lists (tabular rows), matched to potential header columns found in sibling keys
        - Keyed collection (dict of dicts sharing the same keys)
        """
        candidates = []

        def traverse(val, path, parent):
            if isinstance(val, dict):
                if len(val) >= 2:
                    values = list(val.values())
                    if all(isinstance(v, dict) for v in values):
                        key_sets = [frozenset(v.keys()) for v in values]
                        if len(set(key_sets)) == 1:
                            avg_keys = len(key_sets[0])
                            score = len(val) * avg_keys
                            candidates.append({
                                "type": "keyed_collection",
                                "score": score,
                                "data": val,
                                "path": path,
                                "parent": parent
                            })
                
                for k, v in val.items():
                    traverse(v, path + (k,), val)
                    
            elif isinstance(val, list):
                if not val:
                    return
                
                if all(isinstance(v, dict) for v in val):
                    avg_keys = sum(len(v) for v in val) / len(val)
                    score = len(val) * avg_keys
                    candidates.append({
                        "type": "list_of_dicts",
                        "score": score,
                        "data": val,
                        "path": path,
                        "parent": parent
                    })
                elif all(isinstance(v, list) for v in val):
                    inner_lens = [len(v) for v in val]
                    if len(set(inner_lens)) == 1 or (len(inner_lens) > 0 and sum(inner_lens)/len(inner_lens) > 0):
                        avg_len = sum(inner_lens) / len(inner_lens)
                        score = len(val) * avg_len
                        candidates.append({
                            "type": "list_of_lists",
                            "score": score,
                            "data": val,
                            "path": path,
                            "parent": parent
                        })
                
                for i, v in enumerate(val):
                    traverse(v, path + (i,), val)

        traverse(obj, (), None)

        if not candidates:
            yield _flatten(obj)
            return

        best = max(candidates, key=lambda c: c["score"])

        if best["type"] == "list_of_dicts":
            for item in best["data"]:
                yield _flatten(item)
        elif best["type"] == "keyed_collection":
            for k, v in best["data"].items():
                yield _flatten({"_key": k, **v})
        elif best["type"] == "list_of_lists":
            rows = best["data"]
            row_len = len(rows[0]) if rows else 0
            parent = best["parent"]

            headers = []
            if isinstance(parent, dict):
                for k, sibling in parent.items():
                    if isinstance(sibling, list) and sibling is not rows and len(sibling) == row_len:
                        possible_headers = []
                        for item in sibling:
                            if isinstance(item, str):
                                possible_headers.append(item)
                            elif isinstance(item, dict):
                                h_name = item.get("id") or item.get("name") or item.get("key") or item.get("label")
                                if h_name:
                                    possible_headers.append(str(h_name))
                        if len(possible_headers) == row_len:
                            headers = possible_headers
                            break

            if not headers:
                headers = [f"column_{i}" for i in range(row_len)]

            for row in rows:
                record_dict = {}
                for i, val in enumerate(row):
                    if i < len(headers):
                        record_dict[headers[i]] = val
                    else:
                        record_dict[f"column_{i}"] = val
                yield _flatten(record_dict)
