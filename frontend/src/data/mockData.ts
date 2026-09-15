import type {
  ArchiveDoc,
  BoreholeLog,
  ClusterPoint,
  ContextVector,
  EvidenceDocument,
  QueryStreamEvent,
  SeamRow,
  SecondaryTopic,
  Topic,
  TopicDomain,
} from "../types";

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
