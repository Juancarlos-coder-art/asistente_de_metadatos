// src/pages/BlockForm.jsx
import { useState, useEffect } from "react";
import MetadataPreview from "../components/MetadataPreview";
import {
  completeBlock, saveManual, validateMetadata,
  getMissingFields, finalizeMetadata, getMetadata
} from "../api/client";

const FIELD_LABELS_ES = {
  title: "Título",
  notes: "Descripción",
  identifier: "Identificador",
  hdab: "Autoridad de acceso a los datos",
  access_rights: "Derechos de acceso",
};

const NON_PUBLIC_URI = "NON_PUBLIC";

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

  // ── Detecta si el acceso es No Público ──
  const isNonPublic = (meta = metadata) => {
    const ar = meta.access_rights || "";
    return ar.includes(NON_PUBLIC_URI);
  };

  // ── Filtra campos según lógica condicional ──
  const activeFields = block.fields.filter(f => {
    if (f === "identifier" && isNonPublic()) return false;
    if (f === "applicable_legislation") return false;
    return true;
  });

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
    const metaRes = await getMetadata();
    const currentMeta = metaRes.data;

    // Si NON_PUBLIC → filtrar identifier del aviso
    const nonPublic = isNonPublic(currentMeta);
    const missing = res.data.descriptions.filter(item =>
      !(nonPublic && item.field === "identifier")
    );

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
    } catch {
      setError("Error al finalizar");
    }
    setLoading(false);
  };

  // ── Pregunta adaptada si es No Público y el bloque tiene identifier ──
  const blockQuestion = isNonPublic() && block.fields.includes("identifier")
    ? block.question + "\n\n🔒 El identificador se asignará automáticamente por ser un dataset No Público."
    : block.question;

  return (
    <div>
      {/* Tarjeta del bloque */}
      <div className="block-card">
        <p className="block-label">Bloque {currentIdx + 1} · {block.name.replace(/_/g, " ").toUpperCase()}</p>
        <p className="block-question" style={{ whiteSpace: "pre-line" }}>{blockQuestion}</p>
      </div>

      {/* Aviso campos faltantes */}
      {showWarning && (
        <div className="missing-warning">
          <p className="missing-warning-title">⚠️ {missingInfo.length} campo(s) sin rellenar — puedes completarlos o continuar</p>
          {missingInfo.map((item, i) => (
            <div key={i} className="missing-field-item">
              <p className="missing-field-name">{FIELD_LABELS_ES[item.field] ?? item.field}</p>
              <p className="missing-field-desc"><strong>{item.label}</strong>{item.obligatorio ? " · obligatorio" : ""} — {item.descripcion}</p>
              {item.ejemplo && <p className="missing-field-example">Ej: {item.ejemplo}</p>}
            </div>
          ))}
          <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
            <button className="btn btn--secondary btn--sm" onClick={() => setShowWarning(false)}>✏️ Volver a rellenar</button>
            <button className="btn btn--primary btn--sm" onClick={() => { setShowWarning(false); onNext(); }}>➡️ Continuar de todas formas</button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab-btn ${tab === "ia" ? "tab-btn--active" : ""}`} onClick={() => setTab("ia")}>Completar automáticamente</button>
        <button className={`tab-btn ${tab === "manual" ? "tab-btn--active" : ""}`} onClick={() => setTab("manual")}>Rellenar manualmente</button>
      </div>

      {tab === "ia" && (
        <div className="tab-content">
          <p className="tab-desc">Describe el dataset con tus propias palabras y el asistente extraerá los campos.</p>
          <div className="field-group">
            <textarea
              className="field-textarea"
              placeholder="Ej.: El dataset trata sobre casos de viruela del mono en España durante 2023, incluyendo distribución geográfica y datos demográficos..."
              value={userContext}
              onChange={(e) => setUserContext(e.target.value)}
            />
          </div>
          <button className="btn btn--primary" onClick={handleComplete} disabled={loading || !userContext.trim()}>
            {loading ? "Analizando..." : "Completar bloque"}
          </button>
          {result && <div className="alert alert--ok">✅ Bloque completado correctamente.</div>}
          {error && <div className="alert alert--error">❌ {error}</div>}
        </div>
      )}

      {tab === "manual" && (
        <div className="tab-content">
          <p className="tab-desc">Rellena los campos del bloque uno a uno.</p>

          {/* Aviso identificador automático */}
          {isNonPublic() && block.fields.includes("identifier") && (
            <div className="alert alert--info" style={{ marginBottom: "16px" }}>
              🔒 <strong>Identificador</strong> asignado automáticamente por ser un dataset No Público.
            </div>
          )}

          {activeFields.map(field => (
            <div key={field} className="field-group">
              <label className="field-label">{FIELD_LABELS_ES[field] ?? field}</label>
              <input
                className="field-input"
                type="text"
                placeholder={`Introduce ${FIELD_LABELS_ES[field] ?? field}...`}
                value={manualFields[field] || ""}
                onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}
              />
            </div>
          ))}

          {block.fields.includes("applicable_legislation") && (
            <div className="alert alert--info">
              <strong>applicable_legislation</strong> se rellena automáticamente al finalizar.
            </div>
          )}

          <button className="btn btn--primary" style={{ marginTop: "16px" }} onClick={handleManualSave} disabled={loading}>
            {loading ? "Guardando..." : "Guardar bloque"}
          </button>
          {result && <div className="alert alert--ok">✅ Bloque guardado correctamente.</div>}
          {error && <div className="alert alert--error">❌ {error}</div>}
        </div>
      )}

      {/* Vista previa + Validación */}
      <div className="bottom-grid">
        <div>
          <p className="json-viewer-header">Resumen del dataset</p>
          <MetadataPreview metadata={metadata} />
        </div>
        <div className="validation-box">
          <p className="validation-header">Estado de validación</p>
          {validation.valid ? (
            <div className="alert alert--ok" style={{ marginTop: 0 }}>✅ Todo correcto.</div>
          ) : (
            <>
              {validation.missing_required
                .filter(m => !(isNonPublic() && m === "identifier"))
                .map((m, i) => (
                  <div key={i} className="validation-item">
                    <span>{FIELD_LABELS_ES[m] ?? m}</span>
                    <span className="tag">obligatorio</span>
                  </div>
                ))}
              {validation.errors.map((e, i) => (
                <div key={i} className="alert alert--error" style={{ marginTop: "4px" }}>{e}</div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* Navegación */}
      <div className="nav-bar">
        <button className="btn btn--secondary" onClick={onPrev} style={{ visibility: currentIdx === 0 ? "hidden" : "visible" }}>
          ⬅️ Anterior
        </button>
        <span className="nav-info">Bloque {currentIdx + 1} / {blocks.length} · {block.name.replace(/_/g, " ")}</span>
        {currentIdx < blocks.length - 1 ? (
          <button className="btn btn--primary" onClick={handleNext}>➡️ Siguiente bloque</button>
        ) : (
          <button className="btn btn--success" onClick={handleFinalize} disabled={loading}>
            🏁 Finalizar y guardar
          </button>
        )}
      </div>
    </div>
  );
}
