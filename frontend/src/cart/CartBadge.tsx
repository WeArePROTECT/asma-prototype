import React from "react";
import { useCart } from "./CartContext";

export default function CartBadge() {
  const { isolates, clear, removeIsolate } = useCart();
  const [open, setOpen] = React.useState(false);
  const extra = Math.max(0, isolates.length - 12);

  return (
    <div style={{ position: "relative" }} onMouseLeave={() => setOpen(false)}>
      <button
        className="border rounded px-2 py-1"
        onMouseEnter={() => setOpen(true)}
        onClick={() => setOpen(o => !o)}
        aria-label="Open formulation cart"
      >
        Cart ({isolates.length})
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            right: 0,
            top: "110%",
            width: 320,
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            boxShadow: "0 6px 20px rgba(0,0,0,0.12)",
            padding: 10,
            zIndex: 100,
          }}
        >
          <div style={{ display: "flex", alignItems: "center" }}>
            <div style={{ fontWeight: 700 }}>Selected isolates</div>
            <button
              className="ml-auto border rounded px-2 py-1"
              onClick={() => { if (confirm("Clear isolates and prebiotics?")) clear(); }}
            >
              Clear
            </button>
          </div>

          <div style={{ marginTop: 8, display: "grid", gridTemplateColumns: "1fr auto", rowGap: 6, columnGap: 8 }}>
            {isolates.slice(0, 12).map(id => (
              <React.Fragment key={id}>
                <div>{id}</div>
                <button
                  className="text-xs border rounded px-2 py-0.5"
                  onClick={() => removeIsolate(id)}
                  aria-label={"Remove " + id}
                >
                  ×
                </button>
              </React.Fragment>
            ))}
          </div>
          {extra > 0 && <div style={{ marginTop: 6, fontSize: 12, opacity: 0.7 }}>+{extra} more…</div>}
        </div>
      )}
    </div>
  );
}
