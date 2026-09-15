/**
 * Base configuration for talking to the FastAPI + RAG orchestrator backend.
 *
 * Both URLs are overridable via Vite env vars so the same build can point at
 * a local backend during development and a deployed one in production:
 *   VITE_API_BASE_URL=http://localhost:8000
 *   VITE_WS_BASE_URL=ws://localhost:8000
 */

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

export const WS_BASE_URL: string =
  (import.meta.env.VITE_WS_BASE_URL as string | undefined) ??
  (API_BASE_URL.startsWith("https") ? "wss://localhost:8000" : "ws://localhost:8000");

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}
