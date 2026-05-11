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
        "hint": "Describe con tus palabras quién tiene acceso y bajo qué condiciones."

    },
    {
        "name": "identificacion_basica",
        "fields": ["title", "identifier", "notes"],
        "question": (
            "Proporciona una descripción general del dataset e incluye el identificador del conjunto "
            "de datos si está disponible."
        ),
        "hint": "Dinos cómo se llama el dataset, de qué trata y si tiene algún identificador como un DOI."
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
        "hint":"Indícanos qué organismo es el responsable de dar acceso a estos datos y cómo contactarle."
    }
]


def is_non_public(state_data: dict) -> bool:
    """Comprueba si el access_rights del estado es NON_PUBLIC."""
    ar = state_data.get("access_rights", "")
    if not ar:
        return False
    return "No Público" in str(ar).upper()


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
    if is_non_public(state.data):
        state.data["identifier"] = ENDS_NON_PUBLIC_URI  # ← siempre, no solo si está vacío
        print(f"\n🔒 Acceso No Público. Identificador asignado: {ENDS_NON_PUBLIC_URI}")


def ask_block(schema: HealthDCATAPSchema, state: MetadataState, block: dict):
    print(f"\n=== BLOQUE: {block['name'].replace('_', ' ').upper()} ===\n")
    print(block["question"])

    # Si el bloque contiene 'identifier' y el acceso ya es NON_PUBLIC → omitir identifier
    if "identifier" in block["fields"] and is_non_public(state.data):
        print(f"\n🔒 El identificador se asignará automáticamente por ser un dataset No Público.")
        # Preguntar solo por los campos restantes (sin identifier)
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
        # Aplicar lógica condicional aunque se omita
        apply_conditional_logic(state)
        return

    prompt = build_prompt_for_block(schema, block_modified, user_context)
    contract = build_contract(block_modified)

    ai_result = call_llm(prompt, contract, user_context)

    partial = {name: ai_result.get(name, None) for name in block_modified["fields"]}
    state.merge_partial(partial)

    # ✅ Aplicar lógica condicional tras procesar el bloque
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

    # ✅ Inserción automática de legislación aplicable
    state.data["applicable_legislation"] = [
        {
            "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
            "label": "GDPR"
        }
    ]

    print("\n=== RESULTADO FINAL ===\n")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))

    save_output(state)
    print("\n✅ Metadatos guardados en metadata_output.json")