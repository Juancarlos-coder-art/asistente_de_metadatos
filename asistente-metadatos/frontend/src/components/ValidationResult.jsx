// src/components/ValidationResult.jsx
import { useState } from "react";
import axios from "axios";

const isProduction = window.location.hostname !== "localhost";
const BASE_URL = isProduction ? "" : (import.meta.env.VITE_API_URL || "http://localhost:8000");

const TYPE_LABELS = {
  public: "Health DCAT-AP – Acceso público",
  restricted: "Health DCAT-AP – Acceso restringido",
  nonpublic: "Health DCAT-AP – Acceso no público",
};

export default function ValidationResult() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleValidate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await axios.post(`${BASE_URL}/validate-shacl`, {}, {
        withCredentials: true,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Error al conectar con el validador SHACL.");
    }
    setLoading(false);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.icon}>🔬</span>
        <div>
          <h3 style={styles.title}>Validación SHACL — HealthDCAT-AP</h3>
          <p style={styles.subtitle}>
            Valida los metadatos generados contra las shapes oficiales de HealthDCAT-AP.
          </p>
        </div>
      </div>

      <button
        style={{ ...styles.btnValidate, opacity: loading ? 0.7 : 1 }}
        onClick={handleValidate}
        disabled={loading}
      >
        {loading ? "⏳ Validando..." : "🔬 Validar contra HealthDCAT-AP"}
      </button>

      {error && (
        <div style={styles.errorBox}>
          <strong>❌ Error:</strong> {error}
          {error.includes("localhost:8085") && (
            <p style={styles.errorHint}>
              Arranca el validador con: <code>docker run -p 8085:8080 healthdcat-validator</code>
            </p>
          )}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          {/* Cabecera resultado */}
          <div style={{
            ...styles.resultHeader,
            background: result.success ? "#defbe6" : "#fff1f1",
            borderColor: result.success ? "#198038" : "#da1e28",
          }}>
            <span style={{ fontSize: "1.5rem" }}>
              {result.success ? "✅" : "❌"}
            </span>
            <div>
              <p style={{ ...styles.resultStatus, color: result.success ? "#198038" : "#da1e28" }}>
                {result.success ? "VALIDACIÓN CORRECTA" : "VALIDACIÓN CON ERRORES"}
              </p>
              <p style={styles.resultType}>{TYPE_LABELS[result.validation_type] || result.validation_type}</p>
              <p style={styles.resultSummary}>
                {result.total_errors} error(s) · {result.total_warnings} aviso(s)
              </p>
            </div>
          </div>

          {/* Errores */}
          {result.errors.length > 0 && (
            <div style={styles.section}>
              <p style={styles.sectionTitle}>❌ Errores ({result.errors.length})</p>
              {result.errors.map((e, i) => (
                <div key={i} style={styles.errorItem}>
                  {e.path && <p style={styles.itemPath}>📍 {e.path}</p>}
                  <p style={styles.itemDesc}>{e.description}</p>
                </div>
              ))}
            </div>
          )}

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <div style={styles.section}>
              <p style={styles.sectionTitle}>⚠️ Avisos ({result.warnings.length})</p>
              {result.warnings.map((w, i) => (
                <div key={i} style={styles.warningItem}>
                  {w.path && <p style={styles.itemPath}>📍 {w.path}</p>}
                  <p style={styles.itemDesc}>{w.description}</p>
                </div>
              ))}
            </div>
          )}

          {result.success && result.warnings.length === 0 && (
            <div style={styles.successMsg}>
              🎉 Los metadatos son conformes con el estándar HealthDCAT-AP.
            </div>
          )}
        </div>
      )}
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
  },
  btnValidate: {
    background: "#0f62fe",
    color: "white",
    border: "none",
    padding: "12px 24px",
    fontSize: "0.9rem",
    fontFamily: "'IBM Plex Sans', sans-serif",
    fontWeight: 600,
    cursor: "pointer",
    marginBottom: "16px",
  },
  errorBox: {
    background: "#fff1f1",
    border: "1px solid #ffd7d9",
    borderLeft: "3px solid #da1e28",
    padding: "12px 16px",
    fontSize: "0.88rem",
    color: "#da1e28",
    marginBottom: "16px",
  },
  errorHint: {
    marginTop: "8px",
    fontSize: "0.82rem",
    color: "#525252",
  },
  resultBox: {
    border: "1px solid #e0e0e0",
  },
  resultHeader: {
    display: "flex",
    gap: "16px",
    alignItems: "center",
    padding: "16px 20px",
    borderBottom: "1px solid",
  },
  resultStatus: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "1rem",
    fontWeight: 600,
    margin: "0 0 4px 0",
  },
  resultType: {
    fontSize: "0.85rem",
    color: "#525252",
    margin: "0 0 2px 0",
  },
  resultSummary: {
    fontSize: "0.82rem",
    color: "#6f6f6f",
    margin: 0,
  },
  section: {
    padding: "16px 20px",
    borderBottom: "1px solid #e0e0e0",
  },
  sectionTitle: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "0.82rem",
    fontWeight: 600,
    color: "#161616",
    marginBottom: "10px",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  errorItem: {
    background: "#fff1f1",
    border: "1px solid #ffd7d9",
    borderLeft: "3px solid #da1e28",
    padding: "10px 14px",
    marginBottom: "8px",
  },
  warningItem: {
    background: "#fff8e1",
    border: "1px solid #f1c21b",
    borderLeft: "3px solid #f1c21b",
    padding: "10px 14px",
    marginBottom: "8px",
  },
  itemPath: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "0.78rem",
    color: "#6f6f6f",
    margin: "0 0 4px 0",
  },
  itemDesc: {
    fontSize: "0.88rem",
    color: "#161616",
    margin: 0,
    lineHeight: 1.5,
  },
  successMsg: {
    padding: "16px 20px",
    fontSize: "0.9rem",
    color: "#198038",
    fontWeight: 500,
  },
};
