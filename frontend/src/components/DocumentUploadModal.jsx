// src/components/DocumentUploadModal.jsx
import { useState, useRef } from "react";
import axios from "axios";
import { importSessionMetadata } from "../api/client";

const isProduction = window.location.hostname !== "localhost";
const BASE_URL = isProduction ? "" : (import.meta.env.VITE_API_URL || "http://localhost:8000");

// Detecta el formato por extensión o MIME
function getFileFormat(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  if (ext === "json" || file.type === "application/json") return "json";
  if (ext === "rdf"  || file.type === "application/rdf+xml") return "rdf";
  if (ext === "ttl"  || file.type === "text/turtle" || file.type === "application/x-turtle") return "ttl";
  return null;
}

const FORMAT_LABEL = { json: "JSON", rdf: "RDF/XML", ttl: "Turtle" };

export default function DocumentUploadModal({ onClose, onSkip, onSuccess, mode = "document" }) {
  const isSessionImport = mode === "session";
  const [file, setFile] = useState(null);
  const [fileFormat, setFileFormat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (!f) return;

    if (!isSessionImport) {
      if (f.type === "application/pdf") {
        setFile(f); setError(null);
      } else {
        setError("Solo se aceptan archivos PDF.");
      }
      return;
    }

    // Modo sesión: JSON, RDF/XML o Turtle
    const fmt = getFileFormat(f);
    if (fmt) {
      setFile(f); setFileFormat(fmt); setError(null);
    } else {
      setFile(null); setFileFormat(null);
      setError("Formato no soportado. Usa JSON (.json), RDF/XML (.rdf) o Turtle (.ttl).");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = isSessionImport
        ? await importSessionMetadata(file, fileFormat)
        : await axios.post(`${BASE_URL}/upload-document`, (() => {
            const formData = new FormData();
            formData.append("file", file);
            return formData;
          })(), { headers: { "Content-Type": "multipart/form-data" }, withCredentials: true });
      onSuccess(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || (isSessionImport ? "Error al importar la sesión." : "Error al procesar el documento."));
    }
    setLoading(false);
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <span style={styles.icon}>📄</span>
          <div>
            <h2 style={styles.title}>
              {isSessionImport ? "¿Quieres retomar una sesión guardada?" : "¿Tienes documentación del dataset?"}
            </h2>
            <p style={styles.subtitle}>
              {isSessionImport
                ? "Sube un JSON, RDF/XML o Turtle y el asistente recuperará los campos ya completados para seguir desde ahí."
                : "Sube un PDF y el asistente intentará rellenar automáticamente todos los campos posibles."}
            </p>
          </div>
        </div>

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
            accept={
              isSessionImport
                ? "application/json,.json,application/rdf+xml,.rdf,text/turtle,.ttl"
                : "application/pdf"
            }
            style={{ display: "none" }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <div style={styles.fileSelected}>
              <span style={styles.fileIcon}>✅</span>
              <span style={styles.fileName}>{file.name}</span>
              {fileFormat && (
                <span style={styles.formatBadge}>{FORMAT_LABEL[fileFormat]}</span>
              )}
              <span style={styles.fileSize}>({(file.size / 1024).toFixed(0)} KB)</span>
            </div>
          ) : (
            <div style={styles.dropHint}>
              <span style={styles.dropIcon}>⬆️</span>
              <p style={styles.dropText}>
                {isSessionImport
                  ? "Arrastra tu archivo aquí o haz clic para seleccionarlo"
                  : "Arrastra tu PDF aquí o haz clic para seleccionarlo"}
              </p>
              <p style={styles.dropSubtext}>
                {isSessionImport ? "JSON · RDF/XML · Turtle  ·  Máx. 10MB" : "Solo archivos PDF · Máx. 10MB"}
              </p>
              {isSessionImport && (
                <div style={styles.formatTags}>
                  <span style={styles.formatTag}>.json</span>
                  <span style={styles.formatTag}>.rdf</span>
                  <span style={styles.formatTag}>.ttl</span>
                </div>
              )}
            </div>
          )}
        </div>

        {error && <div style={styles.error}>❌ {error}</div>}

        <div style={styles.buttons}>
          {isSessionImport ? (
            <button style={styles.btnSkip} onClick={onClose} disabled={loading}>Cancelar</button>
          ) : (
            <button style={styles.btnSkip} onClick={onSkip} disabled={loading}>Omitir y continuar manualmente</button>
          )}
          <button
            style={{ ...styles.btnUpload, opacity: (!file || loading) ? 0.6 : 1 }}
            onClick={handleUpload}
            disabled={!file || loading}
          >
            {loading ? "Procesando..." : (isSessionImport ? "↩ Reanudar sesión" : "⚡ Analizar documento")}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
    background: "rgba(0,0,0,0.6)", display: "flex",
    alignItems: "center", justifyContent: "center", zIndex: 9999,
  },
  modal: {
    background: "white", borderTop: "4px solid #0f62fe",
    padding: "32px", maxWidth: "560px", width: "90%",
    boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
  },
  header: { display: "flex", gap: "16px", alignItems: "flex-start", marginBottom: "24px" },
  icon: { fontSize: "2.5rem", lineHeight: 1 },
  title: {
    fontFamily: "'IBM Plex Mono', monospace", fontSize: "1.1rem",
    fontWeight: 600, color: "#161616", margin: "0 0 6px 0",
  },
  subtitle: { fontSize: "0.88rem", color: "#525252", margin: 0, lineHeight: 1.5 },
  dropZone: {
    border: "2px dashed #c6c6c6", padding: "32px", textAlign: "center",
    cursor: "pointer", marginBottom: "16px",
    transition: "border-color 0.15s, background 0.15s", background: "#f4f4f4",
  },
  dropZoneActive: { borderColor: "#0f62fe", background: "#edf5ff" },
  dropHint: {},
  dropIcon: { fontSize: "2rem", display: "block", marginBottom: "8px" },
  dropText: { fontSize: "0.9rem", color: "#161616", margin: "0 0 4px 0", fontWeight: 500 },
  dropSubtext: { fontSize: "0.78rem", color: "#6f6f6f", margin: "0 0 10px 0" },
  formatTags: { display: "flex", justifyContent: "center", gap: "6px" },
  formatTag: {
    fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.72rem",
    background: "#e0e0e0", color: "#393939", padding: "2px 8px",
  },
  fileSelected: { display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", flexWrap: "wrap" },
  fileIcon: { fontSize: "1.4rem" },
  fileName: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.85rem", color: "#161616", fontWeight: 600 },
  formatBadge: {
    fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.72rem",
    background: "#0f62fe", color: "white", padding: "2px 8px",
  },
  fileSize: { fontSize: "0.78rem", color: "#6f6f6f" },
  error: {
    background: "#fff1f1", border: "1px solid #ffd7d9",
    borderLeft: "3px solid #da1e28", padding: "10px 14px",
    fontSize: "0.88rem", color: "#da1e28", marginBottom: "16px",
  },
  buttons: { display: "flex", justifyContent: "space-between", gap: "12px", marginTop: "8px" },
  btnSkip: {
    background: "transparent", border: "1px solid #c6c6c6", color: "#525252",
    padding: "10px 20px", fontSize: "0.88rem",
    fontFamily: "'IBM Plex Sans', sans-serif", cursor: "pointer",
  },
  btnUpload: {
    background: "#0f62fe", border: "none", color: "white",
    padding: "10px 24px", fontSize: "0.88rem",
    fontFamily: "'IBM Plex Sans', sans-serif", fontWeight: 600, cursor: "pointer",
  },
};
