# Phase 1 Implementation Plan: SCFM Growth Metrics (Minimal Viable Implementation)

**Date:** [To be filled after approval]  
**Feature:** ASMA Unified Isolate Characterization Table (UICT)  
**Phase:** Phase 1 - SCFM Growth Metrics  
**Status:** Planning - Awaiting Approval

---

## Overview

This plan implements comprehensive SCFM growth analytics for each isolate and replicate, extending the existing minimal delta_OD calculation with time-point-specific metrics, binary growth calls, maximum yield tracking, and provisional growth rate (μ) estimation using a sliding-window approach.

---

## Dataset Information

**Source File:** `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx`  
**Sheet:** `SCFM_growth_curve`  
**Structure:**
- Columns: `sample_id`, `ASMA_id`, `assay_start_date`, `cyc_1` through `cyc_193`
- Total cycles: 193
- Time interval: 15 minutes per cycle
- Time formula: `time_hours = (cycle_index - 1) × 0.25`
- Key time points:
  - 24 hours → cycle 97
  - 48 hours → cycle 193

---

## Phase 1 μ (mu_simple) Estimation Overview

**Purpose:** Provide provisional growth rate estimates for immediate analysis while reserving sophisticated Curveball-based methods for Phase 2.

**Approach:** Sliding-window log-linear regression on exponential growth segments.

**Method:**
1. Convert cycle indices to time (hours) using `time_hours = (cycle_index - 1) × 0.25`
2. Slide windows of size N cycles (between `SCFM_MU_WINDOW_MIN_CYCLES` and `SCFM_MU_WINDOW_MAX_CYCLES`)
3. For each window:
   - Filter OD values > `SCFM_MU_MIN_OD` (epsilon cutoff)
   - Compute `ln(OD)` and fit `ln(OD) ~ time_hours` with linear regression
   - Extract slope (μ candidate) and R²
4. Select best window:
   - Highest R²
   - R² >= `SCFM_MU_MIN_R2`
   - Positive slope (μ > 0)
   - OD increasing (no plateau)
5. Output: `mu_simple`, `mu_simple_r2`, `mu_simple_t_start_hours`, `mu_simple_t_end_hours`

**Note:** This is a provisional estimate. Phase 2 will integrate Curveball for model-based μ and K parameters.

---

## Implementation Steps

### STEP 1: Dataset Validation & Structure Verification

**Objective:** Validate the SCFM dataset structure and verify cycle columns exist.

**Tasks:**
1.1. Create validation function `validate_scfm_dataset()` in `etl/scfm.py`
   - Check that required columns exist: `sample_id`, `ASMA_id`, `assay_start_date`
   - Verify cycle columns `cyc_1` through `cyc_193` are present
   - Validate that cycle columns contain numeric data
   - Raise descriptive errors if validation fails

1.2. Add validation call in `scripts/build_uict_table.py` after loading SCFM sheet
   - Call validation function before processing
   - Print validation status to console

**Files to Modify:**
- `etl/scfm.py` (add validation function)
- `scripts/build_uict_table.py` (add validation call)

**Output:** Validation function that ensures data integrity before processing

---

### STEP 2: Update Configuration Constants

**Objective:** Add Phase 1 configuration constants to `etl/config.py`.

**Tasks:**
2.1. Add SCFM time point constants:
   - `SCFM_CYCLE_24H = 97` (24-hour time point)
   - `SCFM_CYCLE_48H = 193` (48-hour time point)
   - `SCFM_CYCLE_BASELINE = 1` (baseline cycle, typically cycle 1)

2.2. Add growth threshold constant:
   - `SCFM_GROWTH_DELTA_OD_THRESHOLD = 0.1` (default threshold for binary growth calls, configurable)

2.3. Add time conversion constant:
   - `SCFM_CYCLE_INTERVAL_HOURS = 0.25` (15 minutes = 0.25 hours)

