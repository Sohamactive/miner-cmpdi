import type {
  KPIData, PipelineStepData, AssetBreakdownItem, GalleryCard,
  AuditRecord, ReportSection, SeamReserveRow, ReviewChecklist,
  ApprovalAuditEntry, UserProfile, ReportTemplate, NavItem,
  ArchiveDoc, BoreholeLog, ClusterPoint, ContextVector,
  EvidenceDocument, QueryStreamEvent, SeamRow, SecondaryTopic,
  Topic, TopicDomain,
} from '@/types';

// ── Navigation ──
export const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard & Ingestion', icon: 'dashboard', sidebarLabel: 'Dashboard Overview' },
  { path: '/ai-query', label: 'AI Query & Evidence Viewer', icon: 'psychology', sidebarLabel: 'AI Neural Query' },
  { path: '/topics', label: 'Topic Explorer & Clusters', icon: 'hub', sidebarLabel: 'Topic Clusters' },
  { path: '/review-approval', label: 'Human Review & Approval', icon: 'fact_check', sidebarLabel: 'Audit & Review' },
  { path: '/reports', label: 'Report Synthesis & Export', icon: 'summarize', sidebarLabel: 'Synthesis Engine' },
];

// ── Dashboard KPIs ──
export const kpiData: KPIData[] = [
  {
    label: 'Archival Footprint', value: '48,290', subtitle: 'Ingested Mining Records',
    trend: '+342 this week', trendPositive: true, detail: '7 Regional Institutes',
    icon: 'folder_special', iconColor: 'text-outline',
  },
  {
    label: 'Neural Index', value: '1.42M', subtitle: 'Qdrant Vector Embeddings',
    trend: 'text-embedding-004', detail: '1536 dims',
    icon: 'hub', iconColor: 'text-secondary',
  },
  {
    label: 'Optical Accuracy', value: '99.4%', subtitle: 'OCR Success Rate',
    detail: '1890-2024 Maps', trend: 'Surya + Tesseract Engine',
    icon: 'document_scanner', iconColor: 'text-outline',
  },
  {
    label: 'Governance Queue', value: '14', subtitle: 'Pending Officer Validations',
    trend: '4 High-Priority Seams', trendPositive: false, detail: 'SLA < 24h',
    icon: 'assignment_turned_in', iconColor: 'text-secondary', valueColor: 'text-secondary',
  },
];

// ── Pipeline Steps ──
export const pipelineSteps: PipelineStepData[] = [
  { step: '01', title: 'Doc Parser', subtitle: 'PyMuPDF, Unstructured', progress: 100, status: 'complete', icon: 'check_circle' },
  { step: '02', title: 'OCR Engine', subtitle: 'Tesseract / Surya OCR', progress: 96, status: 'complete', icon: 'check_circle' },
  { step: '03', title: 'Normalization', subtitle: 'Stratum Table Cleanse', progress: 88, status: 'complete', icon: 'check_circle' },
  { step: '04', title: 'Classification', subtitle: 'CMPDI Coal Taxonomy', progress: 72, status: 'active', icon: 'sync' },
  { step: '05', title: 'Semantic Chunk', subtitle: '512 token boundary', progress: 45, status: 'pending', icon: 'hourglass_top' },
  { step: '06', title: 'Qdrant Sync', subtitle: 'HNSW Indexed Vectors', progress: 30, status: 'pending', icon: 'pending' },
];

// ── Asset Breakdown ──
export const assetBreakdown: AssetBreakdownItem[] = [
  { label: 'Exploration PDFs', value: 22213, percentage: 46, color: 'bg-primary-container' },
  { label: 'Historical Scanned Maps / Blueprints', value: 13521, percentage: 28, color: 'bg-secondary' },
  { label: 'Borehole Logs & Stratum (XLSX)', value: 7726, percentage: 16, color: 'bg-on-tertiary-container' },
  { label: 'Feasibility & Legal Directives (DOCX)', value: 4830, percentage: 10, color: 'bg-outline' },
];

