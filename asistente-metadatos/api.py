"""
api.py — Backend FastAPI para el Asistente HealthDCAT-AP-ES
Sesiones por usuario mediante cookies.
Run: uvicorn api:app --reload --port 8000
"""
from dotenv import load_dotenv
load_dotenv()

import json
import uuid
import os
from fastapi import FastAPI, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from assistant.rag_helper import get_block_missing, get_missing_descriptions
from cli import BLOCKS, build_prompt_for_block, build_contract
# Añadir estos imports al principio de api.py
from fastapi import UploadFile, File
from pypdf import PdfReader
import io


app = FastAPI(
    title="Asistente HealthDCAT-AP-ES",
    description="API para metadatar datasets sanitarios conforme a HealthDCAT-AP-ES",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_schema = HealthDCATAPSchema("health_dcat_ap.yaml")
sessions: dict = {}

def get_session(session_id, response):
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    new_id = str(uuid.uuid4())
    sessions[new_id] = MetadataState("health_dcat_ap.yaml")
    response.set_cookie(key="session_id", value=new_id, httponly=True, samesite="lax", max_age=60*60*8)
    return new_id, sessions[new_id]

ENDS_NON_PUBLIC_URI = "https://catalogo.ends.gob.es/dataset"
NON_PUBLIC_URI = "http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC"

def apply_conditional_logic(state: MetadataState):
    """Si access_rights es NON_PUBLIC → asignar identifier automáticamente."""
    ar = state.data.get("access_rights", "")
    if ar and "NON_PUBLIC" in str(ar).upper():
        if not state.data.get("identifier"):
            state.data["identifier"] = ENDS_NON_PUBLIC_URI

class CompleteBlockRequest(BaseModel):
    block_id: int
    user_context: str

class ManualSaveRequest(BaseModel):
    block_id: int
    partial: dict

class ResetRequest(BaseModel):
    confirm: bool = True

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Asistente HealthDCAT-AP-ES"
    }

@app.get("/blocks")
def get_blocks():
    return [
        {
            "id": i,
            "name": b["name"],
            "question": b["question"],
            "fields": b["fields"],
            "hint": b.get("hint", ""),
            "placeholder": b.get("placeholder", "")  # ← añade esto
        }
        for i, b in enumerate(BLOCKS)
    ]
@app.get("/blocks/{block_id}")
def get_block(block_id: int):
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    b = BLOCKS[block_id]
    return {"id": block_id, "name": b["name"], "question": b["question"], "fields": b["fields"]}


def _extract_choices(choices_list):
    """Extrae value + label (es) de una lista de choices del YAML."""
    result = []
    for ch in (choices_list or []):
        lbl = ch.get("label", {})
        label_es = lbl.get("es", ch.get("value", "")) if isinstance(lbl, dict) else str(lbl)
        result.append({"value": ch.get("value", ""), "label": label_es})
    return result


def _extract_subfields(subfields_list):
    """Extrae info de subcampos (nombre, label, required, choices)."""
    result = []
    for sf in (subfields_list or []):
        sf_name = sf.get("field_name")
        raw_label = (sf.get("label", {}).get("es", sf_name)
                     if isinstance(sf.get("label"), dict)
                     else str(sf.get("label", sf_name)))
        # Desambiguar subcampos de horario duplicados
        if sf_name and sf_name.startswith("special_opening_hours"):
            raw_label = f"Horario especial – {raw_label}"
        elif sf_name and sf_name.startswith("opening_hours"):
            raw_label = f"Horario habitual – {raw_label}"
        entry = {
            "field_name": sf_name,
            "label": raw_label,
            "required": sf.get("required", False),
        }
        if sf.get("choices"):
            entry["choices"] = _extract_choices(sf["choices"])
        result.append(entry)
    return result


# Valores permitidos de access_rights para el formulario
_ALLOWED_ACCESS_RIGHTS = {
    "PUBLIC", "RESTRICTED", "NON_PUBLIC",
}


