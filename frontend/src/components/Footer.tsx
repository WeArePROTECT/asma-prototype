import React from "react";

export default function Footer() {
  return (
    <footer
      style={{
        borderTop: "1px solid #e5e7eb",
        background: "#fff",
      }}
    >
      <div
        style={{
          padding: "10px 14px",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <img src="./arkinn-logo-black-400.png" alt="ArkInn" style={{ height: 18 }} />
        <span style={{ color: "#9ca3af" }}>•</span>
        <img src="./2025_01_15_PROTECT_Logo-01.jpg" alt="PROTECT" style={{ height: 22 }} />
        <span style={{ marginLeft: "auto", color: "#6b7280" }}>© 2025 PROTECT Team</span>
      </div>
      <div
        style={{
          padding: "8px 14px 12px",
          color: "#6b7280",
          fontSize: 11,
          lineHeight: 1.5,
          textAlign: "center",
        }}
      >
        This research was funded, in part, by the Advanced Research Projects Agency for Health (ARPA-H) under award #1AY2AX000051. The views and conclusions contained in this site are those of the authors and should not be interpreted as representing the official policies, either expressed or implied, of the U.S. Government.
      </div>
    </footer>
  );
}
