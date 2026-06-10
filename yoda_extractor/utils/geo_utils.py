"""
Geospatial vocabulary lookup utilities.

Resolution order (first match wins):
  1. datos_provincia  — Spanish province dict (datos.gob.es, no network)
  2. datos_autonomia  — Spanish autonomous community dict (datos.gob.es, no network)
  3. eu_continent     — continent name dict (EU authority, no network)
  4. eu_country       — ISO 3166-1 alpha-3 dict (EU authority, no network)
  5. eu_country       — ISO 3166-1 alpha-2 dict (EU authority, no network)
  6. eu_country       — country name dict EN/ES (EU authority, no network)
  7. SPARQL cache     — pre-warmed from EU Publications Office before the full scan
  8. EU SPARQL        — individual fallback for values not seen during sampling

Vocabulary names:
  datos_provincia  http://datos.gob.es/recurso/sector-publico/territorio/Provincia/…
  datos_autonomia  http://datos.gob.es/recurso/sector-publico/territorio/Autonomia/…
  eu_continent     http://publications.europa.eu/resource/authority/continent/{CODE}
  eu_country       http://publications.europa.eu/resource/authority/country/{ISO3}
  eu_atu           http://publications.europa.eu/resource/authority/atu/{CODE}
  eu_place         http://publications.europa.eu/resource/authority/place/{CODE}
"""

from __future__ import annotations

import re
from typing import Optional

from utils.spain_geo import try_provincia, try_autonomia

# ── Base URIs ─────────────────────────────────────────────────────────────────
_EU_CONTINENT_BASE = "http://publications.europa.eu/resource/authority/continent/"
_EU_COUNTRY_BASE   = "http://publications.europa.eu/resource/authority/country/"

# ── Continent map: normalised name → EU authority code ───────────────────────
_CONTINENT_MAP: dict[str, str] = {
    "africa": "AFRICA", "áfrica": "AFRICA",
    "america": "AMERICA", "américas": "AMERICA", "americas": "AMERICA",
    "north america": "AMERICA", "south america": "AMERICA",
    "latin america": "AMERICA", "central america": "AMERICA",
    "asia": "ASIA",
    "europe": "EUROPE", "europa": "EUROPE",
    "oceania": "OCEANIA", "oceanía": "OCEANIA",
    "antarctica": "ANTARCTICA", "antártida": "ANTARCTICA",
}

