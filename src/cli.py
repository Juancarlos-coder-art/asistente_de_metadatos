#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI mejorado para la creación guiada de metadatos HealthDCAT-AP.
Incluye:
 - Preguntas asistidas manualmente por bloques
 - Autocompletado opcional con IA (si está disponible)
 - Validación SHACL (local)
 - MQA avanzado (EHDS) + SHACL + reporte consolidado
"""

import json
import os
from pathlib import Path

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available


# =====================================================================
# Utilidades
# =====================================================================

LIST_FIELDS = [
    "tag_string", "theme", "language", "documentation", "conforms_to",
    "is_referenced_by", "analytics", "alternate_identifier", "purpose",
    "population_coverage", "personal_data", "health_category", "health_theme",
    "legal_basis", "code_values", "coding_system", "applicable_legislation",
    "has_version"
]


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title):
    print("\n" + "=" * 60)
    print(f"🔷 {title}")
    print("=" * 60)


def ensure_ttl_path(msg="Ruta del archivo TTL: "):
    path = input(msg).strip()
    if not os.path.exists(path):
        print(f"❌ Error: el archivo no existe: {path}")
        return None
    return path


# =====================================================================
# Prompt y parsing
# =====================================================================

def build_contract(block):
    return {field: None for field in block["fields"]}


def build_prompt_for_block(schema, block, user_context=""):
    instrucciones = (
        "Devuelve SOLO JSON válido.\n"
        "• Listas como arrays.\n"
        "• No añadas claves no solicitadas.\n"
        "• No incluyas texto fuera del JSON.\n"
    )

    fields = ", ".join(block["fields"])
    prompt = (
        f"{block['question']}\n\n"
        f"Campos esperados: [{fields}]\n\n"
        f"{instrucciones}"
    )
    if user_context:
        prompt += f"\nContexto adicional del usuario: {user_context}"

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


# =====================================================================
# Lógica del asistente
# =====================================================================

def ask_block(schema, state, block):
    print_header(f"Bloque: {block['name']}")
    print(block["question"])

    use_ai = False
    if llm_available():
        choice = input("Pulsa Enter para responder manualmente, o escribe 'ia' para autocompletar: ").strip().lower()
        use_ai = (choice == "ia")

    partial = {}

    if use_ai:
        ctx = input("Añade contexto opcional (o Enter): ").strip()
        prompt = build_prompt_for_block(schema, block, ctx)
        contract = build_contract(block)

        ai_json = call_llm(prompt, contract, ctx) or {}

        for f in block["fields"]:
            partial[f] = ai_json.get(f)

    else:
        for f in block["fields"]:
            partial[f] = ask_field(schema, f)

    state.merge_partial(partial)

    print("\n✔️ Estado actualizado:")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))


# =====================================================================
# Validación SHACL
# =====================================================================

def validar_ttl(state):
    print_header("VALIDACIÓN SHACL LOCAL (pySHACL)")

    ttl_path = ensure_ttl_path("Introduce la ruta del archivo TTL: ")
    if ttl_path is None:
        return

    resultado = state.validar_shacl(ttl_path)
    print("\n📄 Resultado SHACL:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


# =====================================================================
# Menú principal
# =====================================================================

if __name__ == "__main__":
    clear()
    print_header("ASISTENTE DE METADATOS HealthDCAT‑AP / EHDS")

    print("Opciones disponibles:\n")
    print("  1️⃣  Ejecutar asistente completo (preguntas + JSON + TTL)")
    print("  2️⃣  Validar un TTL con SHACL (local)")
    print("  3️⃣  Validar calidad (MQA EHDS + SHACL)")
    print("4. Validar calidad y generar informe HTML")
    print("  0️⃣  Salir\n")

    opt = input("Selecciona opción: ").strip()

    # ------------------------------------------------------------
    # Opción 2: Validación SHACL directa
    # ------------------------------------------------------------
    if opt == "2":
        state = MetadataState("health_dcat_ap.json")
        validar_ttl(state)
        exit()

    # ------------------------------------------------------------
    # Opción 3: MQA + SHACL
    # ------------------------------------------------------------
    elif opt == "3":
        print_header("VALIDACIÓN COMPLETA (MQA + SHACL)")

        ttl_path = ensure_ttl_path("Ruta del TTL: ")
        if ttl_path is None:
            exit()

        from validador.quality_validator import QualityValidator
        from validador.report_builder import build_report

        print("\n🔎 Ejecutando MQA...")
        qv = QualityValidator(ttl_path)
        score, mqa_results = qv.run()

        state = MetadataState("health_dcat_ap.json")

        print("\n🔎 Ejecutando SHACL...")
        shacl_results = state.validar_shacl(ttl_path)

        report = build_report(score, mqa_results, shacl_results)

        print("\n📊 Informe completo MQA + SHACL:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        exit()
    elif opt == "4":
        print_header("VALIDACIÓN COMPLETA + INFORME HTML")

        ttl_path = ensure_ttl_path("Ruta del TTL: ")
        if ttl_path is None:
            exit()

        from validador.quality_validator import QualityValidator
        from validador.report_builder import build_report
        from validador.report_html import generate_html_report

        print("\n🔎 Ejecutando MQA (EHDS)...")
        qv = QualityValidator(ttl_path)
        score, mqa_results = qv.run()

        print("\n🔎 Ejecutando SHACL...")
        state = MetadataState("health_dcat_ap.json")
        shacl_results = state.validar_shacl(ttl_path)

        report = build_report(score, mqa_results, shacl_results)

        print("\n📝 Generando informe HTML...")
        html_path = generate_html_report(report)

        print(f"\n📄 Informe HTML generado en:\n   {html_path}\n")
        exit()


    # ------------------------------------------------------------
    # Opción 1: Asistente completo
    # ------------------------------------------------------------
    elif opt == "1":
        print_header("EJECUTANDO ASISTENTE COMPLETO HealthDCAT‑AP")

        schema = HealthDCATAPSchema("health_dcat_ap.json")
        state = MetadataState("health_dcat_ap.json")

        # Bloques definidos en tu CLI original — aquí no los cambio
        from bloques_definidos import BLOQUES  # <=== RECOMENDACIÓN: mover los bloques a un archivo

        for block in BLOQUES:
            ask_block(schema, state, block)

        # Guardar JSON
        save_path = "metadata_output.json"
        print("\n💾 Guardando JSON del dataset...")
        root = Path(__file__).resolve().parent
        out_dir = root / "datasets"
        out_dir.mkdir(exist_ok=True)
        json_path = out_dir / save_path
        json_path.write_text(json.dumps(state.data, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"📄 JSON guardado en: {json_path}")

        # Generar TTL
        ttl_path = out_dir / "metadata_output.ttl"
        print("🔄 Exportando a TTL...")
        state.export_to_rdf(str(ttl_path))

        print(f"📄 TTL generado en: {ttl_path}")
        print("\n🎉 Proceso completado\n")
        exit()

    # ------------------------------------------------------------
    # Opción 0 o cualquier otra
    # ------------------------------------------------------------
    else:
        print("\n👋 Saliendo del asistente.")
        exit()
