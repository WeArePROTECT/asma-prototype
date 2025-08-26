import React, { useEffect, useState } from "react";

const container: React.CSSProperties = {
  maxWidth: 1200,
  margin: "0 auto",
  padding: "0 24px",
};

export default function Landing() {
  // show right column only on >= 1024px
  const [wide, setWide] = useState<boolean>(() =>
    typeof window !== "undefined"
      ? window.matchMedia("(min-width: 1024px)").matches
      : false
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setWide(mq.matches);
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else mq.addListener(onChange);
    return () => {
      if (mq.removeEventListener) mq.removeEventListener("change", onChange);
      else mq.removeListener(onChange);
    };
  }, []);

  return (
    <div style={{ paddingTop: 24, paddingBottom: 24 }}>
      {/* HERO */}
      <div style={{ ...container }}>
        <div
          style={{
            borderRadius: 14,
            boxShadow: "0 6px 20px rgba(0,0,0,.06)",
            background: "#fff",
          }}
        >
          {/* Grid content */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: wide ? "1fr 460px" : "1fr",
              gap: 24,
              alignItems: "center",
              padding: "24px",
              minHeight: 340,
            }}
          >
            {/* LEFT: Headline + CTAs + motif image */}
            <div style={{ maxWidth: 720 }}>
              <div style={{ fontSize: 32, fontWeight: 800, marginBottom: 6 }}>
                ASMA Prototype
              </div>
              <div style={{ color: "#374151", fontSize: 16 }}>
                Pro/Prebiotic Regulation for Optimized Treatment &amp; Eradication
                of Clinical Threats.
              </div>

              <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
                <a href="#/browser" style={btn()}>Open Browser</a>
                <a
                  href="#/browser"
                  style={btn("outline")}
                  onClick={(e) => {
                    e.preventDefault();
                    const sp = new URLSearchParams(window.location.search);
                    sp.set("net", "1");
                    window.history.replaceState({}, "", `${window.location.pathname}?${sp.toString()}`);
                    window.location.hash = "#/browser";
                  }}
                >
                  Explore Network
                </a>
              </div>

              {/* PROTECT motif (bigger) */}
              <div style={{ marginTop: 18 }}>
                <img
                  src="/ProtectBanner_short.png"
                  alt="PROTECT network motif"
                  style={{
                    width: "clamp(420px, 78%, 720px)",
                    height: "auto",
                    display: "block",
                    opacity: 0.98,
                    borderRadius: 12,
                  }}
                />
              </div>
            </div>

            {/* RIGHT: Circular lung art (only on wide) */}
            {wide && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <div
                  style={{
                    width: "min(420px, 36vw)",
                    aspectRatio: "1 / 1",
                    borderRadius: "50%",
                    overflow: "hidden",
                    background: "#fff",
                    border: "8px solid #fff",
                    boxShadow: "0 16px 36px rgba(0,0,0,.14)",
                  }}
                >
                  <img
                    src="/lung3.png"
                    alt="Airway isolates illustration"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      display: "block",
                    }}
                    onError={(e) => { e.currentTarget.style.display = "none"; }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* FEATURE CARDS */}
      <div style={{ ...container, marginTop: 18 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          <Card
            title="Universal Browser"
            desc="Filter patients → samples → bins → isolates. Export what you see."
            onClick={() => { window.location.hash = "#/browser"; }}
          />
          <Card
            title="Interaction Network"
            desc="Explore isolate co-occurrence and interactions. Export PNG/SVG."
            onClick={() => {
              const sp = new URLSearchParams(window.location.search);
              sp.set("net", "1");
              window.history.replaceState({}, "", `${window.location.pathname}?${sp.toString()}`);
              window.location.hash = "#/browser";
            }}
          />
          <Card
            title="Formulation Builder"
            desc="(Preview) Add isolates + choose prebiotics to mock score a blend."
            onClick={() => { window.location.hash = "#/formulate"; }}
          />
        </div>
      </div>
    </div>
  );
}

function Card({ title, desc, onClick }: { title: string; desc: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: "left",
        padding: 16,
        borderRadius: 12,
        background: "white",
        border: "1px solid #e5e7eb",
        boxShadow: "0 6px 18px rgba(0,0,0,0.05)",
        cursor: "pointer",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div>
      <div style={{ color: "#6b7280" }}>{desc}</div>
    </button>
  );
}

function btn(kind: "solid" | "outline" = "solid"): React.CSSProperties {
  const base: React.CSSProperties = {
    display: "inline-block",
    padding: "10px 14px",
    borderRadius: 10,
    fontWeight: 600,
    textDecoration: "none",
  };
  if (kind === "solid") return { ...base, background: "#0ea5e9", color: "white" };
  return { ...base, border: "1px solid #0ea5e9", color: "#0ea5e9", background: "white" };
}
