from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import csv
import json
import os
import io

app = FastAPI(title="ASMA Demo API", version="0.3.2")

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR_ENV = os.getenv("ASMA_DATA_DIR") or os.getenv("DEMO_DATA_DIR")
DATA_DIR: Path = Path(DATA_DIR_ENV or (REPO_ROOT / "demo_data")).resolve()
print(f"[ASMA] REPO_ROOT = {REPO_ROOT}")
print(f"[ASMA] DATA_DIR  = {DATA_DIR}")
if not DATA_DIR.exists():
    raise RuntimeError(f"Demo data folder not found: {DATA_DIR}. Set ASMA_DATA_DIR or DEMO_DATA_DIR.")

def load_csv(path: Path):
  with open(path, newline="", encoding="utf-8") as f:
    return list(csv.DictReader(f))
def load_json(path: Path):
  with open(path, encoding="utf-8") as f:
    return json.load(f)
def load_jsonl(path: Path):
  with open(path, "r", encoding="utf-8") as f:
    text = f.read().strip()
  if not text: return []
  if text.lstrip().startswith("["):
    return json.loads(text)
  items = []
  for line in text.splitlines():
    line = line.strip()
    if not line: continue
    items.append(json.loads(line))
  return items

patients     = load_csv(DATA_DIR / "patients.csv")
samples      = load_csv(DATA_DIR / "samples.csv")
bins         = load_jsonl(DATA_DIR / "bins.jsonl")
isolates     = load_jsonl(DATA_DIR / "isolates.jsonl")
interactions = load_json(DATA_DIR / "interactions.json")
prebiotics   = load_csv(DATA_DIR / "prebiotics.csv")
formulations = load_json(DATA_DIR / "formulations.json")

PATIENT_INDEX  = {p.get("patient_id"): p for p in patients}
SAMPLE_INDEX   = {s.get("sample_id"): s for s in samples}
BIN_INDEX      = {b.get("bin_id"): b for b in bins}
ISOLATE_INDEX  = {i.get("isolate_id"): i for i in isolates}

ALLOWED_ORIGINS = [
  "http://127.0.0.1:5174", "http://localhost:5174",
  "http://127.0.0.1:5173", "http://localhost:5173",
  "http://127.0.0.1:3000", "http://localhost:3000",
]
app.add_middleware(
  CORSMiddleware,
  allow_origins=ALLOWED_ORIGINS,
  allow_credentials=False,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/health")
def health():
  return {"status": "ok", "data_dir": str(DATA_DIR)}

@app.get("/patients")
def get_patients(): return patients

@app.get("/samples")
def get_samples(patient_id: Optional[str] = None):
  if patient_id:
    return [s for s in samples if s.get("patient_id") == patient_id]
  return samples

@app.get("/bins")
def get_bins(sample_id: Optional[str] = None):
  if sample_id:
    return [b for b in bins if b.get("sample_id") == sample_id]
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
  it = ISOLATE_INDEX.get(isolate_id)
  if not it: raise HTTPException(status_code=404, detail="isolate not found")
  return it

@app.get("/prebiotics")
def get_prebiotics(): return prebiotics

@app.get("/network")
def get_network(isolate_id: Optional[str] = None, type: Optional[str] = Query(None), max_neighbors: int = 80):
  edges = interactions
  if type:
    edges = [e for e in edges if e.get("type") == type]
  if isolate_id:
    edges = [e for e in edges if e.get("source_isolate") == isolate_id or e.get("target_isolate") == isolate_id]
  edges = edges[:max_neighbors]
  ids = set()
  for e in edges:
    ids.add(e.get("source_isolate")); ids.add(e.get("target_isolate"))
  nodes = [{"id": nid, "label": ISOLATE_INDEX.get(nid, {}).get("taxid_genus", nid)} for nid in ids if nid]
  edgelist = [{"source": e.get("source_isolate"), "target": e.get("target_isolate"), "type": e.get("type"), "score": e.get("score", 0.0)} for e in edges]
  return {"nodes": nodes, "edges": edgelist}

class FormPreviewIn(BaseModel):
  organisms: List[str]
  prebiotics: Optional[List[str]] = []

def _score_breakdown(organisms: List[str]):
  chosen = set(organisms or [])
  comp_sum = 0.0
  inhib_sum = 0.0
  compo_sum = 0.0
  comp_list = []
  inhib_list = []
  comp_count = inhib_count = compo_count = 0

  for e in interactions:
    a = e.get("source_isolate"); b = e.get("target_isolate")
    if a in chosen and b in chosen:
      t = e.get("type"); s = float(e.get("score", 0.5))
      if t == "complementarity":
        comp_sum += s; comp_count += 1; comp_list.append(e)
      elif t == "inhibition":
        inhib_sum += s; inhib_count += 1; inhib_list.append(e)
      elif t == "competition":
        compo_sum += s; compo_count += 1; inhib_list.append({"type":"competition", **e})

  score = 0.1 + 0.2 * comp_sum - 0.3 * (inhib_sum + 0.5 * compo_sum)
  if inhib_count:
    score -= 0.12 * (inhib_sum / max(1, inhib_count))
  score = max(0.0, min(1.0, score))

  return {
    "organisms": list(chosen),
    "sum_complementarity": round(comp_sum, 3),
    "sum_inhibition": round(inhib_sum, 3),
    "sum_competition": round(compo_sum, 3),
    "avg_inhibition": round(inhib_sum/max(1,inhib_count), 3) if inhib_count else 0.0,
    "counts": {"complementarity": comp_count, "inhibition": inhib_count, "competition": compo_count},
    "edges_included": {"complementarity": comp_list, "inhibition_or_competition": inhib_list},
    "score_predicted": round(score, 2),
  }

@app.post("/formulations/preview")
def preview_formulation(payload: FormPreviewIn, debug: Optional[int] = 0):
  bd = _score_breakdown(payload.organisms)
  notes = []
  if bd["sum_complementarity"]:
    notes.append("Complementarity present")
  if bd["sum_inhibition"] or bd["sum_competition"]:
    notes.append("Internal negative interactions (inhibition/competition)")
  if payload.prebiotics:
    notes.append(f"Prebiotics: {', '.join(payload.prebiotics)}")
  if debug:
    bd["notes"] = notes or ["No notable interactions"]
    return bd
  return {"score_predicted": bd["score_predicted"], "notes": notes or ["No notable interactions"]}
