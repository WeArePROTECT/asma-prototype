
import React from "react";
import CartBadge from "../cart/CartBadge";

export default function Header() {
  const [hash, setHash] = React.useState<string>(
    typeof window !== "undefined" ? window.location.hash : ""
  );
  const [is_dropdown_open, setIsDropdownOpen] = React.useState<boolean>(false);
  const dropdown_ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handle_click_outside = (event: MouseEvent) => {
      if (dropdown_ref.current && !dropdown_ref.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (is_dropdown_open) {
      document.addEventListener("mousedown", handle_click_outside);
    }

    return () => {
      document.removeEventListener("mousedown", handle_click_outside);
    };
  }, [is_dropdown_open]);

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
          src="./2025_01_15_PROTECT_Logo-01.jpg"
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

        {/* PROTECT Tools Dropdown */}
        <div ref={dropdown_ref} style={{ position: "relative" }}>
          <button
            onClick={() => setIsDropdownOpen(!is_dropdown_open)}
            style={{
              ...linkStyle(),
              background: "transparent",
              border: "1px solid transparent",
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: "inherit",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#e5e7eb";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "transparent";
            }}
          >
            PROTECT Tools
          </button>
          {is_dropdown_open && (
            <div
              style={{
                position: "absolute",
                top: "100%",
                right: 0,
                marginTop: 4,
                background: "#ffffff",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
                minWidth: 200,
                zIndex: 50,
                overflow: "hidden",
              }}
            >
              <a
                href="https://protect.qb3.berkeley.edu/protect/"
                target="_blank"
                rel="noopener noreferrer"
                style={dropdownItemStyle()}
                onClick={() => setIsDropdownOpen(false)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f3f4f6";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                PROTECT File Viewer
              </a>
              <a
                href="https://protect.qb3.berkeley.edu/genomedepot/"
                target="_blank"
                rel="noopener noreferrer"
                style={dropdownItemStyle()}
                onClick={() => setIsDropdownOpen(false)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f3f4f6";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                PROTECT GenomeDepot
              </a>
              <a
                href="https://protect.qb3.berkeley.edu/asma/api/taxonomy/table"
                target="_blank"
                rel="noopener noreferrer"
                style={dropdownItemStyle()}
                onClick={() => setIsDropdownOpen(false)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f3f4f6";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                PROTECT Taxonomic Data Table
              </a>
              <a
                href="https://protect.qb3.berkeley.edu/asma/api/taxonomy/treemap"
                target="_blank"
                rel="noopener noreferrer"
                style={dropdownItemStyle()}
                onClick={() => setIsDropdownOpen(false)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f3f4f6";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                PROTECT Taxonomy Treemap
              </a>
            </div>
          )}
        </div>

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

function dropdownItemStyle(): React.CSSProperties {
  return {
    display: "block",
    padding: "10px 14px",
    color: "#1f2937",
    textDecoration: "none",
    fontSize: 14,
    transition: "background-color 0.15s ease",
  };
}
