import type { SecondaryTopic } from "../../types";

export function TopicChip({ topic }: { topic: SecondaryTopic }) {
  return (
    <button className="flex items-center justify-between gap-3 rounded-xl border border-border bg-surface px-3.5 py-2.5 text-left transition-colors hover:border-border-strong hover:bg-surface-raised">
      <span className="flex items-center gap-2 text-sm font-medium text-ink">
        <span className="material-symbols-outlined text-[18px] leading-none text-ink-muted">
          {topic.icon}
        </span>
        {topic.label}
      </span>
      <span className="flex items-center gap-1 font-data text-xs text-ink-faint">
        {topic.count}
        <span className="material-symbols-outlined text-[16px] leading-none">arrow_forward</span>
      </span>
    </button>
  );
}