2.4. Add μ (mu_simple) estimation configuration constants:
   - `SCFM_MU_WINDOW_MIN_CYCLES = 8` (minimum window size for μ estimation)
   - `SCFM_MU_WINDOW_MAX_CYCLES = 12` (maximum window size for μ estimation)
   - `SCFM_MU_MIN_OD = 0.01` (epsilon cutoff for log(OD) - filter out OD values <= this)
   - `SCFM_MU_MIN_R2 = 0.95` (minimum R² threshold for acceptable μ fit, configurable)

**Files to Modify:**
- `etl/config.py`

**Output:** Centralized configuration for Phase 1 metrics including μ estimation

---

### STEP 3: Implement Replicate-Level Metric Computation

**Objective:** Compute all required metrics at the replicate level in `etl/scfm.py`.

**Tasks:**
3.1. Create function `compute_replicate_metrics()` that computes:
   - **OD at 24 hours:** Extract `cyc_97` value → `od_24h`
   - **OD at 48 hours:** Extract `cyc_193` value → `od_48h`
   - **Baseline OD:** Extract `cyc_1` value → `od_baseline`
   - **ΔOD at 24h:** `od_24h - od_baseline` → `delta_od_24h`
   - **ΔOD at 48h:** `od_48h - od_baseline` → `delta_od_48h`
   - **Binary growth call at 24h:** `True` if `delta_od_24h >= threshold`, else `False` → `growth_24h`
   - **Binary growth call at 48h:** `True` if `delta_od_48h >= threshold`, else `False` → `growth_48h`
   - **Maximum growth yield:** `max(cyc_1, ..., cyc_193)` → `od_max_yield`
   - **Time of maximum yield:** Find cycle index where max occurs, convert to hours → `time_max_yield_hours`
     - Formula: `(cycle_index - 1) × 0.25`

3.2. Handle edge cases:
   - Missing cycle values (NaN) → propagate NaN to dependent metrics
   - All cycles identical → `time_max_yield_hours` = time of first occurrence
   - Multiple cycles with same max value → use first occurrence

3.3. Create function `compute_mu_simple()` for provisional growth rate estimation:
   - **Input:** Array of OD values for all cycles (cyc_1 through cyc_193)
   - **Time conversion:** Build `time_hours` array using `SCFM_CYCLE_INTERVAL_HOURS`:
     - `time_hours[i] = (cycle_index - 1) × 0.25` for each cycle
   - **Sliding window approach:**
     - Slide a window of N cycles between `SCFM_MU_WINDOW_MIN_CYCLES` and `SCFM_MU_WINDOW_MAX_CYCLES`
     - For each window position and size:
       - Filter out OD values <= `SCFM_MU_MIN_OD` (epsilon cutoff)
       - Compute `ln(OD)` for remaining values
       - Fit linear regression: `ln(OD) ~ time_hours`
       - Compute slope (mu_candidate) and R²
   - **Window selection criteria:**
     - Keep window with highest R²
     - Require R² >= `SCFM_MU_MIN_R2`
     - Require positive slope (mu_candidate > 0)
     - Require OD increasing (no obvious plateau - check that final OD in window > initial OD)
   - **Output replicate-level fields:**
     - `mu_simple`: Selected μ value (slope from best window) or NaN if no suitable window
     - `mu_simple_r2`: R² of selected fit or NaN
     - `mu_simple_t_start_hours`: Start time of selected window or NaN
     - `mu_simple_t_end_hours`: End time of selected window or NaN
   - **Edge cases:**
     - No window meets criteria → all fields = NaN
     - Insufficient data points after filtering → all fields = NaN
     - All OD values below `SCFM_MU_MIN_OD` → all fields = NaN

3.4. Update `process_scfm_growth_curve()` function:
   - Keep existing `od_min`, `od_max`, `delta_od`, `growth_class` calculations (for backward compatibility)
   - Add new Phase 1 metrics as additional columns (including μ metrics)
   - Call `compute_mu_simple()` for each replicate
   - Return DataFrame with both old and new columns

