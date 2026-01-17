#!/usr/bin/env python3
"""
Debug script to investigate PA inhibition pipeline.
Exploratory checks on real data without modifying core logic.
"""

import pandas as pd
import math
from etl.loaders import load_phenotype_excel
from etl.config import PA_REPORTER_IDS, REQUIRED_GAIN, RATIO_100X_REL_TOL, RATIO_100X_ABS_TOL

# Load pairwise interaction data
print("=" * 80)
print("1. BASIC PAIRWISE OVERVIEW")
print("=" * 80)

phenotype_sheets = load_phenotype_excel("/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20251209.xlsx")
df_pairwise = phenotype_sheets['pairwise_interaction']

print("\nColumns in pairwise_interaction sheet:")
print(df_pairwise.columns.tolist())

print("\nFirst 10 rows (all columns):")
print(df_pairwise.head(10).to_string())

print("\nGain value counts:")
print(df_pairwise["gain"].value_counts(dropna=False))

print("\nTop 20 bacterium_2_ASMA_id values:")
print(df_pairwise["bacterium_2_ASMA_id"].value_counts().head(20))

print("\nUnique combinations of starting ODs:")
od_combos = df_pairwise[["bacterium_1_starting_OD", "bacterium_2_starting_OD"]].drop_duplicates().sort_values(["bacterium_1_starting_OD", "bacterium_2_starting_OD"])
print(od_combos.to_string())

# 2. Check raw ratio distribution
print("\n" + "=" * 80)
print("2. RAW RATIO DISTRIBUTION (before any filtering)")
print("=" * 80)

df_pairwise["ratio_b1_over_b2"] = df_pairwise["bacterium_1_starting_OD"] / df_pairwise["bacterium_2_starting_OD"]

print("\nTop 20 ratio values (b1/b2):")
print(df_pairwise["ratio_b1_over_b2"].value_counts().head(20))

# Check for ratios near 100
mask_approx_100 = df_pairwise["ratio_b1_over_b2"].apply(
    lambda x: math.isclose(x, 100.0, rel_tol=RATIO_100X_REL_TOL, abs_tol=RATIO_100X_ABS_TOL) if pd.notna(x) else False
)
print(f"\nRows with ratio ≈ 100 (rel_tol={RATIO_100X_REL_TOL}, abs_tol={RATIO_100X_ABS_TOL}): {mask_approx_100.sum()}")

if mask_approx_100.sum() > 0:
    print("\nSample rows with ratio ≈ 100:")
    sample_100 = df_pairwise.loc[mask_approx_100, [
        "sample_id", "bacterium_1_ASMA_id", "bacterium_2_ASMA_id", 
        "bacterium_1_starting_OD", "bacterium_2_starting_OD", "ratio_b1_over_b2", "gain"
    ]].head(10)
    print(sample_100.to_string())
else:
    print("\nNo rows found with ratio ≈ 100")

# Check ratio distribution more broadly
print("\nRatio statistics:")
print(df_pairwise["ratio_b1_over_b2"].describe())

# 3. Step-wise filter counts
print("\n" + "=" * 80)
print("3. STEP-WISE FILTER COUNTS")
print("=" * 80)

n_total = len(df_pairwise)
print(f"\nTotal rows in pairwise_interaction: {n_total}")

# Filter 1: gain == 150
df_gain = df_pairwise[df_pairwise["gain"] == REQUIRED_GAIN].copy()
n_gain = len(df_gain)
print(f"After gain == {REQUIRED_GAIN}: {n_gain}")

if n_gain > 0:
    print("\nSample after gain filter (first 5 rows):")
    print(df_gain[["sample_id", "bacterium_1_ASMA_id", "bacterium_2_ASMA_id", 
                   "bacterium_1_starting_OD", "bacterium_2_starting_OD", "gain", "ratio_b1_over_b2"]].head(5).to_string())
else:
    print("No rows after gain filter!")

# Filter 2: reporter filter
print(f"\nPA_REPORTER_IDS from config: {PA_REPORTER_IDS}")
print(f"\nUnique bacterium_2_ASMA_id values in gain-filtered data:")
print(df_gain["bacterium_2_ASMA_id"].value_counts().head(20))

df_reporter = df_gain[df_gain["bacterium_2_ASMA_id"].isin(PA_REPORTER_IDS)].copy()
n_reporter = len(df_reporter)
print(f"\nAfter reporter filter (bacterium_2_ASMA_id in PA_REPORTER_IDS): {n_reporter}")

