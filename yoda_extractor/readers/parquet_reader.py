import pandas as pd
import pyarrow.parquet as pq
from typing import Generator
from .base import BaseReader


class ParquetReader(BaseReader):
    def stream_records(self) -> Generator[dict, None, None]:
        dataset = pq.ParquetDataset(self.path)
        for fragment in dataset.fragments:
            for batch in fragment.to_batches():
                df = batch.to_pandas()
                for record in df.to_dict(orient="records"):
                    yield {
                        k: str(v)
                        for k, v in record.items()
                        if v is not None and not (isinstance(v, float) and pd.isna(v))
                    }

