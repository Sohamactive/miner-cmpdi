import { Badge } from "../ui/Badge";
import { SearchInput } from "../ui/SearchInput";

export function PortalHeader() {
  return (
    <div className="flex h-16 items-center justify-between border-b border-border bg-surface px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
          <span className="material-symbols-outlined text-[20px] leading-none">terrain</span>
        </div>
        <div className="leading-tight">
          <p className="text-base font-bold tracking-tight text-ink">M.I.N.E.R.</p>
          <p className="text-[11px] text-ink-faint">Mining Intelligence, Knowledge &amp; Evidence Reporter</p>
        </div>
        <Badge tone="danger" className="ml-2">
          RESTRICTED · OFFICIAL USE
        </Badge>
      </div>

      <SearchInput placeholder="Search archives, doc IDs, seams…" className="w-80" />

      <div className="flex items-center gap-3">
        <button className="relative rounded-full p-2 text-ink-muted hover:bg-surface-raised">
          <span className="material-symbols-outlined text-[20px] leading-none">notifications</span>
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-danger" />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cluster-bg text-sm font-semibold text-cluster">
            RK
          </div>
          <div className="leading-tight">
            <p className="text-sm font-medium text-ink">R. Kulkarni</p>
            <p className="text-[11px] text-ink-faint">Reviewing Officer</p>
          </div>
        </div>
      </div>
    </div>
  );
}
