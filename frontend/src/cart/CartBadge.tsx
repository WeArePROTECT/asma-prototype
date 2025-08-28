
import React, { useEffect, useState } from "react";
import { useCart } from "./CartContext";
import { api } from "../lib/api";

export default function CartBadge() {
  const { items } = useCart();
  const [open, setOpen] = useState(false);
  const [labels, setLabels] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!open) return;
    let alive = true;
    const toFetch = items.slice(0, 12).filter((id) => !labels[id]);
    if (toFetch.length === 0) return;
    (async () => {
      for (const id of toFetch) {
        try {
          const d = await api.isolate(id);
          if (!alive) return;
          const label = d?.taxonomy ?? d?.taxid_genus ?? id;
          setLabels((prev) => ({ ...prev, [id]: label }));
        } catch {}
      }
    })();
    return () => { alive = false; };
  }, [open, items.join("|")]);

  const preview = items.slice(0, 12);
  const more = Math.max(0, items.length - preview.length);

  return (
    <div
      style={{ position: "relative", display: "inline-block" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        className="border rounded px-3 py-1"
        title="Formulation cart"
        onClick={() => (window.location.hash = "#/formulate")}
      >
        🧪 Cart{" "}
        <span
          style={{
            marginLeft: 6,
            padding: "0 8px",
            borderRadius: 999,
            background: "#111827",
            color: "white",
            fontWeight: 700,
            fontSize: 12,
            display: "inline-block",
            minWidth: 22,
            textAlign: "center",
          }}
        >
          {items.length}
        </span>
      </button>
      {open && (
        <div
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 8px)",
            width: 320,
            maxHeight: 360,
            overflowY: "auto",
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            boxShadow: "0 12px 24px rgba(0,0,0,0.12)",
            zIndex: 50,
            padding: 10,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Selected isolates</div>
          {preview.length === 0 ? (
            <div style={{ opacity: 0.7 }}>
              Nothing yet. Click nodes in the network, then “Add to formulation”.
            </div>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
              {preview.map((id) => (
                <li key={id} style={{ padding: "4px 0", borderBottom: "1px solid #f3f4f6" }}>
                  <div style={{ fontSize: 12, opacity: 0.75 }}>{id}</div>
                  <div style={{ fontSize: 13 }}>{labels[id] || "…"}</div>
                </li>
              ))}
              {more > 0 && (
                <li style={{ padding: "6px 0", fontStyle: "italic", opacity: 0.8 }}>+{more} more…</li>
              )}
            </ul>
          )}
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
            <a href="#/formulate" className="border rounded px-2 py-1" style={{ textDecoration: "none", fontWeight: 600 }}>
              Open Formulate
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
