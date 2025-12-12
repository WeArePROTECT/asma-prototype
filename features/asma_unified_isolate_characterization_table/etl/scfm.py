"""
SCFM growth curve processing for UICT v1.
"""

import pandas as pd
import numpy as np
from scipy import stats
from .config import (
    SCFM_DELTA_OD_THRESHOLDS,
    SCFM_CYCLE_24H,
    SCFM_CYCLE_48H,
    SCFM_CYCLE_BASELINE,
    SCFM_GROWTH_DELTA_OD_THRESHOLD,
    SCFM_CYCLE_INTERVAL_HOURS,
    SCFM_MU_WINDOW_MIN_CYCLES,
    SCFM_MU_WINDOW_MAX_CYCLES,
    SCFM_MU_MIN_OD,
    SCFM_MU_MIN_R2
)
from .loaders import filter_blank_rows


def validate_scfm_dataset(df: pd.DataFrame) -> bool:
    """
    Validate SCFM dataset structure and verify cycle columns exist.
    
    Args:
        df: DataFrame containing SCFM growth curve data
        
    Returns:
        True if valid, raises ValueError if invalid
        
    Raises:
        ValueError: If required columns are missing or cycle columns are invalid
    """
    if df.empty:
        raise ValueError("SCFM dataset is empty")
    
    # Check required columns
    required_cols = ['sample_id', 'ASMA_id', 'assay_start_date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"SCFM dataset missing required columns: {missing_cols}")
    
    # Verify cycle columns cyc_1 through cyc_193 are present
    expected_cycles = [f'cyc_{i}' for i in range(1, 194)]  # cyc_1 to cyc_193
    missing_cycles = [cycle for cycle in expected_cycles if cycle not in df.columns]
    if missing_cycles:
        raise ValueError(f"SCFM dataset missing cycle columns: {missing_cycles[:10]}{'...' if len(missing_cycles) > 10 else ''}")
    
    # Validate that cycle columns contain numeric data
    cycle_cols = [col for col in df.columns if col.startswith('cyc_')]
    for col in cycle_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Try to convert to numeric, checking if conversion fails
            non_numeric = pd.to_numeric(df[col], errors='coerce').isna().sum()
            if non_numeric > 0:
                raise ValueError(f"Cycle column {col} contains {non_numeric} non-numeric values")
    
    return True


def compute_mu_simple(od_values: np.ndarray) -> dict:
    """
    Compute provisional growth rate (μ) using sliding-window log-linear regression.
    
    Args:
        od_values: Array of OD values for all cycles (cyc_1 through cyc_193)
        
    Returns:
        Dictionary with keys: mu_simple, mu_simple_r2, mu_simple_t_start_hours, mu_simple_t_end_hours
        All values are NaN if no suitable window is found.
    """
    # Convert cycle indices to time (hours)
    n_cycles = len(od_values)
    time_hours = np.array([(i - 1) * SCFM_CYCLE_INTERVAL_HOURS for i in range(1, n_cycles + 1)])
    
    # Initialize result with NaN
    result = {
        'mu_simple': np.nan,
        'mu_simple_r2': np.nan,
        'mu_simple_t_start_hours': np.nan,
        'mu_simple_t_end_hours': np.nan
    }
    
    # Check if all OD values are below minimum threshold
    if np.all(od_values <= SCFM_MU_MIN_OD):
        return result
    
    best_r2 = -np.inf
    best_window = None
    
    # Slide windows of different sizes
    for window_size in range(SCFM_MU_WINDOW_MIN_CYCLES, SCFM_MU_WINDOW_MAX_CYCLES + 1):
        # Slide window across all possible positions
        for start_idx in range(n_cycles - window_size + 1):
            end_idx = start_idx + window_size
            
            # Extract window data
            window_od = od_values[start_idx:end_idx]
            window_time = time_hours[start_idx:end_idx]
            
            # Filter out OD values <= SCFM_MU_MIN_OD
            mask = window_od > SCFM_MU_MIN_OD
            filtered_od = window_od[mask]
            filtered_time = window_time[mask]
            
            # Need at least 3 points for regression
            if len(filtered_od) < 3:
                continue
            
            # Check that OD is increasing (no plateau)
            if filtered_od[-1] <= filtered_od[0]:
                continue
            
            # Compute ln(OD) and fit linear regression
            log_od = np.log(filtered_od)
            
            # Fit: log(OD) ~ time_hours
            slope, intercept, r_value, p_value, std_err = stats.linregress(filtered_time, log_od)
            r2 = r_value ** 2
            
            # Check criteria: positive slope, R² >= threshold
            if slope > 0 and r2 >= SCFM_MU_MIN_R2 and r2 > best_r2:
                best_r2 = r2
                best_window = {
                    'mu': slope,
                    'r2': r2,
                    't_start': filtered_time[0],
                    't_end': filtered_time[-1]
                }
    
    # If we found a suitable window, populate result
    if best_window is not None:
        result['mu_simple'] = best_window['mu']
        result['mu_simple_r2'] = best_window['r2']
        result['mu_simple_t_start_hours'] = best_window['t_start']
        result['mu_simple_t_end_hours'] = best_window['t_end']
    
    return result


def compute_replicate_metrics(row: pd.Series, cycle_cols: list) -> dict:
    """
    Compute all Phase 1 replicate-level metrics for a single replicate.
    
    Args:
        row: Series containing one replicate's data (including cycle columns)
        cycle_cols: List of cycle column names (cyc_1, cyc_2, ..., cyc_193)
        
    Returns:
        Dictionary with all replicate-level metrics
    """
    # Extract OD values for all cycles
    od_values = row[cycle_cols].values.astype(float)
    
    # Baseline OD (cycle 1)
    od_baseline = od_values[SCFM_CYCLE_BASELINE - 1] if not pd.isna(od_values[SCFM_CYCLE_BASELINE - 1]) else np.nan
    
    # OD at 24h (cycle 97)
    od_24h = od_values[SCFM_CYCLE_24H - 1] if not pd.isna(od_values[SCFM_CYCLE_24H - 1]) else np.nan
    
    # OD at 48h (cycle 193)
    od_48h = od_values[SCFM_CYCLE_48H - 1] if not pd.isna(od_values[SCFM_CYCLE_48H - 1]) else np.nan
    
    # ΔOD calculations
    delta_od_24h = od_24h - od_baseline if not (pd.isna(od_24h) or pd.isna(od_baseline)) else np.nan
    delta_od_48h = od_48h - od_baseline if not (pd.isna(od_48h) or pd.isna(od_baseline)) else np.nan
    
    # Binary growth calls
    growth_24h = delta_od_24h >= SCFM_GROWTH_DELTA_OD_THRESHOLD if not pd.isna(delta_od_24h) else False
    growth_48h = delta_od_48h >= SCFM_GROWTH_DELTA_OD_THRESHOLD if not pd.isna(delta_od_48h) else False
    
    # Maximum growth yield and time
    valid_od = od_values[~pd.isna(od_values)]
    if len(valid_od) > 0:
        od_max_yield = np.max(valid_od)
        # Find first occurrence of max (in case of ties)
        max_indices = np.where(od_values == od_max_yield)[0]
        max_cycle_idx = max_indices[0] + 1  # Convert to 1-based cycle index
        time_max_yield_hours = (max_cycle_idx - 1) * SCFM_CYCLE_INTERVAL_HOURS
    else:
        od_max_yield = np.nan
        time_max_yield_hours = np.nan
    
    # Compute μ (mu_simple)
    mu_result = compute_mu_simple(od_values)
    
    # Combine all metrics
    metrics = {
        'od_baseline': od_baseline,
        'od_24h': od_24h,
        'od_48h': od_48h,
        'delta_od_24h': delta_od_24h,
        'delta_od_48h': delta_od_48h,
        'growth_24h': growth_24h,
        'growth_48h': growth_48h,
        'od_max_yield': od_max_yield,
        'time_max_yield_hours': time_max_yield_hours,
        **mu_result
    }
    
    return metrics


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
    Process SCFM growth curve data to compute delta_OD, growth class, and Phase 1 metrics per replicate.
    
    Args:
        df: DataFrame with columns: sample_id, ASMA_id, assay_start_date, cyc_1 ... cyc_193
        
    Returns:
        DataFrame with columns: sample_id, ASMA_id, assay_start_date, od_min, od_max, 
        delta_od, growth_class, and all Phase 1 metrics
    """
    # Filter out BLANK rows
    df = filter_blank_rows(df)
    
    if df.empty:
        return pd.DataFrame(columns=['sample_id', 'ASMA_id', 'assay_start_date', 
                                     'od_min', 'od_max', 'delta_od', 'growth_class',
                                     'od_baseline', 'od_24h', 'od_48h', 'delta_od_24h', 'delta_od_48h',
                                     'growth_24h', 'growth_48h', 'od_max_yield', 'time_max_yield_hours',
                                     'mu_simple', 'mu_simple_r2', 'mu_simple_t_start_hours', 'mu_simple_t_end_hours'])
    
    # Identify cycle columns
    cycle_cols = [col for col in df.columns if col.startswith('cyc_')]
    cycle_cols.sort(key=lambda x: int(x.split('_')[1]))  # Sort by cycle number
    
    if not cycle_cols:
        raise ValueError("No cycle columns (cyc_*) found in SCFM growth curve data")
    
    # Start with base columns
    df_result = df[['sample_id', 'ASMA_id', 'assay_start_date']].copy()
    
    # Compute existing metrics (for backward compatibility)
    df_result['od_min'] = df[cycle_cols].min(axis=1)
    df_result['od_max'] = df[cycle_cols].max(axis=1)
    df_result['delta_od'] = df_result['od_max'] - df_result['od_min']
    df_result['growth_class'] = df_result['delta_od'].apply(classify_growth_class)
    
    # Compute Phase 1 metrics for each replicate
    phase1_metrics = df.apply(lambda row: compute_replicate_metrics(row, cycle_cols), axis=1)
    phase1_df = pd.DataFrame(list(phase1_metrics))
    
    # Combine all metrics
    df_result = pd.concat([df_result, phase1_df], axis=1)
    
    return df_result


def aggregate_scfm_by_asma_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate SCFM growth data by ASMA_id, including all Phase 1 metrics.
    
    Args:
        df: DataFrame from process_scfm_growth_curve()
        
    Returns:
        DataFrame with one row per ASMA_id containing aggregated metrics
    """
    if df.empty:
        return pd.DataFrame(columns=['ASMA_id', 'scfm_n_reps', 'scfm_delta_od_mean',
                                     'scfm_delta_od_sd', 'scfm_delta_od_max', 
                                     'scfm_growth_class', 'scfm_last_assay_date',
                                     'scfm_od_24h_mean', 'scfm_od_24h_sd',
                                     'scfm_od_48h_mean', 'scfm_od_48h_sd',
                                     'scfm_delta_od_24h_mean', 'scfm_delta_od_24h_sd',
                                     'scfm_delta_od_48h_mean', 'scfm_delta_od_48h_sd',
                                     'scfm_growth_24h_n', 'scfm_growth_24h_pct',
                                     'scfm_growth_48h_n', 'scfm_growth_48h_pct',
                                     'scfm_od_max_yield_mean', 'scfm_od_max_yield_sd',
                                     'scfm_time_max_yield_mean', 'scfm_time_max_yield_sd',
                                     'scfm_mu_simple_mean', 'scfm_mu_simple_sd', 'scfm_mu_simple_n_reps',
                                     'scfm_mu_simple_r2_mean', 'scfm_mu_simple_r2_sd'])
    
    # Group by ASMA_id
    grouped = df.groupby('ASMA_id', as_index=False).agg({
        'delta_od': ['count', 'mean', 'std', 'max'],
        'assay_start_date': 'max',
        # Phase 1 OD metrics
        'od_24h': ['mean', 'std'],
        'od_48h': ['mean', 'std'],
        # Phase 1 ΔOD metrics
        'delta_od_24h': ['mean', 'std'],
        'delta_od_48h': ['mean', 'std'],
        # Phase 1 max yield metrics
        'od_max_yield': ['mean', 'std'],
        'time_max_yield_hours': ['mean', 'std'],
        # Phase 1 μ metrics
        'mu_simple': ['mean', 'std'],
        'mu_simple_r2': ['mean', 'std']
    })
    
    # Flatten column names
    grouped.columns = ['ASMA_id', 'scfm_n_reps', 'scfm_delta_od_mean', 
                       'scfm_delta_od_sd', 'scfm_delta_od_max', 'scfm_last_assay_date',
                       'scfm_od_24h_mean', 'scfm_od_24h_sd',
                       'scfm_od_48h_mean', 'scfm_od_48h_sd',
                       'scfm_delta_od_24h_mean', 'scfm_delta_od_24h_sd',
                       'scfm_delta_od_48h_mean', 'scfm_delta_od_48h_sd',
                       'scfm_od_max_yield_mean', 'scfm_od_max_yield_sd',
                       'scfm_time_max_yield_mean', 'scfm_time_max_yield_sd',
                       'scfm_mu_simple_mean', 'scfm_mu_simple_sd',
                       'scfm_mu_simple_r2_mean', 'scfm_mu_simple_r2_sd']
    
    # Replace NaN std with NaN (when n_reps = 1) - pandas already handles this, but ensure consistency
    std_cols = [col for col in grouped.columns if col.endswith('_sd')]
    for col in std_cols:
        grouped[col] = grouped[col].replace({np.nan: np.nan})
    
    # Classify based on mean delta_od
    grouped['scfm_growth_class'] = grouped['scfm_delta_od_mean'].apply(classify_growth_class)
    
    # Convert assay date to string format (YYYYMMDD)
    grouped['scfm_last_assay_date'] = grouped['scfm_last_assay_date'].astype(str)
    
    # Compute binary growth counts and percentages
    def safe_percentage(sum_val, count_val):
        """Compute percentage safely, handling division by zero."""
        if count_val == 0 or pd.isna(count_val) or pd.isna(sum_val):
            return np.nan
        return (sum_val / count_val) * 100
    
    growth_24h_counts = df.groupby('ASMA_id')['growth_24h'].agg(['sum', 'count'])
    growth_48h_counts = df.groupby('ASMA_id')['growth_48h'].agg(['sum', 'count'])
    
    grouped['scfm_growth_24h_n'] = grouped['ASMA_id'].map(growth_24h_counts['sum']).fillna(0).astype(int)
    grouped['scfm_growth_24h_pct'] = grouped.apply(
        lambda row: safe_percentage(
            growth_24h_counts.loc[row['ASMA_id'], 'sum'] if row['ASMA_id'] in growth_24h_counts.index else 0,
            growth_24h_counts.loc[row['ASMA_id'], 'count'] if row['ASMA_id'] in growth_24h_counts.index else 0
        ), axis=1
    )
    
    grouped['scfm_growth_48h_n'] = grouped['ASMA_id'].map(growth_48h_counts['sum']).fillna(0).astype(int)
    grouped['scfm_growth_48h_pct'] = grouped.apply(
        lambda row: safe_percentage(
            growth_48h_counts.loc[row['ASMA_id'], 'sum'] if row['ASMA_id'] in growth_48h_counts.index else 0,
            growth_48h_counts.loc[row['ASMA_id'], 'count'] if row['ASMA_id'] in growth_48h_counts.index else 0
        ), axis=1
    )
    
    # Compute count of replicates with valid μ estimates
    mu_valid_counts = df.groupby('ASMA_id')['mu_simple'].apply(lambda x: x.notna().sum())
    grouped['scfm_mu_simple_n_reps'] = grouped['ASMA_id'].map(mu_valid_counts).fillna(0).astype(int)
    
    return grouped

