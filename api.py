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
    "instituto de investigación": "http://13.81.34.152:1101/resource/authority/publisher-type/research-institute-org",
    "autoridad nacional": "http://13.81.34.152:1101/resource/authority/publisher-type/national-authority",
    "autoridad regional": "http://13.81.34.152:1101/resource/authority/publisher-type/regional-authority",
    "universidad": "http://13.81.34.152:1101/resource/authority/publisher-type/university",
    "registro de salud pública": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-registry",
    "organización de salud pública": "http://13.81.34.152:1101/resource/authority/publisher-type/public-health-org",
    "agencia de estadísticas": "http://13.81.34.152:1101/resource/authority/publisher-type/stat-agency",
    "biobanco": "http://13.81.34.152:1101/resource/authority/publisher-type/biobank",
    "hospital": "http://13.81.34.152:1101/resource/authority/publisher-type/inpatient-institute",
    "laboratorio": "http://13.81.34.152:1101/resource/authority/publisher-type/laboratory",
    "empresa privada": "http://13.81.34.152:1101/resource/authority/publisher-type/private-company",
    "organización gubernamental": "http://13.81.34.152:1101/resource/authority/publisher-type/gov-public-sector-org",
    "proveedor de atención médica": "http://13.81.34.152:1101/resource/authority/publisher-type/healthcare-providers",
}

HEALTH_CATEGORIES = {
    "registros electrónicos de salud": "http://13.81.34.152:1101/resource/authority/healthcategories/EHRS",
    "datos administrativos sanitarios": "http://13.81.34.152:1101/resource/authority/healthcategories/HRAD",
    "registros médicos y mortalidad": "http://13.81.34.152:1101/resource/authority/healthcategories/MRMR",
    "datos de patógenos": "http://13.81.34.152:1101/resource/authority/healthcategories/RPDG",
    "cohortes e investigación": "http://13.81.34.152:1101/resource/authority/healthcategories/RQSH",
    "registros de salud pública": "http://13.81.34.152:1101/resource/authority/healthcategories/PHDR",
    "ensayos clínicos": "http://13.81.34.152:1101/resource/authority/healthcategories/EHCT",
    "datos genómicos": "http://13.81.34.152:1101/resource/authority/healthcategories/HGPD",
    "biobancos": "http://13.81.34.152:1101/resource/authority/healthcategories/EINS",
    "dispositivos médicos": "http://13.81.34.152:1101/resource/authority/healthcategories/EMRD",
    "datos moleculares": "http://13.81.34.152:1101/resource/authority/healthcategories/HPML",
    "datos de medicamentos": "http://13.81.34.152:1101/resource/authority/healthcategories/RMMD",
    "datos agregados sanitarios": "http://13.81.34.152:1101/resource/authority/healthcategories/NRPE",
    "vigilancia epidemiológica": "http://13.81.34.152:1101/resource/authority/healthcategories/PHDR",
}

THEMES = {
    "salud": "http://publications.europa.eu/resource/authority/data-theme/HEAL",
    "ciencia": "http://publications.europa.eu/resource/authority/data-theme/TECH",
    "tecnología": "http://publications.europa.eu/resource/authority/data-theme/TECH",
    "población": "http://publications.europa.eu/resource/authority/data-theme/SOCI",
    "sociedad": "http://publications.europa.eu/resource/authority/data-theme/SOCI",
    "gobierno": "http://publications.europa.eu/resource/authority/data-theme/GOVE",
    "educación": "http://publications.europa.eu/resource/authority/data-theme/EDUC",
    "economía": "http://publications.europa.eu/resource/authority/data-theme/ECON",
    "medio ambiente": "http://publications.europa.eu/resource/authority/data-theme/ENVI",
}

