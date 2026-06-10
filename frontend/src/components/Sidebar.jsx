import { useState } from "react";

const isProduction = window.location.hostname !== "localhost";
const guideUrl = isProduction ? "/guide" : "http://localhost:8000/guide";

const RING_RADIUS = 38;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

function ProgressRing({ filled, total, label, color }) {
  const pct = total > 0 ? filled / total : 0;
  const offset = RING_CIRCUMFERENCE * (1 - pct);
  return (
    <div className="ring-wrap">
      <div className="ring">
        <svg width="88" height="88" viewBox="0 0 88 88">
          <circle className="ring-bg" cx="44" cy="44" r={RING_RADIUS} />
          <circle
            className="ring-fg"
            cx="44"
            cy="44"
            r={RING_RADIUS}
            style={{
              stroke: color,
              strokeDasharray: RING_CIRCUMFERENCE,
              strokeDashoffset: offset,
            }}
          />
        </svg>
        <div className="ring-label">{filled}/{total}</div>
      </div>
      <span className="ring-text">{label}</span>
    </div>
  );
}

export default function Sidebar({
  blocks,
  currentIdx,
  blocksDone,
  progress,
  onNavigate,
  onReset,
  onSaveProgress
}) {

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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

      <div className="rings-row">
        <ProgressRing
          filled={progress.filled_optional}
          total={progress.total_optional}
          label="Opcionales"
          color="#78a9ff"
        />
        <ProgressRing
          filled={progress.filled_required}
          total={progress.total_required}
          label="Obligatorios"
          color="#ff8389"
        />
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
      <button className="sidebar-btn" onClick={onSaveProgress}>Guardar progreso</button>
      <button className="sidebar-btn" onClick={onReset}>← Volver al inicio</button>
    </aside>
  );
}
