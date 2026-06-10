from .csv_reader import CSVReader
from .json_reader import JSONReader
from .xml_reader import XMLReader
from .excel_reader import ExcelReader
from .parquet_reader import ParquetReader

READERS = {
    ".csv": CSVReader,
    ".json": JSONReader,
    ".xml": XMLReader,
    ".xlsx": ExcelReader,
    ".xls": ExcelReader,
    ".parquet": ParquetReader,
}


def get_reader(path: str):
    import os
    ext = os.path.splitext(path)[1].lower()
    if ext not in READERS:
        raise ValueError(f"Unsupported file extension: {ext!r}. Supported: {list(READERS)}")
    return READERS[ext](path)
