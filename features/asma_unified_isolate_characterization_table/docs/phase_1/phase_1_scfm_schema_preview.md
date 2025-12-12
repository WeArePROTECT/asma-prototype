# Phase 1 SCFM Growth Metrics - Schema Preview

**Date:** 12/11/2025  
**Feature:** ASMA Unified Isolate Characterization Table (UICT)  
**Phase:** Phase 1 - SCFM Growth Metrics  
**Status:** Complete

---

## Phase 1 SCFM Column Schema

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `scfm_od_24h_mean` | float | Mean OD at 24 hours across replicates |
| `scfm_od_24h_sd` | float | Standard deviation of OD at 24 hours across replicates |
| `scfm_od_48h_mean` | float | Mean OD at 48 hours across replicates |
| `scfm_od_48h_sd` | float | Standard deviation of OD at 48 hours across replicates |
| `scfm_delta_od_24h_mean` | float | Mean change in OD from baseline to 24 hours across replicates |
| `scfm_delta_od_24h_sd` | float | Standard deviation of ΔOD at 24 hours across replicates |
| `scfm_delta_od_48h_mean` | float | Mean change in OD from baseline to 48 hours across replicates |
| `scfm_delta_od_48h_sd` | float | Standard deviation of ΔOD at 48 hours across replicates |
| `scfm_growth_24h_n` | integer | Count of replicates with growth at 24 hours (ΔOD ≥ 0.1) |
| `scfm_growth_24h_pct` | float | Percentage of replicates with growth at 24 hours (0-100) |
| `scfm_growth_48h_n` | integer | Count of replicates with growth at 48 hours (ΔOD ≥ 0.1) |
| `scfm_growth_48h_pct` | float | Percentage of replicates with growth at 48 hours (0-100) |
| `scfm_od_max_yield_mean` | float | Mean maximum OD across entire growth curve across replicates |
| `scfm_od_max_yield_sd` | float | Standard deviation of maximum OD across replicates |
| `scfm_time_max_yield_mean` | float | Mean time (hours) when maximum yield occurs across replicates |
| `scfm_time_max_yield_sd` | float | Standard deviation of time to maximum yield across replicates |
| `scfm_mu_simple_mean` | float | Mean provisional growth rate (μ) estimate across replicates (h⁻¹) |
| `scfm_mu_simple_sd` | float | Standard deviation of μ estimates across replicates (h⁻¹) |
| `scfm_mu_simple_n_reps` | integer | Count of replicates with valid μ estimates |
| `scfm_mu_simple_r2_mean` | float | Mean R² of μ regression fits across replicates |
| `scfm_mu_simple_r2_sd` | float | Standard deviation of R² values across replicates |

**Note:** All Phase 1 columns are nullable (NaN for isolates without SCFM data).

---

## Example Isolates Preview

| ASMA_id | od_24h_mean | od_48h_mean | delta_od_24h_mean | delta_od_48h_mean | growth_24h_pct | growth_48h_pct | od_max_yield_mean | time_max_yield_mean | mu_simple_mean | mu_simple_r2_mean |
|---------|-------------|-------------|-------------------|-------------------|----------------|----------------|-------------------|---------------------|----------------|-------------------|
| ASMA-1046 | 0.0952 | 0.0948 | 0.0002 | -0.0002 | 0.0 | 0.0 | 0.0958 | 1.50 | 0.002251 | 0.9872 |
| ASMA-1058 | 0.1317 | 0.1599 | 0.0265 | 0.0547 | 0.0 | 0.0 | 0.1889 | 40.25 | 0.062330 | 0.9904 |
| ASMA-1060 | 0.0945 | 0.0938 | -0.0013 | -0.0020 | 0.0 | 0.0 | 0.0958 | 0.00 | 0.004923 | 0.9642 |
| ASMA-1061 | 0.1259 | 0.1207 | 0.0167 | 0.0114 | 0.0 | 0.0 | 0.1362 | 7.00 | 0.030386 | 0.9800 |
| ASMA-1062 | 0.0947 | 0.0950 | -0.0015 | -0.0012 | 0.0 | 0.0 | 0.0962 | 0.00 | NaN | NaN |
| ASMA-1064 | 0.2766 | 0.2678 | 0.1567 | 0.1479 | 75.0 | 75.0 | 0.2996 | 20.38 | 0.181843 | 0.9947 |
| ASMA-1070 | 0.1248 | 0.1304 | 0.0298 | 0.0354 | 0.0 | 0.0 | 0.1310 | 44.00 | 0.020406 | 0.9976 |
| ASMA-1071 | 0.0928 | 0.0916 | -0.0015 | -0.0027 | 0.0 | 0.0 | 0.0948 | 0.75 | NaN | NaN |

### Examples: Strong Growth + Strong Inhibition

| ASMA_id | growth_24h_pct | inhib_100x_mean | mu_simple_mean | delta_od_24h_mean |
|---------|----------------|-----------------|----------------|-------------------|
| ASMA-1664 | 100.0 | 71.65 | 0.038577 | 0.1074 |
| ASMA-3066 | 100.0 | 79.37 | 0.017528 | 0.1606 |
| ASMA-687 | 100.0 | 80.16 | 0.160885 | 0.2077 |

### Examples: Weak/No Growth

| ASMA_id | growth_24h_pct | delta_od_24h_mean | mu_simple_mean |
|---------|----------------|-------------------|----------------|
| ASMA-1046 | 0.0 | 0.0002 | 0.002251 |
| ASMA-1058 | 0.0 | 0.0265 | 0.062330 |
| ASMA-1060 | 0.0 | -0.0013 | 0.004923 |

---

## Sanity Check Statistics

### Data Coverage

- **Total isolates in UICT:** 3,890
- **Isolates with SCFM data:** 448 (11.5%)
- **Isolates with valid μ (mu_simple) estimates:** 318 (8.2% of total, 71.0% of SCFM isolates)

### μ (mu_simple) Distribution Summary

For the 318 isolates with valid μ estimates:

- **Minimum:** 0.001596 h⁻¹
- **25th percentile:** 0.017372 h⁻¹
- **Median:** 0.033286 h⁻¹
- **75th percentile:** 0.069600 h⁻¹
- **Maximum:** 0.427847 h⁻¹
- **Mean:** 0.051019 h⁻¹

**Interpretation:** The μ distribution shows a wide range of growth rates, with most isolates (50%) having growth rates between 0.017 and 0.070 h⁻¹. The median growth rate of 0.033 h⁻¹ corresponds to a doubling time of approximately 21 hours (ln(2) / μ).

### Example Isolates

**Strong Growth + Strong Inhibition:**
- **ASMA-1664:** 100% growth at 24h, 71.65% inhibition, μ = 0.039 h⁻¹
- **ASMA-3066:** 100% growth at 24h, 79.37% inhibition, μ = 0.018 h⁻¹
- **ASMA-687:** 100% growth at 24h, 80.16% inhibition, μ = 0.161 h⁻¹ (very fast growth)

**Weak/No Growth:**
- **ASMA-1046:** 0% growth at 24h, ΔOD = 0.0002 (essentially no growth)
- **ASMA-1058:** 0% growth at 24h, ΔOD = 0.0265 (below threshold), but μ = 0.062 h⁻¹ (some growth detected in exponential phase)
- **ASMA-1060:** 0% growth at 24h, negative ΔOD = -0.0013 (declining), μ = 0.005 h⁻¹ (minimal growth)

---

**END OF PREVIEW**

