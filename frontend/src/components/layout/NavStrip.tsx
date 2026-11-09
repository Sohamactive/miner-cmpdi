import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Ingestion Dashboard' },
  { path: '/reports', label: 'Report Synthesis' },
  { path: '/chat', label: 'Evidence Chat' },
]

export default function NavStrip() {
  return (
    <div className="bg-primary-container text-on-primary">
      <div className="w-full px-[var(--spacing-gutter)] h-10 flex items-center">
        <nav className="flex items-center gap-[var(--spacing-space-xs)] h-full text-[13px] leading-[18px] tracking-[0.01em] font-semibold">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `px-[var(--spacing-space-md)] h-full flex items-center transition-colors ${
                  isActive
                    ? 'bg-secondary text-on-secondary'
                    : 'text-on-primary hover:bg-primary'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}
