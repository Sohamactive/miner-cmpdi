import type {
  KPIData, PipelineStepData, AssetBreakdownItem, GalleryCard,
  AuditRecord, ReportSection, SeamReserveRow, ReviewChecklist,
  ApprovalAuditEntry, UserProfile, ReportTemplate, NavItem,
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
