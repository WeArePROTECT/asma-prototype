#!/usr/bin/env python3
"""
Detailed debug script for control data and merge logic.
"""

import pandas as pd
import math
from etl.loaders import load_phenotype_excel
from etl.config import (
    PA_REPORTER_IDS, 
    REQUIRED_GAIN, 
    RATIO_100X_REL_TOL, 
    RATIO_100X_ABS_TOL, 
    CONTROL_EXCLUSIONS
)

print("=" * 80)
print("1. INSPECT REPORTER-ONLY, GAIN=150 CONTROLS")
print("=" * 80)

# Load control data
phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
df_control = phenotype_sheets['inhibition_standard_control']

print("\nControl columns:", df_control.columns.tolist())
print("\ndf_control.head(10):")
print(df_control.head(10).to_string())

print("\ngain value_counts:")
print(df_control["gain"].value_counts(dropna=False))

print("\ntype value_counts:")
print(df_control["type"].value_counts(dropna=False))

print("\nstarting_OD dtype:", df_control["starting_OD"].dtype)
print("\nstarting_OD value_counts (sorted):")
print(df_control["starting_OD"].value_counts(dropna=False).sort_index())

# Filter to reporter-only, gain=150
df_control_rep_150 = df_control[
    (df_control["type"] == "reporter") &
    (df_control["gain"] == REQUIRED_GAIN)
].copy()

print(f"\nReporter-only, gain=150 rows: {len(df_control_rep_150)}")
print("\nReporter-only, gain=150 starting_OD value_counts (sorted):")
print(df_control_rep_150["starting_OD"].value_counts(dropna=False).sort_index())
print("\ndf_control_rep_150.head(10):")
print(df_control_rep_150.head(10).to_string())

print("\n" + "=" * 80)
print("2. INSPECT CONTROL_EXCLUSIONS USAGE")
print("=" * 80)

print(f"\nCONTROL_EXCLUSIONS from config: {CONTROL_EXCLUSIONS}")

# Show the exact exclusion logic from etl/inhibition.py (lines 30-35)
print("\nExclusion logic from etl/inhibition.py (lines 30-35):")
print("  for exclusion in CONTROL_EXCLUSIONS:")
print("      for key, value in exclusion.items():")
print("          if key in df_filtered.columns:")
print("              if isinstance(value, str):")
print("                  df_filtered = df_filtered[df_filtered[key] != value]")
print("              else:")
print("                  df_filtered = df_filtered[df_filtered[key] != value]")

# Without exclusions
df_control_rep_150_no_excl = df_control[
    (df_control["type"] == "reporter") &
    (df_control["gain"] == REQUIRED_GAIN)
].copy()

print(f"\nReporter-only, gain=150 (NO exclusions): {len(df_control_rep_150_no_excl)} rows")
print("starting_OD value_counts (no exclusions):")
print(df_control_rep_150_no_excl["starting_OD"].value_counts(dropna=False).sort_index())

# With exclusions - apply exact logic from etl/inhibition.py
df_control_rep_150_with_excl = df_control[
    (df_control["type"] == "reporter") &
    (df_control["gain"] == REQUIRED_GAIN)
].copy()

print(f"\nApplying CONTROL_EXCLUSIONS...")
initial_count = len(df_control_rep_150_with_excl)
for exclusion in CONTROL_EXCLUSIONS:
    for key, value in exclusion.items():
        if key in df_control_rep_150_with_excl.columns:
            before = len(df_control_rep_150_with_excl)
            if isinstance(value, str):
                df_control_rep_150_with_excl = df_control_rep_150_with_excl[
                    df_control_rep_150_with_excl[key] != value
                ]
            else:
                df_control_rep_150_with_excl = df_control_rep_150_with_excl[
                    df_control_rep_150_with_excl[key] != value
                ]
            after = len(df_control_rep_150_with_excl)
            if before != after:
                print(f"  Excluding {key} == {value}: {before} -> {after} rows")

print(f"\nReporter-only, gain=150 (WITH exclusions): {len(df_control_rep_150_with_excl)} rows")
print("starting_OD value_counts (with exclusions):")
print(df_control_rep_150_with_excl["starting_OD"].value_counts(dropna=False).sort_index())

# Check specifically for starting_OD = 0.0001
has_00001_no_excl = (df_control_rep_150_no_excl["starting_OD"] == 0.0001).any()
has_00001_with_excl = (df_control_rep_150_with_excl["starting_OD"] == 0.0001).any()

print(f"\nHas starting_OD == 0.0001 (no exclusions): {has_00001_no_excl}")
print(f"Has starting_OD == 0.0001 (with exclusions): {has_00001_with_excl}")

if has_00001_no_excl:
    print("\nRows with starting_OD == 0.0001 (no exclusions):")
    print(df_control_rep_150_no_excl[df_control_rep_150_no_excl["starting_OD"] == 0.0001].head())

