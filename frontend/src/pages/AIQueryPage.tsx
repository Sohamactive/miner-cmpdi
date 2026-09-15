import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ConfidenceMeter } from "../components/ui/ConfidenceMeter";
import { StreamingText } from "../components/ui/StreamingText";
import { useAIQueryStream } from "../hooks/useAIQueryStream";
import type { QueryFilters } from "../types";

const DOCUMENT_TYPES = ["All Types", "Exploration Reports", "Maps", "XLSX Registers", "DOCX Filings"];
const TIME_SPANS = ["All Time", "Last 5 Years", "2015 – 2020", "Pre-2015"];

const DEFAULT_FILTERS: QueryFilters = {
  documentType: DOCUMENT_TYPES[0],
  timeSpan: TIME_SPANS[0],
};

export function AIQueryPage() {
  const [query, setQuery] = useState(
    "What is the seam thickness reported for the Talcher block, and does it match prior drilling?",
  );
  const [filters, setFilters] = useState<QueryFilters>(DEFAULT_FILTERS);
  const { state, submit } = useAIQueryStream();

  const isStreaming = state.status === "streaming" || state.status === "connecting";
  const hasEvidence = !!state.evidence;

  return (
    <div className="grid grid-cols-12 gap-6 p-6">
      {/* ---------------------------------------------------------------- */}
      {/* LEFT PANEL — query, filters, streaming synthesis                  */}
      {/* ---------------------------------------------------------------- */}
      <section className="col-span-12 flex flex-col gap-5 lg:col-span-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-ink">Geological Vector Retrieval</h1>
            <p className="text-sm text-ink-muted">Stratigraphic search across the CMPDI archive</p>
          </div>
          <Badge tone="cluster" icon="bolt">
            GOV-RAG V4.2
          </Badge>
        </div>

        <div className="rounded-2xl border border-border bg-surface p-4">
          <p className="mb-3 font-data text-[11px] uppercase tracking-wide text-ink-faint">
            Stratigraphic Search Filters
          </p>
          <div className="grid grid-cols-2 gap-2">
            <FilterSelect
              value={filters.documentType}
              options={DOCUMENT_TYPES}
              onChange={(v) => setFilters((f) => ({ ...f, documentType: v }))}
            />
            <FilterSelect
              value={filters.timeSpan}
              options={TIME_SPANS}
              onChange={(v) => setFilters((f) => ({ ...f, timeSpan: v }))}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-surface p-4">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
            placeholder="Ask a natural-language question about the archive…"
            className="w-full resize-none bg-transparent text-sm text-ink outline-none placeholder:text-ink-faint"
          />
          <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
            <div className="flex items-center gap-1 text-ink-faint">
              <IconButton icon="attach_file" label="Attach reference" />
            </div>
            <Button
              icon="auto_awesome"
              disabled={isStreaming || !query.trim()}
              onClick={() => submit(query, filters)}
            >
              {isStreaming ? "Synthesizing…" : "Synthesize"}
            </Button>
          </div>
        </div>

        {(isStreaming || state.status === "done") && (
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-3 font-data text-[11px] uppercase tracking-wide text-ink-faint">
              Orchestrator Telemetry {state.usedFallback && "· local simulation"}
            </p>
            <div className="space-y-2.5">
              <ConfidenceMeter label="Gemini 1.5 Pro" value={state.status === "done" ? 0.97 : 0.6} />
              <ConfidenceMeter
                label="Cosine Similarity"
                value={state.evidence?.cosineSimilarity ?? 0.4}
              />
              <ConfidenceMeter label="RAG Grounding" value={hasEvidence ? 0.9 : 0.3} />
            </div>
            {state.stage && (
              <p className="mt-3 flex items-center gap-2 text-xs text-ink-muted">
                <span className="h-1.5 w-1.5 animate-pulse-ring rounded-full bg-cluster" />
                {state.stage}
              </p>
            )}
          </div>
        )}

        {(state.answer || isStreaming) && (
          <div className="rounded-2xl border border-border bg-surface p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-data text-[11px] uppercase tracking-wide text-ink-faint">
                CMPDI Intelligence Summary
              </p>
              {state.status === "done" && <Badge tone="success" icon="verified">Grounded</Badge>}
            </div>
            <div className="text-sm text-ink">
              <StreamingText text={state.answer} streaming={isStreaming} />
            </div>

            {state.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {state.citations.map((c) => (
                  <span
                    key={c.id}
                    className="rounded-md bg-cluster-bg px-2 py-0.5 font-data text-[11px] text-cluster"
                  >
                    {c.label}
                  </span>
                ))}
              </div>
            )}

            {state.status === "done" && (
              <div className="mt-4 flex items-center gap-2 border-t border-border pt-3">
                <span className="text-xs text-ink-muted">Does this answer match the source record?</span>
                <Button size="sm" variant="ghost" icon="thumb_up">
                  Yes
                </Button>
                <Button size="sm" variant="ghost" icon="report" className="text-danger">
                  Discrepancy
                </Button>
              </div>
            )}
          </div>
        )}

        {state.vectors.length > 0 && (
          <div className="rounded-2xl border border-border bg-surface p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-data text-[11px] uppercase tracking-wide text-ink-faint">
                Extracted Context Vectors
              </p>
              <Link
                to="/topics"
                className="flex items-center gap-1 text-xs font-medium text-cluster hover:underline"
              >
                View topic clusters
                <span className="material-symbols-outlined text-[16px] leading-none">arrow_forward</span>
              </Link>
            </div>
            <ul className="space-y-2">
              {state.vectors.map((v) => (
                <li key={v.id} className="rounded-lg border border-border p-2.5">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-ink">{v.title}</p>
                    <span className="font-data text-[11px] text-vector">{v.matchPercent}% match</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-muted">{v.excerpt}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* ---------------------------------------------------------------- */}
      {/* RIGHT PANEL — document viewer, grounding, borehole logs           */}
      {/* ---------------------------------------------------------------- */}
      <section className="col-span-12 lg:col-span-7">
        {!hasEvidence ? (
          <EmptyEvidenceState />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between rounded-2xl border border-border bg-surface p-4">
              <div>
                <p className="font-data text-xs text-ink-faint">{state.evidence!.docId}</p>
                <h2 className="text-base font-semibold text-ink">{state.evidence!.title}</h2>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="success" icon="verified_user">
                  {Math.round(state.evidence!.confidence * 100)}% confidence
                </Badge>
                <div className="flex items-center gap-1 font-data text-xs text-ink-muted">
                  <button className="rounded p-1 hover:bg-surface-raised">
                    <span className="material-symbols-outlined text-[16px] leading-none">chevron_left</span>
                  </button>
                  Page {state.evidence!.currentPage} / {state.evidence!.totalPages}
                  <button className="rounded p-1 hover:bg-surface-raised">
                    <span className="material-symbols-outlined text-[16px] leading-none">chevron_right</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <p className="text-sm leading-relaxed text-ink">
                <GroundedExcerpt text={state.evidence!.excerpt} spans={state.evidence!.groundingSpans} />
              </p>
            </div>

            {state.seamRows.length > 0 && (
              <div className="overflow-hidden rounded-2xl border border-border bg-surface">
                <p className="border-b border-border px-4 py-3 font-data text-[11px] uppercase tracking-wide text-ink-faint">
                  Seam Thickness Data
                </p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-ink-faint">
                      <th className="px-4 py-2 font-medium">Seam</th>
                      <th className="px-4 py-2 font-medium">Thickness (m)</th>
                      <th className="px-4 py-2 font-medium">Depth (m)</th>
                      <th className="px-4 py-2 font-medium">Quality</th>
                    </tr>
                  </thead>
                  <tbody className="font-data">
                    {state.seamRows.map((row) => (
                      <tr key={row.seam} className="border-b border-border last:border-0">
                        <td className="px-4 py-2 text-ink">{row.seam}</td>
                        <td className="px-4 py-2 text-ink">{row.thicknessM}</td>
                        <td className="px-4 py-2 text-ink">{row.depthM}</td>
                        <td className="px-4 py-2">
                          <Badge tone={row.quality === "Grade B" ? "success" : "warning"}>{row.quality}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 rounded-2xl border border-border bg-surface p-4 font-data text-xs">
              <div>
                <p className="text-ink-faint">Embedding Vector ID</p>
                <p className="mt-0.5 text-ink">{state.evidence!.embeddingId}</p>
              </div>
              <div>
                <p className="text-ink-faint">Cosine Similarity</p>
                <p className="mt-0.5 text-ink">{state.evidence!.cosineSimilarity.toFixed(3)}</p>
              </div>
              <div className="col-span-2 border-t border-border pt-3">
                <p className="text-ink-faint">Digital Signature</p>
                <p className="mt-0.5 text-ink">
                  {state.evidence!.signedBy} · {new Date(state.evidence!.signedAt).toLocaleString("en-IN")}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button icon="task_alt">Verify &amp; Approve</Button>
              <Button variant="ghost" icon="download">
                Download PDF
              </Button>
              <Button variant="ghost" icon="content_copy">
                Copy Excerpt
              </Button>
              <Button variant="destructive" icon="flag">
                Flag Discrepancy
              </Button>
            </div>

            {state.boreholeLogs.length > 0 && (
              <div>
                <p className="mb-2 font-data text-[11px] uppercase tracking-wide text-ink-faint">
                  Corroborating Borehole Logs
                </p>
                <div className="grid grid-cols-3 gap-3">
                  {state.boreholeLogs.map((log) => (
                    <div key={log.id} className="rounded-xl border border-border bg-surface p-3">
                      <p className="text-sm font-semibold text-ink">{log.name}</p>
                      <p className="mt-1 font-data text-xs text-ink-muted">{log.seam}</p>
                      <p className="font-data text-xs text-ink-muted">{log.depthMeters}m depth</p>
                      <p className="font-data text-xs text-ink-faint">{log.distanceKm}km away</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function FilterSelect({
  value,
  options,
  onChange,
}: {
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-border bg-surface px-2 py-1.5 text-xs text-ink outline-none focus:border-primary"
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}

function IconButton({ icon, label }: { icon: string; label: string }) {
  return (
    <button aria-label={label} className="rounded-lg p-1.5 hover:bg-surface-raised hover:text-ink">
      <span className="material-symbols-outlined text-[18px] leading-none">{icon}</span>
    </button>
  );
}

/** Renders excerpt text with the backend-supplied grounding span highlighted. */
function GroundedExcerpt({ text, spans }: { text: string; spans: { start: number; end: number }[] }) {
  if (spans.length === 0) return <>{text}</>;
  const { start, end } = spans[0];
  return (
    <>
      {text.slice(0, start)}
      <mark className="rounded bg-secondary/40 px-0.5 text-secondary-ink">{text.slice(start, end)}</mark>
      {text.slice(end)}
    </>
  );
}

function EmptyEvidenceState() {
  return (
    <div className="flex h-full min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-border-strong bg-surface p-10 text-center">
      <span className="material-symbols-outlined text-[40px] leading-none text-ink-faint">description</span>
      <h3 className="mt-3 text-sm font-semibold text-ink">No document loaded yet</h3>
      <p className="mt-1 max-w-xs text-sm text-ink-muted">
        Run a query on the left to retrieve grounded evidence — the source document, page,
        and cross-checks will render here as the response streams in.
      </p>
    </div>
  );
}