// ── Gallery Cards ──
export const galleryCards: GalleryCard[] = [
  {
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBHxnnwzRpa_NWtrS0hINPfuIY1LLdifdPp21e3B3ZTnqfG0AMjTWLkfULrnl5Hr38VrzUpPqiI9Di0nkeKb-OYjI3AA_Ak50irUHZ9ucLKLVxj037Yep5xePyU7s-aQen4gJAiUOERNyVUS0wbGaPBHe1XBhuNZ0Snlyh7t8uNqK5EDcAXNkTIDJluDFUqEnQ-qge-rNAUk170NJtOZuVcKn8DUAaIJDPMZrIpGxI8YJmczN_yRk6o',
    tag: 'Scanned Map 1984', badge: '400 DPI Tiff',
    title: 'Jharia Basin Structural Seam X-B',
    description: 'Multi-spectral geo-rectified layer showing historical extraction fault lines and overburden ratio.',
    source: 'CMPDI RI-II Dhanbad', action: 'View Vector Layers',
  },
  {
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuABnzEn6HtQnx624nAV1YSA_5KeGRLxfsdYDriuwBMvGhNZwBj3KHXiteZh-wY8uvlqIDhTSLvsio9fcIu2acvjIykMB82ozgnN74GnSCBE3MGDVZ10SyOKbP8R4E0GBRri1ZJCmd6DEzGKYzrVoYlzjb-wso99GQTGv_6VbsK-Sh3iUtcUMYENzLfdPADfbk_QjzjmjmssrLAKNLGPs1_JtzTugrEC7bQ0UObdn_1mv26RG4mkHEn1',
    tag: 'Core Sample Lab', badge: 'Borehole #BH-409',
    title: 'Petrographic Reflectance Matrix',
    description: 'Vitrinite analysis confirming coking propensity of sub-surface coal seams in Raniganj Coalfield.',
    source: 'CMPDI RI-I Asansol', action: 'View Lab Certificate',
  },
  {
    image: '',
    tag: 'Field Telemetry', badge: 'Lat 23.3441° N',
    title: 'Gondwana Basin Exploration Grid',
    description: 'Active acoustic sounding stations feeding automated ingestion vectors directly into Qdrant index clusters.',
    source: 'HQ Exploration Division', action: 'Explore Station Data',
  },
];

// ── Audit Registry ──
export const auditRecords: AuditRecord[] = [
  {
    title: 'Jharia Coalfield Stratum & Fault Line Survey (1984)',
    recordId: 'DOC-CMPDI-RI2-1984-7492', department: 'CMPDI RI-II Dhanbad',
    format: 'TIFF / PDF', classification: 'Geological Feasibility',
    ocrConfidence: 99.8, ingestionDate: '12 Oct 2025 • 09:41',
  },
  {
    title: 'North Karanpura Super Thermal Overburden Assessment',
    recordId: 'DOC-CMPDI-HQ-2023-1184', department: 'CMPDI HQ Ranchi (Planning)',
    format: 'DOCX / PDF', classification: 'Environmental Clearance',
    classificationBg: 'bg-secondary-fixed', classificationText: 'text-on-secondary-fixed',
    ocrConfidence: 98.2, ingestionDate: '12 Oct 2025 • 08:15',
  },
  {
    title: 'Singrauli Coalfield Methane Gas Emission Monitoring',
    recordId: 'DOC-CMPDI-RI6-2024-9032', department: 'CMPDI RI-VI Singrauli',
    format: 'XLSX TABULAR', classification: 'Mine Safety Compliance',
    ocrConfidence: 99.9, ingestionDate: '11 Oct 2025 • 22:30',
  },
  {
    title: 'Talcher Deep Underground Seam Sealing Manual & Core Drill',
    recordId: 'DOC-CMPDI-RI7-2022-4411', department: 'CMPDI RI-VII Bhubaneswar',
    format: 'PDF / CAD', classification: 'Geological Feasibility',
    ocrConfidence: 94.1, confidenceColor: 'text-secondary', ingestionDate: '11 Oct 2025 • 19:10',
  },
  {
    title: 'Wardha Valley Open Cast Mine Soil Hydrology Impact',
    recordId: 'DOC-CMPDI-RI4-2025-0109', department: 'CMPDI RI-IV Nagpur',
    format: 'SCANNED REPORT', classification: 'Environmental Clearance',
    classificationBg: 'bg-secondary-fixed', classificationText: 'text-on-secondary-fixed',
    ocrConfidence: 99.1, ingestionDate: '10 Oct 2025 • 16:44',
  },
];

