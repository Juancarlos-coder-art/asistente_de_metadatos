"""
Fetch a vocabulary by iterating over its RDF endpoint concept by concept.

Fetches the root RDF to discover concept URIs, then fetches each one individually
to extract English labels.

Label priority: skos:prefLabel[en] > skos:definition[en] > dct:description[en]

Output shape per entry:
  {
    "uri": "https://.../healthcategories/PHDR",
    "prefLabel": "Data from population-based health data registries...",
    "definition": "..."   (optional)
  }
"""

import json
import time
import defusedxml.ElementTree as ET
from pathlib import Path

import requests

_HERE = Path(__file__).parent.parent          # controlled_vocabularies/
_OUT  = _HERE / "vocabs"

_HEADERS = {
    "Accept": "application/rdf+xml",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

_NS = {
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dct":  "http://purl.org/dc/terms/",
}

_LABEL_TAGS = {
    f"{{{_NS['skos']}}}prefLabel":  "prefLabel",
    f"{{{_NS['skos']}}}definition": "definition",
    f"{{{_NS['dct']}}}description": "description",
}


def _fetch_rdf(url: str) -> "xml.etree.ElementTree.Element" | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        return ET.fromstring(r.content)
    except Exception as exc:
        print(f"  ERROR fetching {url}: {exc}")
        return None


def _concept_uris(root_element: "xml.etree.ElementTree.Element", base_url: str) -> list[str]:
    uris = []
    base = base_url.rstrip("/") + "/"
    for desc in root_element.findall(f"{{{_NS['rdf']}}}Description"):
        about = desc.get(f"{{{_NS['rdf']}}}about", "")
        if about.startswith(base) and "/" not in about[len(base):]:
            uris.append(about)
    return sorted(set(uris))


def _extract_english_fields(element: "xml.etree.ElementTree.Element") -> dict:
    fields: dict[str, list] = {}
    for tag, key in _LABEL_TAGS.items():
        for node in element.iter(tag):
            if node.get("{http://www.w3.org/XML/1998/namespace}lang") == "en":
                text = (node.text or "").strip()
                if text:
                    fields.setdefault(key, []).append(text)
    result = {}
    seen: set[str] = set()
    for k, values in fields.items():
        unique = [v for v in values if v not in seen]
        seen.update(unique)
        if unique:
            result[k] = unique[0] if len(unique) == 1 else unique
    return result


def _fetch_concept(uri: str) -> dict | None:
    root = _fetch_rdf(uri)
    if root is None:
        return None
    for desc in root.findall(f"{{{_NS['rdf']}}}Description"):
        if desc.get(f"{{{_NS['rdf']}}}about") == uri:
            fields = _extract_english_fields(desc)
            return {"uri": uri, **fields}
    return {"uri": uri}


def fetch_vocabulary(name: str, url: str, feature: str) -> None:
    url = url.strip()
    print(f"\n[{feature}] {name}")
    print(f"  Fetching root: {url}")

    root_el = _fetch_rdf(url)
    if root_el is None:
        return

    uris = _concept_uris(root_el, url)
    print(f"  Found {len(uris)} concepts")

    vocab: dict = {}
    for uri in uris:
        code = uri.rstrip("/").rsplit("/", 1)[-1]
        print(f"    {code} ...", end=" ", flush=True)
        entry = _fetch_concept(uri)
        if entry:
            vocab[code] = entry
            preview = (
                entry.get("prefLabel") or entry.get("definition")
                or entry.get("description") or "(no label)"
            )
            if isinstance(preview, list):
                preview = preview[0]
            print(preview[:60])
        else:
            print("SKIP")
        time.sleep(0.1)

    _OUT.mkdir(exist_ok=True)
    out_path = _OUT / f"{feature}.json"
    out_path.write_text(json.dumps(vocab, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved {len(vocab)} entries → {out_path.name}")