**Files to Modify:**
- `etl/scfm.py`

**Output:** Enhanced replicate-level processing with all Phase 1 metrics including provisional μ estimation

---

### STEP 4: Implement Isolate-Level Aggregation

**Objective:** Aggregate replicate-level metrics to isolate-level outputs in `etl/scfm.py`.

**Tasks:**
4.1. Update `aggregate_scfm_by_asma_id()` function to include Phase 1 aggregates:
   - **Keep existing aggregates:**
     - `scfm_n_reps` (count)
     - `scfm_delta_od_mean`, `scfm_delta_od_sd`, `scfm_delta_od_max`
     - `scfm_growth_class` (based on mean delta_od)
     - `scfm_last_assay_date`
   
   - **Add new Phase 1 aggregates:**
     - `scfm_od_24h_mean`, `scfm_od_24h_sd` (mean and SD of OD at 24h)
     - `scfm_od_48h_mean`, `scfm_od_48h_sd` (mean and SD of OD at 48h)
     - `scfm_delta_od_24h_mean`, `scfm_delta_od_24h_sd` (mean and SD of ΔOD at 24h)
     - `scfm_delta_od_48h_mean`, `scfm_delta_od_48h_sd` (mean and SD of ΔOD at 48h)
     - `scfm_growth_24h_n`, `scfm_growth_24h_pct` (count and percentage of replicates with growth at 24h)
     - `scfm_growth_48h_n`, `scfm_growth_48h_pct` (count and percentage of replicates with growth at 48h)
     - `scfm_od_max_yield_mean`, `scfm_od_max_yield_sd` (mean and SD of maximum yield)
     - `scfm_time_max_yield_mean`, `scfm_time_max_yield_sd` (mean and SD of time to max yield in hours)
     - **μ (mu_simple) aggregates:**
       - `scfm_mu_simple_mean`, `scfm_mu_simple_sd` (mean and SD of μ estimates)
       - `scfm_mu_simple_n_reps` (count of replicates with valid μ estimates)
       - `scfm_mu_simple_r2_mean`, `scfm_mu_simple_r2_sd` (mean and SD of R² values for μ fits)

4.2. Handle aggregation edge cases:
   - Single replicate → SD = NaN (already handled by pandas)
   - All replicates missing a metric → aggregate = NaN
   - Binary growth percentage: count `True` values, divide by total non-null replicates

**Files to Modify:**
- `etl/scfm.py`

**Output:** Enhanced aggregation function with all Phase 1 isolate-level metrics

---

### STEP 5: Update UICT Merge Logic

**Objective:** Ensure Phase 1 metrics are properly merged into final UICT table.

**Tasks:**
5.1. Update `merge_uict_data()` in `etl/aggregate.py`:
   - Add new Phase 1 SCFM columns to the empty columns list (if SCFM data is empty)
   - Ensure proper data types:
     - Float columns: all mean/SD/max metrics (including μ metrics)
     - Integer columns: `scfm_growth_24h_n`, `scfm_growth_48h_n`, `scfm_mu_simple_n_reps`
     - Float columns: `scfm_growth_24h_pct`, `scfm_growth_48h_pct`

5.2. Verify column order matches documentation

**Files to Modify:**
- `etl/aggregate.py`

**Output:** UICT merge logic handles all Phase 1 columns correctly

---

### STEP 6: Write Comprehensive Tests

**Objective:** Create thorough test coverage for Phase 1 functionality.

