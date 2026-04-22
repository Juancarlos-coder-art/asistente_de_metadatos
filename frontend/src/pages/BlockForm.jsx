// src/pages/BlockForm.jsx
import { useState, useEffect } from "react";
import {
  completeBlock, saveManual, validateMetadata,
  getMissingFields, finalizeMetadata, getMetadata
} from "../api/client";

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
      setError(e.response?.data?.detail || "Error al autocompletar");
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
    <div style={styles.wrapper}>
      {/* Tarjeta del bloque */}
      <div style={styles.blockCard}>
        <p style={styles.blockName}>📦 Bloque {currentIdx + 1} · {block.name.replace(/_/g, " ").toUpperCase()}</p>
        <p style={styles.blockQuestion}>{block.question}</p>
      </div>

      {/* Aviso campos faltantes */}
      {showWarning && (
        <div style={styles.warningCard}>
          <p style={styles.warningTitle}>⚠️ Hay {missingInfo.length} campo(s) sin rellenar. Puedes completarlos o continuar.</p>
          {missingInfo.map((item, i) => (
            <div key={i} style={styles.warnField}>
              <p style={styles.warnFieldName}>{item.field}</p>
              <p style={styles.warnFieldLabel}><strong>{item.label}</strong>{item.obligatorio ? " 🔴" : ""}</p>
              <p style={styles.warnFieldDesc}>{item.descripcion}</p>
              {item.ejemplo && <p style={styles.warnFieldExample}>Ejemplo: {item.ejemplo}</p>}
            </div>
          ))}
          <div style={styles.warnButtons}>
            <button style={styles.btnSecondary} onClick={() => setShowWarning(false)}>✏️ Volver a rellenar</button>
            <button style={styles.btnPrimary} onClick={() => { setShowWarning(false); onNext(); }}>➡️ Continuar de todas formas</button>
          </div>
        </div>
      )}

      {/* Tabs IA / Manual */}
      <div style={styles.tabs}>
        <button style={{ ...styles.tab, ...(tab === "ia" ? styles.tabActive : {}) }} onClick={() => setTab("ia")}>🤖 Autocompletar con IA</button>
        <button style={{ ...styles.tab, ...(tab === "manual" ? styles.tabActive : {}) }} onClick={() => setTab("manual")}>✍️ Rellenar manualmente</button>
      </div>

      {tab === "ia" && (
        <div style={styles.tabContent}>
          <p style={styles.tabDesc}>Describe este bloque con tus propias palabras y la IA extraerá los campos automáticamente.</p>
          <textarea
            style={styles.textarea}
            placeholder="Ej.: El dataset trata sobre casos de viruela del mono en España durante 2023..."
            value={userContext}
            onChange={(e) => setUserContext(e.target.value)}
            rows={5}
          />
          <button style={{ ...styles.btnPrimary, marginTop: "12px", opacity: loading ? 0.7 : 1 }}
            onClick={handleComplete} disabled={loading || !userContext.trim()}>
            {loading ? "Analizando..." : "⚡ Autocompletar bloque"}
          </button>
          {result && <div style={styles.alertOk}>✅ Bloque autocompletado correctamente.</div>}
          {error && <div style={styles.alertError}>❌ {error}</div>}
        </div>
      )}

      {tab === "manual" && (
        <div style={styles.tabContent}>
          <p style={styles.tabDesc}>Rellena los campos del bloque uno a uno.</p>
          {block.fields.filter(f => f !== "applicable_legislation").map(field => (
            <div key={field} style={styles.fieldRow}>
              <label style={styles.label}>{field}</label>
              <input
                style={styles.input}
                type="text"
                placeholder={`Introduce ${field}...`}
                value={manualFields[field] || ""}
                onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}
              />
            </div>
          ))}
          {block.fields.includes("applicable_legislation") && (
            <div style={styles.autoInfo}>📋 <strong>applicable_legislation</strong> se rellena automáticamente al finalizar.</div>
          )}
          <button style={{ ...styles.btnPrimary, marginTop: "16px", opacity: loading ? 0.7 : 1 }}
            onClick={handleManualSave} disabled={loading}>
            {loading ? "Guardando..." : "💾 Guardar bloque"}
          </button>
          {result && <div style={styles.alertOk}>✅ Bloque guardado correctamente.</div>}
          {error && <div style={styles.alertError}>❌ {error}</div>}
        </div>
      )}

      {/* Estado + Validación */}
      <div style={styles.bottomGrid}>
        <div style={styles.jsonBox}>
          <p style={styles.sectionTitle}>📄 Estado actual del metadata</p>
          <pre style={styles.jsonPre}>{JSON.stringify(metadata, null, 2)}</pre>
        </div>
        <div style={styles.validationBox}>
          <p style={styles.sectionTitle}>🔍 Validación en tiempo real</p>
          {validation.valid ? (
            <div style={styles.alertOk}>✅ Todo correcto. Sin errores ni campos pendientes.</div>
          ) : (
            <>
              {validation.errors.map((e, i) => <div key={i} style={styles.alertError}>⚠️ {e}</div>)}
              {validation.missing_required.map((m, i) => <div key={i} style={styles.alertWarn}>📋 {m}</div>)}
            </>
          )}
        </div>
      </div>

      {/* Navegación */}
      <div style={styles.nav}>
        <button style={{ ...styles.btnSecondary, visibility: currentIdx === 0 ? "hidden" : "visible" }}
          onClick={onPrev}>⬅️ Anterior</button>
        <span style={styles.navInfo}>Bloque {currentIdx + 1} / {blocks.length} · {block.name.replace(/_/g, " ")}</span>
        {currentIdx < blocks.length - 1 ? (
          <button style={styles.btnPrimary} onClick={handleNext}>➡️ Siguiente bloque</button>
        ) : (
          <button style={{ ...styles.btnPrimary, background: "#1a7a4a", opacity: loading ? 0.7 : 1 }}
            onClick={handleFinalize} disabled={loading}>
            🏁 Finalizar y guardar
          </button>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrapper: { padding: "0 0 40px 0" },
  blockCard: { background: "white", borderRadius: "12px", border: "1px solid #dde3ed", padding: "24px 28px", marginBottom: "20px", boxShadow: "0 2px 8px rgba(10,22,40,0.06)" },
  blockName: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.75rem", color: "#2e86de", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "6px" },
  blockQuestion: { fontSize: "0.95rem", color: "#2c3e50", lineHeight: 1.6, background: "#f0f4fa", borderLeft: "3px solid #2e86de", padding: "12px 16px", borderRadius: "0 8px 8px 0", marginTop: "8px" },
  warningCard: { background: "#fffbf0", border: "1px solid #f0c040", borderRadius: "10px", padding: "16px 20px", margin: "12px 0" },
  warningTitle: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.8rem", color: "#b07800", fontWeight: 600, marginBottom: "10px" },
  warnField: { background: "white", border: "1px solid #f0d080", borderRadius: "8px", padding: "10px 14px", marginBottom: "8px" },
  warnFieldName: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.75rem", color: "#c08000", fontWeight: 600, margin: "0 0 4px 0" },
  warnFieldLabel: { fontSize: "0.85rem", color: "#3a3000", margin: "0 0 4px 0" },
  warnFieldDesc: { fontSize: "0.85rem", color: "#5a4a00", margin: 0 },
  warnFieldExample: { fontSize: "0.78rem", color: "#888", fontStyle: "italic", margin: "4px 0 0 0" },
  warnButtons: { display: "flex", gap: "12px", marginTop: "12px" },
  tabs: { display: "flex", gap: "0", marginBottom: "0", borderBottom: "2px solid #e0e8f4" },
  tab: { padding: "12px 24px", border: "none", background: "transparent", cursor: "pointer", fontSize: "0.95rem", color: "#6b7f99", fontFamily: "'IBM Plex Sans', sans-serif" },
  tabActive: { color: "#2e86de", borderBottom: "2px solid #2e86de", fontWeight: 600 },
  tabContent: { background: "white", border: "1px solid #dde3ed", borderTop: "none", borderRadius: "0 0 12px 12px", padding: "24px" },
  tabDesc: { fontSize: "0.9rem", color: "#4a6080", marginBottom: "16px" },
  textarea: { width: "100%", padding: "12px", border: "1px solid #dde3ed", borderRadius: "8px", fontSize: "0.95rem", fontFamily: "'IBM Plex Sans', sans-serif", resize: "vertical", boxSizing: "border-box" },
  fieldRow: { marginBottom: "14px" },
  label: { display: "block", fontSize: "0.85rem", fontFamily: "'IBM Plex Mono', monospace", color: "#0a1628", marginBottom: "6px" },
  input: { width: "100%", padding: "10px 12px", border: "1px solid #dde3ed", borderRadius: "8px", fontSize: "0.95rem", fontFamily: "'IBM Plex Sans', sans-serif", boxSizing: "border-box" },
  autoInfo: { background: "#e8f4ff", border: "1px solid #b3d4f5", borderRadius: "8px", padding: "10px 14px", fontSize: "0.88rem", color: "#1a4a7a", marginTop: "8px" },
  bottomGrid: { display: "grid", gridTemplateColumns: "3fr 2fr", gap: "20px", marginTop: "24px" },
  jsonBox: { background: "#0a1628", borderRadius: "10px", padding: "16px", border: "1px solid #1e3a5f" },
  jsonPre: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.8rem", color: "#7ecbff", margin: 0, maxHeight: "320px", overflowY: "auto", whiteSpace: "pre-wrap" },
  validationBox: { background: "white", borderRadius: "10px", padding: "16px", border: "1px solid #dde3ed" },
  sectionTitle: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.85rem", color: "#0a1628", fontWeight: 600, marginBottom: "12px" },
  nav: { display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "24px", padding: "16px 0" },
  navInfo: { fontSize: "0.85rem", color: "#6b7f99", fontFamily: "'IBM Plex Mono', monospace" },
  btnPrimary: { background: "#2e86de", color: "white", border: "none", borderRadius: "8px", padding: "12px 24px", fontSize: "0.95rem", fontWeight: 600, cursor: "pointer", fontFamily: "'IBM Plex Sans', sans-serif" },
  btnSecondary: { background: "white", color: "#2e86de", border: "1px solid #2e86de", borderRadius: "8px", padding: "12px 24px", fontSize: "0.95rem", fontWeight: 600, cursor: "pointer", fontFamily: "'IBM Plex Sans', sans-serif" },
  alertOk: { background: "#eafaf1", border: "1px solid #a9dfbf", color: "#1e8449", borderRadius: "8px", padding: "10px 16px", fontSize: "0.88rem", marginTop: "12px" },
  alertError: { background: "#fdedec", border: "1px solid #f5b7b1", color: "#922b21", borderRadius: "8px", padding: "10px 16px", fontSize: "0.88rem", marginTop: "8px" },
  alertWarn: { background: "#fef9e7", border: "1px solid #f9e79f", color: "#7d6608", borderRadius: "8px", padding: "10px 16px", fontSize: "0.88rem", marginTop: "8px" },
};
