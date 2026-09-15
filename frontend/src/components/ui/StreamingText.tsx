export function StreamingText({ text, streaming }: { text: string; streaming: boolean }) {
  if (!text && streaming) {
    return <span className="text-ink-faint">Waiting for the first token…</span>;
  }
  return (
    <span className="whitespace-pre-wrap leading-relaxed">
      {text}
      {streaming && (
        <span className="animate-caret ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-cluster align-middle" />
      )}
    </span>
  );
}
