# app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import csv, json
from pydantic import BaseModel
from typing import List
import math

app = FastAPI(title="ASMA Demo API", version="0.1.0")

# ---- CORS (dev) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---- Helpers ----
def load_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    # If someone saved as a JSON array instead of JSONL, accept it.
    if text.lstrip().startswith("["):
        return json.loads(text)
    # Otherwise treat as newline-delimited JSON (one object per line)
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    return items

def paginate(items, limit: int, offset: int):
    total = len(items)
    return {"total": total, "limit": limit, "offset": offset, "items": items[offset: offset + limit]}

def sort_items(items, sort: Optional[str]):
    if not sort:
        return items
    key = sort.lstrip("-")
    reverse = sort.startswith("-")
    return sorted(items, key=lambda x: x.get(key), reverse=reverse)

# ---- Pydantic models (stable shapes for the UI) ----
class Patient(BaseModel):
    patient_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    condition: Optional[str] = None
    cohort: Optional[str] = None

class Sample(BaseModel):
    sample_id: str
    patient_id: str
    sample_type: Optional[str] = None
    collection_date: Optional[str] = None
    project_id: Optional[str] = None

class Bin(BaseModel):
    bin_id: str
    sample_id: str
    taxon: Optional[str] = None
    completeness: Optional[float] = Field(None, description="%")
    contamination: Optional[float] = Field(None, description="%")

class Isolate(BaseModel):
    isolate_id: str
    name: Optional[str] = None
    taxonomy: Optional[str] = None
    amr_genes: Optional[List[str]] = None
    linked_bins: List[str] = []

class Interaction(BaseModel):
    source: str
    target: str
    kind: str          # e.g. "cooccurrence" | "competition" | "complementarity"
    score: float

class FormulationComponent(BaseModel):
    isolate_id: str
    role: str          # "organism" | "prebiotic"

class Formulation(BaseModel):
    formulation_id: str
    name: str
    components: List[FormulationComponent]
    score: Optional[float] = None

# ---- Load demo data ----
patients: List[Dict[str, Any]] = load_csv("demo_data/patients.csv")
samples: List[Dict[str, Any]] = load_csv("demo_data/samples.csv")
bins: List[Dict[str, Any]] = load_jsonl("demo_data/bins.jsonl")
isolates: List[Dict[str, Any]] = load_jsonl("demo_data/isolates.jsonl")
interactions: List[Dict[str, Any]] = load_json("demo_data/interactions.json")
prebiotics: List[Dict[str, Any]] = load_csv("demo_data/prebiotics.csv")
formulations: Dict[str, Any] = load_json("demo_data/formulations.json")

# ---- Indices for fast lookups ----
P = {p["patient_id"]: p for p in patients}
S = {s["sample_id"]: s for s in samples}
B = {b["bin_id"]: b for b in bins}
I = {i["isolate_id"]: i for i in isolates}

# ---- Health ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- Patients ----
@app.get("/patients", response_model=Dict[str, Any])
def get_patients(q: Optional[str] = None, sort: Optional[str] = None,
                 limit: int = 100, offset: int = 0):
    items = patients
    if q:
        ql = q.lower()
        items = [p for p in items if ql in p["patient_id"].lower()
                 or ql in (p.get("condition","").lower())]
    items = sort_items(items, sort)
    return paginate(items, limit, offset)

@app.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: str):
    p = P.get(patient_id)
    if not p: raise HTTPException(404, "Patient not found")
    return p

# ---- Samples ----
@app.get("/samples", response_model=Dict[str, Any])
def get_samples(patient_id: Optional[str] = None, q: Optional[str] = None,
                sort: Optional[str] = None, limit: int = 100, offset: int = 0):
    items = samples
    if patient_id:
        items = [s for s in items if s["patient_id"] == patient_id]
    if q:
        ql = q.lower()
        items = [s for s in items if ql in s["sample_id"].lower()
                 or ql in (s.get("sample_type","").lower())]
    items = sort_items(items, sort)
    return paginate(items, limit, offset)

