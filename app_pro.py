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
    page_title="ENDS Metadata Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME — Professional dark/light system
# ─────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

html { color-scheme: light only !important; }
@media (prefers-color-scheme: dark) { :root { color-scheme: light only !important; } }

/* Force Streamlit light mode */
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.stApp,
.main .block-container,
[data-testid="stMainBlockContainer"] {
    background-color: var(--bg) !important;
    color: var(--ink) !important;
    color-scheme: light !important;
}
[data-testid="stSidebar"] > div { color-scheme: light !important; }
[data-theme="dark"], [data-testid="stApp"][data-theme="dark"] {
    color-scheme: light !important;
}
html[data-theme="dark"] { color-scheme: light !important; }
body { background-color: var(--bg) !important; color-scheme: light !important; }

:root {
    --f:  'Inter', system-ui, sans-serif;
    --m:  'Fira Code', 'Consolas', monospace;

    /* sidebar (dark) */
    --sb: #03083c;
    --sb2: #1E3B2D;
    --sb-b: #335542;
    --sb-t: #E2F0E4;
    --sb-d: #94B8A5;
    --sb-f: #648B7B;

    /* main area (light) */
    --bg:       #f0f4f1;
    --card:     #ffffff;
    --raised:   #f7faf8;
    --bdr:      #c9d6ce;
    --bdr2:     #8faa9c;
    --ink:      #0d1f15;
    --dim:      #3d5448;
    --faint:    #8faa9c;

    --ac:       #10b981;
    --ac-g:     rgba(16,185,129,.12);
    --ac-s:     #d1fae5;
    --ac-fg:    #ffffff;

    --ok:       #059669;
    --ok-bg:    #ecfdf5;
    --warn:     #d97706;
    --warn-bg:  #fffbeb;
    --err:      #dc2626;
    --err-bg:   #fef2f2;

    --r:  12px;
    --rs: 8px;
    --shadow: 0 1px 3px rgba(0,0,0,.06);
    --shadow-lg: 0 4px 16px rgba(0,0,0,.08);
}

