import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type NetNode = { id: string; label?: string; x: number; y: number; vx: number; vy: number; };
type NetEdge = { source: string; target: string; type?: string; score?: number; };

const CSS_WIDTH = 860;
const CSS_HEIGHT = 520;

export default function NetworkView() {
  const [isolateId, setIsolateId] = useState<string>("");
  const [edgeType, setEdgeType] = useState<string>(""); // "", "complementarity", "inhibition", "cooccurrence"

  const q = useQuery({
    queryKey: ["network", isolateId, edgeType],
    queryFn: () => api.network({ isolateId: isolateId || undefined, type: edgeType || undefined }),
  });

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
        <div className="muted">
          {q.isLoading
            ? "Loading…"
            : q.error
            ? "Failed to load network"
            : `${q.data?.nodes?.length ?? 0} nodes, ${q.data?.edges?.length ?? 0} edges`}
        </div>
      </div>

      <NetCanvas data={q.data} focusId={isolateId || undefined} />
    </div>
  );
}

function NetCanvas({ data, focusId }: { data: any; focusId?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const dprRef = useRef<number>(1);
  const dragIdRef = useRef<string | null>(null);
  const hoverIdRef = useRef<string | null>(null);
  const [hoverId, setHoverId] = useState<string | null>(null); // for cursor updates

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
      // scale so 1 unit in code == 1 CSS pixel
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
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

    function step() {
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

      // draw
      ctx.clearRect(0, 0, CSS_WIDTH, CSS_HEIGHT);

      // edges
      ctx.lineWidth = 1;
      ctx.strokeStyle = "#d0d0d0";
      for (const e of edges) {
        const a = nodeById.get(e.source);
        const b = nodeById.get(e.target);
        if (!a || !b) continue;
        ctx.beginPath();
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

        // label
        ctx.font = "12px ui-sans-serif, system-ui";
        ctx.fillStyle = "#000";
        ctx.textAlign = "left";
        ctx.fillText(n.label || n.id, n.x + 12, n.y + 4);
      }

      raf = requestAnimationFrame(step);
    }

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [nodes, edges, nodeById, focusId]);

  // Pointer interactions bound directly to the canvas, correcting for CSS->device pixel scaling
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function getXY(e: PointerEvent) {
      const rect = canvas.getBoundingClientRect();
      const dpr = dprRef.current;
      // Convert from client pixels to canvas CSS pixels
      const scaleX = (canvas.width / dpr) / rect.width;
      const scaleY = (canvas.height / dpr) / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
    }

    function pick(mx: number, my: number) {
      let best: NetNode | null = null;
      let bestD = 1e9;
      for (const n of nodes) {
        const d = Math.hypot(n.x - mx, n.y - my);
        if (d < bestD && d < 18) { best = n; bestD = d; } // friendly hit radius
      }
      return best;
    }

    function onPointerDown(e: PointerEvent) {
      const { x: mx, y: my } = getXY(e);
      const n = pick(mx, my);
      if (n) {
        dragIdRef.current = n.id;
        n.x = mx; n.y = my; n.vx = 0; n.vy = 0;
        canvas.setPointerCapture?.(e.pointerId);
        e.preventDefault();
      }
    }

    function onPointerMove(e: PointerEvent) {
      const { x: mx, y: my } = getXY(e);

      if (dragIdRef.current) {
        const n = nodes.find(nd => nd.id === dragIdRef.current);
        if (n) { n.x = mx; n.y = my; n.vx = 0; n.vy = 0; }
      }

      const h = pick(mx, my);
      hoverIdRef.current = h?.id || null;
      setHoverId(hoverIdRef.current); // update cursor
    }

    function onPointerUp(e: PointerEvent) {
      dragIdRef.current = null;
      canvas.releasePointerCapture?.(e.pointerId);
    }

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointerleave", onPointerUp);

    return () => {
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("pointerleave", onPointerUp);
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
      onContextMenu={(e) => e.preventDefault()}
    />
  );
}
