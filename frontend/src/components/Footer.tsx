import React from "react";

export default function Footer() {
  return (
    <footer
      style={{
        padding: "10px 14px",
        borderTop: "1px solid #e5e7eb",
        background: "#fff",
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      <img src="/arkinn-logo-black-400.png" alt="ArkInn" style={{ height: 18 }} />
      <span style={{ color: "#9ca3af" }}>•</span>
      <img src="/2025_01_15_PROTECT_Logo-01.jpg" alt="PROTECT" style={{ height: 22 }} />
      <span style={{ marginLeft: "auto", color: "#6b7280" }}>© 2025 PROTECT Team</span>
    </footer>
  );
}
