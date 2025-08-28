import React, { useEffect, useMemo, useState } from "react";
import { useCart } from "../cart/CartContext";

type PreviewResp =
  | { score_predicted: number; notes?: string[] } // normal
  | {
      score_predicted: number;
      notes?: string[];
      organisms: string[];
      sum_complementarity: number;
      sum_inhibition: number;
      sum_competition: number;
      avg_inhibition: number;
      counts: { complementarity: number; inhibition: number; competition: number };
      edges_included: { complementarity: any[]; inhibition_or_competition: any[] };
    }; // debug

const API_BASE =
  (window as any).__ASMA_API__ ||
  (import.meta as any).env?.VITE_API_BASE ||
  "http://127.0.0.1:8000";

async function fetchPrebiotics() {
  const r = await fetch(`${API_BASE}/prebiotics`);
  if (!r.ok) throw new Error("prebiotics fetch failed");
  return (await r.json()) as { prebiotic_id: string; name?: string }[];
}

async function previewScore(payload: { organisms: string[]; prebiotics?: string[] }, debug: boolean) {
  const url = `${API_BASE}/formulations/preview${debug ? "?debug=1" : ""}`;
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`preview failed: ${r.status}`);
  return (await r.json()) as PreviewResp;
}

export default function Formulate() {
  const { items, removeIsolate, clear } = useCart();
  const [prebiotics, setPrebiotics] = useState<string[]>([]);
  const [allPrebiotics, setAllPrebiotics] = useState<{ id: string; label: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState(false);
  const [result, setResult] = useState<PreviewResp | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const raw = await fetchPrebiotics();
        if (!alive) return;
        setAllPrebiotics(
          raw.map((r) => ({
            id: (r as any).prebiotic_id || (r as any).id || JSON.stringify(r),
            label: (r as any).name || (r as any).prebiotic_id || "Prebiotic",
          }))
        );
      } catch (e: any) {
        console.warn(e);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const canScore = items.length > 0;

  async function onPreview() {
    setErr(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await previewScore({ organisms: items, prebiotics }, debug);
      setResult(res);
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 980, margin: "0 auto", padding: "16px" }}>
      <h1 className="text-2xl font-bold mb-2">Formulation Builder</h1>
      <p className="text-gray-600 mb-4">
        Select isolates in the network (Add to formulation), then preview a composite score with optional prebiotics.
      </p>

      <div className="grid" style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16 }}>
        {/* Left: isolate list */}
        <div className="border rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold">Selected isolates</h2>
            <button className="border rounded px-2 py-1" onClick={() => clear()} disabled={!items.length}>
              Clear all
            </button>
          </div>
          {!items.length ? (
            <div className="text-gray-500">Nothing yet—go to the Network and click “Add to formulation”.</div>
          ) : (
            <ul className="divide-y">
              {items.map((id) => (
                <li key={id} className="py-1 flex items-center justify-between">
                  <span>{id}</span>
                  <button className="text-red-600" onClick={() => removeIsolate(id)}>
                    remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Right: prebiotics + scoring */}
        <div className="border rounded p-3">
          <h2 className="font-semibold mb-2">Prebiotics</h2>
          <div className="space-y-1 mb-3">
            {allPrebiotics.length === 0 ? (
              <div className="text-gray-500">No prebiotics listed.</div>
            ) : (
              allPrebiotics.map((p) => (
                <label key={p.id} className="flex items-center gap-2 block">
                  <input
                    type="checkbox"
                    checked={prebiotics.includes(p.id)}
                    onChange={(e) => {
                      if (e.target.checked) setPrebiotics((x) => Array.from(new Set([...x, p.id])));
                      else setPrebiotics((x) => x.filter((v) => v !== p.id));
                    }}
                  />
                  {p.label} <span className="text-gray-500 text-xs">({p.id})</span>
                </label>
              ))
            )}
          </div>

          <label className="flex items-center gap-2 mb-2">
            <input type="checkbox" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
            Show scoring breakdown (debug)
          </label>

          <button className="border rounded px-3 py-1" onClick={onPreview} disabled={!canScore || loading}>
            {loading ? "Scoring…" : "Preview score"}
          </button>

          {err && <div className="mt-2 text-red-600 text-sm">{err}</div>}

          {result && (
            <div className="mt-3">
              <div className="text-lg">
                <span className="font-semibold">Score:</span>{" "}
                {"score_predicted" in result ? (result as any).score_predicted.toFixed(2) : "—"}
              </div>
              {"notes" in result && (result as any).notes?.length ? (
                <ul className="text-sm mt-1 list-disc pl-5">
                  {(result as any).notes.map((n: string, i: number) => (
                    <li key={i}>{n}</li>
                  ))}
                </ul>
              ) : null}

              {/* Debug table */}
              {"sum_complementarity" in result && (
                <div className="mt-3 text-sm">
                  <div className="font-semibold mb-1">Breakdown</div>
                  <table className="min-w-full text-sm">
                    <tbody>
                      <tr><td className="pr-2 text-gray-600">Sum complementarity</td><td>{(result as any).sum_complementarity}</td></tr>
                      <tr><td className="pr-2 text-gray-600">Sum inhibition</td><td>{(result as any).sum_inhibition}</td></tr>
                      <tr><td className="pr-2 text-gray-600">Sum competition</td><td>{(result as any).sum_competition}</td></tr>
                      <tr><td className="pr-2 text-gray-600">Avg inhibition</td><td>{(result as any).avg_inhibition}</td></tr>
                      <tr><td className="pr-2 text-gray-600">Counts</td><td>
                        c={(result as any).counts?.complementarity ?? 0}, i={(result as any).counts?.inhibition ?? 0}, comp={(result as any).counts?.competition ?? 0}
                      </td></tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
