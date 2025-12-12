# UICT v1 ETL Pipeline - Implementation Plan Via Cursor

## Overview

This document outlines the step-by-step implementation plan for building the ASMA Unified Isolate Characterization Table (UICT) v1 ETL pipeline.

## Goal

Implement an ETL pipeline that builds **UICT v1** (ASMA Unified Isolate Characterization Table).

UICT v1 should:

- Have one row per ASMA_id that exists in taxonomy.tsv.
- Use taxonomy.tsv as the authoritative taxonomy source.
- Derive SCFM growth metrics/calls, PA inhibition metrics/calls, and carbon utilization calls from Sun-Young's phenotype Excel.
- Exclude BLANK / control wells from the final isolate table, but allow using them internally for calculations if needed.
- Write a CSV: `data/derived/asma_unified_isolate_characterization_table.csv` in the ASMA codebase.

---

## Data Sources

1. **Taxonomy:**
   - `/usr2/people/alex.styer/public_html/taxonomy.tsv`
   - Columns (at least): ASMA_id, domain, phylum, class, order, family, genus, species, strain_group, representative.

2. **Phenotypes (Excel):**
   - `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx`
   - Sheets: `SCFM_growth_curve`, `pairwise_interaction`, `inhibition_standard_control`, `carbon_utilization`, `positive_growth`.
   - Per Sun-Young: ignore `positive_growth` for v1.

---

## Phenotype Logic to Implement

### SCFM growth (SCFM_growth_curve)

For each row (one biological replicate: ASMA_id + sample_id):

- Columns: sample_id, ASMA_id, assay_start_date, cyc_1 … cyc_193.
- Compute:
  - od_min = min(cyc_*)
  - od_max = max(cyc_*)
  - delta_od = od_max - od_min
- Per replicate growth class:
  - delta_od < 0.05 → "no_growth"
  - 0.05 ≤ delta_od < 0.1 → "poor"
  - 0.1 ≤ delta_od < 0.2 → "normal"
  - delta_od ≥ 0.2 → "robust"

Aggregate per ASMA_id:

- scfm_n_reps
- scfm_delta_od_mean
- scfm_delta_od_sd (if n>1)
- scfm_delta_od_max
- scfm_growth_class based on scfm_delta_od_mean using the same thresholds.

We will not use positive_growth (BHI) in v1.

### PA inhibition (pairwise_interaction + inhibition_standard_control)

**Control data (inhibition_standard_control):**

- Use only:
  - type = "reporter"
  - gain = 150
- Group by starting_OD and compute rfu_reporter_mean.
- Exclude known bad cases via configurable exclusion list:
  - starting_OD = 0.01 on assay_date = 2025-11-11 (only known exclusion currently)
  - Exclusion list should be editable for future cases

**Pairwise data (pairwise_interaction):**

- Use only:
  - gain = 150
  - rows where bacterium_2_ASMA_id is in PA_REPORTER_IDS (configurable list)
  - Sun-Young confirmed: bacterium_2 is always the reporter in valid pairwise assays
- For each row:
  - asma_id = bacterium_1_ASMA_id (the isolate)
  - pa_starting_od = bacterium_2_starting_OD
  - rfu_pairwise = raw_RFU
  - ratio = bacterium_1_starting_OD / bacterium_2_starting_OD

**Precise 100:1 ratio detection:**

- Use `math.isclose(ratio, 100.0, rel_tol=1e-3, abs_tol=1e-6)` to identify true 100:1 assays
- No wide numeric window - only exact 100:1 data is used

For each ASMA_id at 100:1:

- Compute inhibition_pct for each replicate:
  - inhibition_pct = 100 - (rfu_pairwise / rfu_reporter_mean_for_matching_pa_starting_od) * 100
- Aggregate per ASMA_id:
  - inhib_100x_mean
  - inhib_100x_sd
  - inhib_100x_n
  - inhib_last_assay_date (most recent assay_start_date)
- Classification:
  - inhib_100x_mean ≥ 50 → pa_inhibition_class = "strong"
  - 25 ≤ inhib_100x_mean < 50 → "weak"
  - < 25 → "none"

### Carbon utilization (carbon_utilization)

Per ASMA_id and per carbon substrate:

- Columns: ASMA_id, sample_id, assay_start_date, No_carbon, Glucose, Lactate, … (20+ carbons).

