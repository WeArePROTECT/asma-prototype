import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function SampleAbundance({ sampleId }: { sampleId: string }) {
  const q = useQuery({
    queryKey: ["abundance", sampleId],
    queryFn: () => api.sampleAbundance(sampleId),
  });

  if (q.isLoading) return <div className="text-sm muted">Loading abundance…</div>;
  if (q.error) return <div className="text-sm error">Failed to load abundance.</div>;
  if (!q.data) return null;

  const rows = q.data.bins
    .slice()
    .sort((a, b) => (b.abundance ?? 0) - (a.abundance ?? 0))
    .slice(0, 12);

  const max = Math.max(1, ...rows.map((r) => r.abundance || 0));

  return (
    <div className="ab-card">
      <div className="title">Sample abundance</div>
      <div className="sub">
        Top {rows.length} bins — total {q.data.total_abundance}
      </div>
      <div className="list">
        {rows.map((r) => (
          <div key={r.bin_id} className="row" title={r.taxonomy || r.bin_id}>
            <div className="label">{r.taxonomy || r.bin_id}</div>
            <div className="bar-wrap">
              <div
                className="bar-fill"
                style={{ width: `${(100 * (r.abundance || 0)) / max}%` }}
              />
            </div>
            <div className="val">{(r.abundance ?? 0).toFixed(2)}</div>
          </div>
        ))}
        {!rows.length && <div className="muted text-sm">No abundance values.</div>}
      </div>
    </div>
  );
}
