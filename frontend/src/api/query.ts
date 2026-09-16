import { WS_BASE_URL } from "./client";
import type { QueryFilters } from "../types";

export interface QueryRequestPayload {
  query: string;
  filters: QueryFilters;
}

/** Endpoint the RAG orchestrator listens on for streamed query generation. */
export function buildQuerySocketUrl(): string {
  return `${WS_BASE_URL}/ws/query`;
}

export function toRequestPayload(query: string, filters: QueryFilters): string {
  return JSON.stringify({ type: "query", ...({ query, filters } as QueryRequestPayload) });
}
