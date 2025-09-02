import React from "react";
import { useCart } from "../cart/CartContext";
import { api } from "../lib/api";
import MiniNetworkPreview from "./MiniNetworkPreview";

// Button utilities using existing CSS classes
function Button({ kind="secondary", ...props }: any) {
  const baseClass = "btn";
  const cls = kind === "primary" ? `${baseClass} bg-emerald-600 text-white border-emerald-700 hover:bg-emerald-700` : baseClass;
  return <button {...props} className={cls + " " + (props.className || "")} />;
}

// Card component using existing CSS
function Card({ title, right, children }:{
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section style={{ 
      borderRadius: '12px', 
      border: '1px solid #e5e7eb', 
      backgroundColor: 'white', 
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 
      padding: '16px 20px' 
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', margin: 0 }}>{title}</h2>
        <div style={{ marginLeft: 'auto' }}>{right}</div>
      </div>
      <div style={{ marginTop: '12px' }}>{children}</div>
    </section>
  );
}

// Chip component
function Chip({ children, onRemove }:{
  children: React.ReactNode; 
  onRemove?: () => void;
}) {
  return (
    <span style={{ 
      display: 'inline-flex', 
      alignItems: 'center', 
      gap: '8px', 
      borderRadius: '9999px', 
      border: '1px solid #e5e7eb', 
      padding: '4px 12px', 
      fontSize: '14px', 
      backgroundColor: '#f8fafc' 
    }}>
      {children}
      {onRemove && (
        <button 
          aria-label="Remove" 
          style={{ 
            fontSize: '12px', 
            border: '1px solid #d1d5db', 
            borderRadius: '4px', 
            padding: '2px 6px', 
            cursor: 'pointer',
            backgroundColor: 'white'
          }}
          onClick={onRemove}
        >
          ×
        </button>
      )}
    </span>
  );
}

// Tooltip component
function Tooltip({ children, tip }:{
  children: React.ReactNode; 
  tip: React.ReactNode;
}) {
  return (
    <span style={{ position: 'relative' }} className="group">
      {children}
      <span style={{ 
        pointerEvents: 'none', 
        position: 'absolute', 
        zIndex: 20, 
        display: 'none',
        left: 0, 
        top: '110%', 
        width: '288px', 
        borderRadius: '6px', 
        border: '1px solid #e5e7eb', 
        backgroundColor: 'white', 
        padding: '12px', 
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' 
      }} className="group-hover:block group-focus-within:block">
        <div style={{ fontSize: '14px' }}>{tip}</div>
      </span>
    </span>
  );
}

// Score visualization component
function ScoreDisplay({ score }: { score: number | null }) {
  const barColor = (s?: number | null) => {
    if (s == null) return "#d1d5db";
    if (s < 0.33) return "#ef4444";
    if (s < 0.66) return "#f59e0b";
    return "#10b981";
  };
  
  return (
    <div>
      <div style={{ fontSize: '14px', color: '#64748b' }}>Predicted score</div>
      <div style={{ marginTop: '4px', fontSize: '30px', fontWeight: 'bold' }}>
        {score != null ? score.toFixed(2) : "—"}
      </div>
      <div style={{ 
        marginTop: '8px', 
        height: '8px', 
        width: '100%', 
        borderRadius: '4px', 
        backgroundColor: '#e2e8f0' 
      }}>
        <div 
          style={{ 
            height: '8px', 
            borderRadius: '4px', 
            backgroundColor: barColor(score),
            width: `${Math.max(0, Math.min(1, score || 0)) * 100}%`,
            transition: 'all 0.3s ease'
          }} 
        />
      </div>
    </div>
  );
}

// Helper function for note icons
function iconFor(n: string) {
  if (/prebiotic/i.test(n)) return "🍃";
  if (/inhib|compet/i.test(n)) return "⚠️";
  if (/complement/i.test(n)) return "✅";
  return "ℹ️";
}

// Helper function to extract interaction data from notes
function extractInteractionData(notes: string[]) {
  const data = {
    complementarity: { count: 0, mentions: [] },
    inhibition: { count: 0, mentions: [] },
    competition: { count: 0, mentions: [] }
  };

  notes.forEach(note => {
    const lowerNote = note.toLowerCase();
    if (lowerNote.includes('complementarity') || lowerNote.includes('complement')) {
      data.complementarity.count++;
      data.complementarity.mentions.push(note);
    }
    if (lowerNote.includes('inhibition') || lowerNote.includes('inhib')) {
      data.inhibition.count++;
      data.inhibition.mentions.push(note);
    }
    if (lowerNote.includes('competition') || lowerNote.includes('compet')) {
      data.competition.count++;
      data.competition.mentions.push(note);
    }
  });

  return data;
}

// Enhanced BreakdownRow component to handle cooccurrence
function BreakdownRow({ interactionType, color, interactionData, hasDetailedMetrics }: { 
  interactionType: "complementarity"|"inhibition"|"competition"|"cooccurrence"; 
  color: string; 
  interactionData: any;
  hasDetailedMetrics: boolean;
}) {
  const data = interactionData[interactionType];
  const count = data?.count ?? 0;
  
  // If we have detailed metrics, use them; otherwise show what we can extract from notes
  const sum = hasDetailedMetrics ? (data?.sum ?? 0) : count;
  const avg = hasDetailedMetrics ? (data?.avg ?? 0) : (count > 0 ? 1 : 0);
  
  console.log(`BreakdownRow ${interactionType}:`, { count, sum, avg, hasDetailedMetrics });
  
  return (
    <tr style={{ borderTop: '1px solid #e2e8f0' }}>
      <td style={{ padding: '8px 12px' }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <i style={{ 
            backgroundColor: color, 
            display: 'inline-block', 
            width: '12px', 
            height: '12px', 
            borderRadius: '50%' 
          }} />
          <span style={{ textTransform: 'capitalize', fontWeight: '500' }}>{interactionType}</span>
        </span>
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'center', fontVariantNumeric: 'tabular-nums', fontWeight: '500' }}>{count}</td>
      <td style={{ padding: '8px 12px', textAlign: 'center', fontVariantNumeric: 'tabular-nums', fontWeight: '500' }}>
        {hasDetailedMetrics ? sum.toFixed(2) : (count > 0 ? 'Present' : '—')}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'center', fontVariantNumeric: 'tabular-nums', fontWeight: '500' }}>
        {hasDetailedMetrics ? avg.toFixed(2) : (count > 0 ? 'Active' : '—')}
      </td>
    </tr>
  );
}

