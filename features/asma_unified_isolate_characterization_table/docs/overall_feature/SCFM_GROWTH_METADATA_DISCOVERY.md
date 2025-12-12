# SCFM Growth Curve Metadata Discovery

**Date:** Generated from analysis of Excel and Word files in `/usr2/people/protect/Arkin_Lab/SYK`  
**Purpose:** Extract metadata about SCFM growth curves and plate-reader timing to compute growth yields and growth rates.

---

## 1. Cycle Timing Summary

### Time Per Cycle

**✅ CONFIRMED: 15 minutes per cycle**

**Evidence:** From `notes for ASMA_phenotype.xlsx.docx`:
> "Growth was monitored in a 384-well plate using a plate reader for ~48 hours (193 cycles at 15-minute intervals)."

### Total Duration

**✅ CONFIRMED: ~48 hours (48.25 hours)**

**Calculation:**
- 193 cycles × 15 minutes = 2,895 minutes = 48.25 hours

**Evidence:** Same quote as above, plus calculation matches the documented duration.

### Cycle to Timepoint Mapping

**Formula for Cycle → Time Conversion:**

```
time_hours = (cycle_index - 1) × 0.25
```

Where:
- `cycle_index` ranges from 1 to 193
- Time is in hours
- Cycle 1 corresponds to time = 0 hours (initial reading)
- Each subsequent cycle adds 15 minutes (0.25 hours)

**Key Timepoints:**

| Cycle Index | Time (hours) | Time (hours:minutes) | Notes |
|------------|--------------|---------------------|-------|
| cyc_1 | 0.00 | 0:00 | Initial reading (starting OD₆₀₀ = 0.01) |
| cyc_48 | 11.75 | 11:45 | ~12 hours |
| cyc_96 | 23.75 | 23:45 | **~24 hours** |
| cyc_97 | 24.00 | 24:00 | Exactly 24 hours |
| cyc_144 | 35.75 | 35:45 | ~36 hours |
| cyc_192 | 47.75 | 47:45 | **~48 hours** |
| cyc_193 | 48.00 | 48:00 | Final reading (48.25 hours total) |

**Note:** The notes mention "193 cycles at 15-minute intervals" covering "~48 hours". The actual data contains exactly 193 cycle columns (cyc_1 through cyc_193), confirming this.

### Cycle Index Details

**Data Structure:**
- **Total columns:** 196 (3 metadata columns + 193 cycle columns)
- **Metadata columns:** `sample_id`, `ASMA_id`, `assay_start_date`
- **Cycle columns:** `cyc_1`, `cyc_2`, ..., `cyc_193`
- **Total rows:** 765 (samples including blanks)

**Cycle Numbering:**
- Cycles are numbered starting from 1 (cyc_1, cyc_2, etc.)
- No evidence of skipped cycles or warmup time mentioned in the documentation
- Cycle 1 appears to be the first measurement after normalization

---

## 2. SCFM Experimental Setup

### Plate Reader Configuration

**Plate Type:** 384-well plate  
**Evidence:** From `notes for ASMA_phenotype.xlsx.docx`:
> "Growth was monitored in a 384-well plate using a plate reader..."

**Plate Reader Model:** Not explicitly documented in the files analyzed.

### Temperature, Wavelength, Shaking

**Wavelength:** OD₆₀₀ (600 nm)  
**Evidence:** From `notes for ASMA_phenotype.xlsx.docx`:
> "normalized to a starting OD₆₀₀ = 0.01"

**Temperature:** Not explicitly documented in the files analyzed.

**Shaking:** Not explicitly documented in the files analyzed.

### Background Subtraction / Blank Wells

**Blank Wells Present:** ✅ Yes

**Evidence:** From `ASMA_phenotype_20251209.xlsx` → `SCFM_growth_curve` sheet:
- Multiple rows with `ASMA_id = "BLANK"` are present in the data
- Example: sample_id 1, 2, 3 are all BLANK entries with assay_start_date values (20250920, 20250929, 20251003)

**Background Subtraction Method:** Not explicitly documented. The presence of BLANK wells suggests background subtraction may be applied, but the method is not described in the available documentation.

**OD Values Status:** The notes state "This dataset mainly consists of raw measurements, and a rigorous quality check has not yet been performed for each assay." This suggests the OD values may be raw (not background-subtracted), but blanks are available for manual subtraction if needed.

