"""
Static dictionaries for Spanish territory linked-data URIs.

Source: https://datos.gob.es/es/recurso/sector-publico/territorio
URIs verified via the datos.gob.es SPARQL endpoint.

Lookup functions normalise input (lowercase + strip diacritics) so both
accented ("Cádiz") and plain ("Cadiz") spellings match the same entry.

Resolution order (enforced by geo_utils):
  1. Provincia  (more specific)
  2. Comunidad Autónoma
"""

from __future__ import annotations

import unicodedata
from typing import Optional

_PROVINCIA_BASE = "http://datos.gob.es/recurso/sector-publico/territorio/Provincia/"
_AUTONOMIA_BASE = "http://datos.gob.es/recurso/sector-publico/territorio/Autonomia/"


def _norm(s: str) -> str:
    """Lowercase and strip diacritics  →  'Cádiz' becomes 'cadiz'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


# ── Provincias ────────────────────────────────────────────────────────────────
# key: normalised label (accent-free, lowercase)
# value: URI slug  (appended to _PROVINCIA_BASE)

_PROVINCIA_SLUG: dict[str, str] = {
    # A Coruña
    "a coruna":                  "A-Coruna",
    "coruna":                    "A-Coruna",
    "la coruna":                 "A-Coruna",
    # Albacete
    "albacete":                  "Albacete",
    # Alicante / Alacant
    "alicante":                  "Alicante",
    "alacant":                   "Alicante",
    # Almería
    "almeria":                   "Almeria",
    # Asturias
    "asturias":                  "Asturias",
    # Badajoz
    "badajoz":                   "Badajoz",
    # Barcelona
    "barcelona":                 "Barcelona",
    # Burgos
    "burgos":                    "Burgos",
    # Cantabria
    "cantabria":                 "Cantabria",
    # Castellón / Castelló
    "castellon":                 "Castellon",
    "castello":                  "Castellon",
    "castellon de la plana":     "Castellon",
    # Ceuta
    "ceuta":                     "Ceuta",
    # Ciudad Real
    "ciudad real":               "Ciudad-Real",
    # Cuenca
    "cuenca":                    "Cuenca",
    # Cáceres
    "caceres":                   "Caceres",
    # Cádiz
    "cadiz":                     "Cadiz",
    # Córdoba
    "cordoba":                   "Cordoba",
    # Girona / Gerona
    "girona":                    "Girona",
    "gerona":                    "Girona",
    # Granada
    "granada":                   "Granada",
    # Guadalajara
    "guadalajara":               "Guadalajara",
    # Guipúzcoa / Gipuzkoa
    "guipuzcoa":                 "Guipuzcoa",
    "gipuzkoa":                  "Guipuzcoa",
    # Huelva
    "huelva":                    "Huelva",
    # Huesca
    "huesca":                    "Huesca",
    # Illes Balears
    "illes balears":             "Illes-Balears",
    "baleares":                  "Illes-Balears",
    "islas baleares":            "Illes-Balears",
    # Jaén
    "jaen":                      "Jaen",
    # La Rioja
    "la rioja":                  "La-Rioja",
    "rioja":                     "La-Rioja",
    # Las Palmas
    "las palmas":                "Las-Palmas",
    "las palmas de gran canaria": "Las-Palmas",
    # León
    "leon":                      "Leon",
    # Lleida / Lérida
    "lleida":                    "Lleida",
    "lerida":                    "Lleida",
    # Lugo
    "lugo":                      "Lugo",
    # Madrid
    "madrid":                    "Madrid",
    # Melilla
    "melilla":                   "Melilla",
    # Murcia
    "murcia":                    "Murcia",
    # Málaga
    "malaga":                    "Malaga",
    # Navarra
    "navarra":                   "Navarra",
    "navarre":                   "Navarra",
    # Ourense / Orense
    "ourense":                   "Ourense",
    "orense":                    "Ourense",
    # Palencia
    "palencia":                  "Palencia",
    # Pontevedra
    "pontevedra":                "Pontevedra",
    # Salamanca
    "salamanca":                 "Salamanca",
    # Santa Cruz de Tenerife
    "santa cruz de tenerife":    "Santa-Cruz-Tenerife",
    "tenerife":                  "Santa-Cruz-Tenerife",
    "santa cruz tenerife":       "Santa-Cruz-Tenerife",
    # Segovia
    "segovia":                   "Segovia",
    # Sevilla
    "sevilla":                   "Sevilla",
    "seville":                   "Sevilla",
    # Soria
    "soria":                     "Soria",
    # Tarragona
    "tarragona":                 "Tarragona",
    # Teruel
    "teruel":                    "Teruel",
    # Toledo
    "toledo":                    "Toledo",
    # Valencia / València
    "valencia":                  "Valencia",
    # Valladolid
    "valladolid":                "Valladolid",
    # Vizcaya / Bizkaia
    "vizcaya":                   "Vizcaya",
    "bizkaia":                   "Vizcaya",
    # Zamora
    "zamora":                    "Zamora",
    # Zaragoza
    "zaragoza":                  "Zaragoza",
    # Álava / Araba
    "alava":                     "Alava",
    "araba":                     "Alava",
    # Ávila
    "avila":                     "Avila",
}

# ── Comunidades Autónomas ─────────────────────────────────────────────────────

_AUTONOMIA_SLUG: dict[str, str] = {
    # Andalucía
    "andalucia":                         "Andalucia",
    "andalusia":                         "Andalucia",
    # Aragón
    "aragon":                            "Aragon",
    # Principado de Asturias
    "principado de asturias":            "Principado-Asturias",
    "asturias":                          "Principado-Asturias",
    # Illes Balears
    "illes balears":                     "Illes-Balears",
    "baleares":                          "Illes-Balears",
    "islas baleares":                    "Illes-Balears",
    # Canarias
    "canarias":                          "Canarias",
    "islas canarias":                    "Canarias",
    "canary islands":                    "Canarias",
    # Cantabria
    "cantabria":                         "Cantabria",
    # Castilla y León
    "castilla y leon":                   "Castilla-Leon",
    "castilla leon":                     "Castilla-Leon",
    # Castilla-La Mancha
    "castilla-la mancha":                "Castilla-La-Mancha",
    "castilla la mancha":                "Castilla-La-Mancha",
    # Cataluña
    "cataluna":                          "Cataluna",
    "catalonia":                         "Cataluna",
    "catalunya":                         "Cataluna",
    # Comunitat Valenciana
    "comunitat valenciana":              "Comunitat-Valenciana",
    "comunidad valenciana":              "Comunitat-Valenciana",
    "pais valenciano":                   "Comunitat-Valenciana",
    "valencian community":               "Comunitat-Valenciana",
    # Extremadura
    "extremadura":                       "Extremadura",
    # Galicia
    "galicia":                           "Galicia",
    # Comunidad de Madrid
    "comunidad de madrid":               "Comunidad-Madrid",
    "comunidad madrid":                  "Comunidad-Madrid",
    # Región de Murcia
    "region de murcia":                  "Region-Murcia",
    "region murcia":                     "Region-Murcia",
    # C. Foral de Navarra
    "comunidad foral de navarra":        "Comunidad-Foral-Navarra",
    "comunidad foral navarra":           "Comunidad-Foral-Navarra",
    "c foral de navarra":                "Comunidad-Foral-Navarra",
    "navarra":                           "Comunidad-Foral-Navarra",
    "navarre":                           "Comunidad-Foral-Navarra",
    # País Vasco
    "pais vasco":                        "Pais-Vasco",
    "euskadi":                           "Pais-Vasco",
    "euskal herria":                     "Pais-Vasco",
    "basque country":                    "Pais-Vasco",
    # La Rioja
    "la rioja":                          "La-Rioja",
    "rioja":                             "La-Rioja",
    # Ceuta
    "ceuta":                             "Ceuta",
    # Melilla
    "melilla":                           "Melilla",
}

# ── Public lookup functions ───────────────────────────────────────────────────

def try_provincia(value: str) -> Optional[tuple[str, str]]:
    """Return (uri, 'datos_provincia') if *value* matches a Spanish province."""
    slug = _PROVINCIA_SLUG.get(_norm(value.strip()))
    if slug:
        return (_PROVINCIA_BASE + slug, "datos_provincia")
    return None


def try_autonomia(value: str) -> Optional[tuple[str, str]]:
    """Return (uri, 'datos_autonomia') if *value* matches a Spanish autonomous community."""
    slug = _AUTONOMIA_SLUG.get(_norm(value.strip()))
    if slug:
        return (_AUTONOMIA_BASE + slug, "datos_autonomia")
    return None
