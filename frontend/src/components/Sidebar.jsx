// src/components/Sidebar.jsx
export default function Sidebar({ blocks, currentIdx, blocksDone, metadata, missingCount, onNavigate, onReset }) {
  const filled = Object.values(metadata).filter(v => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0)).length;

  return (
    <aside style={styles.sidebar}>
      <p style={styles.title}>🏥 HealthDCAT-AP-ES</p>
      <hr style={styles.hr} />

      {/* Métricas */}
      <div style={styles.metricsRow}>
        <div style={styles.metricBox}>
          <p style={styles.metricNum}>{filled}</p>
          <p style={styles.metricLabel}>campos rellenos</p>
        </div>
        <div style={styles.metricBox}>
          <p style={{ ...styles.metricNum, color: "#e74c3c" }}>{missingCount}</p>
          <p style={styles.metricLabel}>obligatorios pendientes</p>
        </div>
      </div>

      <hr style={styles.hr} />
      <p style={styles.sectionLabel}>Bloques</p>

      {blocks.map((b, i) => {
        const done = blocksDone.includes(i);
        const active = i === currentIdx;
        const icon = done ? "✅" : active ? "▶️" : "○";
        return (
          <button key={i} style={{ ...styles.navBtn, ...(active ? styles.navBtnActive : {}) }}
            onClick={() => onNavigate(i)}>
            {icon} {b.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
          </button>
        );
      })}

      <hr style={styles.hr} />

      <a href="http://localhost:8000/guide" download style={styles.sideBtn}>📄 Guía de campos</a>

      <button style={{ ...styles.sideBtn, marginTop: "8px", cursor: "pointer", border: "1px solid #1e3a5f", background: "transparent", color: "#c8d8f0", width: "100%", textAlign: "left" }}
        onClick={onReset}>← Volver al inicio</button>
    </aside>
  );
}

const styles = {
  sidebar: { width: "260px", minHeight: "100vh", background: "#0a1628", borderRight: "2px solid #1e3a5f", padding: "20px 16px", display: "flex", flexDirection: "column", fontFamily: "'IBM Plex Sans', sans-serif", flexShrink: 0 },
  title: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "1rem", fontWeight: 600, color: "#c8d8f0", margin: "0 0 12px 0" },
  hr: { border: "none", borderTop: "1px solid #1e3a5f", margin: "12px 0" },
  metricsRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" },
  metricBox: { background: "#0f1f3d", border: "1px solid #1e3a5f", borderRadius: "8px", padding: "10px", textAlign: "center" },
  metricNum: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "1.4rem", fontWeight: 600, color: "#2e86de", margin: 0 },
  metricLabel: { fontSize: "0.7rem", color: "#8899aa", margin: "4px 0 0 0" },
  sectionLabel: { fontSize: "0.8rem", fontWeight: 600, color: "#8899aa", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px 0" },
  navBtn: { display: "block", width: "100%", textAlign: "left", background: "transparent", border: "none", color: "#c8d8f0", padding: "8px 10px", borderRadius: "6px", fontSize: "0.85rem", cursor: "pointer", marginBottom: "4px", fontFamily: "'IBM Plex Sans', sans-serif" },
  navBtnActive: { background: "#1e3a5f", color: "white" },
  sideBtn: { display: "block", background: "#1e3a5f", color: "#c8d8f0", padding: "10px 12px", borderRadius: "8px", fontSize: "0.85rem", textDecoration: "none", textAlign: "center" },
};
