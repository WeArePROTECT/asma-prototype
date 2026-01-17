# ASMA Unified Isolate Characterization Table (UICT) v1

## Overview

UICT v1 is a unified table that combines taxonomy data with phenotype data (SCFM growth, PA inhibition, and carbon utilization) for all ASMA isolates. The table contains one row per `ASMA_id` from the authoritative taxonomy source.

## Data Sources

### Input Files

1. **Taxonomy** (authoritative source):
   - Path: `/usr2/people/alex.styer/public_html/taxonomy.tsv`
   - Format: TSV
   - Columns: `ASMA_id`, `domain`, `phylum`, `class`, `order`, `family`, `genus`, `species`, `strain_group`, `representative`

2. **Phenotype Data**:
   - Path: `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx`
   - Format: Excel workbook with multiple sheets
   - Sheets used:
     - `SCFM_growth_curve`: Growth curve data with cycle measurements
     - `pairwise_interaction`: Pairwise interaction data for PA inhibition
     - `inhibition_standard_control`: Control data for inhibition assays
     - `carbon_utilization`: Carbon source utilization data
     - `positive_growth`: Not used in v1 (per Sun-Young)

### Output File

- Path: `data/derived/asma_unified_isolate_characterization_table.csv`
- Format: CSV
- Rows: One per `ASMA_id` from taxonomy.tsv (all isolates included, even if no phenotype data)
- Missing phenotype data: Represented as NaN/NULL

## Processing Logic

### SCFM Growth

**Per Replicate:**
- Compute `od_min = min(cyc_*)` and `od_max = max(cyc_*)` across all cycle columns
- Compute `delta_od = od_max - od_min`
- Classify growth class:
  - `delta_od < 0.05` → `"no_growth"`
  - `0.05 ≤ delta_od < 0.1` → `"poor"`
  - `0.1 ≤ delta_od < 0.2` → `"normal"`
  - `delta_od ≥ 0.2` → `"robust"`

**Aggregation per ASMA_id:**
- `scfm_n_reps`: Number of replicates
- `scfm_delta_od_mean`: Mean delta OD across replicates
- `scfm_delta_od_sd`: Standard deviation (NaN if n_reps < 2)
- `scfm_delta_od_max`: Maximum delta OD observed
- `scfm_growth_class`: Classification based on `scfm_delta_od_mean` using same thresholds
- `scfm_last_assay_date`: Most recent assay date

### PA Inhibition (100:1 Ratio Only)

**Control Data Processing:**
- Filter: `type == "reporter"` AND `gain == 150`
- Exclude known bad cases (configurable in `etl/config.py`)
- Group by `starting_OD` and compute `rfu_reporter_mean`

**Pairwise Data Processing:**
- Filter: `gain == 150` AND `bacterium_2_ASMA_id` is in PA reporter list (configurable)
- Compute ratio: `bacterium_1_starting_OD / bacterium_2_starting_OD`
- Filter for exact 100:1 ratio using `math.isclose(ratio, 100.0, rel_tol=1e-3, abs_tol=1e-6)`
- Compute inhibition percentage: `inhibition_pct = 100 - (rfu_pairwise / rfu_reporter_mean) * 100`

**Aggregation per ASMA_id:**
- `inhib_100x_n`: Number of replicates at 100:1
- `inhib_100x_mean`: Mean inhibition percentage
- `inhib_100x_sd`: Standard deviation (NaN if n < 2)
- `pa_inhibition_class`: Classification based on `inhib_100x_mean`:
  - `inhib_100x_mean < 25` → `"none"`
  - `25 ≤ inhib_100x_mean < 50` → `"weak"`
  - `inhib_100x_mean ≥ 50` → `"strong"`
- `inhib_last_assay_date`: Most recent assay date

**Note:** Only 100:1 ratio data is used in v1. Other ratios are excluded.

### Carbon Utilization

**Date-Aware Processing:**
1. For each `ASMA_id × assay_start_date`:
   - Compute `mean_no_carbon(date)` and `sd_no_carbon(date)` across replicates
   - For each carbon substrate: compute `mean_C(date)` across replicates
   - Determine utilization per date: `mean_C(date) > mean_no_carbon(date) + 2 * sd_no_carbon(date)`

2. Aggregate across dates per `ASMA_id`:
   - Average of date-wise means for each substrate
   - Utilization = `"utilizes"` if ANY date passes threshold
   - Otherwise `"no_growth"` or `"uncertain"` depending on replication completeness

