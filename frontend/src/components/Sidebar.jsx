// src/components/Sidebar.jsx
import { useLang } from "../context/LanguageContext";
import { t } from "../i18n/translations";

export default function Sidebar({ blocks, currentIdx, blocksDone, metadata, missingCount, onNavigate, onReset }) {
  const { lang, toggle } = useLang();
  const tr = t[lang];

  const filled = Object.values(metadata).filter(v => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0)).length;

  const isProduction = window.location.hostname !== "localhost";
  const guideUrl = isProduction ? "/guide" : "http://localhost:8000/guide";

  return (
    <aside className="sidebar">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
        <p className="sidebar-title" style={{ margin: 0 }}>{tr.sidebarTitle}</p>
        <button
          onClick={toggle}
          style={{
            background: "none",
            border: "1px solid #4a4a4a",
            color: "#e0e0e0",
            padding: "3px 10px",
            fontSize: "0.75rem",
            fontFamily: "'IBM Plex Mono', monospace",
            cursor: "pointer",
            borderRadius: "2px",
            letterSpacing: "0.05em",
          }}
          title={lang === "es" ? "Switch to English" : "Cambiar a Español"}
        >
          {lang === "es" ? "EN" : "ES"}
        </button>
      </div>

      <div className="metrics-grid">
        <div className="metric-box">
          <span className="metric-num">{filled}</span>
          <span className="metric-label">{tr.sidebarFilledFields}</span>
        </div>
        <div className="metric-box">
          <span className={`metric-num ${missingCount > 0 ? "metric-num--error" : ""}`}>{missingCount}</span>
          <span className="metric-label">{tr.sidebarPending}</span>
        </div>
      </div>

      <hr className="sidebar-divider" />
      <p className="sidebar-section-label">{tr.sidebarBlocks}</p>

      {blocks.map((b, i) => {
        const done = blocksDone.includes(i);
        const active = i === currentIdx;
        const icon = done ? "✅" : active ? "▶" : "○";
        const blockName = lang === "en" && b.name_en
          ? b.name_en
          : b.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
        return (
          <button key={i} className={`nav-btn ${active ? "nav-btn--active" : ""}`} onClick={() => onNavigate(i)}>
            {icon} {blockName}
          </button>
        );
      })}

      <hr className="sidebar-divider" />
      <a href={guideUrl} download className="sidebar-btn">{tr.sidebarManual}</a>
      <button className="sidebar-btn" onClick={onReset}>{tr.sidebarBack}</button>
    </aside>
  );
}
