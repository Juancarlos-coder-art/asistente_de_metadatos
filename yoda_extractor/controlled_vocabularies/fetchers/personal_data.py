"""
Parse the local personal_data.rdf file and extract one entry per skos:Concept.

Does not make any network requests — reads the bundled RDF file directly.

Output shape per entry:
  {
    "uri": "https://w3id.org/dpv/pd#Accent",
    "prefLabel": "Accent",
    "definition": "Information about linguistic and speech accents"
  }
"""

import json
from pathlib import Path
from defusedxml import ElementTree as ET

_HERE    = Path(__file__).parent.parent          # controlled_vocabularies/
RDF_FILE = _HERE / "personal_data.rdf"
OUT_FILE = _HERE / "vocabs" / "personal_data.json"

NS = {
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}

CONCEPT_TYPE = "http://www.w3.org/2004/02/skos/core#Concept"


def _en(element: "xml.etree.ElementTree.Element", tag: str) -> str:
    for child in element.findall(f"skos:{tag}", NS):
        lang = child.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if lang == "en" and child.text:
            return child.text.strip()
    return ""


def extract(rdf_file: Path = RDF_FILE, out_file: Path = OUT_FILE) -> None:
    tree = ET.parse(rdf_file)
    root = tree.getroot()

    vocab: dict[str, dict] = {}

    for desc in root.findall("rdf:Description", NS):
        uri = desc.get(f"{{{NS['rdf']}}}about", "")
        if not uri or "#" not in uri:
            continue

        is_concept = any(
            rtype.get(f"{{{NS['rdf']}}}resource") == CONCEPT_TYPE
            for rtype in desc.findall("rdf:type", NS)
        )
        if not is_concept:
            continue

        code = uri.split("#")[-1]
        label = _en(desc, "prefLabel")
        definition = _en(desc, "definition")

        if not label:
            continue

        entry: dict = {"uri": uri, "prefLabel": label}
        if definition:
            entry["definition"] = definition

        vocab[code] = entry

    vocab = dict(sorted(vocab.items()))

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(vocab, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved {len(vocab)} entries → {out_file.name}")
