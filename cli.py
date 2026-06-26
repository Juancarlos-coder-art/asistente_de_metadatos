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
        "name_en": "Access Rights",
        "fields": ["access_rights"],
        "question": (
            "¿Quién puede acceder a este dataset y bajo qué condiciones?\n\n"
            "Ejemplos:\n"
            "- 'Cualquiera puede descargarlo' → Público\n"
            "- 'Solo investigadores acreditados pueden solicitarlo' → Restringido\n"
            "- 'Es un dataset interno, no sale de nuestra organización' → No público\n"
        ),
        "question_en": (
            "Who can access this dataset and under what conditions?\n\n"
            "Examples:\n"
            "- 'Anyone can download it' → Public\n"
            "- 'Only accredited researchers can request it' → Restricted\n"
            "- 'It is internal, it does not leave our organisation' → Non-public\n"
        ),
        "hint": "Describe con tus palabras quién tiene acceso y bajo qué condiciones.",
        "hint_en": "Describe in your own words who has access and under what conditions.",
        "placeholder": "Ej.: El acceso está restringido a investigadores acreditados por organismos públicos de salud...",
        "placeholder_en": "E.g.: Access is restricted to researchers accredited by public health bodies...",
    },
    {
        "name": "identificacion_basica",
        "name_en": "Basic Identification",
        "fields": ["title", "identifier", "notes", "health_category", "theme", "dcat_type", "provenance", "keyword"],
        "question": (
            "Proporciona una descripción general del dataset. Incluye el identificador si está disponible, "
            "la categoría sanitaria, el tema, el tipo de dataset, la procedencia de los datos y las palabras clave."
        ),
        "question_en": (
            "Provide a general description of the dataset. Include the identifier if available, "
            "the health category, the theme, the dataset type, the data provenance and keywords."
        ),
        "hint": "Dinos el nombre del dataset, de qué trata, su categoría sanitaria, tema, tipo y origen.",
        "hint_en": "Tell us the dataset name, what it is about, its health category, theme, type and origin.",
        "placeholder": "Ej.: Dataset sobre casos de Mpox en España 2023. Es un registro epidemiológico del ISCIII...",
        "placeholder_en": "E.g.: Dataset on Mpox cases in Spain 2023. It is an epidemiological registry from ISCIII...",
    },
    {
        "name": "informacion_adicional",
        "name_en": "Additional Information",
        "fields": ["purpose", "language", "population_coverage", "number_of_unique_individuals","number_of_records","min_typical_age","max_typical_age","personal_data","legal_basis","retention_period","coding_system","health_theme","code_values"],
        "question": (
            "Proporciona información adicional sobre el dataset."
            "Indica la finalidad de los datos, el idioma en el que están disponibles y la cobertura poblacional si están disponibles."
        ),
        "question_en": (
            "Provide additional information about the dataset. "
            "Indicate the purpose of the data, the language in which it is available, and the population coverage if available."
        ),
        "hint": "Describe la finalidad del dataset, el idioma en el que está disponible y a qué población cubre.",
        "hint_en": "Describe the purpose of the dataset, the language in which it is available, and which population it covers.",
        "placeholder": "Ej.: La finalidad es investigación epidemiológica. Está disponible en español. Cubre población mayor de 18 años...",
        "placeholder_en": "E.g.: The purpose is epidemiological research. It is available in Spanish. It covers population over 18 years...",
    },
    {
        "name": "organismo_acceso_datos_sanitarios",
        "name_en": "Health Data Access Body",
        "fields": ["hdab"],
        "question": (
            "Indica el organismo que gestiona el acceso a los datos sanitarios (HDAB). "
            "Por favor, proporciona el nombre del organismo y su tipo (por ejemplo: "
            "Instituto de salud pública, Universidad, Registro de salud pública, "
            "Autoridad nacional, etc.). "
            "Si dispones de ellos, incluye también el correo de contacto, "
            "el teléfono, la página web de contacto y el horario de disponibilidad."
        ),
        "question_en": (
            "Indicate the body that manages access to health data (HDAB). "
            "Please provide the name of the body and its type (e.g. "
            "Public health institute, University, Public health registry, "
            "National authority, etc.). "
            "If available, also include the contact email, "
            "phone number, contact page and opening hours."
        ),
        "hint": "Indícanos qué organismo es el responsable de dar acceso a estos datos y cómo contactarle.",
        "hint_en": "Tell us which body is responsible for providing access to this data and how to contact them.",
        "placeholder": "Ej.: El organismo es el ISCIII, su correo es datos.salud@isciii.es...",
        "placeholder_en": "E.g.: The body is ISCIII, email is datos.salud@isciii.es...",
    },
    {
        "name": "punto_de_contacto",
        "name_en": "Contact Point",
        "fields": ["contact"],
        "question": (
            "¿Cuál es el punto de contacto para este dataset?\n\n"
            "Proporciona el correo electrónico y/o la URL de contacto para consultas sobre el dataset."
        ),
        "question_en": (
            "What is the contact point for this dataset?\n\n"
            "Provide the email address and/or contact URL for enquiries about the dataset."
        ),
        "hint": "Indica el correo o web de contacto para consultas sobre este dataset.",
        "hint_en": "Provide the contact email or website for enquiries about this dataset.",
        "placeholder": "Ej.: Para consultas contacta en info@ministeriodesanidad.es o visita https://www.sanidad.gob.es/contacto",
        "placeholder_en": "E.g.: For enquiries contact info@health.gov or visit https://www.health.gov/contact",
    },
    {
        "name": "responsables_dataset",
        "name_en": "Dataset Responsible Parties",
        "fields": ["publisher", "publisher_note", "creator", "qualified_attribution","quality_annotation"],
        "question": (
            "Indica quién es el editor (publicador) y el creador de este dataset.\n\n"
            "Para el editor, proporciona el nombre de la organización, su tipo (universidad, autoridad nacional, etc.), "
            "el correo electrónico, teléfono, página de contacto y, si lo conoces, "
            "la descripción y frecuencia del horario de atención.\n\n"
            "Para el creador, proporciona el nombre, correo, URL y tipo de organización.\n\n"
            "Si hay alguna atribución cualificada (agentes con un rol específico como autor, custodio, financiador, etc.), "
            "indícalo también con su nombre, tipo, contacto y rol."
        ),
        "question_en": (
            "Indicate who is the publisher and creator of this dataset.\n\n"
            "For the publisher, provide the organisation name, its type (university, national authority, etc.), "
            "the email, phone, contact page and, if known, "
            "the description and frequency of opening hours.\n\n"
            "For the creator, provide the name, email, URL and organisation type.\n\n"
            "If there is any qualified attribution (agents with a specific role such as author, custodian, funder, etc.), "
            "include their name, type, contact and role."
        ),
        "hint": "Indica el editor, creador y atribuciones cualificadas del dataset.",
        "hint_en": "Provide the publisher, creator and qualified attributions of the dataset.",
        "placeholder": "Ej.: El editor es la Universidad de Valencia, correo datos@uv.es. El creador es el ISCIII, correo isciii@gob.es...",
        "placeholder_en": "E.g.: The publisher is the University of Valencia, email datos@uv.es. The creator is ISCIII, email isciii@gob.es...",
    },
    {
        "name": "cobertura_temporalidad",
        "name_en": "Coverage and Temporality",
        "fields": ["was_generated_by", "spatial", "temporal_coverage", "temporal_resolution", "spatial_resolution_in_meters", "frequency", "issued", "modified"],
        "question": (
            "Proporciona información sobre la cobertura y temporalidad del dataset.\n\n"
            "Indica cómo se generaron los datos (ensayo clínico, encuesta, registros hospitalarios, etc.), "
            "la cobertura geográfica (países), el periodo temporal cubierto, "
            "la resolución temporal y espacial, la frecuencia de actualización, "
            "y las fechas de publicación y última modificación."
        ),
        "question_en": (
            "Provide information about the dataset's coverage and temporality.\n\n"
            "Indicate how the data was generated (clinical trial, survey, hospital records, etc.), "
            "the geographical coverage (countries), the temporal period covered, "
            "the temporal and spatial resolution, the update frequency, "
            "and the publication and last modification dates."
        ),
        "hint": "Describe cómo se generaron los datos, su cobertura geográfica y temporal, frecuencia y fechas.",
        "hint_en": "Describe how the data was generated, its geographic and temporal coverage, frequency and dates.",
        "placeholder": "Ej.: Datos generados por registros hospitalarios, cobertura en España, periodo 2020-2023, actualización mensual...",
        "placeholder_en": "E.g.: Data generated from hospital records, coverage in Spain, period 2020-2023, monthly update...",
    },
    {
        "name": "relaciones_versionado",
        "name_en": "Relationships and Versioning",
        "fields": ["alternate_identifier", "conforms_to", "related_resource", "is_referenced_by", "url", "documentation", "version", "has_version", "version_notes"],
        "question": (
            "Proporciona información sobre identificadores alternativos, estándares, "
            "recursos relacionados, documentación y versionado del dataset.\n\n"
            "Incluye la página de entrada (landing page), documentación asociada, "
            "la versión actual y sus notas si están disponibles."
        ),
        "question_en": (
            "Provide information about alternate identifiers, standards, "
            "related resources, documentation and versioning of the dataset.\n\n"
            "Include the landing page, associated documentation, "
            "the current version and its notes if available."
        ),
        "hint": "Indica identificadores alternativos, estándares, recursos relacionados, documentación y versión.",
        "hint_en": "Provide alternate identifiers, standards, related resources, documentation and version.",
        "placeholder": "Ej.: Identificador alternativo DOI:10.1234/xyz. Se ajusta a DCAT-AP. Versión 2.0...",
        "placeholder_en": "E.g.: Alternate identifier DOI:10.1234/xyz. Conforms to DCAT-AP. Version 2.0...",
    },
]