# ── ISO 3166-1 alpha-2 → alpha-3 (complete UN member list) ───────────────────
_A2_TO_A3: dict[str, str] = {
    "AF": "AFG", "AL": "ALB", "DZ": "DZA", "AD": "AND", "AO": "AGO",
    "AG": "ATG", "AR": "ARG", "AM": "ARM", "AU": "AUS", "AT": "AUT",
    "AZ": "AZE", "BS": "BHS", "BH": "BHR", "BD": "BGD", "BB": "BRB",
    "BY": "BLR", "BE": "BEL", "BZ": "BLZ", "BJ": "BEN", "BT": "BTN",
    "BO": "BOL", "BA": "BIH", "BW": "BWA", "BR": "BRA", "BN": "BRN",
    "BG": "BGR", "BF": "BFA", "BI": "BDI", "CV": "CPV", "KH": "KHM",
    "CM": "CMR", "CA": "CAN", "CF": "CAF", "TD": "TCD", "CL": "CHL",
    "CN": "CHN", "CO": "COL", "KM": "COM", "CG": "COG", "CD": "COD",
    "CR": "CRI", "HR": "HRV", "CU": "CUB", "CY": "CYP", "CZ": "CZE",
    "DK": "DNK", "DJ": "DJI", "DM": "DMA", "DO": "DOM", "EC": "ECU",
    "EG": "EGY", "SV": "SLV", "GQ": "GNQ", "ER": "ERI", "EE": "EST",
    "SZ": "SWZ", "ET": "ETH", "FJ": "FJI", "FI": "FIN", "FR": "FRA",
    "GA": "GAB", "GM": "GMB", "GE": "GEO", "DE": "DEU", "GH": "GHA",
    "GR": "GRC", "GD": "GRD", "GT": "GTM", "GN": "GIN", "GW": "GNB",
    "GY": "GUY", "HT": "HTI", "HN": "HND", "HU": "HUN", "IS": "ISL",
    "IN": "IND", "ID": "IDN", "IR": "IRN", "IQ": "IRQ", "IE": "IRL",
    "IL": "ISR", "IT": "ITA", "JM": "JAM", "JP": "JPN", "JO": "JOR",
    "KZ": "KAZ", "KE": "KEN", "KI": "KIR", "KP": "PRK", "KR": "KOR",
    "KW": "KWT", "KG": "KGZ", "LA": "LAO", "LV": "LVA", "LB": "LBN",
    "LS": "LSO", "LR": "LBR", "LY": "LBY", "LI": "LIE", "LT": "LTU",
    "LU": "LUX", "MG": "MDG", "MW": "MWI", "MY": "MYS", "MV": "MDV",
    "ML": "MLI", "MT": "MLT", "MH": "MHL", "MR": "MRT", "MU": "MUS",
    "MX": "MEX", "FM": "FSM", "MD": "MDA", "MC": "MCO", "MN": "MNG",
    "ME": "MNE", "MA": "MAR", "MZ": "MOZ", "MM": "MMR", "NA": "NAM",
    "NR": "NRU", "NP": "NPL", "NL": "NLD", "NZ": "NZL", "NI": "NIC",
    "NE": "NER", "NG": "NGA", "MK": "MKD", "NO": "NOR", "OM": "OMN",
    "PK": "PAK", "PW": "PLW", "PA": "PAN", "PG": "PNG", "PY": "PRY",
    "PE": "PER", "PH": "PHL", "PL": "POL", "PT": "PRT", "QA": "QAT",
    "RO": "ROU", "RU": "RUS", "RW": "RWA", "KN": "KNA", "LC": "LCA",
    "VC": "VCT", "WS": "WSM", "SM": "SMR", "ST": "STP", "SA": "SAU",
    "SN": "SEN", "RS": "SRB", "SC": "SYC", "SL": "SLE", "SG": "SGP",
    "SK": "SVK", "SI": "SVN", "SB": "SLB", "SO": "SOM", "ZA": "ZAF",
    "SS": "SSD", "ES": "ESP", "LK": "LKA", "SD": "SDN", "SR": "SUR",
    "SE": "SWE", "CH": "CHE", "SY": "SYR", "TW": "TWN", "TJ": "TJK",
    "TZ": "TZA", "TH": "THA", "TL": "TLS", "TG": "TGO", "TO": "TON",
    "TT": "TTO", "TN": "TUN", "TR": "TUR", "TM": "TKM", "TV": "TUV",
    "UG": "UGA", "UA": "UKR", "AE": "ARE", "GB": "GBR", "US": "USA",
    "UY": "URY", "UZ": "UZB", "VU": "VUT", "VE": "VEN", "VN": "VNM",
    "YE": "YEM", "ZM": "ZMB", "ZW": "ZWE", "XK": "XKX",
}

_VALID_A3: frozenset[str] = frozenset(_A2_TO_A3.values())