// ── Review Page: Seam Reserve Table ──
export const seamReserveData: SeamReserveRow[] = [
  { seamId: 'Seam-II (Top)', meanThickness: '18.4 m', proved: '142.80', indicated: '28.40', grossGCV: '3,850 –\n4,100', confidence: 97, status: 'verified' },
  { seamId: 'Seam-III (Bottom)', meanThickness: '24.1 m', proved: '265.18', indicated: '62.15', grossGCV: '3,400 –\n3,750', confidence: 95, status: 'verified' },
  { seamId: 'Jagannath Split', meanThickness: '9.6 m', proved: '78.40', indicated: '19.00', grossGCV: '4,200 –\n4,450', confidence: 88, status: 'drill-audit' },
];

// ── Review Page: Report Sections ──
export const reportSections: ReportSection[] = [
  {
    number: '01', title: 'Executive Summary & Strategic Mandate',
    validationPercentage: 99.2, validationStatus: 'high',
    content: `The Talcher Coalfield, situated in the Brahmani River Valley, represents one of India's most vital energy resource basins, hosting in excess of 51 Billion Tonnes of thermal-grade Gondwana coal deposits. Under the CMPDI 2025-2030 Phase IV Mechanization Framework, this synthesis reconciles 42 legacy borehole logs with recent high-resolution 3D reflection seismic surveys executed by Regional Institute-VII. The proposed western flank extraction aims to unlock a net extraction increment of 22.4 MTPA while maintaining structural stability against the regional Barakar-Karharbari non-conformity.`,
    provenances: ['CMPDI-RI7-2023-GEO-LOG-89', 'MCL-DGMS-SAFETY-2024-V6.PDF', 'CIL-HDC-STRAT-PLAN-2030'],
  },
  {
    number: '02', title: 'Geological Reserves & Lithological Modeling',
    validationPercentage: 97.8, validationStatus: 'high',
    content: `Through computerized inverse distance weighting and Kriging volumetric synthesis applied to Boreholes CMPDI/TL-401 through 438, reserve classifications are apportioned under standard ISP (Indian Standard Procedure) codes as depicted below:`,
    provenances: ['BOREHOLE-DATASET-TL-401-438.XLSX', 'SURPAC-3D-RESERVE-MODEL-V7'],
    hasTable: true, tableData: seamReserveData,
  },
  {
    number: '03', title: 'Seam Gradient, Tectonic Faulting & Slope Stability',
    validationPercentage: 96.4, validationStatus: 'high',
    content: `The regional dip traverses between 4° to 7° towards N 12° E. Structurally, two strike-slip normal faults (Fault F-14 with throw 56m south; Fault F-18 with throw 45m north) intersect block coordinates 85°04'30"E / 20°57'15"N. Geomechanical rock mass rating (RMR) for the sandstone roof averages 62 (Class II–Good/Fair), supporting dragline benchmark operations up to 35m overburden benches without requiring statutory pilot prestressing.`,
    provenances: ['CMPDI-FAULT-SURVEY-TALCHER-2024', 'RMR-GEOMECH-LAB-TESTS-VOL1'],
    hasImage: true, imageCaption: 'Fig 3.1: Dip Fault Cross-Section',
  },
  {
    number: '04', title: 'Environmental Demarcation & Forest Clearance Review',
    validationPercentage: 91.2, validationStatus: 'caution',
    content: `The planned Western cut infringes on 312.45 hectares of Reserved Forest Land under Angul Forest Division. Total required compensatory afforestation has been matched to 625 hectares in non-forest patches within Athgarh subdivision. Proximity to Nandira Nullah mandates a mandatory 150-meter sterile riparian buffer, strictly prohibiting overburden bench dumping beyond Rs. 180m.`,
    provenances: ['MOEFCC-CLEARANCE-00-2023-99', 'NANDIRA-RIPARIAN-BUFFER-CMPDI-87'],
    hasMap: true,
  },
  {
    number: '05', title: 'Predictive Operational & Regulatory Risk Matrix',
    validationPercentage: 98.6, validationStatus: 'high',
    content: '',
    provenances: [],
    riskCards: [
      { category: 'SPONTANEOUS COMBUSTION RISK', title: 'Category II (Medium)', description: 'Crossing point temp: 154°C. Requires quarterly thermal imaging of stock piles.', color: 'bg-secondary-fixed' },
      { category: 'AQUIFER HAZARD RATING', title: 'Low Residual', description: 'Pumping capacity of 12,000 GPM deemed adequate during monsoon peaks.', color: 'bg-surface-container-high' },
      { category: 'DGMS STATUTORY AUDIT', title: 'Fully Compliant', description: 'Haul road gradient maintained at 1 in 16 max, complying with Circular No. 8 of 2021.', color: 'bg-surface-container-high' },
    ],
  },
];

