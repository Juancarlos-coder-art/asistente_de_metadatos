import json
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available

# URI predeterminada para datasets no públicos
ENDS_NON_PUBLIC_URI = "https://catalogo.ends.gob.es/dataset"
NON_PUBLIC_URI = "http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC"

BLOCKS = [
    {
        "name": "derechos_de_acceso",
        "fields": ["access_rights"],
        "question": (
            "¿Quién puede acceder a este dataset y bajo qué condiciones?\n\n"
            "Ejemplos:\n"
            "- 'Cualquiera puede descargarlo' → Público\n"
            "- 'Solo investigadores acreditados pueden solicitarlo' → Restringido\n"
            "- 'Es un dataset interno, no sale de nuestra organización' → No público\n"
        ),
        "hint": "Describe con tus palabras quién tiene acceso y bajo qué condiciones.",
        "placeholder": "Ej.: El acceso está restringido a investigadores acreditados por organismos públicos de salud..."
    },
    {
        "name": "identificacion_basica",
        "fields": ["title", "identifier", "notes", "health_category", "theme", "dcat_type", "provenance", "keyword"],
        "question": (
            "Proporciona una descripción general del dataset. Incluye el identificador si está disponible, "
            "la categoría sanitaria, el tema, el tipo de dataset, la procedencia de los datos y las palabras clave."
        ),
        "hint": "Dinos el nombre del dataset, de qué trata, su categoría sanitaria, tema, tipo y origen.",
        "placeholder": "Ej.: Dataset sobre casos de Mpox en España 2023. Es un registro epidemiológico del ISCIII, de acceso restringido, con datos de vigilancia de enfermedades infecciosas..."
    },
    {
        "name": "organismo_acceso_datos_sanitarios",
        "fields": ["hdab"],
        "question": (
            "Indica el organismo que gestiona el acceso a los datos sanitarios (HDAB). "
            "Por favor, proporciona el nombre del organismo y su tipo (por ejemplo: "
            "Instituto de salud pública, Universidad, Registro de salud pública, "
            "Autoridad nacional, etc.). "
            "Si dispones de ellos, incluye también el correo de contacto, "
            "el teléfono, la página web de contacto y el horario de disponibilidad."
        ),
        "hint": "Indícanos qué organismo es el responsable de dar acceso a estos datos y cómo contactarle.",
        "placeholder": "Ej.: El organismo es el ISCIII, su correo es datos.salud@isciii.es y su teléfono es +34 918 222 000..."
    },
    {
        "name": "punto_de_contacto",
        "fields": ["contact"],
        "question": (
            "¿Cuál es el punto de contacto para este dataset?\n\n"
            "Proporciona el correo electrónico y/o la URL de contacto para consultas sobre el dataset."
        ),
        "hint": "Indica el correo o web de contacto para consultas sobre este dataset.",
        "placeholder": "Ej.: Para consultas sobre este dataset contacta en info@ministeriodesanidad.es o visita https://www.sanidad.gob.es/contacto"
    }
]


def is_non_public(state_data: dict) -> bool:
    """Comprueba si el access_rights del estado es NON_PUBLIC."""
    ar = state_data.get("access_rights", "")
    if not ar:
        return False
    return "NON_PUBLIC" in str(ar).upper()


def build_contract(block: dict) -> dict:
    return {name: None for name in block["fields"]}