**Logic (must respect assay_date internally):**

1. **Per ASMA_id × assay_date:**
   - Compute mean_no_carbon(date) and sd_no_carbon(date) across replicates for No_carbon
   - For each carbon substrate C: compute mean_C(date) across replicates
   - Determine utilization per date using:
     - mean_C(date) > mean_no_carbon(date) + 2 * sd_no_carbon(date)
     - This prevents mixing baselines across plates

2. **Aggregate across dates per ASMA_id:**
   - Average of the date-wise means for each substrate
   - utilization = "utilizes" if ANY date passes threshold
   - Otherwise "no_growth" or "uncertain" depending on replication completeness

**Replicate definition:**
- A "replicate" is: Same ASMA_id + Same assay_date + Different sample_id or technical replicate values

For each substrate, keep:

- {substrate}_mean_od (aggregated across dates)
- {substrate}_utilization_call ("utilizes" | "no_growth" | "uncertain")
- carbon_last_assay_date (most recent assay_start_date)

Also store baseline once per ASMA_id:

- no_carbon_mean_od (aggregated across dates)
- no_carbon_sd_od (aggregated across dates)

---

## Implementation Plan

### Phase 1: Project Structure and Dependencies

**Step 1:** Create directory structure in `/usr2/people/spencerlong/asma-prototype/features/asma_unified_isolate_characterization_table/`:

```
asma_unified_isolate_characterization_table/
├── etl/                    # ETL pipeline code
│   ├── __init__.py
│   ├── config.py           # Configuration constants and settings
│   ├── loaders.py          # Data loading functions
│   ├── processors.py        # Phenotype processing logic
│   ├── aggregators.py      # Aggregation functions
│   └── pipeline.py         # Main ETL orchestration
├── api/                    # API endpoints (if needed)
│   ├── __init__.py
│   └── endpoints.py
├── frontend/               # Frontend components (if needed)
│   └── (reserved for future UI)
├── data/                   # Data directory
│   └── derived/            # Output location
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_loaders.py
│   ├── test_processors.py
│   ├── test_aggregators.py
│   └── test_pipeline.py
├── scripts/                # Utility scripts
│   └── run_etl.py          # CLI script to run pipeline
└── README.md               # Feature documentation
```

**Step 2:** Update `/usr2/people/spencerlong/asma-prototype/requirements.txt`:
- Add `pandas>=2.0.0`
- Add `openpyxl>=3.1.0` (for Excel reading)
- Add `numpy>=1.24.0` (for statistical calculations)
- Note: `math` module is part of Python standard library (no install needed)

### Phase 2: Data Loading Module (`etl/loaders.py`)

**Step 3:** Implement taxonomy loader:
- Function: `load_taxonomy_table(filepath: str) -> pd.DataFrame`
- Load TSV, validate required columns, return DataFrame
- Filter out any rows with missing `ASMA_id`

**Step 4:** Implement phenotype Excel loader:
- Function: `load_phenotype_excel(filepath: str) -> dict[str, pd.DataFrame]`
- Load all sheets, return dict keyed by sheet name
- Validate expected sheets exist
- Filter out BLANK/control wells where appropriate

**Step 5:** Add data validation helpers:
- Function: `validate_taxonomy_data(df: pd.DataFrame) -> bool`
- Function: `validate_phenotype_data(sheets: dict) -> bool`

### Phase 3: SCFM Growth Processor (`etl/processors.py`)

**Step 6:** Implement SCFM growth calculation:
- Function: `process_scfm_growth_curve(df: pd.DataFrame) -> pd.DataFrame`
- Filter out BLANK rows (where `ASMA_id == "BLANK"`)
- For each row: compute `od_min`, `od_max`, `delta_od`
- Classify each replicate: "no_growth"/"poor"/"normal"/"robust"
- Return DataFrame with: `sample_id`, `ASMA_id`, `od_min`, `od_max`, `delta_od`, `growth_class`

**Step 7:** Implement SCFM aggregation:
- Function: `aggregate_scfm_by_asma_id(df: pd.DataFrame) -> pd.DataFrame`
- Group by `ASMA_id`
- Compute: `scfm_n_reps`, `scfm_delta_od_mean`, `scfm_delta_od_sd`, `scfm_delta_od_max`
- Compute: `scfm_last_assay_date` (most recent assay_start_date)
- Classify based on `scfm_delta_od_mean` using same thresholds
- Return DataFrame with one row per `ASMA_id`

