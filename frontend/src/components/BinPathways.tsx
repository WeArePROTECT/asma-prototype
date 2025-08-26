import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function BinPathways({ binId }: { binId: string }) {
  const q = useQuery({
    queryKey: ["pathways", binId],
    queryFn: () => api.binPathways(binId),
  });

  if (q.isLoading) return <div className="text-sm muted">Loading pathways…</div>;
  if (q.error) return <div className="text-sm error">Failed to load pathways.</div>;
  if (!q.data) return null;

  const items = q.data.pathways.slice(0, 24);

  return (
    <div className="ab-card">
      <div className="title">Pathways</div>
      <div className="chips">
        {items.map((p, i) => (
          <span className="chip" key={i} title={p.evidence ? JSON.stringify(p.evidence) : ""}>
            <span>{p.pathway}</span>
            {p.score != null && <span className="score">{p.score}</span>}
          </span>
        ))}
        {!items.length && <span className="muted text-sm">No pathways listed.</span>}
      </div>
    </div>
  );
}