---

## 3. Growth Interpretation Notes

### Growth/No-Growth Thresholds

**Explicit Threshold:** Not found in the analyzed files.

**Existing Rule Mentioned:** The user mentioned existing "ΔOD ≥ 0.05" rules, but this was not found in the documentation files analyzed.

**Suggested Criterion (for carbon utilization, not SCFM):** From `notes for ASMA_phenotype.xlsx.docx`:
> "A suggested criterion for carbon utilization: Mean(sole carbon source) > Mean(no_carbon) + 2 × SD(no_carbon)"

This criterion is for carbon utilization assays, not SCFM growth curves, but may provide context for how growth thresholds are determined.

### Yield, Max OD, Growth Rate Definitions

**Yield:** Not explicitly defined in the documentation.

**Max OD:** Not explicitly defined, but could be calculated as the maximum OD value across all 193 cycles for each sample.

**Growth Rate (μ):** Not explicitly defined or mentioned in the documentation.

**Log Phase:** Not mentioned in the documentation.

### Replicate Handling

**Biological Replicates:** ✅ Present

**Evidence:** From `notes for ASMA_phenotype.xlsx.docx`:
> "Sample_ID: An arbitrary number assigned to distinguish individual biological replicates."

**Replicate Quality:** The notes mention:
> "I noticed several outliers among the biological replicates, but I currently lack a clear criterion for excluding them. Additional replicates will be performed for samples showing high variability, once there is sufficient evidence to justify re-measurement."

**Replicate Grouping:** Replicates can be identified by matching `ASMA_id` values, as multiple `sample_id` entries share the same `ASMA_id`.

**Starting Conditions:** All cultures were:
> "washed twice with buffer, resuspended in SCFM, and normalized to a starting OD₆₀₀ = 0.01"

This ensures consistent starting conditions across replicates.

---

## 4. Direct Quotes / Evidence Snippets

### From `notes for ASMA_phenotype.xlsx.docx`

**Full context on SCFM growth curves:**
> "growth_curve Each bacterial culture was washed twice with buffer, resuspended in SCFM, and normalized to a starting OD₆₀₀ = 0.01. Growth was monitored in a 384-well plate using a plate reader for ~48 hours (193 cycles at 15-minute intervals)."

**On data quality:**
> "This dataset mainly consists of raw measurements, and a rigorous quality check has not yet been performed for each assay. I noticed several outliers among the biological replicates, but I currently lack a clear criterion for excluding them."

**On sample identification:**
> "Sample_ID: An arbitrary number assigned to distinguish individual biological replicates. ASMA_ID: Represents the isolate's ASMA identifier. Assay_start_date: Indicates the start date of each assay (per sheet), used for tracking experimental records."

**On positive growth control:**
> "positive_growth Represents growth measurements of each ASMA isolate in BHI V2 after three days of incubation. If an isolate fails to grow even in BHI V2, its growth_curve and carbon_utilization data should be considered unreliable."

### From `ASMA_phenotype_20251209.xlsx` → `SCFM_growth_curve` sheet

**Data structure:**
- Shape: 765 rows × 196 columns
- Columns: `sample_id`, `ASMA_id`, `assay_start_date`, `cyc_1` through `cyc_193`
- Blank samples present: Multiple rows with `ASMA_id = "BLANK"`

**Example data (first few cycles for a growing sample):**
```
ASMA-133 (sample_id 7):
cyc_1: 0.095733
cyc_2: 0.097767
cyc_3: 0.101267
cyc_4: 0.103600
cyc_5: 0.105467
cyc_6: 0.107467
cyc_7: 0.109067
```
This shows clear growth from cycle 1 to cycle 7.

**Example blank (sample_id 1, ASMA_id BLANK):**
```
cyc_1: 0.095700
cyc_2: 0.094800
cyc_3: 0.095000
cyc_4: 0.095200
cyc_5: 0.095000
cyc_6: 0.095100
cyc_7: 0.095100
```
This shows stable, low OD values typical of blanks.

### From `APL_metadata.xlsx`

**SCFM-related entries:** 78 rows contain "SCFM" in the media column, indicating SCFM agar was used for initial isolation of many ASMA isolates. However, this is metadata about isolation media, not about the growth curve experiments themselves.