if n_reporter > 0:
    print("\nSample after reporter filter (first 5 rows):")
    print(df_reporter[["sample_id", "bacterium_1_ASMA_id", "bacterium_2_ASMA_id", 
                       "bacterium_1_starting_OD", "bacterium_2_starting_OD", "gain", "ratio_b1_over_b2"]].head(5).to_string())
else:
    print("No rows after reporter filter!")
    print("\nChecking if any reporter IDs match (case-insensitive or partial):")
    for reporter_id in PA_REPORTER_IDS:
        matches = df_gain["bacterium_2_ASMA_id"].str.contains(reporter_id, case=False, na=False).sum()
        if matches > 0:
            print(f"  '{reporter_id}' matches {matches} rows (case-insensitive)")
            print(f"    Sample matches: {df_gain[df_gain['bacterium_2_ASMA_id'].str.contains(reporter_id, case=False, na=False)]['bacterium_2_ASMA_id'].unique()[:5].tolist()}")

# Filter 3: 100:1 ratio filter
if n_reporter > 0:
    df_100x = df_reporter[
        df_reporter.apply(
            lambda row: math.isclose(
                row["bacterium_1_starting_OD"] / row["bacterium_2_starting_OD"], 
                100.0, 
                rel_tol=RATIO_100X_REL_TOL, 
                abs_tol=RATIO_100X_ABS_TOL
            ) if pd.notna(row["bacterium_1_starting_OD"]) and pd.notna(row["bacterium_2_starting_OD"]) and row["bacterium_2_starting_OD"] != 0 else False,
            axis=1
        )
    ].copy()
    n_100x = len(df_100x)
    print(f"\nAfter 100:1 filter (math.isclose with rel_tol={RATIO_100X_REL_TOL}, abs_tol={RATIO_100X_ABS_TOL}): {n_100x}")
    
    if n_100x > 0:
        print("\nSample after 100:1 filter (first 5 rows):")
        print(df_100x[["sample_id", "bacterium_1_ASMA_id", "bacterium_2_ASMA_id", 
                       "bacterium_1_starting_OD", "bacterium_2_starting_OD", "gain", "ratio_b1_over_b2"]].head(5).to_string())
    else:
        print("No rows after 100:1 filter!")
        print("\nChecking ratio distribution in reporter-filtered data:")
        if len(df_reporter) > 0:
            print(df_reporter["ratio_b1_over_b2"].describe())
            print("\nClosest ratios to 100:")
            df_reporter_sorted = df_reporter.copy()
            df_reporter_sorted["dist_from_100"] = abs(df_reporter_sorted["ratio_b1_over_b2"] - 100.0)
            closest = df_reporter_sorted.nsmallest(10, "dist_from_100")
            print(closest[["bacterium_1_ASMA_id", "bacterium_2_ASMA_id", 
                          "bacterium_1_starting_OD", "bacterium_2_starting_OD", 
                          "ratio_b1_over_b2", "dist_from_100"]].to_string())
else:
    print("\nSkipping 100:1 filter (no rows after reporter filter)")

# 4. Reporter ID config check
print("\n" + "=" * 80)
print("4. REPORTER ID CONFIG CHECK")
print("=" * 80)

print(f"\nPA_REPORTER_IDS from config: {PA_REPORTER_IDS}")

print("\nAll unique bacterium_2_ASMA_id values (sorted):")
all_b2_ids = df_pairwise["bacterium_2_ASMA_id"].value_counts()
print(all_b2_ids.to_string())

print("\nChecking for potential matches (case-insensitive, partial):")
for reporter_id in PA_REPORTER_IDS:
    print(f"\n  Looking for: '{reporter_id}'")
    exact_matches = (df_pairwise["bacterium_2_ASMA_id"] == reporter_id).sum()
    case_insensitive = df_pairwise["bacterium_2_ASMA_id"].str.contains(reporter_id, case=False, na=False).sum()
    print(f"    Exact matches: {exact_matches}")
    print(f"    Case-insensitive matches: {case_insensitive}")
    if case_insensitive > 0:
        unique_matches = df_pairwise[df_pairwise["bacterium_2_ASMA_id"].str.contains(reporter_id, case=False, na=False)]["bacterium_2_ASMA_id"].unique()
        print(f"    Unique matching values: {unique_matches.tolist()}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total rows: {n_total}")
print(f"After gain == {REQUIRED_GAIN}: {n_gain}")
print(f"After reporter filter: {n_reporter}")
print(f"After 100:1 filter: {n_100x if n_reporter > 0 else 0}")
print(f"Rows with ratio ≈ 100 (any gain/reporter): {mask_approx_100.sum()}")

