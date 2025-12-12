#!/usr/bin/env python3
"""
Minimal debug - just check the merge step with known values.
"""

import pandas as pd
import sys

# We know from previous debug:
# - 324 rows pass 100:1 filter
# - bacterium_2_starting_OD = 0.0001 for those rows
# - Need to check if control has starting_OD = 0.0001

print("Loading only control sheet...")
try:
    df_control = pd.read_excel(
        "/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx",
        sheet_name='inhibition_standard_control'
    )
    print(f"Loaded: {len(df_control)} rows")
    
    # Filter to reporter, gain 150
    df_rep_150 = df_control[
        (df_control["type"] == "reporter") &
        (df_control["gain"] == 150)
    ]
    print(f"Reporter + gain=150: {len(df_rep_150)} rows")
    
    # Check for starting_OD = 0.0001
    print(f"\nstarting_OD values in reporter+gain150:")
    print(df_rep_150["starting_OD"].value_counts().sort_index())
    
    # Check if 0.0001 exists
    has_00001 = (df_rep_150["starting_OD"] == 0.0001).any()
    print(f"\nHas starting_OD == 0.0001: {has_00001}")
    
    if has_00001:
        print(f"Rows with starting_OD == 0.0001:")
        print(df_rep_150[df_rep_150["starting_OD"] == 0.0001][["starting_OD", "raw_RFU", "assay_start_date"]].head())
    
    # Group by starting_OD
    grouped = df_rep_150.groupby('starting_OD', as_index=False)['raw_RFU'].mean()
    grouped.columns = ['starting_OD', 'rfu_reporter_mean']
    print(f"\nGrouped control (unique starting_OD values):")
    print(grouped)
    
    # Check if 0.0001 is in grouped
    has_in_grouped = (grouped['starting_OD'] == 0.0001).any()
    print(f"\n0.0001 in grouped control: {has_in_grouped}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

