import json
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
BLOCKS = [
    {
        "name": "identificacion_basica",
        "fields": [
            "title", "name","identifier","applicable_legislation"
        ],
        "question": (
            "Proporciona una descripción general del dataset e incluye el DOI del conjunto "
            "de datos si está disponible. El campo 'applicable_legislation' será completado "
            "automáticamente por el asistente, por lo que no es necesario que lo aportes."
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





def ask_block(schema: HealthDCATAPSchema, state: MetadataState, block: dict):
    print(f"\n=== BLOQUE: {block['name']} ===\n")
    print(block["question"])

    # El asistente SIEMPRE usa IA
    user_context = ""  # puedes añadir contexto general si quieres
    prompt = build_prompt_for_block(schema, block, user_context)
    contract = build_contract(block)

    # Llama al LLM para generar TODO EL BLOQUE
    ai_result = call_llm(prompt, contract, user_context)

    # Guarda los datos en el estado
    partial = { name: ai_result.get(name, None) for name in block["fields"] }
    state.merge_partial(partial)

    print("\n✔️ Bloque procesado. Estado parcial actualizado:")
    print(json.dumps(state.data, indent=2, ensure_ascii=False))

    # Validaciones internas
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