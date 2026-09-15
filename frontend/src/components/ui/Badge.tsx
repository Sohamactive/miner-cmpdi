import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info" | "cluster";

const TONE_STYLES: Record<BadgeTone, string> = {
  neutral: "bg-surface-raised text-ink-muted border-border-strong",
  success: "bg-success-bg text-success border-success/20",
  warning: "bg-warning-bg text-warning border-warning/20",
  danger: "bg-danger-bg text-danger border-danger/20",
  info: "bg-info-bg text-info border-info/20",
  cluster: "bg-cluster-bg text-cluster border-cluster/20",
};

export function Badge({
  children,
  tone = "neutral",
  className,
  icon,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
  icon?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium leading-none font-data",
        TONE_STYLES[tone],
        className,
      )}
    >
      {icon && <span className="material-symbols-outlined text-[14px] leading-none">{icon}</span>}
      {children}
    </span>
  );
}
