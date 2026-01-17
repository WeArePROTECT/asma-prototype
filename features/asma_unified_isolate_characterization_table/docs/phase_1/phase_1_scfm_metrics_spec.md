# Phase 1 SCFM Growth Metrics Specification

**Date:** [To be filled]  
**Feature:** ASMA Unified Isolate Characterization Table (UICT)  
**Phase:** Phase 1 - SCFM Growth Metrics  
**Status:** Complete

---

## Overview

Phase 1 implements comprehensive SCFM growth analytics for each isolate and replicate, extending the existing minimal delta_OD calculation with time-point-specific metrics, binary growth calls, maximum yield tracking, and provisional growth rate (μ) estimation.

---

## Time Conversion

**Cycle to Time Mapping:**
- Total cycles: 193
- Time interval: 15 minutes per cycle (0.25 hours)
- Time formula: `time_hours = (cycle_index - 1) × 0.25`
- Key time points:
  - Baseline: cycle 1 → 0 hours
  - 24 hours: cycle 97
  - 48 hours: cycle 193

---

## Replicate-Level Metrics

### OD Measurements

**`od_baseline`** (float)
- **Definition:** Optical density at baseline (cycle 1)
- **Units:** OD (dimensionless)
- **Formula:** `cyc_1`
- **Edge cases:** NaN if cycle 1 is missing

**`od_24h`** (float)
- **Definition:** Optical density at 24 hours (cycle 97)
- **Units:** OD (dimensionless)
- **Formula:** `cyc_97`
- **Edge cases:** NaN if cycle 97 is missing

**`od_48h`** (float)
- **Definition:** Optical density at 48 hours (cycle 193)
- **Units:** OD (dimensionless)
- **Formula:** `cyc_193`
- **Edge cases:** NaN if cycle 193 is missing

### ΔOD (Delta OD) Metrics

**`delta_od_24h`** (float)
- **Definition:** Change in OD from baseline to 24 hours
- **Units:** OD (dimensionless)
- **Formula:** `od_24h - od_baseline`
- **Edge cases:** NaN if either od_24h or od_baseline is missing

**`delta_od_48h`** (float)
- **Definition:** Change in OD from baseline to 48 hours
- **Units:** OD (dimensionless)
- **Formula:** `od_48h - od_baseline`
- **Edge cases:** NaN if either od_48h or od_baseline is missing

### Binary Growth Calls

**`growth_24h`** (boolean)
- **Definition:** Binary growth call at 24 hours
- **Formula:** `True` if `delta_od_24h >= SCFM_GROWTH_DELTA_OD_THRESHOLD` (default: 0.1), else `False`
- **Threshold:** Configurable in `etl/config.py` (`SCFM_GROWTH_DELTA_OD_THRESHOLD`)
- **Edge cases:** `False` if delta_od_24h is NaN

**`growth_48h`** (boolean)
- **Definition:** Binary growth call at 48 hours
- **Formula:** `True` if `delta_od_48h >= SCFM_GROWTH_DELTA_OD_THRESHOLD` (default: 0.1), else `False`
- **Threshold:** Configurable in `etl/config.py` (`SCFM_GROWTH_DELTA_OD_THRESHOLD`)
- **Edge cases:** `False` if delta_od_48h is NaN

### Maximum Yield Metrics

**`od_max_yield`** (float)
- **Definition:** Maximum optical density across entire growth curve
- **Units:** OD (dimensionless)
- **Formula:** `max(cyc_1, cyc_2, ..., cyc_193)`
- **Edge cases:** NaN if all cycles are missing

**`time_max_yield_hours`** (float)
- **Definition:** Time (in hours) when maximum yield occurs
- **Units:** Hours
- **Formula:** `(cycle_index_of_max - 1) × 0.25`
- **Edge cases:** 
  - If multiple cycles have the same max value, uses first occurrence
  - NaN if od_max_yield is NaN

### Provisional Growth Rate (μ) Metrics

**Note:** These are Phase 1 provisional growth rate estimates based on a sliding-window log(OD) vs time fit. Phase 2 will integrate Curveball for model-based μ and K parameters, but mu_simple is available for immediate analysis.

