import { useEffect, useMemo, useState } from 'react'
import { Activity, ArrowUpRight, CheckCircle2, CircleAlert, Download, FileText, Play, ShieldCheck } from 'lucide-react'

import { API_BASE_URL } from '@/api/client'

type AgentLog = { agent: string; status: string; timestamp?: number; duration_seconds?: number; error?: string | null }
type ReportResult = { report_id: number; status: string; title: string; sections: unknown[]; claims: Array<{ validation_status: string }>; report_url: string; download_url: string; agent_logs?: AgentLog[] }
type Job = { job_id: string; status: string; progress: number; step_label: string; error: string | null; result: ReportResult | null; agent_logs: AgentLog[] }

const API = '/api'
const steps = ['Gathering evidence', 'Drafting sections', 'Validating claims', 'Assembling report', 'Done']

export default function ReportSynthesisPage() {
  const [question, setQuestion] = useState('Summarize coal production and offtake figures from indexed documents with document and page references.')
  const [title, setTitle] = useState('Coal Production Report')
  const [reportType, setReportType] = useState('parliamentary_reply')
  const [job, setJob] = useState<Job | null>(null)
  const [error, setError] = useState('')
  const [approving, setApproving] = useState(false)
  const running = job?.status === 'queued' || job?.status === 'running'
  const result = job?.result
  const logs = useMemo(() => result?.agent_logs?.length ? result.agent_logs : job?.agent_logs ?? [], [job, result])

  useEffect(() => {
    if (!job?.job_id || !running) return
    const poll = async () => {
      try {
        const response = await fetch(`${API}/reports/job/${job.job_id}`)
        if (!response.ok) throw new Error(`Job request failed (${response.status})`)
        setJob(await response.json() as Job)
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : 'Unable to read report job.')
      }
    }
    const timer = window.setInterval(poll, 900)
    void poll()
    return () => window.clearInterval(timer)
  }, [job?.job_id, running])

  async function generate() {
    setError(''); setJob(null)
    try {
      const response = await fetch(`${API}/reports/generate-job`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, title, report_type: reportType, doc_ids: [] }) })
      if (!response.ok) throw new Error(`Could not start report (${response.status})`)
      const started = await response.json() as { job_id: string }
      setJob({ job_id: started.job_id, status: 'queued', progress: 0, step_label: steps[0], error: null, result: null, agent_logs: [] })
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to start report.') }
  }

  async function approve() {
    if (!result) return
    setApproving(true)
    try {
      const response = await fetch(`${API}/reports/${result.report_id}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'APPROVE', note: 'Reviewed in report workspace.' }) })
      if (!response.ok) throw new Error(`Approval failed (${response.status})`)
      setJob((current) => current ? { ...current, result: current.result ? { ...current.result, status: 'approved' } : null } : current)
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Approval failed.') } finally { setApproving(false) }
  }

  const statusLabel = job?.status === 'needs_review' ? 'Ready for review' : job?.status === 'failed' ? 'Generation failed' : job?.status ?? 'Awaiting request'

  const resolveApiLink = (path: string) => {
    // Allow both styles:
    // - API_BASE_URL="http://localhost:8000" (direct backend)
    // - API_BASE_URL="/api" (Vite dev proxy)
    if (!path) return ''
    if (!API_BASE_URL || API_BASE_URL.startsWith('/')) return path
    const base = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
    if (base.endsWith('/api') && path.startsWith('/api')) return `${base}${path.slice(4)}`
    return `${base}${path}`
  }

  const downloadHref = result ? resolveApiLink(result.download_url) : ''
  const reportHref = result ? resolveApiLink(result.report_url) : ''

  return <div className="report-workspace"><div className="report-shell">
    <header className="report-hero"><div><div className="eyebrow"><span className="eyebrow-dot" /> Report workstation / live pipeline</div><h1>Evidence to report.</h1><p>Build a cited parliamentary brief from indexed CMPDI and CIL records. Every run leaves a readable processing trail.</p></div><div className="hero-mark" aria-hidden="true"><span>R</span><span>E</span><span>P</span></div></header>
    <main className="report-grid">
      <section className="composer-panel"><div className="panel-kicker">01 / Define brief</div><h2>What should this report answer?</h2><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question grounded in indexed documents..." /><div className="field-row"><label>Report title<input value={title} onChange={(event) => setTitle(event.target.value)} /></label><label>Template<select value={reportType} onChange={(event) => setReportType(event.target.value)}><option value="parliamentary_reply">Parliamentary reply</option><option value="geological_summary">Geological summary</option></select></label></div><div className="composer-footer"><span className="source-note"><ShieldCheck size={15} /> Uses PostgreSQL facts + Qdrant evidence</span><button className="primary-action" onClick={() => void generate()} disabled={!question.trim() || running}><Play size={16} /> {running ? 'Generating' : 'Generate report'}</button></div>{error && <div className="error-note"><CircleAlert size={16} /> {error}</div>}</section>
      <section className="run-panel"><div className="panel-heading"><div><div className="panel-kicker">02 / Run ledger</div><h2>Processing status</h2></div><span className={`status-chip ${job?.status ?? 'idle'}`}>{statusLabel}</span></div><div className="progress-track"><span style={{ width: `${job?.progress ?? 0}%` }} /></div><div className="progress-meta"><span>{job?.step_label ?? 'No active run'}</span><strong>{job?.progress ?? 0}%</strong></div><div className="step-list">{steps.map((step, index) => { const active = Boolean(job && index <= Math.floor((job.progress / 100) * (steps.length - 1))); return <div className={`step-row ${active ? 'is-active' : ''}`} key={step}><span className="step-icon">{active ? <CheckCircle2 size={16} /> : <span>{String(index + 1).padStart(2, '0')}</span>}</span><span>{step}</span></div> })}</div></section>
      <section className="ledger-panel"><div className="panel-heading"><div><div className="panel-kicker">03 / Agent ledger</div><h2>What the run has done</h2></div><Activity size={18} className="muted-icon" /></div><div className="agent-list">{logs.length === 0 ? <div className="empty-ledger">Agent events appear here as the report progresses.</div> : logs.map((log) => <div className="agent-row" key={`${log.agent}-${log.timestamp}`}><span className={`agent-state ${log.status}`} /><span className="agent-name">{log.agent.replace('_agent', '')}</span><span className="agent-result">{log.status}</span>{log.duration_seconds ? <span className="agent-time">{log.duration_seconds.toFixed(1)}s</span> : null}</div>)}</div></section>
      <section className="result-panel"><div className="panel-heading"><div><div className="panel-kicker">04 / Review gate</div><h2>Report output</h2></div>{result && <FileText size={20} className="muted-icon" />}</div>{!result ? <div className="empty-result"><FileText size={30} /><p>Generated report will appear here.</p><span>Run a brief to unlock review and DOCX export.</span></div> : <><div className="result-title"><div><strong>{result.title}</strong><span>Report #{result.report_id} · {result.status}</span></div><ArrowUpRight size={18} /></div><div className="metric-row"><div><strong>{result.sections.length}</strong><span>sections</span></div><div><strong>{result.claims.length}</strong><span>claims</span></div><div><strong>{result.claims.filter((claim) => claim.validation_status === 'SUPPORTED').length}</strong><span>supported</span></div></div><div className="result-actions">{result.status === 'approved' ? <a className="primary-action link-action" href={downloadHref}><Download size={16} /> Download DOCX</a> : <button className="primary-action" onClick={() => void approve()} disabled={approving}><CheckCircle2 size={16} /> {approving ? 'Approving' : 'Approve report'}</button>}<a className="secondary-action" href={reportHref} target="_blank" rel="noreferrer">Open JSON <ArrowUpRight size={15} /></a></div></>}</section>
    </main>
    <footer className="workspace-footer"><span>M.I.N.E.R. / CMPDI evidence reporter</span><span>Live backend connection · No local simulation</span></footer>
  </div></div>
}
