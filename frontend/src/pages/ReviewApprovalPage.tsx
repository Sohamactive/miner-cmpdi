import { reportSections, reviewChecklist, approvalAudit, currentUser } from '@/data/mockData'

export default function ReviewApprovalPage() {
  return (
    <>
      {/* ── Breadcrumb & Security Bar ── */}
      <section className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-sm)] bg-surface-container-low flex flex-wrap items-center justify-between gap-[var(--spacing-space-sm)]">
        <div className="flex items-center gap-[var(--spacing-space-xs)] text-outline text-[12px] leading-[16px] tracking-[0.02em] font-medium">
          <span className="material-symbols-outlined text-[15px] text-primary">folder_managed</span>
          <span>National Coal Repository</span>
          <span className="text-outline-variant">/</span>
          <span>CMPDI Regional Institute-VII (Bhubaneswar)</span>
          <span className="text-outline-variant">/</span>
          <span>MCL - Talcher Expansion Block IV</span>
          <span className="text-outline-variant">/</span>
          <span className="text-on-surface font-semibold">Dossier SYN-2025-TLR-089A</span>
        </div>
        <div className="flex items-center gap-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px]">
          <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-high text-on-surface-variant flex items-center gap-1">
            <span className="material-symbols-outlined text-[13px] text-secondary">verified_user</span>
            DSC Level 3 Required
          </span>
          <span className="text-on-surface-variant">Review Session: #REV-9921-GOI</span>
          <div className="w-2 h-2 rounded-full bg-tertiary-container animate-pulse" />
        </div>
      </section>

      {/* ── Main Split Layout ── */}
      <div className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-md)] grid grid-cols-1 xl:grid-cols-12 gap-[var(--spacing-gutter)] items-start">

        {/* ── LEFT: Draft Report (7 cols) ── */}
        <div className="xl:col-span-7 flex flex-col gap-[var(--spacing-space-md)]">

          {/* Report Header Card */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <div className="flex flex-wrap items-center justify-between gap-[var(--spacing-space-xs)]">
              <div className="flex items-center gap-[var(--spacing-space-xs)]">
                <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-secondary-fixed text-on-secondary-fixed text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                  Confidential // Statutory Audit Ready
                </span>
                <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-high text-primary font-mono text-[12px] leading-[16px]">
                  DOC-ID: CMPDI/HQ/GEO/2025/R-4022
                </span>
              </div>
              <span className="font-mono text-[12px] leading-[16px] text-on-surface-variant flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">history</span>
                Synthesized: Today 08:31 IST via Gemini 1.5 Pro
              </span>
            </div>
            <h1 className="text-[24px] leading-[32px] font-bold text-primary tracking-tight">
              Draft Report: Comprehensive Geo-Technical Synthesis of Talcher Coalfield Expansion (2025–2030)
            </h1>
            <div className="flex flex-wrap items-center gap-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] text-on-surface-variant text-[12px] leading-[16px] tracking-[0.02em] font-medium">
              <span><strong className="text-on-surface">Target Zone:</strong> Bharatpur-Ananta Deep Colliery</span>
              <span><strong className="text-on-surface">Subsidiary:</strong> Mahanadi Coalfields Ltd (MCL)</span>
              <span><strong className="text-on-surface">Seam Depth:</strong> 120m - 450m RL</span>
            </div>
          </div>

          {/* Report Sections */}
          {reportSections.map((section) => (
            <div key={section.number} className="bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
              {/* Section Header */}
              <div className="flex items-start gap-[var(--spacing-space-sm)]">
                <span className="text-[20px] leading-[28px] font-semibold text-primary opacity-30">{section.number}</span>
                <div className="flex-1">
                  <h2 className="text-[20px] leading-[28px] font-semibold text-primary">{section.title}</h2>
                  <div className="flex items-center gap-[var(--spacing-space-xs)] mt-1">
                    <span className={`text-[12px] leading-[16px] tracking-[0.02em] font-medium flex items-center gap-1 ${
                      section.validationStatus === 'caution' ? 'text-secondary' : 'text-on-tertiary-container'
                    }`}>
                      <span className="material-symbols-outlined text-[14px]">
                        {section.validationStatus === 'caution' ? 'warning' : 'verified'}
                      </span>
                      Gemini Validated: {section.validationPercentage}% Grounding
                    </span>
                  </div>
                </div>
              </div>

              {/* Content */}
              {section.content && (
                <p className="text-[14px] leading-[22px] text-on-surface">{section.content}</p>
              )}

              {/* Data Table (Section 02) */}
              {section.hasTable && section.tableData && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[13px] leading-[18px]">
                    <thead>
                      <tr className="bg-surface-container-low text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">
                        <th className="py-2 px-3">Seam ID</th>
                        <th className="py-2 px-3">Mean Thickness (MT)</th>
                        <th className="py-2 px-3">Proved (MT)</th>
                        <th className="py-2 px-3">Indicated (MT)</th>
                        <th className="py-2 px-3">Gross GCV (Kcal/kg)</th>
                        <th className="py-2 px-3">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-container font-mono text-[12px] leading-[16px]">
                      {section.tableData.map((row) => (
                        <tr key={row.seamId} className="hover:bg-surface-container-low">
                          <td className="py-2 px-3 font-semibold text-primary">{row.seamId}</td>
                          <td className="py-2 px-3">{row.meanThickness}</td>
                          <td className="py-2 px-3">{row.proved}</td>
                          <td className="py-2 px-3">{row.indicated}</td>
                          <td className="py-2 px-3 whitespace-pre-line">{row.grossGCV}</td>
                          <td className="py-2 px-3">
                            <span className={`px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] text-[11px] tracking-[0.08em] font-bold uppercase ${
                              row.status === 'verified' ? 'bg-tertiary-fixed text-on-tertiary-fixed' :
                              row.status === 'drill-audit' ? 'bg-secondary-fixed text-on-secondary-fixed' :
                              'bg-surface-container-high text-on-surface-variant'
                            }`}>
                              {row.status === 'verified' ? 'Verified' : row.status === 'drill-audit' ? 'Drill Audit' : 'Pending'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Map Placeholder (Section 04) */}
              {section.hasMap && (
                <div className="w-full h-48 rounded-[var(--radius-md)] overflow-hidden bg-surface-container-high relative">
                  <div className="w-full h-full bg-gradient-to-br from-surface-container-low via-surface-container to-surface-container-high flex items-center justify-center">
                    <div className="flex flex-col items-center gap-2 text-on-surface-variant">
                      <span className="material-symbols-outlined text-[36px]">map</span>
                      <span className="text-[12px] font-mono">Lat 20.95° N, Long 85.12° E | Angul District, Odisha</span>
                      <span className="px-2 py-0.5 bg-primary text-on-primary text-[11px] font-bold rounded-[var(--radius-sm)]">SURVEY OF INDIA PORTAL LINKED</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Image (Section 03) */}
              {section.hasImage && (
                <div className="w-full max-w-sm">
                  <div className="w-full h-32 rounded-[var(--radius-sm)] bg-surface-container-high flex items-center justify-center">
                    <div className="flex flex-col items-center gap-1 text-on-surface-variant text-[12px]">
                      <span className="material-symbols-outlined text-[24px]">image</span>
                      <span className="font-mono">{section.imageCaption}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Risk Cards (Section 05) */}
              {section.riskCards && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-[var(--spacing-space-sm)]">
                  {section.riskCards.map((risk) => (
                    <div key={risk.title} className={`${risk.color} p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] flex flex-col gap-1`}>
                      <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">{risk.category}</span>
                      <span className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">{risk.title}</span>
                      <span className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">{risk.description}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Provenances */}
              {section.provenances.length > 0 && (
                <div className="flex flex-wrap items-center gap-[var(--spacing-space-xs)] pt-[var(--spacing-space-xs)]">
                  <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold text-outline uppercase">Provenances:</span>
                  {section.provenances.map((p) => (
                    <span key={p} className="text-[12px] leading-[16px] font-mono text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px] text-secondary">description</span>
                      {p}
                    </span>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-[var(--spacing-space-sm)] pt-[var(--spacing-space-xs)]">
                <button className="px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-tertiary-container text-on-tertiary rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold flex items-center gap-[var(--spacing-space-xs)] hover:opacity-90 transition-opacity">
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  Accept Formulation
                </button>
                <button className="px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-surface-container-low text-primary rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold flex items-center gap-[var(--spacing-space-xs)] hover:bg-surface-container-high transition-colors">
                  <span className="material-symbols-outlined text-[16px]">edit</span>
                  Modify / Inject Officer Comments
                </button>
              </div>
              <button className="text-secondary text-[12px] leading-[16px] tracking-[0.02em] font-medium flex items-center gap-1 hover:underline">
                <span className="material-symbols-outlined text-[14px]">sync</span>
                Reroute to LLM
              </button>
            </div>
          ))}
        </div>

        {/* ── RIGHT: Review Sidebar (5 cols) ── */}
        <div className="xl:col-span-5 flex flex-col gap-[var(--spacing-space-md)]">

          {/* User Profile Card */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <div className="flex items-center gap-[var(--spacing-space-sm)]">
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-on-primary text-[20px]">person</span>
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">{currentUser.name}</span>
                  <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-tertiary-fixed text-on-tertiary-fixed text-[11px] tracking-[0.08em] font-bold uppercase">
                    {currentUser.status}
                  </span>
                </div>
                <div className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">{currentUser.role}</div>
              </div>
            </div>
            <div className="flex items-center gap-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px] text-on-surface-variant">
              <span>CMP-ID: {currentUser.cilId}</span>
              <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-primary-fixed text-on-primary-fixed text-[11px] tracking-[0.08em] font-bold">
                Digital Role: {currentUser.digitalRole}
              </span>
            </div>
          </div>

          {/* Statutory Review Checklist */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <div className="flex items-center justify-between">
              <h3 className="text-[16px] leading-[24px] font-semibold text-primary flex items-center gap-1">
                <span className="material-symbols-outlined text-[18px]">checklist</span>
                Statutory Review Checklist
              </h3>
              <span className="font-mono text-[12px] leading-[16px] text-secondary font-semibold">2/3 Verified</span>
            </div>
            <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
              Mandatory verifications required prior to cryptographic signature and dispatch to the Coal Ministry Dossier.
            </p>
            <div className="flex flex-col gap-[var(--spacing-space-sm)]">
              {reviewChecklist.map((item) => (
                <label key={item.label} className="flex items-start gap-[var(--spacing-space-sm)] cursor-pointer group">
                  <input
                    type="checkbox"
                    defaultChecked={item.checked}
                    className="mt-0.5 w-4 h-4 rounded-[var(--radius-sm)] border-outline text-primary focus:ring-primary"
                  />
                  <div>
                    <span className={`text-[13px] leading-[18px] tracking-[0.01em] font-semibold ${
                      item.checked ? 'text-primary' : 'text-secondary'
                    }`}>{item.label}</span>
                    <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">{item.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Orchestration Directives */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <h3 className="text-[16px] leading-[24px] font-semibold text-primary flex items-center gap-1">
              <span className="material-symbols-outlined text-[18px]">settings_suggest</span>
              Orchestration Directives
              <span className="font-mono text-[12px] leading-[16px] text-on-surface-variant font-normal ml-auto">Qdrant Vector Sync</span>
            </h3>
            <div className="bg-surface-container-low p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
              <p>Provide consolidated annotations to refine embedding weights and re-rank synthesis pipelines for subsequent draft iterations.</p>
              <p className="mt-2 font-mono text-[12px] leading-[16px]">E.g. Recalculate Seam III fault dip angle by +1.5 deg following latest geotechnical core from Borehole 422...</p>
            </div>
            <div className="flex items-center gap-[var(--spacing-space-sm)]">
              <button className="text-[12px] leading-[16px] tracking-[0.02em] font-medium text-primary flex items-center gap-1 hover:underline">
                <span className="material-symbols-outlined text-[14px]">send</span>
                Submit Feedback Daemon → Online
              </button>
              <button className="text-[12px] leading-[16px] tracking-[0.02em] font-medium text-secondary flex items-center gap-1 hover:underline">
                <span className="material-symbols-outlined text-[14px]">forward</span>
                Transmit Directive
              </button>
            </div>
          </div>

          {/* Executive Certification & Export */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <h3 className="text-[16px] leading-[24px] font-semibold text-primary flex items-center gap-1">
              <span className="material-symbols-outlined text-[18px]">workspace_premium</span>
              Executive Certification &amp; Export
              <span className="font-mono text-[12px] leading-[16px] text-on-surface-variant font-normal ml-auto">DSC AUTH</span>
            </h3>
            <div className="flex flex-col gap-[var(--spacing-space-xs)]">
              <button className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-on-surface-variant flex items-center gap-[var(--spacing-space-xs)] px-[var(--spacing-space-sm)] py-[var(--spacing-space-xs)] bg-surface-container-low rounded-[var(--radius-sm)] hover:bg-surface-container-high transition-colors">
                <span className="material-symbols-outlined text-[16px] text-secondary">key</span>
                Apply Digital Cryptographic Token
              </button>
              <div className="font-mono text-[11px] text-outline px-[var(--spacing-space-sm)]">
                NIC / e-Mudhra USB Token Cert: 4891-A480-0012
              </div>
            </div>
            <button className="w-full px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-primary text-on-primary rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold flex items-center justify-center gap-[var(--spacing-space-xs)] hover:bg-primary-container transition-colors">
              <span className="material-symbols-outlined text-[16px]">picture_as_pdf</span>
              Generate &amp; Download Official PDF (with Gov Emblem &amp; Watermark)
            </button>
            <button className="w-full px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-surface-container-low text-primary rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold flex items-center justify-center gap-[var(--spacing-space-xs)] hover:bg-surface-container-high transition-colors">
              <span className="material-symbols-outlined text-[16px]">description</span>
              Export Editable Synthesis DOCX (Strict Formatting)
            </button>
            <button className="w-full px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-surface-container-low text-primary rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold flex items-center justify-center gap-[var(--spacing-space-xs)] hover:bg-surface-container-high transition-colors">
              <span className="material-symbols-outlined text-[16px]">send</span>
              Dispatch to Ministry of Coal Official Dossier
            </button>
          </div>

          {/* Approval Audit Trail */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <h3 className="text-[16px] leading-[24px] font-semibold text-primary">Official Approval Audit Trail</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-[11px] leading-[16px]">
                <thead>
                  <tr className="text-[11px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">
                    <th className="py-1 pr-2">Session</th>
                    <th className="py-1 pr-2">Sign-off / Timestamp</th>
                    <th className="py-1 pr-2">Officer</th>
                    <th className="py-1 pr-2">Immutable SHA-256 Hash</th>
                    <th className="py-1">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container">
                  {approvalAudit.map((entry) => (
                    <tr key={entry.sessionId}>
                      <td className="py-1.5 pr-2 text-primary font-semibold">{entry.sessionId}</td>
                      <td className="py-1.5 pr-2 text-on-surface-variant">{entry.signOffDate}</td>
                      <td className="py-1.5 pr-2 text-on-surface">{entry.officer}</td>
                      <td className="py-1.5 pr-2 text-outline">{entry.hash}</td>
                      <td className="py-1.5">
                        <span className={`px-1.5 py-0.5 rounded-[var(--radius-sm)] text-[10px] tracking-[0.08em] font-bold uppercase ${
                          entry.status === 'dispatched' ? 'bg-secondary-fixed text-on-secondary-fixed' :
                          'bg-surface-container-high text-primary'
                        }`}>
                          {entry.status === 'modified' ? 'MOD' : entry.status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
