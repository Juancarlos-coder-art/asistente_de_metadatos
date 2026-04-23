"""
api.py — Backend FastAPI para el Asistente HealthDCAT-AP-ES
Expone los endpoints que consume el frontend React.
Run: uvicorn api:app --reload --port 8080
"""
from dotenv import load_dotenv
from cli import BLOCKS, build_prompt_for_block, build_contract
from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from assistant.rag_helper import get_block_missing, get_missing_descriptions
load_dotenv()
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="Asistente HealthDCAT-AP-ES",
    description="API para metadatar datasets sanitarios conforme a HealthDCAT-AP-ES",
    version="1.0.0"
)

# CORS — permite que React (localhost:3000) llame a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# ESTADO EN MEMORIA (sesión única por servidor)
# Para producción multi-usuario usar Redis o DB
# ─────────────────────────────────────────────
_schema = HealthDCATAPSchema("health_dcat_ap.yaml")
_state = MetadataState("health_dcat_ap.yaml")


# ─────────────────────────────────────────────
# MODELOS PYDANTIC
# ─────────────────────────────────────────────
class CompleteBlockRequest(BaseModel):
    block_id: int
    user_context: str

class ManualSaveRequest(BaseModel):
    block_id: int
    partial: dict

class ResetRequest(BaseModel):
    confirm: bool = True


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/api/health")
def root():
    return {"status": "ok", "service": "Asistente HealthDCAT-AP-ES"}


# ── 1. Obtener todos los bloques ──────────────
@app.get("/blocks")
def get_blocks():
    """Devuelve la lista de bloques con sus campos y preguntas."""
    return [
        {
            "id": i,
            "name": b["name"],
            "question": b["question"],
            "fields": b["fields"]
        }
        for i, b in enumerate(BLOCKS)
    ]


# ── 2. Obtener un bloque concreto ─────────────
@app.get("/blocks/{block_id}")
def get_block(block_id: int):
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")
    b = BLOCKS[block_id]
    return {
        "id": block_id,
        "name": b["name"],
        "question": b["question"],
        "fields": b["fields"]
    }


# ── 3. Autocompletar bloque con IA ───────────
@app.post("/complete/{block_id}")
def complete_block(block_id: int, body: CompleteBlockRequest):
    """El usuario describe el bloque en texto libre y el LLM extrae los campos."""
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")

    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM no disponible. Configura GROQ_API_KEY.")

    if not body.user_context.strip():
        raise HTTPException(status_code=400, detail="El texto de descripción no puede estar vacío.")

    block = BLOCKS[block_id]

    try:
        prompt = build_prompt_for_block(_schema, block, body.user_context)
        contract = build_contract(block)
        ai_result = call_llm(prompt, contract, body.user_context)

        partial = {name: ai_result.get(name, None) for name in block["fields"]}
        _state.merge_partial(partial)

        return {
            "success": True,
            "partial": partial,
            "metadata": _state.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 4. Guardar bloque manualmente ────────────
@app.post("/save-manual")
def save_manual(body: ManualSaveRequest):
    """Guarda los campos rellenados manualmente por el usuario."""
    if body.block_id < 0 or body.block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")

    to_merge = {k: v for k, v in body.partial.items() if v is not None and v != ""}
    _state.merge_partial(to_merge)

    return {
        "success": True,
        "metadata": _state.data
    }


# ── 5. Obtener estado actual del metadata ────
@app.get("/metadata")
def get_metadata():
    """Devuelve el JSON de metadatos acumulado hasta ahora."""
    return _state.data


# ── 6. Validar estado actual ─────────────────
@app.get("/validate")
def validate():
    """Valida el estado actual y devuelve errores y campos obligatorios pendientes."""
    errors = _state.validate_types_basic()
    missing = _state.missing_required()
    return {
        "valid": len(errors) == 0 and len(missing) == 0,
        "errors": errors,
        "missing_required": missing
    }


# ── 7. Campos faltantes de un bloque (RAG) ───
@app.get("/missing/{block_id}")
def get_missing_fields(block_id: int):
    """Devuelve los campos vacíos del bloque con descripción del RAG."""
    if block_id < 0 or block_id >= len(BLOCKS):
        raise HTTPException(status_code=404, detail="Bloque no encontrado")

    block = BLOCKS[block_id]
    missing = get_block_missing(block, _state.data)
    descriptions = get_missing_descriptions(missing, use_llm=False)

    return {
        "block_id": block_id,
        "missing_fields": missing,
        "descriptions": descriptions
    }


# ── 8. Finalizar y guardar JSON ───────────────
@app.post("/finalize")
def finalize():
    """Inserta la legislación automática y devuelve el JSON final."""
    _state.data["applicable_legislation"] = [
        {
            "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
            "label": "GDPR"
        }
    ]

    # Guardar en disco
    with open("metadata_output.json", "w", encoding="utf-8") as f:
        json.dump(_state.data, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "metadata": _state.data
    }


# ── 9. Resetear estado ────────────────────────
@app.post("/reset")
def reset(body: ResetRequest):
    """Resetea el estado de metadatos para empezar de nuevo."""
    global _state
    if body.confirm:
        _state = MetadataState("health_dcat_ap.yaml")
        return {"success": True, "message": "Estado reseteado correctamente."}
    return {"success": False, "message": "Confirma el reset con confirm=true."}


# ── 10. Estado del LLM ────────────────────────
@app.get("/llm-status")
def llm_status():
    """Comprueba si el LLM está disponible."""
    return {
        "available": llm_available(),
        "message": "LLM disponible" if llm_available() else "Configura GROQ_API_KEY en el .env"
    }

# ── 11. Servir frontend React ─────────────────
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_react(full_path: str):
        return FileResponse("frontend/dist/index.html")