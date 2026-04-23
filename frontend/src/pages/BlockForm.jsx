// src/pages/BlockForm.jsx
import { useState, useEffect } from "react";
import {
  completeBlock, saveManual, validateMetadata,
  getMissingFields, finalizeMetadata, getMetadata
} from "../api/client";

// ── Helpers ──────────────────────────────────────────────────
const FIELD_LABELS = {
  title: "Título",
  identifier: "Identificador",
  notes: "Descripción",
  name: "URL slug",
  access_rights: "Derechos de acceso",
  hdab: "Organismo de acceso (HDAB)",
  applicable_legislation: "Legislación aplicable",
  language: "Idioma",
  contact: "Contacto",
};

const FIELD_ICONS = {
  title: "◈",
  identifier: "⌗",
  notes: "≡",
  name: "∞",
  access_rights: "⊛",
  hdab: "⊕",
  applicable_legislation: "§",
  language: "◎",
  contact: "◉",
};

function renderValue(value) {
  if (value === null || value === undefined || value === "") return null;
  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    return value.map((v, i) => (
      <span key={i} style={chip}>
        {typeof v === "object" ? (v.label || v.uri || JSON.stringify(v)) : v}
      </span>
    ));
  }
  if (typeof value === "object") {
    return <span style={chip}>{value.label || value.uri || JSON.stringify(value)}</span>;
  }
  return <span style={valueText}>{String(value)}</span>;
}

const chip = {
  display: "inline-block", background: "#f0f4fb", border: "1px solid #d0daea",
  borderRadius: "20px", padding: "2px 10px", fontSize: "0.78rem", color: "#2c4a7a",
  marginRight: "4px", marginBottom: "4px", fontFamily: "'DM Mono', monospace",
};
const valueText = {
  fontSize: "0.88rem", color: "#1a2a3a", fontFamily: "'DM Sans', sans-serif", lineHeight: 1.5,
};

function MetadataPanel({ metadata }) {
  const entries = Object.entries(metadata).filter(([, v]) => {
    if (v === null || v === undefined || v === "") return false;
    if (Array.isArray(v) && v.length === 0) return false;
    return true;
  });

  if (entries.length === 0) {
    return (
      <div style={emptyState}>
        <span style={{ fontSize: "2rem", opacity: 0.25 }}>◈</span>
        <p style={{ margin: "8px 0 0 0", color: "#9aaabb", fontSize: "0.85rem" }}>
          Aún no hay datos. Completa el primer bloque.
        </p>
      </div>
    );
  }

  return (
    <div style={fieldList}>
      {entries.map(([key, value]) => (
        <div key={key} style={fieldEntry}>
          <div style={fieldHeader}>
            <span style={fieldIcon}>{FIELD_ICONS[key] || "·"}</span>
            <span style={fieldLabel}>{FIELD_LABELS[key] || key}</span>
          </div>
          <div style={fieldValue}>{renderValue(value)}</div>
        </div>
      ))}
    </div>
  );
}