def is_non_public(state_data: dict) -> bool:
    """Comprueba si el access_rights del estado es NON_PUBLIC."""
    ar = state_data.get("access_rights", "")
    if not ar:
        return False
    return "NON_PUBLIC" in str(ar).upper()


def build_contract(block: dict) -> dict:
    return {name: None for name in block["fields"]}

LANGUAGES = {
    "alemán": "http://publications.europa.eu/resource/authority/language/DEU",
    "bokmål": "http://publications.europa.eu/resource/authority/language/NOB",
    "búlgaro": "http://publications.europa.eu/resource/authority/language/BUL",
    "checo": "http://publications.europa.eu/resource/authority/language/CES",
    "croata": "http://publications.europa.eu/resource/authority/language/HRV",
    "danés": "http://publications.europa.eu/resource/authority/language/DAN",
    "eslovaco": "http://publications.europa.eu/resource/authority/language/SLK",
    "esloveno": "http://publications.europa.eu/resource/authority/language/SLV",
    "español": "http://publications.europa.eu/resource/authority/language/SPA",
    "estonio": "http://publications.europa.eu/resource/authority/language/EST",
    "finés": "http://publications.europa.eu/resource/authority/language/FIN",
    "francés": "http://publications.europa.eu/resource/authority/language/FRA",
    "griego": "http://publications.europa.eu/resource/authority/language/ELL",
    "húngaro": "http://publications.europa.eu/resource/authority/language/HUN",
    "inglés": "http://publications.europa.eu/resource/authority/language/ENG",
    "irlandés": "http://publications.europa.eu/resource/authority/language/GLE",
    "islandés": "http://publications.europa.eu/resource/authority/language/ISL",
    "italiano": "http://publications.europa.eu/resource/authority/language/ITA",
    "letón": "http://publications.europa.eu/resource/authority/language/LAV",
    "lituano": "http://publications.europa.eu/resource/authority/language/LIT",
    "maltés": "http://publications.europa.eu/resource/authority/language/MLT",
    "neerlandés": "http://publications.europa.eu/resource/authority/language/NLD",
    "nynorsk": "http://publications.europa.eu/resource/authority/language/NNO",
    "polaco": "http://publications.europa.eu/resource/authority/language/POL",
    "portugués": "http://publications.europa.eu/resource/authority/language/POR",
    "rumano": "http://publications.europa.eu/resource/authority/language/RON",
    "sueco": "http://publications.europa.eu/resource/authority/language/SWE",
}

