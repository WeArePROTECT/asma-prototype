import React from "react";
import { useCart } from "../cart/CartContext";
import { api } from "../lib/api";

export default function FormulationBuilder() {
  const { isolates, prebiotics, setPrebiotics, removeIsolate, clear } = useCart();
  const [pb, setPB] = React.useState<string[]>(prebiotics);
  const [score, setScore] = React.useState<number | null>(null);
  const [notes, setNotes] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => setPB(prebiotics), [prebiotics]);

  async function preview() {
    setLoading(true);
    try {
      const res = await api.previewFormulation({ organisms: isolates, prebiotics: pb });
      setScore(res.score_predicted ?? null);
      setNotes(Array.isArray(res.notes) ? res.notes : []);
    } finally { setLoading(false); }
  }

  function exportCSV() {
    const rows = [["isolate_id"], ...isolates.map(id => [id])];
    if (score != null) rows.push(["score_predicted", String(score)]);
    const text = rows.map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "formulation.csv"; a.click();
    URL.revokeObjectURL(a.href);
  }
  function copyJSON() {
    const payload = { organisms: isolates, prebiotics: pb, score_predicted: score, notes };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2)).catch(()=>{});
    alert("Copied JSON to clipboard");
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center">
        <h1 className="text-xl font-semibold">Formulation Builder</h1>
        <div className="ml-auto flex gap-2">
          <button className="border rounded px-2 py-1" onClick={copyJSON} disabled={!isolates.length}>Copy JSON</button>
          <button className="border rounded px-2 py-1" onClick={exportCSV} disabled={!isolates.length}>Export CSV</button>
          <button className="border rounded px-2 py-1" onClick={() => { if (confirm('Clear formulation?')) clear(); }}>Clear</button>
        </div>
      </div>

      <div className="border rounded p-3">
        <div className="font-semibold mb-2">Selected isolates ({isolates.length})</div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {isolates.map(id => (
            <div key={id} className="border rounded px-2 py-1 flex items-center gap-2">
              <span>{id}</span>
              <button className="ml-auto text-xs border rounded px-2 py-0.5" onClick={() => removeIsolate(id)}>×</button>
            </div>
          ))}
          {isolates.length === 0 && <div className="text-sm text-gray-500">Add isolates from the Network view.</div>}
        </div>
      </div>

      <div className="border rounded p-3">
        <div className="font-semibold mb-2">Prebiotics</div>
        <select
          className="border rounded px-2 py-1"
          value={pb[0] ?? ""}
          onChange={(e)=> setPB(e.target.value ? [e.target.value] : [])}
        >
          <option value="">— none —</option>
          <option value="PB001">PB001</option>
          <option value="PB002">PB002</option>
        </select>
      </div>

      <div className="flex gap-2">
        <button className="border rounded px-3 py-1" onClick={preview} disabled={!isolates.length || loading}>
          {loading ? "Scoring…" : "Preview score"}
        </button>
        {score != null && <div className="px-2 py-1 rounded bg-green-50 border text-green-700">Score: <b>{score.toFixed(2)}</b></div>}
      </div>

      {/* Non-debug breakdown card */}
      {notes?.length ? (
        <div className="border rounded p-3">
          <div className="font-semibold mb-1">Breakdown</div>
          <ul className="list-disc ml-5 text-sm">
            {notes.map((n,i)=> <li key={i}>{n}</li>)}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