# Group by starting_OD (same as process_inhibition_control)
df_control_grouped = df_control_rep_150_with_excl.groupby('starting_OD', as_index=False).agg({
    'raw_RFU': 'mean'
})
df_control_grouped.columns = ['starting_OD', 'rfu_reporter_mean']

print(f"\nControl grouped by starting_OD ({len(df_control_grouped)} unique values):")
print(df_control_grouped.to_string())

print("\n" + "=" * 80)
print("3. RE-RUN THE JOIN WITH DEBUG LENS")
print("=" * 80)

# Load pairwise data
df_pairwise = phenotype_sheets['pairwise_interaction']

# Recreate df_pairwise_100x exactly as in process_pairwise_interactions
df_pairwise_150 = df_pairwise[df_pairwise["gain"] == REQUIRED_GAIN].copy()
df_pairwise_rep = df_pairwise_150[df_pairwise_150["bacterium_2_ASMA_id"].isin(PA_REPORTER_IDS)].copy()

df_pairwise_rep["ratio"] = (
    df_pairwise_rep["bacterium_1_starting_OD"] / 
    df_pairwise_rep["bacterium_2_starting_OD"]
)

df_pairwise_100x = df_pairwise_rep[
    df_pairwise_rep["ratio"].apply(
        lambda r: math.isclose(r, 100.0, rel_tol=RATIO_100X_REL_TOL, abs_tol=RATIO_100X_ABS_TOL)
    )
].copy()

print(f"\n100x rows: {len(df_pairwise_100x)}")
print("\nbacterium_2_starting_OD distribution in 100x rows:")
print(df_pairwise_100x["bacterium_2_starting_OD"].value_counts(dropna=False).sort_index())

# Apply the same merge logic as etl/inhibition.py (lines 96-101)
print("\nMerge logic from etl/inhibition.py (lines 96-101):")
print("  df_100x = df_100x.merge(")
print("      control_df,")
print("      left_on='bacterium_2_starting_OD',")
print("      right_on='starting_OD',")
print("      how='left'")
print("  )")

df_merged_dbg = df_pairwise_100x.merge(
    df_control_grouped,
    left_on='bacterium_2_starting_OD',
    right_on='starting_OD',
    how='left'
)

print(f"\nRows after join: {len(df_merged_dbg)}")

# Find control RFU columns
control_rfu_cols = [col for col in df_merged_dbg.columns if "rfu" in col.lower() or "control" in col.lower() or "reporter" in col.lower()]
print(f"\nControl RFU columns: {control_rfu_cols}")

for col in control_rfu_cols:
    non_null = df_merged_dbg[col].notna().sum()
    print(f"  {col} non-null count: {non_null} / {len(df_merged_dbg)}")

print(f"\nRows with matching control (rfu_reporter_mean not null): {df_merged_dbg['rfu_reporter_mean'].notna().sum()}")
print(f"Rows with null control: {df_merged_dbg['rfu_reporter_mean'].isna().sum()}")

print("\ndf_merged_dbg.head(10):")
print(df_merged_dbg[[
    "bacterium_1_ASMA_id",
    "bacterium_2_starting_OD",
    "starting_OD",
    "raw_RFU",
    "rfu_reporter_mean"
]].head(10).to_string())

# Show rows that didn't match
no_match = df_merged_dbg[df_merged_dbg['rfu_reporter_mean'].isna()]
if len(no_match) > 0:
    print(f"\nSample rows with NO matching control (first 5):")
    print(no_match[[
        "bacterium_1_ASMA_id",
        "bacterium_2_starting_OD",
        "raw_RFU"
    ]].head(5).to_string())

# Show matching ODs
pairwise_ods = set(df_pairwise_100x['bacterium_2_starting_OD'].dropna().unique())
control_ods = set(df_control_grouped['starting_OD'].dropna().unique())

print(f"\nUnique bacterium_2_starting_OD in 100x pairwise: {sorted(pairwise_ods)}")
print(f"Unique starting_OD in control (grouped): {sorted(control_ods)}")
print(f"Matching ODs: {sorted(pairwise_ods & control_ods)}")
print(f"Missing from control: {sorted(pairwise_ods - control_ods)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Control rows (reporter, gain=150, no exclusions): {len(df_control_rep_150_no_excl)}")
print(f"Control rows (reporter, gain=150, with exclusions): {len(df_control_rep_150_with_excl)}")
print(f"Has starting_OD == 0.0001 (no exclusions): {has_00001_no_excl}")
print(f"Has starting_OD == 0.0001 (with exclusions): {has_00001_with_excl}")
print(f"100x pairwise rows: {len(df_pairwise_100x)}")
print(f"100x rows with matching control: {df_merged_dbg['rfu_reporter_mean'].notna().sum()}")