// ── Review Checklist ──
export const reviewChecklist: ReviewChecklist[] = [
  { label: 'DGMS Compliance Parameters Verified', description: 'Bench height to width ratio (1:1.5) meets Coal Mines Regulation (CMR) 2017.', checked: true, status: 'success' },
  { label: 'Seam Reserve Volumetrics Cross-Checked', description: 'Reconciled with 42 physical drill core borehole register folios at RI-VII.', checked: true, status: 'success' },
  { label: 'Forest Clearance Coordinates Authenticated', description: 'Pending: DGPS pillar boundary matches Angul Forest Cadastral Survey.', checked: false, status: 'warning' },
];

// ── Approval Audit Trail ──
export const approvalAudit: ApprovalAuditEntry[] = [
  { sessionId: 'TLR-2024-01', signOffDate: '24/02/2025 16:28', officer: 'Dr.R.Sharma', hash: '8x7f238u9...', status: 'modified' },
  { sessionId: 'JHAR-2024-CQ', signOffDate: '19/02/2025 11:04', officer: 'Er.V.Kumar', hash: '8x994ac1b...', status: 'modified' },
  { sessionId: 'KORBA-EXP-04', signOffDate: '11/02/2025 09:45', officer: 'Er.S.Mukherjee', hash: '8x344cff2...', status: 'dispatched' },
];

// ── User Profile ──
export const currentUser: UserProfile = {
  name: 'Er. R. K. Sharma',
  role: 'Chief Manager (Geology & Planning)',
  cilId: 'CIL-T082491',
  digitalRole: 'Principal Geologist',
  status: 'active',
};

// ── Report Templates ──
export const reportTemplates: ReportTemplate[] = [
  { id: 'geo-feasibility', title: 'Geological Feasibility Report', description: 'Comprehensive geo-technical analysis with seam characterization, reserve estimation, and stripping ratio computation.', icon: 'terrain', category: 'Geological', estimatedTime: '~15 min' },
  { id: 'env-compliance', title: 'Environmental Compliance Report', description: 'Forest clearance status, compensatory afforestation, riparian buffer analysis, and MOEFCC compliance verification.', icon: 'eco', category: 'Environment', estimatedTime: '~12 min' },
  { id: 'safety-audit', title: 'Mine Safety Audit Report', description: 'DGMS compliance, spontaneous combustion risk, slope stability, and statutory regulatory adherence matrix.', icon: 'health_and_safety', category: 'Safety', estimatedTime: '~10 min' },
  { id: 'comprehensive', title: 'Comprehensive Synthesis Report', description: 'Full geo-technical synthesis combining geological, environmental, safety, and operational parameters for expansion planning.', icon: 'auto_awesome', category: 'Synthesis', estimatedTime: '~25 min' },
];

// ---------------------------------------------------------------------------
// AI Query & Evidence Viewer — mock evidence + a scripted event timeline used
// to simulate the backend's WebSocket stream when no live orchestrator is
// reachable at VITE_WS_URL.
// ---------------------------------------------------------------------------

export const MOCK_EVIDENCE: EvidenceDocument = {
  docId: "DOC-CMPDI-NK-2018-042",
  title: "Talcher Coalfield — North Karanpura Exploration Report",
  confidence: 0.94,
  totalPages: 118,
  currentPage: 42,
  excerpt:
    "The seam exhibits a mean thickness of 4.6m across the surveyed block, with overburden ratios consistent with prior 2016 drilling campaigns. Sulphur content remains within permissible limits for grade-B classification.",
  groundingSpans: [{ start: 14, end: 96 }],
  embeddingId: "vec-9f21-4482-b0c7",
  cosineSimilarity: 0.912,
  signedBy: "CMPDI Digital Archive Authority",
  signedAt: "2025-11-03T09:14:00+05:30",
};

