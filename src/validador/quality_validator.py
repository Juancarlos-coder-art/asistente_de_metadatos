from rdflib import Graph, Namespace
from validador.yoda_metrics import metrics

# ------------------------------------------------------------
# Prefijos estándar DCAT + HealthDCAT-AP + EHDS + DQV + PROV
# ------------------------------------------------------------

DCAT   = Namespace("http://www.w3.org/ns/dcat#")
DCT    = Namespace("http://purl.org/dc/terms/")
HDCAT  = Namespace("http://data.europa.eu/88u/health-dcat-ap#")
HPROV  = Namespace("http://data.europa.eu/88u/health-provenance#")
EHDS   = Namespace("http://data.europa.eu/88u/ehds#")
DQV    = Namespace("http://www.w3.org/ns/dqv#")
PROV   = Namespace("http://www.w3.org/ns/prov#")
SPDX   = Namespace("http://spdx.org/rdf/terms#")  # Para checksums

PREFIX_MAP = {
    "dcat": DCAT,
    "dct": DCT,
    "hcat": HDCAT,
    "h-dcat": HDCAT,
    "hprov": HPROV,
    "ehds": EHDS,
    "dqv": DQV,
    "prov": PROV,
    "spdx": SPDX,
}

# ------------------------------------------------------------
# QualityValidator para Health-DCAT-AP (Nivel 3 – EHDS)
# ------------------------------------------------------------

class QualityValidator:

    def __init__(self, ttl_path):
        print(">>> EJECUTANDO QualityValidator HealthDCAT-AP (EHDS) <<<")
        self.ttl_path = ttl_path
        self.graph = Graph()
        self.graph.parse(ttl_path)

    # --------------------------------------------------------
    # Verifica una o múltiples propiedades
    # --------------------------------------------------------
    def check_metric(self, metric_uri):

        # Si la métrica es SHACL → se informa desde fuera
        if isinstance(metric_uri, str) and metric_uri.upper() == "SHACL":
            return False  # SHACL lo gestiona state.validar_shacl

        # Normalizar a lista
        if isinstance(metric_uri, str):
            metric_uri = [metric_uri]

        for item in metric_uri:
            if ":" not in item:
                continue

            prefix, prop = item.split(":")

            ns = PREFIX_MAP.get(prefix)
            if ns is None:
                continue

            # Si existe al menos un triple con esa propiedad → OK
            if any(self.graph.triples((None, ns[prop], None))):
                return True

        return False

    # --------------------------------------------------------
    # Recorre todas las métricas y las evalúa
    # --------------------------------------------------------
    def run(self):
        score = 0
        results = []

        for m in metrics:
            metric_id = m.get("metric")
            if metric_id is None:
                continue

            ok = self.check_metric(metric_id)

            if ok:
                score += m.get("weight", 0)

            results.append({
                "metric": metric_id,
                "indicator": m.get("indicator"),
                "dimension": m.get("dimension"),
                "passed": ok,
                "weight": m.get("weight", 0)
            })

        return score, results