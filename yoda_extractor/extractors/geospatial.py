"""
Geospatial extractor — linked-data URI mapping.

Detection (two phases, mirrors temporal extractor):
  Phase 1 — sampling (first SAMPLE_SIZE records):
    Candidate columns are those whose name contains a geo keyword.
    Up to SAMPLE_SIZE unique values are collected per candidate column.

  Phase 2 — confirmation:
    All unique sample values are batch-resolved via SPARQL (one HTTP request
    per BATCH_SIZE values).  A column is confirmed when ≥ MIN_HIT_RATE of its
    sampled values resolve to a linked-data URI.

Full scan:
  resolve_value() checks the pre-warmed SPARQL cache — no more network calls
  for values seen in the sample.  Values that appear for the first time during
  the full scan fall back to an individual SPARQL query (also cached).

Result keys:
  geo_columns       confirmed geographic columns
  total_records     total records processed
  records_with_geo  records with ≥ 1 resolved URI
  coverage_percent  records_with_geo / total_records × 100
  mappings          {col → {raw_value → {uri, vocabulary, count}}}
  unresolved        {col → [up to MAX_UNRESOLVED unique unresolved values]}
  vocabularies_used sorted list of vocabulary names encountered
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from .base import BaseExtractor
from utils.geo_utils import (
    is_geo_column_by_name,
    is_geo_column_by_values,
    resolve_value,
    warm_sparql_cache,
)

SAMPLE_SIZE    = 200
MIN_HIT_RATE   = 0.30
MAX_UNRESOLVED = 20


class GeospatialExtractor(BaseExtractor):
    name = "geospatial"

    def __init__(self, file_path: str = "") -> None:
        super().__init__(file_path)
        self._total: int = 0
        self._with_geo: int = 0

        # Sampling phase
        self._buffer: list[dict] = []
        self._candidates: Optional[list[str]] = None   # None → not determined yet
        self._col_samples: dict[str, list[str]] = {}

        # Post-confirmation
        self._geo_cols: Optional[list[str]] = None
        # {col → {raw → {"uri": str, "vocabulary": str, "count": int}}}
        self._mappings: dict[str, dict[str, dict]] = defaultdict(dict)
        self._unresolved: dict[str, set[str]] = defaultdict(set)

    # ── Public API ─────────────────────────────────────────────────────────────

    def update(self, record: dict) -> None:
        self._total += 1
        if self._geo_cols is None:
            self._sample(record)
        else:
            self._process(record)

    def result(self) -> dict[str, Any]:
        if self._geo_cols is None:
            self._finalize_detection()
            for r in self._buffer:
                self._process(r)

        if not self._geo_cols:
            return {
                "status": "no_geo_columns_found",
                "total_records": self._total,
                "geo_columns": [],
            }

        coverage = (
            round(self._with_geo / self._total * 100, 2) if self._total else 0.0
        )
        vocabs = sorted({
            e["vocabulary"]
            for col_map in self._mappings.values()
            for e in col_map.values()
        })

        return {
            "geo_columns": sorted(self._geo_cols),
            "total_records": self._total,
            "records_with_geo": self._with_geo,
            "coverage_percent": coverage,
            "mappings": {col: dict(entries) for col, entries in self._mappings.items()},
            "unresolved": {
                col: sorted(vals)[:MAX_UNRESOLVED]
                for col, vals in self._unresolved.items()
                if vals
            },
            "vocabularies_used": vocabs,
        }

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _sample(self, record: dict) -> None:
        self._buffer.append(record)

        if self._candidates is None:
            self._candidates = [c for c in record if is_geo_column_by_name(c)]

        for col in self._candidates:
            val = record.get(col)
            if not isinstance(val, str) or not val.strip():
                continue
            samples = self._col_samples.setdefault(col, [])
            if len(samples) < SAMPLE_SIZE:
                samples.append(val.strip())

        if len(self._buffer) >= SAMPLE_SIZE:
            self._finalize_detection()
            for r in self._buffer:
                self._process(r)
            self._buffer = []

    def _finalize_detection(self) -> None:
        # Batch-resolve all sample values via SPARQL before confirming columns.
        # This ensures the 30% hit-rate check can use SPARQL results, not just
        # the built-in dict fast-path.  One set of batch queries, not one per value.
        all_sample_values = list({
            v
            for samples in self._col_samples.values()
            for v in samples
        })
        if all_sample_values:
            warm_sparql_cache(all_sample_values)

        self._geo_cols = [
            col for col, samples in self._col_samples.items()
            if is_geo_column_by_values(samples, threshold=MIN_HIT_RATE)
        ]
        self._col_samples = {}

    def _process(self, record: dict) -> None:
        found = False
        for col in self._geo_cols:  # type: ignore[union-attr]
            val = record.get(col)
            if not isinstance(val, str) or not val.strip():
                continue
            raw = val.strip()
            match = resolve_value(raw)
            if match:
                found = True
                uri, vocab = match
                if raw not in self._mappings[col]:
                    self._mappings[col][raw] = {"uri": uri, "vocabulary": vocab, "count": 0}
                self._mappings[col][raw]["count"] += 1
            else:
                self._unresolved[col].add(raw)
        if found:
            self._with_geo += 1
