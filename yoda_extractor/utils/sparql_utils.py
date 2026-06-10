"""
SPARQL batch resolver for the EU Publications Office geographic vocabularies.

Endpoint: https://publications.europa.eu/webapi/rdf/sparql
Schemes searched: country · continent · atu (NUTS regions) · place

Spanish territories (provincia, comunidad autónoma) are handled upstream by
the static dicts in utils/spain_geo.py and never reach this module.

Queries are batched (BATCH_SIZE values per request) to limit HTTP traffic.
All results are returned as {raw_value: (uri, vocabulary_name) | None}.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

BATCH_SIZE = 50  # values per SPARQL VALUES clause

_EU_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"

# Scheme URI → (priority, vocabulary label).  Lower number = preferred.
_SCHEME_PRIORITY: dict[str, tuple[int, str]] = {
    "http://publications.europa.eu/resource/authority/country":   (1, "eu_country"),
    "http://publications.europa.eu/resource/authority/continent": (2, "eu_continent"),
    "http://publications.europa.eu/resource/authority/atu":       (3, "eu_atu"),
    "http://publications.europa.eu/resource/authority/place":     (4, "eu_place"),
}

# ── Query templates ───────────────────────────────────────────────────────────

_EU_QUERY = """\
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?input ?uri ?scheme WHERE {{
  VALUES ?input {{ {values} }}
  VALUES ?scheme {{
    <http://publications.europa.eu/resource/authority/country>
    <http://publications.europa.eu/resource/authority/continent>
    <http://publications.europa.eu/resource/authority/atu>
    <http://publications.europa.eu/resource/authority/place>
  }}
  ?uri skos:inScheme ?scheme ;
       skos:prefLabel|skos:altLabel ?label .
  FILTER(LCASE(STR(?label)) = LCASE(?input))
}}
LIMIT {limit}"""

# ── HTTP helper ───────────────────────────────────────────────────────────────

def _post(endpoint: str, query: str, timeout: int = 10) -> Optional[dict]:
    """POST a SPARQL query and return the parsed JSON result, or None on error."""
    data = urllib.parse.urlencode({
        "query": query,
        "format": "application/sparql-results+json",
    }).encode()
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _fmt_values(strings: list[str]) -> str:
    """Escape and format a list of strings as a SPARQL VALUES literal list."""
    return " ".join(
        '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
        for s in strings
    )


def _pick_best(candidates: list[tuple[str, str]]) -> Optional[tuple[str, str]]:
    """Return (uri, vocab) for the highest-priority scheme among candidates."""
    best_priority, best = 999, None
    for uri, scheme in candidates:
        priority, vocab = _SCHEME_PRIORITY.get(scheme, (998, "unknown"))
        if priority < best_priority:
            best_priority, best = priority, (uri, vocab)
    return best

# ── Per-endpoint resolvers ────────────────────────────────────────────────────

def _resolve_eu(batch: list[str]) -> dict[str, Optional[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {v: [] for v in batch}
    lowered = {v.lower(): v for v in batch}

    result = _post(_EU_ENDPOINT, _EU_QUERY.format(
        values=_fmt_values(batch),
        limit=len(batch) * len(_SCHEME_PRIORITY),
    ))
    if result:
        for row in result.get("results", {}).get("bindings", []):
            raw    = row.get("input",  {}).get("value", "")
            uri    = row.get("uri",    {}).get("value", "")
            scheme = row.get("scheme", {}).get("value", "")
            orig = lowered.get(raw.lower())
            if orig:
                out[orig].append((uri, scheme))

    return {v: _pick_best(matches) for v, matches in out.items()}


# ── Public API ────────────────────────────────────────────────────────────────

def resolve_batch(
    values: list[str],
    batch_size: int = BATCH_SIZE,
) -> dict[str, Optional[tuple[str, str]]]:
    """
    Resolve *values* to (uri, vocabulary) pairs via the EU Publications Office.
    Sends at most ceil(len(values) / batch_size) HTTP requests.
    Returns {raw_value: (uri, vocab) | None}.
    """
    result: dict[str, Optional[tuple[str, str]]] = {}

    for i in range(0, len(values), batch_size):
        batch = values[i : i + batch_size]
        result.update(_resolve_eu(batch))

    return result