# ── Country name (normalised) → alpha-3 ──────────────────────────────────────
# English + Spanish common names
_NAME_TO_A3: dict[str, str] = {
    "afghanistan": "AFG", "afganistán": "AFG",
    "albania": "ALB",
    "algeria": "DZA", "argelia": "DZA",
    "andorra": "AND",
    "angola": "AGO",
    "argentina": "ARG",
    "armenia": "ARM",
    "australia": "AUS",
    "austria": "AUT",
    "azerbaijan": "AZE", "azerbaiyán": "AZE",
    "bahamas": "BHS",
    "bahrain": "BHR", "baréin": "BHR",
    "bangladesh": "BGD",
    "barbados": "BRB",
    "belarus": "BLR", "bielorrusia": "BLR",
    "belgium": "BEL", "bélgica": "BEL",
    "belize": "BLZ", "belice": "BLZ",
    "benin": "BEN", "benín": "BEN",
    "bhutan": "BTN", "bután": "BTN",
    "bolivia": "BOL",
    "bosnia and herzegovina": "BIH", "bosnia": "BIH",
    "botswana": "BWA",
    "brazil": "BRA", "brasil": "BRA",
    "brunei": "BRN",
    "bulgaria": "BGR",
    "burkina faso": "BFA",
    "burundi": "BDI",
    "cabo verde": "CPV", "cape verde": "CPV",
    "cambodia": "KHM", "camboya": "KHM",
    "cameroon": "CMR", "camerún": "CMR",
    "canada": "CAN", "canadá": "CAN",
    "central african republic": "CAF", "república centroafricana": "CAF",
    "chad": "TCD",
    "chile": "CHL",
    "china": "CHN",
    "colombia": "COL",
    "comoros": "COM", "comoras": "COM",
    "congo": "COG",
    "democratic republic of the congo": "COD", "república democrática del congo": "COD",
    "costa rica": "CRI",
    "croatia": "HRV", "croacia": "HRV",
    "cuba": "CUB",
    "cyprus": "CYP", "chipre": "CYP",
    "czechia": "CZE", "czech republic": "CZE", "república checa": "CZE",
    "denmark": "DNK", "dinamarca": "DNK",
    "djibouti": "DJI", "yibuti": "DJI",
    "dominica": "DMA",
    "dominican republic": "DOM", "república dominicana": "DOM",
    "ecuador": "ECU",
    "egypt": "EGY", "egipto": "EGY",
    "el salvador": "SLV",
    "equatorial guinea": "GNQ", "guinea ecuatorial": "GNQ",
    "eritrea": "ERI",
    "estonia": "EST",
    "eswatini": "SWZ", "swaziland": "SWZ",
    "ethiopia": "ETH", "etiopía": "ETH",
    "fiji": "FJI",
    "finland": "FIN", "finlandia": "FIN",
    "france": "FRA", "francia": "FRA",
    "gabon": "GAB", "gabón": "GAB",
    "gambia": "GMB",
    "georgia": "GEO",
    "germany": "DEU", "alemania": "DEU",
    "ghana": "GHA",
    "greece": "GRC", "grecia": "GRC",
    "grenada": "GRD", "granada": "GRD",
    "guatemala": "GTM",
    "guinea": "GIN",
    "guinea-bissau": "GNB",
    "guyana": "GUY",
    "haiti": "HTI", "haití": "HTI",
    "honduras": "HND",
    "hungary": "HUN", "hungría": "HUN",
    "iceland": "ISL", "islandia": "ISL",
    "india": "IND",
    "indonesia": "IDN",
    "iran": "IRN", "irán": "IRN",
    "iraq": "IRQ", "irak": "IRQ",
    "ireland": "IRL", "irlanda": "IRL",
    "israel": "ISR",
    "italy": "ITA", "italia": "ITA",
    "jamaica": "JAM",
    "japan": "JPN", "japón": "JPN",
    "jordan": "JOR", "jordania": "JOR",
    "kazakhstan": "KAZ", "kazajistán": "KAZ",
    "kenya": "KEN",
    "kiribati": "KIR",
    "north korea": "PRK", "corea del norte": "PRK",
    "south korea": "KOR", "corea del sur": "KOR",
    "kuwait": "KWT",
    "kyrgyzstan": "KGZ", "kirguistán": "KGZ",
    "laos": "LAO",
    "latvia": "LVA", "letonia": "LVA",
    "lebanon": "LBN", "líbano": "LBN",
    "lesotho": "LSO",
    "liberia": "LBR",
    "libya": "LBY", "libia": "LBY",
    "liechtenstein": "LIE",
    "lithuania": "LTU", "lituania": "LTU",
    "luxembourg": "LUX", "luxemburgo": "LUX",
    "madagascar": "MDG",
    "malawi": "MWI",
    "malaysia": "MYS", "malasia": "MYS",
    "maldives": "MDV", "maldivas": "MDV",
    "mali": "MLI", "malí": "MLI",
    "malta": "MLT",
    "marshall islands": "MHL", "islas marshall": "MHL",
    "mauritania": "MRT",
    "mauritius": "MUS", "mauricio": "MUS",
    "mexico": "MEX", "méxico": "MEX",
    "micronesia": "FSM",
    "moldova": "MDA",
    "monaco": "MCO", "mónaco": "MCO",
    "mongolia": "MNG",
    "montenegro": "MNE",
    "morocco": "MAR", "marruecos": "MAR",
    "mozambique": "MOZ",
    "myanmar": "MMR", "birmania": "MMR",
    "namibia": "NAM",
    "nauru": "NRU",
    "nepal": "NPL",
    "netherlands": "NLD", "países bajos": "NLD", "holanda": "NLD",
    "new zealand": "NZL", "nueva zelanda": "NZL",
    "nicaragua": "NIC",
    "niger": "NER", "níger": "NER",
    "nigeria": "NGA",
    "north macedonia": "MKD", "macedonia del norte": "MKD",
    "norway": "NOR", "noruega": "NOR",
    "oman": "OMN", "omán": "OMN",
    "pakistan": "PAK", "pakistán": "PAK",
    "palau": "PLW",
    "panama": "PAN", "panamá": "PAN",
    "papua new guinea": "PNG", "papúa nueva guinea": "PNG",
    "paraguay": "PRY",
    "peru": "PER", "perú": "PER",
    "philippines": "PHL", "filipinas": "PHL",
    "poland": "POL", "polonia": "POL",
    "portugal": "PRT",
    "qatar": "QAT",
    "romania": "ROU", "rumanía": "ROU",
    "russia": "RUS", "rusia": "RUS",
    "rwanda": "RWA",
    "saint kitts and nevis": "KNA",
    "saint lucia": "LCA", "santa lucía": "LCA",
    "saint vincent and the grenadines": "VCT",
    "samoa": "WSM",
    "san marino": "SMR",
    "sao tome and principe": "STP", "santo tomé y príncipe": "STP",
    "saudi arabia": "SAU", "arabia saudita": "SAU",
    "senegal": "SEN",
    "serbia": "SRB",
    "seychelles": "SYC",
    "sierra leone": "SLE",
    "singapore": "SGP", "singapur": "SGP",
    "slovakia": "SVK", "eslovaquia": "SVK",
    "slovenia": "SVN", "eslovenia": "SVN",
    "solomon islands": "SLB", "islas salomón": "SLB",
    "somalia": "SOM",
    "south africa": "ZAF", "sudáfrica": "ZAF",
    "south sudan": "SSD", "sudán del sur": "SSD",
    "spain": "ESP", "españa": "ESP",
    "sri lanka": "LKA",
    "sudan": "SDN", "sudán": "SDN",
    "suriname": "SUR", "surinam": "SUR",
    "sweden": "SWE", "suecia": "SWE",
    "switzerland": "CHE", "suiza": "CHE",
    "syria": "SYR", "siria": "SYR",
    "taiwan": "TWN",
    "tajikistan": "TJK", "tayikistán": "TJK",
    "tanzania": "TZA",
    "thailand": "THA", "tailandia": "THA",
    "timor-leste": "TLS", "timor oriental": "TLS",
    "togo": "TGO",
    "tonga": "TON",
    "trinidad and tobago": "TTO", "trinidad y tobago": "TTO",
    "tunisia": "TUN", "túnez": "TUN",
    "turkey": "TUR", "türkiye": "TUR", "turquía": "TUR",
    "turkmenistan": "TKM", "turkmenistán": "TKM",
    "tuvalu": "TUV",
    "uganda": "UGA",
    "ukraine": "UKR", "ucrania": "UKR",
    "united arab emirates": "ARE", "emiratos árabes unidos": "ARE",
    "united kingdom": "GBR", "reino unido": "GBR",
    "united states": "USA", "estados unidos": "USA",
    "uruguay": "URY",
    "uzbekistan": "UZB", "uzbekistán": "UZB",
    "vanuatu": "VUT",
    "venezuela": "VEN",
    "vietnam": "VNM", "viet nam": "VNM",
    "yemen": "YEM",
    "zambia": "ZMB",
    "zimbabwe": "ZWE", "zimbabue": "ZWE",
}

