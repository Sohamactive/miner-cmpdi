import { useState } from 'react'
import { reportTemplates } from '@/data/mockData'

export default function ReportSynthesisPage() {
  const [selectedTemplate, setSelectedTemplate] = useState(reportTemplates[3].id)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleSynthesize = () => {
    setIsGenerating(true)
    setTimeout(() => {
      setIsGenerating(false)
      // Transition to a generated state or show toast
    }, 2500)
  }

  return (
    <>
      {/* ── Context & Breadcrumb Bar ── */}
      <section className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-sm)] bg-surface-container-low flex flex-wrap items-center justify-between gap-[var(--spacing-space-sm)] shadow-sm">
        <div className="flex items-center gap-[var(--spacing-space-xs)] text-outline text-[12px] leading-[16px] tracking-[0.02em] font-medium">
          <span className="material-symbols-outlined text-[15px] text-primary">folder_managed</span>
          <span>Repository</span>
          <span className="text-outline-variant">/</span>
          <span>Synthesis Engine Hub</span>
          <span className="text-outline-variant">/</span>
          <span className="text-on-surface font-semibold">New Report Formulation</span>
        </div>
        <div className="flex items-center gap-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px]">
          <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-primary-fixed text-on-primary-fixed flex items-center gap-1 font-bold">
            Synthesis Engine v2.4
          </span>
          <div className="flex items-center gap-1 text-tertiary-container">
            <span className="w-2 h-2 rounded-full bg-tertiary-container animate-pulse" />
            Gemini 1.5 Pro Active
          </div>
        </div>
      </section>

      {/* ── Main Layout ── */}
      <div className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-md)] grid grid-cols-1 xl:grid-cols-12 gap-[var(--spacing-gutter)] items-start animate-fade-in-up">
        
        {/* ── LEFT: Configuration & Templates (7 Cols) ── */}
        <div className="xl:col-span-7 flex flex-col gap-[var(--spacing-space-md)]">
          
          {/* Header */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)]">
            <h1 className="text-[24px] leading-[32px] font-bold text-primary tracking-tight">
              Report Synthesis &amp; Documentation Engine
            </h1>
            <p className="text-[14px] leading-[22px] text-on-surface-variant">
              Generate standardized, audit-ready compliance reports and technical syntheses by fusing data from Qdrant vector indices, live sensor telemetry, and legacy archival ledgers.
            </p>
          </div>

          {/* Template Selector */}
          <div className="flex flex-col gap-[var(--spacing-space-sm)]">
            <h2 className="text-[16px] leading-[24px] font-semibold text-primary">1. Select Target Template</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-[var(--spacing-space-md)]">
              {reportTemplates.map((template) => {
                const isSelected = selectedTemplate === template.id
                return (
                  <div
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`card-hover p-[var(--spacing-space-md)] rounded-[var(--radius-md)] border-2 cursor-pointer transition-all ${
                      isSelected 
                        ? 'bg-surface-container-low border-primary shadow-sm' 
                        : 'bg-surface-container-lowest border-surface-container hover:border-outline-variant hover:bg-surface-container-low/50'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className={`w-10 h-10 rounded-[var(--radius-sm)] flex items-center justify-center ${
                        isSelected ? 'bg-primary text-on-primary' : 'bg-surface-container text-primary'
                      }`}>
                        <span className="material-symbols-outlined text-[20px]">{template.icon}</span>
                      </div>
                      <span className="font-mono text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-outline">
                        {template.category}
                      </span>
                    </div>
                    <h3 className={`text-[14px] leading-[22px] font-semibold mb-1 ${isSelected ? 'text-primary' : 'text-on-surface'}`}>
                      {template.title}
                    </h3>
                    <p className="text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface-variant mb-[var(--spacing-space-sm)]">
                      {template.description}
                    </p>
                    <div className="flex items-center gap-[var(--spacing-space-xs)] font-mono text-[11px] text-on-surface-variant">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      Est. Generation: {template.estimatedTime}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Configuration Panel */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-md)] mt-[var(--spacing-space-sm)]">
            <h2 className="text-[16px] leading-[24px] font-semibold text-primary border-b border-surface-container pb-2">
              2. Parameter Configuration
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--spacing-space-md)]">
              {/* Target Zone */}
              <div className="flex flex-col gap-[var(--spacing-space-xs)]">
                <label className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-outline">Target Zone / Block</label>
                <select className="bg-surface-container-low text-[13px] leading-[18px] tracking-[0.01em] text-on-surface p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] outline-none border border-transparent focus:border-primary">
                  <option>MCL - Talcher Expansion Block IV</option>
                  <option>BCCL - Jharia Sector 9</option>
                  <option>NCL - Singrauli Phase II</option>
                </select>
              </div>

              {/* Subsidiary */}
              <div className="flex flex-col gap-[var(--spacing-space-xs)]">
                <label className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-outline">Managing Subsidiary</label>
                <select className="bg-surface-container-low text-[13px] leading-[18px] tracking-[0.01em] text-on-surface p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] outline-none border border-transparent focus:border-primary">
                  <option>Mahanadi Coalfields Ltd (MCL)</option>
                  <option>Bharat Coking Coal Ltd (BCCL)</option>
                  <option>Northern Coalfields Ltd (NCL)</option>
                </select>
              </div>

              {/* Date Range */}
              <div className="flex flex-col gap-[var(--spacing-space-xs)]">
                <label className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-outline">Exploration Horizon</label>
                <select className="bg-surface-container-low text-[13px] leading-[18px] tracking-[0.01em] text-on-surface p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] outline-none border border-transparent focus:border-primary">
                  <option>Modern Mechanization (2011–2025)</option>
                  <option>Economic Reforms (1991–2010)</option>
                  <option>All Eras (1960–2025)</option>
                </select>
              </div>

              {/* Depth */}
              <div className="flex flex-col gap-[var(--spacing-space-xs)]">
                <label className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-outline">Target Depth Horizon (RL)</label>
                <select className="bg-surface-container-low text-[13px] leading-[18px] tracking-[0.01em] text-on-surface p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] outline-none border border-transparent focus:border-primary">
                  <option>Deep Underground (120m - 450m)</option>
                  <option>Shallow Opencast (0m - 120m)</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-[var(--spacing-space-xs)] pt-[var(--spacing-space-sm)] border-t border-surface-container">
              <label className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-outline">Advanced Directives (Optional Prompts)</label>
              <textarea 
                className="bg-surface-container-low text-[13px] leading-[18px] tracking-[0.01em] text-on-surface p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] outline-none border border-transparent focus:border-primary resize-none placeholder:text-outline-variant" 
                rows={3}
                placeholder="E.g., Emphasize the impact of Fault F-14 on the stripping ratio..."
              />
            </div>
          </div>

          {/* Action Area */}
          <div className="flex items-center justify-end gap-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)]">
            <button className="px-[var(--spacing-space-md)] py-[var(--spacing-space-sm)] bg-surface-container-lowest text-primary rounded-[var(--radius-sm)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold hover:bg-surface-container-high transition-colors border border-surface-container">
              Save Configuration Profile
            </button>
            <button 
              onClick={handleSynthesize}
              disabled={isGenerating}
              className={`px-[var(--spacing-space-xl)] py-[var(--spacing-space-sm)] bg-primary text-on-primary rounded-[var(--radius-sm)] text-[14px] leading-[22px] font-semibold flex items-center justify-center gap-[var(--spacing-space-xs)] transition-colors shadow-sm ${
                isGenerating ? 'opacity-80 cursor-not-allowed' : 'hover:bg-primary-container'
              }`}
            >
              {isGenerating ? (
                <>
                  <span className="material-symbols-outlined text-[20px] animate-spin">autorenew</span>
                  Synthesizing Report...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                  Synthesize Report
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── RIGHT: Recent Reports & Preview (5 Cols) ── */}
        <div className="xl:col-span-5 flex flex-col gap-[var(--spacing-space-md)]">
          
          {/* Generation Queue / Active Tasks */}
          {isGenerating && (
            <div className="bg-primary p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm text-on-primary flex flex-col gap-[var(--spacing-space-sm)] animate-in slide-in-from-top-4 duration-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-[var(--spacing-space-xs)]">
                  <span className="material-symbols-outlined text-secondary-fixed animate-spin">memory</span>
                  <span className="text-[14px] leading-[22px] font-semibold">Gemini LLM Orchestrator</span>
                </div>
                <span className="font-mono text-[12px] leading-[16px] text-primary-fixed-dim">Step 3 of 5</span>
              </div>
              <div className="text-[13px] leading-[18px] tracking-[0.01em]">
                Retrieving vector context for Talcher Block IV Seam Thickness...
              </div>
              <div className="w-full bg-primary-container h-1.5 rounded-full overflow-hidden mt-1">
                <div className="h-full bg-secondary-fixed w-3/5 transition-all duration-500" />
              </div>
            </div>
          )}

          {/* Quick Preview Pane */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)] h-[400px]">
            <div className="flex items-center justify-between border-b border-surface-container pb-2">
              <h3 className="text-[16px] leading-[24px] font-semibold text-primary flex items-center gap-1">
                <span className="material-symbols-outlined text-[18px]">preview</span>
                Output Preview
              </h3>
              <div className="flex items-center gap-[var(--spacing-space-xs)]">
                <button className="p-1 hover:bg-surface-container-low rounded text-outline hover:text-primary transition-colors" title="Download PDF">
                  <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
                </button>
                <button className="p-1 hover:bg-surface-container-low rounded text-outline hover:text-primary transition-colors" title="Download DOCX">
                  <span className="material-symbols-outlined text-[18px]">description</span>
                </button>
              </div>
            </div>
            
            <div className="flex-1 bg-surface-container-low rounded-[var(--radius-sm)] flex flex-col items-center justify-center text-center p-[var(--spacing-space-xl)] relative overflow-hidden">
              <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(0,0,0,0.02)_25%,rgba(0,0,0,0.02)_50%,transparent_50%,transparent_75%,rgba(0,0,0,0.02)_75%,rgba(0,0,0,0.02)_100%)] bg-[length:20px_20px]" />
              <div className="w-16 h-16 rounded-[var(--radius-sm)] bg-surface-container-highest flex items-center justify-center mb-[var(--spacing-space-sm)] text-outline shadow-inner relative z-10">
                <span className="material-symbols-outlined text-[32px]">plagiarism</span>
              </div>
              <h4 className="text-[14px] leading-[22px] font-semibold text-on-surface-variant relative z-10">No active preview</h4>
              <p className="text-[12px] leading-[16px] tracking-[0.02em] font-medium text-outline mt-1 relative z-10">
                Configure parameters and click Synthesize to preview the generated report here.
              </p>
            </div>
          </div>

          {/* Recent Reports Table */}
          <div className="bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-md)] shadow-sm flex flex-col gap-[var(--spacing-space-sm)] flex-1">
            <h3 className="text-[16px] leading-[24px] font-semibold text-primary">Recently Synthesized</h3>
            <div className="flex flex-col gap-[var(--spacing-space-xs)]">
              {[
                { id: 'SYN-2025-TLR-089A', title: 'Talcher Comp Synthesis', date: 'Today, 08:31', status: 'Ready', statusColor: 'bg-tertiary-fixed text-on-tertiary-fixed' },
                { id: 'SYN-2025-JHR-112C', title: 'Jharia Safety Audit', date: 'Yesterday', status: 'In Review', statusColor: 'bg-secondary-fixed text-on-secondary-fixed' },
                { id: 'SYN-2025-NCL-044B', title: 'Singrauli Env Clearance', date: '12 Oct 2025', status: 'Approved', statusColor: 'bg-surface-container-high text-on-surface-variant' },
              ].map(report => (
                <div key={report.id} className="flex items-center justify-between p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] hover:bg-surface-container-low transition-colors group cursor-pointer border border-transparent hover:border-surface-container-high">
                  <div className="flex flex-col">
                    <span className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">{report.title}</span>
                    <span className="font-mono text-[11px] leading-[16px] text-on-surface-variant">{report.id} • {report.date}</span>
                  </div>
                  <div className="flex items-center gap-[var(--spacing-space-sm)]">
                    <span className={`px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] text-[10px] tracking-[0.08em] font-bold uppercase ${report.statusColor}`}>
                      {report.status}
                    </span>
                    <button className="text-outline hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="material-symbols-outlined text-[18px]">download</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </>
  )
}
