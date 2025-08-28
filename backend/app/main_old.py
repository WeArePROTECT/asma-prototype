from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import csv
import json
import os
import io

app = FastAPI(title="ASMA Demo API", version="0.3.0")

# --- Resolve repo root and data directory ---
# main.py is at: <repo_root>/backend/app/main.py
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# Allow either ASMA_DATA_DIR or DEMO_DATA_DIR (fallback to repo/demo_data)
DATA_DIR_ENV = os.getenv("ASMA_DATA_DIR") or os.getenv("DEMO_DATA_DIR")
DATA_DIR: Path = Path(DATA_DIR_ENV or (REPO_ROOT / "demo_data")).resolve()

print(f"[ASMA] REPO_ROOT = {REPO_ROOT}")
print(f"[ASMA] DATA_DIR  = {DATA_DIR}")

if not DATA_DIR.exists():
    raise RuntimeError(
        f"Demo data folder not found: {DATA_DIR}. "
        f"Set ASMA_DATA_DIR (preferred) or DEMO_DATA_DIR if your data lives elsewhere."
    )

# ---- Helpers ----
def load_csv(path: Path) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Tolerant loader: supports JSONL or a JSON array."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    if text.lstrip().startswith("["):
        return json.loads(text)
    items: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    return items

# ---- Load demo data (absolute paths) ----
patients     = load_csv(DATA_DIR / "patients.csv")
samples      = load_csv(DATA_DIR / "samples.csv")
bins         = load_jsonl(DATA_DIR / "bins.jsonl")
isolates     = load_jsonl(DATA_DIR / "isolates.jsonl")
interactions = load_json(DATA_DIR / "interactions.json")
prebiotics   = load_csv(DATA_DIR / "prebiotics.csv")
formulations = load_json(DATA_DIR / "formulations.json")

# ---- Indices ----
PATIENT_INDEX  = {p.get("patient_id"): p for p in patients}
SAMPLE_INDEX   = {s.get("sample_id"): s for s in samples}
BIN_INDEX      = {b.get("bin_id"): b for b in bins}
ISOLATE_INDEX  = {i.get("isolate_id"): i for i in isolates}

# ---- CORS (open for demo; tighten later) ----
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5174",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Health ----
@app.get("/health")
def health():
    return {"status": "ok", "data_dir": str(DATA_DIR)}

# ---- Simple data endpoints needed by the UI ----
@app.get("/patients")
def get_patients():
    return patients

@app.get("/samples")
def get_samples(patient_id: Optional[str] = None):
    if patient_id:
        pid = patient_id
        return [s for s in samples if s.get("patient_id") == pid]
    return samples

@app.get("/bins")
def get_bins(sample_id: Optional[str] = None):
    if sample_id:
        sid = sample_id
        return [b for b in bins if b.get("sample_id") == sid]
    return bins

@app.get("/isolates")
def get_isolates(sample_id: Optional[str] = None, bin_id: Optional[str] = None):
    data = isolates
    if sample_id:
        data = [i for i in data if i.get("source_sample") == sample_id or i.get("sample_id") == sample_id]
    if bin_id:
        data = [i for i in data if i.get("bin_id") == bin_id]
    return data

@app.get("/isolates/{isolate_id}")
def get_isolate(isolate_id: str):
    item = ISOLATE_INDEX.get(isolate_id)
    if not item:
        raise HTTPException(status_code=404, detail="isolate not found")
    return item

# ---- Optional analysis stubs used by UI components ----
@app.get("/samples/{sample_id}/abundance")
def sample_abundance(sample_id: str):
    # Return empty list if not present; UI should handle gracefully.
    return []

@app.get("/bins/{bin_id}/pathways")
def bin_pathways(bin_id: str):
    b = BIN_INDEX.get(bin_id)
    # Pathways may live under b.get("pathways") in some datasets; default to empty.
    return b.get("pathways", []) if b else []

# ---- Search (simple) ----
@app.get("/search")
def search(q: str):
    ql = q.lower().strip()
    found: List[Dict[str, Any]] = []
    for i in isolates:
        if not ql:
            break
        # search in a few common fields
        if any(ql in str(i.get(k, "")).lower() for k in ["isolate_id", "taxonomy", "taxid_genus", "patient_id", "source_sample"]):
            found.append(i)
            if len(found) >= 50:
                break
    return {"isolates": found}

# ---- Prebiotics (for builder dropdown) ----
@app.get("/prebiotics")
def get_prebiotics():
    return prebiotics

# ---- Network ----
@app.get("/network")
def get_network(
    isolate_id: Optional[str] = None,
    type: Optional[str] = Query(None, description="Filter by interaction type"),
    max_neighbors: int = 80,
):
    # Filter edges
    edges = interactions
    if type:
        edges = [e for e in edges if e.get("type") == type]
    if isolate_id:
        edges = [
            e for e in edges
            if e.get("source_isolate") == isolate_id or e.get("target_isolate") == isolate_id
        ]
    # Cap for performance
    edges = edges[:max_neighbors]

    # Build node set
    node_ids = set()
    for e in edges:
        node_ids.add(e.get("source_isolate"))
        node_ids.add(e.get("target_isolate"))

    nodes = [
        {
            "id": nid,
            "label": ISOLATE_INDEX.get(nid, {}).get("taxid_genus", nid),
        }
        for nid in node_ids if nid
    ]
    edgelist = [
        {
            "source": e.get("source_isolate"),
            "target": e.get("target_isolate"),
            "type": e.get("type"),
            "score": e.get("score", 0.0),
        }
        for e in edges
    ]
    return {"nodes": nodes, "edges": edgelist}

# ---- Downloads ----
@app.get("/download/interactions.csv")
def download_interactions_csv():
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["source_isolate","target_isolate","type","score"])
    writer.writeheader()
    for e in interactions:
        writer.writerow({
            "source_isolate": e.get("source_isolate",""),
            "target_isolate": e.get("target_isolate",""),
            "type": e.get("type",""),
            "score": e.get("score",""),
        })
    csv_text = buf.getvalue()
    return Response(content=csv_text, media_type="text/csv")

