// src/components/Sidebar.jsx
export default function Sidebar({ blocks, currentIdx, blocksDone, metadata, missingCount, missingDetails, onNavigate, onReset }) {
  const filled = Object.values(metadata).filter(v => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0)).length;
  const totalBlocks = blocks.length || 1;
  const pct = Math.round((blocksDone.length / totalBlocks) * 100);

  // SVG ring calculations
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct / 100);

  return (
    <aside className="sidebar">
      <p className="sidebar-brand"><span className="sidebar-dot" /> Asistente de Metadatos</p>

      <hr className="sidebar-divider" />

      {/* Progress ring */}
      <p className="sidebar-section-label">Progreso</p>
      <div className="ring-wrap">
        <div className="ring">
          <svg width="84" height="84">
            <circle className="ring-bg" cx="42" cy="42" r={radius} />
            <circle
              className="ring-fg"
              cx="42" cy="42" r={radius}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="ring-label">{pct}%</div>
        </div>
        <span className="ring-text">{blocksDone.length} de {totalBlocks} bloques</span>
      </div>

      <hr className="sidebar-divider" />

      {/* Stats */}
      <p className="sidebar-section-label">Resumen</p>
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

      {/* Steps */}
      <p className="sidebar-section-label">Bloques</p>
      <div className="step-list">
        {blocks.map((b, i) => {
          const done = blocksDone.includes(i);
          const active = i === currentIdx;
          const cls = "step" + (active ? " step--active" : "") + (done ? " step--done" : "");
          return (
            <button key={i} className={cls} onClick={() => onNavigate(i)}>
              <span className="step-num">{done ? "✓" : i + 1}</span>
              <span className="step-name">{b.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</span>
            </button>
          );
        })}
      </div>

      {/* Missing fields detail */}
      {missingDetails && missingDetails.length > 0 && (
        <>
          <hr className="sidebar-divider" />
          <p className="sidebar-section-label">Campos pendientes</p>
          {missingDetails.map((item, i) => (
            <div key={i} className="sidebar-missing-card">
              <div className="sidebar-missing-name">{item.label}</div>
              <div className="sidebar-missing-desc">
                <strong>{item.label}</strong> · {item.descripcion}
              </div>
              {item.ejemplo && (
                <div className="sidebar-missing-example">Ej: {item.ejemplo}</div>
              )}
            </div>
          ))}
        </>
      )}

      <hr className="sidebar-divider" />

      {/* Actions */}
      <a href="/guide" target="_blank" rel="noreferrer" className="sidebar-btn">Guía de campos</a>
      <button className="sidebar-btn" onClick={onReset}>← Volver al inicio</button>
    </aside>
  );
}
