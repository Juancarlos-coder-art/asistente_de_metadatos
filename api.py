"""
api.py — Backend FastAPI para el Asistente HealthDCAT-AP-ES
"""
from dotenv import load_dotenv
load_dotenv()

import json
import uuid
import os
from fastapi import FastAPI, HTTPException, Cookie, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader
import io

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from assistant.rag_helper import get_block_missing, get_missing_descriptions
from cli import BLOCKS, build_prompt_for_block, build_contract

app = FastAPI(title="Asistente HealthDCAT-AP-ES", version="1.0.0")

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

PERSONAL_DATA_TYPES = {
    "salud": "https://w3id.org/dpv/pd#Health",
    "historial médico": "https://w3id.org/dpv/pd#HealthRecord",
    "historial de salud": "https://w3id.org/dpv/pd#HealthHistory",
    "salud médica": "https://w3id.org/dpv/pd#MedicalHealth",
    "salud física": "https://w3id.org/dpv/pd#PhysicalHealth",
    "salud mental": "https://w3id.org/dpv/pd#MentalHealth",
    "historial de salud individual": "https://w3id.org/dpv/pd#IndividualHealthHistory",
    "historial de salud familiar": "https://w3id.org/dpv/pd#FamilyHealthHistory",
    "genética": "https://w3id.org/dpv/pd#Genetic",
    "código adn": "https://w3id.org/dpv/pd#DNACode",
    "datos biométricos": "https://w3id.org/dpv/pd#Biometric",
    "edad": "https://w3id.org/dpv/pd#Age",
    "rango de edad": "https://w3id.org/dpv/pd#AgeRange",
    "género": "https://w3id.org/dpv/pd#Gender",
    "nacionalidad": "https://w3id.org/dpv/pd#Nationality",
    "localización": "https://w3id.org/dpv/pd#Location",
    "prescripción": "https://w3id.org/dpv/pd#Prescription",
    "resultado de la prueba de fármacos": "https://w3id.org/dpv/pd#DrugTestResult",
    "discapacidad": "https://w3id.org/dpv/pd#Disability",
    "tipo de sangre": "https://w3id.org/dpv/pd#BloodType",
    "origen étnico": "https://w3id.org/dpv/pd#EthnicOrigin",
    "nombre": "https://w3id.org/dpv/pd#Name",
    "identificador": "https://w3id.org/dpv/pd#Identifier",
    "identificador oficial": "https://w3id.org/dpv/pd#OfficialID",
    "profesional": "https://w3id.org/dpv/pd#Professional",
}
PERSONAL_DATA_CLASS_TO_URI = {
    "Health": "https://w3id.org/dpv/pd#Health",
    "HealthRecord": "https://w3id.org/dpv/pd#HealthRecord",
    "HealthHistory": "https://w3id.org/dpv/pd#HealthHistory",
    "MedicalHealth": "https://w3id.org/dpv/pd#MedicalHealth",
    "PhysicalHealth": "https://w3id.org/dpv/pd#PhysicalHealth",
    "MentalHealth": "https://w3id.org/dpv/pd#MentalHealth",
    "IndividualHealthHistory": "https://w3id.org/dpv/pd#IndividualHealthHistory",
    "FamilyHealthHistory": "https://w3id.org/dpv/pd#FamilyHealthHistory",
    "Genetic": "https://w3id.org/dpv/pd#Genetic",
    "DNACode": "https://w3id.org/dpv/pd#DNACode",
    "Biometric": "https://w3id.org/dpv/pd#Biometric",
    "Age": "https://w3id.org/dpv/pd#Age",
    "AgeRange": "https://w3id.org/dpv/pd#AgeRange",
    "Gender": "https://w3id.org/dpv/pd#Gender",
    "Nationality": "https://w3id.org/dpv/pd#Nationality",
    "Location": "https://w3id.org/dpv/pd#Location",
    "Prescription": "https://w3id.org/dpv/pd#Prescription",
    "DrugTestResult": "https://w3id.org/dpv/pd#DrugTestResult",
    "Disability": "https://w3id.org/dpv/pd#Disability",
    "BloodType": "https://w3id.org/dpv/pd#BloodType",
    "EthnicOrigin": "https://w3id.org/dpv/pd#EthnicOrigin",
    "Name": "https://w3id.org/dpv/pd#Name",
    "Identifier": "https://w3id.org/dpv/pd#Identifier",
    "OfficialID": "https://w3id.org/dpv/pd#OfficialID",
    "Professional": "https://w3id.org/dpv/pd#Professional",
}