export const MOCK_CONTEXT_VECTORS: ContextVector[] = [
  {
    id: "ctx-1",
    docId: "DOC-CMPDI-NK-2018-042",
    title: "North Karanpura Exploration Report, p.42",
    excerpt: "Seam thickness averages 4.6m with stable overburden ratio.",
    matchPercent: 91,
    embeddingId: "vec-9f21-4482-b0c7",
  },
  {
    id: "ctx-2",
    docId: "DOC-CMPDI-NK-2016-018",
    title: "North Karanpura Drilling Campaign 2016, p.11",
    excerpt: "Prior drilling confirms consistent seam geometry along strike.",
    matchPercent: 84,
    embeddingId: "vec-7a10-2c9e-11ab",
  },
  {
    id: "ctx-3",
    docId: "DOC-CMPDI-ENV-2019-007",
    title: "Environmental Demarcation Survey, p.6",
    excerpt: "Forest clearance boundary sits 1.8km from the proposed block.",
    matchPercent: 76,
    embeddingId: "vec-4b8d-99f1-6e02",
  },
];

export const MOCK_BOREHOLE_LOGS: BoreholeLog[] = [
  { id: "bh-14", name: "BH-14", depthMeters: 212, seam: "Seam VI", distanceKm: 0.4 },
  { id: "bh-22", name: "BH-22", depthMeters: 198, seam: "Seam VI", distanceKm: 0.9 },
  { id: "bh-31", name: "BH-31", depthMeters: 226, seam: "Seam V", distanceKm: 1.6 },
];

export const MOCK_SEAM_ROWS: SeamRow[] = [
  { seam: "Seam VI", thicknessM: 4.6, depthM: 212, quality: "Grade B" },
  { seam: "Seam V", thicknessM: 3.1, depthM: 264, quality: "Grade C" },
  { seam: "Seam IV", thicknessM: 5.8, depthM: 305, quality: "Grade B" },
];

const SUMMARY_SENTENCES = [
  "Across the surveyed Talcher block, the Seam VI horizon shows a mean thickness of 4.6 metres, consistent with the 2016 drilling baseline. ",
  "Overburden ratios remain stable along strike, with no material deviation reported between the 2016 and 2018 campaigns. ",
  "Sulphur content stays within the permissible band for Grade-B classification, and no discrepancy was flagged against the statutory review checklist. ",
  "Forest clearance demarcation sits approximately 1.8 kilometres from the proposed expansion boundary, which keeps the block outside the restricted buffer. ",
  "Corroborating borehole logs BH-14 and BH-22 support the seam continuity claim with less than 6% variance in recorded depth.",
];

/**
 * Builds a scripted sequence of QueryStreamEvents that mirrors what a real
 * orchestrator would push over the WebSocket: status pings, token-by-token
 * generation, retrieved vectors, citations, and the evidence panel payload,
 * arriving progressively rather than all at once.
 */
export function buildMockEventTimeline(): QueryStreamEvent[] {
  const events: QueryStreamEvent[] = [];
  events.push({ type: "status", stage: "Retrieving vectors from Qdrant index" });
  MOCK_CONTEXT_VECTORS.forEach((v) => events.push({ type: "vector", vector: v }));
  events.push({ type: "status", stage: "Grounding response against evidence" });
  events.push({ type: "evidence", evidence: MOCK_EVIDENCE });
  events.push({ type: "borehole", logs: MOCK_BOREHOLE_LOGS });
  events.push({ type: "seams", rows: MOCK_SEAM_ROWS });
  events.push({ type: "status", stage: "Synthesizing grounded response" });

  SUMMARY_SENTENCES.forEach((sentence, sIdx) => {
    const words = sentence.split(" ");
    words.forEach((w) => events.push({ type: "token", text: w + " " }));
    events.push({
      type: "citation",
      citation: {
        id: `cite-${sIdx}`,
        docId: MOCK_EVIDENCE.docId,
        label: `Ref: Doc-CMPDI-NK-2018-p.${42 + sIdx}`,
        page: 42 + sIdx,
      },
    });
  });

  events.push({ type: "done" });
  return events;
}

// ---------------------------------------------------------------------------
// Topic Explorer & Clusters
// ---------------------------------------------------------------------------

export const TOPIC_DOMAINS: TopicDomain[] = [
  { id: "all", label: "All Domains" },
  { id: "seam-geology", label: "Seam Geology" },
  { id: "opencast", label: "Opencast Blasting" },
  { id: "cbm", label: "Coal Bed Methane" },
  { id: "environment", label: "Environmental Clearance" },
  { id: "logistics", label: "Rail & Logistics" },
];

