"""
<<<<<<< HEAD
HealthDCAT-AP Metadata Assistant — FastAPI edition.
Run:  uvicorn app_fastapi:app --reload --port 8000
"""

import json, os, pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from assistant.rag_helper import (
    get_block_missing,
    get_missing_descriptions,
    describe_missing_field,
)
from cli import BLOCKS, build_prompt_for_block, build_contract

# ── FastAPI app ──────────────────────────────────────────────
app = FastAPI(title="HealthDCAT-AP Metadata Assistant")

# ── In-memory session state (single-user demo) ──────────────
=======
api.py — Backend FastAPI para el Asistente HealthDCAT-AP-ES
Expone los endpoints que consume el frontend React.
Run: uvicorn api:app --reload --port 8000
"""
from dotenv import load_dotenv
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
>>>>>>> origin/master
_schema = HealthDCATAPSchema("health_dcat_ap.yaml")
_state = MetadataState("health_dcat_ap.yaml")


<<<<<<< HEAD
# ── Helpers ──────────────────────────────────────────────────
def _blocks_summary():
    """Return block list with completion info."""
    result = []
    for i, blk in enumerate(BLOCKS):
        filled = sum(
            1 for f in blk["fields"]
            if _state.data.get(f) not in (None, "", [], {})
        )
        result.append({
            "index": i,
            "name": blk["name"],
            "fields": blk["fields"],
            "question": blk["question"],
            "filled": filled,
            "total": len(blk["fields"]),
        })
    return result


def _full_status():
    total = sum(len(b["fields"]) for b in BLOCKS)
    filled = sum(
        1
        for b in BLOCKS
        for f in b["fields"]
        if _state.data.get(f) not in (None, "", [], {})
    )
    missing = _state.missing_required()
    errors = _state.validate_types_basic()
    return {
        "data": _state.data,
        "blocks": _blocks_summary(),
        "filled": filled,
        "total": total,
        "pct": round(filled / total * 100) if total else 0,
        "missing_required": missing,
        "validation_errors": errors,
        "llm_available": llm_available(),
    }


# ── API endpoints ────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


@app.get("/api/status")
async def api_status():
    return JSONResponse(_full_status())


@app.post("/api/block/{block_idx}/ai")
async def api_block_ai(block_idx: int, request: Request):
    body = await request.json()
    user_text = body.get("text", "").strip()
    if not user_text:
        return JSONResponse({"error": "Texto vacío"}, 400)
    if block_idx < 0 or block_idx >= len(BLOCKS):
        return JSONResponse({"error": "Bloque inválido"}, 400)

    blk = BLOCKS[block_idx]
    prompt = build_prompt_for_block(_schema, blk, user_text)
    contract = build_contract(blk)
    ai_result = call_llm(prompt, contract, user_text)
    partial = {name: ai_result.get(name) for name in blk["fields"]}
    _state.merge_partial(partial)
    return JSONResponse(_full_status())


@app.post("/api/block/{block_idx}/manual")
async def api_block_manual(block_idx: int, request: Request):
    body = await request.json()
    fields = body.get("fields", {})
    if block_idx < 0 or block_idx >= len(BLOCKS):
        return JSONResponse({"error": "Bloque inválido"}, 400)

    blk = BLOCKS[block_idx]
    partial = {}
    for fname in blk["fields"]:
        val = fields.get(fname)
        if val is not None and val != "":
            partial[fname] = val
    _state.merge_partial(partial)
    return JSONResponse(_full_status())


@app.post("/api/reset")
async def api_reset():
    _state.data.clear()
    return JSONResponse(_full_status())


@app.post("/api/finalize")
async def api_finalize():
    _state.data["applicable_legislation"] = [
        {"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}
    ]
    out = pathlib.Path("metadata_output.json")
    out.write_text(json.dumps(_state.data, indent=2, ensure_ascii=False), encoding="utf-8")
    return JSONResponse({"saved": str(out.resolve()), **_full_status()})


@app.get("/api/missing/{block_idx}")
async def api_missing(block_idx: int):
    if block_idx < 0 or block_idx >= len(BLOCKS):
        return JSONResponse({"error": "Bloque inválido"}, 400)
    blk = BLOCKS[block_idx]
    missing = get_block_missing(blk, _state.data)
    descs = get_missing_descriptions(missing)
    return JSONResponse({"missing": descs})


@app.get("/api/download")
async def api_download():
    return JSONResponse(_state.data)


@app.get("/api/field-guide")
async def api_field_guide():
    guide_path = pathlib.Path("guia_campos_ends.docx")
    if not guide_path.is_file():
        return JSONResponse({"error": "Archivo guia_campos_ends.docx no encontrado"}, 404)
    return FileResponse(
        guide_path,
        filename="guia_campos_ends.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/api/field-descriptions")
async def api_field_descriptions():
    """Return descriptions for all missing fields, grouped by block."""
    result = []
    for i, blk in enumerate(BLOCKS):
        missing = get_block_missing(blk, _state.data)
        descs = get_missing_descriptions(missing)
        result.append({"block_index": i, "block_name": blk["name"], "fields": descs})
    return JSONResponse(result)


# ── Full HTML SPA ────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HealthDCAT-AP Metadata Assistant</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet"/>
<style>
/* ═══════════════════════════════════════════════
   TOKENS
   ═══════════════════════════════════════════════ */
:root {
  /* ── Sidebar (dark) ── */
  --sb-bg:      #0f172a;
  --sb-bg2:     #1e293b;
  --sb-border:  #334155;
  --sb-ink:     #e2e8f0;
  --sb-ink-dim: #94a3b8;
  --sb-ink-faint:#64748b;

  /* ── Main area (light) ── */
  --bg:         #f1f5f9;
  --bg-card:    #ffffff;
  --bg-raised:  #f8fafc;
  --bg-input:   #ffffff;
  --border:     #cbd5e1;
  --border-hl:  #94a3b8;
  --ink:        #0f172a;
  --ink-dim:    #475569;
  --ink-faint:  #94a3b8;
  --accent:     #6d5cff;
  --accent-glow:rgba(109,92,255,.12);
  --accent-soft:#ede9fe;
  --accent-fg:  #ffffff;
  --ok:         #059669;
  --ok-bg:      #ecfdf5;
  --warn:       #d97706;
  --warn-bg:    #fffbeb;
  --err:        #dc2626;
  --err-bg:     #fef2f2;
  --radius:     12px;
  --radius-sm:  8px;
  --font:       'Inter',system-ui,sans-serif;
  --mono:       'Fira Code','Consolas',monospace;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{font-size:15px}
body{
  font-family:var(--font);
  background:var(--bg);
  color:var(--ink);
  min-height:100vh;
  -webkit-font-smoothing:antialiased;
  color-scheme:light;
}

/* ═══════════════════════════════
   LAYOUT
   ═══════════════════════════════ */
.shell{display:flex;min-height:100vh}

/* ── sidebar (dark) ── */
.sidebar{
  width:290px;
  flex-shrink:0;
  background:linear-gradient(180deg,var(--sb-bg) 0%,#162032 100%);
  border-right:1px solid var(--sb-border);
  padding:28px 20px;
  display:flex;
  flex-direction:column;
  gap:18px;
  position:sticky;
  top:0;
  height:100vh;
  overflow-y:auto;
}
.sidebar-brand{
  font-weight:800;
  font-size:1.05rem;
  letter-spacing:-.02em;
  color:var(--sb-ink);
  display:flex;
  align-items:center;
  gap:10px;
}
.sidebar-brand .dot{
  width:10px;height:10px;border-radius:50%;
  background:var(--accent);
  box-shadow:0 0 10px var(--accent-glow);
}
.sidebar-label{
  font-family:var(--mono);
  font-size:.65rem;
  font-weight:500;
  letter-spacing:.08em;
  text-transform:uppercase;
  color:var(--sb-ink-faint);
  margin-bottom:4px;
}

/* step list */
.step-list{display:flex;flex-direction:column;gap:6px}
.step-item{
  display:flex;align-items:center;gap:10px;
  padding:10px 12px;
  border-radius:var(--radius-sm);
  cursor:pointer;
  transition:background .15s,border-color .15s;
  border:1px solid transparent;
}
.step-item:hover{background:rgba(255,255,255,.05);border-color:var(--sb-border)}
.step-item.active{background:rgba(109,92,255,.15);border-color:var(--accent)}
.step-dot{
  width:28px;height:28px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:.75rem;font-weight:700;
  background:var(--sb-bg2);color:var(--sb-ink-dim);
  border:2px solid var(--sb-border);
  flex-shrink:0;
  transition:all .15s;
}
.step-item.active .step-dot{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
.step-item.done .step-dot{background:var(--ok);color:#fff;border-color:var(--ok)}
.step-name{font-size:.82rem;font-weight:500;color:var(--sb-ink-dim)}
.step-item.active .step-name{color:var(--sb-ink);font-weight:600}
.step-item.done .step-name{color:var(--ok)}

/* progress ring */
.progress-ring-wrap{
  display:flex;flex-direction:column;align-items:center;gap:8px;
  padding:16px 0;
}
.progress-ring{position:relative;width:90px;height:90px}
.progress-ring svg{transform:rotate(-90deg)}
.progress-ring circle{
  fill:none;stroke-width:6;
  cx:45;cy:45;r:38;
  stroke-linecap:round;
}
.ring-bg{stroke:var(--sb-border)}
.ring-fg{stroke:var(--accent);transition:stroke-dashoffset .5s ease}
.ring-label{
  position:absolute;inset:0;
  display:flex;align-items:center;justify-content:center;
  font-family:var(--mono);font-size:1.2rem;font-weight:700;
  color:var(--sb-ink);
}

/* sidebar stats */
.sb-stats{display:flex;gap:8px}
.sb-stat{
  flex:1;
  background:rgba(255,255,255,.05);
  border:1px solid var(--sb-border);
  border-radius:var(--radius-sm);
  padding:12px 8px;
  text-align:center;
}
.sb-stat-num{
  font-family:var(--mono);font-size:1.15rem;font-weight:700;color:var(--sb-ink);
}
.sb-stat-label{
  font-size:.65rem;color:var(--sb-ink-faint);text-transform:uppercase;letter-spacing:.04em;
  margin-top:2px;
}
/* sidebar pill */
.sb-pill{
  display:inline-flex;align-items:center;gap:6px;
  font-size:.72rem;font-weight:600;
  padding:5px 12px;
  border-radius:20px;
}
.sb-pill.ok{background:rgba(5,150,105,.15);color:#34d399}
.sb-pill.warn{background:rgba(217,119,6,.15);color:#fbbf24}
.sb-pill.err{background:rgba(220,38,38,.15);color:#f87171}

/* sidebar field descriptions */
.sb-field-desc{
  background:rgba(255,255,255,.04);
  border-left:3px solid var(--warn);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0;
  padding:8px 12px;
  margin-bottom:6px;
}
.sb-field-name{
  font-family:var(--mono);font-size:.68rem;font-weight:600;color:var(--warn);
}
.sb-field-label{
  font-size:.8rem;color:var(--sb-ink);font-weight:500;
}
.sb-field-detail{
  font-size:.75rem;color:var(--sb-ink-dim);line-height:1.5;margin-top:2px;
}
.sb-field-ex{
  font-size:.7rem;color:var(--sb-ink-faint);font-style:italic;margin-top:2px;
}

/* sidebar buttons */
.sb-btn{
  width:100%;padding:10px;border:1px solid var(--sb-border);
  border-radius:var(--radius-sm);background:rgba(255,255,255,.06);
  color:var(--sb-ink-dim);font-family:var(--font);font-size:.82rem;
  font-weight:600;cursor:pointer;transition:all .15s;text-align:center;
}
.sb-btn:hover{background:rgba(255,255,255,.12);color:var(--sb-ink);border-color:var(--sb-ink-faint)}
.sb-btn.danger{border-color:rgba(248,113,113,.3);color:#f87171}
.sb-btn.danger:hover{background:rgba(220,38,38,.15);border-color:#f87171}

/* ── main area (light) ── */
.main{flex:1;padding:36px 48px;max-width:860px;margin:0 auto}

/* ── Welcome ── */
.welcome{text-align:center;padding:80px 0 40px}
.welcome-icon{
  width:72px;height:72px;margin:0 auto 24px;
  background:var(--accent-soft);border-radius:20px;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 30px var(--accent-glow);
}
.welcome-icon svg{width:36px;height:36px;stroke:var(--accent);fill:none;stroke-width:1.8}
.welcome h1{
  font-size:2rem;font-weight:800;letter-spacing:-.03em;
  margin-bottom:10px;
  background:linear-gradient(135deg,var(--ink),var(--accent));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}
.welcome p{color:var(--ink-dim);font-size:.95rem;max-width:460px;margin:0 auto 20px;line-height:1.7}
.welcome-actions{display:flex;flex-direction:column;align-items:center;gap:12px}
.welcome-start{
  display:inline-flex;align-items:center;gap:8px;
  padding:14px 32px;border:none;border-radius:var(--radius);
  background:var(--accent);color:var(--accent-fg);
  font-family:var(--font);font-size:.92rem;font-weight:700;
  cursor:pointer;transition:transform .1s,box-shadow .2s;
  box-shadow:0 4px 20px var(--accent-glow);
}
.welcome-start:hover{transform:translateY(-1px);box-shadow:0 6px 28px rgba(109,92,255,.35)}
.welcome-guide{
  display:inline-flex;align-items:center;gap:8px;
  padding:10px 24px;border:1px solid var(--border-hl);
  border-radius:var(--radius);
  background:var(--bg-card);color:var(--ink-dim);
  font-family:var(--font);font-size:.85rem;font-weight:600;
  cursor:pointer;transition:all .15s;
  text-decoration:none;
}
.welcome-guide:hover{background:var(--accent-soft);color:var(--accent);border-color:var(--accent)}
.welcome-guide svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2}

/* cards */
.card{
  background:var(--bg-card);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:28px 32px;
  margin-bottom:20px;
  box-shadow:0 1px 3px rgba(0,0,0,.06);
}
.card-accent{border-top:3px solid var(--accent)}

/* block header */
.block-header{margin-bottom:24px}
.block-chip{
  display:inline-block;
  font-family:var(--mono);font-size:.6rem;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;
  color:var(--accent);background:var(--accent-glow);
  padding:3px 12px;border-radius:4px;margin-bottom:10px;
}
.block-title{font-size:1.25rem;font-weight:700;color:var(--ink);margin-bottom:6px}
.block-question{
  font-size:.9rem;color:var(--ink-dim);line-height:1.7;
  border-left:3px solid var(--accent);
  padding:12px 18px;
  background:var(--accent-soft);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0;
}

/* tabs */
.tabs{display:flex;gap:4px;margin-bottom:20px}
.tab-btn{
  flex:1;padding:10px 14px;border:1px solid var(--border);
  border-radius:var(--radius-sm);background:var(--bg-raised);
  color:var(--ink-dim);font-family:var(--font);font-size:.82rem;
  font-weight:600;cursor:pointer;text-align:center;
  transition:all .15s;
}
.tab-btn.active{background:var(--accent);color:var(--accent-fg);border-color:var(--accent);box-shadow:0 2px 8px var(--accent-glow)}
.tab-btn:hover:not(.active){background:var(--accent-soft);color:var(--accent)}

/* tab panels */
.tab-panel{display:none}
.tab-panel.active{display:block}

/* forms */
.field-group{margin-bottom:16px}
.field-label{
  display:block;font-size:.78rem;font-weight:600;
  color:var(--ink-dim);margin-bottom:6px;
  text-transform:uppercase;letter-spacing:.04em;
}
.field-input,.field-textarea{
  width:100%;padding:12px 16px;
  background:var(--bg-input);color:var(--ink);
  border:1px solid var(--border);border-radius:var(--radius-sm);
  font-family:var(--font);font-size:.9rem;
  transition:border-color .15s,box-shadow .15s;
  outline:none;
}
.field-textarea{resize:vertical;min-height:120px;line-height:1.6}
.field-input:focus,.field-textarea:focus{
  border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-glow);
}
.field-input::placeholder,.field-textarea::placeholder{color:var(--ink-faint)}
.field-hint{font-size:.72rem;color:var(--ink-faint);margin-top:4px}

/* buttons */
.btn{
  display:inline-flex;align-items:center;gap:6px;
  padding:10px 22px;border:none;border-radius:var(--radius-sm);
  font-family:var(--font);font-size:.85rem;font-weight:600;
  cursor:pointer;transition:all .15s;
}
.btn-primary{background:var(--accent);color:var(--accent-fg);box-shadow:0 2px 12px var(--accent-glow)}
.btn-primary:hover{background:#5a4be6;box-shadow:0 4px 18px rgba(109,92,255,.35)}
.btn-ghost{background:transparent;color:var(--ink-dim);border:1px solid var(--border)}
.btn-ghost:hover{background:var(--bg-raised);color:var(--ink);border-color:var(--border-hl)}
.btn-row{display:flex;gap:10px;margin-top:20px;justify-content:flex-end}

/* alerts */
.alert{padding:12px 18px;border-radius:var(--radius-sm);font-size:.85rem;margin-bottom:12px;display:flex;align-items:center;gap:10px}
.alert-ok{background:var(--ok-bg);color:var(--ok);border:1px solid #a7f3d0}
.alert-warn{background:var(--warn-bg);color:var(--warn);border:1px solid #fde68a}
.alert-err{background:var(--err-bg);color:var(--err);border:1px solid #fecaca}

/* json viewer */
.json-wrap{
  background:#1e1b4b;
  border:1px solid #312e81;
  border-radius:var(--radius);
  padding:20px;margin-top:16px;
  max-height:440px;overflow-y:auto;
}
.json-wrap pre{
  font-family:var(--mono);font-size:.78rem;
  color:#a5b4fc;line-height:1.7;white-space:pre-wrap;
  word-break:break-word;
}

/* missing fields card */
.missing-card{
  background:var(--warn-bg);
  border:1px solid #fde68a;
  border-radius:var(--radius);
  padding:20px 24px;margin-bottom:16px;
}
.missing-title{
  font-size:.78rem;font-weight:700;color:var(--warn);
  text-transform:uppercase;letter-spacing:.04em;margin-bottom:12px;
}
.missing-item{
  background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:8px;
}
.missing-fname{font-family:var(--mono);font-size:.7rem;color:var(--warn);font-weight:600}
.missing-desc{font-size:.82rem;color:var(--ink-dim);margin-top:2px}
.missing-ex{font-size:.72rem;color:var(--ink-faint);font-style:italic;margin-top:4px}

/* nav */
.nav-row{display:flex;gap:10px;justify-content:space-between;margin-top:24px}

/* validation section */
.val-header{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.val-header .tag{
  font-family:var(--mono);font-size:.6rem;font-weight:600;
  padding:3px 10px;border-radius:20px;letter-spacing:.04em;text-transform:uppercase;
}
.tag-ok{background:var(--ok-bg);color:var(--ok)}
.tag-err{background:var(--err-bg);color:var(--err)}
.tag-warn{background:var(--warn-bg);color:var(--warn)}

/* spinner */
.spinner{display:inline-block;width:18px;height:18px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* status bar (bottom-of-sidebar) */
.sidebar-footer{margin-top:auto;display:flex;flex-direction:column;gap:8px}

/* scrollbar (sidebar) */
.sidebar::-webkit-scrollbar{width:6px}
.sidebar::-webkit-scrollbar-track{background:transparent}
.sidebar::-webkit-scrollbar-thumb{background:var(--sb-border);border-radius:3px}
.sidebar::-webkit-scrollbar-thumb:hover{background:var(--sb-ink-faint)}
/* scrollbar (main) */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-hl)}

/* AI unavailable warning */
.ai-unavailable{
  background:var(--warn-bg);
  border:1px solid #fde68a;
  border-radius:var(--radius-sm);
  padding:16px 20px;
  color:var(--warn);
  font-size:.88rem;
  line-height:1.6;
}
.ai-unavailable strong{color:var(--ink)}

/* responsive */
@media (max-width:768px){
  .sidebar{display:none}
  .main{padding:20px 16px}
}
</style>
</head>
<body>
<div class="shell">

<!-- ═══════════ SIDEBAR ═══════════ -->
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand"><span class="dot"></span> HDCAT-AP Assistant</div>

  <div class="progress-ring-wrap">
    <div class="progress-ring">
      <svg width="90" height="90">
        <circle class="ring-bg" cx="45" cy="45" r="38"/>
        <circle class="ring-fg" id="ringFg" cx="45" cy="45" r="38"
                stroke-dasharray="238.76" stroke-dashoffset="238.76"/>
      </svg>
      <div class="ring-label" id="ringLabel">0 %</div>
    </div>
  </div>

  <div class="sidebar-label">Progreso</div>
  <div class="sb-stats" id="sbStats">
    <div class="sb-stat"><div class="sb-stat-num" id="statFilled">0</div><div class="sb-stat-label">Completados</div></div>
    <div class="sb-stat"><div class="sb-stat-num" id="statTotal">0</div><div class="sb-stat-label">Total</div></div>
  </div>

  <div class="sidebar-label">Bloques</div>
  <div class="step-list" id="stepList"></div>

  <div id="sbPills"></div>

  <div id="sbFieldDescs"></div>

  <div class="sidebar-footer">
    <button class="sb-btn" onclick="doFinalize()">Finalizar y guardar</button>
    <button class="sb-btn" onclick="doDownload()">Descargar JSON</button>
    <button class="sb-btn danger" onclick="doReset()">Reiniciar</button>
  </div>
</aside>

<!-- ═══════════ MAIN CONTENT ═══════════ -->
<div class="main" id="mainArea">

<!-- welcome screen -->
<div id="welcomeScreen" class="welcome">
  <div class="welcome-icon">
    <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
  </div>
  <h1>HealthDCAT-AP Metadata Assistant</h1>
  <p>Completa los metadatos de tu dataset sanitario paso a paso, con asistencia de IA o de forma manual.</p>
  <div class="welcome-actions">
    <button class="welcome-start" onclick="startWizard()">Comenzar</button>
    <a class="welcome-guide" href="/api/field-guide" download>
      <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Descargar guia de campos
    </a>
  </div>
</div>

<!-- block workspace (hidden initially) -->
<div id="blockArea" style="display:none"></div>

</div><!-- /main -->
</div><!-- /shell -->

<script>
/* ═══════════════════════════════════════════
   STATE
   ═══════════════════════════════════════════ */
let S = {data:{},blocks:[],filled:0,total:0,pct:0,missing_required:[],validation_errors:[],llm_available:false};
let currentBlock = 0;
let started = false;

/* ═══════════════════════════════════════════
   BOOT
   ═══════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => refresh());

async function refresh() {
  const r = await fetch('/api/status');
  S = await r.json();
  renderSidebar();
  if (started) renderBlock();
}

/* ═══════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════ */
function renderSidebar() {
  // progress ring
  const circum = 2 * Math.PI * 38;
  const offset = circum - (S.pct / 100) * circum;
  document.getElementById('ringFg').style.strokeDashoffset = offset;
  document.getElementById('ringLabel').textContent = S.pct + ' %';

  // stats
  document.getElementById('statFilled').textContent = S.filled;
  document.getElementById('statTotal').textContent = S.total;

  // step list
  const sl = document.getElementById('stepList');
  sl.innerHTML = '';
  S.blocks.forEach((b, i) => {
    const done = b.filled === b.total;
    const active = started && i === currentBlock;
    const div = document.createElement('div');
    div.className = 'step-item' + (active ? ' active' : '') + (done ? ' done' : '');
    div.innerHTML = `<div class="step-dot">${done ? '&#10003;' : i + 1}</div><div class="step-name">${b.name}</div>`;
    div.onclick = () => { if (started) { currentBlock = i; renderBlock(); renderSidebar(); } };
    sl.appendChild(div);
  });

  // pills
  const pp = document.getElementById('sbPills');
  pp.innerHTML = '';
  if (S.validation_errors.length === 0 && S.missing_required.length === 0 && S.filled > 0) {
    pp.innerHTML = '<div class="sb-pill ok">Metadata valida</div>';
  } else {
    if (S.missing_required.length) pp.innerHTML += `<div class="sb-pill warn">${S.missing_required.length} campo(s) pendientes</div>`;
    if (S.validation_errors.length) pp.innerHTML += `<div class="sb-pill err">${S.validation_errors.length} error(es)</div>`;
  }

  // Field descriptions
  loadFieldDescriptions();
}

async function loadFieldDescriptions() {
  const box = document.getElementById('sbFieldDescs');
  if (!started) { box.innerHTML = ''; return; }
  try {
    const r = await fetch('/api/field-descriptions');
    const data = await r.json();
    const currentBlockDescs = data[currentBlock];
    if (!currentBlockDescs || !currentBlockDescs.fields.length) { box.innerHTML = ''; return; }
    box.innerHTML = `<div class="sidebar-label">Campos pendientes</div>` +
      currentBlockDescs.fields.map(f =>
        `<div class="sb-field-desc">
          <div class="sb-field-name">${esc(f.field)}</div>
          <div class="sb-field-label">${esc(f.label)}</div>
          <div class="sb-field-detail">${esc(f.descripcion)}</div>
          ${f.ejemplo ? `<div class="sb-field-ex">Ej: ${esc(f.ejemplo)}</div>` : ''}
        </div>`
      ).join('');
  } catch(e) { box.innerHTML = ''; }
}

/* ═══════════════════════════════════════════
   WELCOME / START
   ═══════════════════════════════════════════ */
function startWizard() {
  started = true;
  document.getElementById('welcomeScreen').style.display = 'none';
  document.getElementById('blockArea').style.display = 'block';
  currentBlock = 0;
  renderBlock();
  renderSidebar();
}

/* ═══════════════════════════════════════════
   RENDER BLOCK
   ═══════════════════════════════════════════ */
function renderBlock() {
  const b = S.blocks[currentBlock];
  if (!b) return;
  const area = document.getElementById('blockArea');

  let fieldInputs = b.fields.map(f => {
    const currentVal = S.data[f] || '';
    const displayVal = typeof currentVal === 'object' ? JSON.stringify(currentVal, null, 2) : currentVal;
    const isLong = f === 'notes' || f === 'hdab';
    return `<div class="field-group">
      <label class="field-label">${f}</label>
      ${isLong
        ? `<textarea class="field-textarea" data-field="${f}" placeholder="${f}">${esc(displayVal)}</textarea>`
        : `<input class="field-input" data-field="${f}" placeholder="${f}" value="${esc(displayVal)}"/>`
      }
      <div class="field-hint">Campo: ${f}${b.fields.indexOf(f) >= 0 && S.missing_required.includes(f) ? ' &mdash; obligatorio, pendiente' : ''}</div>
    </div>`;
  }).join('');

  // missing fields
  let missingHtml = '';
  const missingInBlock = S.missing_required.filter(m => b.fields.includes(m));
  if (missingInBlock.length) {
    missingHtml = `<div class="missing-card">
      <div class="missing-title">Campos pendientes en este bloque</div>
      ${missingInBlock.map(m => `<div class="missing-item">
        <div class="missing-fname">${m}</div>
      </div>`).join('')}
    </div>`;
  }

  // validation
  let valHtml = '';
  if (S.validation_errors.length) {
    valHtml = `<div class="card" style="border-left:3px solid var(--err);margin-top:16px">
      <div class="val-header"><span class="tag tag-err">Errores</span></div>
      ${S.validation_errors.map(e => `<div class="alert alert-err">${esc(e)}</div>`).join('')}
    </div>`;
  }

  area.innerHTML = `
    <div class="card card-accent">
      <div class="block-header">
        <div class="block-chip">Bloque ${currentBlock + 1} de ${S.blocks.length}</div>
        <div class="block-title">${b.name}</div>
        <div class="block-question">${esc(b.question)}</div>
      </div>

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this,'aiTab')">Asistente IA</button>
        <button class="tab-btn" onclick="switchTab(this,'manualTab')">Entrada manual</button>
      </div>

      <!-- AI tab -->
      <div class="tab-panel active" id="aiTab">
        ${S.llm_available ? `
        <div class="field-group">
          <label class="field-label">Describe tu dataset</label>
          <textarea class="field-textarea" id="aiInput" placeholder="Escribe aquí la información relevante para este bloque..."></textarea>
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" id="aiBtn" onclick="submitAI()">Procesar con IA</button>
        </div>
        <div id="aiStatus"></div>
        ` : `
        <div class="ai-unavailable">
          <strong>Asistente IA no disponible.</strong><br/>
          No se ha detectado una API key configurada. Para habilitar el autocompletado con IA,
          configura tu clave en <code style="font-family:var(--mono);background:rgba(0,0,0,.08);padding:2px 6px;border-radius:4px">assistant/llm_provider.py</code>.<br/><br/>
          Puedes seguir completando los campos de forma manual en la pestaña "Entrada manual".
        </div>
        `}
      </div>

      <!-- Manual tab -->
      <div class="tab-panel" id="manualTab">
        ${fieldInputs}
        <div class="btn-row">
          <button class="btn btn-primary" onclick="submitManual()">Guardar campos</button>
        </div>
      </div>
    </div>

    ${missingHtml}
    ${valHtml}

    <!-- JSON preview -->
    <div class="card">
      <div class="val-header"><span class="tag tag-ok">JSON preview</span></div>
      <div class="json-wrap"><pre>${esc(JSON.stringify(S.data, null, 2))}</pre></div>
    </div>

    <!-- Nav -->
    <div class="nav-row">
      <button class="btn btn-ghost" ${currentBlock === 0 ? 'disabled' : ''} onclick="navBlock(-1)">Anterior</button>
      <button class="btn btn-primary" ${currentBlock === S.blocks.length - 1 ? 'disabled' : ''} onclick="navBlock(1)">Siguiente</button>
    </div>
  `;
}

/* ═══════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════ */
function switchTab(el, panelId) {
  el.closest('.tabs').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  el.closest('.card').querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(panelId).classList.add('active');
}

/* ═══════════════════════════════════════════
   SUBMIT AI
   ═══════════════════════════════════════════ */
async function submitAI() {
  const text = document.getElementById('aiInput').value.trim();
  if (!text) return;
  const btn = document.getElementById('aiBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Procesando...';
  document.getElementById('aiStatus').innerHTML = '';

  const r = await fetch(`/api/block/${currentBlock}/ai`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  });
  const data = await r.json();

  if (data.error) {
    document.getElementById('aiStatus').innerHTML = `<div class="alert alert-err">${esc(data.error)}</div>`;
  } else {
    S = data;
    document.getElementById('aiStatus').innerHTML = '<div class="alert alert-ok">Campos actualizados correctamente</div>';
    renderSidebar();
    setTimeout(() => renderBlock(), 600);
  }
  btn.disabled = false;
  btn.innerHTML = 'Procesar con IA';
}

/* ═══════════════════════════════════════════
   SUBMIT MANUAL
   ═══════════════════════════════════════════ */
async function submitManual() {
  const fields = {};
  document.querySelectorAll('#manualTab [data-field]').forEach(el => {
    let v = el.value.trim();
    if (!v) return;
    // try parsing JSON for object fields
    try { const p = JSON.parse(v); v = p; } catch(e) {}
    fields[el.dataset.field] = v;
  });
  const r = await fetch(`/api/block/${currentBlock}/manual`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({fields})
  });
  S = await r.json();
  renderSidebar();
  renderBlock();
}

/* ═══════════════════════════════════════════
   NAV
   ═══════════════════════════════════════════ */
function navBlock(dir) {
  const next = currentBlock + dir;
  if (next >= 0 && next < S.blocks.length) {
    currentBlock = next;
    renderBlock();
    renderSidebar();
    window.scrollTo({top: 0, behavior: 'smooth'});
  }
}

/* ═══════════════════════════════════════════
   ACTIONS
   ═══════════════════════════════════════════ */
async function doFinalize() {
  if (!confirm('Finalizar y guardar metadata_output.json?')) return;
  const r = await fetch('/api/finalize', {method:'POST'});
  const d = await r.json();
  S = d;
  renderSidebar();
  if (started) renderBlock();
  alert('Guardado en: ' + d.saved);
}

async function doReset() {
  if (!confirm('Reiniciar todos los datos?')) return;
  const r = await fetch('/api/reset', {method:'POST'});
  S = await r.json();
  started = false;
  currentBlock = 0;
  document.getElementById('blockArea').style.display = 'none';
  document.getElementById('welcomeScreen').style.display = '';
  renderSidebar();
}

function doDownload() {
  const blob = new Blob([JSON.stringify(S.data, null, 2)], {type:'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'metadata_output.json'; a.click();
  URL.revokeObjectURL(url);
}

/* ═══════════════════════════════════════════
   UTIL
   ═══════════════════════════════════════════ */
function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>
"""
=======
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

@app.get("/")
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
>>>>>>> origin/master