@app.get("/download/patients.csv")
def download_patients_csv():
    buf = io.StringIO()
    if patients:
        writer = csv.DictWriter(buf, fieldnames=list(patients[0].keys()))
        writer.writeheader()
        writer.writerows(patients)
    return Response(content=buf.getvalue(), media_type="text/csv")

@app.get("/download/samples.csv")
def download_samples_csv():
    buf = io.StringIO()
    if samples:
        writer = csv.DictWriter(buf, fieldnames=list(samples[0].keys()))
        writer.writeheader()
        writer.writerows(samples)
    return Response(content=buf.getvalue(), media_type="text/csv")

@app.get("/download/isolates.csv")
def download_isolates_csv():
    buf = io.StringIO()
    if isolates:
        writer = csv.DictWriter(buf, fieldnames=list(isolates[0].keys()))
        writer.writeheader()
        writer.writerows(isolates)
    return Response(content=buf.getvalue(), media_type="text/csv")

# ---- Formulation preview ----
class FormPreviewIn(BaseModel):
    organisms: List[str]
    prebiotics: Optional[List[str]] = []

@app.post("/formulations/preview")
def preview_formulation(payload: FormPreviewIn):
    chosen = set(payload.organisms or [])
    comp = 0.0
    inh = 0.0

    # Sum up complementarity and inhibition among the chosen isolates
    for e in interactions:
        a = e.get("source_isolate")
        b = e.get("target_isolate")
        if a in chosen and b in chosen:
            t = e.get("type")
            s = float(e.get("score", 0.5))
            if t == "complementarity":
                comp += s
            elif t == "inhibition":
                inh += s

    # Base scoring: reward complementarity, penalize internal inhibition
    score = 0.1 + 0.2 * comp - 0.3 * inh

    # Mild additional penalty for internal inhibitions (average)
    inh_edges = [
        e for e in interactions
        if e.get("type") == "inhibition"
        and e.get("source_isolate") in chosen
        and e.get("target_isolate") in chosen
    ]
    if inh_edges:
        avg_inh = sum(float(e.get("score", 0) or 0) for e in inh_edges) / max(1, len(inh_edges))
        score -= 0.12 * avg_inh

    # Clamp and round
    score = max(0.0, min(1.0, score))
    notes: List[str] = []
    if comp:
        notes.append("Complementarity present")
    if inh:
        notes.append("Internal inhibition detected")
    if payload.prebiotics:
        notes.append(f"Prebiotics: {', '.join(payload.prebiotics)}")

    return {"score_predicted": round(score, 2), "notes": notes or ["No notable interactions"]}