@app.get("/samples/{sample_id}", response_model=Sample)
def get_sample(sample_id: str):
    s = S.get(sample_id)
    if not s: raise HTTPException(404, "Sample not found")
    return s

# ---- Bins ----
@app.get("/bins", response_model=Dict[str, Any])
def get_bins(sample_id: Optional[str] = None, q: Optional[str] = None,
             sort: Optional[str] = None, limit: int = 100, offset: int = 0):
    items = bins
    if sample_id:
        items = [b for b in items if b["sample_id"] == sample_id]
    if q:
        ql = q.lower()
        items = [b for b in items if ql in b["bin_id"].lower()
                 or ql in (b.get("taxon","").lower())]
    items = sort_items(items, sort)
    return paginate(items, limit, offset)

@app.get("/bins/{bin_id}", response_model=Bin)
def get_bin(bin_id: str):
    b = B.get(bin_id)
    if not b: raise HTTPException(404, "Bin not found")
    return b

# ---- Isolates ----
@app.get("/isolates", response_model=Dict[str, Any])
def get_isolates(bin_id: Optional[str] = None, q: Optional[str] = None,
                 sort: Optional[str] = None, limit: int = 100, offset: int = 0):
    items = isolates
    if bin_id:
        items = [i for i in items if bin_id in i.get("linked_bins", [])]
    if q:
        ql = q.lower()
        items = [i for i in items if ql in i["isolate_id"].lower()
                 or ql in (i.get("name","").lower())
                 or ql in (i.get("taxonomy","").lower())]
    items = sort_items(items, sort)
    return paginate(items, limit, offset)

@app.get("/isolates/{isolate_id}")
def get_isolate_by_id(isolate_id: str):
    for i in isolates:
        if i["isolate_id"] == isolate_id:
            return i
    return {"error": f"Isolate {isolate_id} not found"}

# ---- Interactions / Prebiotics / Formulations ----
@app.get("/interactions", response_model=List[Interaction])
def get_interactions():
    return interactions

@app.get("/prebiotics")
def get_prebiotics():
    return prebiotics

@app.get("/formulations", response_model=Any)
def get_formulations():
    return formulations

# ---- Lineage helpers ----
@app.get("/lineage/patient/{patient_id}")
def lineage_patient(patient_id: str):
    if patient_id not in P: raise HTTPException(404, "Patient not found")
    samps = [s for s in samples if s["patient_id"] == patient_id]
    samp_ids = {s["sample_id"] for s in samps}
    bs = [b for b in bins if b["sample_id"] in samp_ids]
    bin_ids = {b["bin_id"] for b in bs}
    isos = [i for i in isolates if any(bid in bin_ids for bid in i.get("linked_bins", []))]
    return {"patient": P[patient_id], "samples": samps, "bins": bs, "isolates": isos}

@app.get("/lineage/sample/{sample_id}")
def lineage_sample(sample_id: str):
    if sample_id not in S: raise HTTPException(404, "Sample not found")
    bs = [b for b in bins if b["sample_id"] == sample_id]
    bin_ids = {b["bin_id"] for b in bs}
    isos = [i for i in isolates if any(bid in bin_ids for bid in i.get("linked_bins", []))]
    return {"sample": S[sample_id], "bins": bs, "isolates": isos}

# ---- Universal Search ----
@app.get("/search")
def search(q: str = Query(..., min_length=1)):
    ql = q.lower()
    return {
        "patients": [p for p in patients if ql in p["patient_id"].lower() or ql in (p.get("condition","").lower())],
        "samples":  [s for s in samples  if ql in s["sample_id"].lower() or ql in (s.get("sample_type","").lower())],
        "bins":     [b for b in bins     if ql in b["bin_id"].lower()     or ql in (b.get("taxon","").lower())],
        "isolates": [i for i in isolates if ql in i["isolate_id"].lower() or ql in (i.get("name","").lower())
                                       or ql in (i.get("taxonomy","").lower())],
    }