@app.get("/schema-info")
def get_schema_info():
    """Devuelve info del schema para los campos de los bloques (choices, subcampos)."""
    field_map = {
        "access_rights": "Derechos de acceso",
        "hdab": "Organismo de acceso a datos de salud",
    }
    info = {}
    for field_key, yaml_name in field_map.items():
        schema_field = _schema.get_field(yaml_name)
        if not schema_field:
            continue
        entry = {}
        if schema_field.get("choices"):
            choices = _extract_choices(schema_field["choices"])
            # Filtrar access_rights a solo las opciones permitidas
            if field_key == "access_rights":
                choices = [ch for ch in choices
                           if ch["value"].rsplit("/", 1)[-1] in _ALLOWED_ACCESS_RIGHTS]
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
        raise HTTPException(status_code=503, detail="LLM no disponible. Configura GROQ_API_KEY.")
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
    to_merge = {k: v for k, v in body.partial.items() if v is not None and v != ""}
    state.merge_partial(to_merge)
    apply_conditional_logic(state)
    
    return {"success": True, "metadata": state.data, "session_id": sid}

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
    descriptions = get_missing_descriptions(missing, use_llm=False)
    return {"block_id": block_id, "missing_fields": missing, "descriptions": descriptions}

@app.post("/finalize")
def finalize(response: Response, session_id: str = Cookie(default=None)):
    sid, state = get_session(session_id, response)
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
        return {"success": True, "message": "Estado reseteado correctamente."}
    return {"success": False, "message": "Confirma con confirm=true."}

@app.get("/llm-status")
def llm_status():
    return {"available": llm_available(), "message": "LLM disponible" if llm_available() else "Configura GROQ_API_KEY en el .env"}

@app.get("/guide")
def guide():
    return FileResponse(
        "static/Guía de campos – HealthDCAT-AP-ES.pdf",
        filename="Guía de campos – HealthDCAT-AP-ES.pdf",
        media_type="application/pdf",
    )

@app.get("/sessions/count")
def sessions_count():
    return {"active_sessions": len(sessions)}

if os.path.exists("frontend/dist") and os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_react(full_path: str):
        return FileResponse("frontend/dist/index.html")

