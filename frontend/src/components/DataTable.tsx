// src/components/DataTable.tsx (SAFE, debounced search, regex-free)
import React, { useEffect, useMemo, useState } from "react";
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";

type Props = {
  rows: any[];
  onOpenLineage?: (row: any) => void;
  onRowDetails?: (row: any) => void;   // Optional: opens details drawer on row click (samples/bins)
  onOpenNetworkWithFocus?: (isolateId: string) => void; // Optional: isolates -> open network
  entity: "patients" | "samples" | "bins" | "isolates";
  /** Optional search query. If provided, filtering is handled here with debounce + safe includes(). */
  query?: string;
  /** Debounce milliseconds for the optional query (default 300ms). */
  debounceMs?: number;
};

function toStr(v: any): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  // protect against giant objects
  try { return JSON.stringify(v); } catch { return ""; }
}

export default function DataTable({
  rows,
  onOpenLineage,
  onRowDetails,
  onOpenNetworkWithFocus,
  entity,
  query,
  debounceMs = 300,
}: Props) {
  // Debounce the incoming query (if provided)
  const [qLive, setQLive] = useState(query ?? "");
  useEffect(() => {
    if (query == null) return; // external search not used
    const t = window.setTimeout(() => setQLive(query), debounceMs);
    return () => window.clearTimeout(t);
  }, [query, debounceMs]);

  // Safe, case-insensitive filter. No RegExp; just .includes().
  const filteredRows = useMemo(() => {
    const needle = (qLive ?? "").trim().toLowerCase();
    if (!needle) return rows || [];
    // iterate once per row and check values; bail early when matched
    return (rows || []).filter((r) => {
      for (const v of Object.values(r || {})) {
        if (toStr(v).toLowerCase().includes(needle)) return true;
      }
      return false;
    });
  }, [rows, qLive]);

  const cols = useMemo<ColumnDef<any>[]>(() => {
    const keys = new Set<string>();
    (rows || []).forEach((r) => Object.keys(r || {}).forEach((k) => keys.add(k)));
    const ordered = Array.from(keys);
    // bubble id-like fields to the front
    const idOrder = ["patient_id", "sample_id", "bin_id", "isolate_id", "id"];
    ordered.sort((a, b) => (idOrder.indexOf(a) + 999) - (idOrder.indexOf(b) + 999));

    const baseCols = ordered.slice(0, 8).map((k) => ({
      header: k,
      accessorKey: k,
      cell: (ctx: any) => {
        const v = ctx.getValue();
        if (Array.isArray(v) || typeof v === "object") return <code className="text-xs">json</code>;
        return String(v ?? "");
      },
    })) as ColumnDef<any>[];

    // lineage button (patients + samples)
    const showLineage = entity === "patients" || entity === "samples";
    if (showLineage) {
      baseCols.unshift({
        id: "_actions",
        header: "",
        cell: ({ row }) => (
          <button
            className="text-blue-600 underline"
            onClick={(e) => {
              e.stopPropagation();
              onOpenLineage?.(row.original);
            }}
          >
            Open lineage
          </button>
        ),
      } as ColumnDef<any>);
    }
    return baseCols;
  }, [rows, onOpenLineage, entity]);

  const table = useReactTable({
    data: filteredRows,
    columns: cols,
    getCoreRowModel: getCoreRowModel(),
  });

  function handleRowClick(original: any) {
    if (entity === "samples" || entity === "bins") {
      onRowDetails?.(original);
    } else if (entity === "isolates" && onOpenNetworkWithFocus) {
      const iso = original.isolate_id || original.id;
      if (iso) onOpenNetworkWithFocus(iso);
    }
  }

  const clickable = (entity === "samples" || entity === "bins" || (entity === "isolates" && !!onOpenNetworkWithFocus));

  return (
    <div className="overflow-auto">
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 bg-white">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => (
                <th key={h.id} className="text-left px-2 py-1 border-b">
                  {h.isPlaceholder ? null : flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((r) => (
            <tr
              key={r.id}
              className={
                "odd:bg-gray-50 " + (clickable ? "cursor-pointer hover:bg-gray-100" : "")
              }
              onClick={() => handleRowClick(r.original)}
            >
              {r.getVisibleCells().map((c) => (
                <td key={c.id} className="px-2 py-1 border-b align-top">
                  {flexRender(c.column.columnDef.cell, c.getContext())}
                </td>
              ))}
            </tr>
          ))}
          {!filteredRows?.length && (
            <tr>
              <td className="p-4 text-gray-500">No rows</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
