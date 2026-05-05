import json
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
BLOCKS = [
    {
        "name": "derechos de acceso",
        "fields": [
            "Derechos de acceso"
        ],
        "question": (
            "¿Quién puede acceder legalmente al dataset que estás subiendo y bajo qué condiciones?"
        )
    },
    {
        "name": "identificacion_basica",
        "fields": [
            "Título","Identificador", "Descripción"
        ],
        "question": (
            "Proporciona una descripción general del dataset e incluye el DOI del conjunto "
            "de datos si está disponible."
        )
    },
    {
        "name": "organismo_acceso_datos_sanitarios",
        "fields": [
            "Organismo de Acceso a los Datos Sanitarios"
        ],
        "question": (
            "Indica la entidad u organización que se encarga de gestionar el acceso a los datos sanitarios."
            "Por favor, escribe el nombre del organismo y qué tipo de entidad es (por ejemplo: instituto de salud pública, universidad, registro de salud, autoridad pública, etc.). "
            "Si lo conoces, añade también los datos de contacto para que los usuarios puedan comunicarse con la organización: correo electrónico, teléfono, página web y horario de atención."
        )
    }
]


def build_contract(block: dict) -> dict:
    # Claves esperadas en la respuesta del LLM para este bloque
    return {name: None for name in block["fields"]}

def build_prompt_for_block(schema: HealthDCATAPSchema, block: dict, user_context: str = "") -> str:
    fields = ", ".join(block["fields"])
    instrucciones = (
            "Devuelve SOLO JSON válido. Las listas como arrays JSON. "
            "REGLA MÁS IMPORTANTE: Si el usuario NO menciona explícitamente un campo, "
            "devuelve null para ese campo. NUNCA deduzcas, infergas ni inventes valores. "
            "Solo rellena un campo si el usuario ha proporcionado información DIRECTA sobre él. "
            "Si hay duda, devuelve null. "
    
        
        # ── access_rights ──
        "Para el campo 'access_rights', analiza la descripción y devuelve SOLO la URI:\n"
        "- Público → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
        "- Restringido → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
        "- Confidencial → http://publications.europa.eu/resource/authority/access-right/CONFIDENTIAL\n"
        "- No público → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        "- Sensible → http://publications.europa.eu/resource/authority/access-right/SENSITIVE\n"
        "- Normal → http://publications.europa.eu/resource/authority/access-right/NORMAL\n"
        "- Datos provisionales → http://publications.europa.eu/resource/authority/access-right/OP_DATPRO\n"

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





def ask_block(schema: HealthDCATAPSchema, state: MetadataState, block: dict):
    print(f"\n=== BLOQUE: {block['name']} ===\n")
    print(block["question"])

    # ✅ El usuario responde
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
        return

    prompt = build_prompt_for_block(schema, block, user_context)
    contract = build_contract(block)

    # El LLM interpreta la respuesta del usuario
    ai_result = call_llm(prompt, contract, user_context)

    partial = { name: ai_result.get(name, None) for name in block["fields"] }
    state.merge_partial(partial)

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