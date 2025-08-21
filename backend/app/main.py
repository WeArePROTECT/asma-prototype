# backend/app/main.py
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import csv
import json
import os
import io

app = FastAPI(title="ASMA Demo API", version="0.1.0")

# ---- Config ----
DATA_DIR = os.environ.get("ASMA_DATA_DIR", "demo_data")


# ---- Helpers ----
def load_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    # Tolerant loader: supports JSONL or a JSON array
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


def find_one(
    items: List[Dict[str, Any]], key: str, val: str
) -> Optional[Dict[str, Any]]:
    for x in items:
        if x.get(key) == val:
            return x
    return None


def paginate(items: List[Dict[str, Any]], limit: int, offset: int) -> Dict[str, Any]:
    total = len(items)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items[offset : offset + limit],
    }


def sort_items(
    items: List[Dict[str, Any]], sort: Optional[str]
) -> List[Dict[str, Any]]:
    if not sort:
        return items
    key = sort.lstrip("-")
    reverse = sort.startswith("-")
    return sorted(items, key=lambda x: x.get(key), reverse=reverse)


# ---- Load demo data ----
patients: List[Dict[str, Any]] = load_csv(os.path.join(DATA_DIR, "patients.csv"))
samples: List[Dict[str, Any]] = load_csv(os.path.join(DATA_DIR, "samples.csv"))
bins: List[Dict[str, Any]] = load_jsonl(os.path.join(DATA_DIR, "bins.jsonl"))
isolates: List[Dict[str, Any]] = load_jsonl(os.path.join(DATA_DIR, "isolates.jsonl"))
interactions: List[Dict[str, Any]] = load_json(
    os.path.join(DATA_DIR, "interactions.json")
)
prebiotics: List[Dict[str, Any]] = load_csv(os.path.join(DATA_DIR, "prebiotics.csv"))
formulations: List[Dict[str, Any]] = load_json(
    os.path.join(DATA_DIR, "formulations.json")
)

# ---- Indices ----
PATIENT_INDEX = {p["patient_id"]: p for p in patients}
SAMPLE_INDEX = {s["sample_id"]: s for s in samples}
BIN_INDEX = {b["bin_id"]: b for b in bins}
ISOLATE_INDEX = {i["isolate_id"]: i for i in isolates}

# ---- CORS (open for demo; tighten later) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Health ----
@app.get("/health")
def health():
    return {"status": "ok", "data_dir": DATA_DIR}


# =========================
# Collections
# =========================
@app.get("/patients")
def get_patients():
    return patients


@app.get("/samples")
def get_samples(patient_id: Optional[str] = Query(None)):
    if patient_id:
        return [s for s in samples if s["patient_id"] == patient_id]
    return samples


@app.get("/bins")
def get_bins(sample_id: Optional[str] = Query(None)):
    if sample_id:
        return [b for b in bins if b["sample_id"] == sample_id]
    return bins


@app.get("/isolates")
def get_isolates(bin_id: Optional[str] = Query(None)):
    if bin_id:
        return [i for i in isolates if bin_id in i.get("linked_bins", [])]
    return isolates


@app.get("/interactions")
def get_interactions(
    isolate_id: Optional[str] = Query(None), type: Optional[str] = Query(None)
):
    data = interactions
    if isolate_id:
        data = [
            e
            for e in data
            if e["source_isolate"] == isolate_id or e["target_isolate"] == isolate_id
        ]
    if type:
        data = [e for e in data if e["type"] == type]
    return data


@app.get("/prebiotics")
def get_prebiotics():
    return prebiotics


@app.get("/formulations")
def get_formulations(
    isolate_id: Optional[str] = Query(None), prebiotic_id: Optional[str] = Query(None)
):
    data = formulations
    if isolate_id:
        data = [f for f in data if isolate_id in f.get("organisms", [])]
    if prebiotic_id:
        data = [f for f in data if prebiotic_id in f.get("prebiotics", [])]
    return data


