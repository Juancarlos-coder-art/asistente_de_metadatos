// src/pages/Welcome.jsx
import { useState } from "react";
import { getLlmStatus, resetMetadata } from "../api/client";

export default function Welcome({ onStart }) {
  const [loading, setLoading] = useState(false);

const handleStart = async () => {
  setLoading(true);
  await resetMetadata().catch(() => {});  // ← limpia el estado al empezar
  await getLlmStatus().catch(() => {});
  setLoading(false);
  onStart();
};

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <span className="welcome-logo">🏥</span>
        <h1 className="welcome-title">
          Hola, soy el Asistente conversacional del ENDS.<br />
          Te ayudaré a metadatar tu conjunto de datos.
        </h1>
        <p className="welcome-subtitle">
          El proceso está dividido en bloques de preguntas.
          Puedes responder con tus propias palabras y la IA estructurará
          la información conforme al esquema <strong>HealthDCAT-AP-ES</strong>.
        </p>

        <hr className="welcome-divider" />

        <div className="guide-box">
          <p className="guide-box-title">📄 Guía de campos</p>
          <p className="guide-box-desc">
            Si quieres información sobre los campos que necesitamos
            para metadatar tu dataset, descarga aquí la guía completa.
          </p>
          <a href="http://localhost:8000/guide" download className="btn btn--secondary btn--sm">
            ⬇️ Descargar guía de campos (.docx)
          </a>
        </div>

        <button
          className="btn btn--primary btn--full"
          onClick={handleStart}
          disabled={loading}
        >
          {loading ? "Cargando..." : "🚀 Comenzar a metadatar"}
        </button>
      </div>
    </div>
  );
}
