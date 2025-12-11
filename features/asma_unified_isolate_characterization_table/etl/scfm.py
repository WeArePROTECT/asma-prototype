"""
SCFM growth curve processing for UICT v1.
"""

import pandas as pd
import numpy as np
from .config import SCFM_DELTA_OD_THRESHOLDS
from .loaders import filter_blank_rows


def classify_growth_class(delta_od: float) -> str:
    """
    Classify growth class based on delta_OD value.
    
    Args:
        delta_od: Delta OD value (max - min)
        
    Returns:
        Growth class: "no_growth", "poor", "normal", or "robust"
    """
    if delta_od < SCFM_DELTA_OD_THRESHOLDS["no_growth"]:
        return "no_growth"
    elif delta_od < SCFM_DELTA_OD_THRESHOLDS["poor"]:
        return "poor"
    elif delta_od < SCFM_DELTA_OD_THRESHOLDS["normal"]:
        return "normal"
    else:
        return "robust"


def process_scfm_growth_curve(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process SCFM growth curve data to compute delta_OD and growth class per replicate.
    
    Args:
        df: DataFrame with columns: sample_id, ASMA_id, assay_start_date, cyc_1 ... cyc_193
        
    Returns:
        DataFrame with columns: sample_id, ASMA_id, assay_start_date, od_min, od_max, 
        delta_od, growth_class
    """
    # Filter out BLANK rows
    df = filter_blank_rows(df)
    
    if df.empty:
        return pd.DataFrame(columns=['sample_id', 'ASMA_id', 'assay_start_date', 
                                     'od_min', 'od_max', 'delta_od', 'growth_class'])
    
    # Identify cycle columns
    cycle_cols = [col for col in df.columns if col.startswith('cyc_')]
    
    if not cycle_cols:
        raise ValueError("No cycle columns (cyc_*) found in SCFM growth curve data")
    
    # Compute min, max, and delta OD for each row
    df_result = df[['sample_id', 'ASMA_id', 'assay_start_date']].copy()
    df_result['od_min'] = df[cycle_cols].min(axis=1)
    df_result['od_max'] = df[cycle_cols].max(axis=1)
    df_result['delta_od'] = df_result['od_max'] - df_result['od_min']
    df_result['growth_class'] = df_result['delta_od'].apply(classify_growth_class)
    
    return df_result


def aggregate_scfm_by_asma_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate SCFM growth data by ASMA_id.
    
    Args:
        df: DataFrame from process_scfm_growth_curve()
        
    Returns:
        DataFrame with one row per ASMA_id containing aggregated metrics
    """
    if df.empty:
        return pd.DataFrame(columns=['ASMA_id', 'scfm_n_reps', 'scfm_delta_od_mean',
                                     'scfm_delta_od_sd', 'scfm_delta_od_max', 
                                     'scfm_growth_class', 'scfm_last_assay_date'])
    
    # Group by ASMA_id
    grouped = df.groupby('ASMA_id', as_index=False).agg({
        'delta_od': ['count', 'mean', 'std', 'max'],
        'assay_start_date': 'max'
    })
    
    # Flatten column names
    grouped.columns = ['ASMA_id', 'scfm_n_reps', 'scfm_delta_od_mean', 
                       'scfm_delta_od_sd', 'scfm_delta_od_max', 'scfm_last_assay_date']
    
    # Replace NaN std with NaN (when n_reps = 1)
    grouped['scfm_delta_od_sd'] = grouped['scfm_delta_od_sd'].replace({np.nan: np.nan})
    
    # Classify based on mean delta_od
    grouped['scfm_growth_class'] = grouped['scfm_delta_od_mean'].apply(classify_growth_class)
    
    # Convert assay date to string format (YYYYMMDD)
    grouped['scfm_last_assay_date'] = grouped['scfm_last_assay_date'].astype(str)
    
    return grouped