DATASET_TYPES = {
    "estadístico": "http://publications.europa.eu/resource/authority/dataset-type/STATISTICAL",
    "geoespacial": "http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL",
    "alto valor": "http://publications.europa.eu/resource/authority/dataset-type/HVD",
    "datos sintéticos": "http://publications.europa.eu/resource/authority/dataset-type/SYNTHETIC_DATA",
    "ontología": "http://publications.europa.eu/resource/authority/dataset-type/ONTOLOGY",
    "esquema": "http://publications.europa.eu/resource/authority/dataset-type/SCHEMA",
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


def _extract_choices(choices_list):
    result = []
    for ch in (choices_list or []):
        lbl = ch.get("label", {})
        label_es = lbl.get("es", ch.get("value", "")) if isinstance(lbl, dict) else str(lbl)
        result.append({"value": ch.get("value", ""), "label": label_es})
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
    """PASO 1: Clasificación rápida (~200 tokens)"""
    prompt = (
        f"Analiza este documento sanitario y responde SOLO con un JSON con estas claves:\n"
        f"- 'tipo_organismo': tipo de organismo mencionado (ej: 'instituto de salud pública')\n"
        f"- 'categorias_salud': lista de categorías sanitarias (ej: ['registros médicos', 'epidemiología'])\n"
        f"- 'temas': lista de temas principales (ej: ['salud', 'población'])\n"
        f"- 'tipo_dataset': tipo de dataset (ej: 'estadístico')\n"
        f"Usa SOLO etiquetas simples en español, sin URIs.\n"
        f"Documento:\n{text[:2000]}"
    )
    try:
        return call_llm(prompt, {
            "tipo_organismo": None,
            "categorias_salud": None,
            "temas": None,
            "tipo_dataset": None
        }, text[:2000])
    except Exception:
        return {}


def _build_relevant_vocab(classification: dict) -> dict:
    """PASO 1.5: Filtrar vocabulario relevante (Python puro, sin LLM)"""
    relevant = {"publisher_types": {}, "health_categories": {}, "themes": {}, "dataset_types": {}}

    tipo_org = str(classification.get("tipo_organismo", "")).lower()
    for label, uri in PUBLISHER_TYPES.items():
        if any(word in tipo_org for word in label.split()):
            relevant["publisher_types"][label] = uri
    if not relevant["publisher_types"]:
        relevant["publisher_types"] = dict(list(PUBLISHER_TYPES.items())[:5])

    cats = [str(c).lower() for c in (classification.get("categorias_salud") or [])]
    for label, uri in HEALTH_CATEGORIES.items():
        if any(word in " ".join(cats) for word in label.split()[:2]):
            relevant["health_categories"][label] = uri
    if not relevant["health_categories"]:
        relevant["health_categories"] = dict(list(HEALTH_CATEGORIES.items())[:5])

    temas = [str(t).lower() for t in (classification.get("temas") or [])]
    for label, uri in THEMES.items():
        if label in " ".join(temas):
            relevant["themes"][label] = uri
    if not relevant["themes"]:
        relevant["themes"] = {"salud": THEMES["salud"]}

    tipo_ds = str(classification.get("tipo_dataset", "")).lower()
    for label, uri in DATASET_TYPES.items():
        if label in tipo_ds:
            relevant["dataset_types"][label] = uri
    if not relevant["dataset_types"]:
        relevant["dataset_types"] = {"estadístico": DATASET_TYPES["estadístico"]}

    return relevant


def _extract_fields_smart(text: str, all_fields: list, relevant_vocab: dict, existing_access_rights: str = None) -> dict:
    """PASO 2: Extracción dirigida (~800 tokens)"""
    fields_str = ", ".join(all_fields)
    pub_types_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["publisher_types"].items())
    health_cats_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["health_categories"].items())
    themes_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["themes"].items())
    dataset_types_str = "\n".join(f"    {l} → {u}" for l, u in relevant_vocab["dataset_types"].items())

    access_rights_section = (
        f"- 'access_rights' → YA DEFINIDO POR EL USUARIO: '{existing_access_rights}'. Devuelve exactamente este valor.\n"
        if existing_access_rights else
        f"- 'access_rights' → nivel de acceso URI:\n"
        f"    Público → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
        f"    Restringido → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
        f"    No público → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
    )

    prompt = (
        f"Extrae campos de metadatos de este documento sanitario.\n"
        f"Claves esperadas: [{fields_str}]\n\n"
        f"REGLAS: Devuelve SOLO JSON válido. null si no aparece en el texto.\n\n"
        f"MAPEO:\n"
        f"- 'title' → título del dataset\n"
        f"- 'notes' → descripción completa. Cópiala literalmente.\n"
        f"- 'identifier' → DOI o identificador único\n"
        f"{access_rights_section}"
        f"- 'hdab' → organismo gestor del acceso. Objeto con: name, email, telephone, contact_page, type.\n"
        f"  Tipos posibles:\n{pub_types_str}\n"
        f"- 'health_category' → array de URIs:\n{health_cats_str}\n"
        f"- 'theme' → array de URIs:\n{themes_str}\n"
        f"- 'dcat_type' → URI:\n{dataset_types_str}\n"
        f"- 'provenance' → origen de los datos. Texto libre.\n"
        f"- 'keyword' → palabras clave. Array de strings.\n"
        f"- 'contact' → objeto con: email, url\n"
        f"\nDocumento:\n{text[:5000]}"
    )
    return call_llm(prompt, {f: None for f in all_fields}, text[:5000])


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
    return [{"id": i, "name": b["name"], "question": b["question"], "fields": b["fields"], "hint": b.get("hint", "")} for i, b in enumerate(BLOCKS)]

@app.get("/blocks/{block_id}")
def get_block(block_id: int):
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    b = BLOCKS[block_id]
    return {"id": block_id, "name": b["name"], "question": b["question"], "fields": b["fields"]}

@app.get("/schema-info")
def get_schema_info():
    field_map = {
        "access_rights": "Derechos de acceso",
        "hdab": "Organismo de acceso a datos de salud",
        "health_category": "health_category",
        "theme": "theme",
        "dcat_type": "dcat_type",
        "contact": "contact",
    }
    info = {}
    for field_key, yaml_field_name in field_map.items():
        schema_field = _schema.get_field(yaml_field_name)
        if not schema_field:
            continue
        entry = {}
        if schema_field.get("choices"):
            choices = _extract_choices(schema_field["choices"])
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
        state.data["applicable_legislation"] = [{"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}]
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
    pdf_path = r"C:\Users\juanc_chswm14\Desktop\asistente-metadato\static\Guía de campos – HealthDCAT-AP-ES.pdf"
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

    # PASO 1.5: Filtrar vocabulario relevante
    relevant_vocab = _build_relevant_vocab(classification)

    # PASO 2: Extracción dirigida
    try:
        ai_result = _extract_fields_smart(text, all_fields, relevant_vocab, existing_access_rights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el LLM: {str(e)}")

    if existing_access_rights:
        ai_result["access_rights"] = existing_access_rights

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
