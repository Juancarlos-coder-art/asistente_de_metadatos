"""
Temporal coverage / retention period resolution.

The structure step (StructureExtractor) maps date fields as an array of
{year, month, day} objects, where each part is null or {column, transform} and
has already been cleaned ON ITS OWN by its transform.

This module does the second half of the job:
  1. resolve each cleaned part to a Series (running its transform),
  2. join year/month/day into a single "YYYY-MM-DD" string column,
  3. standardize each value with utils.date_utils.parse_date,
  4. report the global {start, end} across every date-mapping of the field.
"""

import re
from datetime import datetime

import pandas as pd

from utils.date_utils import parse_date
from utils.logger import get_logger

log = get_logger(__name__)

# Tokens that mean "missing" once a part has been cast to string.
_MISSING = frozenset({"", "<na>", "nan", "none", "nat", "null"})


def _derived_col_name(expr: str) -> str | None:
    """Extract the assigned column name from a df['col'] = ... expression."""
    m = re.match(r"df\['([^']+)'\]\s*=", expr.strip())
    return m.group(1) if m else None


def _resolve_part(df: pd.DataFrame, part: dict | None) -> pd.Series | None:
    """Run a date part's transform and return the cleaned Series (or the raw column)."""
    if not part:
        return None

    transforms = part.get("transform") or []
    if isinstance(transforms, str):
        transforms = [transforms]

    if transforms:
        col_name = _derived_col_name(transforms[-1])
        if not col_name:
            return None
        working = df.copy()
        try:
            for expr in transforms:
                exec(expr, {"df": working, "pd": pd})  # noqa: S102
        except Exception as exc:
            log.warning("Failed to clean date part '%s' — %s", col_name, exc)
            return None
        return working.get(col_name)

    column = part.get("column")
    if column and column in df.columns:
        return df[column]
    return None


def _as_str(series: pd.Series, default: str) -> pd.Series:
    """Cast a part Series to a stripped string, replacing missing tokens with *default*."""
    s = series.astype(str).str.strip()
    return s.mask(s.str.lower().isin(_MISSING), default)


def build_date_series(df: pd.DataFrame, mapping: dict) -> pd.Series | None:
    """Join a {year, month, day} mapping into a single "YYYY-MM-DD" string Series.

    Year is mandatory; a missing month or day defaults to "01" so every row yields
    a parseable date. Rows with a missing year stay missing and are dropped later.
    """
    year = _resolve_part(df, mapping.get("year"))
    if year is None:
        return None

    year = _as_str(year, "")
    month = mapping.get("month") and _resolve_part(df, mapping.get("month"))
    day = mapping.get("day") and _resolve_part(df, mapping.get("day"))

    month = _as_str(month, "01") if month is not None else pd.Series("01", index=df.index)
    day = _as_str(day, "01") if day is not None else pd.Series("01", index=df.index)

    combined = year + "-" + month + "-" + day
    # Drop rows whose year never resolved (start with "-").
    return combined.where(year != "", other=pd.NA)


def coverage(df: pd.DataFrame, mappings: list) -> dict | None:
    """Global {start, end} across every date-mapping of a date field.

    Each mapping is resolved independently, joined into one column, and every value
    standardized with parse_date. The min becomes start, the max becomes end.
    """
    min_dates: list[datetime] = []
    max_dates: list[datetime] = []

    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        combined = build_date_series(df, mapping)
        if combined is None:
            continue
        parsed = [
            dt for raw in combined.dropna().astype(str)
            if (dt := parse_date(raw)) is not None
        ]
        if not parsed:
            continue
        min_dates.append(min(parsed))
        max_dates.append(max(parsed))

    if not min_dates:
        return None
    return {
        "start": min(min_dates).strftime("%Y-%m-%d"),
        "end": max(max_dates).strftime("%Y-%m-%d"),
    }
