import { cn } from "../../lib/cn";

export function ConfidenceMeter({
  label,
  value,
  className,
}: {
  label: string;
  value: number; // 0-1
  className?: string;
}) {
  const pct = Math.round(value * 100);
  const tone = pct >= 85 ? "bg-success" : pct >= 60 ? "bg-secondary" : "bg-danger";

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span className="w-32 shrink-0 text-xs font-medium text-ink-muted">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-raised">
        <div className={cn("h-full rounded-full transition-all duration-500", tone)} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 shrink-0 text-right font-data text-xs text-ink">{pct}%</span>
    </div>
  );
}
