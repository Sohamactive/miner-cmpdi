import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiGet } from '@/api/client'

type UploadItem = {
  doc_id: string
  filename: string
  ext: string
  bytes: number
  modified_at?: string
  modified_at_epoch?: number
}

type BatchItem = {
  doc_id: string
  batch_dir: string
  has_merged: boolean
  has_result: boolean
  ready_to_index: boolean
  modified_at?: string
  modified_at_epoch?: number
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  const digits = unit === 0 ? 0 : value >= 10 ? 1 : 2
  return `${value.toFixed(digits)} ${units[unit]}`
}

export default function DashboardPage() {
  const [uploads, setUploads] = useState<UploadItem[]>([])
  const [batches, setBatches] = useState<BatchItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<number | null>(null)

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      const [uploadsPayload, batchesPayload] = await Promise.all([
        apiGet<{ uploads: UploadItem[] }>('/api/documents/uploads'),
        apiGet<{ batches: BatchItem[] }>('/api/documents/batches'),
      ])
      setUploads(uploadsPayload.uploads ?? [])
      setBatches(batchesPayload.batches ?? [])
      setLastUpdated(Date.now())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load ingestion stats.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  const batchById = useMemo(() => {
    const m = new Map<string, BatchItem>()
    batches.forEach((b) => m.set(b.doc_id, b))
    return m
  }, [batches])

  const totals = useMemo(() => {
    const totalUploads = uploads.length
    const totalBytes = uploads.reduce((acc, u) => acc + (u.bytes ?? 0), 0)
    const processed = batches.filter((b) => b.has_result).length
    const readyToIndex = batches.filter((b) => b.ready_to_index).length

    const extCounts = new Map<string, number>()
    uploads.forEach((u) => {
      const ext = (u.ext || 'unknown').toLowerCase()
      extCounts.set(ext, (extCounts.get(ext) ?? 0) + 1)
    })
    const extBreakdown = [...extCounts.entries()]
      .map(([ext, count]) => ({ ext, count }))
      .sort((a, b) => b.count - a.count)

    return { totalUploads, totalBytes, processed, readyToIndex, extBreakdown }
  }, [uploads, batches])

  const recentUploads = useMemo(() => {
    const withTime = uploads.map((u) => ({
      ...u,
      _t: (u.modified_at_epoch ?? 0),
    }))
    withTime.sort((a, b) => b._t - a._t)
    return withTime.slice(0, 12)
  }, [uploads])

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
              Multi-modal document ingestion, AI-powered query, and automated report synthesis for Coal India subsidiaries.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-[var(--spacing-space-sm)]">
          <Link
            to="/ai-query"
            className="px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] font-semibold text-[13px] leading-[18px] tracking-[0.01em] rounded-[var(--radius-sm)] shadow-sm flex items-center gap-[var(--spacing-space-xs)] transition-colors bg-secondary text-on-secondary hover:opacity-95"
          >
            <span className="material-symbols-outlined text-[18px]">quick_reference_all</span>
            <span>Launch AI Query</span>
          </Link>
          <Link
            to="/reports"
            className="px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] font-semibold text-[13px] leading-[18px] tracking-[0.01em] rounded-[var(--radius-sm)] shadow-sm flex items-center gap-[var(--spacing-space-xs)] transition-colors bg-primary text-on-primary hover:bg-primary-container"
          >
            <span className="material-symbols-outlined text-[18px]">upload_file</span>
            <span>Report Synthesis</span>
          </Link>
        </div>
      </section>

      {/* ── Main Content ── */}
      <div className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-lg)] flex flex-col gap-[var(--spacing-space-lg)] animate-fade-in-up">

        {/* ── KPI Grid ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[var(--spacing-space-md)]">
          <div className="card-hover bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-surface-container-low rounded-full -mr-8 -mt-8 pointer-events-none" />
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">Uploads</span>
                <span className="material-symbols-outlined text-outline text-[20px]">folder_special</span>
              </div>
              <div className="mt-[var(--spacing-space-sm)] text-[24px] leading-[32px] font-bold tracking-tight text-primary">{totals.totalUploads.toLocaleString()}</div>
              <div className="mt-[var(--spacing-space-xs)] text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface">Files under backend/data/uploads</div>
            </div>
            <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] flex items-center justify-between text-on-surface-variant font-mono text-[12px] leading-[16px]">
              <span>{loading ? 'syncing…' : 'live'}</span>
              <span>{lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : '—'}</span>
            </div>
          </div>

          <div className="card-hover bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-surface-container-low rounded-full -mr-8 -mt-8 pointer-events-none" />
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">Processed</span>
                <span className="material-symbols-outlined text-secondary text-[20px]">document_scanner</span>
              </div>
              <div className="mt-[var(--spacing-space-sm)] text-[24px] leading-[32px] font-bold tracking-tight text-primary">{totals.processed.toLocaleString()}</div>
              <div className="mt-[var(--spacing-space-xs)] text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface">Batches with result.json</div>
            </div>
            <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] flex items-center justify-between text-on-surface-variant font-mono text-[12px] leading-[16px]">
              <span>ready: {totals.readyToIndex.toLocaleString()}</span>
              <span>of {Math.max(totals.totalUploads, totals.processed).toLocaleString()}</span>
            </div>
          </div>

          <div className="card-hover bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-surface-container-low rounded-full -mr-8 -mt-8 pointer-events-none" />
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">Storage</span>
                <span className="material-symbols-outlined text-outline text-[20px]">hard_drive</span>
              </div>
              <div className="mt-[var(--spacing-space-sm)] text-[24px] leading-[32px] font-bold tracking-tight text-primary">{formatBytes(totals.totalBytes)}</div>
              <div className="mt-[var(--spacing-space-xs)] text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface">Uploaded payload size</div>
            </div>
            <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] flex items-center justify-between text-on-surface-variant font-mono text-[12px] leading-[16px]">
              <span>{totals.extBreakdown[0] ? `${totals.extBreakdown[0].ext.toUpperCase()} top` : '—'}</span>
              <span>{totals.extBreakdown[0] ? `${totals.extBreakdown[0].count} files` : ''}</span>
            </div>
          </div>

          <div className="card-hover bg-surface-container-lowest p-[var(--spacing-space-md)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-surface-container-low rounded-full -mr-8 -mt-8 pointer-events-none" />
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase text-on-surface-variant">Ready To Index</span>
                <span className="material-symbols-outlined text-tertiary-container text-[20px]">hub</span>
              </div>
              <div className="mt-[var(--spacing-space-sm)] text-[24px] leading-[32px] font-bold tracking-tight text-primary">{totals.readyToIndex.toLocaleString()}</div>
              <div className="mt-[var(--spacing-space-xs)] text-[12px] leading-[16px] tracking-[0.02em] font-medium text-on-surface">merged.md + result.json present</div>
            </div>
            <div className="mt-[var(--spacing-space-md)] pt-[var(--spacing-space-xs)] flex items-center justify-between text-on-surface-variant font-mono text-[12px] leading-[16px]">
              <span>{batches.length ? `${Math.round((totals.readyToIndex / Math.max(1, batches.length)) * 100)}%` : '0%'}</span>
              <span>of {batches.length.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* ── Pipeline + File Types ── */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-[var(--spacing-space-md)]">
          <div className="xl:col-span-8 bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between pb-[var(--spacing-space-sm)]">
              <div className="flex items-center gap-[var(--spacing-space-sm)]">
                <span className="material-symbols-outlined text-primary text-[22px]">account_tree</span>
                <div>
                  <h2 className="text-[16px] leading-[24px] font-semibold text-primary">Ingestion Pipeline (Derived)</h2>
                  <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">Computed from backend uploads + batch artifacts (no mock numbers)</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-[var(--spacing-space-sm)] my-[var(--spacing-space-md)]">
              {([
                {
                  step: '01',
                  title: 'Upload',
                  subtitle: `${totals.totalUploads.toLocaleString()} files present`,
                  progress: totals.totalUploads ? 100 : 0,
                  status: totals.totalUploads ? 'complete' : 'pending',
                  icon: totals.totalUploads ? 'check_circle' : 'hourglass_top',
                },
                {
                  step: '02',
                  title: 'Extract',
                  subtitle: `${totals.processed.toLocaleString()} batches with result.json`,
                  progress: totals.totalUploads ? Math.round((totals.processed / Math.max(1, totals.totalUploads)) * 100) : 0,
                  status: totals.processed ? (totals.processed === totals.totalUploads ? 'complete' : 'active') : 'pending',
                  icon: totals.processed === totals.totalUploads && totals.totalUploads ? 'check_circle' : (totals.processed ? 'sync' : 'hourglass_top'),
                },
                {
                  step: '03',
                  title: 'Ready To Index',
                  subtitle: `${totals.readyToIndex.toLocaleString()} ready`,
                  progress: totals.processed ? Math.round((totals.readyToIndex / Math.max(1, totals.processed)) * 100) : 0,
                  status: totals.readyToIndex ? (totals.readyToIndex === totals.processed && totals.processed ? 'complete' : 'active') : 'pending',
                  icon: totals.readyToIndex === totals.processed && totals.processed ? 'check_circle' : (totals.readyToIndex ? 'sync' : 'hourglass_top'),
                },
              ] as const).map((step) => (
                <div key={step.step} className="card-hover bg-surface-container-low p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] flex flex-col justify-between h-36">
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
          </div>

          <div className="xl:col-span-4 bg-surface-container-lowest p-[var(--spacing-space-lg)] rounded-[var(--radius-sm)] shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-[var(--spacing-space-xs)]">
                <h2 className="text-[16px] leading-[24px] font-semibold text-primary">File Types</h2>
                <span className="font-mono text-[12px] leading-[16px] text-outline">Total: {totals.totalUploads.toLocaleString()}</span>
              </div>
              <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">Derived from backend uploads list</p>

              <div className="mt-[var(--spacing-space-md)] space-y-[var(--spacing-space-xs)]">
                {totals.extBreakdown.length === 0 ? (
                  <div className="text-[13px] leading-[18px] text-on-surface-variant">No uploads found.</div>
                ) : (
                  totals.extBreakdown.slice(0, 8).map((item) => {
                    const pct = totals.totalUploads ? Math.round((item.count / totals.totalUploads) * 100) : 0
                    return (
                      <div key={item.ext} className="p-2 rounded-[var(--radius-sm)] bg-surface-container-low">
                        <div className="flex items-center justify-between text-[13px] leading-[18px]">
                          <span className="font-semibold text-primary">.{item.ext}</span>
                          <span className="font-mono text-[12px] leading-[16px] text-on-surface-variant">{item.count} ({pct}%)</span>
                        </div>
                        <div className="mt-2 w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden">
                          <div className="h-full bg-secondary" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Audit Registry Table ── */}
        <div className="bg-surface-container-lowest rounded-[var(--radius-sm)] shadow-sm p-[var(--spacing-space-lg)] flex flex-col">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-[var(--spacing-space-sm)] pb-[var(--spacing-space-md)]">
            <div>
              <div className="flex items-center gap-[var(--spacing-space-sm)]">
                <h2 className="text-[20px] leading-[28px] font-semibold text-primary">Recent Uploads</h2>
                <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-high text-on-surface text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                  Live Sync
                </span>
              </div>
              <p className="text-[13px] leading-[18px] tracking-[0.01em] text-on-surface-variant">
                Backend-derived uploads with batch readiness
              </p>
            </div>
            <div className="flex items-center gap-[var(--spacing-space-sm)] flex-wrap">
              <button onClick={() => void refresh()} disabled={loading} className="px-[var(--spacing-space-sm)] py-1 bg-surface-container-low hover:bg-surface-container-high text-primary text-[12px] leading-[16px] tracking-[0.02em] font-medium rounded-[var(--radius-sm)] flex items-center gap-1 disabled:opacity-60 disabled:cursor-not-allowed">
                <span className="material-symbols-outlined text-[16px]">refresh</span>
                <span>{loading ? 'Refreshing' : 'Refresh'}</span>
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-[var(--spacing-space-md)] px-[var(--spacing-space-md)] py-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] bg-error-container text-on-error-container text-[13px] leading-[18px]">
              {error}
            </div>
          )}

          {/* Table */}
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-[14px] leading-[22px]">
              <thead>
                <tr className="bg-surface-container-low text-on-surface-variant text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">File</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Doc ID</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Type</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Size</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Batch</th>
                  <th className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-semibold">Last Updated (UTC)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container">
                {recentUploads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-[var(--spacing-space-md)] px-[var(--spacing-space-md)] text-on-surface-variant">
                      {loading ? 'Loading…' : 'No uploads found yet.'}
                    </td>
                  </tr>
                ) : recentUploads.map((u) => {
                  const batch = batchById.get(u.doc_id)
                  const batchLabel = !batch ? 'not processed' : batch.ready_to_index ? 'ready to index' : batch.has_result ? 'extracted' : 'incomplete'
                  const badgeClass = !batch ? 'bg-surface-container-high text-primary' : batch.ready_to_index ? 'bg-tertiary-container text-on-tertiary-container' : batch.has_result ? 'bg-secondary-fixed text-on-secondary-fixed' : 'bg-surface-container-high text-primary'
                  return (
                    <tr key={u.doc_id} className="hover:bg-surface-container-low transition-colors">
                      <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                        <div className="text-[13px] leading-[18px] tracking-[0.01em] font-semibold text-primary">{u.filename}</div>
                      </td>
                      <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px] text-on-surface-variant">{u.doc_id}</td>
                      <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                        <span className="px-[var(--spacing-space-xs)] py-0.5 rounded-[var(--radius-sm)] bg-surface-container-highest text-primary text-[11px] leading-[16px] tracking-[0.08em] font-bold uppercase">{u.ext}</span>
                      </td>
                      <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px] text-on-surface-variant">{formatBytes(u.bytes ?? 0)}</td>
                      <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)]">
                        <span className={`px-[var(--spacing-space-sm)] py-0.5 rounded-[var(--radius-sm)] text-[12px] leading-[16px] tracking-[0.02em] font-medium ${badgeClass}`}>{batchLabel}</span>
                      </td>
                      <td className="py-[var(--spacing-space-sm)] px-[var(--spacing-space-md)] font-mono text-[12px] leading-[16px] text-on-surface-variant">{u.modified_at ? u.modified_at.replace('T', ' ').replace('Z', '') : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}