PERSONAL_DATA_TYPES = {
    "edad": "https://w3id.org/dpv/pd#Age",
    "rango de edad": "https://w3id.org/dpv/pd#AgeRange",
    "datos biométricos": "https://w3id.org/dpv/pd#Biometric",
    "tipo de sangre": "https://w3id.org/dpv/pd#BloodType",
    "fecha de nacimiento": "https://w3id.org/dpv/pd#BirthDate",
    "país de nacimiento": "https://w3id.org/dpv/pd#BirthCountry",
    "discapacidad": "https://w3id.org/dpv/pd#Disability",
    "adn": "https://w3id.org/dpv/pd#DNACode",
    "origen étnico": "https://w3id.org/dpv/pd#Ethnicity",
    "género": "https://w3id.org/dpv/pd#Gender",
    "datos genéticos": "https://w3id.org/dpv/pd#Genetic",
    "datos de salud": "https://w3id.org/dpv/pd#HealthData",
    "historial de salud": "https://w3id.org/dpv/pd#HealthHistory",
    "registro de salud": "https://w3id.org/dpv/pd#HealthRecord",
    "altura": "https://w3id.org/dpv/pd#Height",
    "vida sexual": "https://w3id.org/dpv/pd#LifeSexual",
    "historial médico": "https://w3id.org/dpv/pd#MedicalHealth",
    "salud mental": "https://w3id.org/dpv/pd#MentalHealth",
    "salud física": "https://w3id.org/dpv/pd#PhysicalHealth",
    "receta médica": "https://w3id.org/dpv/pd#Prescription",
    "origen racial": "https://w3id.org/dpv/pd#Race",
    "datos de salud sexual": "https://w3id.org/dpv/pd#SexualHistory",
    "peso": "https://w3id.org/dpv/pd#Weight",
}

PUBLISHER_TYPES = {
    "instituto de salud pública": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-institute",
    "instituto/organización de investigación": "http://13.81.34.152:1101/resource/authority/publisher-type/research-institute-org",
    "autoridad nacional": "http://13.81.34.152:1101/resource/authority/publisher-type/national-authority",
    "autoridad regional": "http://13.81.34.152:1101/resource/authority/publisher-type/regional-authority",
    "universidad": "http://13.81.34.152:1101/resource/authority/publisher-type/university",
    "registro de salud pública": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-registry",
    "organización de salud pública": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-org",
    "agencia de estadísticas": "http://13.81.34.152:1101/resource/authority/publisher-type/stat-agency",
    "biobanco": "http://13.81.34.152:1101/resource/authority/publisher-type/biobank",
    "institución de hospitalización/hospital": "http://13.81.34.152:1101/resource/authority/publisher-type/inpatient-institute",
    "laboratorio": "http://13.81.34.152:1101/resource/authority/publisher-type/laboratory",
    "empresa privada": "http://13.81.34.152:1101/resource/authority/publisher-type/private-company",
    "organizaciones gubernamentales y del sector público": "http://13.81.34.152:1101/resource/authority/publisher-type/gov-public-sector-org",
    "proveedor de atención médica": "http://13.81.34.152:1101/resource/authority/publisher-type/healthcare-providers",
    "compañía/organización de seguros de salud": "http://13.81.34.152:1101/resource/authority/publisher-type/health-insurance-company-org",
    "empresas farmacéuticas": "http://13.81.34.152:1101/resource/authority/publisher-type/pharma-company",
    "entidades del sector privado": "http://13.81.34.152:1101/resource/authority/publisher-type/private-sector-entities",
    "fabricante de aplicaciones/tecnología de salud": "http://13.81.34.152:1101/resource/authority/publisher-type/health-technology-manufacturer",
    "fabricante de software": "http://13.81.34.152:1101/resource/authority/publisher-type/software-manufacturer",
    "farmacia": "http://13.81.34.152:1101/resource/authority/publisher-type/pharmacy",
    "infraestructuras de investigación": "http://13.81.34.152:1101/resource/authority/publisher-type/research-infra",
    "institución administrativa": "http://13.81.34.152:1101/resource/authority/publisher-type/administrative-institution",
    "institución ambulatoria": "http://13.81.34.152:1101/resource/authority/publisher-type/outpatient-institute",
    "instituto nacional del cáncer": "http://13.81.34.152:1101/resource/authority/publisher-type/national-cancer-institute",
    "municipio u otra área": "http://13.81.34.152:1101/resource/authority/publisher-type/municipality-or-other-area",
    "organizaciones de investigación y académicas": "http://13.81.34.152:1101/resource/authority/publisher-type/research-academic-org",
    "organizaciones no gubernamentales": "http://13.81.34.152:1101/resource/authority/publisher-type/non-gov-org",
    "organización de atención primaria": "http://13.81.34.152:1101/resource/authority/publisher-type/primary-care-org",
    "organización de salud mental": "http://13.81.34.152:1101/resource/authority/publisher-type/mental-health-org",
    "organización sin ánimo de lucro": "http://13.81.34.152:1101/resource/authority/publisher-type/not-for-profit-org",
    "otra agencia gubernamental": "http://13.81.34.152:1101/resource/authority/publisher-type/other-government-agency",
    "otro tipo de empresa que de alguna manera recopila datos de salud": "http://13.81.34.152:1101/resource/authority/publisher-type/other-company",
    "otros institutos públicos que recogen datos de salud": "http://13.81.34.152:1101/resource/authority/publisher-type/other-public-institute",
    "registro de calidad": "http://13.81.34.152:1101/resource/authority/publisher-type/quality-registry",
    "registro de patología": "http://13.81.34.152:1101/resource/authority/publisher-type/pathology-registry",
    "seguro de salud privado": "http://13.81.34.152:1101/resource/authority/publisher-type/private-health-insurance",
}

