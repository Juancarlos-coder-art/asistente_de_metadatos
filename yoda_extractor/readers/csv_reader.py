import pandas as pd
from typing import Generator
from .base import BaseReader
from utils.logger import get_logger

log = get_logger(__name__)

CHUNK_SIZE = 10_000


class CSVReader(BaseReader):
    def _detect_encoding(self) -> str:
        try:
            with open(self.path, "rb") as f:
                chunk = f.read(10_000)
            chunk.decode("utf-8")
            return "utf-8-sig"
        except UnicodeDecodeError:
            return "latin-1"

    def _detect_delimiter(self, encoding: str) -> str:
        try:
            with open(self.path, "r", encoding=encoding, errors="replace") as f:
                lines = [f.readline() for _ in range(5)]
            lines = [line.strip() for line in lines if line.strip()]
            if not lines:
                return ","
            
            delimiters = [";", ",", "\t", "|"]
            counts = {d: 0 for d in delimiters}
            for d in delimiters:
                line_counts = [line.count(d) for line in lines]
                # A good delimiter should have consistent count across lines
                if all(c > 0 for c in line_counts) and len(set(line_counts)) == 1:
                    counts[d] = line_counts[0] * 100
                else:
                    counts[d] = sum(line_counts)
            
            best = max(counts, key=counts.get)
            if counts[best] > 0:
                return best
        except Exception as e:
            log.warning("Delimiter detection failed: %s", e)
        return ","

    def stream_records(self) -> Generator[dict, None, None]:
        encoding = self._detect_encoding()
        delim = self._detect_delimiter(encoding)
        for chunk in pd.read_csv(
            self.path,
            sep=delim,
            encoding=encoding,
            chunksize=CHUNK_SIZE,
            low_memory=False,
            dtype=str,          # keep everything as string; let extractors parse
            encoding_errors="replace",
        ):
            for record in chunk.to_dict(orient="records"):
                yield {k: v for k, v in record.items() if pd.notna(v)}