# ── Column name keywords that suggest geographic content ──────────────────────
_GEO_KEYWORDS: frozenset[str] = frozenset({
    # English
    "country", "nation", "city", "municipality", "town",
    "region", "province", "state", "district", "county",
    "continent", "location", "place", "geo", "territory",
    "address", "area",
    # Spanish
    "pais", "ciudad", "municipio", "region", "provincia",
    "estado", "continente", "lugar", "territorio", "localidad",
    "direccion",
    # French / German (common in EU open data)
    "pays", "ville", "land", "ort",
})

_SPLIT_RE = re.compile(r"[_\-\s]+")


def is_geo_column_by_name(col_name: str) -> bool:
    """Return True when the column name contains a geo keyword."""
    parts = set(_SPLIT_RE.split(col_name.lower()))
    if parts & _GEO_KEYWORDS:
        return True
    # Also substring-match the whole normalised name (catches "countrycode")
    normalised = col_name.lower()
    return any(kw in normalised for kw in _GEO_KEYWORDS)


def is_geo_column_by_values(samples: list[str], threshold: float = 0.3) -> bool:
    """Return True when ≥ threshold fraction of sample values resolve to a URI."""
    if not samples:
        return False
    hits = sum(1 for v in samples if resolve_value(v) is not None)
    return hits / len(samples) >= threshold


