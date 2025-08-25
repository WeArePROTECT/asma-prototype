// src/App.tsx
import { useEffect, useMemo, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import Sidebar from "./components/Sidebar";
import DataTable from "./components/DataTable";
import { api } from "./lib/api";

const qc = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Root />
    </QueryClientProvider>
  );
}

function Root() {
  const [selectedEntity, setSelectedEntity] = useState<"patients" | "samples" | "bins" | "isolates">("patients");
  const [selectedPatient, setSelectedPatient] = useState<string | undefined>();
  const [selectedSample, setSelectedSample] = useState<string | undefined>();
  const [searchTerm, setSearchTerm] = useState("");
  const [lineage, setLineage] = useState<any | null>(null);

  // hydrate lists
  const patientsQ = useQuery({ queryKey: ["patients"], queryFn: api.patients });
  const samplesQ  = useQuery({ queryKey: ["samples", selectedPatient], queryFn: () => api.samples(selectedPatient) });
  const binsQ     = useQuery({ queryKey: ["bins", selectedSample], queryFn: () => api.bins(selectedSample) });
  const isolatesQ = useQuery({ queryKey: ["isolates", binsQ.data?.map(b=>b.bin_id).join(",")], queryFn: () => api.isolates(), staleTime: 5_000 });

  const tableRows = useMemo(() => {
    if (searchTerm.trim()) return []; // search view handled below
    if (selectedEntity === "patients") return patientsQ.data || [];
    if (selectedEntity === "samples")  return samplesQ.data  || [];
    if (selectedEntity === "bins")     return binsQ.data     || [];
    if (selectedEntity === "isolates") return isolatesQ.data || [];
    return [];
  }, [selectedEntity, patientsQ.data, samplesQ.data, binsQ.data, isolatesQ.data, searchTerm]);

  const searchQ = useQuery({
    queryKey: ["search", searchTerm],
    queryFn: () => api.search(searchTerm),
    enabled: !!searchTerm.trim(),
  });

  const rows = useMemo(() => {
    if (!searchTerm.trim()) return tableRows;
    const b = searchQ.data;
    if (!b) return [];
    if (selectedEntity === "patients") return b.patients;
    if (selectedEntity === "samples")  return b.samples;
    if (selectedEntity === "bins")     return b.bins;
    if (selectedEntity === "isolates") return b.isolates;
    return [];
  }, [tableRows, searchQ.data, searchTerm, selectedEntity]);

  // reset dependent selections when entity changes
  useEffect(() => {
    if (selectedEntity === "patients") { setSelectedPatient(undefined); setSelectedSample(undefined); }
    if (selectedEntity === "samples")  { setSelectedSample(undefined); }
  }, [selectedEntity]);

  const onOpenLineage = async (row: any) => {
    if (selectedEntity === "patients") setLineage(await api.lineagePatient(row.patient_id));
    if (selectedEntity === "samples")  setLineage(await api.lineageSample(row.sample_id));
  };

  const onExport = () => {
    const href = api.downloadCsv(selectedEntity);
    const a = document.createElement("a");
    a.href = href;
    a.download = `${selectedEntity}.csv`;
    a.click();
  };

  return (
    <div className="h-screen flex">
      <Sidebar
        selectedPatient={selectedPatient}
        setSelectedPatient={setSelectedPatient}
        selectedSample={selectedSample}
        setSelectedSample={setSelectedSample}
        selectedEntity={selectedEntity}
        setSelectedEntity={setSelectedEntity}
      />

      <main className="flex-1 p-4 space-y-3">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">ASMA Universal Browser</h1>
          <span className="text-gray-500">API: {api.base}</span>
          <div className="ml-auto flex items-center gap-2">
            <input
              className="border rounded px-2 py-1 w-64"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button className="border rounded px-3 py-1" onClick={onExport}>Export CSV</button>
          </div>
        </div>

        <div className="border rounded">
          <DataTable rows={rows} entity={selectedEntity} onOpenLineage={onOpenLineage} />
        </div>

        {lineage && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center" onClick={() => setLineage(null)}>
            <div className="bg-white rounded shadow-lg max-w-4xl w-full max-h-[80vh] overflow-auto p-4" onClick={(e)=>e.stopPropagation()}>
              <div className="flex items-center mb-2">
                <h2 className="font-semibold text-lg">Lineage</h2>
                <button className="ml-auto border rounded px-2 py-1" onClick={() => setLineage(null)}>Close</button>
              </div>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-auto">{JSON.stringify(lineage, null, 2)}</pre>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
