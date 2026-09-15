import { useEffect, useState } from "react";

export function NationalEmblemBar() {
  const [now, setNow] = useState(new Date());
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [fontStep, setFontStep] = useState(1); // 0=A-, 1=A, 2=A+

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000 * 30);
    return () => window.clearInterval(id);
  }, []);

  const ist = now.toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="flex h-9 items-center justify-between bg-emblem px-4 text-xs text-emblem-ink">
      <span className="truncate">
        {lang === "en"
          ? "Government of India · Ministry of Coal · CMPDI"
          : "भारत सरकार · कोयला मंत्रालय · सीएमपीडीआई"}
      </span>

      <div className="flex items-center gap-4 font-data">
        <div className="flex items-center gap-1" aria-label="Text size">
          {(["A-", "A", "A+"] as const).map((label, i) => (
            <button
              key={label}
              onClick={() => setFontStep(i)}
              className={`rounded px-1.5 py-0.5 transition-colors ${
                fontStep === i ? "bg-emblem-ink/20 text-white" : "text-emblem-ink/70 hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={() => setLang((l) => (l === "en" ? "hi" : "en"))}
          className="text-emblem-ink/70 hover:text-white"
        >
          {lang === "en" ? "हिन्दी" : "English"}
        </button>

        <span className="text-emblem-ink/70">IST {ist}</span>
      </div>
    </div>
  );
}