export const TOPICS: Topic[] = [
  {
    id: "exploration",
    title: "Exploration",
    domain: "seam-geology",
    mentionCount: 184,
    progress: 82,
    icon: "explore",
    summary: "Drilling campaigns, borehole logs and reserve estimation across active coalfields.",
  },
  {
    id: "coal-production",
    title: "Coal Production",
    domain: "opencast",
    mentionCount: 152,
    progress: 71,
    icon: "factory",
    summary: "Opencast output, blasting schedules and mechanized loading records.",
  },
  {
    id: "coal-seams",
    title: "Coal Seams",
    domain: "seam-geology",
    mentionCount: 131,
    progress: 68,
    icon: "layers",
    summary: "Seam thickness, depth and grade classification across surveyed blocks.",
  },
  {
    id: "coal-bed-methane",
    title: "Coal Bed Methane",
    domain: "cbm",
    mentionCount: 97,
    progress: 54,
    icon: "propane",
    summary: "Gas content assays and degasification planning ahead of mining.",
  },
  {
    id: "environmental-clearance",
    title: "Environmental Clearance",
    domain: "environment",
    mentionCount: 88,
    progress: 61,
    icon: "forest",
    summary: "Forest clearance demarcation, buffer zones and statutory compliance.",
  },
  {
    id: "rail-logistics",
    title: "Rail & Logistics",
    domain: "logistics",
    mentionCount: 63,
    progress: 45,
    icon: "railway_alert",
    summary: "Siding capacity, rake loading points and evacuation infrastructure.",
  },
];

export const SECONDARY_TOPICS: SecondaryTopic[] = [
  { id: "reserves", label: "Reserves", icon: "database", count: 214 },
  { id: "borehole", label: "Borehole Data", icon: "vertical_align_bottom", count: 176 },
  { id: "overburden", label: "Overburden", icon: "layers_clear", count: 142 },
  { id: "subsidence", label: "Subsidence", icon: "landslide", count: 98 },
  { id: "rehabilitation", label: "Rehabilitation", icon: "park", count: 87 },
  { id: "washery", label: "Washery Yield", icon: "water_drop", count: 73 },
  { id: "safety", label: "Mine Safety", icon: "shield", count: 121 },
  { id: "geo-survey", label: "Geo Survey", icon: "satellite_alt", count: 156 },
  { id: "dgms", label: "DGMS Filings", icon: "gavel", count: 64 },
];

export const CLUSTER_POINTS: ClusterPoint[] = [
  { id: "c1", x: 120, y: 90, radius: 26, topicId: "exploration", label: "Exploration" },
  { id: "c2", x: 210, y: 60, radius: 20, topicId: "coal-seams", label: "Coal Seams" },
  { id: "c3", x: 300, y: 140, radius: 22, topicId: "coal-production", label: "Coal Production" },
  { id: "c4", x: 90, y: 190, radius: 16, topicId: "environmental-clearance", label: "Environment" },
  { id: "c5", x: 250, y: 220, radius: 14, topicId: "coal-bed-methane", label: "CBM" },
  { id: "c6", x: 350, y: 70, radius: 12, topicId: "rail-logistics", label: "Rail" },
];

export const ARCHIVE_DOCS: ArchiveDoc[] = [
  {
    id: "arc-1",
    title: "North Karanpura Exploration Report 2018",
    topicId: "exploration",
    distance: 0.09,
    excerpt: "Seam VI thickness averages 4.6m across the surveyed block...",
    date: "2018-11-03",
  },
  {
    id: "arc-2",
    title: "Talcher Coalfield Drilling Campaign 2016",
    topicId: "exploration",
    distance: 0.14,
    excerpt: "Confirms seam geometry consistent with 2018 findings...",
    date: "2016-07-19",
  },
  {
    id: "arc-3",
    title: "Opencast Blasting Schedule — Q3",
    topicId: "coal-production",
    distance: 0.21,
    excerpt: "Weekly blasting windows aligned with rake availability...",
    date: "2024-09-02",
  },
  {
    id: "arc-4",
    title: "Environmental Demarcation Survey",
    topicId: "environmental-clearance",
    distance: 0.27,
    excerpt: "Forest clearance boundary sits 1.8km from proposed block...",
    date: "2019-02-14",
  },
  {
    id: "arc-5",
    title: "CBM Degasification Feasibility Note",
    topicId: "coal-bed-methane",
    distance: 0.33,
    excerpt: "Gas content assays support phased degasification...",
    date: "2021-05-28",
  },

];
