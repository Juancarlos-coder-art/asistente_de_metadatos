// src/pages/Welcome.jsx
import { useState } from "react";
import { getLlmStatus, resetMetadata } from "../api/client";
import { useLang } from "../context/LanguageContext";
import { t } from "../i18n/translations";




const isProduction = window.location.hostname !== "localhost";
const guideUrl = isProduction ? "/guide" : "http://localhost:8000/guide";

export default function Welcome({ onStart }) {
  const [loading, setLoading] = useState(false);
  const { lang, toggle } = useLang();  // ← añade toggle
  const tr = t[lang];

  const handleStart = async () => {
    setLoading(true);
    await resetMetadata().catch(() => {});
    await getLlmStatus().catch(() => {});
    setLoading(false);
    onStart();
  };

  return (
    <div className="welcome-container">
      <div className="welcome-card">

        {/* ← Toggle idioma */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "8px" }}>
          <button
            onClick={toggle}
            style={{
              background: "none",
              border: "1px solid #c6c6c6",
              color: "#525252",
              padding: "3px 10px",
              fontSize: "0.75rem",
              fontFamily: "'IBM Plex Mono', monospace",
              cursor: "pointer",
              borderRadius: "2px",
            }}
          >
            {lang === "es" ? "EN" : "ES"}
          </button>
        </div>

        <span className="welcome-logo"></span>
        <h1 className="welcome-title" style={{ whiteSpace: "pre-line" }}>
          {tr.welcomeTitle}
        </h1>
        <p className="welcome-subtitle">
          {tr.welcomeSubtitle}
        </p>

        <hr className="welcome-divider" />

        <div className="guide-box">
          <p className="guide-box-title">{tr.welcomeManualTitle}</p>
          <p className="guide-box-desc">{tr.welcomeManualDesc}</p>
          <a href={guideUrl} download className="btn btn--secondary btn--sm">
            {tr.welcomeManualBtn}
          </a>
        </div>

        <button
          className="btn btn--primary btn--full"
          onClick={handleStart}
          disabled={loading}
        >
          {loading ? tr.welcomeLoading : tr.welcomeStartBtn}
        </button>
      </div>
    </div>
  );
}
