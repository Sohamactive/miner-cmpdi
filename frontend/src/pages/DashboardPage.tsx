import { useState } from 'react'
import { kpiData, pipelineSteps, assetBreakdown, galleryCards, auditRecords } from '@/data/mockData'

export default function DashboardPage() {
  const [showModal, setShowModal] = useState(false)

  return (
    <>
      {/* ── Context Banner ── */}
      <section className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-md)] bg-surface-container-low flex flex-col md:flex-row md:items-center justify-between gap-[var(--spacing-space-md)] shadow-sm">
        <div className="flex items-center gap-[var(--spacing-space-md)]">
          <div className="w-10 h-10 rounded-[var(--radius-sm)] bg-primary text-on-primary flex items-center justify-center shadow-sm">
            <span className="material-symbols-outlined text-[24px]">corporate_fare</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-[var(--spacing-space-sm)]">
              <span className="text-[16px] leading-[24px] font-semibold text-primary">National Coal Archive Intelligence Hub</span>
              <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-highest text-on-surface text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                Node #CMPDI-HQ-01
              </span>
            </div>
            <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
              Automated multi-modal parsing, spatial OCR mapping, and RAG vector pipeline status for Coal India subsidiaries.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-[var(--spacing-space-sm)]">
          {[
            { icon: 'database', label: 'Inspect Vector Indices', variant: 'ghost', iconColor: 'text-secondary' },
            { icon: 'history_edu', label: 'Export Audit Trail', variant: 'ghost', iconColor: 'text-outline' },
            { icon: 'quick_reference_all', label: 'Launch RAG Query Engine', variant: 'secondary', iconColor: '' },
            { icon: 'upload_file', label: 'Ingest Archival Batch', variant: 'primary', iconColor: '' },
          ].map((btn) => (
            <button
              key={btn.label}
              className={`px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] font-semibold text-[13px] leading-[18px] tracking-[0.01em] rounded-[var(--radius-sm)] shadow-sm flex items-center gap-[var(--spacing-space-xs)] transition-colors ${
                btn.variant === 'primary' ? 'bg-primary text-on-primary hover:bg-primary-container' :
                btn.variant === 'secondary' ? 'bg-secondary text-on-secondary hover:opacity-95' :
                'bg-surface-container-lowest text-primary hover:bg-surface-container-high'
              }`}
            >
              <span className={`material-symbols-outlined text-[18px] ${btn.iconColor}`}>{btn.icon}</span>
              <span>{btn.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* ── Main Content ── */}
      <div className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-lg)] flex flex-col gap-[var(--spacing-space-lg)]">

        {/* ── KPI Grid ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[var(--spacing-space-md)]">
          {kpiData.map((kpi) => (
            <div key={kpi.label} className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-surface-container-low rounded-full -mr-8 -mt-8 pointer-events-none" />
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">{kpi.label}</span>
                  <span className={`material-symbols-outlined ${kpi.iconColor} text-[20px]`}>{kpi.icon}</span>
                </div>
                <div className={`mt-[var(--spacing-space-sm)] text-[24px] leading-[32px] font-bold tracking-tight ${kpi.valueColor || 'text-primary'}`}>{kpi.value}</div>
                <div className="mt-[var(--spacing-space-xs)] text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface">{kpi.subtitle}</div>
              </div>
              <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] flex items-center justify-between text-on-surface-variant font-mono text-[12px] leading-[16px]">
                {kpi.trendPositive !== undefined ? (
                  <span className={`flex items-center gap-1 font-semibold ${kpi.trendPositive ? 'text-tertiary-container' : 'text-error'}`}>
                    {kpi.trendPositive && <span className="material-symbols-outlined text-[14px]">trending_up</span>}
                    {kpi.trend}
                  </span>
                ) : (
                  <span className="text-on-tertiary-container font-semibold">{kpi.trend}</span>
                )}
                <span>{kpi.detail}</span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Pipeline + Asset Breakdown ── */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-[var(--spacing-space-md)]">
          {/* Pipeline Lifecycle */}
          <div className="xl:col-span-8 bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between pb-[var(--spacing-space-sm)]">
              <div className="flex items-center gap-[var(--spacing-space-sm)]">
                <span className="material-symbols-outlined text-primary text-[22px]">account_tree</span>
                <div>
                  <h2 className="text-[16px] leading-[24px] font-semibold text-primary">Live Document Intelligence &amp; Ingestion Lifecycle</h2>
                  <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">Synchronous staging from raw scan digitisation to vector payload synchronization</p>
                </div>
              </div>
              <div className="flex items-center gap-[var(--spacing-space-xs)] font-mono text-[12px] leading-[16px] text-tertiary-container bg-surface-container-low px-[var(--spacing-space-sm)] py-1 rounded-[var(--radius-sm)]">
                <span className="w-2 h-2 rounded-full bg-on-tertiary-container animate-pulse" />
                <span>Batch Worker Pool: 32 Threads</span>
              </div>
            </div>

            {/* 6 Pipeline Nodes */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-[var(--spacing-space-sm)] my-[var(--spacing-space-md)]">
              {pipelineSteps.map((step) => (
                <div key={step.step} className="bg-surface-container-low p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] flex flex-col justify-between h-36">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[12px] leading-[16px] text-on-surface-variant">{step.step}</span>
                      <span className={`material-symbols-outlined text-[16px] ${
                        step.status === 'complete' ? 'text-tertiary-container' :
                        step.status === 'active' ? 'text-secondary' : 'text-outline'
                      }`}>{step.icon}</span>
                    </div>
                    <div className="mt-1 text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">{step.title}</div>
                    <p className="mt-1 text-[11px] text-on-surface-variant">{step.subtitle}</p>
                  </div>
                  <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${step.status === 'active' ? 'bg-secondary' : 'bg-primary'}`}
                      style={{ width: `${step.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Active Ingestion Job */}
            <div className="bg-surface-container-low p-[var(--spacing-space-md)] rounded-[var(--radius-sm)] flex flex-col md:flex-row items-center justify-between gap-[var(--spacing-space-md)]">
              <div className="flex items-center gap-[var(--spacing-space-md)]">
                <div className="w-12 h-12 rounded-[var(--radius-sm)] bg-surface-container-lowest flex items-center justify-center text-primary shadow-sm">
                  <span className="material-symbols-outlined text-[24px]">memory</span>
                </div>
                <div>
                  <div className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">Active Ingestion Job: BATCH-RI2-1984-JH-09</div>
                  <div className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">Processing: Jharia Block VII Core Logs (Pages 120-280) • 28 docs queued</div>
                </div>
              </div>
              <div className="flex items-center gap-[var(--spacing-space-sm)]">
                <span className="font-mono text-[12px] leading-[16px] text-on-surface-variant">Throughput: 42 pages/min</span>
                <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-lowest hover:bg-surface-container-high text-primary text-[12px] leading-[16px] tracking-[0.02em] font-medium rounded-[var(--radius-sm)] shadow-sm">
                  Pause Worker
                </button>
              </div>
            </div>
          </div>

          {/* Asset Breakdown Donut */}
          <div className="xl:col-span-4 bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-[var(--spacing-space-xs)]">
                <h2 className="text-[16px] leading-[24px] font-semibold text-primary">Archival Asset Breakdown</h2>
                <span className="font-mono text-[12px] leading-[16px] text-outline">Total: 48.2K</span>
              </div>
              <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">Digitized historical &amp; geological payloads</p>

              {/* SVG Donut Chart */}
              <div className="flex items-center justify-center py-[var(--spacing-space-md)]">
                <div className="relative w-36 h-36 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                    <circle className="text-primary-container" cx="18" cy="18" fill="none" r="15.915" stroke="currentColor" strokeDasharray="46 54" strokeDashoffset="0" strokeWidth="3.5" />
                    <circle className="text-secondary" cx="18" cy="18" fill="none" r="15.915" stroke="currentColor" strokeDasharray="28 72" strokeDashoffset="-46" strokeWidth="3.5" />
                    <circle className="text-on-tertiary-container" cx="18" cy="18" fill="none" r="15.915" stroke="currentColor" strokeDasharray="16 84" strokeDashoffset="-74" strokeWidth="3.5" />
                    <circle className="text-outline" cx="18" cy="18" fill="none" r="15.915" stroke="currentColor" strokeDasharray="10 90" strokeDashoffset="-90" strokeWidth="3.5" />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <span className="text-[20px] leading-[28px] font-semibold text-primary">48.2k</span>
                    <span className="text-[10px] tracking-[0.08em] font-bold text-outline uppercase">Records</span>
                  </div>
                </div>
              </div>

              {/* Legend */}
              <div className="space-y-[var(--spacing-space-xs)]">
                {assetBreakdown.map((item) => (
                  <div key={item.label} className="flex items-center justify-between text-[13px] leading-[18px] p-1 rounded-[var(--radius-sm)] hover:bg-surface-container-low">
                    <div className="flex items-center gap-[var(--spacing-space-xs)]">
                      <span className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                      <span>{item.label}</span>
                    </div>
                    <span className="font-mono text-[12px] leading-[16px] text-primary font-semibold">
                      {item.value.toLocaleString()} ({item.percentage}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Visual Intelligence Gallery ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[var(--spacing-space-md)]">
          {galleryCards.map((card) => (
            <div key={card.title} className="bg-surface-container-lowest rounded-[var(--radius-sm)] shadow-sm overflow-hidden flex flex-col">
              <div className="relative h-44 w-full overflow-hidden bg-surface-container">
                {card.image ? (
                  <img className="w-full h-full object-cover" src={card.image} alt={card.title} />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-primary-container to-primary" />
                )}
                <span className="absolute top-2 left-2 bg-primary text-on-primary text-[11px] leading-[16px] tracking-[0.08em] font-bold px-2 py-0.5 rounded-[var(--radius-sm)]">
                  {card.tag}
                </span>
                <span className="absolute bottom-2 right-2 bg-surface-container-lowest text-on-surface font-mono text-[12px] leading-[16px] px-2 py-0.5 rounded-[var(--radius-sm)] shadow-sm">
                  {card.badge}
                </span>
              </div>
              <div className="p-[var(--spacing-space-md)] flex flex-col justify-between flex-1">
                <div>
                  <h3 className="text-[16px] leading-[24px] font-semibold text-primary">{card.title}</h3>
                  <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant mt-1">{card.description}</p>
                </div>
                <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] flex items-center justify-between text-[12px] leading-[16px] tracking-[0.02em] font-medium">
                  <span className="text-on-surface-variant">{card.source}</span>
                  <a className="text-secondary font-semibold hover:underline cursor-pointer">{card.action}</a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ── Audit Registry Table ── */}
        <div className="bg-surface-container-lowest rounded-[var(--radius-sm)] shadow-sm p-[var(--spacing-space-lg)] flex flex-col">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-[var(--spacing-space-sm)] pb-[var(--spacing-space-md)]">
            <div>
              <div className="flex items-center gap-[var(--spacing-space-sm)]">
                <h2 className="text-[20px] leading-[28px] font-semibold text-primary">Recent Ingestion Log &amp; Non-Repudiation Audit Registry</h2>
                <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-high text-on-surface text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                  Live Sync
                </span>
              </div>
              <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
                Cryptographically signed logs verified against Coal India central records archive policy
              </p>
            </div>
            <div className="flex items-center gap-[var(--spacing-space-sm)] flex-wrap">
              <div className="flex items-center bg-surface-container-low px-[var(--spacing-space-sm)] py-1 rounded-[var(--radius-sm)]">
                <span className="material-symbols-outlined text-[16px] text-outline mr-1">filter_list</span>
                <select className="bg-transparent text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface outline-none cursor-pointer">
                  <option>All Classifications</option>
                  <option>Geological Feasibility</option>
                  <option>Environmental Clearance</option>
                  <option>Mine Safety Compliance</option>
                </select>
              </div>
              <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low hover:bg-surface-container-high text-primary text-[12px] leading-[16px] tracking-[0.02em] font-medium rounded-[var(--radius-sm)] flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">refresh</span>
                <span>Refresh Registry</span>
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-[14px] leading-[22px]">
              <thead>
                <tr className="bg-surface-container-low text-on-surface-variant text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Document Title &amp; Record ID</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Department / Institute</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Format</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Classification Tag</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">OCR / Vector Confidence</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Ingestion Date</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold text-right">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container">
                {auditRecords.map((record) => (
                  <tr key={record.recordId} className="hover:bg-surface-container-low transition-colors">
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                      <div className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">{record.title}</div>
                      <div className="font-mono text-[11px] text-outline">{record.recordId}</div>
                    </td>
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] text-on-surface">{record.department}</td>
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                      <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-highest text-primary text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                        {record.format}
                      </span>
                    </td>
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                      <span className={`px-[var(--spacing-space-sm)] py-0.5 rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium ${
                        record.classificationBg || 'bg-surface-container-high'
                      } ${record.classificationText || 'text-primary'}`}>
                        {record.classification}
                      </span>
                    </td>
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                      <div className="flex items-center gap-[var(--spacing-space-xs)]">
                        <span className={`font-mono text-[12px] leading-[16px] font-semibold ${record.confidenceColor || 'text-tertiary-container'}`}>
                          {record.ocrConfidence}%
                        </span>
                        <div className="w-16 bg-surface-container h-1.5 rounded-full overflow-hidden">
                          <div className={`h-full ${record.ocrConfidence >= 97 ? 'bg-tertiary-container' : 'bg-secondary'}`} style={{ width: `${record.ocrConfidence}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px] text-on-surface-variant">
                      {record.ingestionDate}
                    </td>
                    <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] text-right">
                      <button
                        onClick={() => setShowModal(true)}
                        className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-lowest hover:bg-surface-container-high text-primary text-[12px] leading-[16px] tracking-[0.02em] font-medium rounded-[var(--radius-sm)] shadow-sm inline-flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-[14px] text-secondary">verified_user</span>
                        <span>View Provenance</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pt-[var(--spacing-space-md)] flex flex-col sm:flex-row items-center justify-between gap-[var(--spacing-space-sm)]">
            <span className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
              Showing <span className="font-semibold text-primary">1 to 5</span> of 48,290 records
            </span>
            <div className="flex items-center gap-[var(--spacing-space-xs)]">
              <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low text-outline rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium cursor-not-allowed">Previous</button>
              <button className="px-[var(--spacing-space-sm)] py-1 bg-primary text-on-primary rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium">1</button>
              <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low text-on-surface rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium hover:bg-surface-container-high">2</button>
              <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low text-on-surface rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium hover:bg-surface-container-high">3</button>
              <span className="px-1 text-outline">...</span>
              <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low text-on-surface rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium hover:bg-surface-container-high">9,658</button>
              <button className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low text-on-surface rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium hover:bg-surface-container-high">Next</button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Provenance Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary-container/50" onClick={() => setShowModal(false)}>
          <div className="bg-surface-container-lowest rounded-[var(--radius-sm)] max-w-xl w-full mx-[var(--spacing-space-md)] p-[var(--spacing-space-lg)] shadow-xl relative" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between pb-[var(--spacing-space-md)]">
              <div className="flex items-center gap-[var(--spacing-space-sm)]">
                <span className="material-symbols-outlined text-secondary text-[24px]">verified</span>
                <h3 className="text-[16px] leading-[24px] font-semibold text-primary">Cryptographic Provenance Certificate</h3>
              </div>
              <button className="text-outline hover:text-primary" onClick={() => setShowModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="space-y-[var(--spacing-space-sm)] text-[14px] leading-[22px]">
              <div className="p-[var(--spacing-space-sm)] bg-surface-container-low rounded-[var(--radius-sm)]">
                <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant block">SHA-256 Digest</span>
                <span className="font-mono text-[12px] leading-[16px] text-primary break-all">8f3c4e92a104bfa9824de84c90e1837d991bce09f6e1878d38440938ff56a29e</span>
              </div>
              <div className="grid grid-cols-2 gap-[var(--spacing-space-sm)]">
                <div className="p-[var(--spacing-space-sm)] bg-surface-container-low rounded-[var(--radius-sm)]">
                  <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant block">Ingested By</span>
                  <span className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">CMPDI Dhanbad RI-II</span>
                </div>
                <div className="p-[var(--spacing-space-sm)] bg-surface-container-low rounded-[var(--radius-sm)]">
                  <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant block">Qdrant Collection</span>
                  <span className="font-mono text-[12px] leading-[16px] text-primary">cmpdi_seam_strata_v2</span>
                </div>
              </div>
              <div className="p-[var(--spacing-space-sm)] bg-surface-container-low rounded-[var(--radius-sm)]">
                <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant block">Chunk Distribution</span>
                <span className="text-on-surface">32 Semantic chunks generated • Cosine distance 0.982 • Surya OCR validated</span>
              </div>
            </div>
            <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-sm)] flex justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-primary text-on-primary text-[13px] leading-[18px] tracking-[0.01em] font-semibold rounded-[var(--radius-sm)]"
              >
                Dismiss Certificate
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