# ── Códigos cortos para el LLM ──
HEALTH_CAT_CODES = {
    "EHRS": "http://13.81.34.152:1101/resource/authority/healthcategories/EHRS",
    "HRAD": "http://13.81.34.152:1101/resource/authority/healthcategories/HRAD",
    "MRMR": "http://13.81.34.152:1101/resource/authority/healthcategories/MRMR",
    "RPDG": "http://13.81.34.152:1101/resource/authority/healthcategories/RPDG",
    "RQSH": "http://13.81.34.152:1101/resource/authority/healthcategories/RQSH",
    "EHCT": "http://13.81.34.152:1101/resource/authority/healthcategories/EHCT",
    "HGPD": "http://13.81.34.152:1101/resource/authority/healthcategories/HGPD",
    "EINS": "http://13.81.34.152:1101/resource/authority/healthcategories/EINS",
    "EMRD": "http://13.81.34.152:1101/resource/authority/healthcategories/EMRD",
    "HPML": "http://13.81.34.152:1101/resource/authority/healthcategories/HPML",
    "RMMD": "http://13.81.34.152:1101/resource/authority/healthcategories/RMMD",
    "NRPE": "http://13.81.34.152:1101/resource/authority/healthcategories/NRPE",
    "PHDR": "http://13.81.34.152:1101/resource/authority/healthcategories/PHDR",
    "WELA": "http://13.81.34.152:1101/resource/authority/healthcategories/WELA",
    "PGEH": "http://13.81.34.152:1101/resource/authority/healthcategories/PGEH",
    "IDHP": "http://13.81.34.152:1101/resource/authority/healthcategories/IDHP",
    "DIOH": "http://13.81.34.152:1101/resource/authority/healthcategories/DIOH",
}

THEME_CODES = {
    "AGRI": "http://publications.europa.eu/resource/authority/data-theme/AGRI",
    "ECON": "http://publications.europa.eu/resource/authority/data-theme/ECON",
    "EDUC": "http://publications.europa.eu/resource/authority/data-theme/EDUC",
    "ENER": "http://publications.europa.eu/resource/authority/data-theme/ENER",
    "ENVI": "http://publications.europa.eu/resource/authority/data-theme/ENVI",
    "GOVE": "http://publications.europa.eu/resource/authority/data-theme/GOVE",
    "HEAL": "http://publications.europa.eu/resource/authority/data-theme/HEAL",
    "INTR": "http://publications.europa.eu/resource/authority/data-theme/INTR",
    "JUST": "http://publications.europa.eu/resource/authority/data-theme/JUST",
    "REGI": "http://publications.europa.eu/resource/authority/data-theme/REGI",
    "SOCI": "http://publications.europa.eu/resource/authority/data-theme/SOCI",
    "TECH": "http://publications.europa.eu/resource/authority/data-theme/TECH",
    "TRAN": "http://publications.europa.eu/resource/authority/data-theme/TRAN",
}

DATASET_TYPE_CODES = {
    "STATISTICAL": "http://publications.europa.eu/resource/authority/dataset-type/STATISTICAL",
    "GEOSPATIAL": "http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL",
    "SYNTHETIC_DATA": "http://publications.europa.eu/resource/authority/dataset-type/SYNTHETIC_DATA",
    "HVD": "http://publications.europa.eu/resource/authority/dataset-type/HVD",
    "CORE_COMP": "http://publications.europa.eu/resource/authority/dataset-type/CORE_COMP",
    "ONTOLOGY": "http://publications.europa.eu/resource/authority/dataset-type/ONTOLOGY",
    "SCHEMA": "http://publications.europa.eu/resource/authority/dataset-type/SCHEMA",
    "GLOSSARY": "http://publications.europa.eu/resource/authority/dataset-type/GLOSSARY",
    "THESAURUS": "http://publications.europa.eu/resource/authority/dataset-type/THESAURUS",
    "TAXONOMY": "http://publications.europa.eu/resource/authority/dataset-type/TAXONOMY",
    "CODE_LIST": "http://publications.europa.eu/resource/authority/dataset-type/CODE_LIST",
    "DIRECTORY": "http://publications.europa.eu/resource/authority/dataset-type/DIRECTORY",
}

