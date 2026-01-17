"""
Configuration constants for UICT v1 ETL pipeline.
"""

# PA Reporter IDs - configurable list of ASMA_ids that identify PA reporter strains
PA_REPORTER_IDS = [
    "PA14_KEH108_Reporter",
    "PA14_KEH108",
    "PA14_KEH108_reporter"
]

# Control data exclusions - known bad cases to exclude from reporter control calculations
# Format: list of dicts with keys matching column names
CONTROL_EXCLUSIONS = [
    {"starting_OD": 0.01, "assay_start_date": "2025-11-11"}
]

# SCFM Growth Classification Thresholds
SCFM_DELTA_OD_THRESHOLDS = {
    "no_growth": 0.05,   # delta_od < 0.05
    "poor": 0.1,         # 0.05 <= delta_od < 0.1
    "normal": 0.2,       # 0.1 <= delta_od < 0.2
    "robust": float('inf')  # delta_od >= 0.2
}

# Phase 1 SCFM Time Point Constants
SCFM_CYCLE_24H = 97  # 24-hour time point
SCFM_CYCLE_48H = 193  # 48-hour time point
SCFM_CYCLE_BASELINE = 1  # Baseline cycle, typically cycle 1

# Phase 1 SCFM Growth Threshold
SCFM_GROWTH_DELTA_OD_THRESHOLD = 0.1  # Default threshold for binary growth calls (configurable)

# Phase 1 SCFM Time Conversion
SCFM_CYCLE_INTERVAL_HOURS = 0.25  # 15 minutes = 0.25 hours per cycle

# Phase 1 SCFM μ (mu_simple) Estimation Configuration
SCFM_MU_WINDOW_MIN_CYCLES = 8  # Minimum window size for μ estimation
SCFM_MU_WINDOW_MAX_CYCLES = 12  # Maximum window size for μ estimation
SCFM_MU_MIN_OD = 0.01  # Epsilon cutoff for log(OD) - filter out OD values <= this
SCFM_MU_MIN_R2 = 0.95  # Minimum R² threshold for acceptable μ fit (configurable)

# PA Inhibition Classification Thresholds (inhibition percentage)
INHIBITION_THRESHOLDS = {
    "none": 25,          # inhib_100x_mean < 25
    "weak": 50,          # 25 <= inhib_100x_mean < 50
    "strong": float('inf')  # inhib_100x_mean >= 50
}

# 100:1 Ratio Detection Tolerance
# Used with math.isclose(ratio, 100.0, rel_tol=REL_TOL, abs_tol=ABS_TOL)
RATIO_100X_REL_TOL = 1e-3
RATIO_100X_ABS_TOL = 1e-6

# Carbon Utilization Threshold Multiplier
# utilization = "utilizes" if mean_C > mean_no_carbon + (MULTIPLIER * sd_no_carbon)
CARBON_UTILIZATION_SD_MULTIPLIER = 2.0

# Minimum replicates for carbon utilization certainty
CARBON_MIN_REPLICATES = 3

# Gain value required for PA inhibition data
REQUIRED_GAIN = 150

# Default file paths
DEFAULT_TAXONOMY_PATH = "/usr2/people/alex.styer/public_html/taxonomy.tsv"
DEFAULT_PHENOTYPE_PATH = "/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx"
DEFAULT_OUTPUT_PATH = "data/derived/asma_unified_isolate_characterization_table.csv"

