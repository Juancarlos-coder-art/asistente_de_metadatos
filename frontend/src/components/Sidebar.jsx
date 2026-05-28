import { useState } from "react";

const isProduction = window.location.hostname !== "localhost";
const guideUrl = isProduction ? "/guide" : "http://localhost:8000/guide";

const countFilledFields = (metadata) => {
  let count = 0;

  const SUBFIELDS = {
    hdab: ["name", "type", "contact", "email", "telephone", "opening_hours_description", "opening_hours_frequency", "special_opening_hours_description", "special_opening_hours_frequency"],
    contact: ["email", "url"],
    legal_basis: ["description", "source"],
    retention_period: ["start", "end"],
    coding_system: ["uri", "label"],
    publisher: ["name", "type", "contact_page", "email", "telephone", "opening_hours_description", "opening_hours_frequency", "special_opening_hours_description", "special_opening_hours_frequency"],
    creator: ["name", "email", "url", "type"],
    qualified_attribution: ["qualified_attribution_agent_name", "qualified_attribution_agent_type", "qualified_attribution_agent_contact_page", "qualified_attribution_agent_email", "qualified_attribution_role"],
    temporal_coverage: ["start", "end"],
    conforms_to: ["uri", "label"],
    related_resource: ["uri", "label"],
    documentation: ["uri", "label"],
  };

  for (const [key, val] of Object.entries(metadata)) {
    if (val === null || val === "" || (Array.isArray(val) && val.length === 0) || (typeof val === "object" && !Array.isArray(val) && Object.keys(val).length === 0)) continue;

    if (SUBFIELDS[key] && typeof val === "object" && !Array.isArray(val)) {
      const filled = SUBFIELDS[key].filter(sf => val[sf] && val[sf] !== "").length;
      count += filled;
    } else if (Array.isArray(val)) {
      count += val.length;
    } else {
      count += 1;
    }
  }

  return count;
};

export default function Sidebar({ blocks, currentIdx, blocksDone, metadata, missingCount, onNavigate, onReset }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const filled = countFilledFields(metadata); 

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