PUBLISHER_TYPE_CODES = {
    "public-health-institute": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-institute",
    "research-institute-org": "http://13.81.34.152:1101/resource/authority/publisher-type/research-institute-org",
    "national-authority": "http://13.81.34.152:1101/resource/authority/publisher-type/national-authority",
    "regional-authority": "http://13.81.34.152:1101/resource/authority/publisher-type/regional-authority",
    "university": "http://13.81.34.152:1101/resource/authority/publisher-type/university",
    "public-health-registry": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-registry",
    "public-health-org": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-org",
    "stat-agency": "http://13.81.34.152:1101/resource/authority/publisher-type/stat-agency",
    "biobank": "http://13.81.34.152:1101/resource/authority/publisher-type/biobank",
    "inpatient-institute": "http://13.81.34.152:1101/resource/authority/publisher-type/inpatient-institute",
    "laboratory": "http://13.81.34.152:1101/resource/authority/publisher-type/laboratory",
    "private-company": "http://13.81.34.152:1101/resource/authority/publisher-type/private-company",
    "gov-public-sector-org": "http://13.81.34.152:1101/resource/authority/publisher-type/gov-public-sector-org",
    "healthcare-providers": "http://13.81.34.152:1101/resource/authority/publisher-type/healthcare-providers",
    "pharma-company": "http://13.81.34.152:1101/resource/authority/publisher-type/pharma-company",
    "research-academic-org": "http://13.81.34.152:1101/resource/authority/publisher-type/research-academic-org",
    "non-gov-org": "http://13.81.34.152:1101/resource/authority/publisher-type/non-gov-org",
    "other-government-agency": "http://13.81.34.152:1101/resource/authority/publisher-type/other-government-agency",
}

def get_session(session_id, response):
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    new_id = str(uuid.uuid4())
    sessions[new_id] = MetadataState("health_dcat_ap.yaml")
    response.set_cookie(key="session_id", value=new_id, httponly=True, samesite="lax", max_age=60*60*8)
    return new_id, sessions[new_id]


def apply_conditional_logic(state: MetadataState):
    ar = state.data.get("access_rights", "")
    if ar and "NON_PUBLIC" in str(ar).upper():
        state.data["identifier"] = ENDS_NON_PUBLIC_URI


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
        f"Analiza este documento y responde SOLO con un JSON con estas claves:\n"
        f"- 'idioma': idioma del documento ('es' o 'en')\n"
        f"- 'es_sanitario': true si el documento es de ámbito sanitario/médico/salud, false si no lo es\n"
        f"- 'tipo_organismo': tipo de organismo mencionado, null si no hay\n"
        f"- 'categorias_salud': lista de categorías sanitarias mencionadas, null si no hay\n"
        f"- 'temas': lista de temas principales del documento\n"
        f"- 'tipo_dataset': tipo de dataset si se menciona, null si no\n"
        f"Usa SOLO etiquetas simples, sin URIs.\n"
        f"Documento:\n{text[:1000]}"
    )
    try:
        return call_llm(prompt, {
            "idioma": None,
            "es_sanitario": None,
            "tipo_organismo": None,
            "categorias_salud": None,
            "temas": None,
            "tipo_dataset": None
        }, "")
    except Exception:
        return {}

def _build_relevant_vocab(classification: dict) -> dict:
    # Ya no filtramos — el LLM elige directamente por contexto
    # Solo mantenemos esto por compatibilidad con el código existente
    return {
        "publisher_types": {},
        "health_categories": {},
        "themes": {},
        "dataset_types": {}
    }


