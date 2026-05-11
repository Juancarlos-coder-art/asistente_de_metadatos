// src/pages/BlockForm.jsx
import { useState, useEffect } from "react";
import MetadataPreview from "../components/MetadataPreview";
import {
  completeBlock, saveManual, validateMetadata,
  getMissingFields, finalizeMetadata, getMetadata, getSchemaInfo
} from "../api/client";

const FIELD_LABELS_ES = {
  title: "Título",
  notes: "Descripción",
  identifier: "Identificador",
  hdab: "Autoridad de acceso a los datos",
  access_rights: "Derechos de acceso",
  health_category: "Categoría sanitaria",
  theme: "Tema",
  dcat_type: "Tipo de dataset",
  provenance: "Procedencia",
  keyword: "Palabras clave",
  contact: "Punto de contacto",
};

const NON_PUBLIC_URI = "NON_PUBLIC";

function MissingFieldsModal({ missingInfo, onClose }) {
  return (
    <div style={modalStyles.overlay}>
      <div style={modalStyles.modal}>
        <div style={modalStyles.header}>
          <span style={modalStyles.icon}>⚠️</span>
          <h2 style={modalStyles.title}>Campos obligatorios sin rellenar</h2>
        </div>
        <p style={modalStyles.subtitle}>
          Los siguientes campos son obligatorios. Debes rellenarlos antes de continuar.
        </p>
        <div style={modalStyles.fieldList}>
          {missingInfo.map((item, i) => (
            <div key={i} style={modalStyles.fieldItem}>
              <div style={modalStyles.fieldName}>
                🔴 {FIELD_LABELS_ES[item.field] ?? item.field}
              </div>
              <div style={modalStyles.fieldDesc}>{item.descripcion}</div>
              {item.ejemplo && (
                <div style={modalStyles.fieldExample}>Ej: {item.ejemplo}</div>
              )}
            </div>
          ))}
        </div>
        <div style={modalStyles.buttons}>
          <button style={modalStyles.btnClose} onClick={onClose}>
            ✏️ Volver a rellenar
          </button>
        </div>
      </div>
    </div>
  );
}

const placeholdersPorBloque = {
  derechos_de_acceso: "Ej.: El acceso está restringido a personal sanitario autorizado...",
  identificacion_basica: "Ej.: Dataset sobre casos de viruela del mono en España en 2023...",
  organismo_acceso_datos_sanitarios: "Ej.: Datos recopilados por el Ministerio de Sanidad...",
  punto_de_contacto: "Ej.: Contacta en info@ministeriodesanidad.es o visita https://www.sanidad.gob.es/contacto",
  default: "Describe el contenido del dataset..."
};

const modalStyles = {
  overlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999 },
  modal: { background: "white", borderTop: "4px solid #da1e28", padding: "32px", maxWidth: "520px", width: "90%", boxShadow: "0 8px 32px rgba(0,0,0,0.3)", maxHeight: "80vh", overflowY: "auto" },
  header: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" },
  icon: { fontSize: "1.8rem" },
  title: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "1.1rem", fontWeight: 600, color: "#161616", margin: 0 },
  subtitle: { fontSize: "0.9rem", color: "#525252", marginBottom: "20px", lineHeight: 1.5 },
  fieldList: { display: "flex", flexDirection: "column", gap: "10px", marginBottom: "24px" },
  fieldItem: { background: "#fff1f1", border: "1px solid #ffd7d9", borderLeft: "3px solid #da1e28", padding: "12px 14px" },
  fieldName: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.85rem", fontWeight: 600, color: "#da1e28", marginBottom: "4px" },
  fieldDesc: { fontSize: "0.88rem", color: "#393939", lineHeight: 1.5 },
  fieldExample: { fontSize: "0.78rem", color: "#6f6f6f", fontStyle: "italic", marginTop: "4px" },
  buttons: { display: "flex", justifyContent: "flex-end" },
  btnClose: { background: "#0f62fe", color: "white", border: "none", padding: "12px 24px", fontSize: "0.9rem", fontFamily: "'IBM Plex Sans', sans-serif", fontWeight: 500, cursor: "pointer" },
};

