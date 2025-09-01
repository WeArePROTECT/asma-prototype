import React from "react";

type Props = {
  entity: "patients" | "samples" | "bins" | "isolates" | "interactions" | "prebiotics" | "formulations";
  label?: string;
  className?: string;
};

/**
 * Drop-in replacement for ExportCsvButton that uses an absolute backend base.
 * This makes the button work regardless of Vite proxy or api.ts config.
 */
const ExportCsvButton: React.FC<Props> = ({ entity, label = "Export CSV", className }) => {
  const href = `http://127.0.0.1:8000/download/${encodeURIComponent(entity)}.csv`;
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      style={{
        display: "inline-block",
        fontSize: 12,
        padding: "6px 10px",
        borderRadius: 6,
        border: "1px solid #cbd5e1",
        background: "#f8fafc",
        color: "#111827",
        textDecoration: "none",
      }}
      className={className}
    >
      {label}
    </a>
  );
};

export default ExportCsvButton;