### Phase 4: PA Inhibition Processor (`etl/processors.py`)

**Step 8:** Process control data:
- Function: `process_inhibition_control(df: pd.DataFrame, exclusion_list: list) -> pd.DataFrame`
- Filter: `type == "reporter"` AND `gain == 150`
- Apply exclusions from configurable exclusion list (e.g., starting_OD == 0.01 on assay_date == 2025-11-11)
- Group by `starting_OD`, compute `rfu_reporter_mean`
- Return DataFrame: `starting_OD`, `rfu_reporter_mean`

**Step 9:** Process pairwise interaction data:
- Function: `process_pairwise_interactions(df: pd.DataFrame, control_df: pd.DataFrame, pa_reporter_ids: list) -> pd.DataFrame`
- Filter: `gain == 150` AND `bacterium_2_ASMA_id` is in `pa_reporter_ids` (configurable list)
- Compute `ratio = bacterium_1_starting_OD / bacterium_2_starting_OD`
- Filter for exact 100:1 ratio using `math.isclose(ratio, 100.0, rel_tol=1e-3, abs_tol=1e-6)`
- For each row: compute `inhibition_pct = 100 - (rfu_pairwise / rfu_reporter_mean_for_matching_pa_starting_od) * 100`
- Return DataFrame with: `ASMA_id`, `inhibition_pct`, `pa_starting_od`, `assay_start_date`, etc.

**Step 10:** Aggregate PA inhibition:
- Function: `aggregate_pa_inhibition_by_asma_id(df: pd.DataFrame) -> pd.DataFrame`
- Group by `ASMA_id`
- Compute: `inhib_100x_n`, `inhib_100x_mean`, `inhib_100x_sd`
- Compute: `inhib_last_assay_date` (most recent assay_start_date)
- Classify: "none"/"weak"/"strong" based on `inhib_100x_mean`
- Return DataFrame with one row per `ASMA_id`

### Phase 5: Carbon Utilization Processor (`etl/processors.py`)

**Step 11:** Process carbon utilization:
- Function: `process_carbon_utilization(df: pd.DataFrame) -> pd.DataFrame`
- Filter out BLANK rows (where `ASMA_id == "BLANK"`)
- **Step 11a:** For each `ASMA_id` × `assay_start_date`:
  - Compute `mean_no_carbon(date)` and `sd_no_carbon(date)` across replicates (same date)
  - For each carbon substrate C: compute `mean_C(date)` across replicates (same date)
  - Determine utilization per date: `mean_C(date) > mean_no_carbon(date) + 2 * sd_no_carbon(date)`
- **Step 11b:** Aggregate across dates per `ASMA_id`:
  - Average of date-wise means for each substrate
  - utilization = "utilizes" if ANY date passes threshold
  - Otherwise "no_growth" or "uncertain" based on replication completeness
- Compute `carbon_last_assay_date` (most recent assay_start_date)
- Return wide-format DataFrame with columns for each substrate

**Step 12:** Format carbon utilization for UICT:
- Function: `format_carbon_utilization_for_uict(df: pd.DataFrame) -> pd.DataFrame`
- Convert substrate names to lowercase snake_case (e.g., "Glucose" → "glucose")
- Create columns: `{substrate}_mean_od`, `{substrate}_utilization_call` for each substrate
- Include: `no_carbon_mean_od`, `no_carbon_sd_od`, `carbon_last_assay_date`
- Return one row per `ASMA_id`

### Phase 6: Main ETL Pipeline (`etl/pipeline.py`)

**Step 13:** Implement main pipeline:
- Function: `build_uict_v1(taxonomy_path: str, phenotype_path: str, output_path: str) -> pd.DataFrame`
- Load taxonomy and phenotype data
- Filter out BLANK rows from all phenotype sheets (ASMA_id == "BLANK")
- Process each phenotype type (SCFM, PA inhibition, carbon utilization)
- Merge all results on `ASMA_id` (left join from taxonomy - taxonomy is authoritative)
- **Critical:** Every ASMA_id from taxonomy.tsv must appear in final UICT, even if no phenotype data
- Use NaN/NULL for missing phenotype values
- Write to CSV with all columns in snake_case
- Return final DataFrame

