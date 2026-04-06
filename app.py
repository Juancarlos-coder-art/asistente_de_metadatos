import json
import streamlit as st

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from cli import BLOCKS, build_prompt_for_block, build_contract

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Asistente HealthDCAT-AP-ES",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Fondo general */
.stApp {
    background-color: #f4f6f9;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0a1628;
    border-right: 2px solid #1e3a5f;
}
section[data-testid="stSidebar"] * {
    color: #c8d8f0 !important;
}
section[data-testid="stSidebar"] .stProgress > div > div {
    background-color: #2e86de !important;
}

/* Título principal */
.main-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: #0a1628;
    border-left: 4px solid #2e86de;
    padding-left: 16px;
    margin-bottom: 4px;
}
.main-subtitle {
    font-size: 0.9rem;
    color: #6b7f99;
    margin-left: 20px;
    margin-bottom: 24px;
    font-family: 'IBM Plex Mono', monospace;
}

/* Tarjeta de bloque */
.block-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #dde3ed;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(10,22,40,0.06);
}
.block-name {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #2e86de;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.block-question {
    font-size: 0.95rem;
    color: #2c3e50;
    line-height: 1.6;
    background: #f0f4fa;
    border-left: 3px solid #2e86de;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin-top: 8px;
}

/* Badge modo */
.badge-ia {
    background: #e8f4ff;
    color: #1a6fc4;
    border: 1px solid #b3d4f5;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
}
.badge-manual {
    background: #eafaf1;
    color: #1e8449;
    border: 1px solid #a9dfbf;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
}

/* Campos obligatorios */
.required-dot {
    color: #e74c3c;
    font-weight: bold;
}

/* Métricas sidebar */
.metric-box {
    background: #0f1f3d;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    text-align: center;
}
.metric-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #2e86de;
}
.metric-label {
    font-size: 0.75rem;
    color: #8899aa;
    margin-top: 2px;
}

/* JSON viewer */
.json-container {
    background: #0a1628;
    border-radius: 10px;
    padding: 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #7ecbff;
    max-height: 380px;
    overflow-y: auto;
    border: 1px solid #1e3a5f;
}

/* Navegación */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
}

/* Alerta custom */
.alert-ok {
    background: #eafaf1;
    border: 1px solid #a9dfbf;
    color: #1e8449;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.88rem;
}
.alert-warn {
    background: #fef9e7;
    border: 1px solid #f9e79f;
    color: #7d6608;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.88rem;
}
.alert-error {
    background: #fdedec;
    border: 1px solid #f5b7b1;
    color: #922b21;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.88rem;
}

/* Separador */
hr { border-color: #dde3ed; }

/* Ocultar menú hamburguesa */
#MainMenu {visibility: hidden;}
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

# Estado persistente
if "metadata_state" not in st.session_state:
    st.session_state.metadata_state = MetadataState("health_dcat_ap.yaml")
if "current_block_idx" not in st.session_state:
    st.session_state.current_block_idx = 0
if "block_done" not in st.session_state:
    st.session_state.block_done = set()

state: MetadataState = st.session_state.metadata_state
block_idx: int = st.session_state.current_block_idx
block = BLOCKS[block_idx]
total_blocks = len(BLOCKS)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 HealthDCAT-AP-ES")
    st.markdown("---")

    # Progreso global
    pct = int(len(st.session_state.block_done) / total_blocks * 100)
    st.markdown(f"**Progreso general**")
    st.progress(pct / 100)
    st.caption(f"{len(st.session_state.block_done)} / {total_blocks} bloques completados")

    st.markdown("---")

    # Métricas rápidas
    filled = sum(1 for v in state.data.values() if v not in (None, "", [], {}))
    missing_count = len(state.missing_required())

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-num">{filled}</div>
            <div class="metric-label">campos rellenos</div>
        </div>""", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-num" style="color:#e74c3c">{missing_count}</div>
            <div class="metric-label">obligatorios pendientes</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Bloques**")

    # Lista de bloques navegables
    for i, b in enumerate(BLOCKS):
        done = i in st.session_state.block_done
        icon = "✅" if done else ("▶️" if i == block_idx else "○")
        label = f"{icon} {b['name'].replace('_', ' ').title()}"
        if st.button(label, key=f"nav_{i}", use_container_width=True):
            st.session_state.current_block_idx = i
            st.rerun()

    st.markdown("---")

    # Descargar JSON
    json_str = json.dumps(state.data, indent=2, ensure_ascii=False)
    st.download_button(
        label="⬇️ Descargar metadata.json",
        data=json_str,
        file_name="metadata_output.json",
        mime="application/json",
        use_container_width=True
    )


# ─────────────────────────────────────────────
# CABECERA
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="main-title">Asistente de Metadatos HealthDCAT-AP</div>
<div class="main-subtitle">Esquema sanitario europeo · Bloque {block_idx + 1} de {total_blocks}</div>
""", unsafe_allow_html=True)

