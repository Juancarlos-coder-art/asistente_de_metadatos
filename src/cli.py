#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI para la creación guiada de metadatos HealthDCAT-AP.
Incluye:
 - Preguntas manuales campo a campo
 - Autocompletado mediante IA
 - Validación básica de tipos
 - Carga automática de SHACL embebidos

Autor: Juan Carlos Alias Laguna
Repositorio: https://github.com/Juancarlos-coder-art/asistente_de_metadatos
"""

import json
import os
from pathlib import Path
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available

# ============================================================
# 1. SHACL embebidos directamente en el CLI
# ============================================================

SHACL_HEALTH_DCAT_AP = r"""
# Aquí pegas tu SHACL completo
# Por ejemplo el health-dcat-ap.shacl.ttl
"""

SHACL_PROVENANCE = r"""
# Aquí tu SHACL de procedencia
"""

SHACL_QUALITY = r"""
# Aquí tu SHACL de calidad, si existe
"""

# ============================================================
# 2. Definición de BLOQUES (tal como los tienes)
# ============================================================

# … aquí van tus BLOQUES exactamente como los enviaste …
# LOS HE OMITIDO POR ESPACIO, pero van igual.


# ============================================================
# 3. Utilidades: contratos, prompts, parseo, validación
# ============================================================

LIST_FIELDS = [
    "tag_string", "theme", "language",
    "documentation", "conforms_to", "is_referenced_by",
    "analytics", "alternate_identifier", "purpose",
    "population_coverage", "personal_data", "health_category",
    "health_theme", "legal_basis", "code_values",
    "coding_system", "applicable_legislation", "has_version"
]


def build_contract(block):
    return {field: None for field in block["fields"]}


def build_prompt_for_block(schema, block, user_context=""):
    instrucciones = (
        "Devuelve SOLO JSON válido. "
        "Listas como arrays. "
        "No añadas claves no solicitadas. "
        "No añadas texto fuera del JSON."
    )
    fields = ", ".join(block["fields"])
    prompt = (
        f"{block['question']}\n\n"
        f"Campos esperados: [{fields}]\n"
        f"{instrucciones}\n"
    )
    if user_context:
        prompt += f"\nContexto adicional: {user_context}"

    return prompt


def parse_input(field_name, raw_value):
    raw_value = raw_value.strip()
    if raw_value == "":
        return None

    if field_name in LIST_FIELDS:
        return [v.strip() for v in raw_value.split(",") if v.strip()]

    if field_name == "contact":
        result = []
        for bloque in raw_value.split(";"):
            partes = [p.strip() for p in bloque.split("|")]
            c = {
                "name": partes[0] if len(partes) > 0 else None,
                "email": partes[1] if len(partes) > 1 else None,
                "role": partes[2] if len(partes) > 2 else None,
            }
            result.append(c)
        return result

    return raw_value


def ask_field(schema, field_name):
    field = schema.get_field(field_name)
    print(f"\n📌 {field.get('label', field_name)}")
    if field.get("help_text"):
        print(f"ℹ️ {field['help_text']}")

    raw = input("Tu respuesta: ")
    return parse_input(field_name, raw)


# ============================================================
# 4. Lógica central: preguntar por bloque + IA opcional
# ============================================================

def ask_block(schema, state, block):
    print(f"\n=== 🧩 BLOQUE: {block['name']} ===")
    print(block["question"])

    use_ai = False
    if llm_available():
        choice = input("Pulsa Enter para responder, o escribe 'ia' para autocompletar: ").strip().lower()
        use_ai = (choice == "ia")

    partial = {}

    if use_ai:
        ctx = input("Añade contexto opcional (o Enter): ").strip()
        prompt = build_prompt_for_block(schema, block, ctx)
        contract = build_contract(block)
        ai_result = call_llm(prompt, contract, ctx) or {}

        for f in block["fields"]:
            partial[f] = ai_result.get(f)

    else:
        for f in block["fields"]:
            partial[f] = ask_field(schema, f)

    state.merge_partial(partial)

    print("\n✔️ Estado actualizado:")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))


# ============================================================
# 5. Guardado en /datasets
# ============================================================

def save_output(state, filename="metadata_output.json"):
    root = Path(__file__).resolve().parent
    out_dir = root / "datasets"
    out_dir.mkdir(exist_ok=True)

    target = out_dir / filename
    target.write_text(json.dumps(state.data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n💾 Archivo guardado en: {target}")

# ============================================================
# 6. Validar datasets
# ============================================================    

def validar_ttl_oficial(state):
    print("\n=== VALIDACIÓN SHACL OFICIAL (TTL) ===\n")
    ttl_path = input("Introduce la ruta al archivo TTL: ").strip()

    resultado = state.validar_shacl(ttl_path)

    print(json.dumps(resultado, indent=2, ensure_ascii=False))
# ============================================================
# 7. Programa principal
# ============================================================
if __name__ == "__main__":
    print("\n=== ASISTENTE HealthDCAT-AP ===\n")

    print("Opciones:")
    print("1. Ejecutar asistente completo (preguntas + validación JSON)")
    print("2. Validar un TTL usando SHACL oficial (API Comisión Europea)")
    opt = input("Selecciona opción: ").strip()

    if opt == "2":
        state = MetadataState("health_dcat_ap.json")
        validar_ttl_oficial(state)
        exit()

    elif opt == "3":
        state = MetadataState("health_dcat_ap.json")

        # Cargar JSON generado previamente
        json_path = Path(__file__).resolve().parent / "datasets" / "metadata_output.json"
        state.data = json.loads(json_path.read_text("utf-8"))

        # Exportar a TTL
        ttl_path = Path(__file__).resolve().parent / "datasets" / "metadata_output.ttl"
        state.export_to_rdf(str(ttl_path))
        print(f"Archivo TTL generado: {ttl_path}")
        exit()

    # si NO elige opción 2, ejecuta el asistente normal:
    # si NO elige opción 2 ni 3, ejecuta el asistente normal:

    schema = HealthDCATAPSchema("health_dcat_ap.json")
    state = MetadataState("health_dcat_ap.json")
    BLOQUES = [
        {
            "name": "identificacion_basica",
            "fields": [
                "title",
                "identifier",
                "notes",
                "uri",
                "version",
                "version_notes",
                "has_version"
            ],
            "question": "Indica el título del dataset, su identificador, descripción, URI si existe, versión actual, notas de versión y versiones relacionadas."
        },
        {
            "name": "palabras_clave_y_tipologia",
            "fields": [
                "tag_string",
                "theme",
                "dcat_type",
                "health_category",
                "health_theme",
                "code_values",
                "coding_system"
            ],
            "question": "Indica palabras clave, temática, tipo de dataset, categoría sanitaria, tema de salud y sistemas de codificación utilizados."
        },
        {
            "name": "responsables_dataset",
            "fields": [
                "publisher",
                "creator",
                "contact",
                "owner_org",
                "publisher_note",
                "publisher_type",
                "trusted_data_holder",
                "hdab"
            ],
            "question": "Indica quién publica el dataset, quién lo creó, puntos de contacto, tipo de publicador y si es un trusted data holder."
        },
        {
            "name": "documentacion_relacionada",
            "fields": [
                "homepage",
                "url",
                "documentation",
                "conforms_to",
                "is_referenced_by",
                "analytics"
            ],
            "question": "Indica la página principal, URL del dataset, documentación, estándares aplicados, recursos que lo referencian y herramientas analíticas."
        },
        {
            "name": "licencia_y_acceso",
            "fields": [
                "license_id",
                "access_rights",
                "applicable_legislation",
                "legal_basis"
            ],
            "question": "Indica la licencia del dataset, derechos de acceso, legislación aplicable y base legal del tratamiento de datos."
        },
        {
            "name": "fechas_y_ciclo_vida",
            "fields": [
                "issued",
                "modified",
                "frequency",
                "provenance",
                "provenance_activity"
            ],
            "question": "Indica fecha de publicación, última modificación, frecuencia de actualización y procedencia del dataset."
        },
        {
            "name": "cobertura_temporal_y_espacial",
            "fields": [
                "temporal_coverage",
                "temporal_resolution",
                "spatial_coverage",
                "spatial_resolution_in_meters"
            ],
            "question": "Indica periodo temporal cubierto, resolución temporal, cobertura geográfica y resolución espacial en metros."
        },
        {
            "name": "idioma_e_identificadores",
            "fields": [
                "language",
                "alternate_identifier"
            ],
            "question": "Indica el idioma del dataset y cualquier identificador alternativo (DOI, DataCite, etc.)."
        },
        {
            "name": "finalidad_y_contexto_sanitario",
            "fields": [
                "purpose",
                "population_coverage",
                "personal_data",
                "health_category",
                "health_theme"
            ],
            "question": "Indica la finalidad del dataset, cobertura poblacional, si contiene datos personales y categoría/tema sanitario."
        },
        {
            "name": "variables_demograficas",
            "fields": [
                "min_typical_age",
                "max_typical_age",
                "number_of_records",
                "number_of_unique_individuals"
            ],
            "question": "Indica edades mínima y máxima típicas, número total de registros e individuos únicos."
        },
        {
            "name": "relaciones_y_atribuciones",
            "fields": [
                "qualified_relation",
                "qualified_attribution"
            ],
            "question": "Indica relaciones con otros recursos y atribuciones formales."
        },
        {
            "name": "calidad_dataset",
            "fields": [
                "quality_annotation"
            ],
            "question": "Indica anotaciones de calidad, evidencias, certificaciones o mediciones del dataset."
        },
        {
            "name": "campos_especificos_salud",
            "fields": [
                "publisher_type",
                "publisher_note",
                "code_values",
                "coding_system"
            ],
            "question": "Indica tipo de publicador, notas del publicador y sistemas de codificación utilizados."
        },
        {
            "name": "recursos_dataset",
            "fields": [
                "url",
                "name",
                "description",
                "format",
                "mimetype",
                "compress_format",
                "package_format",
                "size",
                "hash",
                "hash_algorithm"
            ],
            "question": "Indica la URL del recurso, su nombre, descripción, formato, tipo MIME, compresión, empaquetado, tamaño y hash."
        },
        {
            "name": "derechos_recurso",
            "fields": [
                "rights",
                "availability",
                "status",
                "license"
            ],
            "question": "Indica los derechos, disponibilidad, estado y licencia del recurso."
        },
        {
            "name": "acceso_y_descarga_recurso",
            "fields": [
                "access_url",
                "download_url",
                "issued",
                "modified"
            ],
            "question": "Indica URLs de acceso y descarga, fecha de publicación y modificación del recurso."
        },
        {
            "name": "cobertura_idioma_conformidad_recurso",
            "fields": [
                "temporal_resolution",
                "spatial_resolution_in_meters",
                "language",
                "documentation",
                "conforms_to",
                "applicable_legislation",
                "uri"
            ],
            "question": "Indica resolución temporal y espacial, idioma, documentación, conformidad y legislación aplicable del recurso."
        },
        {
            "name": "servicios_acceso",
            "fields": [
                "access_services"
            ],
            "question": "Indica los servicios de acceso, incluyendo su URI, formato, endpoints, idiomas y legislación aplicable."
        }
    ]



    # Ejecutar todos los bloques del asistente
    for block in BLOQUES:
        ask_block(schema, state, block)

    # Guardar JSON final
    save_output(state)

    # Convertir a TTL automáticamente
    ttl_path = Path(__file__).resolve().parent / "datasets" / "metadata_output.ttl"
    state.export_to_rdf(str(ttl_path))

    print(f"\n🎉 Proceso completado")
    print(f"📄 JSON: datasets/metadata_output.json")
    print(f"📄 TTL:  {ttl_path}")