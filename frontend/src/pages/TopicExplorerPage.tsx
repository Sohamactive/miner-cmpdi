import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { FilterPills } from "../components/ui/FilterPills";
import { TopicCard } from "../components/ui/TopicCard";
import { TopicChip } from "../components/ui/TopicChip";
import { fetchTopicExplorerBundle, type TopicExplorerBundle } from "../api/topics";

export function TopicExplorerPage() {
  const [bundle, setBundle] = useState<TopicExplorerBundle | null>(null);
  const [domain, setDomain] = useState("all");
  const [activeTopicId, setActiveTopicId] = useState<string | null>(null);
  const [reclustering, setReclustering] = useState(false);

  useEffect(() => {
    fetchTopicExplorerBundle().then(setBundle);
  }, []);

  const visibleTopics = useMemo(() => {
    if (!bundle) return [];
    return domain === "all" ? bundle.topics : bundle.topics.filter((t) => t.domain === domain);
  }, [bundle, domain]);

  const activeArchives = useMemo(() => {
    if (!bundle) return [];
    return activeTopicId
      ? bundle.archives.filter((a) => a.topicId === activeTopicId)
      : bundle.archives;
  }, [bundle, activeTopicId]);

  const handleRecluster = () => {
    setReclustering(true);
    window.setTimeout(() => setReclustering(false), 1400);
  };

  if (!bundle) {
    return <div className="p-6 text-sm text-ink-muted">Loading topic clusters…</div>;
  }

  const activeTopic = bundle.topics.find((t) => t.id === activeTopicId) ?? null;

  return (
    <div className="grid grid-cols-12 gap-6 p-6">
      <section className="col-span-12 flex flex-col gap-5 lg:col-span-8">
        {/* Command bar */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-data text-xs text-ink-faint">Archives / Topic Explorer</p>
            <h1 className="text-lg font-bold text-ink">Semantic Topic Clusters</h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone={reclustering ? "warning" : "info"} icon={reclustering ? "sync" : "hub"}>
              HDBSCAN {reclustering ? "reclustering…" : "engine idle"}
            </Badge>
            <Button size="sm" variant="ghost" icon="refresh" onClick={handleRecluster} disabled={reclustering}>
              Re-cluster
            </Button>
          </div>
        </div>

        <FilterPills pills={bundle.domains} activeId={domain} onSelect={setDomain} />

        {/* Topic cards grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {visibleTopics.map((topic) => (
            <TopicCard
              key={topic.id}
              topic={topic}
              active={topic.id === activeTopicId}
              onClick={() => setActiveTopicId(topic.id === activeTopicId ? null : topic.id)}
            />
          ))}
        </div>

        {/* Secondary topic matrix */}
        <div>
          <p className="mb-2 font-data text-[11px] uppercase tracking-wide text-ink-faint">
            Secondary Topic Matrix
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {bundle.secondaryTopics.map((t) => (
              <TopicChip key={t.id} topic={t} />
            ))}
          </div>
        </div>

        {/* Semantic topic space */}
        <div className="rounded-2xl border border-border bg-surface p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="font-data text-[11px] uppercase tracking-wide text-ink-faint">
              Semantic Topic Space — UMAP 2D
            </p>
            <span className="text-xs text-ink-faint">Bubble size = mention density</span>
          </div>
          <ClusterMap points={bundle.clusterPoints} activeTopicId={activeTopicId} onSelect={setActiveTopicId} />
        </div>
      </section>

      {/* Extracted archives sidebar */}
      <aside className="col-span-12 flex flex-col gap-3 lg:col-span-4">
        <div className="flex items-center justify-between">
          <p className="font-data text-[11px] uppercase tracking-wide text-ink-faint">
            Extracted Archives {activeTopic && `· ${activeTopic.title}`}
          </p>
          {activeTopicId && (
            <button onClick={() => setActiveTopicId(null)} className="text-xs text-cluster hover:underline">
              Clear
            </button>
          )}
        </div>

        <div className="flex flex-col gap-3">
          {activeArchives.map((doc) => (
            <div key={doc.id} className="rounded-xl border border-border bg-surface p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold text-ink">{doc.title}</h3>
                <span className="shrink-0 font-data text-[11px] text-vector">d={doc.distance.toFixed(2)}</span>
              </div>
              <p className="mt-1 text-xs text-ink-muted">{doc.excerpt}</p>
              <div className="mt-3 flex items-center justify-between">
                <span className="font-data text-[11px] text-ink-faint">{doc.date}</span>
                <Link
                  to="/ai-query"
                  className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                >
                  Load in AI Reader
                  <span className="material-symbols-outlined text-[15px] leading-none">arrow_forward</span>
                </Link>
              </div>
            </div>
          ))}
          {activeArchives.length === 0 && (
            <p className="text-sm text-ink-muted">No archives match this topic yet.</p>
          )}
        </div>
      </aside>
    </div>
  );
}

function ClusterMap({
  points,
  activeTopicId,
  onSelect,
}: {
  points: { id: string; x: number; y: number; radius: number; topicId: string; label: string }[];
  activeTopicId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <svg viewBox="0 0 400 260" className="h-64 w-full">
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="var(--color-border)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="400" height="260" fill="url(#grid)" />
      {points.map((p) => {
        const active = p.topicId === activeTopicId;
        return (
          <g
            key={p.id}
            onClick={() => onSelect(p.topicId)}
            className="cursor-pointer"
            style={{ transition: "opacity 200ms" }}
            opacity={activeTopicId && !active ? 0.35 : 1}
          >
            <circle
              cx={p.x}
              cy={p.y}
              r={p.radius}
              fill="var(--color-cluster-bg)"
              stroke="var(--color-cluster)"
              strokeWidth={active ? 2.5 : 1.5}
            />
            <text
              x={p.x}
              y={p.y + p.radius + 14}
              textAnchor="middle"
              fontSize="10"
              fontFamily="var(--font-mono)"
              fill="var(--color-ink-muted)"
            >
              {p.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
