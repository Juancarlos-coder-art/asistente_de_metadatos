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
        "obligatorio": True,
        "descripcion": "Se rellena automáticamente con GDPR al finalizar. No es necesario introducirlo.",
        "ejemplo": "GDPR – http://data.europa.eu/eli/reg/2016/679/oj",
        "bloque": "automatico"
    },
    "health_category": {
    "label": "Categoría sanitaria",
    "obligatorio": True,
    "descripcion": "Categoría sanitaria del dataset según el vocabulario EHDS.",
    "ejemplo": "Registros Electrónicos de Salud, Datos de ensayos clínicos...",
    "bloque": "identificacion_basica"
    },
    "theme": {
        "label": "Tema",
        "obligatorio": True,
        "descripcion": "Tema principal del dataset según el vocabulario europeo de temas.",
        "ejemplo": "Salud, Ciencia y tecnología...",
        "bloque": "identificacion_basica"
    },
    "dcat_type": {
        "label": "Tipo de dataset",
        "obligatorio": False,
        "descripcion": "Tipo del dataset según la lista controlada de la Publications Office.",
        "ejemplo": "Datos estadísticos, Datos geoespaciales...",
        "bloque": "identificacion_basica"
    },
    "provenance": {
        "label": "Procedencia",
        "obligatorio": False,
        "descripcion": "Origen o procedencia de los datos del dataset.",
        "ejemplo": "Datos recogidos por el ISCIII mediante vigilancia epidemiológica activa.",
        "bloque": "identificacion_basica"
    },
    "keyword": {
        "label": "Palabras clave",
        "obligatorio": False,
        "descripcion": "Palabras clave que describen el contenido del dataset.",
        "ejemplo": "Mpox, epidemiología, España, 2023",
        "bloque": "identificacion_basica"
    },
    "contact": {
        "label": "Punto de contacto",
        "obligatorio": False,
        "descripcion": "Correo electrónico o URL de contacto para consultas sobre el dataset.",
        "ejemplo": "info@ministeriodesanidad.es",
        "bloque": "punto_de_contacto"
    },
    "access_url": {
    "label": "URL de acceso a la distribución",
    "obligatorio": True,
    "descripcion": "URL donde se puede acceder o descargar el dataset.",
    "ejemplo": "https://datos.gob.es/dataset/xyz",
    "bloque": "distribucion"
    },
    "purpose": {
        "label": "Finalidad",
        "obligatorio": False,
        "descripcion": "Finalidad o propósito del dataset.",
        "ejemplo": "Monitorear la evolución de la viruela del mono en España para informar políticas de salud pública.",
        "bloque": "informacion_adicional"
    },
    "language": {
        "label": "Idioma",
        "obligatorio": False,
        "descripcion": "Idioma en el que están disponibles los datos del dataset.",
        "ejemplo": "Español",
        "bloque": "informacion_adicional"
    },
    "population_coverage": {
        "label": "Cobertura poblacional",
        "obligatorio": False,
        "descripcion": "Descripción de la población cubierta por el dataset.",
        "ejemplo": "Población mayor de 18 años en España",
        "bloque": "informacion_adicional"
    },
    "number_of_unique_individuals": {
        "label": "Número de personas individuales",
        "obligatorio": False,
        "descripcion": "Número de individuos únicos representados en el dataset.",
        "ejemplo": "1500",
        "bloque": "informacion_adicional"
    },
    "number_of_records": {
        "label": "Número de registros",
        "obligatorio": False,
        "descripcion": "Número total de registros o filas en el dataset.",
        "ejemplo": "4500",
        "bloque": "informacion_adicional"
    },
    "min_typical_age": {
        "label": "Edad mínima típica",
        "obligatorio": False,
        "descripcion": "Edad mínima típica de los individuos representados en el dataset.",
        "ejemplo": "0",
        "bloque": "informacion_adicional"
    },
    "max_typical_age": {
        "label": "Edad máxima típica",
        "obligatorio": False,
        "descripcion": "Edad máxima típica de los individuos representados en el dataset.",
        "ejemplo": "99",
        "bloque": "informacion_adicional"
    },
    "personal_data": {
        "label": "Datos personales",
        "obligatorio": False,
        "descripcion": "Indica si el dataset contiene datos personales o información identificable.",
        "ejemplo": "Sí, el dataset incluye datos personales como edad, sexo y ubicación geográfica.",
        "bloque": "informacion_adicional"
    },
}

# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: descripción rápida de un campo faltante
# ─────────────────────────────────────────────────────────────

NON_PUBLIC_REQUIRED = {"dcat_type", "contact","provenance","keyword"}

def describe_missing_field(field_name: str, use_llm: bool = False, call_llm_fn=None, is_non_public: bool = False) -> dict:
    """
    Devuelve descripción corta, ejemplo y si es obligatorio para un campo.
    Si use_llm=True y call_llm_fn está disponible, enriquece la descripción con IA.
    """
    entry = FIELD_INDEX.get(field_name)

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

    # Si es NON_PUBLIC, algunos campos opcionales se vuelven obligatorios
    es_obligatorio = entry["obligatorio"] or (is_non_public and field_name in NON_PUBLIC_REQUIRED)

    result = {
        "label": entry["label"],
        "obligatorio": es_obligatorio,  # ← cambiado
        "descripcion": entry["descripcion"],
        "ejemplo": entry["ejemplo"],
        "sugerencia": ""
    }

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

def get_missing_descriptions(missing_fields: list, use_llm: bool = False, call_llm_fn=None, is_non_public: bool = False) -> list:
    return [
        {"field": f, **describe_missing_field(f, use_llm=use_llm, call_llm_fn=call_llm_fn, is_non_public=is_non_public)}
        for f in missing_fields
        if f != "applicable_legislation"
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