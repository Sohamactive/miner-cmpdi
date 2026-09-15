import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

export function SearchInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink-muted focus-within:border-primary",
        className,
      )}
    >
      <span className="material-symbols-outlined text-[18px] leading-none text-ink-faint">search</span>
      <input
        className="w-full bg-transparent text-ink outline-none placeholder:text-ink-faint"
        {...rest}
      />
    </div>
  );
}
