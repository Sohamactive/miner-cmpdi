
// ============================================================
// M.I.N.E.R. TypeScript Types
// ============================================================

export interface KPIData {
  label: string;
  value: string;
  subtitle: string;
  trend?: string;
  trendPositive?: boolean;
  detail?: string;
  icon: string;
  iconColor?: string;
  valueColor?: string;
}

export interface PipelineStepData {
  step: string;
  title: string;
  subtitle: string;
  progress: number;
  status: 'complete' | 'active' | 'pending';
  icon: string;
}

export interface AssetBreakdownItem {
  label: string;
  value: number;
  percentage: number;
  color: string;
}

export interface GalleryCard {
  image: string;
  tag: string;
  badge: string;
  title: string;
  description: string;
  source: string;
  action: string;
}

export interface AuditRecord {
  title: string;
  recordId: string;
  department: string;
  format: string;
  formatBg?: string;
  classification: string;
  classificationBg?: string;
  classificationText?: string;
  ocrConfidence: number;
  confidenceColor?: string;
  ingestionDate: string;
}

export interface ReportSection {
  number: string;
  title: string;
  validationPercentage: number;
  validationStatus: 'high' | 'medium' | 'caution';
  content: string;
  provenances: string[];
  hasTable?: boolean;
  tableData?: SeamReserveRow[];
  hasMap?: boolean;
  hasImage?: boolean;
  imageUrl?: string;
  imageCaption?: string;
  riskCards?: RiskCard[];
}

export interface SeamReserveRow {
  seamId: string;
  meanThickness: string;
  proved: string;
  indicated: string;
  grossGCV: string;
  confidence: number;
  status: 'verified' | 'drill-audit' | 'pending';
}

export interface RiskCard {
  category: string;
  title: string;
  description: string;
  color: string;
}

export interface ReviewChecklist {
  label: string;
  description: string;
  checked: boolean;
  status?: 'success' | 'warning' | 'error';
}

export interface ApprovalAuditEntry {
  sessionId: string;
  signOffDate: string;
  officer: string;
  hash: string;
  status: 'approved' | 'modified' | 'dispatched';
}

export interface UserProfile {
  name: string;
  role: string;
  cilId: string;
  digitalRole: string;
  status: 'active' | 'inactive';
}

export interface ReportTemplate {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: string;
  estimatedTime: string;
}

export interface NavItem {
  path: string;
  label: string;
  icon: string;
}
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
