import { NavLink } from "react-router-dom";
import { cn } from "../../lib/cn";

interface NavTab {
  label: string;
  path?: string; // omitted => not yet implemented
  icon: string;
}

const TABS: NavTab[] = [
  { label: "Dashboard & Ingestion", icon: "dashboard" },
  { label: "AI Query & Evidence", path: "/ai-query", icon: "psychology" },
  { label: "Topic Explorer", path: "/topics", icon: "hub" },
  { label: "Human Review", icon: "fact_check" },
  { label: "Report Synthesis", icon: "description" },
];

export function NavStrip() {
  return (
    <nav className="flex h-11 items-center gap-1 border-b border-border bg-surface px-6">
      {TABS.map((tab) =>
        tab.path ? (
          <NavLink
            key={tab.label}
            to={tab.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-1.5 rounded-t-lg border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "border-secondary text-ink"
                  : "border-transparent text-ink-muted hover:text-ink",
              )
            }
          >
            <span className="material-symbols-outlined text-[18px] leading-none">{tab.icon}</span>
            {tab.label}
          </NavLink>
        ) : (
          <span
            key={tab.label}
            title="Not yet implemented in this build"
            className="flex cursor-not-allowed items-center gap-1.5 rounded-t-lg border-b-2 border-transparent px-3.5 py-2.5 text-sm font-medium text-ink-faint/60"
          >
            <span className="material-symbols-outlined text-[18px] leading-none">{tab.icon}</span>
            {tab.label}
          </span>
        ),
      )}
    </nav>
  );
}
