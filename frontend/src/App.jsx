// src/App.jsx
import { useState, useEffect } from "react";
import Welcome from "./pages/Welcome";
import BlockForm from "./pages/BlockForm";
import Sidebar from "./components/Sidebar";
import { getBlocks, getMetadata, validateMetadata, getMissingFields, resetMetadata } from "./api/client";

export default function App() {
  const [started, setStarted] = useState(false);
  const [blocks, setBlocks] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [blocksDone, setBlocksDone] = useState([]);
  const [metadata, setMetadata] = useState({});
  const [missingCount, setMissingCount] = useState(0);
  const [missingDetails, setMissingDetails] = useState([]);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    getBlocks().then(res => setBlocks(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (started) {
      getMetadata().then(res => setMetadata(res.data)).catch(() => {});
      validateMetadata().then(res => setMissingCount(res.data.missing_required.length)).catch(() => {});
      getMissingFields(currentIdx).then(res => setMissingDetails(res.data.descriptions || [])).catch(() => setMissingDetails([]));
    }
  }, [started, currentIdx]);

  const handleStart = () => setStarted(true);
  const handleNext = () => { if (currentIdx < blocks.length - 1) setCurrentIdx(currentIdx + 1); };
  const handlePrev = () => { if (currentIdx > 0) setCurrentIdx(currentIdx - 1); };

  const handleBlockDone = (idx) => {
    if (!blocksDone.includes(idx)) setBlocksDone([...blocksDone, idx]);
    getMetadata().then(res => setMetadata(res.data)).catch(() => {});
    validateMetadata().then(res => setMissingCount(res.data.missing_required.length)).catch(() => {});
    getMissingFields(currentIdx).then(res => setMissingDetails(res.data.descriptions || [])).catch(() => setMissingDetails([]));
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
    const handleDownloadJSON = () => {
      const blob = new Blob([JSON.stringify(metadata, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "metadata_output.json";
      a.click();
      URL.revokeObjectURL(url);
    };

    return (
      <div className="finish-container">
        <div className="finish-card">
          <div style={{ fontSize: "3rem" }}>✅</div>
          <h1 className="finish-title">Metadatos completados</h1>
          <p className="finish-desc">El archivo <strong>metadata_output.json</strong> ha sido guardado correctamente.</p>
          <pre className="finish-json">{JSON.stringify(metadata, null, 2)}</pre>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            <button className="btn btn--primary" onClick={handleDownloadJSON}>⬇ Descargar JSON</button>
            <button className="btn btn--secondary" onClick={handleReset}>Empezar de nuevo</button>
          </div>
        </div>
      </div>
    );
  }

  if (!started) return <Welcome onStart={handleStart} />;

  return (
    <div className="app-layout">
      <Sidebar
        blocks={blocks}
        currentIdx={currentIdx}
        blocksDone={blocksDone}
        metadata={metadata}
        missingCount={missingCount}
        missingDetails={missingDetails}
        onNavigate={(i) => setCurrentIdx(i)}
        onReset={handleReset}
      />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Asistente de Metadatos HealthDCAT-AP</h1>
          <p className="page-subtitle">Esquema sanitario europeo · Bloque {currentIdx + 1} de {blocks.length}</p>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${((currentIdx + 1) / blocks.length) * 100}%` }} />
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
