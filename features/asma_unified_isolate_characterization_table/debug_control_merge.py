#!/usr/bin/env python3
"""
Debug script to inspect control data processing and merge with pairwise data.
"""

import pandas as pd
import math
from etl.loaders import load_phenotype_excel
from etl.config import PA_REPORTER_IDS, REQUIRED_GAIN, RATIO_100X_REL_TOL, RATIO_100X_ABS_TOL, CONTROL_EXCLUSIONS

# Load data
print("=" * 80)
print("1. INSPECT inhibition_standard_control SHEET")
print("=" * 80)

phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
df_control = phenotype_sheets['inhibition_standard_control']

print("\ndf_control.columns:")
print(df_control.columns.tolist())

print("\ndf_control.head(10):")
print(df_control.head(10).to_string())

print("\ngain value_counts:")
print(df_control["gain"].value_counts(dropna=False))

print("\ntype value_counts:")
print(df_control["type"].value_counts(dropna=False))

print("\nstarting_OD dtype and example values:")
print(f"dtype: {df_control['starting_OD'].dtype}")
print("\nstarting_OD value_counts (sorted):")
print(df_control["starting_OD"].value_counts(dropna=False).sort_index())

# Check for reporter-only, gain 150 rows
print("\n" + "=" * 80)
print("Reporter-only, gain=150 rows")
print("=" * 80)

df_control_rep_150 = df_control[
    (df_control["type"] == "reporter") &
    (df_control["gain"] == REQUIRED_GAIN)
].copy()

print(f"\nReporter-only, gain=150 rows: {len(df_control_rep_150)}")
print("\ndf_control_rep_150.head(10):")
print(df_control_rep_150.head(10).to_string())

print("\nReporter-only, gain=150 starting_OD value_counts (sorted):")
print(df_control_rep_150["starting_OD"].value_counts(dropna=False).sort_index())

# Apply exclusions (same as in process_inhibition_control)
print("\n" + "=" * 80)
print("Applying CONTROL_EXCLUSIONS")
print("=" * 80)
print(f"CONTROL_EXCLUSIONS: {CONTROL_EXCLUSIONS}")

df_control_filtered = df_control_rep_150.copy()
initial_count = len(df_control_filtered)

for exclusion in CONTROL_EXCLUSIONS:
    for key, value in exclusion.items():
        if key in df_control_filtered.columns:
            before = len(df_control_filtered)
            if isinstance(value, str):
                df_control_filtered = df_control_filtered[df_control_filtered[key] != value]
            else:
                df_control_filtered = df_control_filtered[df_control_filtered[key] != value]
            after = len(df_control_filtered)
            print(f"  Excluding {key} == {value}: {before} -> {after} rows")

print(f"\nAfter exclusions: {len(df_control_filtered)} rows")

# Group by starting_OD (same as process_inhibition_control)
df_control_grouped = df_control_filtered.groupby('starting_OD', as_index=False).agg({
    'raw_RFU': 'mean'
})
df_control_grouped.columns = ['starting_OD', 'rfu_reporter_mean']

print("\nControl data grouped by starting_OD:")
print(df_control_grouped.to_string())

# 2. Recreate the merge between controls and 100x pairwise
print("\n" + "=" * 80)
print("2. RECREATE MERGE BETWEEN CONTROLS AND 100X PAIRWISE")
print("=" * 80)

df_pairwise = phenotype_sheets['pairwise_interaction']

# Apply filters exactly as in process_pairwise_interactions
df_pairwise_150 = df_pairwise[df_pairwise["gain"] == REQUIRED_GAIN].copy()
df_pairwise_rep = df_pairwise_150[df_pairwise_150["bacterium_2_ASMA_id"].isin(PA_REPORTER_IDS)].copy()

df_pairwise_100x = df_pairwise_rep[
    df_pairwise_rep.apply(
        lambda row: math.isclose(
            row["bacterium_1_starting_OD"] / row["bacterium_2_starting_OD"],
            100.0,
            rel_tol=RATIO_100X_REL_TOL,
            abs_tol=RATIO_100X_ABS_TOL,
        ) if pd.notna(row["bacterium_1_starting_OD"]) and pd.notna(row["bacterium_2_starting_OD"]) and row["bacterium_2_starting_OD"] != 0 else False,
        axis=1,
    )
].copy()