const emptyState = {
  display: "flex", flexDirection: "column", alignItems: "center",
  justifyContent: "center", padding: "32px 0", textAlign: "center",
};
const fieldList = { display: "flex", flexDirection: "column", gap: "0" };
const fieldEntry = {
  padding: "12px 0", borderBottom: "1px solid #edf0f5",
};
const fieldHeader = { display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" };
const fieldIcon = {
  fontFamily: "'DM Mono', monospace", fontSize: "0.9rem", color: "#2e86de",
  width: "18px", flexShrink: 0,
};
const fieldLabel = {
  fontSize: "0.72rem", fontWeight: 600, color: "#8899bb", textTransform: "uppercase",
  letterSpacing: "0.07em", fontFamily: "'DM Mono', monospace",
};
const fieldValue = { paddingLeft: "26px" };

// ── Main component ───────────────────────────────────────────
export default function BlockForm({ blocks, currentIdx, onNext, onPrev, onFinish, onBlockDone }) {
  const [tab, setTab] = useState("ia");
  const [userContext, setUserContext] = useState("");
  const [manualFields, setManualFields] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState({ valid: true, errors: [], missing_required: [] });
  const [metadata, setMetadata] = useState({});
  const [showWarning, setShowWarning] = useState(false);
  const [missingInfo, setMissingInfo] = useState([]);

  const block = blocks[currentIdx];

  useEffect(() => {
    setUserContext("");
    setManualFields({});
    setResult(null);
    setError(null);
    setShowWarning(false);
    loadMetadata();
  }, [currentIdx]);

  const loadMetadata = async () => {
    try {
      const res = await getMetadata();
      setMetadata(res.data);
      const val = await validateMetadata();
      setValidation(val.data);
    } catch {}
  };

  const handleComplete = async () => {
    if (!userContext.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await completeBlock(currentIdx, userContext);
      setResult(res.data.partial);
      setMetadata(res.data.metadata);
      onBlockDone(currentIdx);
      const val = await validateMetadata();
      setValidation(val.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Error al completar el bloque");
    }
    setLoading(false);
  };

  const handleManualSave = async () => {
    setLoading(true);
    try {
      const res = await saveManual(currentIdx, manualFields);
      setMetadata(res.data.metadata);
      onBlockDone(currentIdx);
      const val = await validateMetadata();
      setValidation(val.data);
      setResult(manualFields);
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar");
    }
    setLoading(false);
  };

  const handleNext = async () => {
    const res = await getMissingFields(currentIdx);
    const missing = res.data.descriptions;
    if (missing.length > 0 && !showWarning) {
      setMissingInfo(missing);
      setShowWarning(true);
      return;
    }
    setShowWarning(false);
    onNext();
  };

  const handleFinalize = async () => {
    setLoading(true);
    try {
      await finalizeMetadata();
      onFinish();
    } catch (e) {
      setError("Error al finalizar");
    }
    setLoading(false);
  };

  return (
    <div style={s.wrapper}>

      {/* Cabecera del bloque */}
      <div style={s.blockCard}>
        <p style={s.blockName}>Bloque {currentIdx + 1} · {block.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</p>
        <p style={s.blockQuestion}>{block.question}</p>
      </div>

      {/* Aviso campos faltantes */}
      {showWarning && (
        <div style={s.warningCard}>
          <p style={s.warningTitle}>Hay {missingInfo.length} campo(s) sin rellenar</p>
          {missingInfo.map((item, i) => (
            <div key={i} style={s.warnField}>
              <p style={s.warnFieldName}>{FIELD_LABELS[item.field] || item.field}{item.obligatorio ? " *" : ""}</p>
              <p style={s.warnFieldDesc}>{item.descripcion}</p>
              {item.ejemplo && <p style={s.warnFieldExample}>Ej: {item.ejemplo}</p>}
            </div>
          ))}
          <div style={s.warnButtons}>
            <button style={s.btnSecondary} onClick={() => setShowWarning(false)}>Volver a rellenar</button>
            <button style={s.btnPrimary} onClick={() => { setShowWarning(false); onNext(); }}>Continuar de todas formas</button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={s.tabs}>
        <button style={{ ...s.tab, ...(tab === "ia" ? s.tabActive : {}) }} onClick={() => setTab("ia")}>
          Completar automáticamente
        </button>
        <button style={{ ...s.tab, ...(tab === "manual" ? s.tabActive : {}) }} onClick={() => setTab("manual")}>
          Rellenar manualmente
        </button>
      </div>

      {tab === "ia" && (
        <div style={s.tabContent}>
          <p style={s.tabDesc}>Describe el dataset con tus propias palabras y el asistente extraerá los campos.</p>
          <textarea
            style={s.textarea}
            placeholder="Ej.: El dataset trata sobre casos de viruela del mono en España durante 2023, incluyendo distribución geográfica y datos demográficos..."
            value={userContext}
            onChange={(e) => setUserContext(e.target.value)}
            rows={5}
          />
          <button
            style={{ ...s.btnPrimary, marginTop: "14px", opacity: loading ? 0.6 : 1 }}
            onClick={handleComplete}
            disabled={loading || !userContext.trim()}
          >
            {loading ? "Procesando..." : "Completar bloque"}
          </button>
          {result && <div style={s.alertOk}>Bloque completado correctamente.</div>}
          {error && <div style={s.alertError}>{error}</div>}
        </div>
      )}

      {tab === "manual" && (
        <div style={s.tabContent}>
          <p style={s.tabDesc}>Introduce los valores de cada campo del bloque.</p>
          {block.fields.filter(f => f !== "applicable_legislation").map(field => (
            <div key={field} style={s.fieldRow}>
              <label style={s.label}>{FIELD_LABELS[field] || field}</label>
              <input
                style={s.input}
                type="text"
                placeholder={`Introduce ${FIELD_LABELS[field] || field}...`}
                value={manualFields[field] || ""}
                onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}
              />
            </div>
          ))}
          {block.fields.includes("applicable_legislation") && (
            <div style={s.autoInfo}>La legislación aplicable (GDPR) se añade automáticamente al finalizar.</div>
          )}
          <button
            style={{ ...s.btnPrimary, marginTop: "16px", opacity: loading ? 0.6 : 1 }}
            onClick={handleManualSave}
            disabled={loading}
          >
            {loading ? "Guardando..." : "Guardar bloque"}
          </button>
          {result && <div style={s.alertOk}>Bloque guardado correctamente.</div>}
          {error && <div style={s.alertError}>{error}</div>}
        </div>
      )}

      {/* Panel inferior: metadata legible + validación */}
      <div style={s.bottomGrid}>

        <div style={s.metaBox}>
          <div style={s.metaHeader}>
            <p style={s.sectionTitle}>Resumen del dataset</p>
            <span style={s.metaBadge}>
              {Object.values(metadata).filter(v => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0)).length} campos
            </span>
          </div>
          <MetadataPanel metadata={metadata} />
        </div>

        <div style={s.validationBox}>
          <p style={s.sectionTitle}>Estado de validación</p>
          {validation.valid ? (
            <div style={s.validOk}>
              <span style={s.validIcon}>✓</span>
              <span>Sin errores ni campos pendientes</span>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {validation.errors.map((e, i) => (
                <div key={i} style={s.validError}>
                  <span style={{ fontWeight: 600, marginRight: "6px" }}>!</span>{e}
                </div>
              ))}
              {validation.missing_required.map((m, i) => (
                <div key={i} style={s.validWarn}>
                  <span style={{ fontWeight: 600, marginRight: "6px" }}>·</span>
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: "0.82rem" }}>
                    {FIELD_LABELS[m] || m}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "#b07000", marginLeft: "6px" }}>obligatorio</span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Navegación */}
      <div style={s.nav}>
        <button
          style={{ ...s.btnSecondary, visibility: currentIdx === 0 ? "hidden" : "visible" }}
          onClick={onPrev}
        >
          ← Anterior
        </button>
        <span style={s.navInfo}>
          {currentIdx + 1} / {blocks.length}
        </span>
        {currentIdx < blocks.length - 1 ? (
          <button style={s.btnPrimary} onClick={handleNext}>Siguiente →</button>
        ) : (
          <button
            style={{ ...s.btnPrimary, background: "#0f5c35", opacity: loading ? 0.6 : 1 }}
            onClick={handleFinalize}
            disabled={loading}
          >
            {loading ? "Guardando..." : "Finalizar y guardar"}
          </button>
        )}
      </div>

    </div>
  );
}

// ── Styles ───────────────────────────────────────────────────
const s = {
  wrapper: {
    padding: "0 0 48px 0",
    fontFamily: "'DM Sans', 'IBM Plex Sans', sans-serif",
  },
  blockCard: {
    background: "white", borderRadius: "12px",
    border: "1px solid #e4eaf4", padding: "24px 28px",
    marginBottom: "20px", boxShadow: "0 1px 4px rgba(10,22,40,0.05)",
  },
  blockName: {
    fontFamily: "'DM Mono', 'IBM Plex Mono', monospace",
    fontSize: "0.7rem", color: "#2e86de", textTransform: "uppercase",
    letterSpacing: "0.1em", marginBottom: "8px", margin: "0 0 8px 0",
  },
  blockQuestion: {
    fontSize: "0.93rem", color: "#2c3e50", lineHeight: 1.65,
    background: "#f5f8fd", borderLeft: "3px solid #2e86de",
    padding: "12px 16px", borderRadius: "0 8px 8px 0", margin: "8px 0 0 0",
  },
  warningCard: {
    background: "#fffcf0", border: "1px solid #e8d080",
    borderRadius: "10px", padding: "16px 20px", margin: "12px 0",
  },
  warningTitle: {
    fontFamily: "'DM Mono', monospace", fontSize: "0.78rem",
    color: "#8a6000", fontWeight: 600, marginBottom: "12px", margin: "0 0 12px 0",
  },
  warnField: {
    background: "white", border: "1px solid #f0dfa0",
    borderRadius: "8px", padding: "10px 14px", marginBottom: "8px",
  },
  warnFieldName: {
    fontFamily: "'DM Mono', monospace", fontSize: "0.75rem",
    color: "#8a6000", fontWeight: 600, margin: "0 0 4px 0",
  },
  warnFieldDesc: { fontSize: "0.85rem", color: "#4a3800", margin: "0" },
  warnFieldExample: {
    fontSize: "0.78rem", color: "#999", fontStyle: "italic", margin: "4px 0 0 0",
  },
  warnButtons: { display: "flex", gap: "12px", marginTop: "14px" },
  tabs: {
    display: "flex", gap: "0", borderBottom: "1px solid #e4eaf4",
  },
  tab: {
    padding: "12px 22px", border: "none", background: "transparent",
    cursor: "pointer", fontSize: "0.88rem", color: "#7a8fa8",
    fontFamily: "'DM Sans', sans-serif", letterSpacing: "0.01em",
    borderBottom: "2px solid transparent", marginBottom: "-1px",
    transition: "color 0.15s",
  },
  tabActive: {
    color: "#0a1628", borderBottom: "2px solid #2e86de", fontWeight: 600,
  },
  tabContent: {
    background: "white", border: "1px solid #e4eaf4", borderTop: "none",
    borderRadius: "0 0 12px 12px", padding: "24px",
  },
  tabDesc: { fontSize: "0.88rem", color: "#5a6a80", marginBottom: "16px", margin: "0 0 16px 0" },
  textarea: {
    width: "100%", padding: "12px 14px", border: "1px solid #d8e2f0",
    borderRadius: "8px", fontSize: "0.92rem", fontFamily: "'DM Sans', sans-serif",
    resize: "vertical", boxSizing: "border-box", color: "#1a2a3a",
    lineHeight: 1.6, outline: "none",
  },
  fieldRow: { marginBottom: "14px" },
  label: {
    display: "block", fontSize: "0.78rem", fontFamily: "'DM Mono', monospace",
    color: "#5a6a80", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.06em",
  },
  input: {
    width: "100%", padding: "10px 12px", border: "1px solid #d8e2f0",
    borderRadius: "8px", fontSize: "0.92rem", fontFamily: "'DM Sans', sans-serif",
    boxSizing: "border-box", color: "#1a2a3a",
  },
  autoInfo: {
    background: "#f0f6ff", border: "1px solid #c8daf5", borderRadius: "8px",
    padding: "10px 14px", fontSize: "0.85rem", color: "#2a4a7a", marginTop: "8px",
  },
  bottomGrid: {
    display: "grid", gridTemplateColumns: "3fr 2fr",
    gap: "16px", marginTop: "24px",
  },
  metaBox: {
    background: "white", borderRadius: "12px", padding: "20px",
    border: "1px solid #e4eaf4",
  },
  metaHeader: {
    display: "flex", justifyContent: "space-between",
    alignItems: "center", marginBottom: "16px",
  },
  metaBadge: {
    fontFamily: "'DM Mono', monospace", fontSize: "0.72rem",
    background: "#f0f4fb", border: "1px solid #d0daea",
    borderRadius: "12px", padding: "2px 10px", color: "#4a6a9a",
  },
  validationBox: {
    background: "white", borderRadius: "12px", padding: "20px",
    border: "1px solid #e4eaf4",
  },
  sectionTitle: {
    fontFamily: "'DM Mono', monospace", fontSize: "0.72rem",
    color: "#8899bb", fontWeight: 600, margin: "0",
    textTransform: "uppercase", letterSpacing: "0.08em",
  },
  validOk: {
    display: "flex", alignItems: "center", gap: "10px",
    background: "#f0faf5", border: "1px solid #b8e8cc",
    borderRadius: "8px", padding: "12px 14px",
    fontSize: "0.85rem", color: "#1a6640", marginTop: "12px",
  },
  validIcon: {
    width: "20px", height: "20px", background: "#2ecc71",
    borderRadius: "50%", display: "flex", alignItems: "center",
    justifyContent: "center", color: "white", fontSize: "0.7rem",
    fontWeight: 700, flexShrink: 0,
  },
  validError: {
    background: "#fef5f5", border: "1px solid #f5c0c0",
    borderRadius: "6px", padding: "8px 12px",
    fontSize: "0.83rem", color: "#8a2020", marginTop: "8px",
    display: "flex", alignItems: "flex-start",
  },
  validWarn: {
    background: "#fdfaf0", border: "1px solid #e8d890",
    borderRadius: "6px", padding: "8px 12px",
    fontSize: "0.83rem", color: "#5a4800", marginTop: "6px",
    display: "flex", alignItems: "center",
  },
  nav: {
    display: "flex", justifyContent: "space-between",
    alignItems: "center", marginTop: "24px", paddingTop: "20px",
    borderTop: "1px solid #e4eaf4",
  },
  navInfo: {
    fontFamily: "'DM Mono', monospace", fontSize: "0.78rem", color: "#9aaabb",
  },
  btnPrimary: {
    background: "#0a1628", color: "white", border: "none",
    borderRadius: "8px", padding: "11px 24px", fontSize: "0.88rem",
    fontWeight: 600, cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
    letterSpacing: "0.01em",
  },
  btnSecondary: {
    background: "white", color: "#0a1628", border: "1px solid #d0daea",
    borderRadius: "8px", padding: "11px 24px", fontSize: "0.88rem",
    fontWeight: 500, cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
  },
  alertOk: {
    background: "#f0faf5", border: "1px solid #b8e8cc", color: "#1a6640",
    borderRadius: "8px", padding: "10px 16px", fontSize: "0.85rem", marginTop: "12px",
  },
  alertError: {
    background: "#fef5f5", border: "1px solid #f5c0c0", color: "#8a2020",
    borderRadius: "8px", padding: "10px 16px", fontSize: "0.85rem", marginTop: "10px",
  },
};
