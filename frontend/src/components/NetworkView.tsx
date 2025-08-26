
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type NetNode = { id: string; label?: string; x: number; y: number; vx: number; vy: number; };
type NetEdge = { source: string; target: string; type?: string; score?: number; };

const CSS_WIDTH = 860;
const CSS_HEIGHT = 520;

// Edge colors by type
const EDGE_COLORS: Record<string, string> = {
  complementarity: "#2563eb", // blue
  cooccurrence: "#10b981",    // green
  inhibition: "#ef4444",      // red
  "": "#d0d0d0",
};

export default function NetworkView({ initialFocusId }: { initialFocusId?: string }) {
  const [isolateId, setIsolateId] = useState<string>(initialFocusId || "");
  const [edgeType, setEdgeType] = useState<string>(""); // "", "complementarity", "inhibition", "cooccurrence"
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // keep input synced with prop
  useEffect(() => {
    if (initialFocusId) setIsolateId(initialFocusId);
  }, [initialFocusId]);

  const q = useQuery({
    queryKey: ["network", isolateId, edgeType],
    queryFn: () => api.network({ isolateId: isolateId || undefined, type: edgeType || undefined }),
  });

  // Fetch isolates once for detail panel (client-side lookup)
  const isolatesQ = useQuery({ queryKey: ["isolates-all"], queryFn: () => api.isolates() });

  const selectedDetails = useMemo(() => {
    if (!selectedId) return null;
    const list = isolatesQ.data || [];
    return list.find((it: any) => it.isolate_id === selectedId || it.id === selectedId) || { id: selectedId, isolate_id: selectedId, label: selectedId };
  }, [selectedId, isolatesQ.data]);

  return (
    <div className="net-wrap">
      <div className="net-toolbar">
        <div className="group">
          <label>Isolate focus</label>
          <input
            value={isolateId}
            onChange={(e) => setIsolateId(e.target.value)}
            placeholder="e.g., I001"
          />
        </div>
        <div className="group">
          <label>Edge type</label>
          <select value={edgeType} onChange={(e) => setEdgeType(e.target.value)}>
            <option value="">All</option>
            <option value="complementarity">complementarity</option>
            <option value="cooccurrence">cooccurrence</option>
            <option value="inhibition">inhibition</option>
          </select>
        </div>
        <div className="group" style={{ marginLeft: "auto" }}>
          <Legend />
        </div>
        <div className="muted">{q.isLoading ? "Loading…" : q.error ? "Failed to load network" : `${q.data?.nodes?.length ?? 0} nodes, ${q.data?.edges?.length ?? 0} edges`}</div>
      </div>

      <NetCanvas data={q.data} focusId={isolateId || undefined} onClickNode={(id) => { setSelectedId(id); setIsolateId(id); }} />

      {selectedDetails && (
        <IsolateDetails details={selectedDetails} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}

function Legend() {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 12 }}>
      {["complementarity", "cooccurrence", "inhibition"].map((t) => (
        <div key={t} style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ width: 18, height: 2, background: EDGE_COLORS[t], display: "inline-block" }} />
          <span>{t}</span>
        </div>
      ))}
    </div>
  );
}

function Chip({ children }: { children: any }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 6px",
      borderRadius: 999,
      background: "#f3f4f6",
      border: "1px solid #e5e7eb",
      fontSize: 12,
      marginRight: 6,
      marginBottom: 6,
    }}>{children}</span>
  );
}

function Row({ label, value }: { label: string; value?: any }) {
  const v = value === null || value === undefined || value === "" ? "—" : value;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: 8 }}>
      <div style={{ color: "#6b7280" }}>{label}</div>
      <div style={{ whiteSpace: "pre-wrap" }}>{String(v)}</div>
    </div>
  );
}

function IsolateDetails({ details, onClose }: { details: any; onClose: () => void }) {
  const chips = (arr?: any[]) => (Array.isArray(arr) ? arr : []).map((x, i) => <Chip key={i}>{String(x)}</Chip>);

  return (
    <div className="border rounded p-3" style={{ marginTop: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <div className="font-semibold">Isolate details</div>
        <div className="text-sm muted">({details.isolate_id || details.id})</div>
        <button className="ml-auto border rounded px-2 py-1" onClick={onClose}>Close</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10 }}>
        <Row label="Isolate ID" value={details.isolate_id || details.id} />
        <Row label="Patient ID" value={details.patient_id} />
        <Row label="Source sample" value={details.source_sample_id} />
        <Row label="Taxonomy" value={details.taxonomy || details.taxon || details.taxon_name} />
        <Row label="Genus TaxID" value={details.taxid_genus} />
        <Row label="Growth media" value={details.growth_media} />
        <Row label="Annotations" value={details.annotations_summary} />

        {/* arrays rendered as chips */}
        <div>
          <div style={{ color: "#6b7280", marginBottom: 4 }}>Linked bins</div>
          <div>{chips(details.linked_bins)}</div>
        </div>
        <div>
          <div style={{ color: "#6b7280", marginBottom: 4 }}>ARM flags</div>
          <div>{chips(details.arm_flags)}</div>
        </div>
        <div>
          <div style={{ color: "#6b7280", marginBottom: 4 }}>Metabolite markers</div>
          <div>{chips(details.metabolite_markers)}</div>
        </div>
      </div>
    </div>
  );
}