# ---- Others ----

# Example: return just pathways for a bin
@app.get("/bins/{bin_id}/pathways")
def bin_pathways(bin_id: str):
    b = next((x for x in bins if x["bin_id"] == bin_id), None)
    if not b: raise HTTPException(404, "Bin not found")
    return {"bin_id": bin_id, "pathways": b.get("pathways_scored") or [{"pathway": p, "score": None} for p in b.get("pathways", [])]}

# Bin Pathways
@app.get("/bins/{bin_id}/pathways")
def bin_pathways(bin_id: str):
    b = next((x for x in bins if x["bin_id"] == bin_id), None)
    if not b:
        raise HTTPException(404, "Bin not found")
    scored = b.get("pathways_scored")
    if scored:
        return {"bin_id": bin_id, "pathways": scored}
    # fallback to unscored list if present
    return {"bin_id": bin_id, "pathways": [{"pathway": p, "score": None, "evidence": None} for p in b.get("pathways", [])]}

# Sample Abundance for bar charts
@app.get("/samples/{sample_id}/abundance")
def sample_abundance(sample_id: str):
    # verify sample exists (optional)
    if not any(s["sample_id"] == sample_id for s in samples):
        raise HTTPException(404, "Sample not found")
    b = [x for x in bins if x["sample_id"] == sample_id]
    resp = [{"bin_id": x["bin_id"], "taxonomy": x.get("taxonomy"), "abundance": x.get("abundance", 0)} for x in b]
    total = sum(x.get("abundance", 0) for x in b)
    return {"sample_id": sample_id, "bins": resp, "total_abundance": round(total, 6)}

# Isolate omics summary
@app.get("/isolates/{isolate_id}/omics")
def isolate_omics(isolate_id: str):
    i = next((x for x in isolates if x["isolate_id"] == isolate_id), None)
    if not i:
        raise HTTPException(404, "Isolate not found")
    return {
        "isolate_id": isolate_id,
        "growth_media": i.get("growth_media"),
        "metabolite_markers": i.get("metabolite_markers", []),
        "genome_depot_id": i.get("genome_depot_id"),
    }

# Interaction network
@app.get("/network")
def network(isolate_id: str | None = None, type: str | None = None):
    edges = interactions
    if isolate_id:
        edges = [e for e in edges if e["source_isolate"] == isolate_id or e["target_isolate"] == isolate_id]
    if type:
        edges = [e for e in edges if e["type"] == type]
    node_ids = set()
    for e in edges:
        node_ids.add(e["source_isolate"]); node_ids.add(e["target_isolate"])
    id_to_label = {i["isolate_id"]: i.get("taxonomy") or i["isolate_id"] for i in isolates}
    nodes = [{"id": n, "label": id_to_label.get(n, n)} for n in sorted(node_ids)]
    edges_out = [{"source": e["source_isolate"], "target": e["target_isolate"], "type": e["type"], "score": e["score"]} for e in edges]
    return {"nodes": nodes, "edges": edges_out}

# Formulation preview
class FormulationPreviewIn(BaseModel):
    organisms: List[str]
    prebiotics: List[str]

@app.post("/formulations/preview")
def formulation_preview(payload: FormulationPreviewIn):
    # Very dumb stub: more organisms + any prebiotic → higher score, but cap at 0.9
    base = 0.4 + 0.1 * len(set(payload.organisms))
    if payload.prebiotics:
        base += 0.15
    score = min(0.9, round(base, 2))
    notes = f"Stubbed score based on {len(set(payload.organisms))} organism(s) and {len(set(payload.prebiotics))} prebiotic(s)."
    return {"score_predicted": score, "notes": notes}