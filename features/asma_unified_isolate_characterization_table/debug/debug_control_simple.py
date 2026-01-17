#!/usr/bin/env python3
"""
Simplified debug script to inspect control data and merge.
"""

import pandas as pd
import math
from etl.loaders import load_phenotype_excel
from etl.config import PA_REPORTER_IDS, REQUIRED_GAIN, RATIO_100X_REL_TOL, RATIO_100X_ABS_TOL, CONTROL_EXCLUSIONS

print("Loading data...")
phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
df_control = phenotype_sheets['inhibition_standard_control']
df_pairwise = phenotype_sheets['pairwise_interaction']

print("\n" + "="*80)
print("1. CONTROL DATA INSPECTION")
print("="*80)

print(f"\ndf_control.columns: {df_control.columns.tolist()}")
print(f"\ndf_control.shape: {df_control.shape}")
print(f"\ndf_control.head(5):")
print(df_control.head(5)[['sample_id', 'ASMA_id', 'type', 'assay_start_date', 'starting_OD', 'gain', 'raw_RFU']])

print(f"\ngain value_counts:")
print(df_control["gain"].value_counts(dropna=False))

print(f"\ntype value_counts:")
print(df_control["type"].value_counts(dropna=False))

print(f"\nstarting_OD dtype: {df_control['starting_OD'].dtype}")
print(f"starting_OD value_counts (sorted, top 10):")
print(df_control["starting_OD"].value_counts(dropna=False).sort_index().head(10))

# Reporter-only, gain 150
df_control_rep_150 = df_control[
    (df_control["type"] == "reporter") &
    (df_control["gain"] == REQUIRED_GAIN)
].copy()

print(f"\nReporter-only, gain=150 rows: {len(df_control_rep_150)}")
print(f"\nReporter-only, gain=150 starting_OD value_counts (sorted):")
print(df_control_rep_150["starting_OD"].value_counts(dropna=False).sort_index())

# Apply exclusions
df_control_filtered = df_control_rep_150.copy()
for exclusion in CONTROL_EXCLUSIONS:
    for key, value in exclusion.items():
        if key in df_control_filtered.columns:
            before = len(df_control_filtered)
            if isinstance(value, str):
                df_control_filtered = df_control_filtered[df_control_filtered[key] != value]
            else:
                df_control_filtered = df_control_filtered[df_control_filtered[key] != value]
            after = len(df_control_filtered)
            if before != after:
                print(f"\nExcluded {key} == {value}: {before} -> {after} rows")

# Group by starting_OD
df_control_grouped = df_control_filtered.groupby('starting_OD', as_index=False).agg({
    'raw_RFU': 'mean'
})
df_control_grouped.columns = ['starting_OD', 'rfu_reporter_mean']

print(f"\nControl grouped by starting_OD ({len(df_control_grouped)} unique values):")
print(df_control_grouped)

print("\n" + "="*80)
print("2. PAIRWISE 100X DATA")
print("="*80)

# Filter pairwise to 100x
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

print(f"\n100x rows: {len(df_pairwise_100x)}")
print(f"\nbacterium_2_starting_OD dtype: {df_pairwise_100x['bacterium_2_starting_OD'].dtype}")
print(f"bacterium_2_starting_OD value_counts (sorted):")
print(df_pairwise_100x["bacterium_2_starting_OD"].value_counts(dropna=False).sort_index())

print("\n" + "="*80)
print("3. MERGE ANALYSIS")
print("="*80)

print("\nJoin logic from etl/inhibition.py:")
print("  left_on='bacterium_2_starting_OD' (from pairwise)")
print("  right_on='starting_OD' (from control)")
print("  how='left'")

# Perform merge
df_merged = df_pairwise_100x.merge(
    df_control_grouped,
    left_on='bacterium_2_starting_OD',
    right_on='starting_OD',
    how='left'
)

print(f"\n100x rows before merge: {len(df_pairwise_100x)}")
print(f"100x rows after merge: {len(df_merged)}")
print(f"Rows with matching controls (rfu_reporter_mean not null): {df_merged['rfu_reporter_mean'].notna().sum()}")
print(f"Rows with null controls: {df_merged['rfu_reporter_mean'].isna().sum()}")

# Check matching ODs
pairwise_ods = set(df_pairwise_100x['bacterium_2_starting_OD'].dropna().unique())
control_ods = set(df_control_grouped['starting_OD'].dropna().unique())

print(f"\nUnique bacterium_2_starting_OD in 100x pairwise: {sorted(pairwise_ods)}")
print(f"Unique starting_OD in control (grouped): {sorted(control_ods)}")
print(f"Matching ODs: {sorted(pairwise_ods & control_ods)}")
print(f"Missing from control: {sorted(pairwise_ods - control_ods)}")

if len(pairwise_ods - control_ods) > 0:
    print(f"\nSample rows with no matching control (first 3):")
    no_match = df_merged[df_merged['rfu_reporter_mean'].isna()]
    print(no_match[['bacterium_1_ASMA_id', 'bacterium_2_starting_OD', 'raw_RFU']].head(3))

if len(pairwise_ods & control_ods) > 0:
    print(f"\nSample rows with matching control (first 3):")
    match = df_merged[df_merged['rfu_reporter_mean'].notna()]
    print(match[['bacterium_1_ASMA_id', 'bacterium_2_starting_OD', 'raw_RFU', 'rfu_reporter_mean']].head(3))

