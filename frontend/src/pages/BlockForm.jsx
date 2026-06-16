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
  applicable_legislation: "Legislación Aplicable",
  health_category: "Categoría sanitaria",
  theme: "Tema",
  dcat_type: "Tipo de dataset",
  provenance: "Procedencia",
  keyword: "Palabras clave",
  language: "Idioma",
  population_coverage: "Cobertura poblacional",
  number_of_records: "Número de registros",
  number_of_unique_individuals: "Número de individuos únicos",
  min_typical_age: "Edad mínima típica",
  max_typical_age: "Edad máxima típica",
  personal_data: "Datos personales",
  purpose: "Finalidad",
  contact: "Punto de contacto",
  access_url: "URL de Acceso",
  download_url: "URL de descarga",
  description: "Descripción de la distribución",
  license: "Licencia",
  format: "Formato",
  mimetype: "Tipo de medio",
  compress_format: "Formato de compresión",
  package_format: "Formato de empaquetado",
  size: "Tamaño (bytes)",
  hash: "Hash",
  hash_algorithm: "Algoritmo hash",
  rights: "Derechos",
  availability: "Disponibilidad",
  status: "Estado",
  name: "Nombre del Dataset",
  spatial: "Cobertura geográfica",
  temporal_coverage: "Cobertura temporal",
  frequency: "Frecuencia",
  was_generated_by: "Generado por",
  health_theme: "Tema de salud",
  code_values: "Valores codificados",
  coding_system: "Sistema de codificación",
  publisher: "Editor",
  creator: "Creador",
  qualified_attribution: "Atribución cualificada",
  quality_annotation: "Anotación de calidad",
  legal_basis: "Base jurídica",
  retention_period: "Período de conservación",
  publisher_note: "Nota del editor",
  temporal_resolution: "Resolución temporal",
  spatial_resolution_in_meters: "Resolución espacial (m)",
  issued: "Fecha de publicación",
  modified: "Fecha de modificación",
  alternate_identifier: "Identificador alternativo",
  conforms_to: "Se ajusta a",
  related_resource: "Recurso relacionado",
  is_referenced_by: "Referenciado por",
  url: "Página de entrada",
  documentation: "Documentación",
  version: "Versión",
  has_version: "Tiene versión",
  version_notes: "Notas de versión",
};

const NON_PUBLIC_URI = "NON_PUBLIC";