HEALTH_CATEGORIES = {
    "registros electrónicos de salud": "http://13.81.34.152:1101/resource/authority/healthcategories/EHRS",
    "datos administrativos relacionados con la salud, incluidos los datos de dispensación, reclamaciones y reembolsos": "http://13.81.34.152:1101/resource/authority/healthcategories/HRAD",
    "datos de registros médicos y registros de mortalidad": "http://13.81.34.152:1101/resource/authority/healthcategories/MRMR",
    "datos de patógenos que afectan a la salud humana": "http://13.81.34.152:1101/resource/authority/healthcategories/RPDG",
    "datos de cohortes de investigación, cuestionarios y encuestas relacionados con la salud, tras la primera publicación de los resultados": "http://13.81.34.152:1101/resource/authority/healthcategories/RQSH",
    "datos de ensayos clínicos, estudios clínicos e investigaciones clínicas sujetos respectivamente al reglamento (ue) 536/2014, al reglamento [soho], al reglamento (ue) 2017/745 y al reglamento (ue) 2017/746": "http://13.81.34.152:1101/resource/authority/healthcategories/EHCT",
    "datos genéticos, epigenómicos y genómicos humanos": "http://13.81.34.152:1101/resource/authority/healthcategories/HGPD",
    "datos de salud de biobancos y bases de datos asociadas": "http://13.81.34.152:1101/resource/authority/healthcategories/EINS",
    "otros datos de salud de dispositivos médicos": "http://13.81.34.152:1101/resource/authority/healthcategories/EMRD",
    "otros datos moleculares humanos como datos proteómicos, transcriptómicos, metabolómicos, lipidómicos y otros datos ómicos": "http://13.81.34.152:1101/resource/authority/healthcategories/HPML",
    "datos de registros de productos medicinales y dispositivos médicos": "http://13.81.34.152:1101/resource/authority/healthcategories/RMMD",
    "datos agregados sobre las necesidades de atención sanitaria, los recursos asignados a la atención sanitaria, la prestación y el acceso a la atención sanitaria, el gasto sanitario y la financiación": "http://13.81.34.152:1101/resource/authority/healthcategories/NRPE",
    "registros de datos de salud basados en la población (registros de salud pública)": "http://13.81.34.152:1101/resource/authority/healthcategories/PHDR",
    "datos de aplicaciones de bienestar": "http://13.81.34.152:1101/resource/authority/healthcategories/WELA",
    "datos electrónicos de salud personales generados automáticamente a través de dispositivos médicos": "http://13.81.34.152:1101/resource/authority/healthcategories/PGEH",
    "datos sobre el estado profesional, la especialización y la institución de los profesionales de la salud involucrados en el tratamiento de una persona física": "http://13.81.34.152:1101/resource/authority/healthcategories/IDHP",
    "datos sobre factores que afectan a la salud, incluidos los determinantes socioeconómicos, ambientales y de comportamiento de la salud": "http://13.81.34.152:1101/resource/authority/healthcategories/DIOH",
}

THEMES = {
    "agricultura, pesca, silvicultura y alimentación": "http://publications.europa.eu/resource/authority/data-theme/AGRI",
    "economía y finanzas": "http://publications.europa.eu/resource/authority/data-theme/ECON",
    "educación, cultura y deportes": "http://publications.europa.eu/resource/authority/data-theme/EDUC",
    "energía": "http://publications.europa.eu/resource/authority/data-theme/ENER",
    "medio ambiente": "http://publications.europa.eu/resource/authority/data-theme/ENVI",
    "gobierno y sector público": "http://publications.europa.eu/resource/authority/data-theme/GOVE",
    "salud": "http://publications.europa.eu/resource/authority/data-theme/HEAL",
    "asuntos internacionales": "http://publications.europa.eu/resource/authority/data-theme/INTR",
    "justicia, sistema judicial y seguridad pública": "http://publications.europa.eu/resource/authority/data-theme/JUST",
    "datos provisionales": "http://publications.europa.eu/resource/authority/data-theme/OP_DATPRO",
    "regiones y ciudades": "http://publications.europa.eu/resource/authority/data-theme/REGI",
    "población y sociedad": "http://publications.europa.eu/resource/authority/data-theme/SOCI",
    "ciencia y tecnología": "http://publications.europa.eu/resource/authority/data-theme/TECH",
    "transporte": "http://publications.europa.eu/resource/authority/data-theme/TRAN",
}