# Barra de progreso del bloque actual
st.progress((block_idx + 1) / total_blocks)


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
# MODO: IA o MANUAL
# ─────────────────────────────────────────────
tab_ia, tab_manual = st.tabs(["🤖 Autocompletar con IA", "✍️ Rellenar manualmente"])

partial = {}

# ── TAB IA ──
with tab_ia:
    if not llm_available():
        st.warning("⚠️ No hay LLM disponible. Configura tu API key en `llm_provider.py`.")
    else:
        st.markdown("Describe este bloque con tus propias palabras y la IA extraerá los campos automáticamente.")
        user_context = st.text_area(
            "Tu descripción",
            placeholder="Ej.: El dataset trata sobre casos de viruela del mono en España durante 2023, publicado por el Ministerio de Sanidad...",
            height=120,
            key="ia_context"
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

                        partial = {
                            name: ai_result.get(name, None)
                            for name in block["fields"]
                        }
                        state.merge_partial(partial)
                        st.session_state.block_done.add(block_idx)

                        st.markdown('<div class="alert-ok">✅ Bloque autocompletado correctamente.</div>', unsafe_allow_html=True)
                        st.json(partial)

                    except Exception as e:
                        st.markdown(f'<div class="alert-error">❌ Error: {e}</div>', unsafe_allow_html=True)

# ── TAB MANUAL ──
with tab_manual:
    st.markdown("Rellena los campos del bloque uno a uno.")

    for field_name in block["fields"]:
        # applicable_legislation → solo automático
        if field_name == "applicable_legislation":
            st.info("📋 **applicable_legislation** se rellena automáticamente al guardar el resultado final.")
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

        raw_value = st.text_input(
            display_label,
            value=default_val,
            help=f"{help_text}\n\n*Campo obligatorio*" if required else help_text,
            key=f"manual_{block['name']}_{field_name}"
        )

        partial[field_name] = parse_input(field_name, raw_value, schema) if raw_value else None

    st.markdown("")
    if st.button("💾 Guardar bloque", type="primary", key="btn_manual"):
        # Filtrar Nones para no sobreescribir con vacíos
        to_merge = {k: v for k, v in partial.items() if v is not None}
        state.merge_partial(to_merge)
        st.session_state.block_done.add(block_idx)
        st.markdown('<div class="alert-ok">✅ Bloque guardado correctamente.</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PANEL INFERIOR: Estado + Validación
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
# NAVEGACIÓN ENTRE BLOQUES
# ─────────────────────────────────────────────
st.markdown("---")
col_prev, col_info, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("⬅️ Anterior", disabled=(block_idx == 0), use_container_width=True):
        st.session_state.current_block_idx -= 1
        st.rerun()

with col_info:
    st.markdown(
        f"<div style='text-align:center; color:#6b7f99; font-family:IBM Plex Mono,monospace; font-size:0.85rem; padding-top:8px'>"
        f"Bloque {block_idx + 1} / {total_blocks} · {block['name'].replace('_', ' ')}"
        f"</div>",
        unsafe_allow_html=True
    )

with col_next:
    if block_idx < total_blocks - 1:
        if st.button("➡️ Siguiente", use_container_width=True, type="primary"):
            st.session_state.current_block_idx += 1
            st.rerun()
    else:
        # Último bloque: botón de finalizar
        if st.button("🏁 Finalizar y guardar", use_container_width=True, type="primary"):
            # Insertar legislación automática
            state.data["applicable_legislation"] = [
                {
                    "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
                    "label": "GDPR"
                }
            ]
            with open("metadata_output.json", "w", encoding="utf-8") as f:
                json.dump(state.data, f, indent=2, ensure_ascii=False)
            st.balloons()
            st.success("✅ Metadatos completos guardados en `metadata_output.json`")