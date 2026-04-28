// src/api/client.js
import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,  // ← envía y recibe cookies de sesión
});

export const getBlocks = () => API.get("/blocks");
export const getBlock = (id) => API.get(`/blocks/${id}`);
export const completeBlock = (blockId, userContext) =>
  API.post(`/complete/${blockId}`, { block_id: blockId, user_context: userContext });
export const saveManual = (blockId, partial) =>
  API.post("/save-manual", { block_id: blockId, partial });
export const getMetadata = () => API.get("/metadata");
export const validateMetadata = () => API.get("/validate");
export const getMissingFields = (blockId) => API.get(`/missing/${blockId}`);
export const finalizeMetadata = () => API.post("/finalize");
export const resetMetadata = () => API.post("/reset", { confirm: true });
export const getLlmStatus = () => API.get("/llm-status");