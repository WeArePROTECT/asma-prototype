#!/usr/bin/env python3
"""
Debug script with checkpoints - writes progress incrementally.
"""

import pandas as pd
import math
import time
from pathlib import Path
from etl.loaders import load_phenotype_excel
from etl.config import (
    PA_REPORTER_IDS, 
    REQUIRED_GAIN, 
    RATIO_100X_REL_TOL, 
    RATIO_100X_ABS_TOL, 
    CONTROL_EXCLUSIONS
)

CHECKPOINT_FILE = "debug_checkpoint.txt"
RESULTS_FILE = "debug_control_results.txt"

def checkpoint(msg, results_file=None):
    """Write checkpoint message."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    checkpoint_msg = f"[{timestamp}] {msg}\n"
    print(checkpoint_msg.strip())
    
    with open(CHECKPOINT_FILE, 'a') as f:
        f.write(checkpoint_msg)
    
    if results_file:
        with open(results_file, 'a') as f:
            f.write(msg + "\n")

def clear_checkpoints():
    """Clear checkpoint file."""
    Path(CHECKPOINT_FILE).unlink(missing_ok=True)
    Path(RESULTS_FILE).unlink(missing_ok=True)

# Clear old checkpoints
clear_checkpoints()

checkpoint("=" * 80)
checkpoint("DEBUG SCRIPT STARTED")
checkpoint("=" * 80)

try:
    checkpoint("CHECKPOINT 1: Loading phenotype Excel file...")
    phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
    checkpoint(f"CHECKPOINT 1 COMPLETE: Loaded {len(phenotype_sheets)} sheets")
    
    checkpoint("CHECKPOINT 2: Extracting control sheet...")
    df_control = phenotype_sheets['inhibition_standard_control']
    checkpoint(f"CHECKPOINT 2 COMPLETE: Control shape {df_control.shape}")
    
    checkpoint("CHECKPOINT 3: Analyzing control data...")
    checkpoint(f"Control columns: {df_control.columns.tolist()}", RESULTS_FILE)
    checkpoint(f"Control shape: {df_control.shape}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 4: Gain value counts...")
    gain_counts = df_control["gain"].value_counts(dropna=False)
    checkpoint(f"gain value_counts:\n{gain_counts}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 5: Type value counts...")
    type_counts = df_control["type"].value_counts(dropna=False)
    checkpoint(f"type value_counts:\n{type_counts}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 6: Starting OD analysis...")
    checkpoint(f"starting_OD dtype: {df_control['starting_OD'].dtype}", RESULTS_FILE)
    od_counts = df_control["starting_OD"].value_counts(dropna=False).sort_index()
    checkpoint(f"starting_OD value_counts (sorted, top 20):\n{od_counts.head(20)}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 7: Filtering to reporter-only, gain=150...")
    df_control_rep_150 = df_control[
        (df_control["type"] == "reporter") &
        (df_control["gain"] == REQUIRED_GAIN)
    ].copy()
    checkpoint(f"CHECKPOINT 7 COMPLETE: {len(df_control_rep_150)} rows")
    
    checkpoint("CHECKPOINT 8: Reporter-only starting OD counts...")
    rep_od_counts = df_control_rep_150["starting_OD"].value_counts(dropna=False).sort_index()
    checkpoint(f"Reporter-only, gain=150 starting_OD value_counts:\n{rep_od_counts}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 9: Checking for 0.0001...")
    has_00001 = (df_control_rep_150["starting_OD"] == 0.0001).any()
    checkpoint(f"Has starting_OD == 0.0001: {has_00001}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 10: Applying CONTROL_EXCLUSIONS...")
    checkpoint(f"CONTROL_EXCLUSIONS: {CONTROL_EXCLUSIONS}", RESULTS_FILE)
    
    df_control_rep_150_no_excl = df_control[
        (df_control["type"] == "reporter") &
        (df_control["gain"] == REQUIRED_GAIN)
    ].copy()
    
    checkpoint(f"Before exclusions: {len(df_control_rep_150_no_excl)} rows", RESULTS_FILE)
    no_excl_od_counts = df_control_rep_150_no_excl["starting_OD"].value_counts(dropna=False).sort_index()
    checkpoint(f"starting_OD value_counts (no exclusions):\n{no_excl_od_counts}", RESULTS_FILE)
    
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
                    checkpoint(f"  Excluded {key} == {value}: {before} -> {after} rows", RESULTS_FILE)
    
    checkpoint(f"After exclusions: {len(df_control_rep_150_with_excl)} rows", RESULTS_FILE)
    with_excl_od_counts = df_control_rep_150_with_excl["starting_OD"].value_counts(dropna=False).sort_index()
    checkpoint(f"starting_OD value_counts (with exclusions):\n{with_excl_od_counts}", RESULTS_FILE)
    
    has_00001_no_excl = (df_control_rep_150_no_excl["starting_OD"] == 0.0001).any()
    has_00001_with_excl = (df_control_rep_150_with_excl["starting_OD"] == 0.0001).any()
    checkpoint(f"Has starting_OD == 0.0001 (no exclusions): {has_00001_no_excl}", RESULTS_FILE)
    checkpoint(f"Has starting_OD == 0.0001 (with exclusions): {has_00001_with_excl}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 11: Grouping control by starting_OD...")
    df_control_grouped = df_control_rep_150_with_excl.groupby('starting_OD', as_index=False).agg({
        'raw_RFU': 'mean'
    })
    df_control_grouped.columns = ['starting_OD', 'rfu_reporter_mean']
    checkpoint(f"CHECKPOINT 11 COMPLETE: {len(df_control_grouped)} unique starting_OD values")
    checkpoint(f"Control grouped:\n{df_control_grouped.to_string()}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 12: Loading pairwise data...")
    df_pairwise = phenotype_sheets['pairwise_interaction']
    checkpoint(f"CHECKPOINT 12 COMPLETE: Pairwise shape {df_pairwise.shape}")
    
    checkpoint("CHECKPOINT 13: Filtering pairwise to gain=150...")
    df_pairwise_150 = df_pairwise[df_pairwise["gain"] == REQUIRED_GAIN].copy()
    checkpoint(f"CHECKPOINT 13 COMPLETE: {len(df_pairwise_150)} rows")
    
    checkpoint("CHECKPOINT 14: Filtering to reporter...")
    df_pairwise_rep = df_pairwise_150[df_pairwise_150["bacterium_2_ASMA_id"].isin(PA_REPORTER_IDS)].copy()
    checkpoint(f"CHECKPOINT 14 COMPLETE: {len(df_pairwise_rep)} rows")
    
    checkpoint("CHECKPOINT 15: Computing ratios...")
    df_pairwise_rep["ratio"] = (
        df_pairwise_rep["bacterium_1_starting_OD"] / 
        df_pairwise_rep["bacterium_2_starting_OD"]
    )
    checkpoint("CHECKPOINT 15 COMPLETE")
    
    checkpoint("CHECKPOINT 16: Filtering to 100:1 ratio...")
    df_pairwise_100x = df_pairwise_rep[
        df_pairwise_rep["ratio"].apply(
            lambda r: math.isclose(r, 100.0, rel_tol=RATIO_100X_REL_TOL, abs_tol=RATIO_100X_ABS_TOL)
        )
    ].copy()
    checkpoint(f"CHECKPOINT 16 COMPLETE: {len(df_pairwise_100x)} rows")
    
    checkpoint("CHECKPOINT 17: Analyzing 100x starting ODs...")
    od_100x_counts = df_pairwise_100x["bacterium_2_starting_OD"].value_counts(dropna=False).sort_index()
    checkpoint(f"bacterium_2_starting_OD distribution in 100x rows:\n{od_100x_counts}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 18: Performing merge...")
    df_merged_dbg = df_pairwise_100x.merge(
        df_control_grouped,
        left_on='bacterium_2_starting_OD',
        right_on='starting_OD',
        how='left'
    )
    checkpoint(f"CHECKPOINT 18 COMPLETE: {len(df_merged_dbg)} rows after merge")
    
    checkpoint("CHECKPOINT 19: Analyzing merge results...")
    matching_count = df_merged_dbg['rfu_reporter_mean'].notna().sum()
    null_count = df_merged_dbg['rfu_reporter_mean'].isna().sum()
    checkpoint(f"Rows with matching control: {matching_count}", RESULTS_FILE)
    checkpoint(f"Rows with null control: {null_count}", RESULTS_FILE)
    
    pairwise_ods = set(df_pairwise_100x['bacterium_2_starting_OD'].dropna().unique())
    control_ods = set(df_control_grouped['starting_OD'].dropna().unique())
    
    checkpoint(f"Unique bacterium_2_starting_OD in 100x pairwise: {sorted(pairwise_ods)}", RESULTS_FILE)
    checkpoint(f"Unique starting_OD in control (grouped): {sorted(control_ods)}", RESULTS_FILE)
    checkpoint(f"Matching ODs: {sorted(pairwise_ods & control_ods)}", RESULTS_FILE)
    checkpoint(f"Missing from control: {sorted(pairwise_ods - control_ods)}", RESULTS_FILE)
    
    checkpoint("CHECKPOINT 20: Final summary...")
    checkpoint("=" * 80, RESULTS_FILE)
    checkpoint("SUMMARY", RESULTS_FILE)
    checkpoint("=" * 80, RESULTS_FILE)
    checkpoint(f"Control rows (reporter, gain=150, no exclusions): {len(df_control_rep_150_no_excl)}", RESULTS_FILE)
    checkpoint(f"Control rows (reporter, gain=150, with exclusions): {len(df_control_rep_150_with_excl)}", RESULTS_FILE)
    checkpoint(f"Has starting_OD == 0.0001 (no exclusions): {has_00001_no_excl}", RESULTS_FILE)
    checkpoint(f"Has starting_OD == 0.0001 (with exclusions): {has_00001_with_excl}", RESULTS_FILE)
    checkpoint(f"100x pairwise rows: {len(df_pairwise_100x)}", RESULTS_FILE)
    checkpoint(f"100x rows with matching control: {matching_count}", RESULTS_FILE)
    
    checkpoint("=" * 80)
    checkpoint("DEBUG SCRIPT COMPLETE!")
    checkpoint("=" * 80)
    
except Exception as e:
    checkpoint(f"ERROR at checkpoint: {str(e)}")
    import traceback
    checkpoint(f"Traceback:\n{traceback.format_exc()}")
    raise