function MissingFieldsModal({ missingInfo, onClose, onSaveAndContinue, schemaInfo }) {
  const [fields, setFields] = useState({});

  const handleChange = (fieldName, value) => {
    setFields(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleHdabChange = (subfield, value) => {
    setFields(prev => ({
      ...prev,
      hdab: { ...(prev.hdab || {}), [subfield]: value }
    }));
  };

  const handleSave = () => {
    const filled = Object.fromEntries(
      Object.entries(fields).filter(([, v]) => v !== "" && v !== null && v !== undefined)
    );
    onSaveAndContinue(filled);
  };

  const anyFilled = Object.values(fields).some(v =>
    v !== "" && v !== null && v !== undefined &&
    (typeof v !== "object" || Object.values(v).some(sv => sv !== "" && sv !== null))
  );

  return (
    <div style={modalStyles.overlay}>
      <div style={modalStyles.modal}>
        <div style={modalStyles.header}>
          <span style={modalStyles.icon}>⚠️</span>
          <h2 style={modalStyles.title}>Campos con errores</h2>
        </div>
        <p style={modalStyles.subtitle}>Corrige los siguientes campos antes de continuar.</p>
        <div style={modalStyles.fieldList}>
          {missingInfo.map((item, i) => {
            const fieldName = item.field;
            const label = FIELD_LABELS_ES[fieldName] ?? item.label ?? fieldName;
            const fieldSchema = schemaInfo[fieldName] || {};
            return (
              <div key={i} style={modalStyles.fieldItem}>
                <div style={modalStyles.fieldName}>
                  🔴 {label} — <span style={{ color: "#da1e28" }}>obligatorio</span>
                </div>
                <div style={modalStyles.fieldDesc}>{item.descripcion}</div>
                {item.ejemplo && <div style={modalStyles.fieldExample}>Ej: {item.ejemplo}</div>}
                <div style={{ marginTop: "10px" }}>
                  {fieldSchema.choices ? (
                    <select style={modalStyles.input} value={fields[fieldName] || ""}
                      onChange={e => handleChange(fieldName, e.target.value)}>
                      <option value="">— Selecciona una opción —</option>
                      {fieldSchema.choices.map(ch => (
                        <option key={ch.value} value={ch.value}>{ch.label}</option>
                      ))}
                    </select>
                  ) : fieldName === "hdab" && fieldSchema.subfields ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {fieldSchema.subfields.map(sf => (
                        <div key={sf.field_name}>
                          <label style={modalStyles.subLabel}>{sf.required ? "* " : ""}{sf.label}</label>
                          {sf.choices ? (
                            <select style={modalStyles.input}
                              value={(fields.hdab || {})[sf.field_name] || ""}
                              onChange={e => handleHdabChange(sf.field_name, e.target.value)}>
                              <option value="">— Selecciona —</option>
                              {sf.choices.map(ch => (
                                <option key={ch.value} value={ch.value}>{ch.label}</option>
                              ))}
                            </select>
                          ) : (
                            <input style={modalStyles.input} type="text"
                              placeholder={`Introduce ${sf.label}...`}
                              value={(fields.hdab || {})[sf.field_name] || ""}
                              onChange={e => handleHdabChange(sf.field_name, e.target.value)} />
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <input style={modalStyles.input} type="text"
                      placeholder={`Introduce ${label}...`}
                      value={fields[fieldName] || ""}
                      onChange={e => handleChange(fieldName, e.target.value)} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <div style={modalStyles.buttons}>
          <button style={modalStyles.btnBack} onClick={onClose}>✏️ Volver a rellenar</button>
          <button style={{ ...modalStyles.btnSave, opacity: anyFilled ? 1 : 0.5 }}
            onClick={handleSave} disabled={!anyFilled}>
            💾 Guardar y continuar
          </button>
        </div>
      </div>
    </div>
  );
}

const modalStyles = {
  overlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999 },
  modal: { background: "white", borderTop: "4px solid #da1e28", maxWidth: "520px", width: "90%", boxShadow: "0 8px 32px rgba(0,0,0,0.3)", maxHeight: "85vh", display: "flex", flexDirection: "column" },
  header: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px", padding: "32px 32px 0 32px" },
  icon: { fontSize: "1.8rem" },
  title: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "1.1rem", fontWeight: 600, color: "#161616", margin: 0 },
  subtitle: { fontSize: "0.9rem", color: "#525252", marginBottom: "20px", lineHeight: 1.5, padding: "0 32px" },
  fieldList: { display: "flex", flexDirection: "column", gap: "10px", marginBottom: "0", padding: "0 32px", overflowY: "auto", flex: 1 },
  fieldItem: { background: "#fff1f1", border: "1px solid #ffd7d9", borderLeft: "3px solid #da1e28", padding: "12px 14px" },
  fieldName: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.85rem", fontWeight: 600, color: "#da1e28", marginBottom: "4px" },
  fieldDesc: { fontSize: "0.88rem", color: "#393939", lineHeight: 1.5 },
  fieldExample: { fontSize: "0.78rem", color: "#6f6f6f", fontStyle: "italic", marginTop: "4px" },
  input: { width: "100%", boxSizing: "border-box", border: "1px solid #da1e28", padding: "8px 10px", fontSize: "0.88rem", fontFamily: "'IBM Plex Sans', sans-serif", background: "white", marginTop: "4px", outline: "none" },
  subLabel: { fontSize: "0.78rem", color: "#525252", fontFamily: "'IBM Plex Sans', sans-serif", display: "block", marginBottom: "2px" },
  buttons: { display: "flex", justifyContent: "space-between", gap: "12px", padding: "16px 32px 32px 32px", borderTop: "1px solid #e0e0e0", background: "white", flexShrink: 0 },
  btnBack: { background: "transparent", border: "1px solid #c6c6c6", color: "#525252", padding: "10px 20px", fontSize: "0.88rem", fontFamily: "'IBM Plex Sans', sans-serif", cursor: "pointer" },
  btnSave: { background: "#0f62fe", color: "white", border: "none", padding: "10px 24px", fontSize: "0.9rem", fontFamily: "'IBM Plex Sans', sans-serif", fontWeight: 600, cursor: "pointer" },
};

// Helper para renderizar subcampos genéricos
function SubfieldGroup({ field, label, subfields, values, onChange }) {
  return (
    <div className="field-group">
      <label className="field-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{label}</label>
      <div className="hdab-subfields">
        {subfields.map(sf => {
          const sfLabel = `${sf.required ? "* " : ""}${sf.label}`;
          if (sf.choices) {
            return (
              <div key={sf.field_name} className="field-group">
                <label className="field-label">{sfLabel}</label>
                <select className="field-select" value={values[sf.field_name] || ""}
                  onChange={(e) => onChange({ ...values, [sf.field_name]: e.target.value })}>
                  <option value="">— Selecciona —</option>
                  {sf.choices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
                </select>
              </div>
            );
          }
          return (
            <div key={sf.field_name} className="field-group">
              <label className="field-label">{sfLabel}</label>
              <input className="field-input" type="text" placeholder={`Introduce ${sf.label}...`}
                value={values[sf.field_name] || ""}
                onChange={(e) => onChange({ ...values, [sf.field_name]: e.target.value })} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function BlockForm({ blocks, currentIdx, onNext, onPrev, onFinish, onBlockDone, initialMetadata, onMetadataChange, navigateTarget, onNavigateComplete }) {
  const [tab, setTab] = useState("ia");
  const [userContext, setUserContext] = useState("");
  const [manualFields, setManualFields] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState(null);
  const [blockMissingInfo, setBlockMissingInfo] = useState(null);
  const [metadata, setMetadata] = useState(initialMetadata || {});
  const [showModal, setShowModal] = useState(false);
  const [missingInfo, setMissingInfo] = useState([]);
  const [schemaInfo, setSchemaInfo] = useState({});
  const [schemaLoaded, setSchemaLoaded] = useState(false);
  const [pendingNavTarget, setPendingNavTarget] = useState(null);
  
  const block = blocks[currentIdx];

  useEffect(() => {
    getSchemaInfo().then(res => {
      setSchemaInfo(res.data);
      setSchemaLoaded(true);
    }).catch(() => setSchemaLoaded(true));
  }, []);

  useEffect(() => {
    if (initialMetadata && Object.keys(initialMetadata).length > 0) {
      setMetadata(initialMetadata);
    }
  }, [initialMetadata]);

  const isNonPublic = (meta = metadata) => {
    const ar = meta.access_rights || "";
    return ar.includes(NON_PUBLIC_URI);
  };

  const activeFields = block.fields.filter(f => {
    if (f === "identifier" && isNonPublic()) return false;
    if (f === "access_url" && isNonPublic()) return false;
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
    setPendingNavTarget(null);
    loadMetadata();
  }, [currentIdx]);

  useEffect(() => {
    if (navigateTarget === null || navigateTarget === currentIdx) return;
    const validateAndNavigate = async () => {
      const res = await getMissingFields(currentIdx);
      const metaRes = await getMetadata();
      const currentMeta = metaRes.data;
      const nonPublic = isNonPublic(currentMeta);
      const obligatoryMissing = res.data.descriptions.filter(item =>
        item.obligatorio && !(nonPublic && item.field === "identifier")
      );
      if (obligatoryMissing.length > 0) {
        setPendingNavTarget(navigateTarget);
        setMissingInfo(obligatoryMissing);
        const schemaRes = await getSchemaInfo();
        setSchemaInfo(schemaRes.data);
        setTimeout(() => setShowModal(true), 50);
      } else {
        onNavigateComplete(navigateTarget);
      }
    };
    validateAndNavigate();
  }, [navigateTarget]);

  const loadMetadata = async () => {
    try {
      const res = await getMetadata();
      if (res.data && Object.keys(res.data).length > 5) setMetadata(res.data);
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
      const schemaRes = await getSchemaInfo();
      setSchemaInfo(schemaRes.data);
      setTimeout(() => setShowModal(true), 50);
      return;
    }
    onNext();
  };

  const handleModalSave = async (filledFields) => {
    setLoading(true);
    try {
      const res = await saveManual(currentIdx, filledFields);
      setMetadata(res.data.metadata);
      onBlockDone(currentIdx);
      const metaRes = await getMetadata();
      const nonPublic = isNonPublic(metaRes.data);
      const misRes = await getMissingFields(currentIdx);
      setBlockMissingInfo(misRes.data.descriptions || []);
      const stillMissing = misRes.data.descriptions.filter(item =>
        item.obligatorio && !(nonPublic && item.field === "identifier")
      );
      if (stillMissing.length > 0) {
        setMissingInfo(stillMissing);
      } else {
        setShowModal(false);
        if (pendingNavTarget !== null) {
          const target = pendingNavTarget;
          setPendingNavTarget(null);
          onNavigateComplete(target);
        } else {
          onNext();
        }
      }
    } catch (e) {
      setError(e.response?.data?.detail || "Error al guardar desde el modal");
    }
    setLoading(false);
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

  const handleFieldSave = async (field, value) => {
    try {
      const res = await saveManual(currentIdx, { [field]: value });
      setMetadata(res.data.metadata);
    } catch {}
  };

  const blockQuestion = isNonPublic() && block.fields.includes("identifier")
    ? block.question + "\n\n🔒 El identificador se asignará automáticamente por ser un dataset No Público."
    : block.question;

  const STATUS_CHOICES = [
    { value: "http://purl.org/adms/status/Completed", label: "Completado" },
    { value: "http://purl.org/adms/status/UnderDevelopment", label: "En desarrollo" },
    { value: "http://purl.org/adms/status/Deprecated", label: "Obsoleto" },
    { value: "http://purl.org/adms/status/Withdrawn", label: "Retirado" },
  ];

  const renderField = (field) => {
    const isDistribBlock = block.fields.includes("access_url");
    const fieldLabel = field === "name" && isDistribBlock
      ? "Nombre del recurso"
      : (FIELD_LABELS_ES[field] ?? field);
    const fieldSchema = schemaInfo[field] || {};

    // Campos con choices → select
    const effectiveChoices = field === "status" && (!fieldSchema.choices || fieldSchema.choices.length === 0)
      ? STATUS_CHOICES
      : fieldSchema.choices;

    if (effectiveChoices) {
      return (
        <div key={field} className="field-group">
          <label className="field-label">{fieldLabel}</label>
          <select className="field-select" value={manualFields[field] || ""}
            onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })}>
            <option value="">— Selecciona una opción —</option>
            {effectiveChoices.map(ch => (
              <option key={ch.value} value={ch.value}>{ch.label}</option>
            ))}
          </select>
        </div>
      );
    }

    // Campos con subfields → SubfieldGroup
    const SUBFIELD_FIELDS = ["hdab", "contact", "legal_basis", "coding_system", "publisher", "creator", "qualified_attribution", "quality_annotation", "conforms_to", "related_resource", "documentation"];
    if (SUBFIELD_FIELDS.includes(field) && fieldSchema.subfields) {
      const values = manualFields[field] || {};
      return (
        <SubfieldGroup key={field} field={field} label={fieldLabel}
          subfields={fieldSchema.subfields} values={values}
          onChange={(newValues) => setManualFields({ ...manualFields, [field]: newValues })} />
      );
    }

    // retention_period → start + end con date picker
    if (field === "retention_period") {
      const rpValues = manualFields.retention_period || {};
      return (
        <div key={field} className="field-group">
          <label className="field-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{fieldLabel}</label>
          <div style={{ display: "flex", gap: "12px", marginTop: "6px" }}>
            <div style={{ flex: 1 }}>
              <label className="field-label" style={{ fontSize: "0.78rem", color: "#525252" }}>Inicio</label>
              <input className="field-input" type="date" value={rpValues.start || ""}
                onChange={(e) => setManualFields({ ...manualFields, retention_period: { ...rpValues, start: e.target.value } })} />
            </div>
            <div style={{ flex: 1 }}>
              <label className="field-label" style={{ fontSize: "0.78rem", color: "#525252" }}>Fin</label>
              <input className="field-input" type="date" value={rpValues.end || ""}
                onChange={(e) => setManualFields({ ...manualFields, retention_period: { ...rpValues, end: e.target.value } })} />
            </div>
          </div>
        </div>
      );
    }

    // temporal_coverage → start + end con date picker
    if (field === "temporal_coverage") {
      const tcValues = manualFields.temporal_coverage || {};
      return (
        <div key={field} className="field-group">
          <label className="field-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>{fieldLabel}</label>
          <div style={{ display: "flex", gap: "12px", marginTop: "6px" }}>
            <div style={{ flex: 1 }}>
              <label className="field-label" style={{ fontSize: "0.78rem", color: "#525252" }}>Inicio</label>
              <input className="field-input" type="date" value={tcValues.start || ""}
                onChange={(e) => setManualFields({ ...manualFields, temporal_coverage: { ...tcValues, start: e.target.value } })} />
            </div>
            <div style={{ flex: 1 }}>
              <label className="field-label" style={{ fontSize: "0.78rem", color: "#525252" }}>Fin</label>
              <input className="field-input" type="date" value={tcValues.end || ""}
                onChange={(e) => setManualFields({ ...manualFields, temporal_coverage: { ...tcValues, end: e.target.value } })} />
            </div>
          </div>
        </div>
      );
    }

    // description → textarea
    if (field === "description") {
      return (
        <div key={field} className="field-group">
          <label className="field-label">{fieldLabel}</label>
          <textarea className="field-textarea" placeholder={`Introduce ${fieldLabel}...`}
            value={manualFields[field] || ""} rows={3}
            onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })} />
        </div>
      );
    }

    // Campos numéricos
    if (["number_of_unique_individuals", "number_of_records", "min_typical_age", "max_typical_age", "size", "spatial_resolution_in_meters"].includes(field)) {
      return (
        <div key={field} className="field-group">
          <label className="field-label">{fieldLabel}</label>
          <input className="field-input" type="number" min="0"
            placeholder={`Introduce ${fieldLabel}...`}
            value={manualFields[field] ?? ""}
            onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value ? parseInt(e.target.value, 10) : "" })} />
        </div>
      );
    }

    // Campos fecha
    if (["issued", "modified"].includes(field)) {
      return (
        <div key={field} className="field-group">
          <label className="field-label">{fieldLabel}</label>
          <input className="field-input" type="date" value={manualFields[field] || ""}
            onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })} />
        </div>
      );
    }

    // Campo de texto libre por defecto
    return (
      <div key={field} className="field-group">
        <label className="field-label">{fieldLabel}</label>
        <input className="field-input" type="text" placeholder={`Introduce ${fieldLabel}...`}
          value={manualFields[field] || ""}
          onChange={(e) => setManualFields({ ...manualFields, [field]: e.target.value })} />
      </div>
    );
  };

  return (
    <div>
      {showModal && (
        <MissingFieldsModal
          missingInfo={missingInfo}
          schemaInfo={schemaInfo}
          onClose={() => { setShowModal(false); setPendingNavTarget(null); if (onNavigateComplete && navigateTarget !== null) onNavigateComplete(currentIdx); }}
          onSaveAndContinue={handleModalSave}
        />
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
          <p className="tab-desc">
            {block.fields.includes("identifier") && isNonPublic()
              ? "Dinos cómo se llama el dataset y de qué trata. El identificador ya está asignado automáticamente."
              : block.hint || block.question}
          </p>
          <div className="field-group">
            <textarea className="field-textarea"
              placeholder={block.placeholder || "Describe el bloque con tus propias palabras..."}
              value={userContext} onChange={(e) => setUserContext(e.target.value)} />
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
          {isNonPublic() && block.fields.includes("access_url") && (
            <div className="alert alert--info" style={{ marginBottom: "16px" }}>
              🔒 <strong>URL de acceso</strong> asignada automáticamente por ser un dataset No Público.
            </div>
          )}
          {activeFields.map(field => renderField(field))}
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

      <div className="bottom-grid">
        <div>
          <p className="json-viewer-header">Resumen del dataset</p>
          <MetadataPreview metadata={metadata} schemaInfo={schemaInfo} onFieldSave={handleFieldSave} />
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
            const blockErrors = validation ? validation.errors.filter(e =>
              activeFields.some(f => e.includes(f))
            ) : [];
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
                      <div key={i} className="alert alert--error" style={{ marginTop: "4px" }}>{e.replace(/^[(OBLIG|OPT)]\s*/,"").replace(/^[[^]]+]\s*/,"")}</div>
                    ))}
                  </>
                )}
                {blockOptional.length > 0 && blockOptional.map((item, i) => (
                  <div key={i} className="validation-item">
                    <span>{FIELD_LABELS_ES[item.field] ?? item.label ?? item.field}</span>
                    <span className="tag tag--warn">opcional</span>
                  </div>
                ))}
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
