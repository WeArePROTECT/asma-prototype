import { useEffect, useMemo, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Card, Button, Input, Space, Typography, Divider, Badge } from "antd";
import { SearchOutlined, ExportOutlined, NodeIndexOutlined, DatabaseOutlined } from "@ant-design/icons";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import DataTable from "./components/DataTable";
import { api } from "./lib/api";
import SampleAbundance from "./components/SampleAbundance";
import BinPathways from "./components/BinPathways";
import BinAbundance from "./components/BinAbundance";
import NetworkView from "./components/NetworkView";
import Landing from "./Landing";
import Footer from "./components/Footer";
import { useCart, CartProvider } from "./cart/CartContext";
import FormulationBuilder from "./formulation/FormulationBuilder";
import LineageView from './components/LineageView';

const { Title, Text } = Typography;

const qc = new QueryClient();
export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <CartProvider>
        <Shell />
      </CartProvider>
    </QueryClientProvider>
  );
}

type Entity = "patients" | "samples" | "bins" | "isolates";

function Shell() {
  const [route, setRoute] = useState<string>(() => window.location.hash || "#/landing");
  useEffect(() => {
    const onHash = () => setRoute(window.location.hash || "#/landing");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // Clean ?net when on landing so URL stays tidy
  useEffect(() => {
    if ((window.location.hash || "#/landing").startsWith("#/landing")) {
      const sp = new URLSearchParams(window.location.search);
      if (sp.has("net")) {
        sp.delete("net");
        const qs = sp.toString();
        window.history.replaceState({}, "", `${window.location.pathname}${qs ? "?" + qs : ""}#/landing`);
      }
    }
  }, [route]);

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      <Header />
      <div className="flex-1">
        {route.startsWith("#/landing") ? <Landing /> :  route.startsWith("#/formulate") ? <FormulationBuilder /> : <Root />}
      </div>
      <Footer />
    </div>
  );
}

// COMPLETELY SEPARATE COMPONENTS FOR EACH ENTITY
function PatientsTable({ searchTerm, onOpenLineage, onRowDetails, onOpenNetworkWithFocus }: any) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.patients();
        setData(result);
      } catch (error) {
        console.error("Failed to load patients:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <DataTable
      rows={data}
      entity="patients"
      onOpenLineage={onOpenLineage}
      onRowDetails={onRowDetails}
      onOpenNetworkWithFocus={onOpenNetworkWithFocus}
      searchTerm={searchTerm}
      loading={loading}
    />
  );
}

function SamplesTable({ searchTerm, onOpenLineage, onRowDetails, onOpenNetworkWithFocus }: any) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.samples();
        setData(result);
      } catch (error) {
        console.error("Failed to load samples:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <DataTable
      rows={data}
      entity="samples"
      onOpenLineage={onOpenLineage}
      onRowDetails={onRowDetails}
      onOpenNetworkWithFocus={onOpenNetworkWithFocus}
      searchTerm={searchTerm}
      loading={loading}
    />
  );
}

function BinsTable({ searchTerm, onOpenLineage, onRowDetails, onOpenNetworkWithFocus }: any) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.bins();
        setData(result);
      } catch (error) {
        console.error("Failed to load bins:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <DataTable
      rows={data}
      entity="bins"
      onOpenLineage={onOpenLineage}
      onRowDetails={onRowDetails}
      onOpenNetworkWithFocus={onOpenNetworkWithFocus}
      searchTerm={searchTerm}
      loading={loading}
    />
  );
}

function IsolatesTable({ searchTerm, onOpenLineage, onRowDetails, onOpenNetworkWithFocus }: any) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.isolates();
        setData(result);
      } catch (error) {
        console.error("Failed to load isolates:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <DataTable
      rows={data}
      entity="isolates"
      onOpenLineage={onOpenLineage}
      onRowDetails={onRowDetails}
      onOpenNetworkWithFocus={onOpenNetworkWithFocus}
      searchTerm={searchTerm}
      loading={loading}
    />
  );
}

