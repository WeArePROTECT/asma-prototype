import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type Props = {
  binId: string;
  sampleId?: string;
  abundance?: number | null;
};

/**
 * Shows a single abundance bar for the selected bin.
 * - If `abundance` is provided, uses it directly (fast path).
 * - Otherwise (or if you want to confirm), fetches /samples/{sampleId}/abundance and finds the bin.
 */
export default function BinAbundance({ binId, sampleId, abundance }: Props) {
  const needsFetch = (abundance == null) && !!sampleId;

  const q = useQuery({
    queryKey: ["abundance-for-bin", sampleId, binId],
    queryFn: () => api.sampleAbundance(sampleId as string),
    enabled: needsFetch,
  });

  const value =
    (abundance ?? null) ??
    (q.data?.bins.find((b: any) => b.bin_id === binId)?.abundance ?? null);

  const display = typeof value === "number" ? value : 0;
  const widthPct = Math.max(0, Math.min(100, 100 * display));

  return (
    <div className="ab-card" style={{ marginTop: 8 }}>
      <div className="title">Abundance</div>
      <div className="sub">Bin {binId}{sampleId ? ` in ${sampleId}` : ""}</div>
      {!needsFetch && abundance == null && (
        <div className="muted text-sm" style={{ marginBottom: 6 }}>
          (No direct abundance in row; fetching sample to estimate…)
        </div>
      )}
      {q.isLoading && needsFetch ? (
        <div className="muted text-sm">Loading…</div>
      ) : (
        <div className="row" title={`abundance: ${display.toFixed(2)}`}>
          <div className="bar-wrap">
            <div className="bar-fill" style={{ width: `${widthPct}%` }} />
          </div>
          <div className="val">{display.toFixed(2)}</div>
        </div>
      )}
    </div>
  );
}
