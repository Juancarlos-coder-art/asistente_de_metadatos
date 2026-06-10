"""
DataFrame statistics extractor.

Receives an already-loaded pandas DataFrame and the output of StructureExtractor.
All column identification has already been done by the structure step — this extractor
only resolves the mapped columns (applying transforms when needed) and computes values.
"""

import re
from typing import Any

import pandas as pd

from .base import BaseExtractor
from . import temporal
from utils.logger import get_logger

log = get_logger(__name__)


# ── Shared helper ─────────────────────────────────────────────────────────────

def _derived_col_name(expr: str) -> str | None:
    """Extract the assigned column name from a df['col'] = ... expression."""
    m = re.match(r"df\['([^']+)'\]\s*=", expr.strip())
    return m.group(1) if m else None


def _resolve_series(df: pd.DataFrame, mapping: dict) -> pd.Series | None:
    """Return the target Series for a structure mapping, applying transforms if needed.

    transform is an ordered list of pandas expressions; the last one that assigns
    to df['<field>_mod_N'] is the final derived column. Executes each expression
    in sequence on a working copy of df.
    """
    cols = mapping.get("columns", [])
    transforms: list = mapping.get("transform") or []
    if isinstance(transforms, str):
        transforms = [transforms]

    if transforms:
        final_expr = transforms[-1]
        col_name = _derived_col_name(final_expr)
        if not col_name:
            return None
        working = df.copy()
        try:
            for expr in transforms:
                exec(expr, {"df": working, "pd": pd})  # noqa: S102
        except Exception as exc:
            log.warning("Failed to apply transform for '%s' — %s", col_name, exc)
            return None
        return working.get(col_name)

    col_name = cols[0] if cols else None
    if not col_name or col_name not in df.columns:
        return None
    return df[col_name]


# ── Extractor ─────────────────────────────────────────────────────────────────

class DataFrameStatisticsExtractor(BaseExtractor):
    name = "dataframe_statistics"

    def update(self, record: dict) -> None:
        pass

    def result(self) -> dict[str, Any]:
        return {}

    def finalize(self, results: dict, df: pd.DataFrame | None) -> dict[str, Any]:
        if df is None:
            log.warning("No DataFrame available — skipping dataframe_statistics")
            return {}
        structure = results.get("structure", {})
        log.info("Computing dataframe statistics (%d rows)", len(df))
        return self._extract(df, structure)

    def _extract(self, df: pd.DataFrame, structure: dict) -> dict:
        """
        Compute statistics from df using the column mappings in structure.

        structure is the direct output of StructureExtractor. Value fields are
        arrays of {"columns": [...], "transform": [...]} objects; the date fields
        (temporal_coverage) are arrays of {year, month, day}
        objects resolved and standardized in extractors.temporal.
        """
        return {
            "number_of_records": len(df),
            "number_of_unique_individuals": self._count_unique(
                df, structure.get("number_of_unique_individuals", [])
            ),
            "min_typical_age": self._agg_numeric(
                df, structure.get("min_typical_age", []), "min"
            ),
            "max_typical_age": self._agg_numeric(
                df, structure.get("max_typical_age", []), "max"
            ),
            "temporal_coverage": temporal.coverage(
                df, structure.get("temporal_coverage", [])
            ),
        }

    # ── Per-field methods ──────────────────────────────────────────────────────

    def _count_unique(self, df: pd.DataFrame, mappings: list) -> int | None:
        """Distinct value count from the first valid identifier mapping."""
        for mapping in mappings:
            series = _resolve_series(df, mapping)
            if series is None:
                continue
            return int(series.nunique())
        return None

    def _agg_numeric(self, df: pd.DataFrame, mappings: list, agg: str) -> int | float | None:
        """Min or max numeric value from the first valid mapping."""
        for mapping in mappings:
            series = _resolve_series(df, mapping)
            if series is None:
                continue
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            if numeric.empty:
                continue
            value = numeric.min() if agg == "min" else numeric.max()
            return int(value) if value == int(value) else float(value)
        return None