# ── Endpoint: subir documento PDF y extraer metadatos ──
@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    response: Response = None,
    session_id: str = Cookie(default=None)
):
    """
    Recibe un PDF, extrae el texto y usa el LLM para inferir
    todos los campos de todos los bloques posibles.
    Devuelve un diccionario con los campos inferidos por bloque.
    """
    sid, state = get_session(session_id, response)
 
    # ── 1. Extraer texto del PDF ──
    try:
        contents = await file.read()
        pdf = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        text = text[:8000]  # limitar a 8000 chars para no exceder tokens
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el PDF: {str(e)}")
 
    if not text.strip():
        raise HTTPException(status_code=400, detail="El PDF no contiene texto extraíble.")
 
    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM no disponible.")
 
    # ── 2. Inferir todos los campos de todos los bloques ──
    all_fields = []
    for block in BLOCKS:
        all_fields.extend(block["fields"])
    all_fields = list(dict.fromkeys(all_fields))  # deduplicar
 
    fields_str = ", ".join(all_fields)
 
    prompt = (
        f"El usuario ha subido un documento sobre un dataset sanitario.\n"
        f"Extrae ÚNICAMENTE la información que aparezca explícitamente en el texto.\n"
        f"Claves esperadas: [{fields_str}]\n\n"
        f"REGLAS:\n"
        f"- Devuelve SOLO JSON válido\n"
        f"- Si un campo no aparece en el texto, devuelve null\n"
        f"- NUNCA inventes ni deduzcas información\n"
        f"- El campo 'notes' corresponde a la descripción general del dataset. "
        f"Copia el texto de descripción del documento aunque sea largo.\n"  # ← mejora 1
        f"- Para 'access_rights' usa la URI correspondiente:\n"
        f"  Público → http://publications.europa.eu/resource/authority/access-right/PUBLIC\n"
        f"  Restringido → http://publications.europa.eu/resource/authority/access-right/RESTRICTED\n"
        f"  No público → http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC\n"
        f"- Para 'hdab' devuelve objeto con: name, type, email, telephone, contact_page\n"
        f"\nTexto del documento:\n{text[:6000]}" 
        f"MAPEO DE CAMPOS (clave JSON → qué buscar en el documento):\n"
        f"- 'title' → título o nombre del dataset\n"
        f"- 'notes' → descripción, resumen o abstract del dataset\n"
        f"- 'identifier' → DOI, identificador único o URI del dataset\n"
        f"- 'access_rights' → nivel de acceso, condiciones de uso, quién puede acceder\n"
        f"- 'hdab' → organismo de acceso, entidad gestora, HDAB\n"
        f"  Subcampos: name (nombre), email (correo), telephone (teléfono), contact_page (web)\n"# ← mejora 2: reducido de 8000 a 6000
    )
    
    contract = {f: None for f in all_fields}
 
    try:
        ai_result = call_llm(prompt, contract, text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el LLM: {str(e)}")
 
    # ── 3. Organizar resultados por bloque ──
    results_by_block = {}
    filled_fields = {}
 
    for block in BLOCKS:
        block_result = {}
        block_filled = 0
        block_total = len(block["fields"])
 
        for field in block["fields"]:
            value = ai_result.get(field)
            block_result[field] = value
            if value is not None and value != "" and value != []:
                block_filled += 1
                filled_fields[field] = value
 
        results_by_block[block["name"]] = {
            "fields": block_result,
            "filled": block_filled,
            "total": block_total,
            "complete": block_filled == block_total
        }
 
    # ── 4. Guardar en el estado de sesión ──
    state.merge_partial(filled_fields)
    apply_conditional_logic(state)
 
    return {
        "success": True,
        "text_extracted": len(text),
        "results_by_block": results_by_block,
        "metadata": state.data,
        "session_id": sid
    }

# ── Endpoint: validar con SHACL contra el validador ITB ──
@app.post("/validate-shacl")
async def validate_shacl(
    response: Response,
    session_id: str = Cookie(default=None)
):
    """
    Convierte el metadata_output.json a JSON-LD y lo envía
    al validador ITB local (http://localhost:8085).
    Elige el tipo de validación según access_rights.
    """
    sid, state = get_session(session_id, response)

    if not state.data:
        raise HTTPException(status_code=400, detail="No hay metadatos para validar.")

    # ── 1. Determinar tipo de validación según access_rights ──
    access_rights = state.data.get("access_rights", "")
    if "NON_PUBLIC" in str(access_rights).upper():
        validation_type = "nonpublic"
    elif "RESTRICTED" in str(access_rights).upper():
        validation_type = "restricted"
    else:
        validation_type = "public"

    # ── 2. Preparar el JSON-LD ──
    json_ld_content = json.dumps(state.data, indent=2, ensure_ascii=False)

    # ── 3. Llamar a la API REST del validador ITB ──
    validator_url = "https://www.itb.ec.europa.eu/shacl/any/api/validate"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                validator_url,
                json={
                    "contentToValidate": json_ld_content,
                    "contentSyntax": "application/ld+json",
                    "validationType": validation_type
                },
                headers={"Content-Type": "application/json"}
            )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"El validador devolvió error {resp.status_code}"
            )

        result = resp.json()

        # ── 4. Parsear resultado ──
        reports = result.get("reports", [])
        errors = []
        warnings = []
        messages = []

        for report in reports:
            for item in report.get("items", []):
                severity = item.get("level", "").upper()
                description = item.get("description", "")
                path = item.get("path", "")
                entry = {"description": description, "path": path}

                if severity == "ERROR" or severity == "VIOLATION":
                    errors.append(entry)
                elif severity == "WARNING":
                    warnings.append(entry)
                else:
                    messages.append(entry)

        success = len(errors) == 0

        return {
            "success": success,
            "validation_type": validation_type,
            "errors": errors,
            "warnings": warnings,
            "messages": messages,
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "raw": result
        }

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="No se puede conectar con el validador SHACL. Asegúrate de que está corriendo en http://localhost:8085"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al validar: {str(e)}")