import { useState } from "react";

const isProduction = window.location.hostname !== "localhost";
const guideUrl = isProduction ? "/guide" : "http://localhost:8000/guide";

export default function Sidebar({
  blocks,
  currentIdx,
  blocksDone,
  metadata,
  missingCount,
  onNavigate,
  onReset
}) {

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const filled = Object.values(metadata).filter(
    v =>
      v !== null &&
      v !== "" &&
      !(Array.isArray(v) && v.length === 0)
  ).length;

  return (
    <aside className={`sidebar ${sidebarCollapsed ? "sidebar--collapsed" : ""}`}>

      <button
        className="sidebar-toggle"
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        title={sidebarCollapsed ? "Expandir menú" : "Contraer menú"}
      >
        {sidebarCollapsed ? "›" : "‹"}
      </button>
      <p className="sidebar-title">HealthDCAT-AP</p>

      <div className="metrics-grid">
        <div className="metric-box">
          <span className="metric-num">{filled}</span>
          <span className="metric-label">campos rellenos</span>
        </div>
        <div className="metric-box">
          <span className={`metric-num ${missingCount > 0 ? "metric-num--error" : ""}`}>{missingCount}</span>
          <span className="metric-label">obligatorios pendientes</span>
        </div>
      </div>

      <hr className="sidebar-divider" />
      <p className="sidebar-section-label">Bloques</p>

      {blocks.map((b, i) => {
        const done = blocksDone.includes(i);
        const active = i === currentIdx;
        const icon = done ? "✅" : active ? "▶" : "○";
        return (
          <button key={i} className={`nav-btn ${active ? "nav-btn--active" : ""}`} onClick={() => onNavigate(i)}>
            <span className="nav-icon">{icon}</span>
            <span className="nav-text">
              {b.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
            </span>
          </button>
        );
      })}

      <hr className="sidebar-divider" />
      <a href={guideUrl} download className="sidebar-btn">Manual de usuario</a>
      <button className="sidebar-btn" onClick={onReset}>← Volver al inicio</button>
    </aside>
  );
}
