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

def _resolve_series(df: pd.DataFrame, mapping: dict) -> pd.Series | None:
    """Return the target Series for a structure mapping, applying transforms if needed.

    With DSL, uses the safe evaluate_dsl interpreter.
    """
    from utils.dsl_evaluator import evaluate_dsl
    cols = mapping.get("columns", [])
    transforms = mapping.get("transform") or []
    
    if transforms:
        try:
            return evaluate_dsl(df, mapping)
        except Exception as exc:
            log.warning("Failed to apply DSL transform — %s", exc)
            return None

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
        prefilled = {
            f: self.input_json[f]
            for f in ("number_of_records", "number_of_unique_individuals", "min_typical_age", "max_typical_age", "temporal_coverage")
            if f in self.input_json and self.has_content(self.input_json[f])
        }
        if df is None:
            if prefilled:
                log.info("No DataFrame available, returning prefilled stats: %s", list(prefilled.keys()))
                return prefilled
            log.warning("No DataFrame available — skipping dataframe_statistics")
            return {}
        structure = results.get("structure_tmpt", {})
        log.info("Computing dataframe statistics (%d rows)", len(df))
        return self._extract(df, structure)

    def _extract(self, df: pd.DataFrame, structure: dict) -> dict:
        out = {}
        
        if "number_of_records" in self.input_json and self.has_content(self.input_json["number_of_records"]):
            out["number_of_records"] = self.input_json["number_of_records"]
        else:
            out["number_of_records"] = len(df)
            
        if "number_of_unique_individuals" in self.input_json and self.has_content(self.input_json["number_of_unique_individuals"]):
            out["number_of_unique_individuals"] = self.input_json["number_of_unique_individuals"]
        else:
            out["number_of_unique_individuals"] = self._count_unique(
                df, structure.get("number_of_unique_individuals", [])
            )
            
        if "min_typical_age" in self.input_json and self.has_content(self.input_json["min_typical_age"]):
            out["min_typical_age"] = self.input_json["min_typical_age"]
        else:
            out["min_typical_age"] = self._agg_numeric(
                df, structure.get("min_typical_age", []), "min"
            )
            
        if "max_typical_age" in self.input_json and self.has_content(self.input_json["max_typical_age"]):
            out["max_typical_age"] = self.input_json["max_typical_age"]
        else:
            out["max_typical_age"] = self._agg_numeric(
                df, structure.get("max_typical_age", []), "max"
            )
            
        if "temporal_coverage" in self.input_json and self.has_content(self.input_json["temporal_coverage"]):
            out["temporal_coverage"] = self.input_json["temporal_coverage"]
        else:
            out["temporal_coverage"] = temporal.coverage(
                df, structure.get("temporal_coverage", [])
            )
            
        return out

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