export default function BlockForm({ blocks, currentIdx, onNext, onPrev, onFinish, onBlockDone }) {
  const [tab, setTab] = useState("ia");
  const [userContext, setUserContext] = useState("");
  const [manualFields, setManualFields] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState(null);
  const [blockMissingInfo, setBlockMissingInfo] = useState(null);
  const [metadata, setMetadata] = useState({});
  const [showModal, setShowModal] = useState(false);
  const [missingInfo, setMissingInfo] = useState([]);
  const [schemaInfo, setSchemaInfo] = useState({});

  const block = blocks[currentIdx];

  useEffect(() => {
    getSchemaInfo().then(res => setSchemaInfo(res.data)).catch(() => {});
  }, []);

  const isNonPublic = (meta = metadata) => {
    const ar = meta.access_rights || "";
    return ar.includes(NON_PUBLIC_URI);
  };

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
    setShowModal(false);
    setBlockMissingInfo(null);
    loadMetadata();
  }, [currentIdx]);

  const loadMetadata = async () => {
    try {
      const res = await getMetadata();
      setMetadata(res.data);
      const val = await validateMetadata();
      setValidation(val.data);
      const misRes = await getMissingFields(currentIdx);
      setBlockMissingInfo(misRes.data.descriptions || []);
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
      const misRes = await getMissingFields(currentIdx);
      setBlockMissingInfo(misRes.data.descriptions || []);
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
      const misRes = await getMissingFields(currentIdx);
      setBlockMissingInfo(misRes.data.descriptions || []);
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
    const nonPublic = isNonPublic(currentMeta);

    const obligatoryMissing = res.data.descriptions.filter(item =>
      item.obligatorio && !(nonPublic && item.field === "identifier")
    );

    if (obligatoryMissing.length > 0) {
      setMissingInfo(obligatoryMissing);
      setShowModal(true);
      return;
    }
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

  const placeholder = placeholdersPorBloque[block.name] || block.hint || block.question || placeholdersPorBloque.default;

  const blockQuestion = isNonPublic() && block.fields.includes("identifier")
    ? block.question + "\n\n🔒 El identificador se asignará automáticamente por ser un dataset No Público."
    : block.question;

  return (
    <div>
      {showModal && (
        <MissingFieldsModal missingInfo={missingInfo} onClose={() => setShowModal(false)} />
      )}

      <div className="block-card">
        <p className="block-label">Bloque {currentIdx + 1} · {block.name.replace(/_/g, " ").toUpperCase()}</p>
        <p className="block-question" style={{ whiteSpace: "pre-line" }}>{blockQuestion}</p>
      </div>

      <div className="tabs">
        <button className={`tab-btn ${tab === "ia" ? "tab-btn--active" : ""}`} onClick={() => setTab("ia")}>Completar automáticamente</button>
        <button className={`tab-btn ${tab === "manual" ? "tab-btn--active" : ""}`} onClick={() => setTab("manual")}>Rellenar manualmente</button>
      </div>

      {tab === "ia" && (
        <div className="tab-content">
          <p className="tab-desc">{block.hint || "Describe este bloque con tus propias palabras."}</p>
          <div className="field-group">
            <textarea
              className="field-textarea"
              placeholder={placeholder}
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
          {isNonPublic() && block.fields.includes("identifier") && (
            <div className="alert alert--info" style={{ marginBottom: "16px" }}>
              🔒 <strong>Identificador</strong> asignado automáticamente por ser un dataset No Público.
            </div>
          )}
          {activeFields.map(field => {
            const fieldLabel = FIELD_LABELS_ES[field] ?? field;
            const fieldSchema = schemaInfo[field] || {};

            // ── access_rights → select ──
            if (field === "access_rights" && fieldSchema.choices) {
              return (
                <div key={field} className="field-group">
                  <label className="field-label">{fieldLabel}</label>
                  <select className="field-select" value={manualFields[field] || ""} onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}>
                    <option value="">— Selecciona una opción —</option>
                    {fieldSchema.choices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
                  </select>
                </div>
              );
            }

            // ── health_category → select ──
            if (field === "health_category" && fieldSchema.choices) {
              return (
                <div key={field} className="field-group">
                  <label className="field-label">{fieldLabel}</label>
                  <select className="field-select" value={manualFields[field] || ""} onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}>
                    <option value="">— Selecciona una categoría sanitaria —</option>
                    {fieldSchema.choices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
                  </select>
                </div>
              );
            }

            // ── theme → select ──
            if (field === "theme" && fieldSchema.choices) {
              return (
                <div key={field} className="field-group">
                  <label className="field-label">{fieldLabel}</label>
                  <select className="field-select" value={manualFields[field] || ""} onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}>
                    <option value="">— Selecciona un tema —</option>
                    {fieldSchema.choices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
                  </select>
                </div>
              );
            }

            // ── dcat_type → select ──
            if (field === "dcat_type" && fieldSchema.choices) {
              return (
                <div key={field} className="field-group">
                  <label className="field-label">{fieldLabel}</label>
                  <select className="field-select" value={manualFields[field] || ""} onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}>
                    <option value="">— Selecciona un tipo de dataset —</option>
                    {fieldSchema.choices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
                  </select>
                </div>
              );
            }

            // ── hdab → subcampos ──
            if (field === "hdab" && fieldSchema.subfields) {
              const hdabValues = manualFields.hdab || {};
              return (
                <div key={field} className="field-group">
                  <label className="field-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{fieldLabel}</label>
                  <div className="hdab-subfields">
                    {fieldSchema.subfields.map(sf => {
                      const sfLabel = `${sf.required ? "* " : ""}${sf.label}`;
                      if (sf.choices) {
                        return (
                          <div key={sf.field_name} className="field-group">
                            <label className="field-label">{sfLabel}</label>
                            <select className="field-select" value={hdabValues[sf.field_name] || ""} onChange={(e) => setManualFields({ ...manualFields, hdab: { ...hdabValues, [sf.field_name]: e.target.value } })}>
                              <option value="">— Selecciona —</option>
                              {sf.choices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
                            </select>
                          </div>
                        );
                      }
                      return (
                        <div key={sf.field_name} className="field-group">
                          <label className="field-label">{sfLabel}</label>
                          <input className="field-input" type="text" placeholder={`Introduce ${sf.label}...`} value={hdabValues[sf.field_name] || ""} onChange={(e) => setManualFields({ ...manualFields, hdab: { ...hdabValues, [sf.field_name]: e.target.value } })} />
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            }

            // ── contact → subcampos email y url ──
            if (field === "contact" && fieldSchema.subfields) {
              const contactValues = manualFields.contact || {};
              return (
                <div key={field} className="field-group">
                  <label className="field-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{fieldLabel}</label>
                  <div className="hdab-subfields">
                    {fieldSchema.subfields.map(sf => (
                      <div key={sf.field_name} className="field-group">
                        <label className="field-label">{sf.label}</label>
                        <input className="field-input" type="text" placeholder={`Introduce ${sf.label}...`} value={contactValues[sf.field_name] || ""} onChange={(e) => setManualFields({ ...manualFields, contact: { ...contactValues, [sf.field_name]: e.target.value } })} />
                      </div>
                    ))}
                  </div>
                </div>
              );
            }

            // ── Campo de texto normal ──
            return (
              <div key={field} className="field-group">
                <label className="field-label">{fieldLabel}</label>
                <input className="field-input" type="text" placeholder={`Introduce ${fieldLabel}...`} value={manualFields[field] || ""} onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })} />
              </div>
            );
          })}

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
          {(() => {
            if (!blockMissingInfo) {
              return <div className="alert alert--info" style={{ marginTop: 0 }}>⏳ Pendiente de validación. Completa el bloque para comprobar.</div>;
            }

            const blockObligatory = blockMissingInfo.filter(item =>
              item.obligatorio && !(isNonPublic() && item.field === "identifier")
            );
            const blockOptional = blockMissingInfo.filter(item => !item.obligatorio);
            const blockErrors = validation ? validation.errors.filter(e => activeFields.some(f => e.includes(f))) : [];
            const globalMissingCount = validation
              ? validation.missing_required.filter(m => !activeFields.includes(m)).length
              : 0;

            return (
              <>
                {blockObligatory.length === 0 && blockErrors.length === 0 ? (
                  <div className="alert alert--ok" style={{ marginTop: 0 }}>✅ Bloque actual correcto.</div>
                ) : (
                  <>
                    {blockObligatory.map((item, i) => (
                      <div key={i} className="validation-item">
                        <span>{FIELD_LABELS_ES[item.field] ?? item.label ?? item.field}</span>
                        <span className="tag tag--error">obligatorio</span>
                      </div>
                    ))}
                    {blockErrors.map((e, i) => (
                      <div key={i} className="alert alert--error" style={{ marginTop: "4px" }}>{e}</div>
                    ))}
                  </>
                )}
                {blockOptional.length > 0 && (
                  <div style={{ marginTop: "8px" }}>
                    {blockOptional.map((item, i) => (
                      <div key={i} className="validation-item" style={{ borderLeft: "3px solid #f1c21b" }}>
                        <span>{FIELD_LABELS_ES[item.field] ?? item.label ?? item.field}</span>
                        <span className="tag">opcional</span>
                      </div>
                    ))}
                  </div>
                )}
                {globalMissingCount === 0 && blockObligatory.length === 0 && blockErrors.length === 0 && (
                  <div className="alert alert--ok" style={{ marginTop: "8px" }}>
                    🎉 Todos los campos obligatorios están completos.
                  </div>
                )}
              </>
            );
          })()}
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