**Replicate Definition:**
- Same `ASMA_id` + Same `assay_start_date` + Different `sample_id`

**Per Substrate Columns:**
- `{substrate}_mean_od`: Mean OD aggregated across dates
- `{substrate}_utilization_call`: `"utilizes"` | `"no_growth"` | `"uncertain"`

**Baseline Columns:**
- `no_carbon_mean_od`: Mean OD for No_carbon control
- `no_carbon_sd_od`: SD for No_carbon control
- `carbon_last_assay_date`: Most recent assay date

**Minimum Replicates:**
- Requires ≥ 3 replicates for both No_carbon and substrate to make definitive calls
- < 3 replicates → `"uncertain"`

## Key Thresholds

### SCFM Growth
- **Delta OD thresholds:**
  - `no_growth`: < 0.05
  - `poor`: 0.05 - 0.1
  - `normal`: 0.1 - 0.2
  - `robust`: ≥ 0.2

### PA Inhibition
- **Inhibition percentage thresholds:**
  - `none`: < 25%
  - `weak`: 25% - 50%
  - `strong`: ≥ 50%
- **Ratio detection:** Exact 100:1 using `math.isclose()` with `rel_tol=1e-3, abs_tol=1e-6`
- **Gain requirement:** `gain == 150`

### Carbon Utilization
- **Threshold multiplier:** 2.0 × SD (mean_C > mean_no_carbon + 2 * sd_no_carbon)
- **Minimum replicates:** 3 for definitive calls

## Configuration

Configuration constants are defined in `etl/config.py`:

- `PA_REPORTER_IDS`: List of ASMA_ids that identify PA reporter strains
- `CONTROL_EXCLUSIONS`: List of known bad control cases to exclude
- `SCFM_DELTA_OD_THRESHOLDS`: Growth class thresholds
- `INHIBITION_THRESHOLDS`: Inhibition class thresholds
- `RATIO_100X_REL_TOL`, `RATIO_100X_ABS_TOL`: 100:1 ratio detection tolerance
- `CARBON_UTILIZATION_SD_MULTIPLIER`: Threshold multiplier for carbon utilization
- `CARBON_MIN_REPLICATES`: Minimum replicates for carbon utilization

## Usage

### Running the Pipeline

```bash
cd /usr2/people/spencerlong/asma-prototype/features/asma_unified_isolate_characterization_table
python3 build_uict_table.py
```

### Command-Line Options

```bash
python3 build_uict_table.py [--taxonomy PATH] [--phenotype PATH] [--output PATH]
```

- `--taxonomy`: Path to taxonomy TSV (default: `/usr2/people/alex.styer/public_html/taxonomy.tsv`)
- `--phenotype`: Path to phenotype Excel (default: `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx`)
- `--output`: Path to output CSV (default: `data/derived/asma_unified_isolate_characterization_table.csv`)

### Running Tests

```bash
python3 -m pytest tests/ -v
```

## Project Structure

```
asma_unified_isolate_characterization_table/
├── etl/                    # ETL pipeline code
│   ├── __init__.py
│   ├── config.py           # Configuration constants
│   ├── loaders.py          # Data loading functions
│   ├── scfm.py             # SCFM growth processing
│   ├── inhibition.py       # PA inhibition processing
│   ├── carbon.py           # Carbon utilization processing
│   └── aggregate.py        # Aggregation functions
├── tests/                  # Test suite
│   ├── test_scfm.py
│   ├── test_inhibition.py
│   └── test_carbon.py
├── data/                   # Data directory
│   └── derived/            # Output location
├── build_uict_table.py     # Main entry point
└── README.md               # This file
```

## Data Quality Notes

- **BLANK filtering:** All rows where `ASMA_id == "BLANK"` are filtered from phenotype processing
- **Missing data:** Isolates with no phenotype data are included with NaN values
- **Taxonomy authority:** Every `ASMA_id` from taxonomy.tsv appears in UICT, even if no phenotype data exists
- **Date handling:** Carbon utilization respects assay dates to prevent mixing baselines across plates
- **Precise ratio detection:** Only exact 100:1 ratios are used for PA inhibition (no wide tolerance window)

## Output Schema

See `UICT_V1_PREVIEW.md` for detailed schema and sample rows.

## Future Enhancements

- Support for other ratio ranges (e.g., 10:1, 1000:1)
- Date filtering options
- Additional phenotype data types
- API endpoints for querying UICT data

