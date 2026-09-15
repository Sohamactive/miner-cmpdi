// ---------------------------------------------------------------------------
// AI Query & Evidence Viewer
// ---------------------------------------------------------------------------

export type QueryStatus = "idle" | "connecting" | "streaming" | "done" | "error";

export interface QueryFilters {
  documentType: string;
  timeSpan: string;
}

export interface Citation {
  id: string;
  docId: string;
  label: string; // e.g. "Doc-CMPDI-NK-2018-p.42"
  page: number;
}

export interface ContextVector {
  id: string;
  docId: string;
  title: string;
  excerpt: string;
  matchPercent: number;
  embeddingId: string;
}

export interface EvidenceDocument {
  docId: string;
  title: string;
  confidence: number;
  totalPages: number;
  currentPage: number;
  excerpt: string;
  groundingSpans: { start: number; end: number }[];
  embeddingId: string;
  cosineSimilarity: number;
  signedBy: string;
  signedAt: string;
}

export interface BoreholeLog {
  id: string;
  name: string;
  depthMeters: number;
  seam: string;
  distanceKm: number;
}

export interface SeamRow {
  seam: string;
  thicknessM: number;
  depthM: number;
  quality: string;
}

/**
 * Discriminated union of every event the backend RAG/ML orchestrator can
 * push down the WebSocket while a query is being answered. The UI reduces
 * these into visible state as they arrive, so the "generation" is always a
 * live, incremental render rather than a single blocking response.
 */
export type QueryStreamEvent =
  | { type: "status"; stage: string }
  | { type: "token"; text: string }
  | { type: "vector"; vector: ContextVector }
  | { type: "citation"; citation: Citation }
  | { type: "evidence"; evidence: EvidenceDocument }
  | { type: "borehole"; logs: BoreholeLog[] }
  | { type: "seams"; rows: SeamRow[] }
  | { type: "done" }
  | { type: "error"; message: string };

// ---------------------------------------------------------------------------
// Topic Explorer & Clusters
// ---------------------------------------------------------------------------

export interface TopicDomain {
  id: string;
  label: string;
}

export interface Topic {
  id: string;
  title: string;
  domain: string;
  mentionCount: number;
  progress: number; // 0-100, coverage / confidence
  icon: string; // material symbol name
  summary: string;
}

export interface SecondaryTopic {
  id: string;
  label: string;
  icon: string;
  count: number;
}

export interface ClusterPoint {
  id: string;
  x: number;
  y: number;
  radius: number;
  topicId: string;
  label: string;
}

export interface ArchiveDoc {
  id: string;
  title: string;
  topicId: string;
  distance: number; // semantic distance score, lower = closer
  excerpt: string;
  date: string;
}
