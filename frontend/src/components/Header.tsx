
import React from "react";
import CartBadge from "../cart/CartBadge";

export default function Header() {
  const [hash, setHash] = React.useState<string>(
    typeof window !== "undefined" ? window.location.hash : ""
  );

  React.useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  // Cart only on the Universal Browser / Open Network views
  const showCart = hash.startsWith("#/browser");

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
      {/* PROTECT / ASMA brand (keeps the original look) */}
      <a
        href="#/landing"
        style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "inherit" }}
        aria-label="ASMA Prototype — Home"
      >
        <img
          src="/2025_01_15_PROTECT_Logo-01.jpg"
          alt="PROTECT Team"
          style={{ width: 36, height: 36, borderRadius: 6, objectFit: "cover" }}
        />
        <div style={{ fontWeight: 700 }}>ASMA Prototype</div>
      </a>

      {/* Right-aligned nav + (optional) cart badge */}
      <nav style={{ marginLeft: "auto", display: "flex", gap: 12, alignItems: "center" }}>
        <a href="#/landing" style={linkStyle()}>Home</a>
        <a href="#/browser" style={linkStyle()}>Browser</a>
        <a
          href="#/browser"
          style={linkStyle()}
          onClick={(e) => {
            // Preserve your original "Network" behavior: force ?net=1 then route to browser
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

        {/* Cart appears only on Browser/Open Network routes */}
        {showCart ? <div style={{ marginLeft: 8 }}><CartBadge /></div> : null}
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
