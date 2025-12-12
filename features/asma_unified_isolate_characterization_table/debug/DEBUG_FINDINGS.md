# Debug Findings: PA Inhibition Pipeline

## Summary from debug_inhibition.py (Successful Run)

### Key Findings:

1. **Pairwise Data Filtering Works:**
   - Total rows: 1,626
   - After gain == 150: 754 rows
   - After reporter filter: 754 rows (all match `PA14_KEH108_Reporter`)
   - After 100:1 filter: **324 rows** ✅

2. **100:1 Ratio Data:**
   - All 324 rows have `bacterium_2_starting_OD = 0.0001`
   - Ratio calculation: `bacterium_1_starting_OD / bacterium_2_starting_OD = 100.0`
   - Example: `0.01 / 0.0001 = 100.0`

3. **Merge Logic (from etl/inhibition.py lines 96-101):**
   ```python
   df_100x = df_100x.merge(
       control_df,
       left_on='bacterium_2_starting_OD',  # Value = 0.0001
       right_on='starting_OD',              # Need to check if this exists in control
       how='left'
   )
   ```

4. **The Problem:**
   - 324 rows pass the 100:1 filter
   - These rows have `bacterium_2_starting_OD = 0.0001`
   - The merge joins on `bacterium_2_starting_OD` (pairwise) == `starting_OD` (control)
   - **Likely issue:** Control data may not have `starting_OD = 0.0001` for reporter-only, gain=150 rows
   - After merge, rows with no matching control get `rfu_reporter_mean = NaN`
   - Line 119 filters out rows where `inhibition_pct` is NaN
   - Result: 0 rows survive → 0 isolates in final UICT

## What We Need to Check:

1. **Control Data:**
   - Does `inhibition_standard_control` have rows with:
     - `type == "reporter"`
     - `gain == 150`
     - `starting_OD == 0.0001`?
   
2. **Possible Issues:**
   - Control data might have `starting_OD = 0.0001` but with different `type` or `gain`
   - Control data might have `starting_OD = 0.0001` but it gets excluded by `CONTROL_EXCLUSIONS`
   - Data type mismatch (float vs string)
   - Precision issue (0.0001 vs 0.00010000001)

## Next Steps:

1. Manually check control sheet for `starting_OD = 0.0001` with reporter + gain=150
2. If missing, check what `starting_OD` values DO exist in control data
3. Determine if we need to:
   - Adjust the merge key
   - Add missing control data
   - Use a different matching strategy (e.g., closest match, or group by date)

