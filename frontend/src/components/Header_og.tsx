import React from "react";

export default function Header() {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "10px 14px",
        borderBottom: "1px solid #e5e7eb",
        background: "#ffffff",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <img src="/2025_01_15_PROTECT_Logo-01.jpg" alt="PROTECT Team" style={{ width: 36, height: 36, borderRadius: 6 }} />
      <div style={{ fontWeight: 700 }}>ASMA Prototype</div>
      <nav style={{ marginLeft: "auto", display: "flex", gap: 12 }}>
        <a href="#/landing" style={linkStyle()}>Home</a>
        <a href="#/browser" style={linkStyle()}>Browser</a>
        <a
          href="#/browser"
          style={linkStyle()}
          onClick={(e) => {
            e.preventDefault();
            const sp = new URLSearchParams(window.location.search);
            sp.set("net", "1");
            window.history.replaceState({}, "", `${window.location.pathname}?${sp.toString()}`);
            window.location.hash = "#/browser"; // fire hashchange so Shell() switches views
          }}
        >
          Network
        </a>
        <a href="#/formulate" style={linkStyle()}>Formulate</a>
      </nav>
    </header>
  );
}

function linkStyle(): React.CSSProperties {
  return {
    textDecoration: "none",
    color: "#1f2937",
    padding: "6px 10px",
    borderRadius: 6,
    border: "1px solid transparent",
  };
}
