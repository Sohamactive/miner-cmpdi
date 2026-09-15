import { NavLink } from 'react-router-dom'
import { navItems } from '@/data/mockData'

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-[136px] bottom-0 w-64 bg-surface-container-lowest shadow-[0_1px_8px_rgba(0,0,0,0.04)] flex flex-col justify-between p-[var(--spacing-space-md)] z-30">
      <div className="flex flex-col gap-[var(--spacing-space-md)]">
        <div className="text-[11px] leading-[16px] tracking-[0.08em] font-bold text-outline uppercase px-[var(--spacing-space-sm)]">
          Geological Operational Rail
        </div>
        <nav className="flex flex-col gap-[var(--spacing-space-xs)] text-[13px] leading-[18px] tracking-[0.01em] font-semibold">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-[var(--spacing-space-sm)] px-[var(--spacing-space-sm)] py-[var(--spacing-space-xs)] rounded-[var(--radius-sm)] transition-colors ${
                  isActive
                    ? 'bg-primary-container text-on-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-high'
                }`
              }
            >
              <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
              <span>{item.sidebarLabel}</span>
            </NavLink>
          ))}
        </nav>
      </div>
      {/* System Telemetry Widget */}
      <div className="bg-surface-container-low p-[var(--spacing-space-sm)] rounded-[var(--radius-sm)] flex flex-col gap-[var(--spacing-space-xs)] font-mono text-[12px] leading-[16px]">
        <div className="text-[11px] leading-[16px] tracking-[0.08em] font-bold text-primary">System Telemetry</div>
        <div className="flex justify-between text-on-surface-variant">
          <span>Qdrant Nodes</span>
          <span className="text-tertiary-container font-semibold">6/6 UP</span>
        </div>
        <div className="flex justify-between text-on-surface-variant">
          <span>Sync Latency</span>
          <span>42 ms</span>
        </div>
      </div>
    </aside>
  )
}
