// src/components/DocumentUploadModal.jsx
import { useState, useRef } from "react";
import axios from "axios";

const isProduction = window.location.hostname !== "localhost";
const BASE_URL = isProduction ? "" : (import.meta.env.VITE_API_URL || "http://localhost:8000");

export default function DocumentUploadModal({ onClose, onSkip, onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (f && f.type === "application/pdf") {
      setFile(f);
      setError(null);
    } else {
      setError("Solo se aceptan archivos PDF.");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${BASE_URL}/upload-document`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        withCredentials: true,
      });
      onSuccess(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Error al procesar el documento.");
    }
    setLoading(false);
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        {/* Cabecera */}
        <div style={styles.header}>
          <span style={styles.icon}>📄</span>
          <div>
            <h2 style={styles.title}>¿Tienes documentación del dataset?</h2>
            <p style={styles.subtitle}>
              Sube un PDF y el asistente intentará rellenar automáticamente
              todos los campos posibles.
            </p>
          </div>
        </div>

        {/* Zona de subida */}
        <div
          style={{ ...styles.dropZone, ...(dragOver ? styles.dropZoneActive : {}) }}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFile(e.dataTransfer.files[0]);
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            style={{ display: "none" }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <div style={styles.fileSelected}>
              <span style={styles.fileIcon}>✅</span>
              <span style={styles.fileName}>{file.name}</span>
              <span style={styles.fileSize}>({(file.size / 1024).toFixed(0)} KB)</span>
            </div>
          ) : (
            <div style={styles.dropHint}>
              <span style={styles.dropIcon}>⬆️</span>
              <p style={styles.dropText}>Arrastra tu PDF aquí o haz clic para seleccionarlo</p>
              <p style={styles.dropSubtext}>Solo archivos PDF · Máx. 10MB</p>
            </div>
          )}
        </div>

        {error && (
          <div style={styles.error}>❌ {error}</div>
        )}

        {/* Botones */}
        <div style={styles.buttons}>
          <button style={styles.btnSkip} onClick={onSkip} disabled={loading}>
            Omitir y continuar manualmente
          </button>
          <button
            style={{ ...styles.btnUpload, opacity: (!file || loading) ? 0.6 : 1 }}
            onClick={handleUpload}
            disabled={!file || loading}
          >
            {loading ? "Procesando..." : "⚡ Analizar documento"}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    top: 0, left: 0, right: 0, bottom: 0,
    background: "rgba(0,0,0,0.6)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
  },
  modal: {
    background: "white",
    borderTop: "4px solid #0f62fe",
    padding: "32px",
    maxWidth: "560px",
    width: "90%",
    boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
  },
  header: {
    display: "flex",
    gap: "16px",
    alignItems: "flex-start",
    marginBottom: "24px",
  },
  icon: { fontSize: "2.5rem", lineHeight: 1 },
  title: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "1.1rem",
    fontWeight: 600,
    color: "#161616",
    margin: "0 0 6px 0",
  },
  subtitle: {
    fontSize: "0.88rem",
    color: "#525252",
    margin: 0,
    lineHeight: 1.5,
  },
  dropZone: {
    border: "2px dashed #c6c6c6",
    padding: "32px",
    textAlign: "center",
    cursor: "pointer",
    marginBottom: "16px",
    transition: "border-color 0.15s, background 0.15s",
    background: "#f4f4f4",
  },
  dropZoneActive: {
    borderColor: "#0f62fe",
    background: "#edf5ff",
  },
  dropHint: {},
  dropIcon: { fontSize: "2rem", display: "block", marginBottom: "8px" },
  dropText: {
    fontSize: "0.9rem",
    color: "#161616",
    margin: "0 0 4px 0",
    fontWeight: 500,
  },
  dropSubtext: {
    fontSize: "0.78rem",
    color: "#6f6f6f",
    margin: 0,
  },
  fileSelected: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
  },
  fileIcon: { fontSize: "1.4rem" },
  fileName: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "0.85rem",
    color: "#161616",
    fontWeight: 600,
  },
  fileSize: {
    fontSize: "0.78rem",
    color: "#6f6f6f",
  },
  error: {
    background: "#fff1f1",
    border: "1px solid #ffd7d9",
    borderLeft: "3px solid #da1e28",
    padding: "10px 14px",
    fontSize: "0.88rem",
    color: "#da1e28",
    marginBottom: "16px",
  },
  buttons: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
    marginTop: "8px",
  },
  btnSkip: {
    background: "transparent",
    border: "1px solid #c6c6c6",
    color: "#525252",
    padding: "10px 20px",
    fontSize: "0.88rem",
    fontFamily: "'IBM Plex Sans', sans-serif",
    cursor: "pointer",
  },
  btnUpload: {
    background: "#0f62fe",
    border: "none",
    color: "white",
    padding: "10px 24px",
    fontSize: "0.88rem",
    fontFamily: "'IBM Plex Sans', sans-serif",
    fontWeight: 600,
    cursor: "pointer",
  },
};
