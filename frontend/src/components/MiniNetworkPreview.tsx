import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api";

const W = 420, H = 260, R = 10;
const EDGE_COLORS: Record<string,string> = {
  complementarity: "#2563eb",
  cooccurrence: "#10b981",
  inhibition: "#ef4444",
  competition: "#6b7280",
};

function circleLayout(ids: string[]) {
  const cx = W/2, cy = H/2;
  const rad = Math.min(W,H)/2 - 28;
  const pos: Record<string,{x:number;y:number}> = {};
  const n = Math.max(1, ids.length);
  ids.forEach((id, i) => {
    const t = (2*Math.PI*i)/n;
    pos[id] = { x: cx + rad*Math.cos(t), y: cy + rad*Math.sin(t) };
  });
  return pos;
}

export default function MiniNetworkPreview({ isolateIds }:{ isolateIds: string[] }) {
  const canvasRef = useRef<HTMLCanvasElement|null>(null);
  const [edges, setEdges] = useState<any[]>([]);
  const ids = useMemo(() => Array.from(new Set(isolateIds || [])), [isolateIds]);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!ids.length) { setEdges([]); return; }
      try {
        const net = await api.network({ type: "All", max_neighbors: 200 });
        const keep = new Set(ids);
        const e = (net.edges || []).filter((x: any) => keep.has(x.source) && keep.has(x.target));
        if (alive) setEdges(e);
      } catch {
        if (alive) setEdges([]);
      }
    })();
    return () => { alive = false; };
  }, [ids.join(",")]);

  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const ctx = el.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;
    el.width = W*dpr; el.height = H*dpr; el.style.width = W+"px"; el.style.height = H+"px";
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,W,H);

    if (!ids.length) {
      ctx.font = "13px system-ui";
      ctx.fillStyle = "#64748b";
      ctx.fillText("Add isolates to see a mini network preview", 16, 24);
      return;
    }

    const pos = circleLayout(ids);

    // edges
    edges.forEach((e) => {
      const a = pos[e.source], b = pos[e.target];
      if (!a || !b) return;
      ctx.strokeStyle = EDGE_COLORS[e.type || "cooccurrence"] || "#999";
      ctx.lineWidth = 1.5 + Math.max(0, Math.min(1, (e.score ?? 0))) * 0.8;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    });

    // nodes + labels
    ids.forEach(id => {
      const p = pos[id];
      ctx.beginPath();
      ctx.arc(p.x, p.y, R, 0, Math.PI*2);
      ctx.fillStyle = "#334155";
      ctx.fill();
      ctx.fillStyle = "#111";
      ctx.font = "12px system-ui";
      ctx.fillText(id, p.x + R + 4, p.y + 4);
    });
  }, [ids.join(","), edges]);

  return (
    <div className="rounded-lg border bg-white">
      <div className="px-3 py-2 border-b text-sm text-slate-600">Mini network preview</div>
      <div className="p-2">
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}
