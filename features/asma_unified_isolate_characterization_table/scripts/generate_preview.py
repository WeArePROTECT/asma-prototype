#!/usr/bin/env python3
"""
Generate preview output for UICT v1.
"""

import pandas as pd
from pathlib import Path

UICT_PATH = "data/derived/asma_unified_isolate_characterization_table.csv"

def main():
    """Generate markdown-friendly preview of UICT."""
    df = pd.read_csv(UICT_PATH)
    
    print("# UICT v1 Preview Output\n")
    
    print("## Schema (Columns + Data Types)\n")
    print("| Column | Data Type |")
    print("|--------|-----------|")
    for col, dtype in zip(df.columns, df.dtypes):
        print(f"| `{col}` | `{dtype}` |")
    
    print(f"\n## First 10 Rows\n")
    print("| " + " | ".join(df.columns[:15].tolist()) + " |")
    print("|" + "|".join(["---" for _ in range(min(15, len(df.columns)))]) + "|")
    
    for idx, row in df.head(10).iterrows():
        row_values = []
        for val in row[:15]:
            if pd.isna(val):
                row_values.append("NaN")
            elif isinstance(val, float):
                row_values.append(f"{val:.4f}" if abs(val) < 1000 else f"{val:.2e}")
            else:
                val_str = str(val)[:50]
                row_values.append(val_str)
        print("| " + " | ".join(row_values) + " |")
    
    if len(df.columns) > 15:
        print(f"\n*Note: Showing first 15 of {len(df.columns)} columns*\n")
    
    print("\n## Summary Statistics\n")
    print(f"- **Total isolates:** {len(df)}")
    print(f"- **With SCFM data:** {df['scfm_n_reps'].notna().sum()}")
    print(f"- **With inhibition data (100:1):** {df['inhib_100x_n'].notna().sum()}")
    print(f"- **With carbon utilization data:** {df['no_carbon_mean_od'].notna().sum()}")
    
    # Count by growth class
    print("\n### SCFM Growth Class Distribution\n")
    if df['scfm_growth_class'].notna().any():
        growth_counts = df['scfm_growth_class'].value_counts()
        for class_name, count in growth_counts.items():
            print(f"- `{class_name}`: {count}")
    else:
        print("- No SCFM growth class data")
    
    # Count by inhibition class
    print("\n### PA Inhibition Class Distribution\n")
    if df['pa_inhibition_class'].notna().any():
        inhib_counts = df['pa_inhibition_class'].value_counts()
        for class_name, count in inhib_counts.items():
            print(f"- `{class_name}`: {count}")
    else:
        print("- No PA inhibition class data")

if __name__ == '__main__':
    main()