/* ── Reset ── */
html, body, [class*="css"] {
    font-family: var(--f) !important;
    color: var(--ink);
}
.stApp { background: var(--bg); }
/* Hide menu and footer, keep header for sidebar toggle */
#MainMenu, footer { visibility: hidden; }
/* Make header transparent — keep only the sidebar toggle button */
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
}
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
hr { border-color: var(--bdr); margin: 1.5rem 0; }
/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--sb);
    border-right: 1px solid var(--sb-b);
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stText"],
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--sb-d) !important;
}
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] b {
    color: var(--sb-t) !important;
}
section[data-testid="stSidebar"] div.stButton > button {
    background: rgba(255,255,255,.06) !important;
    color: var(--sb-d) !important;
    border: 0.8px solid var(--sb-b) !important;
    font-size: .8rem !important;
    padding: 6px 10px !important;
    min-height: 34px !important;
}
section[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255,255,255,.12) !important;
    color: var(--sb-t) !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,.06) !important;
    color: var(--sb-d) !important;
    border: 1px solid var(--sb-b) !important;
    font-size: .8rem !important;
    padding: 6px 10px !important;
    min-height: 34px !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {
    background: rgba(255,255,255,.12) !important;
    color: var(--sb-t) !important;
}
section[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(255,255,255,.06) !important;
    color: var(--sb-d) !important;
    border-color: var(--sb-b) !important;
}
section[data-testid="stSidebar"] [data-testid="stProgress"] > div > div,
section[data-testid="stSidebar"] .stProgress > div > div {
    background: var(--ac) !important;
}
.sb-brand {
    font-weight: 800;
    font-size: 1.2rem;
    color: var(--sb-t) !important;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sb-brand .dot {
    display: inline-block;
    width: 9px; height: 9px;
    border-radius: 50%;
    background: var(--ac);
}
.sb-title {
    font-family: var(--f);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--sb-t) !important;
    line-height: 1.3;
    margin-bottom: 2px;
}
.sb-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,.08);
    margin: 14px 0;
}
.sb-label {
    font-family: var(--m);
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--sb-f) !important;
    margin-bottom: 4px;
}
.sb-stat {
    background: rgba(255,255,255,.05);
    border: 1px solid var(--sb-b);
    border-radius: var(--rs);
    padding: 12px 8px;
    text-align: center;
}
.sb-stat-num {
    font-family: var(--m);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--sb-t) !important;
    line-height: 1;
}
.sb-stat-label {
    font-size: 0.6rem;
    color: var(--sb-f) !important;
    text-transform: uppercase;
    letter-spacing: .04em;
    margin-top: 2px;
}
.sb-stat-num.danger { color: #FFB700 !important; }

/* progress ring */
.ring-w{display:flex;flex-direction:column;align-items:center;gap:6px;padding:10px 0}
.ring{position:relative;width:84px;height:84px}
.ring svg{transform:rotate(-90deg)}
.ring circle{fill:none;stroke-width:5;stroke-linecap:round}
.ring .bg{stroke:var(--sb-b)}.ring .fg{stroke:var(--ac);transition:stroke-dashoffset .5s}
.ring .lbl{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:var(--m);font-size:1.1rem;font-weight:700;color:var(--sb-t)}

/* sidebar steps */
.sb-steps { display:flex; flex-direction:column; gap:4px; }
.sb-step {
    display:flex; align-items:center; gap:8px;
    padding:8px 10px; border-radius:var(--rs);
    border:1px solid transparent;
    transition:.15s;
}
.sb-step:hover { background:rgba(255,255,255,.05); border-color:var(--sb-b); }
.sb-step .sn {
    width:26px; height:26px; border-radius:50%; display:flex;
    align-items:center; justify-content:center; font-size:.72rem;
    font-weight:700; flex-shrink:0;
    background:var(--sb2); color:var(--sb-d); border:2px solid var(--sb-b);
}
.sb-step span { font-size:.8rem; font-weight:500; color:var(--sb-d); }
.sb-step.active { background:rgba(16,185,129,.15); border-color:var(--ac); }
.sb-step.active .sn { background:var(--ac); color:var(--ac-fg); border-color:var(--ac); }
.sb-step.active span { color:var(--sb-t); font-weight:600; }
.sb-step.done .sn { background:var(--ok); color:var(--ac-fg); border-color:var(--ok); }
.sb-step.done span { color:var(--ok); }
/* hide nav buttons (they sit right after the steps HTML) */
section[data-testid="stSidebar"] .nav-btn-wrap { height:0; min-height:0; overflow:hidden; margin:0; padding:0; }

/* sidebar pills */
.sb-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: .7rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
}
.sb-pill.ok  { background: rgba(5,150,105,.15); color: #34d399; }
.sb-pill.wrn { background: rgba(217,119,6,.15); color: #fbbf24; }
.sb-pill.err { background: rgba(220,38,38,.15); color: #f87171; }

/* sidebar missing */
.sb-missing {
    background: rgba(255,255,255,.04);
    border-left: 3px solid var(--warn);
    border-radius: 0 var(--rs) var(--rs) 0;
    padding: 7px 10px;
    margin-bottom: 5px;
}
.sb-missing-field {
    font-family: var(--m);
    font-size: 0.65rem;
    color: #fbbf24 !important;
    font-weight: 600;
}
.sb-missing-desc {
    font-size: 0.75rem;
    color: var(--sb-d) !important;
    line-height: 1.4;
}

/* ── Welcome ── */
.welcome-wrap {
    max-width: 620px;
    margin: 70px auto;
    text-align: center;
}
.welcome-badge {
    display: inline-block;
    font-family: var(--m);
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--ac);
    background: var(--ac-g);
    padding: 3px 12px;
    border-radius: 4px;
    margin-bottom: 20px;
}
.welcome-h1 {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -.03em;
    background: linear-gradient(135deg, var(--ink), var(--ac));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 12px;
}
.welcome-p {
    font-size: 0.92rem;
    color: var(--dim);
    line-height: 1.7;
    max-width: 460px;
    margin: 0 auto 28px;
}
.welcome-guide {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--r);
    padding: 22px 26px;
    text-align: left;
    box-shadow: var(--shadow);
}
.welcome-guide-title {
    font-family: var(--m);
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--faint);
    margin-bottom: 4px;
}
.welcome-guide-text {
    font-size: 0.88rem;
    color: var(--dim);
    line-height: 1.6;
    margin-bottom: 10px;
}

