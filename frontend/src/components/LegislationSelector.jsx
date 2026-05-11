// src/components/LegislationSelector.jsx
import { useState } from "react";
import axios from "axios";

const isProduction = window.location.hostname !== "localhost";
const BASE_URL = isProduction ? "" : (import.meta.env.VITE_API_URL || "http://localhost:8000");

const LEGISLATION_OPTIONS = [
  {
    uri: "http://data.europa.eu/eli/reg/2016/679/oj",
    label: "GDPR — Reglamento General de Protección de Datos (UE) 2016/679",
    required: true,
  },
  {
    uri: "http://data.europa.eu/eli/reg/2025/327/oj",
    label: "Reglamento EHDS — Espacio Europeo de Datos de Salud (UE) 2025/327",
    required: false,
  },
  {
    uri: "http://data.europa.eu/eli/dir/2019/1024/oj",
    label: "Directiva de Datos Abiertos (UE) 2019/1024",
    required: false,
  },
  {
    uri: "http://data.europa.eu/eli/reg/2022/868/oj",
    label: "Reglamento de Gobernanza de Datos (UE) 2022/868",
    required: false,
  },
  {
    uri: "https://www.boe.es/eli/es/lo/2018/12/05/3",
    label: "LOPDGDD — Ley Orgánica de Protección de Datos (España) 3/2018",
    required: false,
  },
];

export default function LegislationSelector({ onSave }) {
  const [selected, setSelected] = useState(
    LEGISLATION_OPTIONS.filter(o => o.required).map(o => o.uri)
  );
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  const toggle = (uri) => {
    // No se puede desmarcar el GDPR
    if (LEGISLATION_OPTIONS.find(o => o.uri === uri)?.required) return;
    setSelected(prev =>
      prev.includes(uri) ? prev.filter(u => u !== uri) : [...prev, uri]
    );
    setSaved(false);
  };

  const handleSave = async () => {
    setLoading(true);
    const legislation = selected.map(uri => ({
      uri,
      label: LEGISLATION_OPTIONS.find(o => o.uri === uri)?.label.split(" — ")[0] || uri,
    }));

    try {
      await axios.post(`${BASE_URL}/save-legislation`, { legislation }, { withCredentials: true });
      setSaved(true);
      if (onSave) onSave(legislation);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.icon}>⚖️</span>
        <div>
          <h3 style={styles.title}>Legislación aplicable</h3>
          <p style={styles.subtitle}>
            El GDPR es obligatorio. Selecciona cualquier otra normativa que aplique a este dataset.
          </p>
        </div>
      </div>

      <div style={styles.list}>
        {LEGISLATION_OPTIONS.map(opt => (
          <div
            key={opt.uri}
            style={{
              ...styles.item,
              ...(selected.includes(opt.uri) ? styles.itemSelected : {}),
              cursor: opt.required ? "not-allowed" : "pointer",
            }}
            onClick={() => toggle(opt.uri)}
          >
            <div style={styles.checkbox}>
              {selected.includes(opt.uri) ? "☑" : "☐"}
            </div>
            <div style={styles.itemContent}>
              <span style={styles.itemLabel}>{opt.label}</span>
              {opt.required && (
                <span style={styles.requiredTag}>obligatorio</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <button
        style={{ ...styles.btn, opacity: loading ? 0.7 : 1 }}
        onClick={handleSave}
        disabled={loading}
      >
        {loading ? "Guardando..." : saved ? "✅ Guardado" : "💾 Confirmar legislación"}
      </button>
    </div>
  );
}

const styles = {
  container: {
    background: "white",
    border: "1px solid #c6c6c6",
    borderTop: "3px solid #0f62fe",
    padding: "24px",
    marginTop: "24px",
  },
  header: {
    display: "flex",
    gap: "16px",
    alignItems: "flex-start",
    marginBottom: "20px",
  },
  icon: { fontSize: "2rem", lineHeight: 1 },
  title: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "1rem",
    fontWeight: 600,
    color: "#161616",
    margin: "0 0 4px 0",
  },
  subtitle: {
    fontSize: "0.88rem",
    color: "#525252",
    margin: 0,
    lineHeight: 1.5,
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginBottom: "20px",
  },
  item: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "12px 14px",
    border: "1px solid #e0e0e0",
    background: "#f4f4f4",
    transition: "background 0.1s, border-color 0.1s",
  },
  itemSelected: {
    background: "#edf5ff",
    borderColor: "#0f62fe",
  },
  checkbox: {
    fontSize: "1.3rem",
    color: "#0f62fe",
    flexShrink: 0,
  },
  itemContent: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexWrap: "wrap",
  },
  itemLabel: {
    fontSize: "0.88rem",
    color: "#161616",
    lineHeight: 1.4,
  },
  requiredTag: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "0.7rem",
    color: "#0f62fe",
    background: "#edf5ff",
    border: "1px solid #0f62fe",
    padding: "2px 6px",
    flexShrink: 0,
  },
  btn: {
    background: "#0f62fe",
    color: "white",
    border: "none",
    padding: "10px 24px",
    fontSize: "0.9rem",
    fontFamily: "'IBM Plex Sans', sans-serif",
    fontWeight: 600,
    cursor: "pointer",
  },
};