function Root() {
  const [selectedEntity, setSelectedEntity] = useState<Entity>("patients");
  // Remove these unused state variables
  // const [selectedPatient, setSelectedPatient] = useState<string | undefined>();
  // const [selectedSample, setSelectedSample] = useState<string | undefined>();
  const [searchTerms, setSearchTerms] = useState<Record<Entity, string>>({
    patients: "",
    samples: "",
    bins: "",
    isolates: ""
  });
  const [lineage, setLineage] = useState<any | null>(null);
  const [detailsRow, setDetailsRow] = useState<any | null>(null);
  const [networkFocusId, setNetworkFocusId] = useState<string | undefined>(undefined);
  const [showNetwork, setShowNetwork] = useState(false);

  const { cartItems, addToCart, removeFromCart } = useCart();

  // Get current search term for selected entity
  const currentSearchTerm = searchTerms[selectedEntity];

  // Update search term for specific entity
  const updateSearchTerm = (entity: Entity, term: string) => {
    setSearchTerms(prev => ({
      ...prev,
      [entity]: term
    }));
  };

  // Handlers
  const onOpenLineage = async (row: any) => {
    try {
      if (selectedEntity === "patients") {
        const lineageData = await api.lineagePatient(row.patient_id);
        setLineage(lineageData);
      } else if (selectedEntity === "samples") {
        const lineageData = await api.lineageSample(row.sample_id);
        setLineage(lineageData);
      }
    } catch (error) {
      console.error("Failed to fetch lineage:", error);
    }
  };

  const onExport = () => {
    const href = api.downloadCsv(selectedEntity);
    const a = document.createElement("a");
    a.href = href;
    a.download = `${selectedEntity}.csv`;
    a.click();
  };

  const onOpenNetworkWithFocus = (id: string) => {
    setNetworkFocusId(id);
    setShowNetwork(true);
  };

  // Render the appropriate table component
  const renderTable = () => {
    const props = {
      searchTerm: currentSearchTerm,
      onOpenLineage,
      onRowDetails: setDetailsRow,
      onOpenNetworkWithFocus,
    };

    switch (selectedEntity) {
      case "patients":
        return <PatientsTable {...props} />;
      case "samples":
        return <SamplesTable {...props} />;
      case "bins":
        return <BinsTable {...props} />;
      case "isolates":
        return <IsolatesTable {...props} />;
      default:
        return <PatientsTable {...props} />;
    }
  };

  return (
    <div className="h-full flex bg-gradient-to-br from-slate-50 to-blue-50">
      <Sidebar
        selectedEntity={selectedEntity}
        setSelectedEntity={setSelectedEntity}
      />

      <main className="flex-1 p-6 space-y-6">
        {/* Header Section */}
        <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <DatabaseOutlined className="text-2xl text-blue-600" />
                <Title level={2} className="!mb-0 !text-gray-800">
                  ASMA Universal Browser
                </Title>
              </div>
              <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                API: {api.base}
              </div>
            </div>
            
            <Space size="middle">
              <Input
                placeholder={`Search ${selectedEntity}...`}
                prefix={<SearchOutlined className="text-gray-400" />}
                value={currentSearchTerm}
                onChange={(e) => updateSearchTerm(selectedEntity, e.target.value)}
                style={{ width: 280 }}
                className="shadow-sm"
                allowClear
              />
              <Button 
                type="primary" 
                icon={<NodeIndexOutlined />}
                onClick={() => setShowNetwork(true)}
                className="shadow-sm"
              >
                Open Network
              </Button>
              <Button 
                icon={<ExportOutlined />}
                onClick={onExport}
                className="shadow-sm"
              >
                Export CSV
              </Button>
            </Space>
          </div>
        </Card>

        {/* Data Table Section */}
        <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
          {renderTable()}
        </Card>

        {/* Lineage Modal */}
        {lineage && (
          <LineageView 
            lineage={lineage} 
            entity={selectedEntity} 
            onClose={() => setLineage(null)} 
          />
        )}

        {/* Details Panel */}
        {detailsRow && (
          <div className="fixed bottom-6 right-6 left-6 md:left-auto md:w-[580px] bg-white/95 backdrop-blur-sm border-0 shadow-2xl rounded-xl p-6 space-y-4">
            <div className="flex items-center">
              <div className="font-semibold text-lg text-gray-800">
                Details — {selectedEntity === "samples" ? detailsRow.sample_id : selectedEntity === "bins" ? detailsRow.bin_id : ""}
              </div>
              <Button 
                type="text" 
                className="ml-auto text-gray-500 hover:text-gray-700" 
                onClick={() => setDetailsRow(null)}
              >
                ×
              </Button>
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
              <div className="text-sm text-gray-500 text-center py-4">Select a Sample or Bin to see details.</div>
            )}
          </div>
        )}

        {/* Network Modal */}
        {showNetwork && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowNetwork(false)}>
            <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl w-[1024px] max-w-[96vw] max-h-[92vh] overflow-hidden" onClick={(e)=>e.stopPropagation()}>
              <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
                <div className="flex items-center space-x-3">
                  <NodeIndexOutlined className="text-2xl text-blue-600" />
                  <Title level={3} className="!mb-0 !text-gray-800">
                    Isolate Interaction Network
                  </Title>
                </div>
                <Button 
                  type="text" 
                  className="text-gray-500 hover:text-gray-700" 
                  onClick={() => setShowNetwork(false)}
                >
                  ×
                </Button>
              </div>
              <div className="p-6">
                <NetworkView initialFocusId={networkFocusId ?? undefined} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}