def _extract_fields_smart(text: str, all_fields: list, relevant_vocab: dict, existing_access_rights: str = None, doc_lang: str = "es") -> dict:
    fields_str = ", ".join(all_fields)

    # Descripciones comprimidas para el LLM
    health_cats_compact = (
        "EHRS: Electronic Health Records | "
        "HRAD: Health administrative data (dispensing, claims) | "
        "MRMR: Medical records and mortality registries | "
        "RPDG: Pathogens affecting human health | "
        "RQSH: Research cohorts, questionnaires, health surveys | "
        "EHCT: Clinical trials and clinical studies | "
        "HGPD: Human genetic, epigenomic and genomic data | "
        "EINS: Biobank health data | "
        "EMRD: Medical device health data | "
        "HPML: Molecular data (proteomics, genomics, metabolomics) | "
        "RMMD: Medicinal products and medical devices registries | "
        "NRPE: Aggregate healthcare needs, resources, spending | "
        "PHDR: Population-based health data registries | "
        "WELA: Wellness application data | "
        "PGEH: Personal electronic health data from medical devices | "
        "IDHP: Health professionals status and specialization data | "
        "DIOH: Social, environmental and behavioural health determinants"
    )

    themes_compact = (
        "AGRI: Agriculture, fisheries, forestry | "
        "ECON: Economy and finance | "
        "EDUC: Education, culture, sport | "
        "ENER: Energy | "
        "ENVI: Environment | "
        "GOVE: Government and public sector | "
        "HEAL: Health | "
        "INTR: International affairs | "
        "JUST: Justice, legal system, public safety | "
        "REGI: Regions and cities | "
        "SOCI: Population and society | "
        "TECH: Science and technology | "
        "TRAN: Transport"
    )

    dataset_types_compact = (
        "STATISTICAL: Statistical data | "
        "GEOSPATIAL: Geospatial data | "
        "SYNTHETIC_DATA: Synthetic data | "
        "HVD: High value dataset | "
        "CORE_COMP: Core component | "
        "ONTOLOGY: Ontology | "
        "SCHEMA: Schema | "
        "GLOSSARY: Glossary | "
        "THESAURUS: Thesaurus | "
        "TAXONOMY: Taxonomy | "
        "CODE_LIST: Code list | "
        "DIRECTORY: Directory"
    )

    publisher_types_compact = (
        "public-health-institute: Public health institute | "
        "research-institute-org: Research institute or organization | "
        "national-authority: National authority | "
        "regional-authority: Regional authority | "
        "university: University | "
        "public-health-registry: Public health registry | "
        "public-health-org: Public health organization | "
        "stat-agency: Statistics agency | "
        "biobank: Biobank | "
        "inpatient-institute: Hospital or inpatient institution | "
        "laboratory: Laboratory | "
        "private-company: Private company | "
        "gov-public-sector-org: Government or public sector organization | "
        "healthcare-providers: Healthcare provider | "
        "pharma-company: Pharmaceutical company | "
        "research-academic-org: Research or academic organization | "
        "non-gov-org: Non-governmental organization | "
        "other-government-agency: Other government agency"
    )

    if doc_lang == "en":
        access_rights_section = (
            f"- 'access_rights' → ALREADY SET BY USER: '{existing_access_rights}'. Return exactly this value.\n"
            if existing_access_rights else
            f"- 'access_rights' → one of: PUBLIC, RESTRICTED, NON_PUBLIC. Return full URI:\n"
            f"  PUBLIC → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
            f"  RESTRICTED → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
            f"  NON_PUBLIC → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        )
        prompt = (
            f"Extract metadata from this document.\n"
            f"Expected keys: [{fields_str}]\n\n"
            f"RULES: Return ONLY valid JSON.\n"
            f"- 'title', 'notes', 'keyword': ALWAYS extract, even if not a health document.\n"
            f"- Health-specific fields: null if not applicable.\n\n"
            f"MAPPING:\n"
            f"- 'title' → document title\n"
            f"- 'notes' → full description, copy literally\n"
            f"- 'identifier' → DOI or unique ID\n"
            f"{access_rights_section}"
            f"- 'hdab' → object: name, email, telephone, contact_page, type (use code from list below)\n"
            f"  Publisher types: {publisher_types_compact}\n"
            f"  For 'type' return full URI: http://13.81.34.152:1101/resource/authority/publisher-type/{{code}}\n"
            f"- 'health_category' → array of full URIs. Choose codes from: {health_cats_compact}\n"
            f"  URI format: http://13.81.34.152:1101/resource/authority/healthcategories/{{CODE}}\n"
            f"- 'theme' → array of full URIs. Choose codes from: {themes_compact}\n"
            f"  URI format: http://publications.europa.eu/resource/authority/data-theme/{{CODE}}\n"
            f"- 'dcat_type' → full URI. Choose code from: {dataset_types_compact}\n"
            f"  URI format: http://publications.europa.eu/resource/authority/dataset-type/{{CODE}}\n"
            f"- 'provenance' → data origin, free text\n"
            f"- 'keyword' → array of strings\n"
            f"- 'contact' → object: email, url\n"
            f"- 'personal_data' → array of DPV-PD class names (e.g. ['Health', 'Age']). null if not mentioned.\n"
            f"- 'number_of_unique_individuals' → integer or null\n"
            f"- 'number_of_records' → integer or null\n"
            f"- 'min_typical_age' → integer or null\n"
            f"- 'max_typical_age' → integer or null\n"
            f"- 'purpose' → array of strings or null\n"
            f"- 'population_coverage' → array of strings or null\n"
            f"- 'language' → array of URIs: Spanish=http://publications.europa.eu/resource/authority/language/SPA, English=.../ENG\n"
            f"\nDocument:\n{text[:4000]}"
        )
    else:
        access_rights_section = (
            f"- 'access_rights' → YA DEFINIDO: '{existing_access_rights}'. Devuelve exactamente este valor.\n"
            if existing_access_rights else
            f"- 'access_rights' → uno de: PUBLIC, RESTRICTED, NON_PUBLIC. Devuelve URI completa:\n"
            f"  PUBLIC → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
            f"  RESTRICTED → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
            f"  NON_PUBLIC → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        )
        prompt = (
            f"Extrae metadatos de este documento.\n"
            f"Claves esperadas: [{fields_str}]\n\n"
            f"REGLAS: Devuelve SOLO JSON válido.\n"
            f"- 'title', 'notes', 'keyword': EXTRAE SIEMPRE aunque no sea sanitario.\n"
            f"- Campos específicos de salud: null si no aplica.\n\n"
            f"MAPEO:\n"
            f"- 'title' → título del documento\n"
            f"- 'notes' → descripción completa, cópiala literalmente\n"
            f"- 'identifier' → DOI o identificador único\n"
            f"{access_rights_section}"
            f"- 'hdab' → objeto: name, email, telephone, contact_page, type (usa código de la lista)\n"
            f"  Tipos de organismo: {publisher_types_compact}\n"
            f"  Para 'type' devuelve URI completa: http://13.81.34.152:1101/resource/authority/publisher-type/{{código}}\n"
            f"- 'health_category' → array de URIs completas. Elige códigos de: {health_cats_compact}\n"
            f"  Formato URI: http://13.81.34.152:1101/resource/authority/healthcategories/{{CÓDIGO}}\n"
            f"- 'theme' → array de URIs completas. Elige códigos de: {themes_compact}\n"
            f"  Formato URI: http://publications.europa.eu/resource/authority/data-theme/{{CÓDIGO}}\n"
            f"- 'dcat_type' → URI completa. Elige código de: {dataset_types_compact}\n"
            f"  Formato URI: http://publications.europa.eu/resource/authority/dataset-type/{{CÓDIGO}}\n"
            f"- 'provenance' → origen de los datos, texto libre\n"
            f"- 'keyword' → array de strings\n"
            f"- 'contact' → objeto: email, url\n"
            f"- 'personal_data' → array de nombres de clase DPV-PD (ej: ['Health', 'Age']). null si no se menciona.\n"
            f"- 'number_of_unique_individuals' → entero o null\n"
            f"- 'number_of_records' → entero o null\n"
            f"- 'min_typical_age' → entero o null\n"
            f"- 'max_typical_age' → entero o null\n"
            f"- 'purpose' → array de strings o null\n"
            f"- 'population_coverage' → array de strings o null\n"
            f"- 'language' → array de URIs: Español=http://publications.europa.eu/resource/authority/language/SPA, Inglés=.../ENG\n"
            f"\nDocumento:\n{text[:4000]}"
        )

    return call_llm(prompt, {f: None for f in all_fields}, "")
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
    return {"status": "ok", "service": "Asistente HealthDCAT-AP-ES"}

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
        "purpose": "purpose",
        "language": "language",
        "population_coverage": "population_coverage",
        "number_of_unique_individuals":"number_of_unique_individuals",
        "number_of_records": "number_of_records",
        "min_typical_age": "min_typical_age",
        "max_typical_age": "max_typical_age"
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
    return info

@app.post("/complete/{block_id}")
def complete_block(block_id: int, body: CompleteBlockRequest, response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM no disponible.")
    if not body.user_context.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    block = BLOCKS[block_id]
    try:
        prompt = build_prompt_for_block(_schema, block, body.user_context)
        contract = build_contract(block)
        ai_result = call_llm(prompt, contract, body.user_context)
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
    to_merge = {k: v for k, v in body.partial.items() if v not in (None, "", [])}
    state.merge_partial(to_merge)
    missing_fields = [f for f in block["fields"] if not state.data.get(f)]
    ai_partial = {}
    if missing_fields and llm_available():
        try:
            user_context = f"Datos actuales:\n{json.dumps(state.data, ensure_ascii=False)}\nNuevos datos:\n{json.dumps(to_merge, ensure_ascii=False)}\nCompleta SOLO los campos faltantes."
            prompt = build_prompt_for_block(_schema, block, user_context)
            contract = {f: None for f in missing_fields}
            ai_result = call_llm(prompt, contract, user_context)
            ai_partial = {k: v for k, v in ai_result.items() if v not in (None, "", [])}
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
    return {"valid": len(errors) == 0 and len(missing) == 0, "errors": errors, "missing_required": missing}

@app.get("/missing/{block_id}")
def get_missing_fields(block_id: int, response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    block = BLOCKS[block_id]
    missing = get_block_missing(block, state.data)
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
    access_url = state.data.pop("access_url", None)
    if access_url:
        state.data["distribution"] = [{
            "access_url": access_url,
            "applicable_legislation": state.data.get("applicable_legislation", [
                {"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}
            ])
        }]
    filename = f"metadata_output_{sid[:8]}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state.data, f, indent=2, ensure_ascii=False)
    return {"success": True, "metadata": state.data, "file": filename}

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
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "Guía de campos – HealthDCAT-AP-ES.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Guía no encontrada")
    return FileResponse(
        pdf_path,
        filename="Guía de campos – HealthDCAT-AP-ES.pdf",
        media_type="application/pdf"
    )
    
@app.get("/sessions/count")
def sessions_count():
    return {"active_sessions": len(sessions)}

@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    response: Response = None,
    session_id: str = Cookie(default=None)
):
    sid, state = get_session(session_id, response)

    try:
        contents = await file.read()
        pdf = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        text = text[:4000]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el PDF: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="El PDF no contiene texto extraíble.")
    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM no disponible.")

    existing_access_rights = state.data.get("access_rights")
    all_fields = list(dict.fromkeys(f for block in BLOCKS for f in block["fields"]))



    classification = _classify_document(text)
    print(f"[DEBUG] Classification: {classification}")
    relevant_vocab = _build_relevant_vocab(classification)
    doc_lang = classification.get("idioma", "es")
    es_sanitario = classification.get("es_sanitario", True)
    if not es_sanitario:
        print(f"[WARN] Documento no sanitario subido")

    # PASO 2: Extracción dirigida
    try:
        ai_result = _extract_fields_smart(
            text, all_fields, relevant_vocab,
            existing_access_rights,
            doc_lang=doc_lang
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el LLM: {str(e)}")

    if ai_result.get("personal_data") and isinstance(ai_result["personal_data"], list):
        mapped = []
        for item in ai_result["personal_data"]:
            item_clean = str(item).strip()
            if item_clean in PERSONAL_DATA_CLASS_TO_URI:
                mapped.append(PERSONAL_DATA_CLASS_TO_URI[item_clean])
            else:
                mapped.append(f"https://w3id.org/dpv/pd#{item_clean.replace(' ', '')}")
        ai_result["personal_data"] = mapped if mapped else None

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


# ── Servir React (SIEMPRE AL FINAL) ──
if os.path.exists("frontend/dist") and os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_react(full_path: str):
        return FileResponse("frontend/dist/index.html")
