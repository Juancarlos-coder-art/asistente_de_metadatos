"""
Date parsing utilities.

Strategy (in order):
1. Quick reject: value is too short, purely numeric without separators, or a
   known non-date token.
2. Explicit format list: fast strptime against common patterns.
3. dateutil.parser.parse: handles almost everything else.

All functions return a timezone-naive datetime.datetime or None.
"""

import re
from datetime import datetime
from typing import Optional

from dateutil import parser as du_parser
from dateutil.parser import ParserError

# ── Quick-reject patterns ─────────────────────────────────────────────────────

_NON_DATE_TOKENS = frozenset({
    "nan", "none", "null", "n/a", "na", "undefined", "unknown",
    "true", "false", "", "-", "--",
})

# Values that look like plain integers (IDs, counts, codes) — skip them
_PLAIN_INT_RE = re.compile(r"^\d{1,6}$")

# Values that look like plain floats without separators
_PLAIN_FLOAT_RE = re.compile(r"^\d+\.\d+$")

# Minimum length for a value to bother attempting a parse
_MIN_LEN = 6

# ── Explicit format list ──────────────────────────────────────────────────────

_FORMATS = [
    # ISO variants
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    # Day-first variants
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    # Month-first (US) variants
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%m-%d-%Y",
    # Year-first without dashes
    "%Y%m%d",
    # With month names
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d-%b-%Y",
    "%d-%B-%Y",
    # Year-first with month name (produced by temporal.py when joining date parts)
    "%Y-%B-%d",
    "%Y-%b-%d",
    "%Y-%B",
    "%Y-%b",
    # RFC / HTTP
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S",
    # Year-month only
    "%Y-%m",
    "%m/%Y",
    "%Y/%m",
]


def _strip_timezone(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def parse_date(value: str) -> Optional[datetime]:
    """
    Attempt to parse *value* as a date/datetime.
    Returns a timezone-naive datetime or None if parsing fails.
    """
    if not isinstance(value, str):
        return None

    cleaned = value.strip()

    if len(cleaned) < _MIN_LEN:
        return None

    if cleaned.lower() in _NON_DATE_TOKENS:
        return None

    if _PLAIN_INT_RE.match(cleaned) or _PLAIN_FLOAT_RE.match(cleaned):
        return None

    # Fast path: try explicit formats first
    for fmt in _FORMATS:
        try:
            return _strip_timezone(datetime.strptime(cleaned, fmt))
        except ValueError:
            continue

    # Slow path: let dateutil handle the rest
    try:
        dt = du_parser.parse(cleaned, dayfirst=False, yearfirst=False)
        # Reject if dateutil guessed today's date (means it found no date info)
        today = datetime.now().date()
        if dt.date() == today and not any(
            token in cleaned for token in (str(today.year), str(today.day))
        ):
            return None
        return _strip_timezone(dt)
    except (ParserError, OverflowError, ValueError):
        return None


def is_likely_date_column(
    sample_values: list[str],
    threshold: float = 0.6,
    min_hits: int = 3,
) -> bool:
    """
    Return True if at least *threshold* fraction of non-empty sample values
    parse as dates AND the absolute hit count meets *min_hits*.
    """
    non_empty = [v for v in sample_values if v and v.strip() not in _NON_DATE_TOKENS]
    if not non_empty:
        return False
    hits = sum(1 for v in non_empty if parse_date(v) is not None)
    return hits >= min_hits and hits / len(non_empty) >= threshold
