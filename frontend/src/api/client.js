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
export const getMetadata = () => API.get("/metadata");
export const validateMetadata = () => API.get("/validate");
export const getMissingFields = (blockId) => API.get(`/missing/${blockId}`);
export const finalizeMetadata = () => API.post("/finalize");
export const resetMetadata = () => API.post("/reset", { confirm: true });
export const getLlmStatus = () => API.get("/llm-status");
export const getSchemaInfo = (lang = "es") =>
  API.get(`/schema-info?lang=${lang}`);