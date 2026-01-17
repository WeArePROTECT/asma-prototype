#!/usr/bin/env python3
"""
Debug script to check control data processing for PA inhibition.
"""

import pandas as pd
from etl.loaders import load_phenotype_excel
from etl.inhibition import process_inhibition_control, process_pairwise_interactions
from etl.config import CONTROL_EXCLUSIONS, REQUIRED_GAIN

# Load data
phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
df_control = phenotype_sheets['inhibition_standard_control']
df_pairwise = phenotype_sheets['pairwise_interaction']

print("=" * 80)
print("CONTROL DATA DEBUG")
print("=" * 80)

print("\nControl data columns:")
print(df_control.columns.tolist())

print("\nControl data head:")
print(df_control.head(10).to_string())

print("\nControl data - type value counts:")
print(df_control["type"].value_counts(dropna=False))

print("\nControl data - gain value counts:")
print(df_control["gain"].value_counts(dropna=False))

print("\nControl data - starting_OD value counts:")
print(df_control["starting_OD"].value_counts().head(20))

print("\nControl data - assay_start_date value counts:")
print(df_control["assay_start_date"].value_counts().head(20))

# Process control data
print("\n" + "=" * 80)
print("PROCESSING CONTROL DATA")
print("=" * 80)

control_processed = process_inhibition_control(df_control)
print(f"\nProcessed control data rows: {len(control_processed)}")
print("\nProcessed control data:")
print(control_processed.to_string())

# Check pairwise data that passes filters
print("\n" + "=" * 80)
print("PAIRWISE DATA AFTER FILTERS")
print("=" * 80)

pairwise_processed = process_pairwise_interactions(df_pairwise, control_processed)
print(f"\nProcessed pairwise data rows: {len(pairwise_processed)}")

if len(pairwise_processed) > 0:
    print("\nProcessed pairwise data head:")
    print(pairwise_processed.head(10).to_string())
    
    print("\nUnique pa_starting_od values in pairwise data:")
    print(pairwise_processed["pa_starting_od"].value_counts())
    
    print("\nUnique starting_OD values in control data:")
    print(control_processed["starting_OD"].value_counts())
    
    # Check for matching starting_OD values
    pairwise_ods = set(pairwise_processed["pa_starting_od"].dropna().unique())
    control_ods = set(control_processed["starting_OD"].unique())
    
    print(f"\nPairwise starting_OD values: {sorted(pairwise_ods)}")
    print(f"Control starting_OD values: {sorted(control_ods)}")
    print(f"Matching ODs: {sorted(pairwise_ods & control_ods)}")
    print(f"Missing from control: {sorted(pairwise_ods - control_ods)}")
else:
    print("\nNo rows in processed pairwise data!")
    print("\nChecking why merge failed...")
    
    # Manually check the merge
    from etl.inhibition import process_pairwise_interactions
    import math
    from etl.config import PA_REPORTER_IDS, RATIO_100X_REL_TOL, RATIO_100X_ABS_TOL
    
    # Apply filters manually
    df_gain = df_pairwise[df_pairwise["gain"] == REQUIRED_GAIN].copy()
    df_reporter = df_gain[df_gain["bacterium_2_ASMA_id"].isin(PA_REPORTER_IDS)].copy()
    df_reporter["ratio"] = df_reporter["bacterium_1_starting_OD"] / df_reporter["bacterium_2_starting_OD"]
    df_100x = df_reporter[
        df_reporter["ratio"].apply(
            lambda r: math.isclose(r, 100.0, rel_tol=RATIO_100X_REL_TOL, abs_tol=RATIO_100X_ABS_TOL)
        )
    ].copy()
    
    print(f"\nRows after 100:1 filter: {len(df_100x)}")
    print(f"Unique bacterium_2_starting_OD values: {sorted(df_100x['bacterium_2_starting_OD'].unique())}")
    print(f"Control starting_OD values: {sorted(control_processed['starting_OD'].unique())}")