**`mu_simple`** (float)
- **Definition:** Provisional growth rate estimate (μ) from sliding-window log-linear regression
- **Units:** per hour (h⁻¹)
- **Method:**
  1. Convert cycle indices to time (hours): `time_hours = (cycle_index - 1) × 0.25`
  2. Slide windows of size N cycles (between `SCFM_MU_WINDOW_MIN_CYCLES` and `SCFM_MU_WINDOW_MAX_CYCLES`)
  3. For each window:
     - Filter OD values > `SCFM_MU_MIN_OD` (epsilon cutoff, default: 0.01)
     - Compute `ln(OD)` and fit `ln(OD) ~ time_hours` with linear regression
     - Extract slope (μ candidate) and R²
  4. Select best window:
     - Highest R²
     - R² >= `SCFM_MU_MIN_R2` (default: 0.95)
     - Positive slope (μ > 0)
     - OD increasing (no plateau: final OD > initial OD)
  5. Output: slope from best window
- **Edge cases:** NaN if no suitable window is found

**`mu_simple_r2`** (float)
- **Definition:** R² of the linear regression fit for the selected window
- **Units:** Dimensionless (0-1)
- **Range:** 0.0 to 1.0
- **Edge cases:** NaN if mu_simple is NaN

**`mu_simple_t_start_hours`** (float)
- **Definition:** Start time (in hours) of the selected window for μ estimation
- **Units:** Hours
- **Edge cases:** NaN if mu_simple is NaN

**`mu_simple_t_end_hours`** (float)
- **Definition:** End time (in hours) of the selected window for μ estimation
- **Units:** Hours
- **Edge cases:** NaN if mu_simple is NaN

**Configuration Constants:**
- `SCFM_MU_WINDOW_MIN_CYCLES = 8` (minimum window size)
- `SCFM_MU_WINDOW_MAX_CYCLES = 12` (maximum window size)
- `SCFM_MU_MIN_OD = 0.01` (epsilon cutoff for log(OD))
- `SCFM_MU_MIN_R2 = 0.95` (minimum R² threshold)

---

## Isolate-Level Aggregates

All replicate-level metrics are aggregated to isolate level by `ASMA_id` using the following operations:

### Mean and Standard Deviation Aggregates

For each replicate-level metric `X`, we compute:
- **`scfm_X_mean`**: Mean across all replicates
- **`scfm_X_sd`**: Standard deviation across replicates (NaN if n_reps < 2)

**Examples:**
- `scfm_od_24h_mean`, `scfm_od_24h_sd`
- `scfm_od_48h_mean`, `scfm_od_48h_sd`
- `scfm_delta_od_24h_mean`, `scfm_delta_od_24h_sd`
- `scfm_delta_od_48h_mean`, `scfm_delta_od_48h_sd`
- `scfm_od_max_yield_mean`, `scfm_od_max_yield_sd`
- `scfm_time_max_yield_mean`, `scfm_time_max_yield_sd`
- `scfm_mu_simple_mean`, `scfm_mu_simple_sd`
- `scfm_mu_simple_r2_mean`, `scfm_mu_simple_r2_sd`

### Binary Growth Aggregates

**`scfm_growth_24h_n`** (integer)
- **Definition:** Count of replicates with growth at 24h
- **Formula:** Count of replicates where `growth_24h == True`

**`scfm_growth_24h_pct`** (float)
- **Definition:** Percentage of replicates with growth at 24h
- **Units:** Percentage (0-100)
- **Formula:** `(scfm_growth_24h_n / total_replicates) × 100`
- **Edge cases:** NaN if total_replicates = 0

**`scfm_growth_48h_n`** (integer)
- **Definition:** Count of replicates with growth at 48h
- **Formula:** Count of replicates where `growth_48h == True`

**`scfm_growth_48h_pct`** (float)
- **Definition:** Percentage of replicates with growth at 48h
- **Units:** Percentage (0-100)
- **Formula:** `(scfm_growth_48h_n / total_replicates) × 100`
- **Edge cases:** NaN if total_replicates = 0

### μ (mu_simple) Aggregates

**`scfm_mu_simple_n_reps`** (integer)
- **Definition:** Count of replicates with valid μ estimates
- **Formula:** Count of replicates where `mu_simple` is not NaN

**`scfm_mu_simple_mean`** (float)
- **Definition:** Mean μ across replicates with valid estimates
- **Units:** per hour (h⁻¹)
- **Edge cases:** NaN if no valid μ estimates

**`scfm_mu_simple_sd`** (float)
- **Definition:** Standard deviation of μ across replicates
- **Units:** per hour (h⁻¹)
- **Edge cases:** NaN if n_reps < 2 or no valid μ estimates

**`scfm_mu_simple_r2_mean`** (float)
- **Definition:** Mean R² of μ fits across replicates
- **Units:** Dimensionless (0-1)
- **Edge cases:** NaN if no valid μ estimates

