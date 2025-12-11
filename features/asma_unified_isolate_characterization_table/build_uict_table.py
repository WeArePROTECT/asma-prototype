#!/usr/bin/env python3
"""
Main entry point for building UICT v1 table.

Usage:
    python build_uict_table.py [--taxonomy PATH] [--phenotype PATH] [--output PATH]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from etl.loaders import (
    load_taxonomy_table,
    load_phenotype_excel,
    validate_taxonomy_data,
    validate_phenotype_data
)
from etl.scfm import process_scfm_growth_curve, aggregate_scfm_by_asma_id
from etl.inhibition import (
    process_inhibition_control,
    process_pairwise_interactions,
    aggregate_pa_inhibition_by_asma_id
)
from etl.carbon import process_carbon_utilization
from etl.aggregate import merge_uict_data
from etl.config import (
    DEFAULT_TAXONOMY_PATH,
    DEFAULT_PHENOTYPE_PATH,
    DEFAULT_OUTPUT_PATH
)


def build_uict_v1(
    taxonomy_path: str,
    phenotype_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Build UICT v1 table from taxonomy and phenotype data.
    
    Args:
        taxonomy_path: Path to taxonomy.tsv
        phenotype_path: Path to phenotype Excel file
        output_path: Path to output CSV file
        
    Returns:
        UICT DataFrame
    """
    print("Loading taxonomy data...")
    taxonomy_df = load_taxonomy_table(taxonomy_path)
    validate_taxonomy_data(taxonomy_df)
    print(f"  Loaded {len(taxonomy_df)} isolates from taxonomy")
    
    print("\nLoading phenotype data...")
    phenotype_sheets = load_phenotype_excel(phenotype_path)
    validate_phenotype_data(phenotype_sheets)
    print(f"  Loaded {len(phenotype_sheets)} sheets")
    
    print("\nProcessing SCFM growth data...")
    scfm_raw = process_scfm_growth_curve(phenotype_sheets['SCFM_growth_curve'])
    scfm_agg = aggregate_scfm_by_asma_id(scfm_raw)
    print(f"  Processed {len(scfm_raw)} replicates for {len(scfm_agg)} isolates")
    
    print("\nProcessing PA inhibition data...")
    control_df = process_inhibition_control(phenotype_sheets['inhibition_standard_control'])
    pairwise_df = process_pairwise_interactions(
        phenotype_sheets['pairwise_interaction'],
        control_df
    )
    inhibition_agg = aggregate_pa_inhibition_by_asma_id(pairwise_df)
    print(f"  Processed {len(pairwise_df)} 100:1 replicates for {len(inhibition_agg)} isolates")
    
    print("\nProcessing carbon utilization data...")
    carbon_agg = process_carbon_utilization(phenotype_sheets['carbon_utilization'])
    print(f"  Processed data for {len(carbon_agg)} isolates")
    
    print("\nMerging all data into UICT...")
    uict = merge_uict_data(taxonomy_df, scfm_agg, inhibition_agg, carbon_agg)
    print(f"  Final UICT contains {len(uict)} isolates")
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nWriting UICT to {output_path}...")
    uict.to_csv(output_path, index=False)
    print("  Done!")
    
    return uict


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(description="Build UICT v1 table")
    parser.add_argument(
        '--taxonomy',
        type=str,
        default=DEFAULT_TAXONOMY_PATH,
        help=f"Path to taxonomy TSV (default: {DEFAULT_TAXONOMY_PATH})"
    )
    parser.add_argument(
        '--phenotype',
        type=str,
        default=DEFAULT_PHENOTYPE_PATH,
        help=f"Path to phenotype Excel (default: {DEFAULT_PHENOTYPE_PATH})"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output CSV (default: {DEFAULT_OUTPUT_PATH})"
    )
    
    args = parser.parse_args()
    
    try:
        uict = build_uict_v1(args.taxonomy, args.phenotype, args.output)
        
        # Print summary statistics
        print("\n" + "="*80)
        print("UICT v1 Summary Statistics")
        print("="*80)
        print(f"Total isolates: {len(uict)}")
        print(f"  With SCFM data: {uict['scfm_n_reps'].notna().sum()}")
        print(f"  With inhibition data (100:1): {uict['inhib_100x_n'].notna().sum()}")
        print(f"  With carbon utilization data: {uict['no_carbon_mean_od'].notna().sum()}")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