DATASET_TYPES = {
    "componente básico": "http://publications.europa.eu/resource/authority/dataset-type/CORE_COMP",
    "conjunto de datos de alto valor": "http://publications.europa.eu/resource/authority/dataset-type/HVD",
    "correspondencia": "http://publications.europa.eu/resource/authority/dataset-type/MAPPING",
    "cuadro atto – dominio eur-lex": "http://publications.europa.eu/resource/authority/dataset-type/ATTO_LEX",
    "cuadro atto – dominio publicaciones": "http://publications.europa.eu/resource/authority/dataset-type/ATTO_PUB",
    "datos de prueba": "http://publications.europa.eu/resource/authority/dataset-type/TEST_DATA",
    "datos estadísticos": "http://publications.europa.eu/resource/authority/dataset-type/STATISTICAL",
    "datos geoespaciales": "http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL",
    "datos provisionales": "http://publications.europa.eu/resource/authority/dataset-type/OP_DATPRO",
    "datos sintéticos": "http://publications.europa.eu/resource/authority/dataset-type/SYNTHETIC_DATA",
    "descripción de un paquete de intercambio de información": "http://publications.europa.eu/resource/authority/dataset-type/IEPD",
    "descripción del servicio": "http://publications.europa.eu/resource/authority/dataset-type/DSCRP_SERV",
    "directorio": "http://publications.europa.eu/resource/authority/dataset-type/DIRECTORY",
    "esquema": "http://publications.europa.eu/resource/authority/dataset-type/SCHEMA",
    "esquema de codificación sintáctica": "http://publications.europa.eu/resource/authority/dataset-type/SYNTAX_ECD_SCHEME",
    "glosario": "http://publications.europa.eu/resource/authority/dataset-type/GLOSSARY",
    "hojas de estilo": "http://publications.europa.eu/resource/authority/dataset-type/STYLES",
    "lista autorizada de nombres": "http://publications.europa.eu/resource/authority/dataset-type/NAL",
    "lista de códigos": "http://publications.europa.eu/resource/authority/dataset-type/CODE_LIST",
    "modelo de dominio": "http://publications.europa.eu/resource/authority/dataset-type/DOMAIN_MODEL",
    "ontología": "http://publications.europa.eu/resource/authority/dataset-type/ONTOLOGY",
    "perfil de aplicación": "http://publications.europa.eu/resource/authority/dataset-type/APROF",
    "publicación": "http://publications.europa.eu/resource/authority/dataset-type/RELEASE",
    "taxonomía": "http://publications.europa.eu/resource/authority/dataset-type/TAXONOMY",
    "tesauro": "http://publications.europa.eu/resource/authority/dataset-type/THESAURUS",
}
HEALTH_ACTIVITIES = {
    "aplicación de sanidad electrónica": "http://13.81.34.152:1101/resource/authority/health-activity/EHEALTH_APPLICATION",
    "aplicación no médica": "http://13.81.34.152:1101/resource/authority/health-activity/NONMEDICAL_APPLICATION",
    "base de datos de historiales hospitalarios": "http://13.81.34.152:1101/resource/authority/health-activity/HOSPITAL_RECORDS",
    "base de datos de investigación específica": "http://13.81.34.152:1101/resource/authority/health-activity/RESEARCH_DATABASE",
    "biobanco/recogida de muestras": "http://13.81.34.152:1101/resource/authority/health-activity/BIOBANK_COLLECTION",
    "cohorte": "http://13.81.34.152:1101/resource/authority/health-activity/COHORT",
    "colecciones de muestras": "http://13.81.34.152:1101/resource/authority/health-activity/SAMPLE_COLLECTIONS",
    "datos de observación": "http://13.81.34.152:1101/resource/authority/health-activity/OBSERVATIONAL_DATA",
    "datos del censo": "http://13.81.34.152:1101/resource/authority/health-activity/CENSUS_DATA",
    "encuesta de probabilidad": "http://13.81.34.152:1101/resource/authority/health-activity/PROBABILITY_SURVEY",
    "encuesta de salud": "http://13.81.34.152:1101/resource/authority/health-activity/HEALTH_SURVEY",
    "ensayo clínico": "http://13.81.34.152:1101/resource/authority/health-activity/CLINICAL_TRIAL",
    "generado automáticamente": "http://13.81.34.152:1101/resource/authority/health-activity/AUTOMATIC_GENERATION",
    "ingreso, atención y alta del paciente": "http://13.81.34.152:1101/resource/authority/health-activity/ADMISSION_DISCHARGE",
    "mediciones": "http://13.81.34.152:1101/resource/authority/health-activity/MEASUREMENTS",
    "modelos y simulaciones": "http://13.81.34.152:1101/resource/authority/health-activity/MODELS_SIMULATIONS",
    "prescripción o dispensación de medicamentos": "http://13.81.34.152:1101/resource/authority/health-activity/PRESCRIBING_DISPENSING",
    "procesos administrativos": "http://13.81.34.152:1101/resource/authority/health-activity/ADMINISTRATIVE_PROCESSES",
    "prom (medidas de resultados comunicados por los pacientes)": "http://13.81.34.152:1101/resource/authority/health-activity/PATIENT_OUTCOMES",
    "proyecto de investigación": "http://13.81.34.152:1101/resource/authority/health-activity/RESEARCH_PROJECT",
    "pruebas de laboratorio": "http://13.81.34.152:1101/resource/authority/health-activity/LABORATORY_TESTS",
    "reclamaciones, seguros y reembolsos": "http://13.81.34.152:1101/resource/authority/health-activity/INSURANCE_CLAIMS",
    "registro de calidad": "http://13.81.34.152:1101/resource/authority/health-activity/QUALITY_REGISTRY",
    "registro médico": "http://13.81.34.152:1101/resource/authority/health-activity/MEDICAL_REGISTRY",
    "registros de rutina (no sanitarios)": "http://13.81.34.152:1101/resource/authority/health-activity/ROUTINE_RECORDS",
    "registros nacionales de calidad médica": "http://13.81.34.152:1101/resource/authority/health-activity/QUALITY_REGISTRIES",
    "registros nacionales de salud": "http://13.81.34.152:1101/resource/authority/health-activity/HEALTH_REGISTRIES",
    "repositorio municipal de datos sanitarios": "http://13.81.34.152:1101/resource/authority/health-activity/MUNICIPAL_REPOSITORY",
    "seguimiento geoespacial": "http://13.81.34.152:1101/resource/authority/health-activity/GEOSPATIAL_MONITORING",
    "uso de productos sanitarios": "http://13.81.34.152:1101/resource/authority/health-activity/MEDICAL_DEVICES",
    "vigilancia": "http://13.81.34.152:1101/resource/authority/health-activity/SURVEILLANCE",
    "vigilancia de enfermedades infecciosas": "http://13.81.34.152:1101/resource/authority/health-activity/DISEASE_MONITORING",
    "vigilancia de la salud pública": "http://13.81.34.152:1101/resource/authority/health-activity/HEALTH_SURVEILLANCE",
    "visita sanitaria": "http://13.81.34.152:1101/resource/authority/health-activity/HEALTHCARE_VISIT",
}