**Tasks:**
6.1. Create `tests/test_scfm_phase1.py` with tests for:
   - **Dataset validation:**
     - Valid dataset passes validation
     - Missing required columns raises error
     - Missing cycle columns raises error
     - Non-numeric cycle values raises error
   
   - **Replicate-level metrics:**
     - Correct extraction of OD at 24h and 48h
     - Correct ΔOD calculations (24h and 48h)
     - Binary growth calls with threshold = 0.1
     - Binary growth calls with custom threshold
     - Maximum yield calculation
     - Time of maximum yield calculation (cycle to hours conversion)
     - Edge case: all cycles identical
     - Edge case: missing cycle values (NaN handling)
     - Edge case: multiple cycles with same max (first occurrence)
   
   - **μ (mu_simple) estimation:**
     - Synthetic exponential curve with known μ → verify mu_simple is close to true value and R² is high
     - Flat curve (no growth) → verify μ is NaN or rejected
     - Curve with noisy data but clear exponential segment → verify selected window is correct and μ is positive
     - Edge case: all OD values below `SCFM_MU_MIN_OD` → verify all μ fields are NaN
     - Edge case: insufficient data points after filtering → verify all μ fields are NaN
     - Edge case: no window meets R² threshold → verify all μ fields are NaN
     - Edge case: negative slope (declining OD) → verify μ is rejected
     - Edge case: plateau (OD not increasing) → verify μ is rejected
   
   - **Isolate-level aggregation:**
     - Mean and SD calculations for all metrics (including μ metrics)
     - Binary growth percentage calculations
     - μ aggregation: mean, SD, count of valid estimates, R² aggregation
     - Single replicate handling (SD = NaN)
     - Multiple replicates with missing data
     - Empty DataFrame handling
   
   - **Integration:**
     - Full pipeline test with sample data
     - Verify all Phase 1 columns appear in output
     - Verify data types are correct

6.2. Update existing `tests/test_scfm.py`:
   - Ensure existing tests still pass with updated functions
   - Add tests for backward compatibility (old metrics still work)

**Files to Create:**
- `tests/test_scfm_phase1.py`

**Files to Modify:**
- `tests/test_scfm.py` (if needed for compatibility)

**Output:** Comprehensive test suite covering all Phase 1 functionality

---

### STEP 7: Update Main Pipeline Script

**Objective:** Ensure `scripts/build_uict_table.py` properly uses Phase 1 functions.

**Tasks:**
7.1. Verify that existing function calls work with updated signatures
7.2. Add console output for Phase 1 metrics:
   - Print count of replicates processed
   - Print summary statistics (e.g., mean growth at 24h, mean growth at 48h)
7.3. Ensure error handling is robust

**Files to Modify:**
- `scripts/build_uict_table.py`

**Output:** Updated pipeline script with Phase 1 integration

---

### STEP 8: Create Phase 1 Documentation

**Objective:** Document Phase 1 implementation for handoff.

**Tasks:**
8.1. Create `docs/phase_1/phase_1_scfm_metrics_spec.md`:
   - Document all replicate-level metrics (definitions, formulas, units)
   - Document all isolate-level aggregates (definitions, formulas, units)
   - Document time conversion logic
   - Document threshold configuration
   - **Document μ (mu_simple) metrics:**
     - Clearly label as "Phase 1 provisional growth rate estimates based on a sliding-window log(OD) vs time fit"
     - Explain sliding window approach
     - Document selection criteria (R² threshold, positive slope, increasing OD)
     - Document window size range and OD filtering
     - Note that Phase 2 will integrate Curveball for model-based μ and K, but mu_simple is available for immediate analysis
     - Include example calculations
   - Include example calculations for all metrics

8.2. Create `docs/phase_1/phase_1_scfm_progress.md`:
   - Track implementation progress
   - Document any deviations from plan
   - Document edge cases encountered and solutions
   - Document testing results

8.3. Update main `README.md` (if needed):
   - Add Phase 1 metrics to SCFM Growth section
   - Update schema documentation

**Files to Create:**
- `docs/phase_1/phase_1_scfm_metrics_spec.md`
- `docs/phase_1/phase_1_scfm_progress.md`

**Files to Modify:**
- `README.md` (if needed)

**Output:** Complete Phase 1 documentation

---

### STEP 9: Regenerate Final UICT Table

**Objective:** Generate updated UICT table with Phase 1 metrics.

