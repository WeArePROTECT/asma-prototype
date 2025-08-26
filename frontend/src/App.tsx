
import { useEffect, useMemo, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import Sidebar from "./components/Sidebar";
import DataTable from "./components/DataTable";
import { api } from "./lib/api";
import SampleAbundance from "./components/SampleAbundance";
import BinPathways from "./components/BinPathways";
import BinAbundance from "./components/BinAbundance";
import NetworkView from "./components/NetworkView";

const qc = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Root />
    </QueryClientProvider>
  );
}

type Entity = "patients" | "samples" | "bins" | "isolates";

function Root() {
  const [selectedEntity, setSelectedEntity] = useState<Entity>("patients");
  const [selectedPatient, setSelectedPatient] = useState<string | undefined>();
  const [selectedSample, setSelectedSample] = useState<string | undefined>();
  const [searchTerm, setSearchTerm] = useState("");
  const [lineage, setLineage] = useState<any | null>(null);
  const [detailsRow, setDetailsRow] = useState<any | null>(null);
  const [showNetwork, setShowNetwork] = useState(false);

  // Close modals with Esc
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setLineage(null);
        setDetailsRow(null);
        setShowNetwork(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // hydrate lists
  const patientsQ = useQuery({ queryKey: ["patients"], queryFn: api.patients });
  const samplesQ  = useQuery({ queryKey: ["samples", selectedPatient], queryFn: () => api.samples(selectedPatient) });
  const binsQ     = useQuery({ queryKey: ["bins", selectedSample], queryFn: () => api.bins(selectedSample) });
  const isolatesQ = useQuery({ queryKey: ["isolates"], queryFn: () => api.isolates(), staleTime: 5_000 });

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
            <button className="border rounded px-3 py-1" onClick={() => setShowNetwork(true)}>Open Network</button>
            <button className="border rounded px-3 py-1" onClick={onExport}>Export CSV</button>
          </div>
        </div>

        <div className="border rounded">
          <DataTable rows={rows} entity={selectedEntity} onOpenLineage={onOpenLineage} onRowDetails={setDetailsRow} />
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

        {detailsRow && (
          <div className="fixed bottom-4 right-4 left-4 md:left-auto md:w-[520px] bg-white border shadow-lg rounded p-4 space-y-3">
            <div className="flex items-center">
              <div className="font-semibold">
                Details — {selectedEntity === "samples" ? detailsRow.sample_id : selectedEntity === "bins" ? detailsRow.bin_id : ""}
              </div>
              <button className="ml-auto border rounded px-2 py-1" onClick={() => setDetailsRow(null)}>Close</button>
            </div>

            {selectedEntity === "samples" && detailsRow?.sample_id && (
              <SampleAbundance sampleId={detailsRow.sample_id} />
            )}

            {selectedEntity === "bins" && detailsRow?.bin_id && (
              <>
                <BinAbundance
                  binId={detailsRow.bin_id}
                  sampleId={detailsRow.sample_id}
                  abundance={detailsRow.abundance}
                />
                <BinPathways binId={detailsRow.bin_id} />
              </>
            )}

            {(selectedEntity !== "samples" && selectedEntity !== "bins") && (
              <div className="text-sm text-gray-500">Select a Sample or Bin to see details.</div>
            )}
          </div>
        )}

        {showNetwork && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center" onClick={() => setShowNetwork(false)}>
            <div className="bg-white rounded shadow-lg w-[980px] max-w-[96vw] max-h-[90vh] overflow-auto p-4" onClick={(e)=>e.stopPropagation()}>
              <div className="flex items-center mb-2">
                <h2 className="font-semibold text-lg">Isolate Interaction Network</h2>
                <button className="ml-auto border rounded px-2 py-1" onClick={() => setShowNetwork(false)}>Close</button>
              </div>
              <NetworkView />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