# ── SPARQL cache (populated by warm_sparql_cache before the full scan) ────────
# Maps raw string → (uri, vocabulary) | None
_sparql_cache: dict[str, Optional[tuple[str, str]]] = {}


def warm_sparql_cache(values: list[str]) -> None:
    """
    Batch-resolve *values* via EU SPARQL and store results in the module cache.
    Should be called once after column detection, before the full scan begins.

    Skips values already covered by any dict fast-path (Spanish territories,
    ISO codes, country names, continent names) — SPARQL is only called for
    genuinely unknown values (e.g. NUTS regions, cities outside Spain).
    """
    from utils.sparql_utils import resolve_batch
    to_resolve = [
        v for v in values
        if v not in _sparql_cache
        and not (
            try_provincia(v) or try_autonomia(v)
            or _try_continent(v) or _try_iso_a3(v) or _try_iso_a2(v) or _try_country_name(v)
        )
    ]
    if not to_resolve:
        return
    _sparql_cache.update(resolve_batch(to_resolve))


# ── Resolution pipeline ───────────────────────────────────────────────────────

def resolve_value(value: str) -> Optional[tuple[str, str]]:
    """
    Map *value* to a (uri, vocabulary_name) pair, or None if unresolved.

    Order:
      1. datos_provincia  — Spanish province dict (no network)
      2. datos_autonomia  — Spanish autonomous community dict (no network)
      3. EU dicts         — continent / ISO alpha-3 / alpha-2 / country name (no network)
      4. SPARQL cache     — pre-warmed before the full scan
      5. EU SPARQL        — individual fallback for cache misses (rare)
    """
    if not isinstance(value, str):
        return None
    v = value.strip()
    if not v:
        return None

    fast = (
        try_provincia(v)
        or try_autonomia(v)
        or _try_continent(v)
        or _try_iso_a3(v)
        or _try_iso_a2(v)
        or _try_country_name(v)
    )
    if fast:
        return fast

    if v in _sparql_cache:
        return _sparql_cache[v]

    # Cache miss: value was not seen during sampling — resolve individually.
    from utils.sparql_utils import resolve_batch
    result = resolve_batch([v], batch_size=1).get(v)
    _sparql_cache[v] = result
    return result


def _try_continent(value: str) -> Optional[tuple[str, str]]:
    code = _CONTINENT_MAP.get(value.lower())
    if code:
        return (_EU_CONTINENT_BASE + code, "eu_continent")
    return None


def _try_iso_a3(value: str) -> Optional[tuple[str, str]]:
    upper = value.upper()
    if len(upper) == 3 and upper.isalpha() and upper in _VALID_A3:
        return (_EU_COUNTRY_BASE + upper, "eu_country")
    return None


def _try_iso_a2(value: str) -> Optional[tuple[str, str]]:
    upper = value.upper()
    if len(upper) == 2 and upper.isalpha():
        a3 = _A2_TO_A3.get(upper)
        if a3:
            return (_EU_COUNTRY_BASE + a3, "eu_country")
    return None


def _try_country_name(value: str) -> Optional[tuple[str, str]]:
    a3 = _NAME_TO_A3.get(re.sub(r"\s+", " ", value.lower().strip()))
    if a3:
        return (_EU_COUNTRY_BASE + a3, "eu_country")
    return None
