from typing import Generator
from .base import BaseReader


class ExcelReader(BaseReader):
    def stream_records(self) -> Generator[dict, None, None]:
        from openpyxl import load_workbook

        wb = load_workbook(self.path, read_only=True, data_only=True)
        for sheet in wb.worksheets:
            headers = None
            for row in sheet.iter_rows(values_only=True):
                if headers is None:
                    # First row is the header
                    headers = [str(c) if c is not None else f"col_{i}" for i, c in enumerate(row)]
                    continue
                record = {}
                for header, cell in zip(headers, row):
                    if cell is None:
                        continue
                    val = str(cell).strip()
                    if val and val not in ("nan", "NaN", "None"):
                        record[header] = val
                if record:
                    yield record
        wb.close()
