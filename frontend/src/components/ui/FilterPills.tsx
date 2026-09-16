import { cn } from "../../lib/cn";

interface Pill {
  id: string;
  label: string;
}

export function FilterPills({
  pills,
  activeId,
  onSelect,
  className,
}: {
  pills: Pill[];
  activeId: string;
  onSelect: (id: string) => void;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {pills.map((pill) => {
        const active = pill.id === activeId;
        return (
          <button
            key={pill.id}
            onClick={() => onSelect(pill.id)}
            className={cn(
              "rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
              active
                ? "border-primary bg-primary text-white"
                : "border-border bg-surface text-ink-muted hover:border-border-strong hover:text-ink",
            )}
          >
            {pill.label}
          </button>
        );
      })}
    </div>
  );
}
