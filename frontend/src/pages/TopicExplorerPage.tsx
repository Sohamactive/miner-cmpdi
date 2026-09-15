export default function TopicExplorerPage() {
  return (
    <div className="w-full px-[var(--spacing-gutter)] py-[var(--spacing-space-lg)]">
      <div className="max-w-3xl mx-auto text-center py-[var(--spacing-space-xl)]">
        <div className="w-16 h-16 rounded-[var(--radius-lg)] bg-primary-container flex items-center justify-center mx-auto mb-[var(--spacing-space-md)]">
          <span className="material-symbols-outlined text-on-primary text-[32px]">hub</span>
        </div>
        <h1 className="text-[24px] leading-[32px] font-bold text-primary tracking-tight mb-[var(--spacing-space-sm)]">
          Topic Explorer &amp; Mining Clusters
        </h1>
        <p className="text-[14px] leading-[22px] text-on-surface-variant mb-[var(--spacing-space-md)]">
          HDBSCAN cluster engine with interactive topic matrix, semantic topic space visualization,
          UMAP 2D projections, and extracted archives dossier stream.
        </p>
        <div className="inline-flex items-center gap-[var(--spacing-space-xs)] px-[var(--spacing-space-md)] py-[var(--spacing-space-xs)] bg-surface-container-high rounded-[var(--radius-sm)] text-[12px] leading-[16px] font-mono text-on-surface-variant">
          <span className="w-2 h-2 rounded-full bg-secondary-fixed-dim animate-pulse"></span>
          Module under development — Your friend's scope
        </div>
      </div>
    </div>
  )
}