/* ── Page header ── */
.page-header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 4px;
}
.page-h1 {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--ink);
}
.page-badge {
    font-family: var(--m);
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--ac);
    background: var(--ac-g);
    padding: 2px 10px;
    border-radius: 4px;
}
.page-sub {
    font-size: 0.85rem;
    color: var(--faint);
    margin-bottom: 20px;
}

/* ── Block card ── */
.block-card {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--r);
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
    border-top: 3px solid var(--ac);
}
.block-chip {
    display: inline-block;
    font-family: var(--m);
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--ac);
    background: var(--ac-g);
    padding: 2px 10px;
    border-radius: 4px;
    margin-bottom: 8px;
}
.block-question {
    font-size: 0.9rem;
    color: var(--dim);
    line-height: 1.7;
    border-left: 3px solid rgb(10, 113, 78);
    padding: 10px 16px;
    background: #d1e6fa;
    border-radius: 0 var(--rs) var(--rs) 0;
}

/* ── Warning card ── */
.warn-card {
    background: var(--warn-bg);
    border: 1px solid #fde68a;
    border-radius: var(--r);
    padding: 18px 22px;
    margin-bottom: 18px;
}
.warn-card-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--warn);
    text-transform: uppercase;
    letter-spacing: .04em;
    margin-bottom: 10px;
}
.warn-field {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--rs);
    padding: 10px 14px;
    margin-bottom: 6px;
}
.warn-field-name {
    font-family: var(--m);
    font-size: 0.68rem;
    color: var(--warn);
    font-weight: 600;
}
.warn-field-label  { font-size: 0.82rem; color: var(--ink); font-weight: 500; }
.warn-field-desc   { font-size: 0.8rem; color: var(--dim); line-height: 1.5; }
.warn-field-ex     { font-size: 0.72rem; color: var(--faint); font-style: italic; margin-top: 3px; }
.warn-field-hint   { font-size: 0.78rem; color: var(--ac); margin-top: 3px; font-weight: 500; }

/* ── Tabs ── */
div[data-testid="stTabs"] {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--r);
    padding: 10px;
    box-shadow: var(--shadow);
}
button[role="tab"] {
    background: var(--raised) !important;
    color: var(--dim) !important;
    font-weight: 600;
    font-size: 0.9rem;
    border-radius: 10px;
    padding: 12px 48px !important;
    min-width: 180px;
}
button[role="tab"][aria-selected="true"] {
    background: #105db9 !important;
    color: var(--ac-fg) !important;
    font-weight: 600;
    border-radius: 15px;
    padding: 12px 48px !important;
    min-width: 210px;
}
button[role="tab"]:hover:not([aria-selected="true"]) {
    background: var(--ac-s) !important;
    color: var(--ac) !important;
}

/* ── Buttons ── */
div.stButton {
    margin: 6px 0;
}
div.stButton > button {
    font-family: var(--f);
    font-weight: 600;
    font-size: 0.88rem;
    border-radius: var(--rs);
    border: 1px solid var(--bdr);
    background: var(--card);
    color: var(--ink);
    padding: 12px 28px;
    min-height: 44px;
    transition: all .15s;
}
div.stButton > button:hover {
    background: var(--raised);
    border-color: var(--bdr2);
}
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--ac) !important;
    color: var(--ac-fg) !important;
    border: none !important;
    box-shadow: 0 2px 10px var(--ac-g);
}
div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: #059669 !important;
    box-shadow: 0 4px 16px rgba(16,185,129,.3);
}

/* ── Inputs ── */
textarea, input[type="text"] {
    background: var(--card) !important;
    color: var(--ink) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: var(--rs) !important;
    font-family: var(--f) !important;
    transition: border .15s;
}
textarea:focus, input[type="text"]:focus {
    border-color: var(--ac) !important;
    box-shadow: 0 0 0 3px var(--ac-g) !important;
}

