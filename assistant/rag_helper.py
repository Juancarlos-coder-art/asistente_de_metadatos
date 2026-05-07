# assistant/rag_helper.py
"""
RAG ligero basado en el documento Word guia_campos_ends.docx.
Indexa los campos en memoria y genera descripciones cortas
usando el LLM cuando un campo obligatorio está vacío.
"""

import json
import re

# ─────────────────────────────────────────────────────────────
# ÍNDICE ESTÁTICO extraído del Word (guia_campos_ends.docx)
# Si el Word cambia, actualiza este diccionario.
# ─────────────────────────────────────────────────────────────
FIELD_INDEX = {
    "title": {
        "label": "Título",
        "obligatorio": True,
        "descripcion": "Nombre descriptivo del dataset.",
        "ejemplo": "Casos de viruela del mono en España 2023",
        "bloque": "identificacion_basica"
    },
    "name": {
        "label": "URL",
        "obligatorio": False,
        "descripcion": "Identificador URL del dataset. Se genera automáticamente a partir del título.",
        "ejemplo": "casos-viruela-mono-espana-2023",
        "bloque": "identificacion_basica"
    },
    "notes": {
        "label": "Descripción",
        "obligatorio": True,
        "descripcion": "Descripción detallada del contenido, alcance y propósito del dataset.",
        "ejemplo": "Dataset con registros de casos confirmados de viruela del mono notificados en España durante 2023, incluyendo distribución geográfica y datos demográficos.",
        "bloque": "identificacion_basica"
    },
    "identifier": {
        "label": "Identificador",
        "obligatorio": True,
        "descripcion": "Identificador único del dataset, preferiblemente un DOI.",
        "ejemplo": "https://doi.org/10.5281/zenodo.123456",
        "bloque": "identificacion_basica"
    },
    "access_rights": {
        "label": "Derechos de acceso",
        "obligatorio": True,
        "descripcion": "Nivel de acceso al dataset según vocabulario europeo.",
        "ejemplo": "Restringido (solo investigadores acreditados), Público, No Público (los datos no salen de la organización)",
        "bloque": "acceso_y_derechos"
    },
    "hdab": {
        "label": "Organismo de acceso (HDAB)",
        "obligatorio": True,
        "descripcion": "Organismo que gestiona el acceso a los datos sanitarios. Incluye nombre, tipo, email, teléfono y página web.",
        "ejemplo": "CSIC · Instituto de investigación · 639 99 15 67",
        "bloque": "organismo_acceso_datos_sanitarios"
    },
    "applicable_legislation": {
        "label": "Legislación aplicable",
        "obligatorio": False,
        "descripcion": "Se rellena automáticamente con GDPR al finalizar. No es necesario introducirlo.",
        "ejemplo": "GDPR – http://data.europa.eu/eli/reg/2016/679/oj",
        "bloque": "automatico"
    },
}

# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: descripción rápida de un campo faltante
# ─────────────────────────────────────────────────────────────

def describe_missing_field(field_name: str, use_llm: bool = False, call_llm_fn=None) -> dict:
    """
    Devuelve descripción corta, ejemplo y si es obligatorio para un campo.
    Si use_llm=True y call_llm_fn está disponible, enriquece la descripción con IA.
    """
    # Buscar en el índice (búsqueda exacta primero, luego parcial)
    entry = FIELD_INDEX.get(field_name)

    # Búsqueda parcial si no hay match exacto (ej: "hdab.name" → "hdab")
    if not entry:
        for key in FIELD_INDEX:
            if field_name.startswith(key) or key.startswith(field_name):
                entry = FIELD_INDEX[key]
                break

    if not entry:
        return {
            "label": field_name,
            "obligatorio": False,
            "descripcion": "Campo no documentado en la guía.",
            "ejemplo": "",
            "sugerencia": ""
        }

    result = {
        "label": entry["label"],
        "obligatorio": entry["obligatorio"],
        "descripcion": entry["descripcion"],
        "ejemplo": entry["ejemplo"],
        "sugerencia": ""
    }

    # Enriquecer con LLM si está disponible
    if use_llm and call_llm_fn:
        context = (
            f"Campo: {field_name}\n"
            f"Etiqueta: {entry['label']}\n"
            f"Descripción: {entry['descripcion']}\n"
            f"Ejemplo: {entry['ejemplo']}\n"
        )
        prompt = (
            f"Eres un asistente de metadatos sanitarios HealthDCAT-AP-ES.\n"
            f"El usuario no ha rellenado el campo '{entry['label']}'.\n"
            f"Con esta información del campo:\n{context}\n"
            f"Escribe UNA sola frase corta (máx 25 palabras) en español que ayude "
            f"al usuario a entender qué debe escribir. Sé concreto y amigable. "
            f"Devuelve SOLO el texto de la sugerencia, sin JSON ni formato extra."
        )
        try:
            raw = call_llm_fn(prompt, {}, "")
            if isinstance(raw, dict):
                sugerencia = " ".join(str(v) for v in raw.values() if v)
            else:
                sugerencia = str(raw)
            result["sugerencia"] = sugerencia[:200].strip()
        except Exception:
            result["sugerencia"] = f"Indica {entry['label'].lower()} de tu dataset."

    return result


def get_missing_descriptions(missing_fields: list, use_llm: bool = False, call_llm_fn=None) -> list:
    """
    Dado una lista de field_names faltantes, devuelve lista de dicts con descripción.
    """
    return [
        {"field": f, **describe_missing_field(f, use_llm=use_llm, call_llm_fn=call_llm_fn)}
        for f in missing_fields
        if f != "applicable_legislation"  # este es automático, no avisar
    ]


def get_block_missing(block: dict, state_data: dict) -> list:
    """
    Devuelve los campos del bloque actual que están vacíos.
    """
    missing = []
    for field_name in block.get("fields", []):
        if field_name == "applicable_legislation":
            continue
        val = state_data.get(field_name)
        if val in (None, "", [], {}):
            missing.append(field_name)
    return missing