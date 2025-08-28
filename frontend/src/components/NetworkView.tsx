import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { useCart } from "../cart/CartContext";

type NetNode = { id: string; label?: string; x: number; y: number };
type NetEdge = { source: string; target: string; type?: string; score?: number };

const W = 860;
const H = 520;
const R = 14;

const EDGE_COLORS: Record<string, string> = {
  complementarity: "#2563eb",
  cooccurrence: "#10b981",
  inhibition: "#ef4444",
  competition: "#6b7280", // NEW: neutral gray
};

function circleLayout(ids: string[]): Record<string, {x:number;y:number}> {
  const n = Math.max(1, ids.length);
  const cx = W/2, cy = H/2;
  const rad = Math.min(W,H)/2 - 40;
  const out: Record<string, {x:number;y:number}> = {};
  ids.forEach((id, i) => {
    const t = (2*Math.PI*i)/n;
    out[id] = { x: cx + rad*Math.cos(t), y: cy + rad*Math.sin(t) };
  });
  return out;
}

function distPointToSegment(px:number, py:number, ax:number, ay:number, bx:number, by:number) {
  const vx = bx - ax, vy = by - ay;
  const wx = px - ax, wy = py - ay;
  const vv = vx*vx + vy*vy;
  let t = vv === 0 ? 0 : (wx*vx + wy*vy) / vv;
  t = Math.max(0, Math.min(1, t));
  const cx = ax + t*vx, cy = ay + t*vy;
  const dx = px - cx, dy = py - cy;
  return { d: Math.sqrt(dx*dx + dy*dy), cx, cy, t };
}

