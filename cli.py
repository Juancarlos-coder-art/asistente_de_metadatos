import json
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
BLOCKS = [
    {
        "name": "identificacion_basica",
        "fields": [
            "title", "name", "notes", "identifier", "uri",
            "version", "version_notes", "has_version"
        ],
        "question": (
            "Indica el título del dataset, el nombre corto para la URL en CKAN, "
            "una descripción general de qué contiene y para qué sirve, su identificador "
            "único si existe, la URI del dataset si la tienes, la versión actual, "
            "las notas de versión y si existe alguna versión relacionada o previa."
        )
    },
    {
        "name": "palabras_clave_y_clasificacion",
        "fields": [
            "tag_string", "theme", "dcat_type",
            "health_category", "health_theme",
            "code_values", "coding_system"
        ],
        "question": (
            "Indica las palabras clave del dataset, su temática general, el tipo de dataset, "
            "la categoría y temática sanitaria a la que pertenece, así como los códigos "
            "clínicos, clasificaciones o sistemas de codificación utilizados "
            "(por ejemplo ICD-10, SNOMED CT, etc.)."
        )
    },
    {
        "name": "responsables_del_dataset",
        "fields": [
            "publisher", "creator", "contact", "owner_org",
            "publisher_note", "publisher_type",
            "trusted_data_holder", "hdab"
        ],
        "question": (
            "Indica quién publica el dataset, quién lo creó y cuál es el punto de contacto "
            "para consultas. Para cada entidad, incluye si es posible nombre, URI, email, "
            "URL, tipo e identificador. Añade también la organización de CKAN a la que "
            "pertenecerá, el tipo de publicador, una breve nota sobre el publicador, "
            "si es un trusted data holder y, en su caso, el Health Data Access Body asociado."
        )
    },
    {
        "name": "paginas_y_documentacion",
        "fields": [
            "homepage", "url", "documentation",
            "conforms_to", "is_referenced_by", "analytics"
        ],
        "question": (
            "Indica la página principal del dataset, su landing page, la documentación "
            "disponible, las normas o especificaciones que sigue, las publicaciones o "
            "recursos que lo referencian y cualquier enlace a servicios analíticos, "
            "informes técnicos o indicadores de calidad asociados."
        )
    },
    {
        "name": "licencia_y_acceso",
        "fields": [
            "license_id", "access_rights",
            "applicable_legislation", "legal_basis"
        ],
        "question": (
            "Indica la licencia del dataset, sus condiciones o derechos de acceso, "
            "la legislación aplicable que obliga a su creación o gestión y la base "
            "jurídica que justifica el tratamiento de los datos personales, si aplica."
        )
    },
    {
        "name": "fechas_y_ciclo_de_vida",
        "fields": [
            "issued", "modified", "frequency",
            "provenance", "provenance_activity"
        ],
        "question": (
            "Indica la fecha de publicación del dataset, la última fecha de modificación, "
            "la frecuencia de actualización, una descripción de su procedencia o linaje y, "
            "si quieres documentarlo de forma estructurada, la actividad de procedencia "
            "que lo originó, incluyendo agentes, organización, tipo de actividad y fechas."
        )
    },
    {
        "name": "cobertura_temporal_y_espacial",
        "fields": [
            "temporal_coverage", "temporal_resolution",
            "spatial_coverage", "spatial_resolution_in_meters"
        ],
        "question": (
            "Indica el periodo temporal cubierto por el dataset, su resolución temporal, "
            "el ámbito geográfico que cubre y, si la conoces, la resolución espacial en metros. "
            "Para la cobertura geográfica puedes incluir URI, nombre de la región, geometría, "
            "bounding box o centroide."
        )
    },
    {
        "name": "idioma_e_identificadores",
        "fields": [
            "language", "alternate_identifier"
        ],
        "question": (
            "Indica el idioma o idiomas del dataset y cualquier identificador alternativo "
            "o secundario que tenga, como DOI, DataCite, ADS, MAST u otros."
        )
    },
    {
        "name": "finalidad_y_contexto_sanitario",
        "fields": [
            "purpose", "population_coverage",
            "personal_data", "health_category", "health_theme"
        ],
        "question": (
            "Explica la finalidad del tratamiento o del uso del dataset, qué población cubre, "
            "qué tipos de datos personales contiene o representa y, si procede, vuelve a indicar "
            "la categoría y temática sanitaria desde el punto de vista de HealthDCAT-AP."
        )
    },
    {
        "name": "variables_demograficas_y_tamano",
        "fields": [
            "min_typical_age", "max_typical_age",
            "number_of_records", "number_of_unique_individuals"
        ],
        "question": (
            "Indica la edad mínima y máxima típica de la población del dataset, "
            "el número total de registros y, si aplica, el número de individuos únicos representados."
        )
    },
    {
        "name": "conservacion_y_disponibilidad",
        "fields": [
            "retention_period"
        ],
        "question": (
            "Indica el periodo durante el cual el dataset está disponible para uso secundario, "
            "señalando fecha de inicio y de fin si se conocen."
        )
    },
    {
        "name": "relaciones_y_atribuciones",
        "fields": [
            "qualified_relation", "qualified_attribution"
        ],
        "question": (
            "Indica si el dataset mantiene relaciones formales con otros recursos o datasets "
            "y describe esas relaciones. Añade también, si aplica, atribuciones cualificadas, "
            "indicando el agente implicado y su rol respecto al dataset."
        )
    },
    {
        "name": "calidad_del_dataset",
        "fields": [
            "quality_annotation"
        ],
        "question": (
            "Indica si existen anotaciones de calidad sobre el dataset, como certificados, "
            "mediciones, resultados de evaluación o evidencias de calidad. Para cada una, "
            "incluye el contenido de la anotación, a qué aspecto del dataset se refiere "
            "y con qué motivación se realizó."
        )
    }
]