/* ── Alerts ── */
.alert-ok   { background:var(--ok-bg);  border:1px solid #a7f3d0; color:var(--ok);  border-radius:var(--rs); padding:10px 16px; font-size:.85rem; }
.alert-warn { background:var(--warn-bg); border:1px solid #fde68a; color:var(--warn); border-radius:var(--rs); padding:10px 16px; font-size:.85rem; }
.alert-err  { background:var(--err-bg);  border:1px solid #fecaca; color:var(--err);  border-radius:var(--rs); padding:10px 16px; font-size:.85rem; }

/* ── Inline code in validation panels ── */
.alert-ok code, .alert-warn code, .alert-err code,
.val-panel code,
[data-testid="stMarkdownContainer"] code {
    padding: 0.2em 0.4em;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    margin: 0;
    border-radius: 0.25rem;
    background: rgb(255, 215, 116) !important;
    color: rgb(21, 39, 130) !important;
    font-family: 'Source Code Pro', 'Fira Code', monospace;
    font-size: 0.9em;
    font-weight: 400;
}

/* ── JSON viewer ── */
.json-viewer {
    background: #1e1b4b;
    border: 1px solid #312e81;
    border-radius: var(--r);
    padding: 18px;
    font-family: var(--m);
    font-size: 0.76rem;
    color: #a5b4fc;
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.7;
}

/* ── Section panel ── */
.section-panel {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-top: 3px solid var(--ac);
    border-radius: var(--r);
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: var(--shadow);
}

/* ── Accent panel ── */
.accent-panel {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--r);
    padding: 20px 24px;
    margin-bottom: 20px;
}

/* ── Hero header ── */
.hero-header {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-top: 3px solid var(--ac);
    border-radius: var(--r);
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: var(--shadow);
}
.hero-header .hero-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--ink);
    margin: 0 0 4px;
}
.hero-header .hero-sub {
    font-size: 0.85rem;
    color: var(--faint);
    margin: 0;
}
.hero-header .hero-badge {
    display: inline-block;
    font-family: var(--m);
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--ac);
    background: var(--ac-g);
    padding: 2px 10px;
    border-radius: 4px;
    margin-bottom: 8px;
}

/* ── Section label ── */
.section-label {
    font-family: var(--m);
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--faint);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--bdr);
}

/* ── Stat row ── */
.stat-row {
    display: flex;
    gap: 14px;
    margin-bottom: 20px;
}
.stat-card {
    flex: 1;
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--r);
    padding: 20px 14px;
    text-align: center;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--ac);
}
.stat-card.stat-warn::before {
    background: var(--err);
}
.stat-card .stat-num {
    font-family: var(--m);
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--ac);
    line-height: 1;
}
.stat-card.stat-warn .stat-num {
    color: var(--err);
}
.stat-card .stat-label {
    font-size: 0.68rem;
    color: var(--faint);
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: .04em;
}

/* ── Tab intro ── */
.tab-intro {
    background: var(--ac-s);
    border: 1px solid var(--bdr);
    border-left: 3px solid var(--ac);
    border-radius: var(--rs);
    padding: 12px 16px;
    margin-bottom: 14px;
    color: var(--dim);
    font-size: 0.88rem;
    line-height: 1.6;
}

/* ── Validation panel ── */
.val-panel {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-top: 3px solid var(--ac);
    border-radius: var(--r);
    padding: 14px 18px;
    box-shadow: var(--shadow);
}
.val-panel-title {
    font-family: var(--m);
    font-size: 1rem;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--faint);
    margin-bottom: 8px;
}

/* field rows in metadata preview */
.field-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid var(--bdr);
}
.field-row:last-child { border-bottom: none; }
.field-key {
    font-family: var(--m);
    font-size: .72rem;
    font-weight: 600;
    color: var(--ac);
    white-space: nowrap;
    min-width: 160px;
    flex-shrink: 0;
}
.field-val {
    font-size: .85rem;
    color: var(--ink);
    word-break: break-word;
    line-height: 1.5;
}
.field-val.empty {
    color: var(--faint);
    font-style: italic;
    font-size: .8rem;
}

/* ── Footer ── */
.footer-text {
    text-align: center;
    font-size: 0.75rem;
    color: var(--faint);
    padding: 6px 0;
}

/* ── Progress bar ── */
/* fill */
[data-testid="stProgress"] > div > div,
.stProgress > div > div {
    background: var(--ac) !important;
    border-radius: 4px !important;
    transition: width .3s ease;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: var(--bdr); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--bdr2); }

