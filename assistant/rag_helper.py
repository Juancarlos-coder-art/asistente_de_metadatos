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
    "legal_basis": {
        "label": "Base jurídica",
        "obligatorio": False,
        "descripcion": "Base jurídica que ampara el tratamiento de los datos.",
        "ejemplo": "Reglamento General de Protección de Datos (RGPD)",
        "bloque": "informacion_adicional"
    },
    "retention_period": {
        "label": "Periodo de conservación",
        "obligatorio": False,
        "descripcion": "Periodo durante el cual se conservarán los datos.",
        "ejemplo": "2020-01-01 a 2030-12-31",
        "bloque": "informacion_adicional"
    },
    "coding_system": {
        "label": "Sistema de codificación",
        "obligatorio": False,
        "descripcion": "Sistema de codificación utilizado en el dataset.",
        "ejemplo": "ICD-10, SNOMED CT",
        "bloque": "informacion_adicional"
    },
    "health_theme": {
        "label": "Tema de salud",
        "obligatorio": False,
        "descripcion": "Tema de salud específico del dataset.",
        "ejemplo": "Cáncer, Salud mental",
        "bloque": "informacion_adicional"
    },
    "code_values": {
        "label": "Valores codificados",
        "obligatorio": False,
        "descripcion": "Valores codificados utilizados en el dataset.",
        "ejemplo": "A00-B99, C00-D48",
        "bloque": "informacion_adicional"
    },
    "publisher": {
        "label": "Editor",
        "obligatorio": False,
        "descripcion": "Organización que publica el dataset, incluyendo tipo, contacto y horario.",
        "ejemplo": "Universidad de Valencia, tipo universidad, correo datos@uv.es",
        "bloque": "responsables_dataset"
    },
    "publisher_note": {
        "label": "Nota del editor",
        "obligatorio": False,
        "descripcion": "Notas adicionales del editor sobre el dataset.",
        "ejemplo": "Datos actualizados trimestralmente. Contactar para acceso especial.",
        "bloque": "responsables_dataset"
    },
    "creator": {
        "label": "Creador",
        "obligatorio": False,
        "descripcion": "Organización o persona que creó el dataset.",
        "ejemplo": "ISCIII, tipo autoridad nacional, correo isciii@gob.es",
        "bloque": "responsables_dataset"
    },
    "qualified_attribution": {
        "label": "Atribución cualificada",
        "obligatorio": False,
        "descripcion": "Agente con un rol específico respecto al dataset (autor, custodio, financiador, etc.).",
        "ejemplo": "Autor: Dr. García, Universidad de Valencia",
        "bloque": "responsables_dataset"
    },
    "was_generated_by": {
        "label": "Se generó por",
        "obligatorio": False,
        "descripcion": "Actividad sanitaria que generó los datos.",
        "ejemplo": "Ensayo clínico, registros hospitalarios",
        "bloque": "cobertura_temporalidad"
    },
    "spatial": {
        "label": "Cobertura geográfica",
        "obligatorio": False,
        "descripcion": "Países o territorios que cubre el dataset.",
        "ejemplo": "España, Francia",
        "bloque": "cobertura_temporalidad"
    },
    "temporal_coverage": {
        "label": "Cobertura temporal",
        "obligatorio": False,
        "descripcion": "Periodo temporal cubierto por el dataset.",
        "ejemplo": "2020-01-01 a 2023-12-31",
        "bloque": "cobertura_temporalidad"
    },
    "temporal_resolution": {
        "label": "Resolución temporal",
        "obligatorio": False,
        "descripcion": "Mínima resolución temporal de los datos.",
        "ejemplo": "P1D (diaria), PT1H (horaria)",
        "bloque": "cobertura_temporalidad"
    },
    "spatial_resolution_in_meters": {
        "label": "Resolución espacial (metros)",
        "obligatorio": False,
        "descripcion": "Resolución espacial del dataset en metros.",
        "ejemplo": "100",
        "bloque": "cobertura_temporalidad"
    },
    "frequency": {
        "label": "Frecuencia",
        "obligatorio": False,
        "descripcion": "Frecuencia de actualización del dataset.",
        "ejemplo": "Mensual, Anual",
        "bloque": "cobertura_temporalidad"
    },
    "issued": {
        "label": "Fecha de publicación",
        "obligatorio": False,
        "descripcion": "Fecha de publicación original del dataset.",
        "ejemplo": "2023-01-15",
        "bloque": "cobertura_temporalidad"
    },
    "modified": {
        "label": "Fecha de modificación",
        "obligatorio": False,
        "descripcion": "Fecha de última modificación del dataset.",
        "ejemplo": "2024-06-30",
        "bloque": "cobertura_temporalidad"
    },
    "alternate_identifier": {
        "label": "Identificador alternativo",
        "obligatorio": False,
        "descripcion": "Identificadores alternativos del dataset (DOI, URN, etc.).",
        "ejemplo": "DOI:10.1234/xyz",
        "bloque": "relaciones_versionado"
    },
    "conforms_to": {
        "label": "Se ajusta a",
        "obligatorio": False,
        "descripcion": "Estándar o especificación al que se ajusta el dataset.",
        "ejemplo": "DCAT-AP 2.1",
        "bloque": "relaciones_versionado"
    },
    "related_resource": {
        "label": "Recurso relacionado",
        "obligatorio": False,
        "descripcion": "Recurso relacionado con el dataset.",
        "ejemplo": "https://example.org/related-dataset",
        "bloque": "relaciones_versionado"
    },
    "is_referenced_by": {
        "label": "Está referenciado por",
        "obligatorio": False,
        "descripcion": "Recursos que referencian este dataset.",
        "ejemplo": "https://doi.org/10.1234/paper",
        "bloque": "relaciones_versionado"
    },
    "url": {
        "label": "Página de entrada",
        "obligatorio": False,
        "descripcion": "URL de la página de entrada (landing page) del dataset.",
        "ejemplo": "https://datos.gob.es/dataset/xyz",
        "bloque": "relaciones_versionado"
    },
    "documentation": {
        "label": "Documentación",
        "obligatorio": False,
        "descripcion": "Documentación asociada al dataset.",
        "ejemplo": "https://example.org/docs",
        "bloque": "relaciones_versionado"
    },
    "version": {
        "label": "Versión",
        "obligatorio": False,
        "descripcion": "Versión actual del dataset.",
        "ejemplo": "2.0",
        "bloque": "relaciones_versionado"
    },
    "has_version": {
        "label": "Tiene versión",
        "obligatorio": False,
        "descripcion": "Versiones disponibles del dataset.",
        "ejemplo": "1.0, 1.1, 2.0",
        "bloque": "relaciones_versionado"
    },
    "version_notes": {
        "label": "Notas de versión",
        "obligatorio": False,
        "descripcion": "Notas sobre la versión actual.",
        "ejemplo": "Corregidos errores de codificación en variables clínicas.",
        "bloque": "relaciones_versionado"
    },
}

