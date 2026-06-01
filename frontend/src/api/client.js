// src/api/client.js
import axios from "axios";

const isProduction = window.location.hostname !== "localhost";
const BASE_URL = isProduction ? "" : (import.meta.env.VITE_API_URL || "http://localhost:8000");

const API = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

export const getBlocks = () => API.get("/blocks");
export const getBlock = (id) => API.get(`/blocks/${id}`);
export const completeBlock = (blockId, userContext) =>
  API.post(`/complete/${blockId}`, { block_id: blockId, user_context: userContext });
export const saveManual = (blockId, partial) =>
  API.post("/save-manual", { block_id: blockId, partial });
// api/client.js
export async function importSessionMetadata(file, format = "json") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("format", format);   // ← añadir esto
  return axios.post(`${BASE_URL}/import-session`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    withCredentials: true,
  });
}
export const getMetadata = () => API.get("/metadata");
export const validateMetadata = () => API.get("/validate");
export const getMissingFields = (blockId) => API.get(`/missing/${blockId}`);
export const finalizeMetadata = () => API.post("/finalize");
export const resetMetadata = () => API.post("/reset", { confirm: true });
export const getLlmStatus = () => API.get("/llm-status");
export const getSchemaInfo = () => API.get("/schema-info");
// Exportar metadatos como RDF (fmt: "turtle" | "xml")
export async function exportRdf(fmt = "turtle") {
  const res = await fetch(`${BASE_URL}/export-rdf?fmt=${fmt}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Error al exportar RDF");
  const blob = await res.blob();
  const ext  = fmt === "xml" ? "rdf" : "ttl";
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `metadata.${ext}`;
  a.click();
  URL.revokeObjectURL(url);
}
