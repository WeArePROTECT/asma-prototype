#!/usr/bin/env python3
"""
Incremental debug script - writes output to file to avoid timeouts.
"""

import pandas as pd
import math
import sys
from etl.loaders import load_phenotype_excel
from etl.config import (
    PA_REPORTER_IDS, 
    REQUIRED_GAIN, 
    RATIO_100X_REL_TOL, 
    RATIO_100X_ABS_TOL, 
    CONTROL_EXCLUSIONS
)

output_file = "debug_control_results.txt"

def print_and_log(msg, file_handle):
    """Print to console and write to file."""
    print(msg)
    file_handle.write(msg + "\n")
    file_handle.flush()

with open(output_file, 'w') as f:
    print_and_log("=" * 80, f)
    print_and_log("1. INSPECT REPORTER-ONLY, GAIN=150 CONTROLS", f)
    print_and_log("=" * 80, f)
    
    print("Loading data...")
    phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
    df_control = phenotype_sheets['inhibition_standard_control']
    
    print_and_log(f"\nControl shape: {df_control.shape}", f)
    print_and_log(f"Control columns: {df_control.columns.tolist()}", f)
    
    print_and_log("\ngain value_counts:", f)
    print_and_log(str(df_control["gain"].value_counts(dropna=False)), f)
    
    print_and_log("\ntype value_counts:", f)
    print_and_log(str(df_control["type"].value_counts(dropna=False)), f)
    
    print_and_log(f"\nstarting_OD dtype: {df_control['starting_OD'].dtype}", f)
    print_and_log("\nstarting_OD value_counts (sorted, top 20):", f)
    print_and_log(str(df_control["starting_OD"].value_counts(dropna=False).sort_index().head(20)), f)
    
    # Filter to reporter-only, gain=150
    df_control_rep_150 = df_control[
        (df_control["type"] == "reporter") &
        (df_control["gain"] == REQUIRED_GAIN)
    ].copy()
    
    print_and_log(f"\nReporter-only, gain=150 rows: {len(df_control_rep_150)}", f)
    print_and_log("\nReporter-only, gain=150 starting_OD value_counts (sorted):", f)
    print_and_log(str(df_control_rep_150["starting_OD"].value_counts(dropna=False).sort_index()), f)
    
    print_and_log("\n" + "=" * 80, f)
    print_and_log("2. INSPECT CONTROL_EXCLUSIONS", f)
    print_and_log("=" * 80, f)
    
    print_and_log(f"\nCONTROL_EXCLUSIONS: {CONTROL_EXCLUSIONS}", f)
    
    # Without exclusions
    df_control_rep_150_no_excl = df_control[
        (df_control["type"] == "reporter") &
        (df_control["gain"] == REQUIRED_GAIN)
    ].copy()
    
    print_and_log(f"\nReporter-only, gain=150 (NO exclusions): {len(df_control_rep_150_no_excl)} rows", f)
    print_and_log("starting_OD value_counts (no exclusions):", f)
    print_and_log(str(df_control_rep_150_no_excl["starting_OD"].value_counts(dropna=False).sort_index()), f)
    
    # With exclusions
    df_control_rep_150_with_excl = df_control[
        (df_control["type"] == "reporter") &
        (df_control["gain"] == REQUIRED_GAIN)
    ].copy()
    
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
                    print_and_log(f"  Excluded {key} == {value}: {before} -> {after} rows", f)
    
    print_and_log(f"\nReporter-only, gain=150 (WITH exclusions): {len(df_control_rep_150_with_excl)} rows", f)
    print_and_log("starting_OD value_counts (with exclusions):", f)
    print_and_log(str(df_control_rep_150_with_excl["starting_OD"].value_counts(dropna=False).sort_index()), f)
    
    has_00001_no_excl = (df_control_rep_150_no_excl["starting_OD"] == 0.0001).any()
    has_00001_with_excl = (df_control_rep_150_with_excl["starting_OD"] == 0.0001).any()
    
    print_and_log(f"\nHas starting_OD == 0.0001 (no exclusions): {has_00001_no_excl}", f)
    print_and_log(f"Has starting_OD == 0.0001 (with exclusions): {has_00001_with_excl}", f)
    
    # Group by starting_OD
    df_control_grouped = df_control_rep_150_with_excl.groupby('starting_OD', as_index=False).agg({
        'raw_RFU': 'mean'
    })
    df_control_grouped.columns = ['starting_OD', 'rfu_reporter_mean']
    
    print_and_log(f"\nControl grouped by starting_OD ({len(df_control_grouped)} unique values):", f)
    print_and_log(str(df_control_grouped), f)
    
    print_and_log("\n" + "=" * 80, f)
    print_and_log("3. RE-RUN THE JOIN", f)
    print_and_log("=" * 80, f)
    
    df_pairwise = phenotype_sheets['pairwise_interaction']
    
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
    
    print_and_log(f"\n100x rows: {len(df_pairwise_100x)}", f)
    print_and_log("\nbacterium_2_starting_OD distribution in 100x rows:", f)
    print_and_log(str(df_pairwise_100x["bacterium_2_starting_OD"].value_counts(dropna=False).sort_index()), f)
    
    df_merged_dbg = df_pairwise_100x.merge(
        df_control_grouped,
        left_on='bacterium_2_starting_OD',
        right_on='starting_OD',
        how='left'
    )
    
    print_and_log(f"\nRows after join: {len(df_merged_dbg)}", f)
    print_and_log(f"Rows with matching control (rfu_reporter_mean not null): {df_merged_dbg['rfu_reporter_mean'].notna().sum()}", f)
    print_and_log(f"Rows with null control: {df_merged_dbg['rfu_reporter_mean'].isna().sum()}", f)
    
    pairwise_ods = set(df_pairwise_100x['bacterium_2_starting_OD'].dropna().unique())
    control_ods = set(df_control_grouped['starting_OD'].dropna().unique())
    
    print_and_log(f"\nUnique bacterium_2_starting_OD in 100x pairwise: {sorted(pairwise_ods)}", f)
    print_and_log(f"Unique starting_OD in control (grouped): {sorted(control_ods)}", f)
    print_and_log(f"Matching ODs: {sorted(pairwise_ods & control_ods)}", f)
    print_and_log(f"Missing from control: {sorted(pairwise_ods - control_ods)}", f)
    
    print_and_log("\n" + "=" * 80, f)
    print_and_log("SUMMARY", f)
    print_and_log("=" * 80, f)
    print_and_log(f"Control rows (reporter, gain=150, no exclusions): {len(df_control_rep_150_no_excl)}", f)
    print_and_log(f"Control rows (reporter, gain=150, with exclusions): {len(df_control_rep_150_with_excl)}", f)
    print_and_log(f"Has starting_OD == 0.0001 (no exclusions): {has_00001_no_excl}", f)
    print_and_log(f"Has starting_OD == 0.0001 (with exclusions): {has_00001_with_excl}", f)
    print_and_log(f"100x pairwise rows: {len(df_pairwise_100x)}", f)
    print_and_log(f"100x rows with matching control: {df_merged_dbg['rfu_reporter_mean'].notna().sum()}", f)

print(f"\nDebug complete! Results written to {output_file}")

