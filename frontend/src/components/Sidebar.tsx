// src/components/Sidebar.tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type Props = {
  selectedEntity: "patients" | "samples" | "bins" | "isolates";
  setSelectedEntity: (v: "patients" | "samples" | "bins" | "isolates") => void;
};

export default function Sidebar(p: Props) {
  return (
    <aside className="w-72 p-4 border-r border-gray-200 space-y-4">
      <h2 className="font-semibold text-lg">Navigation</h2>

      <div>
        <label className="block text-sm mb-1">Entity</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={p.selectedEntity}
          onChange={(e) => p.setSelectedEntity(e.target.value as any)}
        >
          <option value="patients">Patients</option>
          <option value="samples">Samples</option>
          <option value="bins">Bins</option>
          <option value="isolates">Isolates</option>
        </select>
      </div>
    </aside>
  );
}
