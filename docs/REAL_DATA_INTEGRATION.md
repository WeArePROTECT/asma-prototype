# ASMA Prototype — Real Data Integration

**Date:** April 12, 2026  
**Author:** Spencer Long + Claude (Anthropic)  
**Branch:** `feat/pydantic-validation-real-data`  
**Commit:** `675ff94`  
**Repo:** [github.com/WeArePROTECT/asma-prototype](https://github.com/WeArePROTECT/asma-prototype)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Background & Motivation](#2-background--motivation)
3. [Architecture Decision: Flat Files Over Live Database](#3-architecture-decision-flat-files-over-live-database)
4. [Data Sources](#4-data-sources)
5. [Data Model](#5-data-model)
6. [ETL Pipeline (`prepare_real_data.py`)](#6-etl-pipeline-prepare_real_datapy)
7. [Pydantic Validation Layer (`schemas.py`)](#7-pydantic-validation-layer-schemaspy)
8. [FastAPI Backend Changes (`main.py`)](#8-fastapi-backend-changes-mainpy)
9. [Deployment Procedure](#9-deployment-procedure)
10. [Validation Results & Data Quality Notes](#10-validation-results--data-quality-notes)
11. [Git & Branch Strategy](#11-git--branch-strategy)
12. [Known Gaps & Deferred Work](#12-known-gaps--deferred-work)
13. [Next Steps: UI Improvements](#13-next-steps-ui-improvements)
14. [Runbook: Re-running the ETL When New Data Arrives](#14-runbook-re-running-the-etl-when-new-data-arrives)
- [Appendix A: Schema Field Reference](#appendix-a-schema-field-reference)
- [Appendix B: ETL Validation Report Structure](#appendix-b-etl-validation-report-structure)

---

## 1. Overview

In a single session on April 12, 2026, the ASMA prototype was transitioned from serving synthetic demo data to serving real, validated PROTECT multi-omics study data. The pipeline ingests data from five live sources on the THAR server, validates every row against production-grade Pydantic v2 schemas, and produces clean flat files that the existing FastAPI backend reads unchanged. Final output: **35 patients, 241 samples, and 4,259 isolates** — zero validation failures, zero NaN/None string leakage in any output file. Pydantic validation operates at both the ETL layer (data cleaning at write time) and the FastAPI layer (response model enforcement at serve time), giving two independent correctness checkpoints without introducing any new infrastructure.

---

## 2. Background & Motivation

### What the ASMA Prototype Is

The ASMA (Arkin–Styer Microbiome Architect) prototype is a FastAPI + React web application for exploring PROTECT study microbial isolate data. The backend is a single-file FastAPI app (`backend/app/main.py`) that reads flat CSV and JSONL files from a data directory at startup and serves them through a REST API. The frontend is a Vite/React SPA built into the container's `/app/static/` directory. There is intentionally no live database connection — the app is stateless and the data files are the source of truth.

### Why It Previously Used Fake Data

The prototype was built at R&D/demo pace. The `demo_data/` directory contains six synthetic files (`patients.csv`, `samples.csv`, `bins.jsonl`, `isolates.jsonl`, `interactions.json`, `formulations.json`) with 5–10 hand-authored records each, sufficient for frontend development and UI iteration but not representative of real PROTECT data. Real data integration was deferred until the prototype had a stable enough architecture to support it without breakage.

### Goal of This Session

Integrate real PROTECT multi-omics data into the prototype without:
- Modifying or deleting `demo_data/` (preserved as safe fallback)
- Changing the backend's data loading architecture
- Adding infrastructure (no new database, no new service)
- Breaking existing API contracts consumed by the frontend

---

## 3. Architecture Decision: Flat Files Over Live Database

### Why Not Connect Directly to GenomeDepot or REDCap?

During exploration, the GenomeDepot MySQL database was identified at `gd-db:3306`, database `genomedepot`, containing Django ORM models including `Strain`, `Genome`, `Taxon`, `Annotation`, and `Gene`. The schema is fully mapped and the connection credentials exist in `/usr2/people/spencerlong/GenomeDepot/.env`. However, a live database connection was deferred for several reasons:

1. **Stateless container design** — the existing architecture reads files at startup. Adding a live DB connection would require connection pooling, retry logic, and credential management inside the container.
2. **No new infrastructure needed** — the flat-file ETL approach produces the same data without adding a MySQL dependency to the container image.
3. **The pipeline already integrates the data** — the PROTECT data integration pipeline produces a single pre-joined bridge CSV that is more useful than raw DB tables for this use case.
4. **Targeted future sprint** — AMR resistance gene data (the one field that requires GenomeDepot) is a well-scoped addition: query `Annotation`/`Gene` tables `WHERE annotation_type = 'AMR' AND strain_id = ASMA_id`.

### The Volume Mount Strategy

Rather than adding a new environment variable or code path, `real_data/` is mounted to `/app/demo_data` inside the container. The backend's existing `ASMA_DATA_DIR=/app/demo_data` environment variable, which previously pointed at the demo data, now points at real data with no code changes to path resolution logic.

```
Host:                                     Container:
real_data/                →  mount  →     /app/demo_data/
├── patients.csv                          ├── patients.csv      ← backend reads this
├── samples.csv                           ├── samples.csv
├── isolates.jsonl                        ├── isolates.jsonl
└── ...                                   └── ...

demo_data/                (untouched, available as fallback by setting ASMA_DATA_DIR)
```

---

## 4. Data Sources

All paths are on the THAR server (`protect.qb3.berkeley.edu`).

### 4.1 PROTECT Data Integration Pipeline — Bridge Datasets

**Base directory (auto-detected by ETL):**
```
/usr2/people/protect/Arkin_Lab/protect_data/protect_data_integration_pipeline/pipeline_outputs/runs/
```

The ETL auto-detects the most recent dated subfolder by parsing folder names in both `M_D_YY` and `YYYY-MM-DD` formats, converting to a sortable integer, and taking the highest. On April 12, 2026, the most recent run was `4_12_26`.

**Platinum layer (sample-level bridge):**
```
.../runs/4_12_26/protect_multiomics_isolate_sample_patient_integration_4_12_26.csv
```
- **Grain:** one row per enrolled sample
- **Dimensions:** 241 rows × 55 columns
- **Unique patients:** 35 (after deduplication)
- **Key fields:** `sample_id` (PRO1–PRO241), `patient_id` (integer), `asma_id_list` (pipe-delimited ASMA IDs), `has_metag`, `has_metars`, `has_isolates`, `diagnosis`, `collection_date`, `assessment_of_pex`, lung function metrics (`fev1_pp`, `fev1_l`, `fvc_pp`, `fvc_l`), metagenomic diversity metrics (`metag_shannon`, `metag_richness`, `metag_chao1`, `metag_simpson`)

**Gold layer (isolate-level):**
```
.../runs/4_12_26/protect_clinical_isolate_sample_patient_merged_4_12_26.csv
```
- **Grain:** one row per ASMA isolate ID
- **Dimensions:** 4,405 rows × 78 columns (includes 146 rows with `has_isolates=False`)
- **Unique ASMA IDs:** 4,259 after filtering `has_isolates=True` and dropping 22 rows with empty `ASMA_id`
- **Key fields:** `ASMA_id` (e.g. `ASMA-1`), `pro_sample_id` (e.g. `PRO1`), `patient_id`, `isolation_media`, `apl_metag_same_sample` (comma-separated metaG sample IDs linked to this isolation sample), 25 individual antibiotic treatment columns

### 4.2 Patient Metadata (Supplemental Reference)

```
/usr2/people/protect/Conrad_Lab/metadata/protect_metadata_12_29_2025.csv
```
- **Dimensions:** 7 columns
- **Status:** Supplemental reference; clinical data used in this sprint was sourced from the bridge CSV. This file is available for future enrichment (e.g., additional demographic fields).

### 4.3 Isolate Taxonomy — Alex Styer's TSV

```
/usr2/people/alex.styer/public_html/taxonomy.tsv
```
- **Auto-detected** by the ETL (scans for `taxonomy*.tsv` then `*.tsv` in the directory)
- **Dimensions:** 4,949 rows × 21 columns
- **Join key:** `ASMA_id` (e.g. `ASMA-1`)
- **Taxonomy columns:** Domain, Phylum, Class, Order, Family, Genus, Species
- **Genome quality columns:** `Completeness (checkM2)`, `Contamination (checkM2)`, `Genome Size (Mb)`, `Total Contigs`, `Contig N50 (Kb)`, `GC Content`, `Total Coding Sequences`
- **Reference columns:** `Closest Genome Reference` (RefSeq accession), `Closest Genome ANI`
- **Clustering:** `Strain Group`, `Representative`
- **Match rate against gold layer:** 4,196 / 4,259 = **98.5%** — 63 ASMA IDs in gold layer not in taxonomy.tsv

### 4.4 GenomeDepot MySQL (Explored, Deferred)

- **Host:** `gd-db:3306`
- **Database:** `genomedepot`
- **User:** `genomedepot`
- **Config:** `/usr2/people/spencerlong/GenomeDepot/.env`
- **Relevant tables for future AMR integration:** `Annotation`, `Gene`, `Strain`, `Genome`, `Taxon`
- **Status:** Read-only exploration completed; no data extracted this sprint. AMR resistance gene data for each ASMA_id lives in the `Annotation` and `Gene` tables.

### 4.5 WoL2 Metagenomic Abundance Data

**CPM abundance table:**
```
/usr2/people/protect/Zengler_Lab/Emma/WoL_Subset50_analysis/data/WoL2_Subset50_multiomics_clean_filtered_cpm_metaG.tsv
```
- **Dimensions:** 134 species × 74 metaG samples
- **Sample IDs:** `PRO97_metaG` through `PRO141_metaG` (approximate range)
- **Used to generate:** `bins.jsonl` — 1,225 bins, top 30 species per sample with relative abundance ≥ 0.5%

**metaG sample metadata:**
```
/usr2/people/protect/Zengler_Lab/Emma/WoL_Subset50_analysis/data/WoL2_Subset50_metaG_metadata.tsv
```
- **Dimensions:** 74 rows
- **Key fields:** `SampleID`, `subjectID`, `Richness`, `Shannon`, alignment metrics

---

## 5. Data Model

### Hierarchy

```
Patient (35)
  └── Sample (241)  —  one or more samples per patient
        └── Isolate (4,259)  —  one or more isolates per sample (cultured bacteria)
              └── linked_bin (Optional[str])  —  first metaG bin by genus match
```

Bins (1,225) are a parallel structure derived from metagenomics, keyed by `sample_id`. They are not strictly subordinate to isolates — they represent metagenomic species relative abundances from the WoL2 pipeline, which operates on separate physical samples (metaG samples `PRO97+`) from the isolation samples (`PRO1–PRO49` range). The overlap between the two sample pools is intentionally limited to avoid contaminating culture-based data with metagenomics assumptions.

### Key Linkage

The bridge between isolation and metagenomics is carried in the gold layer column `apl_metag_same_sample` (e.g., `PRO8_metaG, PRO14_metaG, PRO49_metaG`), which lists the metaG sample IDs from the same physical patient visit as a given isolation sample. The ETL strips the `_metaG` suffix and looks up bins from the WoL2 CPM table for those sample IDs.

**Why only 5% of isolates have a linked bin:** The WoL2 Subset50 CPM table covers samples `PRO97+`, while many isolation samples are `PRO1–PRO49`. These two sample ID ranges have minimal overlap, reflecting different collection timepoints or cohorts.

### Interactions and Formulations

`interactions.json` is an empty array `[]`. Co-occurrence scores are computable via Spearman correlation across species-pair abundances in the WoL2 CPM table — this is a well-defined future sprint. `formulations.json` is an empty array `[]` — formulation records are outputs of the ASMA tool, not inputs.

---

## 6. ETL Pipeline (`prepare_real_data.py`)

**Location:** `/usr2/people/spencerlong/asma-prototype/real_data/prepare_real_data.py`  
**Run from:** any directory (uses absolute paths; imports `backend.app.schemas` via `sys.path` manipulation)

### Auto-Detection Logic

**Latest run folder** (function `find_latest_run`):
```python
# Converts M_D_YY → (2000+YY)*10000 + M*100 + D
# Converts YYYY_MM_DD → YYYY*10000 + MM*100 + DD
# Sorts descending, returns first result
```

**Taxonomy TSV** (function `find_taxonomy_tsv`):
```python
# Tries: taxonomy.tsv → taxonomy*.tsv → *.tsv
# Returns first hit in /usr2/people/alex.styer/public_html/
```

### Processing Stages

**1. Patients** (`patients.csv`)
- Source: platinum CSV rows where `has_redcap_metadata = True`
- Deduplicated by `patient_id`, taking the earliest `visit_number`
- Key mappings: `lung_function_age_years → age`, `sex_at_birth → sex`, `diagnosis → condition`, `patient_population → cohort`
- New fields vs. old demo schema: `fev1_pp`, `fev1_l`, `fvc_pp`, `fvc_l`, `fev1_fvc_ratio`, `bmi`, `weight_kg`, `ht_cm`, `race`, `ethnicity`, `cftr_modulator_status`, `patient_population`

**2. Samples** (`samples.csv`)
- Source: all 241 rows of the platinum CSV (one row per enrolled sample)
- Key mappings: `sample_id → sample_id`, `sample_material.lower() → sample_type`, `collection_date → YYYY-MM-DD`
- New fields vs. old demo schema: `visit_number`, `days_since_first_collection`, `patient_status_collection`, `assessment_of_pex`, `antibiotic_status`, `any_iv_antibiotics`, `n_active_antibiotics`, `pa_positive`, `has_isolates`, `has_metag`, `has_metars`, `data_streams_count`, all `metag_*` and `metars_*` diversity metrics, `pa_alignment_pct`, `sampling_site`, `sample_material`, `isolation_source_type`, `asma_id_count`

**3. Isolates** (`isolates.jsonl`)
- Source: gold layer CSV filtered to `has_isolates = True`, 22 rows with empty `ASMA_id` excluded via `dropna`
- Deduplicated on `ASMA_id` (one row per isolate)
- Taxonomy joined: left join on `ASMA_id` → Species, Genus, Family, Order, Class, Phylum
- `linked_bin`: first bin from `bin_by_sample[pro_sample_id]` or from metaG-linked samples via `apl_metag_same_sample`; `None` if no CPM bins available
- `amr_flags`: 25 antibiotic treatment columns from gold layer (see gap note in §12)

**4. Bins** (`bins.jsonl`)
- Source: WoL2 CPM TSV, normalized to relative abundance per sample column
- Filter: top 30 species per sample with relative abundance ≥ 0.5%
- `bin_id` format: `BIN_{pro_id}_{rank:03d}` (e.g. `BIN_PRO101_001`)
- `sample_id`: CPM column name with `_metaG` / `_metaRS` suffix stripped
- Result: 1,225 bins across 74 metaG samples

**5. Per-row Validation**
```python
for _, row in source_df.iterrows():
    try:
        obj = Patient(**row_dict)   # or Sample, Isolate
        valid_rows.append(obj.model_dump())
        _COUNTERS[entity]["valid"] += 1
    except ValidationError as exc:
        _capture(entity, row_id, exc, raw_row)
        # _capture appends {entity, id, field, raw_value, error} to _failures
```

### Output Files

| File | Size | Records | Notes |
|------|------|---------|-------|
| `patients.csv` | 4.6 KB | 35 | 17 fields per row |
| `samples.csv` | 37 KB | 241 | 28 fields per row |
| `isolates.jsonl` | 1.5 MB | 4,259 | 13 fields per object |
| `bins.jsonl` | 280 KB | 1,225 | 7 fields per object |
| `etl_validation_report.json` | 1.3 KB | — | see Appendix B |
| `interactions.json` | 2 B | 0 | `[]` |
| `formulations.json` | 2 B | 0 | `[]` |
| `prebiotics.csv` | 195 B | 2 | copied from `demo_data/` |

---

## 7. Pydantic Validation Layer (`schemas.py`)

**Location:** `/usr2/people/spencerlong/asma-prototype/backend/app/schemas.py`  
**~230 lines, Pydantic v2.12.5 (container), v2.8.2 (host system)**  
**Imported by:** `backend/app/main.py` (FastAPI response models) and `real_data/prepare_real_data.py` (ETL validation)

### Global Pre-pass: `model_validator(mode="before")`

Runs before any field-level validator on every model. Iterates over all fields in the input dict and calls `_nil()`:

```python
_BLANK = {"nan", "none", "null", "na", "n/a", ""}

def _nil(v):
    if v is None: return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)): return None
    if isinstance(v, str) and v.strip().lower() in _BLANK: return None
    # pandas NA
    try:
        import pandas as _pd
        if v is _pd.NA: return None
    except ImportError: pass
    return v
```

This ensures that `"NaN"`, `"nan"`, `"None"`, `""`, `float('nan')`, `float('inf')`, and `pd.NA` are all coerced to `None` before field validators run, eliminating the most common sources of dirty output.

### Field-level Validators

| Schema | Field(s) | Validator | Behavior |
|--------|----------|-----------|----------|
| Patient | `patient_id` | `_pid` | `str(v).strip()`; raises if None |
| Patient | `sex` | `_sex` | `"Male"/"m"→"M"`, `"Female"/"f"→"F"`, else `"Unknown"` |
| Patient | `condition` | `_condition` | passes CF/NCFB/etc through; null→`"Unknown"` |
| Patient | `cohort` | `_cohort` | `"adult"→"Adult"`, `"pediatric"→"Pediatric"`, null→`"Unknown"` |
| Patient | `age`, `fev1_pp`, `fev1_l`, `fvc_pp`, `fvc_l`, `fev1_fvc_ratio`, `bmi`, `weight_kg`, `ht_cm` | `_float` | `float(v)`; inf/NaN→`None`; parse error→`None` |
| Patient | `race`, `ethnicity`, `cftr_modulator_status`, `patient_population` | `_ostr` | strip; empty→`None` |
| Sample | `sample_id`, `patient_id` | `_ids` | `str(v).strip()`; raises if None |
| Sample | `collection_date` | `_date` | tries `%m/%d/%Y`, `%Y-%m-%d`, `%m/%d/%y`, `%Y/%m/%d`, `%d-%m-%Y` → `"YYYY-MM-DD"`; null/unparseable→`None` |
| Sample | `visit_number`, `days_since_first_collection`, `data_streams_count`, `asma_id_count` | `_int` | `int(float(v))`; NaN/inf→`None` |
| Sample | `n_active_antibiotics`, `metag_*`, `pa_alignment_pct` | `_float` | same as Patient float validator |
| Sample | `any_iv_antibiotics`, `pa_positive`, `has_isolates`, `has_metag`, `has_metars` | `_bool` | `"true"/"1"/"yes"→True`; `"false"/"0"/"no"→False`; else→`None` |
| Sample | `sample_type`, `patient_status_collection`, `assessment_of_pex`, `antibiotic_status`, `sampling_site`, `sample_material`, `isolation_source_type` | `_ostr` | strip; empty→`None` |
| Isolate | `isolate_id` | `_iid` | raises `ValueError` if not prefixed `"ASMA-"` |
| Isolate | `sample_id`, `patient_id` | `_ids` | raises if None or empty |
| Isolate | `taxonomy` | `_tax` | null/blank→`"Unknown"` |
| Isolate | `genus` | `_genus` | null/blank→`"Unknown"` |
| Isolate | `family`, `order`, `class_`, `phylum`, `growth_media`, `genome_depot_id`, `linked_bin` | `_ostr` | strip; empty→`None` |
| Isolate | `amr_flags` | `_amr` | list passthrough; JSON string parsed; comma-separated string split; null→`[]` |

### Back-Compatibility Aliases (Isolate `model_validator(mode="before")`)

The demo data uses different field names than the new schema. The model validator maps legacy fields before Pydantic validation runs:

```
source_sample_id  →  sample_id        (demo data used source_sample_id)
taxid_genus       →  genus            (demo data used taxid_genus)
linked_bins[0]    →  linked_bin       (demo data used a list; new schema takes first element)
```

This ensures the API works identically whether `ASMA_DATA_DIR` points at `demo_data/` (legacy schema) or `real_data/` (new schema).

---

## 8. FastAPI Backend Changes (`main.py`)

**Location:** `/usr2/people/spencerlong/asma-prototype/backend/app/main.py`

### Response Models Added

```python
from .schemas import Patient, Sample, Isolate

@app.get("/patients",        response_model=List[Patient])
@app.get("/samples",         response_model=List[Sample])
@app.get("/isolates",        response_model=List[Isolate])
@app.get("/isolates/{id}",   response_model=Isolate)
```

FastAPI serializes each row through the Pydantic model before returning, applying all field validators to data already on disk. This is the second validation checkpoint (after ETL).

### Safe Data Loading (`_safe_load`)

Replaced bare file loads with a wrapper that never crashes the server:

```python
def _safe_load(name, loader, path, default):
    try:
        return loader(path)
    except FileNotFoundError:
        _load_errors[name] = f"{name}: file not found ({path})"
        print(f"[ASMA] WARNING: ...")
        return default
    except Exception as exc:
        _load_errors[name] = f"{name}: {type(exc).__name__}: {exc}"
        print(f"[ASMA] WARNING: ...")
        return default
```

If a file fails to load, the endpoint returns HTTP 500 with a clear message (`_load_errors[name]`) rather than crashing the process.

### Startup Check (`_startup_check`)

Called at module load time, before any request is served:

```python
_REQUIRED_FILES = [
    "patients.csv", "samples.csv", "bins.jsonl", "isolates.jsonl",
    "interactions.json", "prebiotics.csv", "formulations.json",
]

def _startup_check():
    missing = [f for f in _REQUIRED_FILES if not (DATA_DIR / f).exists()]
    if missing:
        for fname in missing:
            print(f"[ASMA] WARNING: required file missing: {DATA_DIR / fname}")
    else:
        print(f"[ASMA] All required data files present in {DATA_DIR}")
```

Does not raise — the app starts even with partial data.

### Dual Field-Name Support (`_iso_links_any`)

The lineage endpoints now use a helper that handles both old and new Isolate schema:

```python
def _iso_links_any(iso: dict, bin_ids: set) -> bool:
    lb = iso.get("linked_bin")         # new schema: single str
    if lb and lb in bin_ids:
        return True
    lbs = iso.get("linked_bins")       # demo schema: list
    if isinstance(lbs, list):
        return any(b in bin_ids for b in lbs)
    return False
```

Network node labels similarly check `genus` first, falling back to `taxid_genus`.

### Endpoints Without `response_model` (and Why)

| Endpoint | Reason |
|----------|--------|
| `GET /bins` | No `Bin` Pydantic model defined; deferred to future sprint |
| `GET /prebiotics` | No `Prebiotic` Pydantic model defined |
| `GET /network` | Returns composite `{nodes, edges}` structure, not a single entity list |
| `GET /lineage/patient/{id}` | Returns `{patient, samples, bins, isolates}` composite |
| `GET /lineage/sample/{id}` | Returns `{sample, bins, isolates}` composite |
| `POST /formulations/preview` | Uses existing `FormPreviewIn` input model; output structure is custom |
| `GET /search` | Returns `{patients, samples, bins, isolates}` composite |
| `GET /download/{entity}.csv` | Returns `Response` object, not a Pydantic model |
| `GET /bins/{bin_id}/pathways` | Returns `{bin_id, pathways}` composite |

---

## 9. Deployment Procedure

### Prerequisites

- THAR server access (`protect.qb3.berkeley.edu`) as `spencerlong`
- Podman available (`/usr/bin/podman`)
- Source files accessible at expected paths (see §4)

### Step 1 — Build Image

```bash
cd /usr2/people/spencerlong/asma-prototype
podman build -t localhost/asma-prototype:main-latest -f Dockerfile .
```

**Result on April 12, 2026:**
```
Successfully tagged localhost/asma-prototype:main-latest
Image ID: eea77c80f4ee3c255aa28bf375b25995ae3386973f8fcb22d944256bf4d48522
Image size: 456 MB
Pydantic version in container: 2.12.5
FastAPI version in container: 0.135.3
Python version in container: 3.13
```

The Dockerfile is a three-stage build: (1) Python backend stage installs requirements and copies `backend/`, (2) Node frontend stage builds the React SPA, (3) final stage combines both.

### Step 2 — Stop and Remove Old Container

```bash
systemctl --user stop container-asma-proto.service
podman stop asma-proto-v10
podman rm asma-proto-v10
```

### Step 3 — Launch with Real Data

```bash
podman run -d --name asma-proto-v10 -p 8765:5000 \
  -v /usr2/people/spencerlong/asma-prototype/real_data:/app/demo_data:ro \
  -v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro \
  -e ASMA_DATA_DIR=/app/demo_data \
  -e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html \
  localhost/asma-prototype:main-latest
```

Two volume mounts:
- `real_data/ → /app/demo_data` (the data files; read-only)
- `alex.styer/public_html/ → /app/alex_public_html` (taxonomy TSV, treemap HTML, logo; read-only)

### Step 4 — Re-register with Systemd

```bash
systemctl --user start container-asma-proto.service
```

The service unit at `~/.config/systemd/user/container-asma-proto.service` calls `podman start asma-proto-v10`. Since the container is already running from Step 3, this is a no-op that confirms the service is managing the container.

### Step 5 — Verify

```bash
curl -s http://127.0.0.1:8765/health | python3 -m json.tool
# Expected: {"status": "ok", "data_dir": "/app/demo_data"}

curl -s http://127.0.0.1:8765/patients | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Patients: {len(d)}')"
# Expected: Patients: 35

curl -s http://127.0.0.1:8765/samples | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Samples: {len(d)}')"
# Expected: Samples: 241

curl -s http://127.0.0.1:8765/isolates | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Isolates: {len(d)}')"
# Expected: Isolates: 4259

podman logs --tail 20 asma-proto-v10
# Expected in logs:
# [ASMA] All required data files present in /app/demo_data
# [ASMA] Taxonomy files found at /app/alex_public_html
```

> **Note on CNI warnings:** `podman` logs contain two recurring `level=warning` lines about CNI config validation (`firewall` plugin does not support config version `"1.0.0"`). These are a pre-existing network configuration artifact on THAR, present in all podman invocations on this system, and are unrelated to the ASMA application.

---

## 10. Validation Results & Data Quality Notes

### ETL Run Results (April 13 00:58:54 UTC)

| Entity | Valid | Failed | NaN in output CSV | None string in output |
|--------|-------|--------|-------------------|----------------------|
| patients | **35** | **0** | 0 | 0 |
| samples | **241** | **0** | 0 | 0 |
| isolates | **4,259** | **0** | N/A (JSONL) | N/A |

```bash
grep -c "NaN" real_data/patients.csv real_data/samples.csv
# patients.csv:0
# samples.csv:0
```

All 5 source files confirmed present (`true`) in `etl_validation_report.json`.

### Warning: Taxonomy Join Gap

```
Taxonomy join: 63/4259 isolates (1.5%) had no taxonomy match
→ genus/taxonomy set to "Unknown"
```

These 63 ASMA IDs exist in the gold isolation layer but are absent from Alex Styer's `taxonomy.tsv`. Probable causes: recently cultured isolates not yet genome-sequenced, or sequencing complete but TSV not yet updated. **Action item:** extract these 63 ASMA IDs and share with Alex Styer for taxonomy follow-up.

To identify them:
```bash
python3 -c "
import json
isolates = [json.loads(l) for l in open('real_data/isolates.jsonl')]
gaps = [r['isolate_id'] for r in isolates if r['taxonomy'] == 'Unknown']
print(f'{len(gaps)} isolates with Unknown taxonomy:')
for g in gaps[:10]: print(f'  {g}')
if len(gaps) > 10: print(f'  ... and {len(gaps)-10} more')
"
```

### 22 Rows Excluded from Isolates

The gold layer CSV contains 22 rows where `ASMA_id` is empty (not null — they have `has_isolates=True` but no assigned ASMA ID). These are excluded by `iso_df.dropna(subset=["ASMA_id"])`. This is correct behavior: these rows represent samples in the isolation workflow that have not yet received an ASMA identifier. They are **not** a data loss — they were never valid isolate records.

### Validation Report

`etl_validation_report.json` is written to `real_data/` on every ETL run. Review it immediately after each run:
```bash
cat real_data/etl_validation_report.json | python3 -m json.tool
```

---

## 11. Git & Branch Strategy

- **Repo:** [github.com/WeArePROTECT/asma-prototype](https://github.com/WeArePROTECT/asma-prototype)
- **Branch protection:** `main` is protected — all changes require a pull request with at least one review. Direct pushes are rejected.
- **Feature branch:** `feat/pydantic-validation-real-data` — pushed to remote successfully
- **Commit:** `675ff94` — "feat: production ETL with Pydantic validation + real data integration"
- **PR URL:** `https://github.com/WeArePROTECT/asma-prototype/pull/new/feat/pydantic-validation-real-data`

### Current State (as of April 12, 2026)

```
origin/main        deab605  chore: ignore ops diagnostics and REORG_PLAN
local/main         675ff94  feat: production ETL with Pydantic validation + real data integration
origin/feat/...    675ff94  (same — pushed to remote feature branch)
```

Local `main` is **1 commit ahead of `origin/main`**. The running container is built from local `main` (commit `675ff94`) and is stable. `origin/main` will be updated once the PR is reviewed and merged.

### What Is Not in Git

The `real_data/` output files (CSVs, JSONL, JSON) are not committed and should not be — they are generated artifacts containing patient data. They live only on THAR disk. The `real_data/prepare_real_data.py` script **is** committed and is the reproducible way to regenerate them.

`demo_data/` is committed, untouched, and preserved as a safe development fallback.

---

## 12. Known Gaps & Deferred Work

| Gap | Data Available | Location | Work Needed | Priority |
|-----|---------------|----------|-------------|----------|
| `amr_flags` reflect patient antibiotic *treatment*, not isolate AMR *genes* | GenomeDepot `Annotation` + `Gene` tables | `gd-db:3306`, db `genomedepot` | SQL export query: `WHERE annotation_type='AMR' AND strain_id=ASMA_id`; join into isolates at ETL time | Medium |
| `pathways` / `pathways_scored` empty on all bins | KEGG pathway data available | `WoL2_Subset50_species_KEGG_WoL_filtered_cpm.tsv` (7.2 MB, 8,318 species×KO features) | KO → pathway rollup script; add to bins.jsonl at ETL time | Medium |
| `linked_bin` coverage: only 212/4,259 isolates (5%) have a linked bin | CPM table covers 74 metaG samples (PRO97+); isolation samples skew toward PRO1–PRO49 | WoL2 analysis directory | Expand metagenomics coverage to earlier PRO IDs as new data arrives | Low — data-dependent |
| `interactions.json` empty | WoL2 CPM table has 134 species × 74 samples — sufficient for co-occurrence | CPM TSV (see §4.5) | Compute Spearman correlation per species-pair across shared samples above 0.5% threshold | Medium |
| `metabolite_markers` on isolates: always `[]` | No metabolomics data exists in current pipeline | None identified | N/A at this time | Low |
| `prebiotics.csv`: two demo placeholder records | No real prebiotic data source identified | Demo data | Identify real prebiotic inventory; likely lives in lab inventory or literature | Low |
| Pydantic `response_model` on composite endpoints (`/bins`, `/network`, `/search`, `/lineage/*`, `/download/*`, `/formulations/preview`, `/bins/{id}/pathways`) | All data already in codebase | `backend/app/main.py` | Define `Bin`, `Prebiotic`, `Interaction` Pydantic models; wrap composite responses | Low |

---

## 13. Next Steps: UI Improvements

With real PROTECT data now flowing through the prototype, the next development phase is UI/UX improvements. The prototype was reviewed with real data for the first time on April 12, 2026. Real data surfaces display and interaction issues that synthetic data never revealed:

- **Patient card content:** Real patients have many more clinical fields (FEV1, FVC, BMI, CFTR modulator status) that are not yet surfaced in the patient detail view.
- **Sample detail view:** The 28-field Sample schema (vs. 5 in the demo) contains rich clinical and metagenomic context that should be shown when a user drills into a sample.
- **Isolate cards:** Full taxonomy lineage (phylum → class → order → family → genus → species) is now available and should replace the current single-genus display.
- **Network view labeling:** Node labels currently show genus; species-level labels (now available) would be more informative.
- **Assessment of PEX / antibiotic status:** These per-sample clinical flags are now available and could be useful as filter dimensions in the patient/sample tables.

A dedicated UI review session is planned to capture and prioritize specific improvements. These will be tracked as GitHub issues on [WeArePROTECT/asma-prototype](https://github.com/WeArePROTECT/asma-prototype).

---

## 14. Runbook: Re-running the ETL When New Data Arrives

Follow these steps whenever the PROTECT data integration pipeline produces a new dated run folder.

**1. SSH to THAR**
```bash
ssh spencerlong@protect.qb3.berkeley.edu
```

**2. Confirm new dated folder exists**
```bash
ls /usr2/people/protect/Arkin_Lab/protect_data/protect_data_integration_pipeline/pipeline_outputs/runs/
```
The ETL auto-detects the most recent folder — no config change needed.

**3. Run the ETL**
```bash
python3 /usr2/people/spencerlong/asma-prototype/real_data/prepare_real_data.py
```

**4. Review the validation report**
```bash
cat /usr2/people/spencerlong/asma-prototype/real_data/etl_validation_report.json | python3 -m json.tool
```
Check:
- All `source_files` values are `true`
- `summary` shows 0 `failed` counts for all entities
- `failures` list is empty
- `warnings` list — investigate any unexpected entries before proceeding

**5. If failures exist, investigate before restarting**

Failures are written with `entity`, `id`, `field`, `raw_value`, and `error`. Fix the root cause in the source data or in the ETL script, then re-run from step 3.

**6. Restart the container to reload data files**

The backend reads files at startup — a container restart is required to pick up new data.

```bash
systemctl --user stop container-asma-proto.service
podman stop asma-proto-v10 && podman rm asma-proto-v10

podman run -d --name asma-proto-v10 -p 8765:5000 \
  -v /usr2/people/spencerlong/asma-prototype/real_data:/app/demo_data:ro \
  -v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro \
  -e ASMA_DATA_DIR=/app/demo_data \
  -e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html \
  localhost/asma-prototype:main-latest

systemctl --user start container-asma-proto.service
```

> **Note:** If `backend/app/main.py` or `backend/app/schemas.py` have changed since the last build, run `podman build -t localhost/asma-prototype:main-latest -f Dockerfile .` before the `podman run` command above.

**7. Health checks**
```bash
curl -s http://127.0.0.1:8765/health
# Expected: {"status": "ok", "data_dir": "/app/demo_data"}

curl -s http://127.0.0.1:8765/patients | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'patients')"
curl -s http://127.0.0.1:8765/samples  | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'samples')"
curl -s http://127.0.0.1:8765/isolates | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'isolates')"
```

**8. Verify record counts match expectations**

Compare against the ETL validation report `summary` section. API counts should exactly match `valid` counts from the report.

---

## Appendix A: Schema Field Reference

### Patient

| Field | Type | Default | Source Column | Validator Notes |
|-------|------|---------|---------------|-----------------|
| `patient_id` | `str` | *required* | `patient_id` | Cast to str; raises if null |
| `age` | `Optional[float]` | `None` | `lung_function_age_years` | NaN/inf→None |
| `sex` | `Optional[str]` | `"Unknown"` | `sex_at_birth` | `"Male"→"M"`, `"Female"→"F"`, else `"Unknown"` |
| `condition` | `Optional[str]` | `"Unknown"` | `diagnosis` | Strip; empty→`"Unknown"` |
| `cohort` | `Optional[str]` | `"Unknown"` | `patient_population` | `"adult"→"Adult"`, `"pediatric"→"Pediatric"`, null→`"Unknown"` |
| `fev1_pp` | `Optional[float]` | `None` | `fev1_pp` | NaN/inf→None |
| `fev1_l` | `Optional[float]` | `None` | `fev1_l` | NaN/inf→None |
| `fvc_pp` | `Optional[float]` | `None` | `fvc_pp` | NaN/inf→None |
| `fvc_l` | `Optional[float]` | `None` | `fvc_l` | NaN/inf→None |
| `fev1_fvc_ratio` | `Optional[float]` | `None` | `fev1_fvc_ratio` | NaN/inf→None |
| `bmi` | `Optional[float]` | `None` | `bmi` | NaN/inf→None |
| `weight_kg` | `Optional[float]` | `None` | `weight_kg` | NaN/inf→None |
| `ht_cm` | `Optional[float]` | `None` | `ht_cm` | NaN/inf→None |
| `race` | `Optional[str]` | `None` | `race` | Strip; empty→None |
| `ethnicity` | `Optional[str]` | `None` | `ethnicity` | Strip; empty→None |
| `cftr_modulator_status` | `Optional[str]` | `None` | `cftr_modulator_status` | Strip; empty→None |
| `patient_population` | `Optional[str]` | `None` | `patient_population` | Strip; empty→None |

### Sample

| Field | Type | Default | Source Column | Validator Notes |
|-------|------|---------|---------------|-----------------|
| `sample_id` | `str` | *required* | `sample_id` | Cast to str; raises if null |
| `patient_id` | `str` | *required* | `patient_id` | Cast to str; raises if null |
| `sample_type` | `Optional[str]` | `None` | `sample_material` (lowercased) | Strip; empty→None |
| `collection_date` | `Optional[str]` | `None` | `collection_date` | Parses MM/DD/YYYY etc → YYYY-MM-DD; null→None |
| `visit_number` | `Optional[int]` | `None` | `visit_number` | int(float(v)); NaN→None |
| `days_since_first_collection` | `Optional[int]` | `None` | `days_since_first_collection` | int(float(v)); NaN→None |
| `project_id` | `str` | `"PROTECT"` | (hardcoded) | — |
| `patient_status_collection` | `Optional[str]` | `None` | `patient_status_collection` | Strip; empty→None |
| `assessment_of_pex` | `Optional[str]` | `None` | `assessment_of_pex` | Strip; empty→None |
| `antibiotic_status` | `Optional[str]` | `None` | `antibiotic_status` | Strip; empty→None |
| `any_iv_antibiotics` | `Optional[bool]` | `None` | `any_iv_antibiotics` | `"True"/"1"/"yes"→True`, `"False"/"0"/"no"→False` |
| `n_active_antibiotics` | `Optional[float]` | `None` | `n_active_antibiotics` | NaN/inf→None |
| `pa_positive` | `Optional[bool]` | `None` | `pa_positive` | Same as `any_iv_antibiotics` |
| `has_isolates` | `Optional[bool]` | `False` | `has_isolates` | Same bool coercion |
| `has_metag` | `Optional[bool]` | `False` | `has_metag` | Same bool coercion |
| `has_metars` | `Optional[bool]` | `False` | `has_metars` | Same bool coercion |
| `data_streams_count` | `Optional[int]` | `None` | `data_streams_count` | int(float(v)); NaN→None |
| `metag_shannon` | `Optional[float]` | `None` | `metag_shannon` | NaN/inf→None |
| `metag_richness` | `Optional[float]` | `None` | `metag_richness` | NaN/inf→None |
| `metag_chao1` | `Optional[float]` | `None` | `metag_chao1` | NaN/inf→None |
| `metag_simpson` | `Optional[float]` | `None` | `metag_simpson` | NaN/inf→None |
| `metag_total_reads` | `Optional[float]` | `None` | `metag_total_reads` | NaN/inf→None |
| `metag_alignment_rate` | `Optional[float]` | `None` | `metag_alignment_rate` | NaN/inf→None |
| `pa_alignment_pct` | `Optional[float]` | `None` | `pa_alignment_pct` | NaN/inf→None |
| `sampling_site` | `Optional[str]` | `None` | `sampling_site` | Strip; empty→None |
| `sample_material` | `Optional[str]` | `None` | `sample_material` | Strip; empty→None |
| `isolation_source_type` | `Optional[str]` | `None` | `isolation_source_type` | Strip; empty→None |
| `asma_id_count` | `Optional[int]` | `None` | `asma_id_count` | int(float(v)); NaN→None |

### Isolate

| Field | Type | Default | Source Column | Validator Notes |
|-------|------|---------|---------------|-----------------|
| `isolate_id` | `str` | *required* | `ASMA_id` | Must start with `"ASMA-"`; raises `ValueError` otherwise |
| `sample_id` | `str` | *required* | `pro_sample_id` (gold layer) | Back-compat: `source_sample_id` if `sample_id` absent |
| `patient_id` | `str` | *required* | `patient_id` | Cast to str; raises if null or empty |
| `taxonomy` | `Optional[str]` | `"Unknown"` | `taxonomy.tsv → Species` | null/blank→`"Unknown"` |
| `genus` | `Optional[str]` | `"Unknown"` | `taxonomy.tsv → Genus` | null/blank→`"Unknown"`; back-compat: `taxid_genus` |
| `family` | `Optional[str]` | `None` | `taxonomy.tsv → Family` | Strip; empty→None |
| `order` | `Optional[str]` | `None` | `taxonomy.tsv → Order` | Strip; empty→None |
| `class_` | `Optional[str]` | `None` | `taxonomy.tsv → Class` | Strip; empty→None. Note: `class_` avoids Python keyword collision |
| `phylum` | `Optional[str]` | `None` | `taxonomy.tsv → Phylum` | Strip; empty→None |
| `growth_media` | `Optional[str]` | `None` | `isolation_media` | Strip; empty→None |
| `genome_depot_id` | `Optional[str]` | `None` | `ASMA_id` | Same value as `isolate_id`; GenomeDepot lookup key |
| `linked_bin` | `Optional[str]` | `None` | Derived | First bin from CPM table for same/linked sample; back-compat: `linked_bins[0]` |
| `amr_flags` | `Optional[List[str]]` | `[]` | Gold layer antibiotic columns | List passthrough; JSON/CSV string parsed; null→`[]` |

---

## Appendix B: ETL Validation Report Structure

The report is written to `real_data/etl_validation_report.json` on every ETL run.

```json
{
  "run_timestamp": "2026-04-13T00:58:54Z",
  "source_files": {
    "platinum_csv":   true,
    "gold_csv":       true,
    "taxonomy_tsv":   true,
    "cpm_tsv":        true,
    "metag_meta_tsv": true
  },
  "source_paths": {
    "platinum_csv":   "/usr2/people/protect/.../protect_multiomics_isolate_sample_patient_integration_4_12_26.csv",
    "gold_csv":       "/usr2/people/protect/.../protect_clinical_isolate_sample_patient_merged_4_12_26.csv",
    "taxonomy_tsv":   "/usr2/people/alex.styer/public_html/taxonomy.tsv",
    "cpm_tsv":        "/usr2/people/protect/Zengler_Lab/.../WoL2_Subset50_multiomics_clean_filtered_cpm_metaG.tsv",
    "metag_meta_tsv": "/usr2/people/protect/Zengler_Lab/.../WoL2_Subset50_metaG_metadata.tsv"
  },
  "summary": {
    "patients":  {"valid": 35,   "failed": 0},
    "samples":   {"valid": 241,  "failed": 0},
    "isolates":  {"valid": 4259, "failed": 0}
  },
  "failures": [],
  "warnings": [
    "Taxonomy join: 63/4259 isolates (1.5%) had no taxonomy match → genus/taxonomy set to 'Unknown'"
  ]
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `run_timestamp` | UTC ISO-8601 timestamp of when the ETL run completed |
| `source_files` | Dict of `{logical_name: bool}` — whether each source file existed at run time |
| `source_paths` | Dict of `{logical_name: absolute_path}` — exact paths used in this run |
| `summary` | Per-entity count of `valid` (passed Pydantic validation) and `failed` rows |
| `failures` | List of dicts: `{entity, id, field, raw_value, error}` — one entry per failed field per failed row |
| `warnings` | List of non-fatal advisory strings — review after every run |

A clean run has `failures: []` and `warnings` containing only known, expected issues (e.g., the taxonomy gap note). Any unexpected failure entries should be investigated before the container is restarted.