HEALTH_THEMES = {
    "clima y salud planetaria": "http://13.81.34.152:1101/resource/authority/health-theme/CLIMATE_HEALTH",
    "cáncer": "http://13.81.34.152:1101/resource/authority/health-theme/CANCER_DISEASE",
    "emergencias, catástrofes, viajes y entornos humanitarios": "http://13.81.34.152:1101/resource/authority/health-theme/EMERGENCY_SETTINGS",
    "enfermedades cutáneas tropicales, parasitarias y fúngicas desatendidas": "http://13.81.34.152:1101/resource/authority/health-theme/TROPICAL_DISEASES",
    "enfermedades infecciosas respiratorias": "http://13.81.34.152:1101/resource/authority/health-theme/RESPIRATORY_DISEASES",
    "enfermedades no transmisibles: metabólicas y cardiopulmonares": "http://13.81.34.152:1101/resource/authority/health-theme/NONCOMMUNICABLE_DISEASES",
    "enfermedades víricas de transmisión vectorial y zoonóticas": "http://13.81.34.152:1101/resource/authority/health-theme/VECTOR_DISEASES",
    "infecciones de transmisión sanguínea y de transmisión sexual": "http://13.81.34.152:1101/resource/authority/health-theme/BLOOD_INFECTIONS",
    "infecciones entéricas, transmitidas por el agua y los alimentos": "http://13.81.34.152:1101/resource/authority/health-theme/ENTERIC_INFECTIONS",
    "inmunización y enfermedades prevenibles mediante vacunación": "http://13.81.34.152:1101/resource/authority/health-theme/IMMUNIZATION_DISEASES",
    "lesiones, envenenamiento y ahogamiento": "http://13.81.34.152:1101/resource/authority/health-theme/INJURY_PREVENTION",
    "nutrición y seguridad alimentaria": "http://13.81.34.152:1101/resource/authority/health-theme/NUTRITION_SECURITY",
    "productos sanitarios, tecnologías, datos e investigación": "http://13.81.34.152:1101/resource/authority/health-theme/HEALTH_PRODUCTS",
    "resistencia a los antimicrobianos y control de las infecciones": "http://13.81.34.152:1101/resource/authority/health-theme/ANTIMICROBIAL_CONTROL",
    "salud a lo largo de la vida: materna, neonatal, infantil, adolescente y envejecimiento": "http://13.81.34.152:1101/resource/authority/health-theme/LIFECOURSE_HEALTH",
    "salud ambiental, laboral y radiológica (incl. wash y urbana)": "http://13.81.34.152:1101/resource/authority/health-theme/ENVIRONMENTAL_HEALTH",
    "salud bucal, ocular y sensorial": "http://13.81.34.152:1101/resource/authority/health-theme/SENSORY_HEALTH",
    "salud y derechos sexuales y reproductivos": "http://13.81.34.152:1101/resource/authority/health-theme/REPRODUCTIVE_HEALTH",
    "sistemas de salud, calidad, modelos de atención y determinantes": "http://13.81.34.152:1101/resource/authority/health-theme/HEALTH_SYSTEMS",
    "uso de sustancias mentales, neurológicas y": "http://13.81.34.152:1101/resource/authority/health-theme/MENTAL_HEALTH",
}

FREQUENCIES = {
    "anual": "http://publications.europa.eu/resource/authority/frequency/ANNUAL",
    "bienal": "http://publications.europa.eu/resource/authority/frequency/BIENNIAL",
    "bimensual": "http://publications.europa.eu/resource/authority/frequency/MONTHLY_2",
    "bimestral": "http://publications.europa.eu/resource/authority/frequency/BIMONTHLY",
    "bisemanal": "http://publications.europa.eu/resource/authority/frequency/WEEKLY_2",
    "continuo": "http://publications.europa.eu/resource/authority/frequency/CONT",
    "continuamente actualizado": "http://publications.europa.eu/resource/authority/frequency/UPDATE_CONT",
    "cuatrimestral": "http://publications.europa.eu/resource/authority/frequency/ANNUAL_3",
    "diario": "http://publications.europa.eu/resource/authority/frequency/DAILY",
    "dos veces al día": "http://publications.europa.eu/resource/authority/frequency/DAILY_2",
    "en función de las necesidades": "http://publications.europa.eu/resource/authority/frequency/AS_NEEDED",
    "irregular": "http://publications.europa.eu/resource/authority/frequency/IRREG",
    "mensual": "http://publications.europa.eu/resource/authority/frequency/MONTHLY",
    "no previsto": "http://publications.europa.eu/resource/authority/frequency/NOT_PLANNED",
    "nunca": "http://publications.europa.eu/resource/authority/frequency/NEVER",
    "otro": "http://publications.europa.eu/resource/authority/frequency/OTHER",
    "quincenal": "http://publications.europa.eu/resource/authority/frequency/BIWEEKLY",
    "semanal": "http://publications.europa.eu/resource/authority/frequency/WEEKLY",
    "semestral": "http://publications.europa.eu/resource/authority/frequency/ANNUAL_2",
    "trimestral": "http://publications.europa.eu/resource/authority/frequency/QUARTERLY",
    "trienal": "http://publications.europa.eu/resource/authority/frequency/TRIENNIAL",
    "desconocido": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
}

ATTRIBUTION_ROLES = {
    "autor": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#author",
    "co autor": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#coAuthor",
    "colaborador": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#collaborator",
    "contribuyente": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#contributor",
    "custodio": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#custodian",
    "distribuidor": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#distributor",
    "editor": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#publisher",
    "financiador": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#funder",
    "investigador principal": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#principalInvestigator",
    "originador": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#originator",
    "propietario": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#owner",
    "punto de contacto": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#pointOfContact",
    "titular de los derechos": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#rightsHolder",
    "usuario": "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#user",
}

