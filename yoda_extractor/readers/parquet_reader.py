import pandas as pd
import pyarrow.parquet as pq
from typing import Generator
from .base import BaseReader

BATCH_SIZE = 10_000


class ParquetReader(BaseReader):
    def stream_records(self) -> Generator[dict, None, None]:
        pf = pq.ParquetFile(self.path)
        for batch in pf.iter_batches(batch_size=BATCH_SIZE):
            df = batch.to_pandas()
            for record in df.to_dict(orient="records"):
                yield {
                    k: str(v)
                    for k, v in record.items()
                    if v is not None and not (isinstance(v, float) and pd.isna(v))
                }
