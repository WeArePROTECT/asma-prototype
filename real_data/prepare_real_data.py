#!/usr/bin/env python3
"""
prepare_real_data.py
====================
Production-grade ETL: reads real PROTECT study sources, validates every row
against Pydantic schemas, writes API-compatible flat files to real_data/.

Sources (auto-detected)
-----------------------
PIPELINE_RUNS  most recent dated folder under .../pipeline_outputs/runs/
TAXONOMY_TSV   taxonomy.tsv in /usr2/people/alex.styer/public_html/

Outputs
-------
patients.csv           validated Patient rows
samples.csv            validated Sample rows
isolates.jsonl         validated Isolate rows (one JSON object per line)
etl_validation_report.json  structured run report (see § Report below)

Unchanged from previous run
---------------------------
bins.jsonl             re-generated from WoL2 CPM table (not validated by schema)
interactions.json      [] — requires co-occurrence analysis
formulations.json      [] — formulation tool output, not input data
prebiotics.csv         copied from demo  — no real prebiotic data source

Report fields
-------------
run_timestamp    UTC ISO-8601
source_files     dict of path → exists bool
summary          {entity: {valid: N, failed: N}}
failures         [{entity, id, field, raw_value, error}]
warnings         [str]
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

# ── Repo root on sys.path so we can import backend.app.schemas ────────────────
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.schemas import Isolate, Patient, Sample  # noqa: E402

# ── Fixed source locations ────────────────────────────────────────────────────

RUNS_BASE = Path(
    "/usr2/people/protect/Arkin_Lab/protect_data/"
    "protect_data_integration_pipeline/pipeline_outputs/runs"
)
ALEX_DIR = Path("/usr2/people/alex.styer/public_html")

WOL2_DIR = Path(
    "/usr2/people/protect/Zengler_Lab/Emma/WoL_Subset50_analysis/data"
)
CPM_TSV    = WOL2_DIR / "WoL2_Subset50_multiomics_clean_filtered_cpm_metaG.tsv"
METAG_META = WOL2_DIR / "WoL2_Subset50_metaG_metadata.tsv"
DEMO_DIR   = Path("/opt/shared/spencerlong/asma-prototype/demo_data")
OUT_DIR    = Path(__file__).parent


# ── Path auto-detection ───────────────────────────────────────────────────────

def _run_sort_key(p: Path) -> int:
    """Convert run folder name (M_D_YY or YYYY-MM-DD) to a sortable int."""
    parts = re.split(r"[-_]", p.name)
    try:
        nums = [int(x) for x in parts]
        if len(nums) == 3:
            # M_D_YY  →  (2000+YY)*10000 + M*100 + D
            if nums[0] <= 12 and nums[2] < 100:
                return (2000 + nums[2]) * 10000 + nums[0] * 100 + nums[1]
            # YYYY_MM_DD
            if nums[0] > 31:
                return nums[0] * 10000 + nums[1] * 100 + nums[2]
    except (ValueError, IndexError):
        pass
    return 0


def find_latest_run(runs_dir: Path) -> Path:
    dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not dirs:
        raise RuntimeError(f"No run folders found in {runs_dir}")
    return sorted(dirs, key=_run_sort_key, reverse=True)[0]


def find_taxonomy_tsv(alex_dir: Path) -> Path:
    for pat in ("taxonomy.tsv", "taxonomy*.tsv", "*.tsv"):
        hits = sorted(alex_dir.glob(pat))
        if hits:
            return hits[0]
    raise FileNotFoundError(f"No taxonomy TSV found in {alex_dir}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_true(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes")


def _safe_str(val: Any, default: str = "") -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    s = str(val).strip()
    return s if s else default


# ── Report accumulator ────────────────────────────────────────────────────────

_failures: list[dict] = []
_warnings: list[str] = []

_COUNTERS: dict[str, dict] = {
    "patients": {"valid": 0, "failed": 0},
    "samples":  {"valid": 0, "failed": 0},
    "isolates": {"valid": 0, "failed": 0},
}


def _capture(entity: str, row_id: str, exc: ValidationError, raw_row: dict) -> None:
    _COUNTERS[entity]["failed"] += 1
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(x) for x in loc) if loc else "unknown"
        raw_val = raw_row.get(field.split(".")[0], "<not in row>")
        _failures.append({
            "entity":    entity,
            "id":        row_id,
            "field":     field,
            "raw_value": str(raw_val)[:200],
            "error":     err.get("msg", str(err)),
        })


# ── 1. Auto-detect paths ──────────────────────────────────────────────────────

print("=" * 60)
print("Detecting source paths...")

latest_run = find_latest_run(RUNS_BASE)
print(f"  Latest run folder: {latest_run.name}")

# Find platinum and gold CSVs inside the run folder
platinum_candidates = sorted(latest_run.glob("*integration*.csv"))
gold_candidates     = sorted(latest_run.glob("*merged*.csv"))

if not platinum_candidates:
    raise FileNotFoundError(f"No *integration*.csv found in {latest_run}")
if not gold_candidates:
    raise FileNotFoundError(f"No *merged*.csv found in {latest_run}")

PLATINUM_CSV = platinum_candidates[0]
GOLD_CSV     = gold_candidates[0]
TAXONOMY_TSV = find_taxonomy_tsv(ALEX_DIR)

print(f"  Platinum CSV: {PLATINUM_CSV.name}")
print(f"  Gold CSV:     {GOLD_CSV.name}")
print(f"  Taxonomy TSV: {TAXONOMY_TSV.name}")


# ── 2. Load sources ───────────────────────────────────────────────────────────

print("\nLoading source files...")
platinum = pd.read_csv(PLATINUM_CSV, low_memory=False)
gold     = pd.read_csv(GOLD_CSV,     low_memory=False)
taxonomy = pd.read_csv(TAXONOMY_TSV, sep="\t")
taxonomy.columns = [c.strip() for c in taxonomy.columns]

cpm_ok  = CPM_TSV.exists()
meta_ok = METAG_META.exists()

cpm:        pd.DataFrame | None = None
metag_meta: pd.DataFrame | None = None

if cpm_ok:
    cpm = pd.read_csv(CPM_TSV, sep="\t", index_col=0)
    print(f"  CPM table:  {len(cpm):>5} species × {len(cpm.columns)} metaG samples")
else:
    _warnings.append(f"CPM table not found: {CPM_TSV}")
    print(f"  CPM table:  NOT FOUND")

if meta_ok:
    metag_meta = pd.read_csv(METAG_META, sep="\t")
    print(f"  metaG meta: {len(metag_meta):>5} rows")

print(f"  Platinum:   {len(platinum):>5} rows × {len(platinum.columns)} cols")
print(f"  Gold:       {len(gold):>5} rows × {len(gold.columns)} cols")
print(f"  Taxonomy:   {len(taxonomy):>5} rows × {len(taxonomy.columns)} cols")

# Build taxonomy lookup: ASMA_id → row dict
tax_index: dict[str, dict] = {}
for _, tr in taxonomy.iterrows():
    aid = _safe_str(tr.get("ASMA_id"))
    if aid:
        tax_index[aid] = tr.to_dict()


# ── 3. Patients ───────────────────────────────────────────────────────────────

print("\n[1/6] Building patients.csv ...")

has_redcap = platinum[platinum["has_redcap_metadata"].apply(_is_true)].copy()
if has_redcap.empty:
    has_redcap = platinum.copy()

patient_src = (
    has_redcap
    .sort_values("visit_number")
    .groupby("patient_id", as_index=False)
    .first()
)

valid_patients: list[dict] = []
for _, row in patient_src.iterrows():
    raw = row.to_dict()
    row_id = _safe_str(raw.get("patient_id"), default=f"row_{_}")
    try:
        p = Patient(
            patient_id          = raw.get("patient_id"),
            age                 = raw.get("lung_function_age_years"),
            sex                 = raw.get("sex_at_birth"),
            condition           = raw.get("diagnosis"),
            cohort              = raw.get("patient_population"),
            fev1_pp             = raw.get("fev1_pp"),
            fev1_l              = raw.get("fev1_l"),
            fvc_pp              = raw.get("fvc_pp"),
            fvc_l               = raw.get("fvc_l"),
            fev1_fvc_ratio      = raw.get("fev1_fvc_ratio"),
            bmi                 = raw.get("bmi"),
            weight_kg           = raw.get("weight_kg"),
            ht_cm               = raw.get("ht_cm"),
            race                = raw.get("race"),
            ethnicity           = raw.get("ethnicity"),
            cftr_modulator_status = raw.get("cftr_modulator_status"),
            patient_population  = raw.get("patient_population"),
        )
        valid_patients.append(p.model_dump())
        _COUNTERS["patients"]["valid"] += 1
    except ValidationError as exc:
        _capture("patients", row_id, exc, raw)

# Write CSV
if valid_patients:
    fieldnames = list(valid_patients[0].keys())
    with open(OUT_DIR / "patients.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(valid_patients)

print(f"  → {_COUNTERS['patients']['valid']} valid, "
      f"{_COUNTERS['patients']['failed']} failed")


# ── 4. Samples ────────────────────────────────────────────────────────────────

print("[2/6] Building samples.csv ...")

valid_samples: list[dict] = []

for _, row in platinum.iterrows():
    raw = row.to_dict()
    row_id = _safe_str(raw.get("sample_id"), default=f"row_{_}")
    try:
        s = Sample(
            sample_id                    = raw.get("sample_id"),
            patient_id                   = raw.get("patient_id"),
            sample_type                  = _safe_str(raw.get("sample_material")).lower() or None,
            collection_date              = raw.get("collection_date"),
            visit_number                 = raw.get("visit_number"),
            days_since_first_collection  = raw.get("days_since_first_collection"),
            project_id                   = "PROTECT",
            patient_status_collection    = raw.get("patient_status_collection"),
            assessment_of_pex            = raw.get("assessment_of_pex"),
            antibiotic_status            = raw.get("antibiotic_status"),
            any_iv_antibiotics           = raw.get("any_iv_antibiotics"),
            n_active_antibiotics         = raw.get("n_active_antibiotics"),
            pa_positive                  = raw.get("pa_positive"),
            has_isolates                 = raw.get("has_isolates"),
            has_metag                    = raw.get("has_metag"),
            has_metars                   = raw.get("has_metars"),
            data_streams_count           = raw.get("data_streams_count"),
            metag_shannon                = raw.get("metag_shannon"),
            metag_richness               = raw.get("metag_richness"),
            metag_chao1                  = raw.get("metag_chao1"),
            metag_simpson                = raw.get("metag_simpson"),
            metag_total_reads            = raw.get("metag_total_reads"),
            metag_alignment_rate         = raw.get("metag_alignment_rate"),
            pa_alignment_pct             = raw.get("pa_alignment_pct"),
            sampling_site                = raw.get("sampling_site"),
            sample_material              = raw.get("sample_material"),
            isolation_source_type        = raw.get("isolation_source_type"),
            asma_id_count                = raw.get("asma_id_count"),
        )
        valid_samples.append(s.model_dump())
        _COUNTERS["samples"]["valid"] += 1
    except ValidationError as exc:
        _capture("samples", row_id, exc, raw)

if valid_samples:
    fieldnames = list(valid_samples[0].keys())
    with open(OUT_DIR / "samples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(valid_samples)

print(f"  → {_COUNTERS['samples']['valid']} valid, "
      f"{_COUNTERS['samples']['failed']} failed")


# ── 5. Bins (re-generate from CPM, not schema-validated) ─────────────────────

print("[3/6] Building bins.jsonl ...")

bins: list[dict] = []
bin_by_sample: dict[str, list[str]] = {}

if cpm is not None:
    col_sums = cpm.sum(axis=0).replace(0, 1)
    cpm_norm = cpm.div(col_sums, axis=1)
    TOP_N, MIN_ABUND = 30, 0.005

    for col in cpm_norm.columns:
        pro_id = re.sub(r"_(metaG|metaRS|PA_align)$", "", col, flags=re.IGNORECASE)
        series = cpm_norm[col].sort_values(ascending=False)
        series = series[series >= MIN_ABUND].head(TOP_N)

        for rank, (species, rel_abund) in enumerate(series.items(), start=1):
            bid = f"BIN_{pro_id}_{rank:03d}"
            bins.append({
                "bin_id":          bid,
                "sample_id":       pro_id,
                "taxonomy":        str(species),
                "abundance":       round(float(rel_abund), 6),
                "pathways":        [],
                "pathways_scored": [],
                "notes": (
                    f"WoL2 metaG WoL2-Subset50; "
                    f"rank {rank} by relative abundance in {col}."
                ),
            })
            bin_by_sample.setdefault(pro_id, []).append(bid)

    print(f"  → {len(bins)} bins across {len(bin_by_sample)} metaG samples")
else:
    print("  → CPM unavailable; empty bins.jsonl")

with open(OUT_DIR / "bins.jsonl", "w") as f:
    for b in bins:
        f.write(json.dumps(b) + "\n")


# ── 6. Isolates ───────────────────────────────────────────────────────────────

print("[4/6] Building isolates.jsonl ...")

# Build metaG link map: pro_sample_id → [metaG PRO ids]
metag_link_map: dict[str, list[str]] = {}
if "apl_metag_same_sample" in gold.columns:
    for _, row in gold.drop_duplicates("pro_sample_id").iterrows():
        src = _safe_str(row.get("pro_sample_id"))
        lstr = _safe_str(row.get("apl_metag_same_sample"))
        ids = [x.strip() for x in re.split(r"[,|]", lstr) if x.strip()]
        mg_ids = [re.sub(r"_(metaG|metaRS)$", "", x, flags=re.IGNORECASE) for x in ids]
        if src and mg_ids:
            metag_link_map[src] = mg_ids

# Antibiotic columns (patient treatment, not isolate AMR — documented gap)
ABX_COLS = [c for c in gold.columns if any(k in c.lower() for k in [
    "tobramycin", "aztreonam", "amikacin", "azithromycin", "smx_tmp",
    "cipro", "levaquin", "augmentin", "ethambutol", "rifabutin",
    "clofaz", "ceftazidime", "clindamycin", "colistin", "doxycycline",
    "levofloxacin", "linezolid", "meropenem", "pipe_tazo", "tigecycline",
    "vancomycin",
])]

iso_df = gold[gold["has_isolates"].apply(_is_true)].copy()
iso_df = iso_df.dropna(subset=["ASMA_id"]).drop_duplicates("ASMA_id")

n_tax_miss = 0
valid_isolates: list[dict] = []

for _, row in iso_df.iterrows():
    raw = row.to_dict()
    asma_id  = _safe_str(raw.get("ASMA_id"))
    src_samp = _safe_str(raw.get("pro_sample_id"))

    # Taxonomy join
    tx = tax_index.get(asma_id, {})
    if not tx:
        n_tax_miss += 1

    # linked_bin: first bin from directly linked or metaG-linked sample
    linked: list[str] = list(bin_by_sample.get(src_samp, []))
    for mg in metag_link_map.get(src_samp, []):
        linked += bin_by_sample.get(mg, [])
    first_bin = linked[0] if linked else None

    row_id = asma_id or f"row_{_}"
    try:
        iso = Isolate(
            isolate_id    = asma_id,
            sample_id     = src_samp or None,
            patient_id    = raw.get("patient_id"),
            taxonomy      = tx.get("Species"),
            genus         = tx.get("Genus"),
            family        = tx.get("Family"),
            order         = tx.get("Order"),
            class_        = tx.get("Class"),
            phylum        = tx.get("Phylum"),
            growth_media  = raw.get("isolation_media"),
            genome_depot_id = asma_id,
            linked_bin    = first_bin,
            amr_flags     = [c for c in ABX_COLS if _is_true(raw.get(c, False))],
        )
        valid_isolates.append(iso.model_dump())
        _COUNTERS["isolates"]["valid"] += 1
    except ValidationError as exc:
        _capture("isolates", row_id, exc, raw)

if n_tax_miss:
    pct = 100.0 * n_tax_miss / max(1, len(iso_df))
    msg = (f"Taxonomy join: {n_tax_miss}/{len(iso_df)} isolates "
           f"({pct:.1f}%) had no taxonomy match → genus/taxonomy set to 'Unknown'")
    _warnings.append(msg)

with open(OUT_DIR / "isolates.jsonl", "w") as f:
    for r in valid_isolates:
        f.write(json.dumps(r) + "\n")

n_with_bin = sum(1 for r in valid_isolates if r.get("linked_bin"))
print(f"  → {_COUNTERS['isolates']['valid']} valid, "
      f"{_COUNTERS['isolates']['failed']} failed "
      f"({n_with_bin} with linked_bin)")


# ── 7. Interactions, Formulations, Prebiotics ─────────────────────────────────

print("[5/6] Writing interactions.json, formulations.json ...")
(OUT_DIR / "interactions.json").write_text("[]")
(OUT_DIR / "formulations.json").write_text("[]")

print("[6/6] Copying prebiotics.csv from demo ...")
src = DEMO_DIR / "prebiotics.csv"
if src.exists():
    shutil.copy(src, OUT_DIR / "prebiotics.csv")
else:
    (OUT_DIR / "prebiotics.csv").write_text("prebiotic_id,name,class,notes\n")
    _warnings.append(f"Demo prebiotics.csv not found at {src}; wrote empty file")


# ── 8. Validation report ──────────────────────────────────────────────────────

source_files = {
    "platinum_csv":   str(PLATINUM_CSV),
    "gold_csv":       str(GOLD_CSV),
    "taxonomy_tsv":   str(TAXONOMY_TSV),
    "cpm_tsv":        str(CPM_TSV),
    "metag_meta_tsv": str(METAG_META),
}

report = {
    "run_timestamp":  datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source_files":   {k: Path(v).exists() for k, v in source_files.items()},
    "source_paths":   source_files,
    "summary":        _COUNTERS,
    "failures":       _failures,
    "warnings":       _warnings,
}

report_path = OUT_DIR / "etl_validation_report.json"
report_path.write_text(json.dumps(report, indent=2))
print(f"\nValidation report → {report_path.name}")


# ── 9. File summary ───────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print(f"ETL complete → {OUT_DIR}")
total = 0
for p in sorted(OUT_DIR.iterdir()):
    if p.suffix == ".py":
        continue
    sz = p.stat().st_size
    total += sz
    print(f"  {p.name:<50} {sz:>10,} bytes")
print(f"  {'TOTAL':<50} {total:>10,} bytes")

print("\n=== SUMMARY ===")
for entity, counts in _COUNTERS.items():
    print(f"  {entity:<12}  valid={counts['valid']:>5}  failed={counts['failed']:>3}")
if _warnings:
    print("\n=== WARNINGS ===")
    for w in _warnings:
        print(f"  ⚠  {w}")
if _failures:
    print(f"\n=== FAILURES ({len(_failures)} total) ===")
    for f in _failures[:20]:
        print(f"  [{f['entity']}] {f['id']} | {f['field']} | "
              f"raw={f['raw_value']!r:.60} | {f['error']}")
    if len(_failures) > 20:
        print(f"  ... {len(_failures) - 20} more (see etl_validation_report.json)")
else:
    print("\n  No validation failures.")
