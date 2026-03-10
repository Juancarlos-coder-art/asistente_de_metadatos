import json
import streamlit as st

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from cli import BLOCKS, build_prompt_for_block, build_contract, parse_input


st.set_page_config(page_title="Asistente HealthDCAT-AP", layout="wide")

st.title("Asistente multicampo HealthDCAT-AP")

# Cargar schema una sola vez
@st.cache_resource
def load_schema():
    return HealthDCATAPSchema("health_dcat_ap.json")

schema = load_schema()

# Estado persistente de la app
if "metadata_state" not in st.session_state:
    st.session_state.metadata_state = MetadataState("health_dcat_ap.json")

if "current_block_idx" not in st.session_state:
    st.session_state.current_block_idx = 0

state = st.session_state.metadata_state
block_idx = st.session_state.current_block_idx
block = BLOCKS[block_idx]

st.subheader(f"Bloque: {block['name']}")
st.write(block["question"])

modo = st.radio(
    "Modo de rellenado",
    options=["Manual", "IA"] if llm_available() else ["Manual"],
    horizontal=True
)

partial = {}

if modo == "IA":
    user_context = st.text_area(
        "Describe este bloque en lenguaje natural",
        placeholder="Ej.: Dataset sobre viruela del mono en España, con versión 1.0, publicado por..."
    )

    if st.button("Autocompletar con IA"):
        prompt = build_prompt_for_block(schema, block, user_context)
        contract = build_contract(block)

        try:
            ai_result = call_llm(prompt, contract, user_context)

            for name in block["fields"]:
                partial[name] = ai_result.get(name, None)

            state.merge_partial(partial)
            st.success("Bloque autocompletado con IA.")
            st.json(partial)

        except Exception as e:
            st.error(f"Error usando la IA: {e}")

else:
    st.markdown("### Campos del bloque")
    for field_name in block["fields"]:
        field = schema.get_field(field_name)

        if field:
            label = field.get("label", field_name)
            help_text = field.get("help_text", "")
            required = field.get("required", False)
        else:
            label = field_name
            help_text = ""
            required = False

        raw_value = st.text_input(
            f"{label}{' *' if required else ''}",
            help=help_text,
            key=f"{block['name']}_{field_name}"
        )
        partial[field_name] = parse_input(field_name, raw_value)

    if st.button("Guardar bloque manual"):
        state.merge_partial(partial)
        st.success("Bloque guardado.")

errors = state.validate_types_basic()
missing = state.missing_required()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Estado parcial")
    st.json(state.data)

with col2:
    st.markdown("### Validación")
    if errors:
        st.warning("Validaciones detectadas:")
        for err in errors:
            st.write(f"- {err}")
    else:
        st.success("Sin errores de tipo detectados.")

    if missing:
        st.info("Campos obligatorios pendientes:")
        for m in missing:
            st.write(f"- {m}")

st.divider()

col_prev, col_next, col_save = st.columns(3)

with col_prev:
    if st.button("⬅️ Bloque anterior", disabled=block_idx == 0):
        st.session_state.current_block_idx -= 1
        st.rerun()

with col_next:
    if st.button("➡️ Siguiente bloque", disabled=block_idx == len(BLOCKS) - 1):
        st.session_state.current_block_idx += 1
        st.rerun()

with col_save:
    if st.button("💾 Guardar JSON final"):
        with open("metadata_output.json", "w", encoding="utf-8") as f:
            json.dump(state.data, f, indent=2, ensure_ascii=False)
        st.success("Metadatos guardados en metadata_output.json")