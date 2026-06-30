from datetime import datetime

import pytest

from utils.date_utils import is_likely_date_column, parse_date


# ── parse_date: quick-reject cases ───────────────────────────────────────────

def test_returns_none_for_non_string():
    assert parse_date(None) is None
    assert parse_date(12345) is None
    assert parse_date(3.14) is None


def test_returns_none_for_too_short_string():
    assert parse_date("") is None
    assert parse_date("202") is None
    assert parse_date("2020") is None


def test_returns_none_for_non_date_tokens():
    for token in ("nan", "none", "null", "n/a", "na", "unknown", "true", "false", "-", "--"):
        assert parse_date(token) is None, f"Expected None for token: {token!r}"


def test_returns_none_for_plain_integers():
    assert parse_date("123") is None
    assert parse_date("999999") is None


def test_returns_none_for_plain_floats():
    assert parse_date("3.14") is None
    assert parse_date("0.5") is None


# ── parse_date: valid ISO formats ─────────────────────────────────────────────

def test_parses_iso_date():
    result = parse_date("2023-05-15")
    assert result == datetime(2023, 5, 15)


def test_parses_iso_datetime():
    result = parse_date("2023-05-15T14:30:00")
    assert result == datetime(2023, 5, 15, 14, 30, 0)


def test_parses_iso_datetime_with_z():
    result = parse_date("2023-05-15T14:30:00Z")
    assert result is not None
    assert result.year == 2023
    assert result.tzinfo is None


def test_parses_iso_datetime_with_microseconds():
    result = parse_date("2023-05-15T14:30:00.123456")
    assert result is not None
    assert result.year == 2023


# ── parse_date: day-first formats ────────────────────────────────────────────

def test_parses_day_first_slash():
    result = parse_date("15/05/2023")
    assert result == datetime(2023, 5, 15)


def test_parses_day_first_dash():
    result = parse_date("15-05-2023")
    assert result == datetime(2023, 5, 15)


def test_parses_day_first_dot():
    result = parse_date("15.05.2023")
    assert result == datetime(2023, 5, 15)


# ── parse_date: year-month only ──────────────────────────────────────────────

def test_parses_year_month():
    result = parse_date("2023-05")
    assert result is not None
    assert result.year == 2023
    assert result.month == 5


# ── parse_date: compact format ───────────────────────────────────────────────

def test_parses_compact_yyyymmdd():
    result = parse_date("20230515")
    assert result == datetime(2023, 5, 15)


# ── parse_date: named month formats ─────────────────────────────────────────

def test_parses_named_month_long():
    result = parse_date("15 January 2023")
    assert result == datetime(2023, 1, 15)


def test_parses_named_month_short():
    result = parse_date("15 Jan 2023")
    assert result == datetime(2023, 1, 15)


# ── parse_date: timezone-naive guarantee ─────────────────────────────────────

def test_result_is_always_timezone_naive():
    result = parse_date("2023-05-15T14:30:00Z")
    assert result is not None
    assert result.tzinfo is None


# ── is_likely_date_column ────────────────────────────────────────────────────

def test_likely_date_column_with_enough_dates():
    sample = ["2020-01-01", "2021-06-15", "2022-12-31", "2023-03-20"]
    assert is_likely_date_column(sample) is True


def test_not_likely_date_column_when_too_few_hits():
    sample = ["2020-01-01", "hello", "world", "not-a-date", "still-not"]
    assert is_likely_date_column(sample) is False


def test_not_likely_date_column_empty():
    assert is_likely_date_column([]) is False


def test_not_likely_date_column_all_empty_strings():
    assert is_likely_date_column(["", "", ""]) is False


def test_likely_date_column_respects_min_hits():
    sample = ["2020-01-01", "2021-06-15"]
    assert is_likely_date_column(sample, min_hits=3) is False


def test_likely_date_column_respects_threshold():
    sample = ["2020-01-01", "2021-06-15", "2022-12-31", "not-a-date", "not-a-date", "not-a-date"]
    assert is_likely_date_column(sample, threshold=0.8) is False
    assert is_likely_date_column(sample, threshold=0.4) is True