**Step 14:** Add configuration module (`etl/config.py`):
- Constants for thresholds:
  - SCFM delta_OD thresholds: [0.05, 0.1, 0.2]
  - PA inhibition thresholds: [25, 50]
- PA reporter IDs (configurable list):
  ```python
  PA_REPORTER_IDS = [
      "PA14_KEH108_Reporter",
      "PA14_KEH108",
      "PA14_KEH108_reporter"
  ]
  ```
- Known bad control cases (editable exclusion list):
  ```python
  CONTROL_EXCLUSIONS = [
      {"starting_OD": 0.01, "assay_date": "2025-11-11"}
  ]
  ```
- 100:1 ratio tolerance: `rel_tol=1e-3, abs_tol=1e-6` for `math.isclose()`

### Phase 7: CLI Script (`scripts/run_etl.py`)

**Step 15:** Create command-line interface:
- Accept optional arguments for input/output paths
- Default to standard paths
- Run pipeline and print summary statistics
- Handle errors gracefully

### Phase 8: Testing (`tests/`)

**Step 16:** Create test fixtures:
- Sample taxonomy data
- Sample phenotype data (mini versions of each sheet)
- Expected output examples

**Step 17:** Write unit tests:
- `test_loaders.py`: Test data loading and validation
- `test_processors.py`: Test each processing function
- `test_aggregators.py`: Test aggregation logic
- `test_pipeline.py`: Test end-to-end pipeline

**Step 18:** Add integration test:
- Run pipeline on sample data
- Validate output schema and data quality

### Phase 9: Documentation

**Step 19:** Create `README.md`:
- Feature overview
- Data sources
- Processing logic summary
- Usage instructions
- Schema documentation

**Step 20:** Add docstrings:
- All functions with parameters, return types, and examples
- Module-level documentation

---

## Refined UICT v1 Schema

### Column Naming Convention
- Prefixes: `scfm_`, `inhib_100x_`, `pa_`, `{substrate}_`
- Suffixes: `_mean`, `_sd`, `_n`, `_max`, `_call`, `_class`

### Complete Schema

```python
# Identity & Taxonomy (from taxonomy.tsv)
asma_id: str                    # Primary key
domain: str
phylum: str
class: str                      # Note: 'class' is a Python keyword, but OK in CSV
order: str
family: str
genus: str
species: str
strain_group: float             # May be NaN
representative: str             # "Yes"/"No" or boolean

# SCFM Growth Metrics
scfm_n_reps: int                # Number of replicates
scfm_delta_od_mean: float       # Mean delta OD across replicates
scfm_delta_od_sd: float         # Standard deviation (NaN if n_reps < 2)
scfm_delta_od_max: float        # Maximum delta OD observed
scfm_growth_class: str          # "no_growth" | "poor" | "normal" | "robust"
scfm_last_assay_date: str       # Most recent assay_start_date (YYYYMMDD format)

# PA Inhibition Metrics (100:1 ratio)
inhib_100x_n: int               # Number of replicates at 100:1
inhib_100x_mean: float          # Mean inhibition percentage
inhib_100x_sd: float            # Standard deviation (NaN if n < 2)
pa_inhibition_class: str        # "none" | "weak" | "strong"
inhib_last_assay_date: str      # Most recent assay_start_date (YYYYMMDD format)

# Carbon Utilization (for each substrate)
# Substrates from discovery: No_carbon, Glucose, Lactate, Serine, Threonine, 
# Alanine, Glycine, Proline, Isoleucine, Leucine, Valine, Aspartate, Glutamate,
# Phenylalanine, Tryptophan, Lysine, Histidine, Arginine, Ornithine, Cystein, Methionine

# For each substrate (e.g., glucose, lactate, etc.):
# Note: All substrate names converted to lowercase snake_case
{substrate}_mean_od: float      # Mean OD for this substrate (aggregated across dates)
{substrate}_utilization_call: str  # "utilizes" | "no_growth" | "uncertain"

# Also store baseline:
no_carbon_mean_od: float        # Mean OD for No_carbon control (aggregated across dates)
no_carbon_sd_od: float          # SD for No_carbon control (aggregated across dates)
carbon_last_assay_date: str    # Most recent assay_start_date (YYYYMMDD format)
```

