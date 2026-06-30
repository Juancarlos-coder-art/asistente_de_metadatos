# Dataset Readers (`readers/`)

Responsible for loading and streaming tabular or structured datasets record-by-record into flat Python dictionaries. By streaming records instead of loading entire files into memory, the pipeline remains memory-efficient even when dealing with extremely large datasets.

All readers inherit from `BaseReader` (`readers/base.py`) and implement a generator method `stream_records() -> Generator[dict, None, None]`.

---

## Supported Formats

The appropriate reader is automatically resolved by the pipeline using the file extension:

| File Extension | Reader Class | Supported Features |
|----------------|--------------|--------------------|
| `.csv` | `CSVReader` | Encoding auto-detection, delimiter auto-detection, chunked loading. |
| `.xlsx`, `.xls` | `ExcelReader` | Worksheet iteration, auto-detected header row, low-memory read-only streaming. |
| `.json` | `JSONReader` | Standard JSON Arrays, NDJSON, nested object unwrapping (score-based), `ijson` memory-efficient streaming. |
| `.parquet` | `ParquetReader` | Single files or partition-based Parquet directories. |
| `.xml` | `XMLReader` | Low-memory iterative parsing (`iterparse`), automatic record tag detection. |

---

## Reader Implementations

### 1. CSV Reader (`readers/csv_reader.py`)

Streams records from delimited text files in chunks of 10,000 using Pandas `read_csv`.

* **Encoding Auto-detection**: Inspects the first 10,000 bytes. It attempts to decode with UTF-8 (and supports UTF-8 BOM by mapping to `utf-8-sig`). If a `UnicodeDecodeError` is raised, it automatically switches to `latin-1` to preserve Spanish characters (like `ñ`, `ó`, etc.).
* **Delimiter Auto-detection**: Scans the first 5 non-empty lines and checks for candidate separators: `;`, `,`, `\t`, and `|`. It scores delimiters based on how consistently and frequently they appear across lines, prioritizing separators that appear in equal numbers on every line.
* **Casting**: Keeps all fields as string (`dtype=str`) during parsing to avoid Pandas making premature casting decisions, leaving coercion to downstream extractors.

> [!NOTE]
> If encoding or delimiter detection fails to find a clear candidate, it defaults to `utf-8-sig` and comma-delimited `,` parsing.

---

### 2. Excel Reader (`readers/excel_reader.py`)

Loads spreadsheets using `openpyxl` with `read_only=True` to minimize RAM consumption.

* **Worksheet Iteration**: Loops through all worksheets in the workbook.
* **Header Auto-detection**: Instead of assuming headers are on row 0, it reads the first 10 rows and scores them. The row containing the highest count of non-empty values is selected as the header row. This automatically skips introductory title rows, logos, or empty rows.
* **Row Streaming**: Rows below the detected header are yielded as dictionaries mapping header labels to cell values, discarding cells containing `NaN` or empty strings.

---

### 3. JSON Reader (`readers/json_reader.py`)

A highly sophisticated reader designed to stream JSON records from various schema patterns.

* **Memory-Efficient Streaming (`ijson`)**: Attempts to use the `ijson` library to stream objects one-by-one without loading the entire document. If `ijson` is missing, it falls back to standard `json.load`.
* **UTF-8 BOM Support**: Detects and skips the 3-byte BOM sequence `\xef\xbb\xbf`.
* **Structural Types Handled**:
  1. **Arrays**: Streams elements inside a root array `[...]`.
  2. **NDJSON**: Detects newline-separated JSON structures (like `{"a": 1}\n{"a": 2}`) and parses line-by-line.
  3. **Nested/Wrapped Objects**: If the root is a single dictionary containing metadata alongside the dataset list, the reader runs a recursive scoring traversal to unwrap the dataset:
     * **List of dicts**: Evaluated by the average keys per dictionary times list length.
     * **Keyed Collections**: Evaluated by number of keys times key consistency (records mapped to keys).
     * **Tabular Lists of Lists**: Recognizes rows stored as arrays. It searches sibling keys (like metadata dictionaries or codelist schemas) to find list headers (e.g. searching for fields named `"id"`, `"name"`, `"label"`) and maps the values correctly.

---

### 4. Parquet Reader (`readers/parquet_reader.py`)

Reads columnar datasets using `pyarrow.parquet`.

* **Fragment/Partition Streaming**: Uses `pyarrow.parquet.ParquetDataset` which automatically detects partitioned data structures (multi-file folders formatted by columns) as well as single files.
* **Batch Conversion**: Iterates through fragments and batch chunks, converting them to Pandas dataframes dynamically and yielding row dictionaries. All values are cast to string representations.

---

### 5. XML Reader (`readers/xml_reader.py`)

Processes nested hierarchical XML trees using low-memory iterative parsing (`xml.etree.ElementTree.iterparse`).

* **Two-Pass Parse**:
  1. **Pass 1**: Iterates over start elements to count child tag frequencies under the root. The tag with the highest occurrence count (minimum 5 hits) is declared the repeated dataset "record" tag.
  2. **Pass 2**: Iterates on element end events. When the target record tag is encountered, it flattens the sub-tree into a flat dictionary, strips XML namespaces, and clears the element's node memory to keep RAM usage stable.
* **Hierarchical Flattening**: Attributes are included as top-level keys. Children are flattened using dot-notation (e.g. `<parent><child>text</child></parent>` is flattened to `parent.child: "text"`). If children share the same tag name, numeric suffixes (e.g. `tag_1`, `tag_2`) are appended.

---

## Edge cases

| Situation | Behaviour |
|-----------|-----------|
| Empty file | Generator completes immediately without yielding records |
| Unsupported extension | Throws a `ValueError` during reader resolution |
| Missing Excel headers | Columns without a label in the header row default to `col_0`, `col_1` |
| JSON List of Lists without metadata headers | Column names default to `column_0`, `column_1` |
| Deeply nested JSON/XML structures | Recursively flattened using dot-notation (`root.parent.child`) |
| Invalid JSON line in NDJSON | The invalid line is skipped, and parsing continues with the next lines |