# =========================
# ID lookups
# =========================
@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    p = PATIENT_INDEX.get(patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    return p


@app.get("/samples/{sample_id}")
def get_sample(sample_id: str):
    s = SAMPLE_INDEX.get(sample_id)
    if not s:
        raise HTTPException(404, "Sample not found")
    return s


@app.get("/bins/{bin_id}")
def get_bin(bin_id: str):
    b = BIN_INDEX.get(bin_id)
    if not b:
        raise HTTPException(404, "Bin not found")
    return b


@app.get("/isolates/{isolate_id}")
def get_isolate(isolate_id: str):
    i = ISOLATE_INDEX.get(isolate_id)
    if not i:
        raise HTTPException(404, "Isolate not found")
    return i


# =========================
# Lineage
# =========================
@app.get("/lineage/patient/{patient_id}")
def lineage_patient(patient_id: str):
    if patient_id not in PATIENT_INDEX:
        raise HTTPException(404, "Patient not found")
    samps = [s for s in samples if s["patient_id"] == patient_id]
    samp_ids = {s["sample_id"] for s in samps}
    bs = [b for b in bins if b["sample_id"] in samp_ids]
    bin_ids = {b["bin_id"] for b in bs}
    isos = [
        i for i in isolates if any(bid in bin_ids for bid in i.get("linked_bins", []))
    ]
    return {
        "patient": PATIENT_INDEX[patient_id],
        "samples": samps,
        "bins": bs,
        "isolates": isos,
    }


@app.get("/lineage/sample/{sample_id}")
def lineage_sample(sample_id: str):
    if sample_id not in SAMPLE_INDEX:
        raise HTTPException(404, "Sample not found")
    bs = [b for b in bins if b["sample_id"] == sample_id]
    bin_ids = {b["bin_id"] for b in bs}
    isos = [
        i for i in isolates if any(bid in bin_ids for bid in i.get("linked_bins", []))
    ]
    return {"sample": SAMPLE_INDEX[sample_id], "bins": bs, "isolates": isos}


# =========================
# Search & Download
# =========================
@app.get("/search")
def search(q: str = Query(..., min_length=1)):
    ql = q.lower()
    return {
        "patients": [
            p
            for p in patients
            if ql in p["patient_id"].lower() or ql in (p.get("condition", "").lower())
        ],
        "samples": [
            s
            for s in samples
            if ql in s["sample_id"].lower() or ql in (s.get("sample_type", "").lower())
        ],
        "bins": [
            b
            for b in bins
            if ql in b["bin_id"].lower()
            or ql in (b.get("taxonomy", "").lower())
            or ql in (b.get("taxon", "").lower())
        ],
        "isolates": [
            i
            for i in isolates
            if ql in i["isolate_id"].lower()
            or ql in (i.get("taxonomy", "").lower())
            or ql in (i.get("taxid_genus", "").lower())
        ],
    }


@app.get("/download/{entity}.csv")
def download_csv(entity: str):
    entity = entity.lower()
    mapping: Dict[str, List[Dict[str, Any]]] = {
        "patients": patients,
        "samples": samples,
        "bins": bins,
        "isolates": isolates,
        "interactions": interactions,
        "prebiotics": prebiotics,
        "formulations": formulations,
    }
    if entity not in mapping:
        raise HTTPException(404, f"Unknown entity {entity}")

    rows = mapping[entity]
    if not rows:
        return Response(content="", media_type="text/csv")

    # Determine columns from union of keys
    cols: List[str] = []
    for r in rows:
        for k in r.keys() if isinstance(r, dict) else []:
            if k not in cols:
                cols.append(k)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols)
    writer.writeheader()
    for r in rows:
        out: Dict[str, Any] = {}
        for c in cols:
            val = r.get(c)
            if isinstance(val, (list, dict)):
                out[c] = json.dumps(val)
            else:
                out[c] = val
        writer.writerow(out)

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{entity}.csv"'},
    )


# =========================
# Focused endpoints
# =========================
@app.get("/bins/{bin_id}/pathways")
def bin_pathways(bin_id: str):
    b = BIN_INDEX.get(bin_id)
    if not b:
        raise HTTPException(404, "Bin not found")
    scored = b.get("pathways_scored")
    if scored:
        return {"bin_id": bin_id, "pathways": scored}
    return {
        "bin_id": bin_id,
        "pathways": [
            {"pathway": p, "score": None, "evidence": None}
            for p in b.get("pathways", [])
        ],
    }


@app.get("/samples/{sample_id}/abundance")
def sample_abundance(sample_id: str):
    if sample_id not in SAMPLE_INDEX:
        raise HTTPException(404, "Sample not found")
    bs = [x for x in bins if x["sample_id"] == sample_id]
    resp = [
        {
            "bin_id": x["bin_id"],
            "taxonomy": x.get("taxonomy") or x.get("taxon"),
            "abundance": x.get("abundance", 0),
        }
        for x in bs
    ]
    total = sum(x.get("abundance", 0) for x in bs)
    return {"sample_id": sample_id, "bins": resp, "total_abundance": round(total, 6)}


@app.get("/isolates/{isolate_id}/omics")
def isolate_omics(isolate_id: str):
    i = ISOLATE_INDEX.get(isolate_id)
    if not i:
        raise HTTPException(404, "Isolate not found")
    return {
        "isolate_id": isolate_id,
        "growth_media": i.get("growth_media"),
        "metabolite_markers": i.get("metabolite_markers", []),
        "genome_depot_id": i.get("genome_depot_id"),
    }


@app.get("/network")
def network(isolate_id: Optional[str] = None, type: Optional[str] = None):
    edges = interactions
    if isolate_id:
        edges = [
            e
            for e in edges
            if e["source_isolate"] == isolate_id or e["target_isolate"] == isolate_id
        ]
    if type:
        edges = [e for e in edges if e["type"] == type]
    node_ids: set[str] = set()
    for e in edges:
        node_ids.add(e["source_isolate"])
        node_ids.add(e["target_isolate"])
    id_to_label = {
        i["isolate_id"]: i.get("taxonomy") or i["isolate_id"] for i in isolates
    }
    nodes = [{"id": n, "label": id_to_label.get(n, n)} for n in sorted(node_ids)]
    edges_out = [
        {
            "source": e["source_isolate"],
            "target": e["target_isolate"],
            "type": e["type"],
            "score": e["score"],
        }
        for e in edges
    ]
    return {"nodes": nodes, "edges": edges_out}
