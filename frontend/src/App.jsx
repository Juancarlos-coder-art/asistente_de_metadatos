// src/App.jsx
import { useState, useEffect } from "react";
import Welcome from "./pages/Welcome";
import BlockForm from "./pages/BlockForm";
import Sidebar from "./components/Sidebar";
import { getBlocks, getMetadata, validateMetadata, resetMetadata } from "./api/client";

export default function App() {
  const [started, setStarted] = useState(false);
  const [blocks, setBlocks] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [blocksDone, setBlocksDone] = useState([]);
  const [metadata, setMetadata] = useState({});
  const [missingCount, setMissingCount] = useState(0);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    getBlocks().then(res => setBlocks(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (started) {
      getMetadata().then(res => setMetadata(res.data)).catch(() => {});
      validateMetadata().then(res => setMissingCount(res.data.missing_required.length)).catch(() => {});
    }
  }, [started, currentIdx]);

  const handleStart = () => setStarted(true);

  const handleNext = () => {
    if (currentIdx < blocks.length - 1) setCurrentIdx(currentIdx + 1);
  };

  const handlePrev = () => {
    if (currentIdx > 0) setCurrentIdx(currentIdx - 1);
  };

  const handleBlockDone = (idx) => {
    if (!blocksDone.includes(idx)) setBlocksDone([...blocksDone, idx]);
    getMetadata().then(res => setMetadata(res.data)).catch(() => {});
    validateMetadata().then(res => setMissingCount(res.data.missing_required.length)).catch(() => {});
  };

  const handleFinish = () => setFinished(true);

  const handleReset = async () => {
    await resetMetadata().catch(() => {});
    setStarted(false);
    setCurrentIdx(0);
    setBlocksDone([]);
    setMetadata({});
    setFinished(false);
  };

  // Pantalla final
  if (finished) {
    return (
      <div style={styles.finishContainer}>
        <div style={styles.finishCard}>
          <div style={{ fontSize: "4rem" }}>🎉</div>
          <h1 style={styles.finishTitle}>¡Metadatos completados!</h1>
          <p style={styles.finishDesc}>El archivo <strong>metadata_output.json</strong> ha sido guardado correctamente.</p>
          <pre style={styles.finishJson}>{JSON.stringify(metadata, null, 2)}</pre>
          <button style={styles.btnPrimary} onClick={handleReset}>Empezar de nuevo</button>
        </div>
      </div>
    );
  }

  // Bienvenida
  if (!started) return <Welcome onStart={handleStart} />;

  // App principal
  return (
    <div style={styles.layout}>
      <Sidebar
        blocks={blocks}
        currentIdx={currentIdx}
        blocksDone={blocksDone}
        metadata={metadata}
        missingCount={missingCount}
        onNavigate={(i) => { setCurrentIdx(i); }}
        onReset={handleReset}
      />
      <main style={styles.main}>
        {/* Cabecera */}
        <div style={styles.header}>
          <h1 style={styles.mainTitle}>Asistente de Metadatos HealthDCAT-AP</h1>
          <p style={styles.mainSubtitle}>Esquema sanitario europeo · Bloque {currentIdx + 1} de {blocks.length}</p>
        </div>

        {/* Barra de progreso */}
        <div style={styles.progressBar}>
          <div style={{ ...styles.progressFill, width: `${((currentIdx + 1) / blocks.length) * 100}%` }} />
        </div>

        {blocks.length > 0 && (
          <BlockForm
            blocks={blocks}
            currentIdx={currentIdx}
            onNext={handleNext}
            onPrev={handlePrev}
            onFinish={handleFinish}
            onBlockDone={handleBlockDone}
          />
        )}
      </main>
    </div>
  );
}

const styles = {
  layout: { display: "flex", minHeight: "100vh", fontFamily: "'IBM Plex Sans', sans-serif" },
  main: { flex: 1, padding: "32px 40px", background: "#f4f6f9", overflowY: "auto" },
  header: { marginBottom: "8px" },
  mainTitle: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "1.6rem", fontWeight: 600, color: "#0a1628", borderLeft: "4px solid #2e86de", paddingLeft: "16px", margin: "0 0 4px 0" },
  mainSubtitle: { fontSize: "0.9rem", color: "#6b7f99", fontFamily: "'IBM Plex Mono', monospace", marginLeft: "20px" },
  progressBar: { height: "6px", background: "#dde3ed", borderRadius: "4px", margin: "16px 0 24px 0" },
  progressFill: { height: "100%", background: "#2e86de", borderRadius: "4px", transition: "width 0.3s ease" },
  finishContainer: { minHeight: "100vh", background: "#f4f6f9", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" },
  finishCard: { background: "white", borderRadius: "16px", border: "1px solid #dde3ed", padding: "48px", maxWidth: "700px", width: "100%", textAlign: "center", boxShadow: "0 4px 24px rgba(10,22,40,0.08)" },
  finishTitle: { fontFamily: "'IBM Plex Mono', monospace", fontSize: "1.8rem", color: "#0a1628", marginBottom: "12px" },
  finishDesc: { fontSize: "1rem", color: "#4a6080", marginBottom: "24px" },
  finishJson: { background: "#0a1628", color: "#7ecbff", borderRadius: "10px", padding: "16px", fontSize: "0.8rem", textAlign: "left", maxHeight: "300px", overflowY: "auto", marginBottom: "24px" },
  btnPrimary: { background: "#2e86de", color: "white", border: "none", borderRadius: "8px", padding: "12px 32px", fontSize: "1rem", fontWeight: 600, cursor: "pointer" },
};
