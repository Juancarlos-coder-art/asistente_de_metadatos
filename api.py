"""
api.py — Backend FastAPI para el Asistente HealthDCAT-AP
"""
from dotenv import load_dotenv
load_dotenv()

import json
import uuid
import os
import sys
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, Cookie, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader
import io
# AÑADIR junto a los otros imports
from rdflib import Graph
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from assistant.rag_helper import get_block_missing, get_missing_descriptions, FIELD_INDEX
from cli import BLOCKS, build_prompt_for_block, build_contract
from rdflib import Graph, URIRef, Literal, Namespace, RDF, XSD
from fastapi.responses import Response as FastAPIResponse
from google.cloud import bigquery

BQ_PROJECT = "peaceful-oath-492814-j5"
BQ_DATASET = "analytics"  
BQ_TABLE = "llm_usage"               

bq_client = bigquery.Client(project=BQ_PROJECT)
LIMITE_TOKENS_SESION = 10_000
LIMITE_TOKENS_DIA = 100_000

def check_token_limits(sid: str):
    """
    Comprueba los límites de tokens por sesión y por día.
    Lanza HTTPException 429 si se supera alguno.
    """
    try:
        table = os.getenv("BQ_USAGE_TABLE", f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")

        # Tokens consumidos por esta sesión hoy
        query_sesion = f"""
            SELECT COALESCE(SUM(total_tokens), 0) as tokens
            FROM `{table}`
            WHERE session_id = '{sid}'
            AND DATE(ts) = CURRENT_DATE()
        """
        resultado_sesion = list(bq_client.query(query_sesion).result())
        tokens_sesion = resultado_sesion[0].tokens if resultado_sesion else 0

        if tokens_sesion >= LIMITE_TOKENS_SESION:
            raise HTTPException(
                status_code=429,
                detail=f"Has superado el límite de {LIMITE_TOKENS_SESION:,} tokens por sesión. Inténtalo mañana."
            )

        # Tokens consumidos en total hoy (todas las sesiones)
        query_dia = f"""
            SELECT COALESCE(SUM(total_tokens), 0) as tokens
            FROM `{table}`
            WHERE DATE(ts) = CURRENT_DATE()
        """
        resultado_dia = list(bq_client.query(query_dia).result())
        tokens_dia = resultado_dia[0].tokens if resultado_dia else 0

        if tokens_dia >= LIMITE_TOKENS_DIA:
            raise HTTPException(
                status_code=429,
                detail=f"El servicio ha alcanzado el límite diario de {LIMITE_TOKENS_DIA:,} tokens. Disponible mañana."
            )

    except HTTPException:
        raise
    except Exception as e:
        # Si BigQuery falla, no bloqueamos al usuario
        print(f"[WARN] No se pudo comprobar límites de tokens: {e}")

# ── yoda_extractor: hacer importable el paquete (carpeta en raíz del repo) ──
_YODA_DIR = Path(__file__).resolve().parent / "yoda_extractor"
if str(_YODA_DIR) not in sys.path:
    sys.path.insert(0, str(_YODA_DIR))

app = FastAPI(title="Asistente HealthDCAT-AP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_schema = HealthDCATAPSchema("health_dcat_ap.yaml")
sessions: dict = {}

ENDS_NON_PUBLIC_URI = "https://catalogo.ends.gob.es/dataset"
NON_PUBLIC_URI = "http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC"

# ── Vocabularios para mapeo dirigido ──
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

def get_session(session_id, response):
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    new_id = str(uuid.uuid4())
    sessions[new_id] = MetadataState("health_dcat_ap.yaml")
    response.set_cookie(key="session_id", value=new_id, httponly=True, samesite="none", secure=True, max_age=60*60*8)
    return new_id, sessions[new_id]


def _summarize_blocks(metadata: dict):
    results_by_block = {}
    for block in BLOCKS:
        block_result = {}
        block_filled = 0
        for field in block["fields"]:
            value = metadata.get(field)
            block_result[field] = value
            if value is not None and value != "" and value != []:
                block_filled += 1

        results_by_block[block["name"]] = {
            "fields": block_result,
            "filled": block_filled,
            "total": len(block["fields"]),
            "complete": block_filled == len(block["fields"]),
        }

    return results_by_block


def _extract_metadata_payload(payload):
    if isinstance(payload, dict):
        if isinstance(payload.get("metadata"), dict):
            return payload["metadata"]
        if isinstance(payload.get("data"), dict):
            return payload["data"]
    return payload


def apply_conditional_logic(state: MetadataState):
    ar = state.data.get("access_rights", "")
    if ar and "NON_PUBLIC" in str(ar).upper():
        state.data["identifier"] = ENDS_NON_PUBLIC_URI
        state.data["access_url"] = ENDS_NON_PUBLIC_URI


def _extract_choices(choices_list, lang="es"):
    result = []
    for ch in (choices_list or []):
        lbl = ch.get("label", {})
        if isinstance(lbl, dict):
            label_val = lbl.get(lang, lbl.get("es", ch.get("value", "")))
        else:
            label_val = str(lbl)
        result.append({"value": ch.get("value", ""), "label": label_val})
    return result


def _extract_subfields(subfields_list):
    result = []
    for sf in (subfields_list or []):
        sf_name = sf.get("field_name")
        raw_label = (sf.get("label", {}).get("es", sf_name)
                     if isinstance(sf.get("label"), dict)
                     else str(sf.get("label", sf_name)))
        if sf_name and sf_name.startswith("special_opening_hours"):
            raw_label = f"Horario especial – {raw_label}"
        elif sf_name and sf_name.startswith("opening_hours"):
            raw_label = f"Horario habitual – {raw_label}"
        entry = {"field_name": sf_name, "label": raw_label, "required": sf.get("required", False)}
        if sf.get("choices"):
            entry["choices"] = _extract_choices(sf["choices"])
        result.append(entry)
    return result


def _classify_document(text: str) -> dict:
    prompt = (
        f"Analiza este documento sanitario y responde SOLO con un JSON con estas claves:\n"
        f"- 'idioma': idioma del documento ('es' o 'en')\n"
        f"- 'tipo_organismo': tipo de organismo mencionado\n"
        f"- 'categorias_salud': lista de categorías sanitarias\n"
        f"- 'temas': lista de temas principales\n"
        f"- 'tipo_dataset': tipo de dataset\n"
        f"Usa SOLO etiquetas simples, sin URIs.\n"
        f"Documento:\n{text[:2000]}"
    )
    try:
        return call_llm(
            prompt,
            {
                "idioma": None,
                "tipo_organismo": None,
                "categorias_salud": None,
                "temas": None,
                "tipo_dataset": None
            },
            text[:2000],
            endpoint="/classify_document",
            session_id=None,
            extra_json={"source": "classifier"}
        )
    except Exception:
        return {}

def _build_relevant_vocab(classification: dict) -> dict:
    relevant = {"publisher_types": {}, "health_categories": {}, "themes": {}, "dataset_types": {}}

    # Traducción simple EN→ES para clasificación
    tipo_org = str(classification.get("tipo_organismo", "")).lower()
    
    cats_raw = classification.get("categorias_salud") or []
    cats = [str(c).lower() for c in cats_raw]

    temas_raw = classification.get("temas") or []
    temas = [str(t).lower() for t in temas_raw]

    tipo_ds = str(classification.get("tipo_dataset", "")).lower()

    # Mapeo EN→ES para temas frecuentes
    EN_TO_ES_THEMES = {
        "health": "salud", "science": "ciencia", "technology": "ciencia",
        "population": "población", "society": "sociedad",
        "government": "gobierno", "education": "educación",
        "economy": "economía", "environment": "medio ambiente",
        "agriculture": "agricultura", "transport": "transporte",
        "justice": "justicia", "regions": "regiones",
        "international": "asuntos internacionales", "energy": "energía",
    }
    temas_es = []
    for t in temas:
        temas_es.append(t)
        for en, es in EN_TO_ES_THEMES.items():
            if en in t:
                temas_es.append(es)

    # Mapeo EN→ES para tipos de dataset
    EN_TO_ES_DATASET = {
        "statistical": "datos estadísticos", "geospatial": "datos geoespaciales",
        "synthetic": "datos sintéticos", "ontology": "ontología",
        "schema": "esquema", "glossary": "glosario", "thesaurus": "tesauro",
        "taxonomy": "taxonomía", "directory": "directorio",
    }
    tipo_ds_es = tipo_ds
    for en, es in EN_TO_ES_DATASET.items():
        if en in tipo_ds:
            tipo_ds_es = es
            break

    for label, uri in PUBLISHER_TYPES.items():
        if any(word in tipo_org for word in label.split()):
            relevant["publisher_types"][label] = uri
    if not relevant["publisher_types"]:
        relevant["publisher_types"] = dict(list(PUBLISHER_TYPES.items())[:5])

    for label, uri in HEALTH_CATEGORIES.items():
        if any(word in " ".join(cats) for word in label.split()[:2]):
            relevant["health_categories"][label] = uri
    if not relevant["health_categories"]:
        relevant["health_categories"] = dict(list(HEALTH_CATEGORIES.items())[:5])

    for label, uri in THEMES.items():
        if label in " ".join(temas_es):
            relevant["themes"][label] = uri
    if not relevant["themes"]:
        relevant["themes"] = {"salud": THEMES["salud"]}

    for label, uri in DATASET_TYPES.items():
        if label in tipo_ds_es:
            relevant["dataset_types"][label] = uri
    if not relevant["dataset_types"]:
        relevant["dataset_types"] = {"datos estadísticos": DATASET_TYPES["datos estadísticos"]}

    return relevant

def _extract_fields_smart(text: str, all_fields: list, relevant_vocab: dict, existing_access_rights: str = None, doc_lang: str = "es") -> dict:

    # ── Vocabularios relevantes (completos con URI) ──
    pub_types_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["publisher_types"].items())
    health_cats_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["health_categories"].items())
    themes_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["themes"].items())
    dataset_types_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["dataset_types"].items())
    languages_str = "\n".join(f"    {l} → {u}" for l, u in LANGUAGES.items())

    # ── Vocabularios compactos (solo códigos) ──
    personal_data_compact = " | ".join(uri.split("#")[-1] for uri in PERSONAL_DATA_TYPES.values())
    health_activities_compact = " | ".join(uri.split("/")[-1] for uri in HEALTH_ACTIVITIES.values())
    health_themes_compact = " | ".join(uri.split("/")[-1] for uri in HEALTH_THEMES.values())
    frequencies_compact = " | ".join(uri.split("/")[-1] for uri in FREQUENCIES.values())
    attribution_roles_compact = " | ".join(uri.split("#")[-1] for uri in ATTRIBUTION_ROLES.values())
    spatial_compact = " | ".join(uri.split("/")[-1] for uri in SPATIAL_COUNTRIES.values())

    if doc_lang == "en":
        access_rights_section = (
            f"- 'access_rights' → ALREADY SET BY USER: '{existing_access_rights}'. Return exactly this value.\n"
            if existing_access_rights else
            f"- 'access_rights' → access level URI:\n"
            f"    Public → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
            f"    Restricted → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
            f"    Non-public → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        )
        prompt = (
            f"Extract metadata fields from this health document.\n"
            f"RULES: Return ONLY valid JSON. null if not found in the text.\n\n"
            f"MAPPING:\n"
            f"- 'title' → dataset title\n"
            f"- 'notes' → full description. Copy literally, do not summarize. Max 300 chars.\n"
            f"- 'identifier' → DOI or unique identifier\n"
            f"{access_rights_section}"
            f"- 'hdab' → body managing data access. Object: name, email, telephone, contact_page, type (URI).\n"
            f"  Types:\n{pub_types_str}\n"
            f"- 'health_category' → array of URIs:\n{health_cats_str}\n"
            f"- 'theme' → array of URIs:\n{themes_str}\n"
            f"- 'dcat_type' → URI:\n{dataset_types_str}\n"
            f"- 'provenance' → data origin. Free text.\n"
            f"- 'keyword' → keywords. Array of strings.\n"
            f"- 'contact' → object: email, url\n"
            f"- 'purpose' → purpose. Array of strings.\n"
            f"- 'language' → array of language URIs:\n{languages_str}\n"
            f"- 'population_coverage' → population coverage. Array of strings.\n"
            f"- 'number_of_unique_individuals' → integer or null\n"
            f"- 'number_of_records' → integer or null\n"
            f"- 'min_typical_age' → integer or null\n"
            f"- 'max_typical_age' → integer or null\n"
            f"- 'personal_data' → array of codes. Choose from: {personal_data_compact}\n"
            f"  URI: https://w3id.org/dpv/pd#{{CODE}}\n"
            f"- 'code_values' → coded values (e.g. A00-B99). Array of strings. null if not mentioned.\n"
            f"- 'publisher_note' → publisher notes. Array of strings. null if not mentioned.\n"
            f"- 'qualified_attribution' → object: qualified_attribution_agent_name, qualified_attribution_agent_type (URI),\n"
            f"  qualified_attribution_agent_contact_page (URL or null), qualified_attribution_agent_email (string or null),\n"
            f"  qualified_attribution_role (URI). Role codes: {attribution_roles_compact}\n"
            f"- 'quality_annotation' → object: body (URI of the quality body), target (URI or string), motivated_by (motivation URI or string). null if not mentioned.\n"
            f"  Role URI: https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#{{CODE}}\n"
            f"- 'was_generated_by' → array of activity codes. Choose from: {health_activities_compact}\n"
            f"  URI: http://13.81.34.152:1101/resource/authority/health-activity/{{CODE}}\n"
            f"- 'temporal_resolution' → min temporal resolution (P1D, PT1H). String. null if not mentioned.\n"
            f"- 'spatial_resolution_in_meters' → integer. null if not mentioned.\n"
            f"- 'issued' → publication date (YYYY-MM-DD). null if not mentioned.\n"
            f"- 'modified' → last modification date (YYYY-MM-DD). null if not mentioned.\n"
            f"- 'alternate_identifier' → alternative identifiers. Array of strings. null if not mentioned.\n"
            f"- 'conforms_to' → standard conformance. Object: uri (URI), label (name). null if not mentioned.\n"
            f"- 'related_resource' → related resource. Object: uri (URI), label (name). null if not mentioned.\n"
            f"- 'is_referenced_by' → referencing resources. Array of strings (URIs). null if not mentioned.\n"
            f"- 'url' → landing page URL. String. null if not mentioned.\n"
            f"- 'documentation' → documentation. Object: uri (URI), label (name). null if not mentioned.\n"
            f"- 'has_version' → available versions. Array of strings. null if not mentioned.\n"
            f"- 'version_notes' → version notes. Free text. null if not mentioned.\n"
            f"- 'legal_basis' → legal basis. Object: description (text), source (text). null if not mentioned.\n"
            f"- 'coding_system' → coding systems (ICD-10, SNOMED CT...). Object: uri (URI), label (name). null if not mentioned.\n"
            f"- 'health_theme' → array of health theme codes. Choose from: {health_themes_compact}\n"
            f"  URI: http://13.81.34.152:1101/resource/authority/health-theme/{{CODE}}\n"
            f"- 'publisher' → object: name, type (URI), email, telephone, contact_page,\n"
            f"- 'creator' → object: name, type (URI), email, url. null if not mentioned.\n"
            f"- 'spatial' → array of country codes. Choose from: {spatial_compact}\n"
            f"  URI: http://publications.europa.eu/resource/authority/country/{{CODE}}\n"
            f"- 'frequency' → frequency code. Choose from: {frequencies_compact}\n"
            f"  URI: http://publications.europa.eu/resource/authority/frequency/{{CODE}}\n"
            f"- 'temporal_coverage' → object: start (YYYY-MM-DD), end (YYYY-MM-DD). null if not mentioned.\n"
            f"- 'version' → dataset version. String. null if not mentioned.\n"
            # ── Distribución ──
            f"- 'access_url' → distribution access URL. String. null if not mentioned.\n"
            f"- 'download_url' → direct download URL. String. null if not mentioned.\n"
            f"- 'name' → distribution resource name. String. null if not mentioned.\n"
            f"- 'description' → distribution resource description. String. null if not mentioned.\n"
            f"- 'format' → file format (CSV, JSON, XML, XLSX, Parquet, RDF, GeoJSON...). String. null if not mentioned.\n"
            f"- 'mimetype' → media type (text/csv, application/json, application/xml...). String. null if not mentioned.\n"
            f"- 'compress_format' → compression format (zip, gzip, bzip2, 7z...). String. null if not mentioned.\n"
            f"- 'package_format' → packaging format (zip, tar, tar.gz...). String. null if not mentioned.\n"
            f"- 'size' → file size in bytes. Integer. null if not mentioned.\n"
            f"- 'hash' → file integrity hash value. String. null if not mentioned.\n"
            f"- 'hash_algorithm' → hash algorithm (MD5, SHA-256, SHA-512...). String. null if not mentioned.\n"
            f"- 'rights' → usage rights description. String. null if not mentioned.\n"
            f"- 'availability' → resource availability description. String. null if not mentioned.\n"
            f"- 'status' → resource status URI:\n"
            f"    Completed → http://purl.org/adms/status/Completed\n"
            f"    Under development → http://purl.org/adms/status/UnderDevelopment\n"
            f"    Deprecated → http://purl.org/adms/status/Deprecated\n"
            f"    Withdrawn → http://purl.org/adms/status/Withdrawn\n"
            f"  null if not mentioned.\n"
            f"- 'license' → licence URL or name (CC BY 4.0, CC BY-NC 4.0, CC0, ODbL...). String. null if not mentioned.\n"
            f"\nDocument:\n{text[:5000]}"
        )
    else:
        access_rights_section = (
            f"- 'access_rights' → YA DEFINIDO: '{existing_access_rights}'. Devuelve exactamente este valor.\n"
            if existing_access_rights else
            f"- 'access_rights' → nivel de acceso URI:\n"
            f"    Público → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
            f"    Restringido → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
            f"    No público → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        )
        prompt = (
            f"Extrae campos de metadatos de este documento sanitario.\n"
            f"REGLAS: Devuelve SOLO JSON válido. null si no aparece en el texto.\n\n"
            f"MAPEO:\n"
            f"- 'title' → título del dataset\n"
            f"- 'notes' → descripción completa. Cópiala literalmente. Máx 300 caracteres.\n"
            f"- 'identifier' → DOI o identificador único\n"
            f"{access_rights_section}"
            f"- 'hdab' → organismo gestor del acceso. Objeto: name, email, telephone, contact_page, type (URI).\n"
            f"  Tipos:\n{pub_types_str}\n"
            f"- 'health_category' → array de URIs:\n{health_cats_str}\n"
            f"- 'theme' → array de URIs:\n{themes_str}\n"
            f"- 'dcat_type' → URI:\n{dataset_types_str}\n"
            f"- 'provenance' → origen de los datos. Texto libre.\n"
            f"- 'keyword' → palabras clave. Array de strings.\n"
            f"- 'contact' → objeto: email, url\n"
            f"- 'purpose' → finalidad. Array de strings.\n"
            f"- 'language' → array de URIs de idiomas:\n{languages_str}\n"
            f"- 'population_coverage' → cobertura poblacional. Array de strings.\n"
            f"- 'number_of_unique_individuals' → número entero o null\n"
            f"- 'number_of_records' → número entero o null\n"
            f"- 'min_typical_age' → número entero o null\n"
            f"- 'max_typical_age' → número entero o null\n"
            f"- 'personal_data' → array de códigos. Elige entre: {personal_data_compact}\n"
            f"  URI: https://w3id.org/dpv/pd#{{CÓDIGO}}\n"
            f"- 'code_values' → valores codificados (ej: A00-B99). Array de strings. null si no se menciona.\n"
            f"- 'publisher_note' → notas del editor. Array de strings. null si no se menciona.\n"
            f"- 'qualified_attribution' → objeto con EXACTAMENTE estas claves:\n"
            f"  qualified_attribution_agent_name (string), qualified_attribution_agent_type (URI),\n"
            f"  qualified_attribution_agent_contact_page (URL o null), qualified_attribution_agent_email (string o null),\n"
            f"  qualified_attribution_role (URI). Códigos de rol: {attribution_roles_compact}\n"
            f"- 'quality_annotation' → objeto: body (URI del organismo de calidad), target (URI o string), motivated_by (motivación URI o string). null si no se menciona.\n"
            f"  URI rol: https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#{{CÓDIGO}}\n"
            f"- 'was_generated_by' → array de códigos de actividad. Elige entre: {health_activities_compact}\n"
            f"  URI: http://13.81.34.152:1101/resource/authority/health-activity/{{CÓDIGO}}\n"
            f"- 'temporal_resolution' → resolución temporal mínima (P1D, PT1H). String. null si no se menciona.\n"
            f"- 'spatial_resolution_in_meters' → entero. null si no se menciona.\n"
            f"- 'issued' → fecha publicación (YYYY-MM-DD). null si no se menciona.\n"
            f"- 'modified' → fecha modificación (YYYY-MM-DD). null si no se menciona.\n"
            f"- 'alternate_identifier' → identificadores alternativos. Array de strings. null si no se menciona.\n"
            f"- 'conforms_to' → conformidad con estándar. Objeto: uri (URI del estándar), label (nombre). null si no se menciona.\n"
            f"- 'related_resource' → recurso relacionado. Objeto: uri (URI), label (nombre). null si no se menciona.\n"
            f"- 'is_referenced_by' → recursos que referencian. Array de strings (URIs). null si no se menciona.\n"
            f"- 'url' → URL de entrada (landing page). String. null si no se menciona.\n"
            f"- 'documentation' → documentación. Objeto: uri (URI), label (nombre). null si no se menciona.\n"
            f"- 'has_version' → versiones disponibles. Array de strings. null si no se menciona.\n"
            f"- 'version_notes' → notas de versión. Texto libre. null si no se menciona.\n"
            f"- 'legal_basis' → base jurídica. Objeto: description (texto), source (texto). null si no se menciona.\n"
            f"- 'coding_system' → sistema de codificación (ICD-10, SNOMED CT...). Objeto: uri (URI), label (nombre). null si no se menciona.\n"
            f"- 'health_theme' → array de códigos de tema de salud. Elige entre: {health_themes_compact}\n"
            f"  URI: http://13.81.34.152:1101/resource/authority/health-theme/{{CÓDIGO}}\n"
            f"- 'publisher' → objeto: name, type (URI), email, telephone, contact_page,\n"
            f"- 'creator' → objeto: name, type (URI), email, url. null si no se menciona.\n"
            f"- 'spatial' → array de códigos de país. Elige entre: {spatial_compact}\n"
            f"  URI: http://publications.europa.eu/resource/authority/country/{{CÓDIGO}}\n"
            f"- 'frequency' → código de frecuencia. Elige entre: {frequencies_compact}\n"
            f"  URI: http://publications.europa.eu/resource/authority/frequency/{{CÓDIGO}}\n"
            f"- 'temporal_coverage' → objeto: start (YYYY-MM-DD), end (YYYY-MM-DD). null si no se menciona.\n"
            f"- 'version' → versión del dataset. String. null si no se menciona.\n"
            # ── Distribución ──
            f"- 'access_url' → URL de acceso a la distribución. String. null si no se menciona.\n"
            f"- 'download_url' → URL de descarga directa. String. null si no se menciona.\n"
            f"- 'name' → nombre del recurso de distribución. String. null si no se menciona.\n"
            f"- 'description' → descripción del recurso de distribución. String. null si no se menciona.\n"
            f"- 'format' → formato del fichero (CSV, JSON, XML, XLSX, Parquet, RDF, GeoJSON...). String. null si no se menciona.\n"
            f"- 'mimetype' → tipo MIME (text/csv, application/json, application/xml...). String. null si no se menciona.\n"
            f"- 'compress_format' → formato de compresión (zip, gzip, bzip2, 7z...). String. null si no se menciona.\n"
            f"- 'package_format' → formato de empaquetado (zip, tar, tar.gz...). String. null si no se menciona.\n"
            f"- 'size' → tamaño en bytes. Entero. null si no se menciona.\n"
            f"- 'hash' → valor hash de integridad. String. null si no se menciona.\n"
            f"- 'hash_algorithm' → algoritmo hash (MD5, SHA-256, SHA-512...). String. null si no se menciona.\n"
            f"- 'rights' → descripción de derechos de uso. String. null si no se menciona.\n"
            f"- 'availability' → descripción de disponibilidad del recurso. String. null si no se menciona.\n"
            f"- 'status' → URI del estado del recurso:\n"
            f"    Completado → http://purl.org/adms/status/Completed\n"
            f"    En desarrollo → http://purl.org/adms/status/UnderDevelopment\n"
            f"    Obsoleto → http://purl.org/adms/status/Deprecated\n"
            f"    Retirado → http://purl.org/adms/status/Withdrawn\n"
            f"  null si no se menciona.\n"
            f"- 'license' → URL o nombre de licencia (CC BY 4.0, CC BY-NC 4.0, CC0, ODbL...). String. null si no se menciona.\n"
            f"\nDocumento:\n{text[:5000]}"
        )

    # ── Llamada al LLM ──
    result = call_llm(
        prompt,
        {f: None for f in all_fields},
        "",
        endpoint="/extract_fields",
        session_id=None,
        extra_json={"doc_lang": doc_lang}
    )

    # ── Convertir códigos cortos a URIs completas ──
    BASE_ACTIVITY = "http://13.81.34.152:1101/resource/authority/health-activity/"
    BASE_HEALTH_THEME = "http://13.81.34.152:1101/resource/authority/health-theme/"
    BASE_FREQUENCY = "http://publications.europa.eu/resource/authority/frequency/"
    BASE_COUNTRY = "http://publications.europa.eu/resource/authority/country/"
    BASE_DPV = "https://w3id.org/dpv/pd#"
    BASE_ROLE = "https://standards.iso.org/iso/19115/resources/Codelists/gml/CI_RoleCode.xml#"

    def expand_uris(value, base):
        if not value or not isinstance(value, list):
            return value
        return [item if str(item).startswith("http") else f"{base}{item}" for item in value if item]

    result["was_generated_by"] = expand_uris(result.get("was_generated_by"), BASE_ACTIVITY)
    result["health_theme"] = expand_uris(result.get("health_theme"), BASE_HEALTH_THEME)
    result["personal_data"] = expand_uris(result.get("personal_data"), BASE_DPV)
    result["spatial"] = expand_uris(result.get("spatial"), BASE_COUNTRY)

    if result.get("frequency") and not str(result["frequency"]).startswith("http"):
        result["frequency"] = f"{BASE_FREQUENCY}{result['frequency']}"

    if result.get("qualified_attribution") and isinstance(result["qualified_attribution"], dict):
        role = result["qualified_attribution"].get("qualified_attribution_role", "")
        if role and not str(role).startswith("http"):
            result["qualified_attribution"]["qualified_attribution_role"] = f"{BASE_ROLE}{role}"

    return result

# ── Modelos ──
class CompleteBlockRequest(BaseModel):
    block_id: int
    user_context: str

class ManualSaveRequest(BaseModel):
    block_id: int
    partial: dict

class ResetRequest(BaseModel):
    confirm: bool = True

class LegislationRequest(BaseModel):
    legislation: list


# ── Endpoints ──
_ALLOWED_ACCESS_RIGHTS = {"PUBLIC", "RESTRICTED", "NON_PUBLIC"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "Asistente HealthDCAT-AP"}


@app.get("/blocks")
def get_blocks():
    return [
        {
            "id": i,
            "name": b["name"],
            "name_en": b.get("name_en", b["name"]),
            "question": b["question"],
            "question_en": b.get("question_en", b["question"]),
            "fields": b["fields"],
            "hint": b.get("hint", ""),
            "hint_en": b.get("hint_en", b.get("hint", "")),
            "placeholder": b.get("placeholder", ""),
            "placeholder_en": b.get("placeholder_en", b.get("placeholder", "")),
        }
        for i, b in enumerate(BLOCKS)
    ]

@app.get("/blocks/{block_id}")
def get_block(block_id: int):
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    b = BLOCKS[block_id]
    return {"id": block_id, "name": b["name"], "question": b["question"], "fields": b["fields"]}

@app.get("/schema-info")
def get_schema_info(lang: str = "es"):
    field_map = {
        "access_rights": "Derechos de acceso",
        "hdab": "Organismo de acceso a datos de salud",
        "health_category": "health_category",
        "theme": "theme",
        "dcat_type": "dcat_type",
        "contact": "contact",
        "language": "language",
        "personal_data": "personal_data",
        "health_theme": "health_theme",
        "legal_basis": "legal_basis",
        "retention_period": "retention_period",
        "coding_system": "coding_system",
        "publisher": "publisher",
        "creator": "creator",
        "qualified_attribution": "qualified_attribution",
        "was_generated_by": "was_generated_by",
        "spatial": "spatial",
        "temporal_coverage": "temporal_coverage",
        "frequency": "frequency",
        "conforms_to": "conforms_to",
        "related_resource": "related_resource",
        "documentation": "documentation",
        "quality_annotation": "quality_annotation"
    }
    info = {}
    for field_key, yaml_field_name in field_map.items():
        schema_field = _schema.get_field(yaml_field_name)
        if not schema_field:
            continue
        entry = {}
        if schema_field.get("choices"):
            choices = _extract_choices(schema_field["choices"],lang=lang)
            if field_key == "access_rights":
                choices = [ch for ch in choices if ch["value"].rsplit("/", 1)[-1] in _ALLOWED_ACCESS_RIGHTS]
            entry["choices"] = choices
        if schema_field.get("repeating_subfields"):
            entry["subfields"] = _extract_subfields(schema_field["repeating_subfields"])
        if entry:
            info[field_key] = entry
    info["health_category"] = {
        "choices": [{"value": uri, "label": label} for label, uri in HEALTH_CATEGORIES.items()]
    }
    info["theme"] = {
        "choices": [{"value": uri, "label": label} for label, uri in THEMES.items()]
    }
    info["dcat_type"] = {
        "choices": [{"value": uri, "label": label} for label, uri in DATASET_TYPES.items()]
    }
    info["health_theme"] = {
        "choices": [{"value": uri, "label": label} for label, uri in HEALTH_THEMES.items()]
    }
    info["was_generated_by"] = {
        "choices": [{"value": uri, "label": label} for label, uri in HEALTH_ACTIVITIES.items()]
    }
    info["language"] = {
        "choices": [{"value": uri, "label": label} for label, uri in LANGUAGES.items()]
    }
    info["spatial"] = {
        "choices": [{"value": uri, "label": label} for label, uri in SPATIAL_COUNTRIES.items()]
    }
    info["frequency"] = {
        "choices": [{"value": uri, "label": label} for label, uri in FREQUENCIES.items()]
    }
    return info

@app.post("/complete/{block_id}")
def complete_block(block_id: int, body: CompleteBlockRequest, response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM no disponible.")
    check_token_limits(sid)
    if not body.user_context.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    check_token_limits(sid)  

    block = BLOCKS[block_id]
    try:
        prompt = build_prompt_for_block(_schema, block, body.user_context)
        contract = build_contract(block)
        ai_result = call_llm(
            prompt,
            contract,
            body.user_context,
            endpoint="/complete",
            session_id=sid,
            extra_json={"block_id": block_id}
        )
        partial = {name: ai_result.get(name, None) for name in block["fields"]}
        state.merge_partial(partial)
        apply_conditional_logic(state)
        return {"success": True, "partial": partial, "metadata": state.data, "session_id": sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-manual")
def save_manual(body: ManualSaveRequest, response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    if body.block_id < 0 or body.block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    block = BLOCKS[body.block_id]
    #convertir claves con punto (ej: hdab.contact_page) en objetos anidados
    raw_partial = {k: v for k, v in body.partial.items() if v not in (None, "", [])}
    to_merge = {}
    for k, v in raw_partial.items():
        if "." in k:
            parent, child = k.split(".", 1)
            to_merge.setdefault(parent, {})
            if isinstance(to_merge[parent], dict):
                to_merge[parent][child] = v
        else:
            to_merge[k] = v
    state.merge_partial(to_merge)
    missing_fields = [f for f in block["fields"] if not state.data.get(f)]
    ai_partial = {}
    if missing_fields and llm_available():
        check_token_limits(sid)
        try:
            user_context = f"Datos actuales:\n{json.dumps(state.data, ensure_ascii=False)}\nNuevos datos:\n{json.dumps(to_merge, ensure_ascii=False)}\nCompleta SOLO los campos faltantes."
            prompt = build_prompt_for_block(_schema, block, user_context)
            contract = {f: None for f in missing_fields}
            ai_result = call_llm(
                prompt,
                contract,
                user_context,
                endpoint="/save-manual",
                session_id=sid,
                extra_json={"block_id": body.block_id}
            )
            ai_partial = {k: v for k, v in ai_result.items() if k in missing_fields and v not in (None, "", [])}
            state.merge_partial(ai_partial)
        except Exception as e:
            print(f"[WARN] LLM error: {e}")
    apply_conditional_logic(state)
    return {"success": True, "metadata": state.data, "ai_completed": ai_partial, "session_id": sid}

@app.post("/save-legislation")
def save_legislation(body: LegislationRequest, response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    state.data["applicable_legislation"] = body.legislation
    return {"success": True, "metadata": state.data}

@app.get("/metadata")
def get_metadata(response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    return state.data

@app.get("/validate")
def validate(response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    errors = state.validate_types_basic()
    missing = state.missing_required()

    filled_required = total_required = 0
    filled_optional = total_optional = 0
    for field, info in FIELD_INDEX.items():
        is_filled = state.data.get(field) not in (None, "", [], {})
        if info.get("obligatorio", False):
            total_required += 1
            if is_filled:
                filled_required += 1
        else:
            total_optional += 1
            if is_filled:
                filled_optional += 1

    return {
        "valid": len(errors) == 0 and len(missing) == 0,
        "errors": errors,
        "missing_required": missing,
        "total_required": total_required,
        "filled_required": filled_required,
        "total_optional": total_optional,
        "filled_optional": filled_optional,
    }

@app.get("/missing/{block_id}")
def get_missing_fields(block_id: int, response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    block = BLOCKS[block_id]
    missing = get_block_missing(block, state.data, restrictions=state.restrictions)
    ar = state.data.get("access_rights", "")
    non_public = "NON_PUBLIC" in str(ar).upper()
    descriptions = get_missing_descriptions(missing, use_llm=False, is_non_public=non_public)
    return {"block_id": block_id, "missing_fields": missing, "descriptions": descriptions}

@app.post("/finalize")
def finalize(response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    if not state.data.get("applicable_legislation"):
        state.data["applicable_legislation"] = [
            {"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}
        ]

    DIST_FIELDS = [
        "access_url", "download_url", "name", "description",
        "format", "mimetype", "compress_format", "package_format",
        "size", "hash", "hash_algorithm", "rights", "availability",
        "status", "license", "retention_period",
    ]

    dist_data = {}
    for f in DIST_FIELDS:
        val = state.data.pop(f, None)
        if val not in (None, "", []):
            dist_data[f] = val

    if dist_data.get("access_url"):
        dist_data["applicable_legislation"] = state.data.get("applicable_legislation", [
            {"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}
        ])
        state.data["distribution"] = [dist_data]

    filename = f"metadata_output_{sid[:8]}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state.data, f, indent=2, ensure_ascii=False)

    # ── Envío a BigQuery ──
    try:
        table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
        row = {
            "session_id": sid,
            "extra_json": json.dumps(state.data, ensure_ascii=False)
        }
        errors = bq_client.insert_rows_json(table_ref, [row])
        if errors:
            print(f"[WARN] BigQuery insert errors: {errors}")
        else:
            print(f"[INFO] BigQuery: fila insertada para sesión {sid[:8]}")
    except Exception as e:
        print(f"[WARN] Error al escribir en BigQuery: {e}")

    return {"success": True, "metadata": state.data, "file": filename}

@app.get("/export-rdf")
async def export_rdf(
    fmt: str = "turtle",   # "turtle" o "xml"
    response: FastAPIResponse = None,
    session_id: str = Cookie(default=None)
):
    if fmt not in ("turtle", "xml"):
        raise HTTPException(status_code=400, detail="fmt debe ser 'turtle' o 'xml'")

    # Recuperar sesión sin crear una nueva
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    state = sessions[session_id]

    d = state.data
    if not d.get("title"):
        raise HTTPException(status_code=400, detail="No hay metadatos que exportar.")

    # ── Namespaces ──────────────────────────────────────────────────────────
    DCAT    = Namespace("http://www.w3.org/ns/dcat#")
    DCT     = Namespace("http://purl.org/dc/terms/")
    HEALTH  = Namespace("https://healthdcat-ap.eu/ns#")
    VCARD   = Namespace("http://www.w3.org/2006/vcard/ns#")
    PROV    = Namespace("http://www.w3.org/ns/prov#")

    g = Graph()
    g.bind("dcat",   DCAT)
    g.bind("dct",    DCT)
    g.bind("health", HEALTH)
    g.bind("vcard",  VCARD)
    g.bind("prov",   PROV)

    # URI del dataset
    dataset_uri = URIRef(
        d.get("identifier") or
        d.get("url") or
        f"https://catalogo.ends.gob.es/dataset/{session_id[:8]}"
    )
    g.add((dataset_uri, RDF.type, DCAT.Dataset))

    # ── Campos escalares simples ────────────────────────────────────────────
    SCALAR_MAP = {
        "title":                    (DCT.title,                  "es"),
        "notes":                    (DCT.description,            "es"),
        "identifier":               (DCT.identifier,             None),
        "provenance":               (DCT.provenance,             "es"),
        "version":                  (DCAT.version,               None),
        "version_notes":            (DCAT.versionNotes,          "es"),
        "legal_basis":              (DCT.license,                None),
        "retention_period":         (HEALTH.retentionPeriod,     "es"),
        "publisher_note":           (HEALTH.publisherNote,       "es"),
        "temporal_resolution":      (DCAT.temporalResolution,    None),
        "spatial_resolution_in_meters": (DCAT.spatialResolutionInMeters, None),
        "number_of_records":        (HEALTH.numberOfRecords,     None),
        "number_of_unique_individuals": (HEALTH.numberOfUniqueIndividuals, None),
        "min_typical_age":          (HEALTH.minTypicalAge,       None),
        "max_typical_age":          (HEALTH.maxTypicalAge,       None),
        "issued":                   (DCT.issued,                 None),
        "modified":                 (DCT.modified,               None),
        "url":                      (DCAT.landingPage,           None),
        "documentation":            (DCAT.qualifiedRelation,     None),
        "frequency":                (DCT.accrualPeriodicity,     None),
        "dcat_type":                (DCT.type,                   None),
        "access_rights":            (DCT.rights,                 None),
    }

    for field, (pred, lang) in SCALAR_MAP.items():
        val = d.get(field)
        if not val and val != 0:
            continue
        if str(val).startswith("http"):
            g.add((dataset_uri, pred, URIRef(str(val))))
        elif lang:
            g.add((dataset_uri, pred, Literal(str(val), lang=lang)))
        else:
            g.add((dataset_uri, pred, Literal(str(val))))

    # ── Campos lista de URIs ────────────────────────────────────────────────
    URI_LIST_MAP = {
        "theme":            DCAT.theme,
        "health_category":  HEALTH.healthCategory,
        "health_theme":     HEALTH.healthTheme,
        "personal_data":    HEALTH.personalData,
        "language":         DCT.language,
        "spatial":          DCT.spatial,
        "conforms_to":      DCT.conformsTo,
        "related_resource": DCT.relation,
        "is_referenced_by": DCT.isReferencedBy,
        "has_version":      DCT.hasVersion,
        "was_generated_by": HEALTH.wasGeneratedBy,
    }

    for field, pred in URI_LIST_MAP.items():
        values = d.get(field) or []
        if isinstance(values, str):
            values = [values]
        for v in values:
            if v:
                node = URIRef(v) if str(v).startswith("http") else Literal(str(v))
                g.add((dataset_uri, pred, node))

    # ── Campos lista de literales ───────────────────────────────────────────
    LITERAL_LIST_MAP = {
        "keyword":             (DCAT.keyword,          "es"),
        "purpose":             (HEALTH.purpose,        "es"),
        "population_coverage": (HEALTH.populationCoverage, "es"),
        "coding_system":       (HEALTH.codingSystem,   None),
        "code_values":         (HEALTH.codeValues,     None),
        "alternate_identifier":(DCT.identifier,        None),
    }

    for field, (pred, lang) in LITERAL_LIST_MAP.items():
        values = d.get(field) or []
        if isinstance(values, str):
            values = [values]
        for v in values:
            if v:
                g.add((dataset_uri, pred, Literal(str(v), lang=lang) if lang else Literal(str(v))))

    # ── Cobertura temporal ──────────────────────────────────────────────────
    tc = d.get("temporal_coverage")
    if isinstance(tc, dict):
        from rdflib import BNode
        period = BNode()
        g.add((dataset_uri, DCT.temporal, period))
        if tc.get("start"):
            g.add((period, Literal("startDate"), Literal(tc["start"], datatype=XSD.date)))
        if tc.get("end"):
            g.add((period, Literal("endDate"),   Literal(tc["end"],   datatype=XSD.date)))

    # ── Contacto ───────────────────────────────────────────────────────────
    contact = d.get("contact")
    if isinstance(contact, dict):
        from rdflib import BNode
        cp = BNode()
        g.add((dataset_uri, DCAT.contactPoint, cp))
        g.add((cp, RDF.type, VCARD.Kind))
        if contact.get("email"):
            g.add((cp, VCARD.hasEmail, URIRef(f"mailto:{contact['email']}")))
        if contact.get("url"):
            g.add((cp, VCARD.hasURL, URIRef(contact["url"])))

    # ── Publisher ──────────────────────────────────────────────────────────
    for field, pred in [("publisher", DCT.publisher), ("creator", DCT.creator)]:
        org = d.get(field)
        if isinstance(org, dict) and org.get("name"):
            from rdflib import BNode
            org_node = BNode()
            g.add((dataset_uri, pred, org_node))
            g.add((org_node, Literal("name"), Literal(org["name"])))
            if org.get("type") and str(org["type"]).startswith("http"):
                g.add((org_node, DCT.type, URIRef(org["type"])))
            if org.get("email"):
                g.add((org_node, VCARD.hasEmail, URIRef(f"mailto:{org['email']}")))

    # ── Legislación aplicable ──────────────────────────────────────────────
    for leg in (d.get("applicable_legislation") or []):
        if isinstance(leg, dict) and leg.get("uri"):
            g.add((dataset_uri, DCT.isPartOf, URIRef(leg["uri"])))
        elif isinstance(leg, str) and leg.startswith("http"):
            g.add((dataset_uri, DCT.isPartOf, URIRef(leg)))

    # ── Distribución ──────────────────────────────────────────────────────
    for dist in (d.get("distribution") or []):
        if isinstance(dist, dict) and dist.get("access_url"):
            from rdflib import BNode
            dist_node = BNode()
            g.add((dataset_uri, DCAT.distribution, dist_node))
            g.add((dist_node, RDF.type, DCAT.Distribution))
            g.add((dist_node, DCAT.accessURL, URIRef(dist["access_url"])))

    # ── Serializar ────────────────────────────────────────────────────────
    if fmt == "turtle":
        rdf_bytes = g.serialize(format="turtle").encode("utf-8")
        media_type  = "text/turtle"
        filename    = f"metadata_{session_id[:8]}.ttl"
    else:
        rdf_bytes = g.serialize(format="xml").encode("utf-8")
        media_type  = "application/rdf+xml"
        filename    = f"metadata_{session_id[:8]}.rdf"

    return FastAPIResponse(
        content=rdf_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.post("/reset")
def reset(body: ResetRequest, response: Response, session_id: str = Cookie(default=None)):
    if body.confirm:
        if session_id and session_id in sessions:
            sessions[session_id] = MetadataState("health_dcat_ap.yaml")
        else:
            get_session(None, response)
        return {"success": True, "message": "Estado reseteado."}
    return {"success": False}

@app.get("/llm-status")
def llm_status():
    return {"available": llm_available()}


@app.get("/guide")
def guide():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "Guía de campos – HealthDCAT-AP.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Guía no encontrada")
    return FileResponse(
        pdf_path,
        filename="Guía de campos – HealthDCAT-AP.pdf",
        media_type="application/pdf"
    )
    
@app.get("/sessions/count")
def sessions_count():
    return {"active_sessions": len(sessions)}

# ── Conversor RDF → dict de metadatos ──────────────────────────────────────
def _rdf_graph_to_metadata(g: Graph) -> dict:
    """
    Extrae predicados del grafo RDF y los mapea a los campos internos del asistente.
    Soporta tanto RDF/XML como Turtle.
    """
    # Prefijos HealthDCAT-AP / DCAT / DCT que usamos
    PRED_MAP = {
        "http://purl.org/dc/terms/title":                   "title",
        "http://purl.org/dc/terms/description":             "notes",
        "http://purl.org/dc/terms/identifier":              "identifier",
        "http://purl.org/dc/terms/publisher":               "publisher",
        "http://purl.org/dc/terms/creator":                 "creator",
        "http://purl.org/dc/terms/language":                "language",
        "http://purl.org/dc/terms/issued":                  "issued",
        "http://purl.org/dc/terms/modified":                "modified",
        "http://purl.org/dc/terms/accrualPeriodicity":      "frequency",
        "http://purl.org/dc/terms/spatial":                 "spatial",
        "http://purl.org/dc/terms/temporal":                "temporal_coverage",
        "http://purl.org/dc/terms/conformsTo":              "conforms_to",
        "http://purl.org/dc/terms/provenance":              "provenance",
        "http://purl.org/dc/terms/relation":                "related_resource",
        "http://purl.org/dc/terms/isReferencedBy":          "is_referenced_by",
        "http://purl.org/dc/terms/hasVersion":              "has_version",
        "http://purl.org/dc/terms/type":                    "dcat_type",
        "http://purl.org/dc/terms/license":                 "legal_basis",
        "http://purl.org/dc/terms/rights":                  "access_rights",
        "http://www.w3.org/ns/dcat#keyword":                "keyword",
        "http://www.w3.org/ns/dcat#theme":                  "theme",
        "http://www.w3.org/ns/dcat#contactPoint":           "contact",
        "http://www.w3.org/ns/dcat#landingPage":            "url",
        "http://www.w3.org/ns/dcat#version":                "version",
        "http://www.w3.org/ns/dcat#spatialResolutionInMeters": "spatial_resolution_in_meters",
        "http://www.w3.org/ns/dcat#temporalResolution":     "temporal_resolution",
        "https://healthdcat-ap.eu/ns#healthCategory":       "health_category",
        "https://healthdcat-ap.eu/ns#healthTheme":          "health_theme",
        "https://healthdcat-ap.eu/ns#hdab":                 "hdab",
        "https://healthdcat-ap.eu/ns#personalData":         "personal_data",
        "https://healthdcat-ap.eu/ns#populationCoverage":   "population_coverage",
        "https://healthdcat-ap.eu/ns#purpose":              "purpose",
        "https://healthdcat-ap.eu/ns#codingSystem":         "coding_system",
        "https://healthdcat-ap.eu/ns#numberOfRecords":      "number_of_records",
        "https://healthdcat-ap.eu/ns#numberOfUniqueIndividuals": "number_of_unique_individuals",
        "https://healthdcat-ap.eu/ns#minTypicalAge":        "min_typical_age",
        "https://healthdcat-ap.eu/ns#maxTypicalAge":        "max_typical_age",
        "https://healthdcat-ap.eu/ns#wasGeneratedBy":       "was_generated_by",
        "https://healthdcat-ap.eu/ns#retentionPeriod":      "retention_period",
        "https://healthdcat-ap.eu/ns#codeValues":           "code_values",
        "https://healthdcat-ap.eu/ns#publisherNote":        "publisher_note",
        "https://healthdcat-ap.eu/ns#qualifiedAttribution": "qualified_attribution",
    }

    # Campos que acumulan múltiples valores en lista
    LIST_FIELDS = {
        "language", "theme", "health_category", "health_theme",
        "personal_data", "keyword", "spatial", "conforms_to",
        "related_resource", "is_referenced_by", "has_version",
        "purpose", "population_coverage", "coding_system",
        "code_values", "was_generated_by",
    }

    result = {}
    for subj, pred, obj in g:
        field = PRED_MAP.get(str(pred))
        if not field:
            continue
        value = str(obj)
        if field in LIST_FIELDS:
            if field not in result:
                result[field] = []
            if value not in result[field]:
                result[field].append(value)
        else:
            # Para campos escalares, el primero gana (salvo que esté vacío)
            if field not in result or not result[field]:
                result[field] = value

    return result
@app.post("/import-session")
async def import_session(
    file: UploadFile = File(...),
    response: Response = None,
    session_id: str = Cookie(default=None)
):
    sid, _ = get_session(session_id, response)

    filename = (file.filename or "").lower()
    is_json  = filename.endswith(".json") or file.content_type in ("application/json", "text/json")
    is_rdf   = filename.endswith(".rdf")  or file.content_type == "application/rdf+xml"
    is_ttl   = filename.endswith(".ttl")  or file.content_type in ("text/turtle", "application/x-turtle")

    if not (is_json or is_rdf or is_ttl):
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Usa JSON (.json), RDF/XML (.rdf) o Turtle (.ttl)."
        )

    contents = await file.read()
    source_type = "json"

    try:
        if is_json:
            payload = json.loads(contents.decode("utf-8-sig"))
            metadata_payload = _extract_metadata_payload(payload)
            if not isinstance(metadata_payload, dict):
                raise HTTPException(status_code=400, detail="El JSON debe contener un objeto de metadatos.")

        elif is_rdf:
            source_type = "rdf"
            g = Graph()
            g.parse(data=contents, format="xml")
            metadata_payload = _rdf_graph_to_metadata(g)

        elif is_ttl:
            source_type = "ttl"
            g = Graph()
            g.parse(data=contents, format="turtle")
            metadata_payload = _rdf_graph_to_metadata(g)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear el archivo ({source_type}): {str(e)}")

    sessions[sid] = MetadataState("health_dcat_ap.yaml")
    state = sessions[sid]
    cleaned_data = {k: v for k, v in metadata_payload.items() if v not in (None, "", [])}
    state.merge_partial(cleaned_data)
    apply_conditional_logic(state)

    return {
        "success": True,
        "metadata": state.data,
        "results_by_block": _summarize_blocks(state.data),
        "session_id": sid,
        "source_type": source_type,
    }


def _run_yoda(file_bytes: bytes, filename: str) -> dict:
    """Ejecuta el pipeline de yoda_extractor sobre un fichero y devuelve el dict HealthDCAT-AP."""
    from readers import get_reader
    from extractors import ALL_EXTRACTORS
    from extractors.static import normalize_language
    from main import _load_dataframe, _merge_output

    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        reader = get_reader(tmp_path)
        extractors = [cls(file_path=tmp_path) for cls in ALL_EXTRACTORS]
        for record in reader.stream_records():
            for extractor in extractors:
                extractor.update(record)
        results = {e.name: e.result() for e in extractors}
        df = _load_dataframe(tmp_path)
        for extractor in extractors:
            finalized = extractor.finalize(results, df)
            if finalized:
                results[extractor.name] = {**results.get(extractor.name, {}), **finalized}
        output, _structure = _merge_output(results)
        return normalize_language(output)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    response: Response = None,
    session_id: str = Cookie(default=None)
):
    sid, state = get_session(session_id, response)

    contents = await file.read()
    ext = Path(file.filename or "").suffix.lower()

    # ── Rama 2: ficheros de datos estructurados (yoda_extractor) ──
    if ext in {".csv", ".json", ".xml", ".xlsx", ".xls", ".parquet"}:
        try:
            yoda_metadata = _run_yoda(contents, file.filename or f"upload{ext}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en yoda_extractor: {e}")

        existing_access_rights = state.data.get("access_rights")
        if existing_access_rights:
            yoda_metadata["access_rights"] = existing_access_rights

        results_by_block = {}
        filled_fields = {}
        for block in BLOCKS:
            block_result = {}
            block_filled = 0
            for field in block["fields"]:
                value = yoda_metadata.get(field)
                block_result[field] = value
                if value is not None and value != "" and value != []:
                    block_filled += 1
                    filled_fields[field] = value
            results_by_block[block["name"]] = {
                "fields": block_result,
                "filled": block_filled,
                "total": len(block["fields"]),
                "complete": block_filled == len(block["fields"]),
            }

        state.merge_partial(filled_fields)
        apply_conditional_logic(state)
        return {
            "success": True,
            "source": "yoda",
            "results_by_block": results_by_block,
            "metadata": state.data,
            "errors": yoda_metadata.get("errors", []),
            "session_id": sid,
        }

    # ── Rama 1: PDF (comportamiento original) ──
    try:
        pdf = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        text = text[:8000]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el PDF: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="El PDF no contiene texto extraíble.")
    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM no disponible.")

    existing_access_rights = state.data.get("access_rights")
    all_fields = list(dict.fromkeys(f for block in BLOCKS for f in block["fields"]))

    # PASO 1: Clasificación rápida
    classification = _classify_document(text)
    print(f"[DEBUG] Classification: {classification}")  # ← añade esto

    # PASO 1.5: Filtrar vocabulario relevante
    relevant_vocab = _build_relevant_vocab(classification)
    print(f"[DEBUG] Relevant vocab: {relevant_vocab}")  # ← y esto

    # ← AÑADE ESTO
    doc_lang = classification.get("idioma", "es")
    print(f"[DEBUG] doc_lang: {doc_lang}")  # ← y esto
    if doc_lang not in ("es", "en"):
        doc_lang = "es"

    # PASO 2: Extracción dirigida
    try:
        ai_result = _extract_fields_smart(
            text, all_fields, relevant_vocab,
            existing_access_rights,
            doc_lang=doc_lang
        )
        print(f"[DEBUG] ai_result: {json.dumps(ai_result, ensure_ascii=False)[:500]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el LLM: {str(e)}")

    if existing_access_rights:
        ai_result["access_rights"] = existing_access_rights
    if doc_lang == "en":
        fields_to_translate = {}
        if ai_result.get("title"):
            fields_to_translate["title"] = ai_result["title"]
        if ai_result.get("notes"):
            fields_to_translate["notes"] = ai_result["notes"]
        
        if fields_to_translate:
            try:
                translate_prompt = (
                    f"Translate the following fields to Spanish. "
                    f"Return ONLY valid JSON with the same keys.\n"
                    f"{json.dumps(fields_to_translate, ensure_ascii=False)}"
                )
                translated = call_llm(translate_prompt, fields_to_translate, "")
                if translated.get("title"):
                    ai_result["title"] = translated["title"]
                if translated.get("notes"):
                    ai_result["notes"] = translated["notes"]
            except Exception:
                pass  
    results_by_block = {}
    filled_fields = {}
    for block in BLOCKS:
        block_result = {}
        block_filled = 0
        for field in block["fields"]:
            value = ai_result.get(field)
            block_result[field] = value
            if value is not None and value != "" and value != []:
                block_filled += 1
                filled_fields[field] = value
        results_by_block[block["name"]] = {
            "fields": block_result,
            "filled": block_filled,
            "total": len(block["fields"]),
            "complete": block_filled == len(block["fields"])
        }

    state.merge_partial(filled_fields)
    apply_conditional_logic(state)
    print(f"[DEBUG] filled_fields: {filled_fields}")
    print(f"[DEBUG] state.data after merge: {state.data}")
    return {
        "success": True,
        "text_extracted": len(text),
        "classification": classification,
        "results_by_block": results_by_block,
        "metadata": state.data,
        "session_id": sid
    }

# ── Servir React (SIEMPRE AL FINAL) ──
if os.path.exists("frontend/dist") and os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_react(full_path: str):
        return FileResponse("frontend/dist/index.html")
    