def build_prompt_for_block(schema: HealthDCATAPSchema, block: dict, user_context: str = "") -> str:
    fields = ", ".join(block["fields"])
    instrucciones = (
        "Devuelve SOLO JSON válido. Las listas como arrays JSON. "
        "REGLA MÁS IMPORTANTE: Si el usuario NO menciona explícitamente un campo, "
        "devuelve null para ese campo. NUNCA deduzcas, infieras ni inventes valores. "
        "Solo rellena un campo si el usuario ha proporcionado información DIRECTA sobre él. "
        "Si hay duda, devuelve null. "

        # ── access_rights ──
        "Para el campo 'access_rights', analiza la descripción y devuelve SOLO la URI:\n"
        "- Público → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
        "- Restringido → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
        "- No público → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        "IMPORTANTE: La diferencia clave entre RESTRINGIDO y NO PÚBLICO es:\n"
        "  - RESTRINGIDO = se puede acceder bajo ciertas condiciones o solicitud\n"
        "  - NO PÚBLICO = no está disponible para nadie fuera de la organización propietaria\n"

        # ── health_category ──
        "Para el campo 'health_category', devuelve un ARRAY con las URIs correspondientes:\n"
        "- Registros Electrónicos de Salud → http://13.81.34.152:1101/resource/authority/healthcategories/EHRS\n"
        "- Datos administrativos relacionados con la salud → http://13.81.34.152:1101/resource/authority/healthcategories/HRAD\n"
        "- Datos de registros médicos y de mortalidad → http://13.81.34.152:1101/resource/authority/healthcategories/MRMR\n"
        "- Datos de ensayos clínicos → http://13.81.34.152:1101/resource/authority/healthcategories/EHCT\n"
        "- Datos genómicos → http://13.81.34.152:1101/resource/authority/healthcategories/HGPD\n"
        "- Datos de registros de salud pública → http://13.81.34.152:1101/resource/authority/healthcategories/PHDR\n"
        "- Datos de cohortes e investigación → http://13.81.34.152:1101/resource/authority/healthcategories/RQSH\n"
        "- Datos de patógenos → http://13.81.34.152:1101/resource/authority/healthcategories/RPDG\n"

        # ── theme ──
        "Para el campo 'theme', devuelve un ARRAY con las URIs del vocabulario europeo de temas:\n"
        "- Salud → http://publications.europa.eu/resource/authority/data-theme/HEAL\n"
        "- Ciencia y tecnología → http://publications.europa.eu/resource/authority/data-theme/TECH\n"
        "- Población y sociedad → http://publications.europa.eu/resource/authority/data-theme/SOCI\n"
        "- Gobierno y sector público → http://publications.europa.eu/resource/authority/data-theme/GOVE\n"

        # ── dcat_type ──
        "Para el campo 'dcat_type', devuelve la URI más adecuada:\n"
        "- Datos estadísticos → http://publications.europa.eu/resource/authority/dataset-type/STATISTICAL\n"
        "- Datos geoespaciales → http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL\n"
        "- Datos sintéticos → http://publications.europa.eu/resource/authority/dataset-type/SYNTHETIC_DATA\n"
        "- Conjunto de datos de alto valor → http://publications.europa.eu/resource/authority/dataset-type/HVD\n"

        # ── keyword ──
        "Para el campo 'keyword', devuelve un ARRAY de strings con las palabras clave del dataset.\n"

        # ── provenance ──
        "Para el campo 'provenance', devuelve un string describiendo el origen de los datos.\n"

        # ── contact ──
        "Para el campo 'contact', devuelve un objeto con:\n"
        "  email (string o null), url (URL o null)\n"

        # ── hdab ──
        "Para el campo 'hdab', devuelve un objeto con EXACTAMENTE estas claves:\n"
        "  name (string), type (URI del tipo de organismo), email (string o null),\n"
        "  telephone (string o null), contact_page (URL o null).\n"
        "Para 'type', usa la URI más adecuada, por ejemplo:\n"
        "- Instituto de investigación → http://13.81.34.152:1101/resource/authority/publisher-type/research-institute-org\n"
        "- Universidad → http://13.81.34.152:1101/resource/authority/publisher-type/university\n"
        "- Instituto de salud pública → http://13.81.34.152:1101/resource/authority/publisher-type/public-health-institute\n"
        "- Autoridad nacional → http://13.81.34.152:1101/resource/authority/publisher-type/national-authority\n"
        "No uses claves en español ni inventes URIs.\n"

        "No añadas claves extra ni texto fuera del JSON."
    )
    return (
        f"{block['question']}\n\n"
        f"Claves esperadas: [{fields}]\n"
        f"{instrucciones}\n"
        f"{'Contexto del usuario: ' + user_context if user_context else ''}"
    )


def apply_conditional_logic(state: MetadataState):
    """Si access_rights es NON_PUBLIC → asignar identifier predeterminado SIEMPRE."""
    ar = state.data.get("access_rights", "")
    if ar and "NON_PUBLIC" in str(ar).upper():
        state.data["identifier"] = ENDS_NON_PUBLIC_URI


def ask_block(schema: HealthDCATAPSchema, state: MetadataState, block: dict):
    print(f"\n=== BLOQUE: {block['name'].replace('_', ' ').upper()} ===\n")
    print(block["question"])

    if "identifier" in block["fields"] and is_non_public(state.data):
        print(f"\n🔒 El identificador se asignará automáticamente por ser un dataset No Público.")
        fields_to_ask = [f for f in block["fields"] if f != "identifier"]
        block_modified = {**block, "fields": fields_to_ask}
    else:
        block_modified = block

    print("\nTu respuesta (pulsa Enter dos veces para terminar):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    user_context = "\n".join(lines)

    if not user_context.strip():
        print("⏭️ Bloque omitido.")
        apply_conditional_logic(state)
        return

    prompt = build_prompt_for_block(schema, block_modified, user_context)
    contract = build_contract(block_modified)
    ai_result = call_llm(prompt, contract, user_context)
    partial = {name: ai_result.get(name, None) for name in block_modified["fields"]}
    state.merge_partial(partial)
    apply_conditional_logic(state)

    print("\n✔️ Bloque procesado:")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))

    errors = state.validate_types_basic()
    if errors:
        print("\n⚠️ Validaciones detectadas:")
        for err in errors:
            print(f" - {err}")

    missing = state.missing_required()
    if missing:
        print("\n⚠️ Campos obligatorios aún pendientes:")
        for m in missing:
            print(f" - {m}")


def save_output(state: MetadataState, path="metadata_output.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state.data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    schema = HealthDCATAPSchema("health_dcat_ap.yaml")
    state = MetadataState("health_dcat_ap.yaml")

    print("\n=== ASISTENTE MULTICAMPO HealthDCAT-AP ===\n")

    for block in BLOCKS:
        ask_block(schema, state, block)

    state.data["applicable_legislation"] = [
        {"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}
    ]

    print("\n=== RESULTADO FINAL ===\n")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))

    save_output(state)
    print("\n✅ Metadatos guardados en metadata_output.json")