FIELD_INDEX["hdab.name"] = {
    "label": "Nombre del organismo (HDAB)",
    "obligatorio": True,
    "descripcion": "Nombre del organismo que gestiona el acceso a los datos.",
    "ejemplo": "Ministerio de Sanidad",
    "bloque": "organismo_acceso_datos_sanitarios"
}
FIELD_INDEX["hdab.contact_page"] = {
    "label": "Página de contacto (HDAB)",
    "obligatorio": True,
    "descripcion": "URL de la página de contacto del organismo.",
    "ejemplo": "https://www.sanidad.gob.es/contacto",
    "bloque": "organismo_acceso_datos_sanitarios"
}
FIELD_INDEX["hdab.email"] = {
    "label": "Correo electrónico (HDAB)",
    "obligatorio": True,
    "descripcion": "Correo electrónico de contacto del organismo.",
    "ejemplo": "hdab@ministerio.es",
    "bloque": "organismo_acceso_datos_sanitarios"
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
            f"Eres un asistente de metadatos sanitarios HealthDCAT-AP.\n"
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
    missing = []
    for field_name in block.get("fields", []):
        if field_name == "applicable_legislation":
            continue
        val = state_data.get(field_name)
        
        # Para campos con subcampos obligatorios, verifica subcampos específicos
        if field_name == "hdab" and isinstance(val, dict):
            for subfield in ["name", "contact_page", "email"]:
                if not val.get(subfield):
                    missing.append(f"hdab.{subfield}")
            continue
            
        if val in (None, "", [], {}):
            missing.append(field_name)
    return missing