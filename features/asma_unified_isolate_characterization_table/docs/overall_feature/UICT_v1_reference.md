# ASMA Unified Isolate Characterization Table (UICT) – Version 1 Specification

## 1. Overview

The **ASMA Unified Isolate Characterization Table (UICT)** was designed as a consolidated phenotype + taxonomy resource linking:

- **Taxonomic identity** (from taxonomy.tsv)
- **SCFM growth classification** (simple max−min OD-based rules)
- **PA inhibition phenotype**
- **Carbon utilization phenotype**
- **Metadata for traceability**

The goal of UICT v1 was to **enable researchers to compare isolates across multiple phenotype datasets** using a consistent `ASMA_id` join key, while keeping the outputs simple and interpretable.

This document captures the **original intended functionality** before the introduction of advanced SCFM kinetic modeling (Phase 1 & 2).

---

## 2. Data Sources Used in UICT v1

### 2.1 Taxonomy data
File:  
`/usr2/people/alex.styer/public_html/taxonomy.tsv`

Contains:
- ASMA_id  
- full taxonomic lineage (Domain → Species)  
- representative flags (not used in v1)  
- daily updates by Alex

**UICT rule:**  
All isolates in this file are included in UICT, even if they have missing phenotype data.

---

### 2.2 SCFM growth data (simple version)
File:  
`ASMA_phenotype_20251209.xlsx`, sheet: `SCFM_growth_curve`

Original UICT v1 used **only simple max−min OD differences**, not full growth kinetic models.

Fields extracted:
- `max_od` (maximum OD across cycles)  
- `min_od` (minimum OD across cycles)  
- `delta_od = max_od - min_od`  

Classification thresholds provided by Sun-Young:

| ΔOD Range | Growth Class |
|----------|--------------|
| <0.05 | no_growth |
| ≥0.05 | poor |
| ≥0.10 | normal |
| ≥0.20 | robust |

**Note:** UICT v1 did *not* use time-specific values (24h/48h) or μ.

---

### 2.3 PA inhibition data
Files:  
- Sheet: `pairwise_interaction`  
- Sheet: `inhibition_standard_control`

UICT v1 combined these to calculate **percent inhibition of PA reporter** at a **100:1 ASMA:PA ratio**, following Sun-Young’s formula:

Inhibition% = 100 - ((pairwise RFU / reporter-only RFU) × 100)

Key UICT v1 fields:
- `inhib_100x_mean`
- `inhib_100x_sd`
- `inhib_100x_n`
- `pa_inhibition_class`  
  - strong ≥ 50%  
  - weak ≥ 25%  
  - none < 25%  
- `inhib_last_assay_date`

---

### 2.4 Carbon utilization data

File:  
`ASMA_phenotype_20251209.xlsx`, sheet: `carbon_utilization`

UICT v1 extracted:

- endpoint OD for each carbon source (after 3 days)
- control OD (“no carbon” wells)
- phenotype call for each carbon source:

Utilizes carbon if: MeanOD(carbon) > MeanOD(no carbon) + 2 × SD(no carbon)

UICT outputs (summaries per isolate):
- count of positive substrates  
- list of positive substrates  
- number of replicates  
- last assay date

---

## 3. Core UICT v1 Schema (Original Spec)

### 3.1 Identity + taxonomy fields
| Column | Description |
|--------|-------------|
| `asma_id` | Unique isolate ID |
| `taxonomy_*` | Domain → Species lineage (from taxonomy.tsv) |

---

### 3.2 SCFM (simple) growth phenotype
| Column | Description |
|--------|-------------|
| `scfm_delta_od` | max−min OD |
| `scfm_growth_class` | no_growth / poor / normal / robust |
| `scfm_last_assay_date` | Most recent SCFM experiment date |

UICT v1 **did not** specify:
- yield at 24h or 48h  
- maximum yield time  
- μ (growth rate)  
- kinetic model fits  

These were added later in Phase 1 and 2.

---

### 3.3 PA inhibition phenotype
| Column | Description |
|--------|-------------|
| `inhib_100x_mean` | mean % inhibition at 100:1 ratio |
| `inhib_100x_sd` | SD |
| `inhib_100x_n` | number of replicates |
| `pa_inhibition_class` | strong / weak / none |
| `inhib_last_assay_date` | last measurement date |

---

### 3.4 Carbon utilization phenotype
| Column | Description |
|--------|-------------|
| `carbon_positive_count` | number of carbon sources utilized |
| `carbon_positive_list` | list of carbon sources utilized |
| `carbon_last_assay_date` | most recent carbon assay |

---

## 4. UICT v1 Philosophy (Original Goals)

UICT v1 was meant to:

- Provide a **unified table** connecting **taxonomy**, **SCFM growth class**, **PA inhibition**, and **carbon utilization**  
- Be **simple and robust**  
- Give researchers a **browsable table** for quick comparisons  
- Serve as a foundation for:
  - future modeling  
  - dashboards  
  - machine learning  
  - isolate prioritization for ASMA experiments

It **did not** aim to capture:
- growth kinetics  
- model-based parameters  
- μ estimation  
- time-resolved yield metrics  
- advanced competition modeling  

These belong to **Phase 1 & 2** expansions sparked by Jake’s needs.

---

## 5. Relationship Between UICT v1 and the New Work

| Component | UICT v1 | Phase 1 | Phase 2 |
|----------|---------|---------|---------|
| Taxonomy | ✔ | same | same |
| SCFM growth | simple ΔOD classification | timepoint yields, max yield, μ_simple | Curveball-based μ, K, lag |
| PA inhibition | ✔ | same | possibly improved integrations later |
| Carbon utilization | ✔ | same | same |
| Modeling | none | log-slope only | full growth models |
| Purpose | general phenotype table | Jake’s analysis needs | scientific-grade kinetics |

---

## 6. File Paths (Original Data Inputs)

- `taxonomy.tsv`  
- `ASMA_phenotype_20251209.xlsx`  
  - `SCFM_growth_curve`  
  - `pairwise_interaction`  
  - `inhibition_standard_control`  
  - `carbon_utilization`  
- UICT v1 codebase (directory containing `etl/`, `build_uict_table.py`, etc.)

---

## 7. Notes for Future Documentation

When building UICT v2 or v3:

- Keep UICT v1 fields intact  
- Add new fields with clear prefixes (`scfm_*`, `curveball_*`)  
- Maintain readability and backward compatibility  
