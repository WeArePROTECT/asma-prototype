# ASMA Prototype — System Overview

> **Goal:** Deliver a clean, demo‑ready system that proves end‑to‑end lineage navigation (Patient → Sample → Bin → Isolate), functional‑omics summaries, interaction network, and a formulation builder — with mock data that can be seamlessly swapped for real lab data later.

---

## 1) Scope & Personas

- **PI / Program reviewer (ARPA‑H):** Click through “happy path” flows, see data lineage, basic charts, and a simple network/formulation demo.
- **Developer (you + collaborators):** Local FastAPI + React for rapid iteration; later, containerize and plug in real pipelines.

**Sprint focus**
- **A:** Universal browser + search + downloads ✅
- **B:** Functional‑omics widgets (bin pathways endpoint + sample abundance) ✅ endpoints ready
- **C:** Interaction network (UI‑ready `/network` payload) ☐
- **D:** Formulation builder (`/formulations/preview` stub scorer) ☐
- **E:** Polish (landing page, export buttons, docs) ☐
- **F:** Packaging (configurable data dir, container) ☐

---

## 2) Architecture (MVP)

```
React (Vite) SPA
  └── axios → FastAPI
        ├── /patients, /samples, /bins, /isolates, /interactions, /prebiotics, /formulations
        ├── /lineage/patient/{id}, /lineage/sample/{id}
        ├── /search, /download/{entity}.csv
        ├── /bins/{id}/pathways, /samples/{id}/abundance
        ├── /isolates/{id}/omics
        └── /network (UI‑ready nodes/edges)
Data: demo_data/*  (swap‑ready via ASMA_DATA_DIR)
```

- **Data hot‑swap:** Set `ASMA_DATA_DIR=/path/to/real_data` and restart. Contracts stay the same.
- **CORS:** Permissive in dev; lock down domains when deploying.

---

## 3) Data Contracts (selected)

### 3.1 Lineage (patient‑centric)
`GET /lineage/patient/{patient_id}` →
```json
{
  "patient": {...},
  "samples": [{...}],
  "bins": [{"bin_id":"B001","sample_id":"S001","taxonomy":"...","abundance":0.32,"pathways":[...],"pathways_scored":[...]}],
  "isolates": [{"isolate_id":"I001","taxonomy":"...","amr_flags":[...],"linked_bins":["B001"], "...": "..."}]
}
```

### 3.2 Bin pathways
`GET /bins/{bin_id}/pathways` →
```json
{"bin_id":"B001","pathways":[{"pathway":"carbohydrate_metabolism","score":0.9,"evidence":"metaG_presence"}]}
```

### 3.3 Sample abundance
`GET /samples/{sample_id}/abundance` →
```json
{"sample_id":"S001","bins":[{"bin_id":"B001","taxonomy":"Streptococcus","abundance":0.32}],"total_abundance":0.32}
```

### 3.4 Isolate omics
`GET /isolates/{isolate_id}/omics` →
```json
{"isolate_id":"I003","growth_media":"LB broth (mock)","metabolite_markers":["pyocyanin","rhamnolipids"],"genome_depot_id":"GD-I003"}
```

### 3.5 Network (UI‑ready)
`GET /network?type=competition` →
```json
{"nodes":[{"id":"I001","label":"Streptococcus mitis group"}],
 "edges":[{"source":"I003","target":"I001","type":"competition","score":0.70}]}
```

### 3.6 Formulation preview (stub)
`POST /formulations/preview`
```json
{"organisms":["I001","I004"],"prebiotics":["PB001"]}
```
→
```json
{"score_predicted":0.68,"notes":"Stubbed score based on 2 organism(s) and 1 prebiotic(s)."}
```

Full endpoint list is discoverable via `/docs`. Data file schemas documented in **demo_data/README.md**.

---

## 4) Repository Layout (recommended)

```
asma-proto/
├─ backend/
│  └─ app/main.py
├─ frontend/
│  └─ src/...
├─ demo_data/               # default mock data (swap with ASMA_DATA_DIR)
│  ├─ patients.csv
│  ├─ samples.csv
│  ├─ bins.jsonl
│  ├─ isolates.jsonl
│  ├─ interactions.json
│  ├─ prebiotics.csv
│  └─ formulations.json
├─ docs/
│  └─ overview.md           # (this file)
└─ requirements.txt
```

---

## 5) Local Development

**Backend**
```bash
pip install -r requirements.txt   # fastapi, uvicorn
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
open http://127.0.0.1:8000/docs
```

**Frontend (Vite)**
```bash
cd frontend
npm i
npm run dev
# Ensure API baseURL = http://127.0.0.1:8000
```

**Swap data**
```bash
# Use real or alternative dataset directory
$env:ASMA_DATA_DIR="H:\path\to\real_data"   # PowerShell example
# or
export ASMA_DATA_DIR=/path/to/real_data
```

---

## 6) Coding Standards & Quality

- **Type safety:** Prefer Pydantic models for request/response shapes on public endpoints.
- **Lint & format:** `ruff` + `black` for Python; `eslint` + `prettier` for React.
- **Testing:** `pytest` for backend (add sample fixtures under demo_data/).
- **Error handling:** Use 404/422 for not‑found/validation; return consistent JSON shape.
- **Perf:** UI endpoints return only what the component needs (e.g., `/bins/{id}/pathways`).

**Suggested dev tools (optional)**
```toml
# pyproject.toml (excerpt)
[tool.black]
line-length = 100
[tool.ruff]
select = ["E","F","I"]
```
```json
// frontend/.eslintrc.json (excerpt)
{ "extends": ["react-app"], "rules": { "no-console": "warn" } }
```

---

## 7) CI/CD (optional but professional)

**GitHub Actions – Python + Node (smoke tests)**
```yaml
name: ci
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt pytest
      - run: pytest -q || true   # keep demo-friendly; tighten later
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci && npm run build
```

---

## 8) Demo Script (3–4 minutes)

1. **Landing:** Open browser app → pick **P001**.
2. **Lineage:** Click sample **S001** → bin **B001** → isolate **I001**.
3. **Functional‑omics:** Hit **/bins/B001/pathways** (chips) + **/samples/S001/abundance** (bar chart).
4. **Network:** Filter `type = competition` → click **I003** and show edge to **I001**.
5. **Formulation:** Add **I001 + I004**, choose **PB001**, **Preview score** via `/formulations/preview`.
6. **Download:** Use **/download/bins.csv** — show export readiness.
7. **Swap story:** Show `ASMA_DATA_DIR` env var to prove easy data replacement.

---

## 9) Security & Privacy (proto level)

- No PHI/PII in mock data; real data ingestion will require IRB‑compliant handling.
- Disable `allow_origins=["*"]` before any non‑local deployment.
- Log minimal request info in prod; scrub IDs if needed.

---

## 10) Roadmap Notes

- Replace mock **pathways_scored** with real DRAM/HUMAnN outputs.
- Integrate isolate AMR annotations from AMRFinder/CARD RGI.
- Add server‑side pagination on large tables.
- Optional: add auth (FastAPI middleware) when multi‑user demos start.

---

**Related document:** `demo_data/README.md` (mock → real mapping and file schemas).