export default function NetworkView() {
  const [focus, setFocus] = useState<string>("");
  const [edgeType, setEdgeType] = useState<string>("All");
  const [showLegend, setShowLegend] = useState<boolean>(true);
  const [showScores, setShowScores] = useState<boolean>(true);

  const [hoverNode, setHoverNode] = useState<{id:string;x:number;y:number}|null>(null);
  const [hoverEdge, setHoverEdge] = useState<{e:NetEdge;x:number;y:number}|null>(null);

  const [selected, setSelected] = useState<string | undefined>(undefined);
  const [details, setDetails] = useState<Record<string, any>>({}); // cache by id
  const { addIsolate } = useCart();

  const [state, setState] = useState<{nodes:NetNode[];edges:NetEdge[]}>({nodes:[],edges:[]});
  const [loading, setLoading] = useState(false);

  async function loadGraph(targetId?: string) {
    setLoading(true);
    try {
      let res;
      // If a focus ID exists, query by it; otherwise pull a small global sample
      if (targetId) {
        res = await api.network({ isolateId: targetId, type: edgeType });
      } else {
        res = await api.network({ type: edgeType, maxNeighbors: 60 });
      }
      const ids = Array.from(new Set([
        ...res.nodes.map(n=>n.id),
        ...res.edges.flatMap(e=>[e.source, e.target])
      ]));
      const pos = circleLayout(ids);
      const nodes: NetNode[] = ids.map(id => ({ id, label: res.nodes.find(n=>n.id===id)?.label, x: pos[id].x, y: pos[id].y }));
      setState({ nodes, edges: res.edges });
      if (!targetId && ids.length) {
        setSelected(ids[0]); // select first node so Add-to-formulation is enabled
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadGraph(focus || undefined); /* eslint-disable-next-line */ }, [focus, edgeType]);

  // Prefetch details for selected & hover nodes (lightweight)
  useEffect(() => {
    const id = selected ?? hoverNode?.id;
    if (!id || details[id]) return;
    let alive = true;
    (async () => {
      try { const d = await api.isolate(id); if (alive) setDetails(prev => ({...prev, [id]: d})); }
      catch { /* ignore */ }
    })();
    return () => { alive = false; };
  }, [selected, hoverNode]);

  // canvas draw
  const canvasRef = useRef<HTMLCanvasElement|null>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = W * dpr; canvas.height = H * dpr; canvas.style.width = W+"px"; canvas.style.height = H+"px";
    ctx.setTransform(dpr,0,0,dpr,0,0);
    
    function draw() {
      ctx.clearRect(0,0,W,H);
      // edges
      state.edges.forEach(e => {
        const a = state.nodes.find(n=>n.id===e.source);
        const b = state.nodes.find(n=>n.id===e.target);
        if (!a || !b) return;
        const hovered = !!(hoverEdge && hoverEdge.e === e);
        const color = EDGE_COLORS[e.type||"cooccurrence"] || "#999";
        const width = hovered ? 3 : 1.5 + Math.max(0, Math.min(1, (e.score ?? 0))) * 1.2;
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.globalAlpha = hovered ? 1.0 : 0.9;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        // optional score labels at midpoint
        if (showScores) {
          const mx = (a.x + b.x)/2, my = (a.y + b.y)/2;
          const labelType = (e.type || "edge");
          const text = labelType + (e.score != null ? ` ${Number(e.score).toFixed(2)}` : "");
          // white halo for readability
          ctx.font = "11px system-ui, -apple-system, Segoe UI, Roboto";
          ctx.fillStyle = "white";
          const pad = 2;
          const tw = ctx.measureText(text).width;
          ctx.fillRect(mx - tw/2 - pad, my - 10, tw + pad*2, 14);
          ctx.fillStyle = "#111";
          ctx.fillText(text, mx - tw/2, my + 1);
        }
      });
      // nodes
      state.nodes.forEach(n => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, R, 0, Math.PI*2);
        ctx.fillStyle = (n.id === selected) ? "#111827" : "#374151";
        ctx.fill();
        ctx.fillStyle = "#111";
        ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto";
        const label = n.label || n.id;
        ctx.fillText(label, n.x+R+4, n.y+4);
      });
    }
    draw();
  }, [state, selected, hoverEdge, showScores]);

  function nearestNode(x: number, y: number): NetNode | null {
    let best: NetNode | null = null, bestDist = 1e9;
    for (const n of state.nodes) {
      const dx = n.x - x, dy = n.y - y;
      const d2 = dx*dx + dy*dy;
      if (d2 < bestDist && d2 <= (R*R)*2.5) { best = n; bestDist = d2; }
    }
    return best;
  }

  function nearestEdge(x:number, y:number): {e:NetEdge; x:number; y:number} | null {
    let best: {e:NetEdge; x:number; y:number} | null = null;
    let bestD = 8; // px threshold
    for (const e of state.edges) {
      const a = state.nodes.find(n=>n.id===e.source);
      const b = state.nodes.find(n=>n.id===e.target);
      if (!a || !b) continue;
      const { d, cx, cy, t } = distPointToSegment(x,y,a.x,a.y,b.x,b.y);
      if (d < bestD && t > 0.05 && t < 0.95) { // ignore near endpoints to avoid clashing with nodes
        bestD = d; best = { e, x: cx, y: cy };
      }
    }
    return best;
  }

  function onCanvasMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const n = nearestNode(x,y);
    if (n) {
      setHoverNode({ id: n.id, x, y });
      setHoverEdge(null);
      return;
    }
    setHoverNode(null);
    const edgeHit = nearestEdge(x,y);
    setHoverEdge(edgeHit);
  }

  function onCanvasClick(e: React.MouseEvent<HTMLCanvasElement>) {
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const n = nearestNode(x,y);
    if (n) setSelected(n.id);
  }

  const hoverNodeDetails = hoverNode ? details[hoverNode.id] : null;
  const selectedDetails = selected ? details[selected] : null;
  const nameFor = (id:string) => {
    const d = details[id];
    const label = state.nodes.find(n=>n.id===id)?.label;
    return (d?.taxonomy ?? d?.taxid_genus ?? label ?? id) + ` (${id})`;
  };

  // Build hover text for edge (with direction icon for inhibition)
  const edgeHoverText = hoverEdge ? (() => {
    const t = hoverEdge.e.type || "edge";
    const s = (hoverEdge.e.score != null) ? Number(hoverEdge.e.score).toFixed(2) : "";
    const a = nameFor(hoverEdge.e.source);
    const b = nameFor(hoverEdge.e.target);
    const arrow = t === "inhibition" ? "→" : "↔";
    return { t, s, a, b, arrow };
  })() : null;

  return (
    <div style={{ display: "grid", gridTemplateRows: "auto auto 1fr", gap: 10 }}>
      {/* Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <button className="border rounded px-2 py-1" onClick={() => setSelected(undefined)}>Close</button>
        <input
          placeholder="Isolate focus  e.g., ASMA-346 or I001"
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") loadGraph(e.currentTarget.value || undefined); }}
          className="border rounded px-2 py-1"
          style={{ width: 220 }}
        />
        <label style={{ fontWeight: 600, marginLeft: 8 }}>Edge type</label>
        <select value={edgeType} onChange={(e)=>setEdgeType(e.target.value)} className="border rounded px-2 py-1">
          <option>All</option>
          <option value="complementarity">complementarity</option>
          <option value="cooccurrence">cooccurrence</option>
          <option value="inhibition">inhibition</option>
          <option value="competition">competition</option>
        </select>
        <label style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: 12 }}>
          <input type="checkbox" checked={showLegend} onChange={(e)=>setShowLegend(e.target.checked)} />
          Show legend
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: 12 }}>
          <input type="checkbox" checked={showScores} onChange={(e)=>setShowScores(e.target.checked)} />
          Show scores
        </label>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <button className="border rounded px-2 py-1" onClick={() => selected && addIsolate(selected)} disabled={!selected}>Add to formulation</button>
          <button className="border rounded px-2 py-1" onClick={() => exportPNG()}>Export PNG</button>
          <button className="border rounded px-2 py-1" onClick={() => exportSVG()}>Export SVG</button>
        </div>
      </div>

      {/* Legend */}
      {showLegend && (
        <div style={{ display: "flex", gap: 18, alignItems: "center", fontSize: 13 }}>
          <LegendItem color={EDGE_COLORS.complementarity} label="complementarity" />
          <LegendItem color={EDGE_COLORS.cooccurrence} label="cooccurrence" />
          <LegendItem color={EDGE_COLORS.inhibition} label="inhibition" />
          <LegendItem color={EDGE_COLORS.competition} label="competition" /> {/* NEW */}
        </div>
      )}

      {/* Canvas */}
      <div style={{ position: "relative", border: "1px solid #e5e7eb", borderRadius: 8, background: "#fff" }}>
        <canvas ref={canvasRef} width={W} height={H} onMouseMove={onCanvasMouseMove} onClick={onCanvasClick} />
        {hoverNode && (
          <div style={{ position: "absolute", left: hoverNode.x + 12, top: hoverNode.y + 12, background: "white", border: "1px solid #e5e7eb", borderRadius: 6, padding: "6px 8px", boxShadow: "0 4px 12px rgba(0,0,0,0.08)", pointerEvents: "none" }}>
            <div style={{ fontWeight: 600 }}>{hoverNode.id}</div>
            {hoverNodeDetails ? (
              <div style={{ fontSize: 12, marginTop: 2, opacity: 0.8 }}>
                {hoverNodeDetails.patient_id ? <>patient: <b>{hoverNodeDetails.patient_id}</b><br/></> : null}
                {hoverNodeDetails.taxonomy || hoverNodeDetails.taxid_genus ? <>taxon: {hoverNodeDetails.taxonomy ?? hoverNodeDetails.taxid_genus}</> : null}
              </div>
            ) : <div style={{ fontSize: 12, opacity: 0.7 }}>…</div>}
          </div>
        )}
        {hoverEdge && edgeHoverText && (
          <div style={{ position: "absolute", left: hoverEdge.x + 12, top: hoverEdge.y + 12, background: "white", border: "1px solid #e5e7eb", borderRadius: 6, padding: "6px 8px", boxShadow: "0 4px 12px rgba(0,0,0,0.08)", pointerEvents: "none" }}>
            <div style={{ fontSize: 12 }}>
              <div><b>{edgeHoverText.t}</b> — score: {edgeHoverText.s || "—"}</div>
              <div style={{ opacity: 0.8 }}>{edgeHoverText.a} {edgeHoverText.arrow} {edgeHoverText.b}</div>
            </div>
          </div>
        )}
      </div>

      {/* Details */}
      <div className="border rounded p-3" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
        <div>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Isolate details {selected ? <span className="text-sm muted">({selected})</span> : null}</div>
          {selected ? (
            details[selected] ? (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <tbody>
                  <tr><td style={{padding:4, opacity:.7}}>Isolate ID</td><td style={{padding:4}}>{details[selected].isolate_id || selected}</td></tr>
                  <tr><td style={{padding:4, opacity:.7}}>Patient ID</td><td style={{padding:4}}>{details[selected].patient_id ?? "—"}</td></tr>
                  <tr><td style={{padding:4, opacity:.7}}>Source sample</td><td style={{padding:4}}>{details[selected].source_sample ?? "—"}</td></tr>
                  <tr><td style={{padding:4, opacity:.7}}>Taxonomy</td><td style={{padding:4}}>{details[selected].taxonomy ?? details[selected].taxid_genus ?? "—"}</td></tr>
                  <tr><td style={{padding:4, opacity:.7}}>Annotations</td><td style={{padding:4}}>{details[selected].annotations_summary ?? "—"}</td></tr>
                  <tr><td style={{padding:4, opacity:.7}}>AMR flags</td><td style={{padding:4}}>{Array.isArray(details[selected].amr_flags)? details[selected].amr_flags.join(", "): (details[selected].amr_flags ?? "—")}</td></tr>
                </tbody>
              </table>
            ) : (
              <div>Loading details…</div>
            )
          ) : (
            <div className="muted">Click a node to see details.</div>
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <button className="border rounded px-2 py-1" onClick={() => selected && addIsolate(selected)} disabled={!selected}>Add to formulation</button>
          <button className="border rounded px-2 py-1" onClick={() => setSelected(undefined)}>Close</button>
        </div>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ width: 26, height: 0, borderTop: `3px solid ${color}`, display: "inline-block" }} />
      <span>{label}</span>
    </div>
  );
}

// --- Export helpers ---
function exportPNG() {
  const el = document.querySelector("canvas");
  if (!el) return;
  const url = (el as HTMLCanvasElement).toDataURL("image/png");
  const a = document.createElement("a");
  a.href = url; a.download = "network.png"; a.click();
}

function exportSVG() {
  alert("SVG export is not implemented in this minimal canvas view.");
}