**Tasks:**
9.1. Run full pipeline:
   ```bash
   cd /usr2/people/spencerlong/asma-prototype/features/asma_unified_isolate_characterization_table
   python3 scripts/build_uict_table.py
   ```

9.2. Verify output:
   - Check that all Phase 1 columns are present
   - Verify data types are correct
   - Spot-check a few isolates for reasonableness
   - Compare row count to previous version (should match)

9.3. Save output to `data/derived/asma_unified_isolate_characterization_table.csv`

**Files Generated:**
- `data/derived/asma_unified_isolate_characterization_table.csv` (updated)

**Output:** Updated UICT table with Phase 1 metrics

---

### STEP 10: Edge Case Review & Cleanup

**Objective:** Perform final edge case sweep and cleanup.

**Tasks:**
10.1. **Edge Case Review:**
    - Boundary conditions: cycles at exact boundaries (1, 97, 193)
    - Error cases: missing data, invalid cycles, negative OD values
    - Odd inputs: all zeros, all identical values, extreme outliers
    - Operational risks: large datasets, memory usage, processing time

10.2. **Cleanup Pass:**
    - Remove any debug print statements
    - Remove temporary test files
    - Ensure no unused imports
    - Verify directory structure is clean
    - Check for any files in wrong directories

10.3. **Code Quality:**
    - Run linter (if available)
    - Verify all functions have docstrings
    - Verify snake_case naming throughout
    - Verify modular code structure

**Files to Review:**
- All modified files in `etl/`, `tests/`, `scripts/`

**Output:** Clean, production-ready code with edge cases handled

---

## Summary of File Changes

### Files to Modify:
1. `etl/config.py` - Add Phase 1 configuration constants (including μ estimation config)
2. `etl/scfm.py` - Add validation, replicate metrics (including μ), and enhanced aggregation
3. `etl/aggregate.py` - Update merge logic for Phase 1 columns (including μ columns)
4. `scripts/build_uict_table.py` - Add validation and updated output
5. `tests/test_scfm.py` - Update for backward compatibility (if needed)
6. `README.md` - Update documentation (if needed)

### Files to Create:
1. `tests/test_scfm_phase1.py` - Comprehensive Phase 1 tests
2. `docs/phase_1/phase_1_scfm_metrics_spec.md` - Metrics specification
3. `docs/phase_1/phase_1_scfm_progress.md` - Implementation progress tracking

### Files Generated:
1. `data/derived/asma_unified_isolate_characterization_table.csv` - Updated UICT table

---

## Testing Strategy

1. **Unit Tests:** All new functions tested in isolation
2. **Integration Tests:** Full pipeline test with sample data
3. **Edge Case Tests:** Boundary conditions, missing data, invalid inputs
4. **Backward Compatibility:** Existing functionality still works
5. **Data Validation:** Output schema matches specification

---

## Success Criteria

- [ ] All Phase 1 metrics computed correctly at replicate level (including μ estimation)
- [ ] All Phase 1 aggregates computed correctly at isolate level (including μ aggregates)
- [ ] μ estimation correctly identifies exponential growth segments
- [ ] μ estimation rejects invalid curves (flat, declining, plateau)
- [ ] All tests pass (including μ estimation tests)
- [ ] Documentation complete (including μ metrics specification)
- [ ] UICT table regenerated with Phase 1 columns (including μ columns)
- [ ] Code follows snake_case and directory structure rules
- [ ] No debug code or temporary files
- [ ] Edge cases handled appropriately (including μ edge cases)

---

## Next Steps After Approval

1. Wait for explicit approval from user
2. Begin with STEP 1 (Dataset Validation)
3. Complete each step sequentially
4. Check in after each major step
5. Document progress in `phase_1_scfm_progress.md`
6. Ask for date before final documentation
7. Commit all work to `dev` branch
8. Ask about merging to `main` after completion

---

**END OF PLAN - AWAITING APPROVAL**