/* ── Sidebar native toggle — make it prominent ── */
section[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    align-items: center;
    justify-content: center;
}
section[data-testid="stSidebarCollapsedControl"] button {
    background: var(--ac) !important;
    border-radius: 8px !important;
    width: 36px !important;
    height: 36px !important;
    border: none !important;
    box-shadow: 0 2px 10px rgba(109,92,255,.35) !important;
}
section[data-testid="stSidebarCollapsedControl"] button svg {
    fill: #fff !important;
    stroke: #fff !important;
}
section[data-testid="stSidebarCollapsedControl"] button:hover {
    background: #5a4be6 !important;
    transform: scale(1.08);
}
/* Collapse arrow inside open sidebar */
section[data-testid="stSidebar"] [data-testid="baseButton-header"] {
    background: rgba(255,255,255,.1) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] [data-testid="baseButton-header"] svg {
    fill: var(--sb-t) !important;
    stroke: var(--sb-t) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _alert(cls: str, text: str):
    st.markdown(f"<div class='{cls}'>{text}</div>", unsafe_allow_html=True)

def alert_ok(t):   _alert("alert-ok", t)
def alert_warn(t): _alert("alert-warn", t)
def alert_err(t):  _alert("alert-err", t)

# ── Block display names ──
_BLOCK_DISPLAY = {
    "identificacion_basica": "Identificación básica",
    "derechos de acceso": "Derechos de acceso",
    "organismo_acceso_datos_sanitarios": "Organismo de acceso a datos sanitarios",
}
def block_display_name(raw_name: str) -> str:
    return _BLOCK_DISPLAY.get(raw_name, raw_name.replace("_", " ").title())


# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────
@st.cache_resource
def load_schema():
    return HealthDCATAPSchema("health_dcat_ap.yaml")

schema = load_schema()

for key, default in [
    ("metadata_state", None),
    ("current_block_idx", 0),
    ("block_done", set()),
    ("started", False),
    ("show_missing_warning", False),
    ("pending_next_block", False),
]:
    if key not in st.session_state:
        st.session_state[key] = MetadataState("health_dcat_ap.yaml") if default is None else default

state: MetadataState = st.session_state.metadata_state
block_idx: int = st.session_state.current_block_idx
total_blocks = len(BLOCKS)


# ─────────────────────────────────────────────
# WELCOME
# ─────────────────────────────────────────────
if not st.session_state.started:
    import base64
    _docx_href = None
    try:
        with open("guia_campos_ends.docx", "rb") as _f:
            _docx_href = "data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64," + base64.b64encode(_f.read()).decode()
    except FileNotFoundError:
        pass

    _download_html = (
        f'<a href="{_docx_href}" download="guia_campos_ends.docx" '
        'style="display:inline-block;margin-top:10px;font-size:.82rem;font-weight:600;'
        'color:#10b981;background:#f0faf4;border:1px solid #10b981;border-radius:6px;'
        'padding:7px 16px;text-decoration:none;">&#8595; Descargar guía de campos</a>'
        if _docx_href else
        '<div style="font-size:.78rem;color:#8faa9c;margin-top:8px;font-style:italic;">'
        'Coloca guia_campos_ends.docx en la raíz del proyecto.</div>'
    )

    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown(
            '<div style="margin-top:48px;text-align:center;">'
            '<span style="display:inline-block;font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#10b981;background:rgba(16,185,129,.1);padding:3px 14px;border-radius:4px;margin-bottom:16px;">Health DCAT-AP-ES</span>'
            '<h1 style="font-size:1.9rem;font-weight:800;letter-spacing:-.02em;color:#0d1f15;margin:0 0 20px;">Asistente de Metadatos del ENDS</h1>'
            '</div>'
            '<div style="background:#f0faf4;border:1px solid #c9d6ce;border-top:4px solid #10b981;border-radius:16px;padding:28px 32px 24px;box-shadow:0 4px 20px rgba(16,185,129,.07);">'
            '<p style="font-size:.93rem;color:#3d5448;line-height:1.75;margin:0 0 20px;">Guía paso a paso para metadatar tu conjunto de datos conforme al esquema sanitario europeo. Responde con tus propias palabras y la IA estructurará la información automáticamente.</p>'
            '<div style="background:#fff;border:1px solid #c9d6ce;border-radius:10px;padding:14px 18px;">'
            '<div style="font-size:.6rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#8faa9c;margin-bottom:5px;">Guía de campos</div>'
            '<div style="font-size:.85rem;color:#3d5448;line-height:1.6;">Descarga la guía completa con la descripción de todos los campos necesarios para catalogar tu dataset.</div>'
            f'{_download_html}'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("Comenzar", type="primary", use_container_width=True):
            st.session_state.started = True
            st.rerun()

    st.stop()


# ─────────────────────────────────────────────
# CURRENT BLOCK DATA
# ─────────────────────────────────────────────
block = BLOCKS[block_idx]
block_missing = get_block_missing(block, state.data)
block_missing_info = get_missing_descriptions(block_missing, use_llm=False, call_llm_fn=None)
all_missing = state.missing_required()
all_missing_info = get_missing_descriptions(all_missing, use_llm=False)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-brand"><span class="dot"></span>Asistente de Metadatos</div>', unsafe_allow_html=True)
    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    # Progress
    pct = int(len(st.session_state.block_done) / total_blocks * 100)
    _circ = 213.63
    _offset = round(_circ * (1 - pct / 100), 2)
    st.markdown('<div class="sb-label">Progreso</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ring-w">'
        f'<div class="ring">'
        f'<svg width="84" height="84">'
        f'<circle class="bg" cx="42" cy="42" r="34" stroke-dasharray="{_circ}" stroke-dashoffset="0"/>'
        f'<circle class="fg" cx="42" cy="42" r="34" stroke-dasharray="{_circ}" stroke-dashoffset="{_offset}"/>'
        f'</svg>'
        f'<div class="lbl">{pct}%</div>'
        f'</div>'
        f'<div style="font-size:.72rem;color:var(--sb-d);letter-spacing:.02em">{len(st.session_state.block_done)} de {total_blocks} bloques</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    # Stats
    filled = sum(1 for v in state.data.values() if v not in (None, "", [], {}))
    st.markdown('<div class="sb-label">Resumen</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="sb-stat"><div class="sb-stat-num">{filled}</div>'
            f'<div class="sb-stat-label">completados</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="sb-stat"><div class="sb-stat-num danger">{len(all_missing)}</div>'
            f'<div class="sb-stat-label">pendientes</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    # Steps
    st.markdown('<div class="sb-label">Bloques</div>', unsafe_allow_html=True)
    for i, b in enumerate(BLOCKS):
        done = i in st.session_state.block_done
        is_current = i == block_idx
        label = block_display_name(b['name'])
        prefix = "\u2713 " if done else ""
        if st.button(
            f"{prefix}{label}",
            key=f"nav_{i}",
            use_container_width=True,
        ):
            st.session_state.current_block_idx = i
            st.session_state.show_missing_warning = False
            st.rerun()

    # Missing fields
    if all_missing_info:
        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)
        st.markdown('<div class="sb-label">Campos pendientes</div>', unsafe_allow_html=True)
        for item in all_missing_info:
            ej = f"<div class='sb-missing-desc' style='font-style:italic;margin-top:2px'>Ej: {item['ejemplo']}</div>" if item["ejemplo"] else ""
            st.markdown(
                f'<div class="sb-missing">'
                f'<div class="sb-missing-field">{item["field"]}</div>'
                f'<div class="sb-missing-desc"><strong>{item["label"]}</strong> &middot; {item["descripcion"]}</div>'
                f'{ej}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    # Downloads
    try:
        with open("guia_campos_ends.docx", "rb") as f:
            st.download_button(
                "Guia de campos",
                data=f.read(),
                file_name="guia_campos_ends.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
    except FileNotFoundError:
        pass

    st.download_button(
        "Descargar JSON",
        data=json.dumps(state.data, indent=2, ensure_ascii=False),
        file_name="metadata_output.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Volver al inicio", use_container_width=True):
        st.session_state.started = False
        st.rerun()


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
st.markdown(
    f'<div class="hero-header">'
    f'<div class="hero-badge">Bloque {block_idx + 1} de {total_blocks}</div>'
    f'<div class="hero-title">Asistente de Metadatos</div>'
    f'<div class="hero-sub">Esquema sanitario europeo &middot; {block_display_name(block["name"])}</div>'
    f'</div>',
    unsafe_allow_html=True,
)
st.progress((block_idx + 1) / total_blocks)


# ─────────────────────────────────────────────
# MISSING WARNING
# ─────────────────────────────────────────────
if st.session_state.show_missing_warning and block_missing_info:
    st.markdown(
        f'<div class="warn-card">'
        f'<div class="warn-card-title">{len(block_missing_info)} campo(s) sin rellenar en este bloque</div>',
        unsafe_allow_html=True,
    )
    for item in block_missing_info:
        hint = f'<div class="warn-field-hint">{item["sugerencia"]}</div>' if item.get("sugerencia") else ""
        ex = f'<div class="warn-field-ex">Ejemplo: {item["ejemplo"]}</div>' if item.get("ejemplo") else ""
        req = " (obligatorio)" if item["obligatorio"] else ""
        st.markdown(
            f'<div class="warn-field">'
            f'<div class="warn-field-name">{item["field"]}</div>'
            f'<div class="warn-field-label">{item["label"]}{req}</div>'
            f'<div class="warn-field-desc">{item["descripcion"]}</div>'
            f'{ex}{hint}</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Volver a rellenar", use_container_width=True):
            st.session_state.show_missing_warning = False
            st.session_state.pending_next_block = False
            st.rerun()
    with c2:
        if st.button("Continuar igualmente", use_container_width=True, type="primary"):
            st.session_state.show_missing_warning = False
            st.session_state.pending_next_block = False
            st.session_state.block_done.add(block_idx)
            st.session_state.current_block_idx += 1
            st.rerun()


# ─────────────────────────────────────────────
# BLOCK CARD
# ─────────────────────────────────────────────
st.markdown(
    f'<div class="section-panel">'
    f'<div class="block-chip">Bloque {block_idx + 1} &middot; {block_display_name(block["name"])}</div>'
    f'<div class="block-question">{block["question"]}</div>'
    f'</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# TABS: AI / MANUAL
# ─────────────────────────────────────────────
tab_ia, tab_manual = st.tabs(["Autocompletar con IA", "Rellenar manualmente"])
partial = {}

with tab_ia:
    if not llm_available():
        st.warning("No hay LLM disponible. Configura tu API key en llm_provider.py.")
    else:
        st.markdown(
            '<div class="tab-intro">'
            'Describe este bloque con tus propias palabras y la IA extraera '
            'los campos automaticamente a partir de tu texto.</div>',
            unsafe_allow_html=True,
        )
        user_context = st.text_area(
            "Tu descripcion",
            placeholder="El dataset contiene datos sobre...",
            height=120,
            key="ia_context",
        )
        if st.button("Autocompletar bloque", type="primary", key="btn_ia"):
            if not user_context.strip():
                st.warning("Escribe algo antes de autocompletar.")
            else:
                with st.spinner("Procesando..."):
                    try:
                        prompt = build_prompt_for_block(schema, block, user_context)
                        contract = build_contract(block)
                        ai_result = call_llm(prompt, contract, user_context)
                        partial = {n: ai_result.get(n) for n in block["fields"]}
                        state.merge_partial(partial)
                        st.session_state.block_done.add(block_idx)
                        st.session_state.show_missing_warning = False
                        alert_ok("Bloque autocompletado correctamente.")
                        st.json(partial)
                    except Exception as e:
                        alert_err(f"Error: {e}")

with tab_manual:
    st.markdown(
        '<div class="tab-intro">'
        'Completa cada campo individualmente. Los campos marcados '
        'con * son obligatorios.</div>',
        unsafe_allow_html=True,
    )
    for field_name in block["fields"]:
        if field_name == "applicable_legislation":
            st.info("applicable_legislation se rellena automaticamente al finalizar.")
            continue
        field = schema.get_field(field_name)
        raw_label = field.get("label", field_name) if field else field_name
        label = raw_label.get("es", str(raw_label)) if isinstance(raw_label, dict) else str(raw_label)
        raw_help = field.get("help_text", "") if field else ""
        help_text = raw_help.get("es", str(raw_help)) if isinstance(raw_help, dict) else str(raw_help)
        required = field.get("required", False) if field else False
        display_label = f"{'* ' if required else ''}{label}"
        current_val = state.data.get(field_name)
        default_val = ""
        if current_val and isinstance(current_val, str):
            default_val = current_val
        elif current_val and not isinstance(current_val, str):
            default_val = json.dumps(current_val, ensure_ascii=False)
        raw_value = st.text_input(
            display_label,
            value=default_val,
            help=(f"{help_text}\n\nCampo obligatorio" if required else help_text),
            key=f"manual_{block['name']}_{field_name}",
        )
        partial[field_name] = raw_value if raw_value else None

    if st.button("Guardar bloque", type="primary", key="btn_manual"):
        to_merge = {k: v for k, v in partial.items() if v is not None}
        state.merge_partial(to_merge)
        st.session_state.block_done.add(block_idx)
        st.session_state.show_missing_warning = False
        alert_ok("Bloque guardado correctamente.")


# ─────────────────────────────────────────────
# STATUS + VALIDATION
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Estado y validacion</div>', unsafe_allow_html=True)
col_json, col_val = st.columns([3, 2])

with col_json:
    rows = []
    for field_name in block["fields"]:
        val = state.data.get(field_name)
        field_meta = schema.get_field(field_name)
        raw_lbl = field_meta.get("label", field_name) if field_meta else field_name
        lbl = raw_lbl.get("es", str(raw_lbl)) if isinstance(raw_lbl, dict) else str(raw_lbl)
        if val is None or val == "" or val == [] or val == {}:
            rows.append(
                f'<div class="field-row">'
                f'<div class="field-key">{lbl}</div>'
                f'<div class="field-val empty">sin rellenar</div>'
                f'</div>'
            )
        else:
            display_val = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val)
            rows.append(
                f'<div class="field-row">'
                f'<div class="field-key">{lbl}</div>'
                f'<div class="field-val">{display_val}</div>'
                f'</div>'
            )
    st.markdown(
        '<div class="val-panel">'
        '<div class="val-panel-title">Estado del bloque</div>'
        + "".join(rows) +
        '</div>',
        unsafe_allow_html=True,
    )

with col_val:
    errors = state.validate_types_basic()
    missing = state.missing_required()
    if not errors and not missing:
        val_content = '<div class="alert-ok">Todo correcto. Sin errores ni campos pendientes.</div>'
    else:
        val_content = ""
        if errors:
            items = "".join(f"<li><code>{e}</code></li>" for e in errors)
            val_content += f'<div class="alert-err">Errores de formato:<ul style="margin:.4rem 0 0 1rem;padding:0">{items}</ul></div>'
        if missing:
            items = "".join(f"<li><code>{m}</code></li>" for m in missing)
            val_content += f'<div class="alert-warn" style="margin-top:8px">Campos obligatorios pendientes:<ul style="margin:.4rem 0 0 1rem;padding:0">{items}</ul></div>'
    st.markdown(
        '<div class="val-panel">'
        '<div class="val-panel-title">Validacion en tiempo real</div>'
        f'{val_content}'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Navegacion</div>', unsafe_allow_html=True)
st.markdown('<div class="nav-bar">', unsafe_allow_html=True)
col_prev, col_info, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("Anterior", disabled=(block_idx == 0), use_container_width=True):
        st.session_state.current_block_idx -= 1
        st.session_state.show_missing_warning = False
        st.rerun()

with col_info:
    st.markdown(
        f'<div class="footer-text">'
        f'Bloque {block_idx + 1} de {total_blocks} &middot; {block_display_name(block["name"])}</div>',
        unsafe_allow_html=True,
    )

with col_next:
    if block_idx < total_blocks - 1:
        if st.button("Siguiente", use_container_width=True, type="primary"):
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
        if st.button("Finalizar y guardar", use_container_width=True, type="primary"):
            state.data["applicable_legislation"] = [
                {"uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR"}
            ]
            with open("metadata_output.json", "w", encoding="utf-8") as f:
                json.dump(state.data, f, indent=2, ensure_ascii=False)
            st.balloons()
            st.success("Metadatos completos guardados en metadata_output.json")

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if st.button("Inicio", use_container_width=True):
        st.session_state.started = False
        st.rerun()
with c2:
    st.markdown('<div class="footer-text">ENDS Metadata Assistant &middot; HealthDCAT-AP-ES</div>', unsafe_allow_html=True)
with c3:
    if st.button("Reiniciar", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
