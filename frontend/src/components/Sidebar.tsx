// src/components/Sidebar.tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type Props = {
  selectedPatient?: string;
  setSelectedPatient: (v?: string) => void;
  selectedSample?: string;
  setSelectedSample: (v?: string) => void;
  selectedEntity: "patients" | "samples" | "bins" | "isolates";
  setSelectedEntity: (v: "patients" | "samples" | "bins" | "isolates") => void;
};

export default function Sidebar(p: Props) {
  const patientsQ = useQuery({ queryKey: ["patients"], queryFn: api.patients });
  const samplesQ  = useQuery({ queryKey: ["samples", p.selectedPatient], queryFn: () => api.samples(p.selectedPatient) });

  return (
    <aside className="w-72 p-4 border-r border-gray-200 space-y-4">
      <h2 className="font-semibold text-lg">Filters</h2>

      <div>
        <label className="block text-sm mb-1">Patient</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={p.selectedPatient || ""}
          onChange={(e) => {
            const v = e.target.value || undefined;
            p.setSelectedPatient(v);
            p.setSelectedSample(undefined);
          }}
        >
          <option value="">All</option>
          {patientsQ.data?.map((x) => (
            <option key={x.patient_id} value={x.patient_id}>
              {x.patient_id} {x.name ? `— ${x.name}` : ""}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm mb-1">Sample</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={p.selectedSample || ""}
          onChange={(e) => p.setSelectedSample(e.target.value || undefined)}
          disabled={!p.selectedPatient}
        >
          <option value="">All</option>
          {samplesQ.data?.map((x) => (
            <option key={x.sample_id} value={x.sample_id}>
              {x.sample_id} {x.sample_type ? `— ${x.sample_type}` : ""}
            </option>
          ))}
        </select>
      </div>

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