print(f"\n100x rows (debug reproduction): {len(df_pairwise_100x)}")
print("\ndf_pairwise_100x head (key columns):")
print(df_pairwise_100x[[
    "sample_id",
    "bacterium_1_ASMA_id",
    "bacterium_2_ASMA_id",
    "bacterium_1_starting_OD",
    "bacterium_2_starting_OD",
    "raw_RFU"
]].head(10).to_string())

print("\nbacterium_2_starting_OD dtype:", df_pairwise_100x["bacterium_2_starting_OD"].dtype)
print("\nbacterium_2_starting_OD value_counts (sorted):")
print(df_pairwise_100x["bacterium_2_starting_OD"].value_counts(dropna=False).sort_index())

# Show the exact join logic from etl/inhibition.py
print("\n" + "=" * 80)
print("EXACT JOIN LOGIC FROM etl/inhibition.py")
print("=" * 80)

# From process_pairwise_interactions:
# df_100x = df_100x.merge(
#     control_df,
#     left_on='bacterium_2_starting_OD',
#     right_on='starting_OD',
#     how='left'
# )

print("\nJoin logic:")
print("  left_on='bacterium_2_starting_OD' (from pairwise)")
print("  right_on='starting_OD' (from control)")
print("  how='left'")

# Recreate the merge
df_pairwise_100x_for_merge = df_pairwise_100x.copy()
df_merged_dbg = df_pairwise_100x_for_merge.merge(
    df_control_grouped,
    left_on='bacterium_2_starting_OD',
    right_on='starting_OD',
    how='left'
)

print(f"\n100x rows before merge: {len(df_pairwise_100x_for_merge)}")
print(f"100x rows after merge: {len(df_merged_dbg)}")
print(f"100x rows with matching controls (rfu_reporter_mean not null): {df_merged_dbg['rfu_reporter_mean'].notna().sum()}")
print(f"100x rows with null controls: {df_merged_dbg['rfu_reporter_mean'].isna().sum()}")

print("\nMerged data head (showing key columns):")
print(df_merged_dbg[[
    "bacterium_1_ASMA_id",
    "bacterium_2_starting_OD",
    "starting_OD",
    "raw_RFU",
    "rfu_reporter_mean"
]].head(10).to_string())

# Check for dtype mismatches
print("\n" + "=" * 80)
print("DTYPE COMPARISON")
print("=" * 80)
print(f"pairwise bacterium_2_starting_OD dtype: {df_pairwise_100x_for_merge['bacterium_2_starting_OD'].dtype}")
print(f"control starting_OD dtype: {df_control_grouped['starting_OD'].dtype}")

# Show unique values for comparison
print("\nUnique bacterium_2_starting_OD values in 100x pairwise:")
pairwise_ods = sorted(df_pairwise_100x_for_merge['bacterium_2_starting_OD'].dropna().unique())
print(pairwise_ods)

print("\nUnique starting_OD values in control (grouped):")
control_ods = sorted(df_control_grouped['starting_OD'].dropna().unique())
print(control_ods)

print("\nMatching ODs (intersection):")
matching = sorted(set(pairwise_ods) & set(control_ods))
print(matching)

print("\nMissing from control (in pairwise but not in control):")
missing = sorted(set(pairwise_ods) - set(control_ods))
print(missing)

print("\nExtra in control (in control but not in pairwise):")
extra = sorted(set(control_ods) - set(pairwise_ods))
print(extra)

# Show sample rows that don't match
if len(missing) > 0:
    print("\n" + "=" * 80)
    print("SAMPLE ROWS WITH NO MATCHING CONTROL")
    print("=" * 80)
    no_match = df_merged_dbg[df_merged_dbg['rfu_reporter_mean'].isna()]
    print(f"Rows with no match: {len(no_match)}")
    print("\nSample rows (first 5):")
    print(no_match[[
        "bacterium_1_ASMA_id",
        "bacterium_2_starting_OD",
        "raw_RFU"
    ]].head(5).to_string())

