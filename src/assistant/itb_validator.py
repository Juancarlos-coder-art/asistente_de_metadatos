import requests

ITB_ENDPOINT = "https://www.itb.ec.europa.eu/shacl/dcat-ap/upload"

def validate_via_itb(ttl_path, validation_type="dcatap.2_1_1_full"):
    """
    Valida RDF usando el motor oficial ITB de la Comisión Europea.
    validation_type puede ser:
    - dcatap.2_1_1_full (estable)
    - dcatap.3_0_1_full (última versión)
    """
    files = {
        "file": ("dataset.ttl", open(ttl_path, "rb"), "text/turtle")
    }

    data = {
        "domain": "semic-shacl",
        "validationType": validation_type
    }

    resp = requests.post(ITB_ENDPOINT, files=files, data=data)

    if resp.status_code != 200:
        raise Exception(f"Error ITB: {resp.status_code}\n{resp.text}")

    return resp.json()