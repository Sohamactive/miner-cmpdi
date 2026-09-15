import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { cn } from "../../lib/cn";

const RAIL_ITEMS = [
  { label: "AI Query", path: "/ai-query", icon: "psychology" },
  { label: "Topics", path: "/topics", icon: "hub" },
];

export function Sidebar() {
  const [latencyMs, setLatencyMs] = useState(42);

  useEffect(() => {
    const id = window.setInterval(() => {
      setLatencyMs(34 + Math.round(Math.random() * 20));
    }, 2500);
    return () => window.clearInterval(id);
  }, []);

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex-1 p-4">
        <p className="mb-2 px-2 font-data text-[11px] uppercase tracking-wide text-ink-faint">
          Geological Operational Rail
        </p>
        <nav className="flex flex-col gap-1">
          {RAIL_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-secondary/20 text-ink" : "text-ink-muted hover:bg-surface-raised hover:text-ink",
                )
              }
            >
              <span className="material-symbols-outlined text-[19px] leading-none">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="m-4 rounded-xl border border-border bg-surface-raised p-4">
        <p className="mb-3 flex items-center gap-1.5 font-data text-[11px] uppercase tracking-wide text-ink-faint">
          <span className="h-1.5 w-1.5 animate-pulse-ring rounded-full bg-info" />
          System Telemetry
        </p>
        <dl className="space-y-2.5 font-data text-xs">
          <div className="flex items-center justify-between">
            <dt className="text-ink-muted">Qdrant Nodes</dt>
            <dd className="font-semibold text-ink">4 / 4 online</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-ink-muted">Sync Latency</dt>
            <dd className="font-semibold text-ink">{latencyMs}ms</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-ink-muted">Vector Index</dt>
            <dd className="font-semibold text-ink">1.42M</dd>
          </div>
        </dl>
      </div>
    </aside>
  );
}