# Solo países más relevantes para datasets sanitarios europeos
SPATIAL_COUNTRIES = {
    "españa": "http://publications.europa.eu/resource/authority/country/ESP",
    "alemania": "http://publications.europa.eu/resource/authority/country/DEU",
    "francia": "http://publications.europa.eu/resource/authority/country/FRA",
    "italia": "http://publications.europa.eu/resource/authority/country/ITA",
    "portugal": "http://publications.europa.eu/resource/authority/country/PRT",
    "países bajos": "http://publications.europa.eu/resource/authority/country/NLD",
    "bélgica": "http://publications.europa.eu/resource/authority/country/BEL",
    "suecia": "http://publications.europa.eu/resource/authority/country/SWE",
    "finlandia": "http://publications.europa.eu/resource/authority/country/FIN",
    "dinamarca": "http://publications.europa.eu/resource/authority/country/DNK",
    "noruega": "http://publications.europa.eu/resource/authority/country/NOR",
    "austria": "http://publications.europa.eu/resource/authority/country/AUT",
    "suiza": "http://publications.europa.eu/resource/authority/country/CHE",
    "polonia": "http://publications.europa.eu/resource/authority/country/POL",
    "irlanda": "http://publications.europa.eu/resource/authority/country/IRL",
    "grecia": "http://publications.europa.eu/resource/authority/country/GRC",
    "república checa": "http://publications.europa.eu/resource/authority/country/CZE",
    "rumanía": "http://publications.europa.eu/resource/authority/country/ROU",
    "hungría": "http://publications.europa.eu/resource/authority/country/HUN",
    "unión europea": "http://publications.europa.eu/resource/authority/country/EUR",
    "reino unido": "http://publications.europa.eu/resource/authority/country/GBR",
    "estados unidos": "http://publications.europa.eu/resource/authority/country/USA",
    "canada": "http://publications.europa.eu/resource/authority/country/CAN",
}


relevant_vocab = {
    "languages": LANGUAGES,
    "personal_data_types": PERSONAL_DATA_TYPES,

    "publisher_types": PUBLISHER_TYPES,
    "health_categories": HEALTH_CATEGORIES,
    "themes": THEMES,
    "dataset_types": DATASET_TYPES,

    "health_activities": HEALTH_ACTIVITIES,
    "health_themes": HEALTH_THEMES,
    "frequencies": FREQUENCIES,
    "attribution_roles": ATTRIBUTION_ROLES,

    "spatial_countries": SPATIAL_COUNTRIES,
}
def build_vocabularies(relevant_vocab: dict) -> dict:
    pub_types_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["publisher_types"].items())
    health_cats_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["health_categories"].items())
    themes_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["themes"].items())
    dataset_types_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["dataset_types"].items())
    languages_str = "\n".join(f"    {l} → {u}" for l, u in LANGUAGES.items())

    personal_data_compact = " | ".join(uri.split("#")[-1] for uri in PERSONAL_DATA_TYPES.values())
    health_activities_compact = " | ".join(uri.split("/")[-1] for uri in HEALTH_ACTIVITIES.values())
    health_themes_compact = " | ".join(uri.split("/")[-1] for uri in HEALTH_THEMES.values())
    frequencies_compact = " | ".join(uri.split("/")[-1] for uri in FREQUENCIES.values())
    attribution_roles_compact = " | ".join(uri.split("#")[-1] for uri in ATTRIBUTION_ROLES.values())
    spatial_compact = " | ".join(uri.split("/")[-1] for uri in SPATIAL_COUNTRIES.values())

    return {
        "pub_types_str": pub_types_str,
        "health_cats_str": health_cats_str,
        "themes_str": themes_str,
        "dataset_types_str": dataset_types_str,
        "languages_str": languages_str,
        "personal_data_compact": personal_data_compact,
        "health_activities_compact": health_activities_compact,
        "health_themes_compact": health_themes_compact,
        "frequencies_compact": frequencies_compact,
        "attribution_roles_compact": attribution_roles_compact,
        "spatial_compact": spatial_compact,
    }
vocabs = build_vocabularies(relevant_vocab)