export default function FormulationBuilder() {
  const { isolates, prebiotics, setPrebiotics, removeIsolate, clear } = useCart();
  const [pb, setPB] = React.useState<string[]>(prebiotics);
  const [score, setScore] = React.useState<number | null>(null);
  const [notes, setNotes] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isolateDetails, setIsolateDetails] = React.useState<Record<string, any>>({});
  // Add state for detailed interaction data
  const [interactionBreakdown, setInteractionBreakdown] = React.useState<any>(null);

  React.useEffect(() => setPB(prebiotics), [prebiotics]);

  // Load isolate details for tooltips
  React.useEffect(() => {
    const loadDetails = async () => {
      const details: Record<string, any> = {};
      for (const id of isolates) {
        if (!isolateDetails[id]) {
          try {
            const data = await api.isolate(id);
            details[id] = data;
          } catch {
            details[id] = null;
          }
        }
      }
      setIsolateDetails(prev => ({ ...prev, ...details }));
    };
    
    if (isolates.length > 0) {
      loadDetails();
    }
  }, [isolates]);

  async function preview() {
    setLoading(true);
    setError(null);
    try {
      // First call without debug to get basic response
      const res = await api.previewFormulation({ organisms: isolates, prebiotics: pb });
      setScore(res.score_predicted ?? null);
      setNotes(Array.isArray(res.notes) ? res.notes : []);
      
      // Now call with debug parameter as query string to get detailed breakdown
      const debugRes = await fetch(`${api.base()}/formulations/preview?debug=1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ organisms: isolates, prebiotics: pb }),
      });
      
      if (debugRes.ok) {
        const debugData = await debugRes.json();
        console.log('DEBUG DATA:', debugData);
        setInteractionBreakdown(debugData);
      } else {
        console.log('DEBUG API ERROR:', debugRes.status, await debugRes.text());
      }
    } catch (err) {
      console.log('PREVIEW ERROR:', err);
      setError(err instanceof Error ? err.message : 'Failed to preview formulation');
    } finally { 
      setLoading(false); 
    }
  }

  function exportCSV() {
    const rows = [["isolate_id"], ...isolates.map(id => [id])];
    if (score != null) rows.push(["score_predicted", String(score)]);
    const text = rows.map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "formulation.csv"; 
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function copyJSON() {
    const payload = { organisms: isolates, prebiotics: pb, score_predicted: score, notes };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2)).catch(()=>{});
    alert("Copied JSON to clipboard");
  }

  function saveFormulation() {
    const payload = { 
      isolates, 
      prebiotics: pb, 
      score_predicted: score, 
      notes,
      created_at: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `formulation-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // Use detailed metrics from backend instead of parsing notes
  const interactionData = React.useMemo(() => {
    if (interactionBreakdown) {
      // Use the detailed metrics from the backend
      const data = {
        complementarity: { 
          count: interactionBreakdown.counts?.complementarity || 0,
          sum: interactionBreakdown.sum_complementarity || 0,
          avg: interactionBreakdown.counts?.complementarity ? 
               (interactionBreakdown.sum_complementarity / interactionBreakdown.counts.complementarity) : 0
        },
        inhibition: { 
          count: interactionBreakdown.counts?.inhibition || 0,
          sum: interactionBreakdown.sum_inhibition || 0,
          avg: interactionBreakdown.avg_inhibition || 0
        },
        competition: { 
          count: interactionBreakdown.counts?.competition || 0,
          sum: interactionBreakdown.sum_competition || 0,
          avg: interactionBreakdown.counts?.competition ? 
               (interactionBreakdown.sum_competition / interactionBreakdown.counts.competition) : 0
        },
        cooccurrence: { 
          count: interactionBreakdown.counts?.cooccurrence || 0,
          sum: interactionBreakdown.sum_cooccurrence || 0,
          avg: interactionBreakdown.counts?.cooccurrence ? 
               (interactionBreakdown.sum_cooccurrence / interactionBreakdown.counts.cooccurrence) : 0
        }
      };
      console.log('PROCESSED INTERACTION DATA:', data); // Add this line
      return data;
    } else {
      // Fallback to parsing notes if no detailed data - ensure all properties exist
      const fallbackData = extractInteractionData(notes);
      const data = {
        complementarity: fallbackData.complementarity || { count: 0, mentions: [] },
        inhibition: fallbackData.inhibition || { count: 0, mentions: [] },
        competition: fallbackData.competition || { count: 0, mentions: [] },
        cooccurrence: { count: 0, mentions: [] } // Add cooccurrence to fallback
      };
      console.log('FALLBACK INTERACTION DATA:', data); // Add this line
      return data;
    }
  }, [interactionBreakdown, notes]);
  
  // Check if we have any interaction data
  const hasInteractions = interactionData.complementarity.count > 0 || 
                         interactionData.inhibition.count > 0 || 
                         interactionData.competition.count > 0;

  return (
    <div style={{ 
      maxWidth: '1152px', 
      margin: '0 auto', 
      padding: '24px', 
      backgroundColor: '#f8fafc' 
    }}>
      {/* Toolbar */}
      <header style={{ marginBottom: '16px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '600', margin: 0 }}>Formulation Builder</h1>
        <div style={{ marginLeft: 'auto', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <Button 
            onClick={saveFormulation} 
            disabled={!isolates.length}
            aria-label="Save formulation as JSON file"
          >
            Save JSON
          </Button>
          <Button 
            onClick={copyJSON} 
            disabled={!isolates.length}
            aria-label="Copy formulation as JSON"
          >
            Copy JSON
          </Button>
          <Button 
            onClick={exportCSV} 
            disabled={!isolates.length}
            aria-label="Export formulation as CSV"
          >
            Export CSV
          </Button>
          <Button 
            onClick={() => { if (confirm('Clear formulation?')) clear(); }}
            aria-label="Clear all selections"
          >
            Clear
          </Button>
        </div>
      </header>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr', 
        gap: '24px',
        '@media (min-width: 1024px)': {
          gridTemplateColumns: '3fr 1fr'
        }
      }}>
        {/* LEFT – main content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Selected isolates */}
          <Card 
            title={`Selected isolates (${isolates.length})`} 
            right={isolates.length > 0 && (
              <Button onClick={() => { if (confirm('Clear all isolates?')) clear(); }} aria-label="Clear selection">
                Clear
              </Button>
            )}
          >
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
              gap: '16px' 
            }}>
              {isolates.map(id => (
                <Tooltip key={id} tip={
                  <div>
                    <div style={{ fontSize: '12px', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', fontWeight: '600' }}>Taxonomy</div>
                    <div style={{ fontSize: '14px' }}>{isolateDetails[id]?.taxonomy ?? isolateDetails[id]?.taxid_genus ?? "—"}</div>
                    {isolateDetails[id]?.amr_flags?.length ? (
                      <>
                        <div style={{ marginTop: '8px', fontSize: '12px', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', fontWeight: '600' }}>AMR flags</div>
                        <div style={{ fontSize: '14px' }}>{isolateDetails[id].amr_flags.join(", ")}</div>
                      </>
                    ) : null}
                  </div>
                }>
                  <div style={{ 
                    borderRadius: '8px', 
                    border: '1px solid #e5e7eb', 
                    padding: '16px', 
                    backgroundColor: '#f8fafc',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s ease'
                  }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '8px' }}>
                      <Chip onRemove={() => removeIsolate(id)}>{id}</Chip>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ fontSize: '12px', fontWeight: '600', color: '#374151', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Taxonomy</div>
                      <div style={{ fontSize: '14px', color: '#1f2937', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {isolateDetails[id]?.taxid_genus ?? isolateDetails[id]?.taxonomy ?? "—"}
                      </div>
                      {isolateDetails[id]?.amr_flags?.length ? (
                        <>
                          <div style={{ fontSize: '12px', fontWeight: '600', color: '#374151', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '8px' }}>AMR Flags</div>
                          <div style={{ fontSize: '12px', color: '#4b5563', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {isolateDetails[id].amr_flags.join(", ")}
                          </div>
                        </>
                      ) : null}
                    </div>
                  </div>
                </Tooltip>
              ))}
              {isolates.length === 0 && (
                <div style={{ fontSize: '14px', color: '#6b7280', gridColumn: '1 / -1', textAlign: 'center', padding: '32px' }}>
                  Add isolates from the Network view.
                </div>
              )}
            </div>
          </Card>

          {/* Prebiotics */}
          <Card title="Prebiotics">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>Prebiotic:</label>
                <select
                  style={{ 
                    border: '1px solid #d1d5db', 
                    borderRadius: '6px', 
                    padding: '8px 12px', 
                    flex: 1 
                  }}
                  value={pb[0] ?? ""}
                  onChange={(e) => setPB(e.target.value ? [e.target.value] : [])}
                  aria-label="Select prebiotic"
                >
                  <option value="">— none —</option>
                  <option value="PB001">PB001</option>
                  <option value="PB002">PB002</option>
                </select>
                <div style={{ marginLeft: '8px' }}>
                  {pb[0] && <Chip onRemove={() => setPB([])}>{pb[0]}</Chip>}
                </div>
              </div>
            </div>
          </Card>

          {/* Breakdown */}
          <Card title="Breakdown">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
              {/* Notes */}
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Notes</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(notes?.length ? notes : ["No notable interactions reported."]).map((n, i) => (
                    <div key={i} style={{ 
                      borderRadius: '6px', 
                      border: '1px solid #e5e7eb', 
                      padding: '12px', 
                      backgroundColor: '#f8fafc', 
                      fontSize: '14px', 
                      display: 'flex', 
                      alignItems: 'flex-start', 
                      gap: '8px' 
                    }}>
                      <span style={{ marginTop: '2px' }}>{iconFor(n)}</span>
                      <span>{n}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Interaction summary table */}
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Interaction Summary</h3>
                <div style={{ overflow: 'hidden', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                  <table style={{ width: '100%', fontSize: '14px' }}>
                    <thead style={{ backgroundColor: '#f1f5f9' }}>
                      <tr>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Type</th>
                        <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>Count</th>
                        <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>Status</th>
                        <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>Level</th>
                      </tr>
                    </thead>
                    <tbody style={{ backgroundColor: 'white' }}>
                      <BreakdownRow key="complementarity" interactionType="complementarity" color="#2563eb" interactionData={interactionData} hasDetailedMetrics={!!interactionBreakdown} />
                      <BreakdownRow key="inhibition" interactionType="inhibition" color="#ef4444" interactionData={interactionData} hasDetailedMetrics={!!interactionBreakdown} />
                      <BreakdownRow key="competition" interactionType="competition" color="#6b7280" interactionData={interactionData} hasDetailedMetrics={!!interactionBreakdown} />
                      <BreakdownRow key="cooccurrence" interactionType="cooccurrence" color="#10b981" interactionData={interactionData} hasDetailedMetrics={!!interactionBreakdown} />
                    </tbody>
                  </table>
                </div>
                {hasInteractions ? (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#059669', textAlign: 'center' }}>
                    ✓ Interaction data extracted from backend metrics
                  </div>
                ) : (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280', textAlign: 'center' }}>
                    No interactions detected in current formulation
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* RIGHT – sticky utility panel */}
        <aside style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '24px',
          position: 'sticky',
          top: '64px'
        }}>
          <Card 
            title="Score" 
            right={
              <Button 
                kind="primary"
                onClick={preview} 
                disabled={loading || isolates.length === 0} 
                aria-label="Preview score"
              >
                {loading ? "Calculating…" : "Preview score"}
              </Button>
            }
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {error && (
                <div style={{ 
                  borderRadius: '6px', 
                  border: '1px solid #fecaca', 
                  backgroundColor: '#fef2f2', 
                  color: '#dc2626', 
                  padding: '8px', 
                  fontSize: '14px' 
                }}>
                  {error}
                </div>
              )}
              
              {score != null && <ScoreDisplay score={score} />}
              
              {/* Secondary actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Button 
                  onClick={saveFormulation} 
                  disabled={!isolates.length}
                  aria-label="Save formulation as JSON file"
                >
                  Save JSON
                </Button>
                <Button 
                  onClick={copyJSON} 
                  disabled={!isolates.length}
                  aria-label="Copy formulation as JSON"
                >
                  Copy JSON
                </Button>
                <Button 
                  onClick={exportCSV} 
                  disabled={!isolates.length}
                  aria-label="Export formulation as CSV"
                >
                  Export CSV
                </Button>
                <Button 
                  onClick={() => { if (confirm('Clear formulation?')) clear(); }}
                  aria-label="Clear all selections"
                >
                  Clear
                </Button>
              </div>
            </div>
          </Card>

          {/* Mini Network Preview moved to right column */}
          <Card title="Network Preview">
            <MiniNetworkPreview isolateIds={isolates} />
          </Card>
        </aside>
      </div>
    </div>
  );
}
