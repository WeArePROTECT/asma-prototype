"""
PA inhibition processing for UICT v1.
"""

import pandas as pd
import numpy as np
import math
from .config import (
    PA_REPORTER_IDS, 
    CONTROL_EXCLUSIONS, 
    REQUIRED_GAIN,
    RATIO_100X_REL_TOL,
    RATIO_100X_ABS_TOL,
    INHIBITION_THRESHOLDS
)


def process_inhibition_control(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process inhibition standard control data to compute reporter RFU means.
    
    Args:
        df: DataFrame with columns: sample_id, ASMA_id, type, assay_start_date, 
            starting_OD, gain, raw_RFU
        
    Returns:
        DataFrame with columns: starting_OD, rfu_reporter_mean
    """
    # Filter: type == "reporter" (case-insensitive) AND gain == REQUIRED_GAIN
    df_filtered = df[
        (df['type'].str.lower() == "reporter") & 
        (df['gain'] == REQUIRED_GAIN)
    ].copy()
    
    # Apply exclusions
    for exclusion in CONTROL_EXCLUSIONS:
        for key, value in exclusion.items():
            if key in df_filtered.columns:
                if isinstance(value, str):
                    df_filtered = df_filtered[df_filtered[key] != value]
                else:
                    df_filtered = df_filtered[df_filtered[key] != value]
    
    if df_filtered.empty:
        return pd.DataFrame(columns=['starting_OD', 'rfu_reporter_mean'])
    
    # Group by starting_OD and compute mean RFU
    grouped = df_filtered.groupby('starting_OD', as_index=False).agg({
        'raw_RFU': 'mean'
    })
    grouped.columns = ['starting_OD', 'rfu_reporter_mean']
    
    return grouped


def process_pairwise_interactions(
    df: pd.DataFrame, 
    control_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Process pairwise interaction data to compute inhibition percentages at 100:1 ratio.
    
    Args:
        df: DataFrame with columns: sample_id, bacterium_1_ASMA_id, bacterium_2_ASMA_id,
            assay_start_date, bacterium_1_starting_OD, bacterium_2_starting_OD, gain, raw_RFU
        control_df: DataFrame from process_inhibition_control()
        
    Returns:
        DataFrame with columns: ASMA_id, inhibition_pct, pa_starting_od, assay_start_date
    """
    # Filter: gain == REQUIRED_GAIN AND bacterium_2_ASMA_id is in PA_REPORTER_IDS
    df_filtered = df[
        (df['gain'] == REQUIRED_GAIN) &
        (df['bacterium_2_ASMA_id'].isin(PA_REPORTER_IDS))
    ].copy()
    
    if df_filtered.empty:
        return pd.DataFrame(columns=['ASMA_id', 'inhibition_pct', 'pa_starting_od', 'assay_start_date'])
    
    # Compute ratio
    df_filtered['ratio'] = (
        df_filtered['bacterium_1_starting_OD'] / 
        df_filtered['bacterium_2_starting_OD']
    )
    
    # Filter for exact 100:1 ratio using math.isclose
    df_filtered['is_100x'] = df_filtered['ratio'].apply(
        lambda r: math.isclose(r, 100.0, rel_tol=RATIO_100X_REL_TOL, abs_tol=RATIO_100X_ABS_TOL)
    )
    df_100x = df_filtered[df_filtered['is_100x']].copy()
    
    if df_100x.empty:
        return pd.DataFrame(columns=['ASMA_id', 'inhibition_pct', 'pa_starting_od', 'assay_start_date'])
    
    # Merge with control data to get reporter mean for matching starting_OD
    df_100x = df_100x.merge(
        control_df,
        left_on='bacterium_2_starting_OD',
        right_on='starting_OD',
        how='left'
    )
    
    # Compute inhibition percentage
    # inhibition_pct = 100 - (rfu_pairwise / rfu_reporter_mean) * 100
    df_100x['inhibition_pct'] = (
        100 - (df_100x['raw_RFU'] / df_100x['rfu_reporter_mean']) * 100
    )
    
    # Select and rename columns
    df_result = df_100x[[
        'bacterium_1_ASMA_id',
        'inhibition_pct',
        'bacterium_2_starting_OD',
        'assay_start_date'
    ]].copy()
    df_result.columns = ['ASMA_id', 'inhibition_pct', 'pa_starting_od', 'assay_start_date']
    
    # Remove rows where we couldn't match control data
    df_result = df_result[df_result['inhibition_pct'].notna()].copy()
    
    return df_result


def classify_inhibition_class(inhibition_mean: float) -> str:
    """
    Classify PA inhibition class based on mean inhibition percentage.
    
    Args:
        inhibition_mean: Mean inhibition percentage
        
    Returns:
        Inhibition class: "none", "weak", or "strong"
    """
    if pd.isna(inhibition_mean):
        return "none"
    
    if inhibition_mean < INHIBITION_THRESHOLDS["none"]:
        return "none"
    elif inhibition_mean < INHIBITION_THRESHOLDS["weak"]:
        return "weak"
    else:
        return "strong"


def aggregate_pa_inhibition_by_asma_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate PA inhibition data by ASMA_id.
    
    Args:
        df: DataFrame from process_pairwise_interactions()
        
    Returns:
        DataFrame with one row per ASMA_id containing aggregated metrics
    """
    if df.empty:
        return pd.DataFrame(columns=['ASMA_id', 'inhib_100x_n', 'inhib_100x_mean',
                                     'inhib_100x_sd', 'pa_inhibition_class', 'inhib_last_assay_date'])
    
    # Group by ASMA_id
    grouped = df.groupby('ASMA_id', as_index=False).agg({
        'inhibition_pct': ['count', 'mean', 'std'],
        'assay_start_date': 'max'
    })
    
    # Flatten column names
    grouped.columns = ['ASMA_id', 'inhib_100x_n', 'inhib_100x_mean', 
                       'inhib_100x_sd', 'inhib_last_assay_date']
    
    # Replace NaN std with NaN (when n = 1)
    grouped['inhib_100x_sd'] = grouped['inhib_100x_sd'].replace({np.nan: np.nan})
    
    # Classify based on mean inhibition
    grouped['pa_inhibition_class'] = grouped['inhib_100x_mean'].apply(classify_inhibition_class)
    
    # Convert assay date to string format (YYYYMMDD)
    grouped['inhib_last_assay_date'] = grouped['inhib_last_assay_date'].astype(str)
    
    return grouped

