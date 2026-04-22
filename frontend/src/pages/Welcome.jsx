// src/pages/Welcome.jsx
import { useState } from "react";
import { getLlmStatus } from "../api/client";

export default function Welcome({ onStart }) {
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    await getLlmStatus().catch(() => {});
    setLoading(false);
    onStart();
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>🏥</div>
        <h1 style={styles.title}>
          Hola, soy el Asistente conversacional del ENDS.<br />
          Te ayudaré a metadatar tu conjunto de datos.
        </h1>
        <p style={styles.subtitle}>
          El proceso está dividido en bloques de preguntas.<br />
          Puedes responder con tus propias palabras y la IA estructurará
          la información conforme al esquema <strong>HealthDCAT-AP-ES</strong>.
        </p>

        <hr style={styles.divider} />

        <div style={styles.guideBox}>
          <p style={styles.guideTitle}>📄 GUÍA DE CAMPOS</p>
          <p style={styles.guideDesc}>
            Si quieres información sobre los campos que necesitamos
            para metadatar tu dataset, descarga aquí la guía completa.
          </p>
          <a
            href="http://localhost:8000/guide"
            download="guia_campos_ends.docx"
            style={styles.downloadLink}
          >
            ⬇️ Pincha aquí para descargar la guía de campos (.docx)
          </a>
        </div>

        <button
          style={{ ...styles.startBtn, opacity: loading ? 0.7 : 1 }}
          onClick={handleStart}
          disabled={loading}
        >
          {loading ? "Cargando..." : "🚀 Comenzar a metadatar"}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#f4f6f9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    fontFamily: "'IBM Plex Sans', sans-serif",
  },
  card: {
    background: "white",
    borderRadius: "16px",
    border: "1px solid #dde3ed",
    padding: "56px 64px",
    maxWidth: "800px",
    width: "100%",
    boxShadow: "0 4px 24px rgba(10,22,40,0.08)",
    textAlign: "center",
  },
  logo: { fontSize: "3.5rem", marginBottom: "20px" },
  title: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "1.5rem",
    fontWeight: 600,
    color: "#0a1628",
    marginBottom: "12px",
    lineHeight: 1.4,
  },
  subtitle: {
    fontSize: "1rem",
    color: "#4a6080",
    lineHeight: 1.8,
    marginBottom: "0",
  },
  divider: {
    border: "none",
    borderTop: "1px solid #e0e8f4",
    margin: "36px 0",
  },
  guideBox: {
    background: "#f0f4fa",
    border: "1px solid #c5d8f0",
    borderRadius: "12px",
    padding: "24px 28px",
    textAlign: "left",
    marginBottom: "32px",
  },
  guideTitle: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "0.8rem",
    color: "#2e86de",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.07em",
    marginBottom: "8px",
  },
  guideDesc: {
    fontSize: "0.93rem",
    color: "#4a6080",
    lineHeight: 1.6,
    marginBottom: "14px",
  },
  downloadLink: {
    display: "inline-block",
    background: "#2e86de",
    color: "white",
    padding: "10px 20px",
    borderRadius: "8px",
    textDecoration: "none",
    fontSize: "0.9rem",
    fontWeight: 500,
  },
  startBtn: {
    background: "#2e86de",
    color: "white",
    border: "none",
    borderRadius: "10px",
    padding: "14px 40px",
    fontSize: "1rem",
    fontWeight: 600,
    cursor: "pointer",
    width: "100%",
    maxWidth: "320px",
    fontFamily: "'IBM Plex Sans', sans-serif",
  },
};
