// Drop-in API client with working previewFormulation()
// - Reads base URL from localStorage key 'asma_api_base' (fallback http://127.0.0.1:8000)
// - Matches your FastAPI endpoints used elsewhere

type NetworkParams = {
  isolate_id?: string;
  type?: string;            // 'All' | 'complementarity' | 'cooccurrence' | 'inhibition' | 'competition'
  max_neighbors?: number;
};

function base() {
  const v = (typeof window !== 'undefined') ? (localStorage.getItem('asma_api_base') || '') : '';
  return v || 'http://127.0.0.1:8000';
}

async function getJson<T>(path: string) : Promise<T> {
  const res = await fetch(base() + path);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

async function postJson<T>(path: string, body: any) : Promise<T> {
  const res = await fetch(base() + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const txt = await res.text().catch(()=>'');
    throw new Error(`POST ${path} -> ${res.status} ${txt}`);
  }
  return res.json();
}

export const api = {
  base,

  patients: () => getJson<any[]>('/patients'),
  samples: (patient_id?: string) => getJson<any[]>('/samples' + (patient_id ? `?patient_id=${encodeURIComponent(patient_id)}` : '')),
  bins: (sample_id?: string) => getJson<any[]>('/bins' + (sample_id ? `?sample_id=${encodeURIComponent(sample_id)}` : '')),
  isolates: (sample_id?: string, bin_id?: string) => {
    const p = new URLSearchParams();
    if (sample_id) p.set('sample_id', sample_id);
    if (bin_id) p.set('bin_id', bin_id);
    const q = p.toString();
    return getJson<any[]>('/isolates' + (q ? `?${q}` : ''));
  },
  isolate: (id: string) => getJson<any>(`/isolates/${encodeURIComponent(id)}`),
  prebiotics: () => getJson<any[]>('/prebiotics'),

  // Add the missing abundance functions
  sampleAbundance: (sample_id: string) => getJson<any>(`/samples/${encodeURIComponent(sample_id)}/abundance`),
  binAbundance: (bin_id: string) => getJson<any>(`/bins/${encodeURIComponent(bin_id)}/abundance`),

  lineagePatient: (patient_id: string) => getJson<any>(`/lineage/patient/${encodeURIComponent(patient_id)}`),
  lineageSample: (sample_id: string) => getJson<any>(`/lineage/sample/${encodeURIComponent(sample_id)}`),

  // Search function
  search: (q: string) => getJson<any>(`/search?q=${encodeURIComponent(q)}`),

  network: (params: NetworkParams = {}) => {
    const p = new URLSearchParams();
    if (params.isolate_id) p.set('isolate_id', params.isolate_id);
    if (params.type && params.type !== 'All') p.set('type', params.type);
    if (params.max_neighbors != null) p.set('max_neighbors', String(params.max_neighbors));
    const q = p.toString();
    return getJson<any>('/network' + (q ? `?${q}` : ''));
  },

  // Sprint E+: prediction preview
  previewFormulation: (payload: { organisms: string[]; prebiotics?: string[] }) =>
    postJson<any>('/formulations/preview', payload),

  // CSV download helper for the Browser Export CSV button (optional)
  downloadCsv: async (kind: 'patients'|'samples'|'bins'|'isolates'|'interactions') => {
    const url = base() + `/download/${kind}.csv`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`GET ${url} -> ${res.status}`);
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${kind}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },

  binPathways: (bin_id: string) => getJson<any>(`/bins/${encodeURIComponent(bin_id)}/pathways`),
};
