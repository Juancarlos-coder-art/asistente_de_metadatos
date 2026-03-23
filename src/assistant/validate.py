# assistant/validate.py
from pyshacl import validate
from rdflib import Graph
import os

def ejecutar_validacion_shacl(ttl_path, shape_path):
    """
    Valida un RDF (TTL) contra un SHACL LOCAL usando pySHACL.
    """

    data_graph = Graph()
    shape_graph = Graph()

    # Cargar RDF y SHACL
    data_graph.parse(ttl_path, format="turtle")
    shape_graph.parse(shape_path, format="turtle")

    # Validación SHACL
    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shape_graph,
        advanced=True,
        allow_warnings=True
    )

    return {
        "shape": os.path.basename(shape_path),
        "conforms": conforms,
        "report": report_text
    }