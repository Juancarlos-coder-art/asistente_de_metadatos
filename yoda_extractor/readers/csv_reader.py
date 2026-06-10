import pandas as pd
from typing import Generator
from .base import BaseReader

CHUNK_SIZE = 10_000


class CSVReader(BaseReader):
    def stream_records(self) -> Generator[dict, None, None]:
        for chunk in pd.read_csv(
            self.path,
            chunksize=CHUNK_SIZE,
            low_memory=False,
            dtype=str,          # keep everything as string; let extractors parse
            encoding_errors="replace",
        ):
            for record in chunk.to_dict(orient="records"):
                yield {k: v for k, v in record.items() if pd.notna(v)}