function NetCanvas({ data, focusId, onClickNode }: { data: any; focusId?: string; onClickNode?: (id: string) => void }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const dprRef = useRef<number>(1);
  const dragIdRef = useRef<string | null>(null);
  const hoverIdRef = useRef<string | null>(null);
  const [hoverId, setHoverId] = useState<string | null>(null); // for cursor updates

  // view transform (zoom/pan)
  const scaleRef = useRef<number>(1);
  const txRef = useRef<number>(0);
  const tyRef = useRef<number>(0);

  // click detection
  const downPosRef = useRef<{x:number,y:number}|null>(null);
  const downNodeRef = useRef<string | null>(null);

  // Prepare canvas for devicePixelRatio (crisp drawing + correct hit testing)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    dprRef.current = dpr;
    // set CSS size
    canvas.style.width = `${CSS_WIDTH}px`;
    canvas.style.height = `${CSS_HEIGHT}px`;
    // set backing store size
    canvas.width = Math.round(CSS_WIDTH * dpr);
    canvas.height = Math.round(CSS_HEIGHT * dpr);
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctxRef.current = ctx;
    }
  }, []);

  // Build nodes/edges once per data
  const { nodes, edges } = useMemo(() => {
    const ns: NetNode[] = (data?.nodes || []).map((n: any, i: number) => {
      const angle = (i / Math.max(1, data.nodes.length)) * Math.PI * 2;
      const r = Math.min(CSS_WIDTH, CSS_HEIGHT) * 0.35;
      return {
        id: n.id,
        label: n.label || n.id,
        x: CSS_WIDTH / 2 + r * Math.cos(angle),
        y: CSS_HEIGHT / 2 + r * Math.sin(angle),
        vx: 0,
        vy: 0,
      };
    });
    const es: NetEdge[] = (data?.edges || []).map((e: any) => ({
      source: e.source,
      target: e.target,
      type: e.type,
      score: e.score,
    }));
    return { nodes: ns, edges: es };
  }, [data]);

  // O(1) node lookup
  const nodeById = useMemo(() => {
    const m = new Map<string, NetNode>();
    nodes.forEach((n) => m.set(n.id, n));
    return m;
  }, [nodes]);

  // Physics + draw loop
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;

    let raf = 0;
    const K_REP = 1200;    // repulsion strength
    const K_SPR = 0.01;    // spring strength
    const LINK_DIST = 120;
    const FRICTION = 0.85;
    const DT = 0.5;
    const RADIUS = 10;     // render radius

    function rectsOverlap(a: {x:number,y:number,w:number,h:number}, b: {x:number,y:number,w:number,h:number}) {
      return !(a.x + a.w < b.x || b.x + b.w < a.x || a.y + a.h < b.y || b.y + b.h < a.y);
    }

    function step() {
      const dpr = dprRef.current;
      const s = scaleRef.current;
      const tx = txRef.current;
      const ty = tyRef.current;

      // repulsion
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let d2 = dx * dx + dy * dy + 0.01;
          let f = K_REP / d2;
          let invd = 1 / Math.sqrt(d2);
          dx *= invd; dy *= invd;
          a.vx += f * dx * DT;
          a.vy += f * dy * DT;
          b.vx -= f * dx * DT;
          b.vy -= f * dy * DT;
        }
      }
      // springs
      for (const e of edges) {
        const a = nodeById.get(e.source);
        const b = nodeById.get(e.target);
        if (!a || !b) continue;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        let diff = dist - LINK_DIST;
        let f = K_SPR * diff;
        let nx = dx / dist, ny = dy / dist;
        a.vx += f * nx * DT;
        a.vy += f * ny * DT;
        b.vx -= f * nx * DT;
        b.vy -= f * ny * DT;
      }
      // integrate + keep inside bounds
      for (const n of nodes) {
        if (n.id === dragIdRef.current) {
          n.vx = 0; n.vy = 0; // position is being set by pointer handler
        } else {
          n.vx *= FRICTION;
          n.vy *= FRICTION;
          n.x += n.vx;
          n.y += n.vy;
          n.x = Math.max(RADIUS, Math.min(CSS_WIDTH - RADIUS, n.x));
          n.y = Math.max(RADIUS, Math.min(CSS_HEIGHT - RADIUS, n.y));
        }
      }

      // clear in CSS coords
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, CSS_WIDTH, CSS_HEIGHT);

      // apply view transform (scale + pan)
      ctx.setTransform(dpr * s, 0, 0, dpr * s, dpr * tx, dpr * ty);

      // edges
      for (const e of edges) {
        const a = nodeById.get(e.source);
        const b = nodeById.get(e.target);
        if (!a || !b) continue;
        ctx.beginPath();
        ctx.lineWidth = 1;
        ctx.strokeStyle = EDGE_COLORS[e.type || ""] || EDGE_COLORS[""];
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }

      // nodes
      for (const n of nodes) {
        const isFocus = !!focusId && n.id === focusId;
        const isHover = hoverIdRef.current === n.id;
        ctx.beginPath();
        ctx.fillStyle = isFocus ? "#2563eb" : isHover ? "#111" : "#444";
        ctx.arc(n.x, n.y, isFocus ? 12 : 10, 0, Math.PI * 2);
        ctx.fill();
      }

      // labels (collision-aware in CSS pixel space)
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.font = "12px ui-sans-serif, system-ui";
      ctx.fillStyle = "#000";
      ctx.textAlign = "left";

      // screen-space node boxes for collision checks
      const nodeBoxes = nodes.map((n) => {
        const sx = n.x * s + tx;
        const sy = n.y * s + ty;
        const rr = (12) * s; // generous for focus/hover
        return { x: sx - rr, y: sy - rr, w: rr * 2, h: rr * 2, cx: sx, cy: sy };
      });

      const placed: Array<{x:number,y:number,w:number,h:number}> = [];

      function placeLabelFor(n: NetNode, text: string) {
        const sx = n.x * s + tx;
        const sy = n.y * s + ty;
        const w = ctx.measureText(text).width;
        const h = 14; // approx line height
        const gap = 10, pad = 2;

        const candidates = [
          { x: sx + gap,               y: sy - h/2,       name: "right" },
          { x: sx - gap - w,           y: sy - h/2,       name: "left" },
          { x: sx - w/2,               y: sy - gap - h,   name: "top" },
          { x: sx - w/2,               y: sy + gap,       name: "bottom" },
          { x: sx + gap,               y: sy - gap - h,   name: "top-right" },
          { x: sx + gap,               y: sy + gap,       name: "bottom-right" },
          { x: sx - gap - w,           y: sy - gap - h,   name: "top-left" },
          { x: sx - gap - w,           y: sy + gap,       name: "bottom-left" },
        ];

        for (const c of candidates) {
          const rect = { x: c.x - pad, y: c.y - pad, w: w + 2*pad, h: h + 2*pad };
          // check against nodes
          let ok = nodeBoxes.every(nb => !rectsOverlap(rect, {x: nb.x, y: nb.y, w: nb.w, h: nb.h}));
          if (!ok) continue;
          // check against placed labels
          ok = placed.every(pb => !rectsOverlap(rect, pb));
          if (!ok) continue;

          // draw leader line if not right
          if (c.name !== "right") {
            ctx.beginPath();
            ctx.strokeStyle = "#c7c7c7";
            ctx.lineWidth = 1;
            ctx.moveTo(sx, sy);
            // connect to nearest edge of label rect
            const lx = Math.max(rect.x, Math.min(sx, rect.x + rect.w));
            const ly = Math.max(rect.y, Math.min(sy, rect.y + rect.h));
            ctx.lineTo(lx, ly);
            ctx.stroke();
          }

          ctx.fillText(text, c.x, c.y + h - 4);
          placed.push(rect);
          return;
        }

        // fallback (right)
        ctx.fillText(text, sx + gap, sy + h/2 - 4);
        placed.push({ x: sx + gap, y: sy - h/2, w, h });
      }

      for (const n of nodes) {
        placeLabelFor(n, n.label || n.id);
      }

      ctx.restore();
      raf = requestAnimationFrame(step);
    }

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [nodes, edges, nodeById, focusId]);

  // Coordinate helpers
  function getCssXYFromEvent(canvas: HTMLCanvasElement, e: PointerEvent) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = CSS_WIDTH / rect.width;
    const scaleY = CSS_HEIGHT / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  }
  function cssToWorld(xCss: number, yCss: number) {
    const s = scaleRef.current;
    const tx = txRef.current;
    const ty = tyRef.current;
    return { x: (xCss - tx) / s, y: (yCss - ty) / s };
  }

  // Pointer interactions (left: drag nodes / click for details, right: pan, wheel: zoom)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function pick(mx: number, my: number) {
      let best: NetNode | null = null;
      let bestD = 1e9;
      for (const n of nodes) {
        const d = Math.hypot(n.x - mx, n.y - my);
        if (d < bestD && d < 18) { best = n; bestD = d; }
      }
      return best;
    }

    function onPointerDown(e: PointerEvent) {
      const css = getCssXYFromEvent(canvas, e);
      const { x: mx, y: my } = cssToWorld(css.x, css.y);
      const n = pick(mx, my);
      downPosRef.current = { x: mx, y: my };
      downNodeRef.current = n?.id || null;

      if (e.button === 2) { // right button -> start panning
        canvas.setPointerCapture?.(e.pointerId);
        e.preventDefault();
        return;
      }

      if (n) {
        dragIdRef.current = n.id;
        n.x = mx; n.y = my; n.vx = 0; n.vy = 0;
        canvas.setPointerCapture?.(e.pointerId);
        e.preventDefault();
      }
    }

    function onPointerMove(e: PointerEvent) {
      const css = getCssXYFromEvent(canvas, e);
      const { x: mx, y: my } = cssToWorld(css.x, css.y);

      if (dragIdRef.current) {
        const n = nodes.find(nd => nd.id === dragIdRef.current);
        if (n) { n.x = mx; n.y = my; n.vx = 0; n.vy = 0; }
      } else if (e.buttons === 2) {
        // panning with right button: move view by delta in CSS coords
        const prev = downPosRef.current;
        if (prev) {
          const s = scaleRef.current;
          const dxCss = (mx - prev.x) * s;
          const dyCss = (my - prev.y) * s;
          txRef.current += dxCss;
          tyRef.current += dyCss;
          downPosRef.current = { x: mx, y: my };
        }
      }

      // hover (in world coords)
      const h = pick(mx, my);
      hoverIdRef.current = h?.id || null;
      const overNode = !!h;
      (canvas as any).style.cursor = dragIdRef.current ? "grabbing" : (overNode ? "grab" : (e.buttons === 2 ? "grabbing" : "default"));
      setHoverId(hoverIdRef.current);
    }

    function onPointerUp(e: PointerEvent) {
      const css = getCssXYFromEvent(canvas, e);
      const { x: mx, y: my } = cssToWorld(css.x, css.y);
      const start = downPosRef.current;
      const startId = downNodeRef.current;
      dragIdRef.current = null;
      downPosRef.current = null;
      downNodeRef.current = null;
      canvas.releasePointerCapture?.(e.pointerId);

      // treat as click if left button and small movement
      if (e.button === 0 && start) {
        const moved = Math.hypot(mx - start.x, my - start.y);
        if (moved < 4 && startId && onClickNode) {
          onClickNode(startId);
        }
      }
    }

    function onWheel(e: WheelEvent) {
      e.preventDefault();
      const delta = -Math.sign(e.deltaY) * 0.1; // zoom step
      const s0 = scaleRef.current;
      const s1 = Math.min(3, Math.max(0.5, s0 * (1 + delta)));
      if (s1 === s0) return;

      // zoom about mouse position (CSS coords -> world)
      const rect = canvas.getBoundingClientRect();
      const cssX = (e.clientX - rect.left) * (CSS_WIDTH / rect.width);
      const cssY = (e.clientY - rect.top) * (CSS_HEIGHT / rect.height);

      const wx = (cssX - txRef.current) / s0;
      const wy = (cssY - tyRef.current) / s0;

      txRef.current = cssX - wx * s1;
      tyRef.current = cssY - wy * s1;
      scaleRef.current = s1;
    }

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointerleave", onPointerUp);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    canvas.addEventListener("contextmenu", (e) => e.preventDefault());

    return () => {
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("pointerleave", onPointerUp);
      canvas.removeEventListener("wheel", onWheel);
    };
  }, [nodes]);

  return (
    <canvas
      ref={canvasRef}
      width={Math.round(CSS_WIDTH * Math.max(1, window.devicePixelRatio || 1))}
      height={Math.round(CSS_HEIGHT * Math.max(1, window.devicePixelRatio || 1))}
      className="net-canvas"
      style={{
        width: `${CSS_WIDTH}px`,
        height: `${CSS_HEIGHT}px`,
        cursor: hoverId ? "grab" : "default",
        touchAction: "none" as any,
        position: "relative",
        zIndex: 10,
      }}
    />
  );
}
