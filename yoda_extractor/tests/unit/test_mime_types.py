from utils.mime_types import get_mimetype


def test_known_extension_csv():
    assert get_mimetype("data.csv") == "text/csv"


def test_known_extension_json():
    assert get_mimetype("data.json") == "application/json"


def test_known_extension_xlsx():
    result = get_mimetype("data.xlsx")
    assert result is not None
    assert "spreadsheet" in result or "excel" in result.lower() or "openxmlformats" in result


def test_known_extension_xml():
    result = get_mimetype("data.xml")
    assert result is not None
    assert "xml" in result


def test_known_extension_parquet():
    result = get_mimetype("data.parquet")
    assert result is not None


def test_unknown_extension_returns_none():
    assert get_mimetype("data.unknownextension123") is None


def test_path_with_directory():
    assert get_mimetype("/some/path/to/data.csv") == "text/csv"


def test_extension_is_case_insensitive():
    assert get_mimetype("data.CSV") == get_mimetype("data.csv")
