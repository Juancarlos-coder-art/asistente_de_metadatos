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
from assistant.validate import validar_shacl
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


def save_embedded_shacl():
    """Escribe los SHACL embebidos a /shacl/ si no existen."""
    base = Path(__file__).resolve().parent / "shacl"
    base.mkdir(exist_ok=True)

    shacl_files = {
        "health_dcat_ap.shacl.ttl": SHACL_HEALTH_DCAT_AP,
        "provenance.shacl.ttl": SHACL_PROVENANCE,
        "quality.shacl.ttl": SHACL_QUALITY,
    }

    for filename, content in shacl_files.items():
        target = base / filename
        if not target.exists():
            target.write_text(content, encoding="utf-8")
            print(f"📄 SHACL generado: {target}")


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
    save_embedded_shacl()
    schema = HealthDCATAPSchema("health_dcat_ap.json")
    state = MetadataState("health_dcat_ap.json")
    
    # … resto de tu código original …