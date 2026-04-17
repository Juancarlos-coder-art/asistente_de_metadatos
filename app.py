import json
import streamlit as st

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from assistant.rag_helper import get_missing_descriptions, get_block_missing
from cli import BLOCKS, build_prompt_for_block, build_contract

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Asistente HealthDCAT-AP-ES",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items = 
{
        "About": """
        ## 🏥 Asistente HealthDCAT-AP-ES

        Asistente conversacional para la creación de metadatos
        conforme al perfil **HealthDCAT-AP-ES**.
        """
    }

)

# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background-color: #f4f6f9; }

section[data-testid="stSidebar"] {
    background-color: #0a1628;
    border-right: 2px solid #1e3a5f;
}
section[data-testid="stSidebar"] * { color: #c8d8f0 !important; }
section[data-testid="stSidebar"] .stProgress > div > div { background-color: #2e86de !important; }

/* Bienvenida */
.welcome-card {
    background: white; border-radius: 16px; border: 1px solid #dde3ed;
    padding: 56px 64px; margin: 40px auto; max-width: 800px;
    box-shadow: 0 4px 24px rgba(10,22,40,0.08); text-align: center;
}
.welcome-logo { font-size: 3.5rem; margin-bottom: 20px; }
.welcome-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.7rem;
    font-weight: 600; color: #0a1628; margin-bottom: 12px; line-height: 1.3;
}
.welcome-subtitle { font-size: 1rem; color: #4a6080; line-height: 1.8; }
.welcome-divider { border: none; border-top: 1px solid #e0e8f4; margin: 36px 0; }
.guide-box {
    background: #f0f4fa; border: 1px solid #c5d8f0;
    border-radius: 12px; padding: 24px 28px; text-align: left;
}
.guide-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: #2e86de;
    font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 8px;
}
.guide-desc { font-size: 0.93rem; color: #4a6080; line-height: 1.6; margin-bottom: 14px; }

/* Cabecera */
.main-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.8rem;
    font-weight: 600; color: #0a1628; border-left: 4px solid #2e86de;
    padding-left: 16px; margin-bottom: 4px;
}
.main-subtitle {
    font-size: 0.9rem; color: #6b7f99; margin-left: 20px;
    margin-bottom: 24px; font-family: 'IBM Plex Mono', monospace;
}

/* Tarjeta de bloque */
.block-card {
    background: white; border-radius: 12px; border: 1px solid #dde3ed;
    padding: 24px 28px; margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(10,22,40,0.06);
}
.block-name {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
    color: #2e86de; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;
}
.block-question {
    font-size: 0.95rem; color: #2c3e50; line-height: 1.6;
    background: #f0f4fa; border-left: 3px solid #2e86de;
    padding: 12px 16px; border-radius: 0 8px 8px 0; margin-top: 8px;
}

/* Métricas sidebar */
.metric-box {
    background: #0f1f3d; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; text-align: center;
}
.metric-num { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 600; color: #2e86de; }
.metric-label { font-size: 0.75rem; color: #8899aa; margin-top: 2px; }

/* Aviso campo faltante (sidebar) */
.missing-field-card {
    background: #1a2f4a; border: 1px solid #2e5c8a;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
}
.missing-field-name {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #f0a500; font-weight: 600; margin-bottom: 3px;
}
.missing-field-desc { font-size: 0.78rem; color: #a0b8d0; line-height: 1.4; }
.missing-field-example { font-size: 0.73rem; color: #5a8fa8; margin-top: 4px; font-style: italic; }

/* Aviso bloque (pantalla principal) */
.block-warning-card {
    background: #fffbf0; border: 1px solid #f0c040;
    border-radius: 10px; padding: 16px 20px; margin: 12px 0;
}
.block-warning-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
    color: #b07800; font-weight: 600; margin-bottom: 10px;
}
.bw-field {
    background: white; border: 1px solid #f0d080;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
}
.bw-field-name { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #c08000; font-weight: 600; }
.bw-field-label { font-size: 0.85rem; color: #3a3000; font-weight: 500; margin-bottom: 4px; }
.bw-field-desc { font-size: 0.85rem; color: #5a4a00; line-height: 1.5; }
.bw-field-example { font-size: 0.78rem; color: #888; margin-top: 4px; font-style: italic; }
.bw-field-suggest { font-size: 0.82rem; color: #1a6fc4; margin-top: 6px; font-weight: 500; }

/* JSON viewer */
.json-container {
    background: #0a1628; border-radius: 10px; padding: 16px;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
    color: #7ecbff; max-height: 380px; overflow-y: auto; border: 1px solid #1e3a5f;
}

/* Alertas */
.alert-ok { background: #eafaf1; border: 1px solid #a9dfbf; color: #1e8449; border-radius: 8px; padding: 10px 16px; font-size: 0.88rem; }
.alert-warn { background: #fef9e7; border: 1px solid #f9e79f; color: #7d6608; border-radius: 8px; padding: 10px 16px; font-size: 0.88rem; }
.alert-error { background: #fdedec; border: 1px solid #f5b7b1; color: #922b21; border-radius: 8px; padding: 10px 16px; font-size: 0.88rem; }

hr { border-color: #dde3ed; }
# MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARGA DE RECURSOS
# ─────────────────────────────────────────────
@st.cache_resource
def load_schema():
    return HealthDCATAPSchema("health_dcat_ap.yaml")

schema = load_schema()

if "metadata_state" not in st.session_state:
    st.session_state.metadata_state = MetadataState("health_dcat_ap.yaml")
if "current_block_idx" not in st.session_state:
    st.session_state.current_block_idx = 0
if "block_done" not in st.session_state:
    st.session_state.block_done = set()
if "started" not in st.session_state:
    st.session_state.started = False
if "show_missing_warning" not in st.session_state:
    st.session_state.show_missing_warning = False
if "pending_next_block" not in st.session_state:
    st.session_state.pending_next_block = False

state: MetadataState = st.session_state.metadata_state
block_idx: int = st.session_state.current_block_idx
total_blocks = len(BLOCKS)


# ─────────────────────────────────────────────
# PANTALLA DE BIENVENIDA
# ─────────────────────────────────────────────
if not st.session_state.started:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-logo">🏥</div>
        <div class="welcome-title">
            Hola, soy el Asistente conversacional del ENDS.<br>
            Te ayudaré a metadatar tu conjunto de datos.
        </div>
        <div class="welcome-subtitle">
            El proceso está dividido en bloques de preguntas.<br>
            Puedes responder con tus propias palabras y la IA estructurará
            la información conforme al esquema <strong>HealthDCAT-AP-ES</strong>.
        </div>
        <hr class="welcome-divider">
        <div class="guide-box">
            <div class="guide-title">📄 Guía de campos</div>
            <div class="guide-desc">
                Si quieres información sobre los campos que necesitamos
                para metadatar tu dataset, descarga aquí la guía completa.
            </div>
    """, unsafe_allow_html=True)

    try:
        with open("guia_campos_ends.docx", "rb") as f:
            st.download_button(
                label="⬇️ Pincha aquí para descargar la guía de campos (.docx)",
                data=f.read(),
                file_name="guia_campos_ends.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
    except FileNotFoundError:
        st.info("ℹ️ Coloca `guia_campos_ends.docx` en la raíz del proyecto.")

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🚀 Comenzar a metadatar", type="primary", use_container_width=True):
            st.session_state.started = True
            st.rerun()
    st.stop()


# ─────────────────────────────────────────────
# BLOQUE ACTUAL
# ─────────────────────────────────────────────
block = BLOCKS[block_idx]

# Campos faltantes del bloque actual
block_missing = get_block_missing(block, state.data)
# DESPUÉS — pon esto
block_missing_info = get_missing_descriptions(
    block_missing,
    use_llm=False,
    call_llm_fn=None
)

# Campos obligatorios pendientes globales
all_missing = state.missing_required()
all_missing_info = get_missing_descriptions(
    all_missing,
    use_llm=False  # sidebar sin LLM para no ralentizar
)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 HealthDCAT-AP-ES")
    st.markdown("---")

    pct = int(len(st.session_state.block_done) / total_blocks * 100)
    st.markdown("**Progreso general**")
    st.progress(pct / 100)
    st.caption(f"{len(st.session_state.block_done)} / {total_blocks} bloques completados")
    st.markdown("---")

    filled = sum(1 for v in state.data.values() if v not in (None, "", [], {}))
    missing_count = len(all_missing)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'<div class="metric-box"><div class="metric-num">{filled}</div><div class="metric-label">campos rellenos</div></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#e74c3c">{missing_count}</div><div class="metric-label">obligatorios pendientes</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Bloques**")
    for i, b in enumerate(BLOCKS):
        done = i in st.session_state.block_done
        icon = "✅" if done else ("▶️" if i == block_idx else "○")
        if st.button(f"{icon} {b['name'].replace('_', ' ').title()}", key=f"nav_{i}", use_container_width=True):
            st.session_state.current_block_idx = i
            st.session_state.show_missing_warning = False
            st.rerun()

    # ── AVISOS DE CAMPOS FALTANTES EN SIDEBAR ──
    if all_missing_info:
        st.markdown("---")
        st.markdown("**⚠️ Campos obligatorios pendientes**")
        for item in all_missing_info:
            st.markdown(f"""
            <div class="missing-field-card">
                <div class="missing-field-name">📌 {item['field']}</div>
                <div class="missing-field-desc"><strong>{item['label']}</strong> · {item['descripcion']}</div>
                {"<div class='missing-field-example'>Ej: " + item['ejemplo'] + "</div>" if item['ejemplo'] else ""}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    try:
        with open("guia_campos_ends.docx", "rb") as f:
            st.download_button("📄 Guía de campos", data=f.read(),
                file_name="guia_campos_ends.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
    except FileNotFoundError:
        pass

    json_str = json.dumps(state.data, indent=2, ensure_ascii=False)
    st.download_button("⬇️ Descargar metadata.json", data=json_str,
        file_name="metadata_output.json", mime="application/json", use_container_width=True)

    if st.button("← Volver al inicio", use_container_width=True):
        st.session_state.started = False
        st.rerun()


# ─────────────────────────────────────────────
# CABECERA
# ─────────────────────────────────────────────
st.markdown(f'<div class="main-title">Asistente de Metadatos HealthDCAT-AP</div><div class="main-subtitle">Esquema sanitario europeo · Bloque {block_idx + 1} de {total_blocks}</div>', unsafe_allow_html=True)
st.progress((block_idx + 1) / total_blocks)


# ─────────────────────────────────────────────
# AVISO DE CAMPOS FALTANTES (pantalla principal)
# Se muestra al intentar pasar de bloque con campos vacíos
# ─────────────────────────────────────────────
if st.session_state.show_missing_warning and block_missing_info:
    st.markdown(f"""
    <div class="block-warning-card">
        <div class="block-warning-title">
            ⚠️ Hay {len(block_missing_info)} campo(s) sin rellenar en este bloque.
            Puedes completarlos ahora o continuar igualmente.
        </div>
    """, unsafe_allow_html=True)

    for item in block_missing_info:
        sugerencia_html = f'<div class="bw-field-suggest">💡 {item["sugerencia"]}</div>' if item.get("sugerencia") else ""
        ejemplo_html = f'<div class="bw-field-example">Ejemplo: {item["ejemplo"]}</div>' if item.get("ejemplo") else ""
        st.markdown(f"""
        <div class="bw-field">
            <div class="bw-field-name">{item['field']}</div>
            <div class="bw-field-label">{item['label']}{"  🔴" if item['obligatorio'] else ""}</div>
            <div class="bw-field-desc">{item['descripcion']}</div>
            {ejemplo_html}
            {sugerencia_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    col_stay, col_continue = st.columns(2)
    with col_stay:
        if st.button("✏️ Volver a rellenar", use_container_width=True):
            st.session_state.show_missing_warning = False
            st.session_state.pending_next_block = False
            st.rerun()
    with col_continue:
        if st.button("➡️ Continuar de todas formas", use_container_width=True, type="primary"):
            st.session_state.show_missing_warning = False
            st.session_state.pending_next_block = False
            st.session_state.block_done.add(block_idx)
            st.session_state.current_block_idx += 1
            st.rerun()


# ─────────────────────────────────────────────
# TARJETA DEL BLOQUE
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="block-card">
    <div class="block-name">📦 Bloque {block_idx + 1} · {block['name'].replace('_', ' ').upper()}</div>
    <div class="block-question">{block['question']}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS: IA / MANUAL
# ─────────────────────────────────────────────
tab_ia, tab_manual = st.tabs(["🤖 Autocompletar con IA", "✍️ Rellenar manualmente"])
partial = {}

with tab_ia:
    if not llm_available():
        st.warning("⚠️ No hay LLM disponible. Configura tu API key en `llm_provider.py`.")
    else:
        st.markdown("Describe este bloque con tus propias palabras y la IA extraerá los campos automáticamente.")
        user_context = st.text_area(
            "Tu descripción",
            placeholder="Ej.: El dataset trata sobre casos de viruela del mono en España durante 2023...",
            height=120, key="ia_context"
        )
        if st.button("⚡ Autocompletar bloque", type="primary", key="btn_ia"):
            if not user_context.strip():
                st.warning("Escribe algo antes de autocompletar.")
            else:
                with st.spinner("Analizando tu descripción..."):
                    try:
                        prompt = build_prompt_for_block(schema, block, user_context)
                        contract = build_contract(block)
                        ai_result = call_llm(prompt, contract, user_context)
                        partial = {name: ai_result.get(name, None) for name in block["fields"]}
                        state.merge_partial(partial)
                        st.session_state.block_done.add(block_idx)
                        st.session_state.show_missing_warning = False
                        st.markdown('<div class="alert-ok">✅ Bloque autocompletado correctamente.</div>', unsafe_allow_html=True)
                        st.json(partial)
                    except Exception as e:
                        st.markdown(f'<div class="alert-error">❌ Error: {e}</div>', unsafe_allow_html=True)

with tab_manual:
    st.markdown("Rellena los campos del bloque uno a uno.")
    for field_name in block["fields"]:
        if field_name == "applicable_legislation":
            st.info("📋 **applicable_legislation** se rellena automáticamente al finalizar.")
            continue
        field = schema.get_field(field_name)
        label = field.get("label", field_name) if field else field_name
        help_text = field.get("help_text", "") if field else ""
        required = field.get("required", False) if field else False
        display_label = f"{'🔴 ' if required else ''}{label}"
        current_val = state.data.get(field_name)
        default_val = ""
        if current_val and isinstance(current_val, str):
            default_val = current_val
        elif current_val and not isinstance(current_val, str):
            default_val = json.dumps(current_val, ensure_ascii=False)
        raw_value = st.text_input(display_label, value=default_val,
            help=f"{help_text}\n\n*Campo obligatorio*" if required else help_text,
            key=f"manual_{block['name']}_{field_name}")
        partial[field_name] = raw_value if raw_value else None

    if st.button("💾 Guardar bloque", type="primary", key="btn_manual"):
        to_merge = {k: v for k, v in partial.items() if v is not None}
        state.merge_partial(to_merge)
        st.session_state.block_done.add(block_idx)
        st.session_state.show_missing_warning = False
        st.markdown('<div class="alert-ok">✅ Bloque guardado correctamente.</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ESTADO + VALIDACIÓN
# ─────────────────────────────────────────────
st.markdown("---")
col_json, col_val = st.columns([3, 2])

with col_json:
    st.markdown("#### 📄 Estado actual del metadata")
    json_preview = json.dumps(state.data, indent=2, ensure_ascii=False)
    st.markdown(f'<div class="json-container"><pre>{json_preview}</pre></div>', unsafe_allow_html=True)

with col_val:
    st.markdown("#### 🔍 Validación en tiempo real")
    errors = state.validate_types_basic()
    missing = state.missing_required()
    if not errors and not missing:
        st.markdown('<div class="alert-ok">✅ Todo correcto. Sin errores ni campos pendientes.</div>', unsafe_allow_html=True)
    else:
        if errors:
            st.markdown('<div class="alert-error">⚠️ Errores de formato:</div>', unsafe_allow_html=True)
            for err in errors:
                st.markdown(f"- `{err}`")
        if missing:
            st.markdown('<div class="alert-warn">📋 Campos obligatorios pendientes:</div>', unsafe_allow_html=True)
            for m in missing:
                st.markdown(f"- `{m}`")


# ─────────────────────────────────────────────
# NAVEGACIÓN
# ─────────────────────────────────────────────
st.markdown("---")
col_prev, col_info, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("⬅️ Anterior", disabled=(block_idx == 0), use_container_width=True):
        st.session_state.current_block_idx -= 1
        st.session_state.show_missing_warning = False
        st.rerun()

with col_info:
    st.markdown(
        f"<div style='text-align:center;color:#6b7f99;font-family:IBM Plex Mono,monospace;font-size:0.85rem;padding-top:8px'>"
        f"Bloque {block_idx + 1} / {total_blocks} · {block['name'].replace('_', ' ')}</div>",
        unsafe_allow_html=True
    )

with col_next:
    if block_idx < total_blocks - 1:
        if st.button("➡️ Siguiente bloque", use_container_width=True, type="primary"):
            # Comprobar campos faltantes antes de avanzar
            current_missing = get_block_missing(block, state.data)
            if current_missing and not st.session_state.show_missing_warning:
                st.session_state.show_missing_warning = True
                st.rerun()
            else:
                st.session_state.show_missing_warning = False
                st.session_state.block_done.add(block_idx)
                st.session_state.current_block_idx += 1
                st.rerun()
    else:
        if st.button("🏁 Finalizar y guardar", use_container_width=True, type="primary"):
            state.data["applicable_legislation"] = [{
                "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
                "label": "GDPR"
            }]
            with open("metadata_output.json", "w", encoding="utf-8") as f:
                json.dump(state.data, f, indent=2, ensure_ascii=False)
            st.balloons()
            st.success("✅ Metadatos completos guardados en `metadata_output.json`")