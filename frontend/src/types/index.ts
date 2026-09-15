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
  sidebarLabel: string;
}
