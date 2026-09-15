import type { Topic } from "../../types";
import { cn } from "../../lib/cn";

export function TopicCard({
  topic,
  active,
  onClick,
}: {
  topic: Topic;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "group flex flex-col gap-3 rounded-2xl border p-5 text-left transition-all",
        active
          ? "border-cluster bg-cluster-bg/60 shadow-sm"
          : "border-border bg-surface hover:border-border-strong hover:shadow-sm",
      )}
    >
      <div className="flex items-start justify-between">
        <span
          className={cn(
            "flex h-11 w-11 items-center justify-center rounded-xl",
            active ? "bg-cluster text-white" : "bg-surface-raised text-primary",
          )}
        >
          <span className="material-symbols-outlined text-[22px] leading-none">{topic.icon}</span>
        </span>
        <span className="font-data text-xs text-ink-faint">{topic.mentionCount} mentions</span>
      </div>

      <div>
        <h3 className="text-base font-semibold text-ink">{topic.title}</h3>
        <p className="mt-1 text-sm leading-snug text-ink-muted">{topic.summary}</p>
      </div>

      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surface-raised">
        <div
          className="h-full rounded-full bg-cluster transition-all"
          style={{ width: `${topic.progress}%` }}
        />
      </div>
    </button>
  );
}
