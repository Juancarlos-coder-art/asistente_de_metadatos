from pyshacl import validate
from rdflib import Graph
import os

def validate_health_dcat_ap(ttl_path):
    """
    Valida extensiones Health‑DCAT‑AP usando SHACL local.
    """

    data_graph = Graph()
    data_graph.parse(ttl_path)

    # Cargar SHACL de Health
    shape_graph = Graph()
    shape_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "tools", "shacl-health", "health-dcat-ap.shacl.ttl"
    )
    shape_graph.parse(shape_path)

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shape_graph,
        inference="rdfs",
        allow_warnings=True,
        advanced=False
    )

    return {
        "conforms": conforms,
        "report": results_text
    }
