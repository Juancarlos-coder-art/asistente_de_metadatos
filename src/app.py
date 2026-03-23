import json
import io
from pathlib import Path

import streamlit as st
from rdflib import Graph, Namespace, Literal, URIRef
from pyshacl import validate

from schema_loader import HealthDCATAPSchema
from assistant.metadata_state import MetadataState
from assistant.llm_provider import call_llm, llm_available
from cli import BLOCKS, build_prompt_for_block, build_contract, parse_input

# ----------------- Config -----------------
st.set_page_config(page_title="Asistente HealthDCAT-AP", layout="wide")
st.title("Asistente multicampo HealthDCAT-AP")

# ----------------- Carga de schema -----------------
@st.cache_resource
def load_schema():
    return HealthDCATAPSchema("health_dcat_ap.json")

schema = load_schema()

# ----------------- Estado persistente -----------------
if "metadata_state" not in st.session_state:
    st.session_state.metadata_state = MetadataState("health_dcat_ap.json")

if "current_block_idx" not in st.session_state:
    st.session_state.current_block_idx = 0

state = st.session_state.metadata_state
block_idx = st.session_state.current_block_idx
block = BLOCKS[block_idx]

# ----------------- Carga de SHACL (opcional) -----------------

@st.cache_resource
def load_shapes() -> Graph | None:
    # Directorio base = carpeta donde está este app.py
    base_dir = Path(__file__).resolve().parent
    # Candidatos de carpeta con shapes
    candidate_dirs = [
        base_dir / "tools" / "shacl",
        base_dir / "tools",
        base_dir.parent / "tools" / "shacl",
        base_dir.parent / "tools",
    ]

    g = Graph()
    found_any = False

    for d in candidate_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.suffix.lower() in (".ttl", ".jsonld", ".json"):
                try:
                    fmt = "turtle" if f.suffix.lower() == ".ttl" else "json-ld"
                    g.parse(f.as_posix(), format=fmt)
                    found_any = True
                except Exception as e:
                    st.warning(f"No se pudo cargar {f.name} desde {d}: {e}")

    if found_any and len(g) > 0:
        st.info(f"Shapes cargados. Total de triples en SHACL: {len(g)}")
        return g

    st.caption("No se localizaron shapes. Revisar rutas: tools/ o tools/shacl.")
    return None


shacl_graph = load_shapes()  # None si no hay shapes

# ----------------- UI del bloque actual -----------------
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

# ----------------- Validaciones básicas & missing -----------------
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

# ----------------- Construcción RDF desde state -----------------
def build_rdf_from_state(data: dict) -> Graph:
    """
    Convierte el JSON parcial/final de state.data en un grafo RDF mínimo
    para validar con SHACL. Completa este mapeo con tu perfil HealthDCAT‑AP.
    """
    g = Graph()

    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    DCT  = Namespace("http://purl.org/dc/terms/")
    XSD  = Namespace("http://www.w3.org/2001/XMLSchema#")

    g.bind("dcat", DCAT)
    g.bind("dct", DCT)

    ds_uri = URIRef(data.get("uri") or "http://example.org/dataset/temp")
    g.add((ds_uri, g.namespace_manager.compute_qname("rdf:type")[1], DCAT.Dataset))

    title = data.get("title") or data.get("name")
    if title:
        g.add((ds_uri, DCT.title, Literal(title)))

    notes = data.get("notes")
    if notes:
        g.add((ds_uri, DCT.description, Literal(notes)))

    identifier = data.get("identifier")
    if identifier:
        g.add((ds_uri, DCT.identifier, Literal(identifier)))

    issued = data.get("issued")
    if issued:
        g.add((ds_uri, DCT.issued, Literal(issued, datatype=XSD.date)))

    modified = data.get("modified")
    if modified:
        g.add((ds_uri, DCT.modified, Literal(modified, datatype=XSD.date)))

    langs = data.get("language") or []
    if isinstance(langs, list):
        for lg in langs:
            g.add((ds_uri, DCT.language, Literal(lg)))

    tags = data.get("tag_string") or data.get("keywords") or []
    if isinstance(tags, list):
        for kw in tags:
            g.add((ds_uri, DCAT.keyword, Literal(kw)))
    elif isinstance(tags, str) and tags.strip():
        g.add((ds_uri, DCAT.keyword, Literal(tags.strip())))

    publisher = data.get("publisher")
    if publisher:
        g.add((ds_uri, DCT.publisher, Literal(publisher)))

    # TODO: Añade aquí tu mapeo completo: theme, contact, distributions, etc.

    return g

def run_shacl_validation(data_graph: Graph, shacl_graph: Graph, fmt: str = "human"):
    serialize_report_graph = None if fmt == "human" else fmt
    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference="rdfs",
        debug=False,
        serialize_report_graph=serialize_report_graph
    )
    return conforms, report_graph, report_text

# ----------------- Navegación & Guardado -----------------
col_prev, col_next, col_mid, col_save = st.columns([1,1,2,2])

with col_prev:
    if st.button("⬅️ Bloque anterior", disabled=block_idx == 0):
        st.session_state.current_block_idx -= 1
        st.rerun()

with col_next:
    if st.button("➡️ Siguiente bloque", disabled=block_idx == len(BLOCKS) - 1):
        st.session_state.current_block_idx += 1
        st.rerun()

with col_mid:
    # Validar on-demand si hay shapes
    if shacl_graph is not None:
        if st.button("✅ Validar con SHACL"):
            data_graph = build_rdf_from_state(state.data)
            ok, rep_g, rep_t = run_shacl_validation(data_graph, shacl_graph, fmt="human")
            st.subheader("Informe de validación SHACL")
            st.write(f"**Conforme:** {'✅ Sí' if ok else '❌ No'}")
            st.code(rep_t, language="text")
    else:
        st.caption("No se han encontrado shapes en tools/shacl — la validación SHACL es opcional.")

with col_save:
    if st.button("💾 Guardar JSON final"):
        with open("metadata_output.json", "w", encoding="utf-8") as f:
            json.dump(state.data, f, indent=2, ensure_ascii=False)
        st.success("Metadatos guardados en metadata_output.json")

        # Validación automática post-guardado si hay shapes
        if shacl_graph is not None:
            data_graph = build_rdf_from_state(state.data)
            ok, rep_g, rep_t = run_shacl_validation(data_graph, shacl_graph, fmt="human")
            st.subheader("Informe de validación SHACL (post-guardado)")
            st.write(f"**Conforme:** {'✅ Sí' if ok else '❌ No'}")
            st.code(rep_t, language="text")
        else:
            st.info("No se ejecutó validación SHACL porque no se encontraron shapes en tools/shacl.")