FIELD_INSTRUCTIONS = {

    #  access_rights 
    "access_rights": (
        "Para el campo 'access_rights', analiza la descripción y devuelve SOLO la URI:\n"
        "- Público → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
        "- Restringido → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
        "- No público → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        "IMPORTANTE:\n"
        "- RESTRINGIDO = acceso bajo condiciones\n"
        "- NO PÚBLICO = no accesible externamente\n"
    ),
    #  Título 
    "title": (
        "Para el campo 'title', devuelve el título del dataset como string.\n"
    ),
    #  Identificador 
    "identifier": (
        "Para el campo 'identifier', devuelve el DOI o identificador único del dataset.\n"
    ),
    #  Notas del editor 
    "publisher_note": (
        "Para el campo 'publisher_note', devuelve ARRAY de strings con notas del editor.\n"
    ),
    #  Organismo de calidad 
    "quality_annotation": (
        "Para el campo 'quality_annotation', devuelve objeto con: "
        "body (URI), target (URI o string), motivated_by (URI o string).\n"
    ),
    #  notes 
    "notes": (
        "Para el campo 'notes', devuelve la descripción completa literal (máx 300 caracteres).\n"
    ),
    #  health_category 
    "health_category": (
        "Para el campo 'health_category', devuelve un ARRAY de URIs:\n"
        f"{vocabs['health_cats_str']}\n"
    ),

    # theme 
    "theme": (
        "Para el campo 'theme', devuelve un ARRAY de URIs:\n"
        f"{vocabs['themes_str']}\n"
    ),

    # dcat_type 
    "dcat_type": (
        "Para el campo 'dcat_type', devuelve una URI:\n"
        f"{vocabs['dataset_types_str']}\n"
    ),

    # keyword 
    "keyword": (
        "Para el campo 'keyword', devuelve un ARRAY de strings.\n"
    ),

    # provenance 
    "provenance": (
        "Para el campo 'provenance', devuelve el origen de los datos.\n"
    ),

    # contact
    "contact": (
        "Para el campo 'contact', devuelve objeto con: email, url\n"
    ),

    # hdab 
    "hdab": (
        "Para el campo 'hdab', devuelve objeto con:\n"
        "name, type (URI), email, telephone, contact\n" 
    ),

    # purpose 
    "purpose": (
        "Para el campo 'purpose', devuelve texto libre.\n"
    ),

    # language 
    "language": (
        "Para el campo 'language', devuelve ARRAY de URIs:\n"
        f"{vocabs['languages_str']}\n"
    ),

    # population_coverage 
    "population_coverage": (
        "Para el campo 'population_coverage', devuelve ARRAY de strings.\n"
    ),

    # numéricos 
    "number_of_unique_individuals": "Devuelve un entero o null.\n",
    "number_of_records": "Devuelve un entero o null.\n",
    "min_typical_age": "Devuelve un entero o null.\n",
    "max_typical_age": "Devuelve un entero o null.\n",

    # personal_data
    "personal_data": (
        "Para el campo 'personal_data', devuelve ARRAY de códigos:\n"
        f"{vocabs['personal_data_compact']}\n"
    ),

    # legal_basis 
    "legal_basis": (
        "Devuelve objeto: description, source.\n"
    ),

    # retention_period 
    "retention_period": (
        "Devuelve objeto: start, end.\n"
    ),

    # coding_system 
    "coding_system": (
        "Devuelve objeto: uri, label.\n"
    ),

    # health_theme
    "health_theme": (
        "Devuelve ARRAY de códigos:\n"
        f"{vocabs['health_themes_compact']}\n"
    ),

    # code_values 
    "code_values": (
        "Devuelve ARRAY de strings.\n"
    ),

    # publisher 
    "publisher": (
        "Devuelve objeto con:\n"
        "name, type, email, telephone, contact_page\n"
    ),

    # creator 
    "creator": (
        "Devuelve objeto con:\n"
        "name, email, url, type\n"
    ),

    # qualified_attribution 
    "qualified_attribution": (
        "Devuelve objeto con role:\n"
        f"{vocabs['attribution_roles_compact']}\n"
    ),

    # was_generated_by 
    "was_generated_by": (
        "Devuelve ARRAY de códigos:\n"
        f"{vocabs['health_activities_compact']}\n"
    ),

    # spatial 
    "spatial": (
        "Devuelve ARRAY de códigos:\n"
        f"{vocabs['spatial_compact']}\n"
    ),

    # temporal_coverage 
    "temporal_coverage": (
        "Devuelve objeto: start, end.\n"
    ),

    # temporal_resolution 
    "temporal_resolution": (
        "Devuelve string (ej: P1D, PT1H).\n"
    ),

    # spatial_resolution_in_meters 
    "spatial_resolution_in_meters": (
        "Devuelve entero.\n"
    ),

    # frequency 
    "frequency": (
        "Devuelve código:\n"
        f"{vocabs['frequencies_compact']}\n"
    ),

    # issued 
    "issued": "Devuelve fecha YYYY-MM-DD.\n",

    # modified 
    "modified": "Devuelve fecha YYYY-MM-DD.\n",

    # alternate_identifier 
    "alternate_identifier": (
        "Devuelve ARRAY de strings.\n"
    ),

    # conforms_to
    "conforms_to": (
        "Devuelve objeto: uri, label.\n"
    ),

    # related_resource 
    "related_resource": (
        "Devuelve objeto: uri, label.\n"
    ),

    # is_referenced_by 
    "is_referenced_by": (
        "Devuelve ARRAY de strings.\n"
    ),

    # url 
    "url": "Devuelve URL.\n",

    # access_url 
    "access_url": "Devuelve URL.\n",

    # license 
    "license": (
        "Devuelve nombre o URL de licencia.\n"
    ),

    # format 
    "format": "Devuelve formato (CSV, JSON, etc).\n",

    # mimetype 
    "mimetype": "Devuelve MIME type.\n",

    # compress_format 
    "compress_format": "Devuelve formato compresión.\n",

    # package_format 
    "package_format": "Devuelve formato empaquetado.\n",

    # size 
    "size": "Devuelve tamaño en bytes.\n",

    # hash 
    "hash": "Devuelve hash.\n",

    # hash_algorithm 
    "hash_algorithm": "Devuelve algoritmo hash.\n",

    # rights 
    "rights": "Devuelve descripción.\n",

    # availability 
    "availability": "Devuelve descripción.\n",

    # status 
    "status": (
        "Devuelve URI:\n"
        "- Completed\n"
        "- UnderDevelopment\n"
        "- Deprecated\n"
        "- Withdrawn\n"
    ),

    # documentation
    "documentation": (
        "Devuelve objeto: uri, label.\n"
    ),

    #  version 
    "version": "Devuelve string versión.\n",

    # has_version 
    "has_version": "Devuelve ARRAY strings.\n",

    # version_notes
    "version_notes": "Devuelve string.\n",
}

def build_prompt_for_block(schema: HealthDCATAPSchema, block: dict, user_context: str = "") -> str:
    fields = ", ".join(block["fields"])

    # Instrucciones base (siempre presentes)
    instrucciones = (
        "Devuelve SOLO JSON válido. Las listas como arrays JSON. "
        "REGLA MÁS IMPORTANTE: Si el usuario NO menciona explícitamente un campo, "
        "devuelve null para ese campo. NUNCA deduzcas, infieras ni inventes valores. "
        "Solo rellena un campo si el usuario ha proporcionado información DIRECTA sobre él. "
        "Si hay duda, devuelve null.\n"
    )

    for field in block["fields"]:
        if field in FIELD_INSTRUCTIONS:
            instrucciones += FIELD_INSTRUCTIONS[field]

    instrucciones += "No añadas claves extra ni texto fuera del JSON."

    return (
        f"Extrae los campos de metadatos del siguiente texto.\n"
        f"Claves esperadas: [{fields}]\n"
        f"{instrucciones}\n"
        f"Texto del usuario: {user_context}"
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