---

## 5. Open Questions

### Answered Questions ✅

1. ✅ **Cycle timing:** 15 minutes per cycle
2. ✅ **Total duration:** ~48 hours (48.25 hours)
3. ✅ **Cycle count:** 193 cycles (cyc_1 through cyc_193)
4. ✅ **24-hour timepoint:** Cycle 97 (exactly 24 hours) or cycle 96 (~24 hours)
5. ✅ **48-hour timepoint:** Cycle 193 (48 hours) or cycle 192 (~48 hours)
6. ✅ **Starting OD:** 0.01 (OD₆₀₀)
7. ✅ **Plate type:** 384-well plate
8. ✅ **Wavelength:** OD₆₀₀ (600 nm)
9. ✅ **Blanks present:** Yes, multiple BLANK entries in data

### Unanswered / Ambiguous Questions ❓

1. ❓ **Plate reader model:** Not documented
2. ❓ **Temperature:** Not documented
3. ❓ **Shaking settings:** Not documented (shaking speed, continuous vs. intermittent)
4. ❓ **Background subtraction method:** Blanks are present, but it's unclear if OD values are already background-subtracted or if manual subtraction is needed
5. ❓ **Explicit growth threshold for SCFM:** The existing "ΔOD ≥ 0.05" rule mentioned by the user was not found in the documentation
6. ❓ **Growth rate definition:** No explicit definition of μ (growth rate) or how to calculate it
7. ❓ **Yield definition:** Not explicitly defined (could be max OD, final OD, or area under curve)
8. ❓ **Log phase identification:** No criteria for identifying exponential/log phase
9. ❓ **Cycle 1 timing:** Assumed to be t=0, but not explicitly confirmed (could be t=15 min if cycle 1 is the first reading after a delay)
10. ❓ **Warmup time:** No mention of any initial warmup period or skipped early readings

### Recommendations for Jake

**For computing growth yields:**
- Consider multiple definitions: max OD, final OD (cyc_193), or area under the curve
- Subtract blank OD values if not already done
- Use replicates (group by ASMA_id) and report mean ± SD

**For computing growth rates:**
- Identify exponential phase (likely between cycles where OD increases consistently)
- Use linear regression on log(OD) vs. time in exponential phase
- Growth rate μ = slope of log(OD) vs. time (units: h⁻¹)
- Consider using cycles 10-50 or similar range (2.5-12.5 hours) as a starting point for log phase identification

**For timepoint analysis:**
- 24 hours ≈ cycle 96-97
- 48 hours = cycle 193 (final reading)
- Use formula: `time_hours = (cycle_index - 1) × 0.25`

---

## Files Analyzed

1. ✅ **APL_metadata.xlsx** - Contains isolation media metadata (78 SCFM agar entries), but not growth curve timing info
2. ✅ **ASMA_phenotype_20251209.xlsx** - Contains `SCFM_growth_curve` sheet with 193 cycles of data (765 samples)
3. ✅ **ASMA_phenotype.xlsx** - Contains `growth_curve` sheet (older version?)
4. ✅ **notes for ASMA_phenotype.xlsx.docx** - **PRIMARY SOURCE** for timing and experimental setup details
5. ✅ **notes for ASMA_list.xlsx and APL_metadata.xlsx.docx** - Contains metadata about isolate identification, not growth curves
6. ✅ **ASMA_list.xlsx** - Not analyzed in detail (appears to be isolate list, not growth data)

---

## Summary

**Most Important Findings:**

1. **Cycle interval: 15 minutes** ✅ (High confidence - explicitly stated in notes)
2. **Total hours: 48.25 hours (193 cycles)** ✅ (High confidence - calculation matches documentation)
3. **24-hour timepoint: Cycle 97** ✅ (High confidence - calculated from formula)
4. **48-hour timepoint: Cycle 193** ✅ (High confidence - final cycle)
5. **Starting OD: 0.01** ✅ (High confidence - explicitly stated)
6. **Wavelength: OD₆₀₀** ✅ (High confidence - explicitly stated)

**Confidence Level:** High for timing and basic setup. Medium for experimental details (temperature, shaking, background subtraction method).

**Next Steps:** If additional details are needed (plate reader model, temperature, shaking), these would need to be obtained from Sun-Young or experimental protocols not included in these files.