LIST_FIELDS = [
    "tag_string",
    "theme",
    "language",
    "documentation",
    "conforms_to",
    "is_referenced_by",
    "analytics",
    "alternate_identifier",
    "purpose",
    "population_coverage",
    "personal_data",
    "health_category",
    "health_theme",
    "legal_basis",
    "code_values",
    "coding_system",
    "applicable_legislation",
    "has_version"
]
def build_contract(block: dict) -> dict:
    # Claves esperadas en la respuesta del LLM para este bloque
    return {name: None for name in block["fields"]}

def build_prompt_for_block(schema: HealthDCATAPSchema, block: dict, user_context: str = "") -> str:
    fields = ", ".join(block["fields"])
    instrucciones = (
        "Devuelve SOLO JSON válido. Las listas como arrays JSON. "
        "El campo 'contact' es una lista de objetos con claves 'name', 'email', 'role'. "
        "No añadas claves extra ni texto fuera del JSON."
    )
    return (
        f"{block['question']}\n\n"
        f"Claves esperadas: [{fields}]\n"
        f"{instrucciones}\n"
        f"{'Contexto del usuario: ' + user_context if user_context else ''}"
    )

def parse_input(field_name: str, raw_value: str):

    raw_value = raw_value.strip()

    if raw_value == "":
        return None

    # campos que son listas
    if field_name in LIST_FIELDS:
        return [v.strip() for v in raw_value.split(",") if v.strip()]

    # campo contacto estructurado
    if field_name == "contact":

        contactos = []
        bloques = [b.strip() for b in raw_value.split(",") if b.strip()]

        for b in bloques:

            partes = [p.strip() for p in b.split("|")]

            contacto = {}

            if len(partes) > 0:
                contacto["name"] = partes[0]

            if len(partes) > 1:
                contacto["email"] = partes[1]

            if len(partes) > 2:
                contacto["role"] = partes[2]

            contactos.append(contacto)

        return contactos if contactos else None

    return raw_value

def ask_field(schema: HealthDCATAPSchema, field_name: str):
    """
    Muestra la pregunta para un campo concreto usando el schema.
    """
    field = schema.get_field(field_name)

    if field:
        label = field.get("label", field_name)
        help_text = field.get("help_text", "")
        required = field.get("required", False)

        print(f"\n📌 {label}" + (" (obligatorio)" if required else ""))
        if help_text:
            print(f"ℹ️ {help_text}")
    else:
        print(f"\n📌 {field_name}")

    raw_value = input("Tu respuesta: ")
    return parse_input(field_name, raw_value)


def ask_block(schema: HealthDCATAPSchema, state: MetadataState, block: dict):
    print(f"\n=== BLOQUE: {block['name']} ===\n")
    print(block["question"])

    # Pregunta si quieres que el LLM lo sugiera todo de una vez
    use_ai = False
    if llm_available():
        choice = input("Pulsa Enter para contestar tú, o escribe 'ia' para autocompletar con IA: ").strip().lower()
        use_ai = (choice == "ia")

    partial = {}

    if use_ai:
        # Recoge contexto libre del usuario (opcional)
        user_context = input("Añade contexto opcional para la IA (o Enter para saltar): ").strip()
        prompt = build_prompt_for_block(schema, block, user_context)
        contract = build_contract(block)
        ai_result = call_llm(prompt, contract, user_context)  # dict con las claves del bloque

        # Integra tal cual lo que devuelve el LLM (ya está tipado)
        for name in block["fields"]:
            partial[name] = ai_result.get(name, None)

    else:
        # Camino manual de siempre
        for field_name in block["fields"]:
            partial[field_name] = ask_field(schema, field_name)

    state.merge_partial(partial)

    print("\n✔️ Bloque procesado. Estado parcial actualizado:")
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
    schema = HealthDCATAPSchema("health_dcat_ap.json")
    state = MetadataState("health_dcat_ap.json")

    print("\n=== ASISTENTE MULTICAMPO HealthDCAT-AP ===\n")

    for block in BLOCKS:
        ask_block(schema, state, block)

    print("\n=== RESULTADO FINAL ===\n")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))

    save_output(state)
    print("\n✅ Metadatos guardados en metadata_output.json")