**`scfm_mu_simple_r2_sd`** (float)
- **Definition:** Standard deviation of R² values
- **Units:** Dimensionless (0-1)
- **Edge cases:** NaN if n_reps < 2 or no valid μ estimates

### Existing Aggregates (Maintained for Backward Compatibility)

- `scfm_n_reps`: Total number of replicates
- `scfm_delta_od_mean`, `scfm_delta_od_sd`, `scfm_delta_od_max`: Aggregates of overall delta_od
- `scfm_growth_class`: Classification based on mean delta_od
- `scfm_last_assay_date`: Most recent assay date

---

## Example Calculations

### Example 1: Simple Growth Curve

**Replicate Data:**
- Baseline (cyc_1): 0.10 OD
- 24h (cyc_97): 0.25 OD
- 48h (cyc_193): 0.35 OD
- Max yield: 0.35 OD at cycle 193

**Calculations:**
- `delta_od_24h = 0.25 - 0.10 = 0.15`
- `delta_od_48h = 0.35 - 0.10 = 0.25`
- `growth_24h = True` (0.15 >= 0.1)
- `growth_48h = True` (0.25 >= 0.1)
- `time_max_yield_hours = (193 - 1) × 0.25 = 48.0 hours`

### Example 2: μ Estimation

**Growth Curve:** Exponential growth with μ ≈ 0.02 h⁻¹

**Process:**
1. Convert cycles to time: cycles 20-30 → 4.75 to 7.25 hours
2. Filter OD > 0.01: All values pass
3. Compute ln(OD) and fit: `ln(OD) = intercept + 0.02 × time`
4. R² = 0.98 (exceeds threshold 0.95)
5. Slope is positive and OD is increasing
6. **Result:** `mu_simple = 0.02`, `mu_simple_r2 = 0.98`

### Example 3: Isolate Aggregation

**Replicates for ASMA-1:**
- Replicate 1: `od_24h = 0.20`, `growth_24h = True`, `mu_simple = 0.018`
- Replicate 2: `od_24h = 0.25`, `growth_24h = True`, `mu_simple = 0.022`
- Replicate 3: `od_24h = 0.15`, `growth_24h = False`, `mu_simple = NaN`

**Aggregates:**
- `scfm_od_24h_mean = (0.20 + 0.25 + 0.15) / 3 = 0.20`
- `scfm_od_24h_sd = 0.05` (standard deviation)
- `scfm_growth_24h_n = 2`
- `scfm_growth_24h_pct = (2 / 3) × 100 = 66.7%`
- `scfm_mu_simple_mean = (0.018 + 0.022) / 2 = 0.020`
- `scfm_mu_simple_n_reps = 2` (only 2 valid estimates)

---

## Configuration

All thresholds and constants are defined in `etl/config.py`:

```python
# Time points
SCFM_CYCLE_24H = 97
SCFM_CYCLE_48H = 193
SCFM_CYCLE_BASELINE = 1
SCFM_CYCLE_INTERVAL_HOURS = 0.25

# Growth threshold
SCFM_GROWTH_DELTA_OD_THRESHOLD = 0.1

# μ estimation
SCFM_MU_WINDOW_MIN_CYCLES = 8
SCFM_MU_WINDOW_MAX_CYCLES = 12
SCFM_MU_MIN_OD = 0.01
SCFM_MU_MIN_R2 = 0.95
```

---

## Edge Cases Handled

1. **Missing cycle values:** NaN propagated to dependent metrics
2. **All cycles identical:** time_max_yield_hours = time of first occurrence
3. **Multiple cycles with same max:** first occurrence used
4. **All OD values below μ threshold:** all μ fields = NaN
5. **Insufficient data points after filtering:** all μ fields = NaN
6. **No window meets R² threshold:** all μ fields = NaN
7. **Negative slope (declining OD):** μ rejected, all μ fields = NaN
8. **Plateau (OD not increasing):** μ rejected, all μ fields = NaN
9. **Single replicate:** SD = NaN (pandas default behavior)
10. **Zero replicates for growth percentage:** percentage = NaN

---

## Phase 2 Notes

Phase 2 will integrate Curveball for model-based μ and K (carrying capacity) parameter estimation. The `mu_simple` estimates provided in Phase 1 are provisional and suitable for immediate analysis, but Phase 2 will provide more sophisticated growth modeling.

---

**END OF SPECIFICATION**