### Data Types Summary
- **Strings:** identity, taxonomy, classes/calls, date fields (YYYYMMDD format)
- **Integers:** counts (`_n` columns)
- **Floats:** means, SDs, max values
- **NaN allowed:** 
  - `strain_group` (from taxonomy)
  - `scfm_delta_od_sd` (if n_reps=1)
  - `inhib_100x_sd` (if n=1)
  - All phenotype fields if isolate has no phenotype data

---

## Clarifications and Resolutions

### ✅ 1. PA Reporter Identification
- **Resolution:** PA reporter strains must be configurable (not hard-coded)
- **Implementation:** Use configurable list `PA_REPORTER_IDS`:
  ```python
  PA_REPORTER_IDS = [
      "PA14_KEH108_Reporter",
      "PA14_KEH108",
      "PA14_KEH108_reporter"
  ]
  ```
- **Logic:** A row is considered reporter-based pairwise data if `bacterium_2_ASMA_id` is in that list
- **Confirmed:** Sun-Young confirmed bacterium_2 is always the reporter in valid pairwise assays

### ✅ 2. 100:1 Ratio Definition
- **Resolution:** Use precise 100:1 ratio detection (no wide range)
- **Implementation:** Use `math.isclose(ratio, 100.0, rel_tol=1e-3, abs_tol=1e-6)`
- **Logic:** Only true 100:1 assays are used for UICT inhibition metrics

### ✅ 3. Control Data Exclusion
- **Resolution:** Use configurable exclusion list (not hard-coded single case)
- **Known exclusion:** starting_OD = 0.01 on assay_date = 2025-11-11
- **Implementation:** Editable exclusion list in config for future cases

### ✅ 4. Missing Phenotype Data
- **Resolution:** Include every ASMA_id from taxonomy.tsv in UICT, even if phenotype data is missing
- **Implementation:** Use NaN/NULL for missing phenotype values
- **Logic:** Taxonomy is authoritative source - all isolates must appear

### ✅ 5. Carbon Substrate Naming
- **Resolution:** All UICT output columns must use lowercase snake_case
- **Examples:** `glucose_mean_od`, `glucose_utilization_call`, `scfm_delta_od_mean`
- **Implementation:** Convert substrate names to snake_case in output (may keep original internally)

### ✅ 6. Replicate Counting for Carbon Utilization
- **Resolution:** Replicate = Same ASMA_id + Same assay_date + Different sample_id
- **Implementation:** Carbon calculations done per ASMA_id × assay_date, then combined across dates
- **Logic:** Prevents mixing baselines across plates

### ✅ 7. Assay Date Handling
- **Resolution:** UICT v1 stores aggregated values AND last_assay_date fields
- **Fields to include:**
  - `scfm_last_assay_date`
  - `inhib_last_assay_date`
  - `carbon_last_assay_date`
- **Purpose:** Supports reproducibility without cluttering table with per-date fields

### ✅ 8. BLANK Filtering
- **Resolution:** Filter out all rows where `ASMA_id == "BLANK"` when constructing UICT
- **Implementation:** Filter from all phenotype sheets
- **Note:** BLANK rows may be kept internally if needed for baseline calculations
- **Requirement:** UICT must contain one row per ASMA_id that appears in taxonomy.tsv

---

## Implementation Requirements Summary

### Key Requirements
1. **Configurable PA Reporter IDs:** Use list, not hard-coded string
2. **Precise 100:1 Ratio:** Use `math.isclose()` with exact tolerance
3. **Carbon Utilization Date-Aware:** Compute per date, then aggregate
4. **Last Assay Dates:** Include `scfm_last_assay_date`, `inhib_last_assay_date`, `carbon_last_assay_date`
5. **Missing Data:** Use NaN/NULL for missing phenotype values
6. **BLANK Filtering:** Filter `ASMA_id == "BLANK"` from all phenotype sheets
7. **Snake Case Output:** All UICT columns in lowercase snake_case
8. **Taxonomy Authority:** Every ASMA_id from taxonomy.tsv must appear in UICT

### Output Location
- CSV file: `data/derived/asma_unified_isolate_characterization_table.csv`
- All columns in snake_case format
- One row per ASMA_id from taxonomy.tsv

---

## Next Steps

1. ✅ Review and approve this revised plan
2. ✅ All ambiguities resolved
3. ✅ Schema confirmed with last_assay_date fields
4. ⏳ **Ready for implementation** - await approval to proceed

