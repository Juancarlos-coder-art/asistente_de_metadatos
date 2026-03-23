from pyshacl import validate
from rdflib import Graph

data_graph = Graph().parse("mi_rdf.ttl", format="turtle")
shape_graph = Graph().parse("mi_shape.ttl", format="turtle")

conforms, report_graph, report_text = validate(
    data_graph,
    shacl_graph=shape_graph,
    advanced=True,
    allow_warnings=True
)

print("¿Conforme?:", conforms)
print("Informe:")
print(report_text)