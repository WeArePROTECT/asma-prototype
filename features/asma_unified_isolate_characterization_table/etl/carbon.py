"""
Carbon utilization processing for UICT v1.
"""

import pandas as pd
import numpy as np
from .config import CARBON_UTILIZATION_SD_MULTIPLIER, CARBON_MIN_REPLICATES
from .loaders import filter_blank_rows


def _to_snake_case(name: str) -> str:
    """Convert string to snake_case."""
    return name.lower().replace(' ', '_').replace('-', '_')


def process_carbon_utilization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process carbon utilization data with date-aware logic.
    
    Logic:
    1. For each ASMA_id × assay_date: compute mean_no_carbon(date) and sd_no_carbon(date)
    2. For each substrate: compute mean_C(date) per date
    3. Determine utilization per date: mean_C(date) > mean_no_carbon(date) + 2*sd_no_carbon(date)
    4. Aggregate across dates: average of date-wise means, utilization = "utilizes" if ANY date passes
    
    Args:
        df: DataFrame with columns: sample_id, ASMA_id, assay_start_date, No_carbon, 
            Glucose, Lactate, ... (20+ carbon substrates)
        
    Returns:
        DataFrame with one row per ASMA_id and columns for each substrate
    """
    # Filter out BLANK rows
    df = filter_blank_rows(df)
    
    if df.empty:
        return pd.DataFrame(columns=['ASMA_id'])
    
    # Identify carbon substrate columns (exclude metadata columns)
    metadata_cols = ['sample_id', 'ASMA_id', 'assay_start_date']
    substrate_cols = [col for col in df.columns if col not in metadata_cols]
    
    if 'No_carbon' not in substrate_cols:
        raise ValueError("No_carbon column not found in carbon utilization data")
    
    # Remove No_carbon from substrate list (handle separately)
    carbon_substrates = [col for col in substrate_cols if col != 'No_carbon']
    
    # Step 1: Process per ASMA_id × assay_date
    results_by_date = []
    
    for (asma_id, assay_date), group in df.groupby(['ASMA_id', 'assay_start_date']):
        # Compute mean and sd for No_carbon at this date
        no_carbon_values = group['No_carbon'].dropna()
        n_no_carbon = len(no_carbon_values)
        
        # Process each carbon substrate
        row_data = {
            'ASMA_id': asma_id,
            'assay_start_date': assay_date,
            'no_carbon_n': n_no_carbon
        }
        
        if n_no_carbon < CARBON_MIN_REPLICATES:
            # Not enough replicates for No_carbon - mark everything as uncertain
            row_data['no_carbon_mean'] = no_carbon_values.mean() if n_no_carbon > 0 else np.nan
            row_data['no_carbon_sd'] = no_carbon_values.std() if n_no_carbon > 1 else np.nan
            
            for substrate in carbon_substrates:
                substrate_values = group[substrate].dropna()
                n_substrate = len(substrate_values)
                row_data[f'{substrate}_mean'] = substrate_values.mean() if n_substrate > 0 else np.nan
                row_data[f'{substrate}_utilization'] = "uncertain"
                row_data[f'{substrate}_n'] = n_substrate
        else:
            # Enough replicates for No_carbon - can compute threshold
            mean_no_carbon_date = no_carbon_values.mean()
            sd_no_carbon_date = no_carbon_values.std()
            row_data['no_carbon_mean'] = mean_no_carbon_date
            row_data['no_carbon_sd'] = sd_no_carbon_date
            
            for substrate in carbon_substrates:
                substrate_values = group[substrate].dropna()
                n_substrate = len(substrate_values)
                
                if n_substrate < CARBON_MIN_REPLICATES:
                    # Not enough replicates for this substrate
                    row_data[f'{substrate}_mean'] = substrate_values.mean() if n_substrate > 0 else np.nan
                    row_data[f'{substrate}_utilization'] = "uncertain"
                    row_data[f'{substrate}_n'] = n_substrate
                else:
                    mean_substrate_date = substrate_values.mean()
                    threshold = mean_no_carbon_date + (CARBON_UTILIZATION_SD_MULTIPLIER * sd_no_carbon_date)
                    
                    row_data[f'{substrate}_mean'] = mean_substrate_date
                    row_data[f'{substrate}_utilization'] = "utilizes" if mean_substrate_date > threshold else "no_growth"
                    row_data[f'{substrate}_n'] = n_substrate
        
        results_by_date.append(row_data)
    
    if not results_by_date:
        return pd.DataFrame(columns=['ASMA_id'])
    
    df_by_date = pd.DataFrame(results_by_date)
    
    # Step 2: Aggregate across dates per ASMA_id
    final_results = []
    
    for asma_id, group in df_by_date.groupby('ASMA_id'):
        row_data = {'ASMA_id': asma_id}
        
        # Aggregate No_carbon (mean of means, mean of SDs)
        row_data['no_carbon_mean_od'] = group['no_carbon_mean'].mean()
        row_data['no_carbon_sd_od'] = group['no_carbon_sd'].mean()
        
        # Get most recent assay date
        row_data['carbon_last_assay_date'] = group['assay_start_date'].max()
        
        # For each substrate: average of means, utilization = "utilizes" if ANY date passes
        for substrate in carbon_substrates:
            mean_col = f'{substrate}_mean'
            util_col = f'{substrate}_utilization'
            
            # Average of date-wise means
            row_data[f'{_to_snake_case(substrate)}_mean_od'] = group[mean_col].mean()
            
            # Utilization: "utilizes" if ANY date passes, otherwise check for "uncertain"
            utilizations = group[util_col].dropna().unique()
            if "utilizes" in utilizations:
                row_data[f'{_to_snake_case(substrate)}_utilization_call'] = "utilizes"
            elif "uncertain" in utilizations:
                row_data[f'{_to_snake_case(substrate)}_utilization_call'] = "uncertain"
            else:
                row_data[f'{_to_snake_case(substrate)}_utilization_call'] = "no_growth"
        
        final_results.append(row_data)
    
    if not final_results:
        return pd.DataFrame(columns=['ASMA_id'])
    
    df_final = pd.DataFrame(final_results)
    
    # Convert assay date to string format (YYYYMMDD)
    df_final['carbon_last_assay_date'] = df_final['carbon_last_assay_date'].astype(str)
    
    return df_final

