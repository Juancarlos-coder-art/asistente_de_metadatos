// src/App.jsx
import { useState, useEffect } from "react";
import Welcome from "./pages/Welcome";
import BlockForm from "./pages/BlockForm";
import Sidebar from "./components/Sidebar";
import { getBlocks, getMetadata, validateMetadata, getMissingFields, resetMetadata } from "./api/client";
import DocumentUploadModal from "./components/DocumentUploadModal";
import LegislationSelector from "./components/LegislationSelector";

export default function App() {
  const [started, setStarted] = useState(false);
  const [blocks, setBlocks] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [blocksDone, setBlocksDone] = useState([]);
  const [metadata, setMetadata] = useState({});
  const [missingCount, setMissingCount] = useState(0);
  const [missingDetails, setMissingDetails] = useState([]);
  const [finished, setFinished] = useState(false);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [documentResults, setDocumentResults] = useState(null);
  const [skipNextMetadataFetch, setSkipNextMetadataFetch] = useState(false);

  useEffect(() => {
    getBlocks().then(res => setBlocks(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (started) {
      if (skipNextMetadataFetch) {
        setSkipNextMetadataFetch(false);
      } else {
        getMetadata().then(res => setMetadata(res.data)).catch(() => {});
      }
      validateMetadata().then(res => setMissingCount(res.data.missing_required.length)).catch(() => {});
      getMissingFields(currentIdx).then(res => setMissingDetails(res.data.descriptions || [])).catch(() => setMissingDetails([]));
    }
  }, [started, currentIdx]);

  const handleStart = () => setStarted(true);

  const handleNext = () => {
    if (currentIdx === 0 && !documentResults) {
      setShowDocumentModal(true);
      return;
    }
    if (currentIdx < blocks.length - 1) setCurrentIdx(currentIdx + 1);
  };

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
    setDocumentResults(null);
  };

  const handleDocumentSuccess = (data) => {
    setDocumentResults(data.results_by_block);
    setMetadata(data.metadata);
    setShowDocumentModal(false);
    setSkipNextMetadataFetch(true);
    const done = [];
    blocks.forEach((b, i) => {
      const result = data.results_by_block[b.name];
      if (result && result.filled > 0) done.push(i);
    });
    setBlocksDone(prev => [...new Set([...prev, ...done])]);
    setCurrentIdx(1);
  };
  // ── Pantalla final ──
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
          <p className="finish-desc">
            Revisa la legislación aplicable y descarga el JSON final.
          </p>
          <LegislationSelector
            onSave={(leg) => setMetadata(prev => ({ ...prev, applicable_legislation: leg }))}
          />
          <pre className="finish-json" style={{ marginTop: "24px" }}>
            {JSON.stringify(metadata, null, 2)}
          </pre>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center", marginTop: "16px" }}>
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
      {showDocumentModal && (
        <DocumentUploadModal
          onClose={() => setShowDocumentModal(false)}
          onSkip={() => {
            setShowDocumentModal(false);
            setCurrentIdx(1);
          }}
          onSuccess={handleDocumentSuccess}
        />
      )}
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
