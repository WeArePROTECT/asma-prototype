"""
Aggregation functions for combining phenotype data with taxonomy.
"""

import pandas as pd


def merge_uict_data(
    taxonomy_df: pd.DataFrame,
    scfm_df: pd.DataFrame,
    inhibition_df: pd.DataFrame,
    carbon_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge all phenotype data with taxonomy to create UICT v1.
    
    Args:
        taxonomy_df: Taxonomy DataFrame (authoritative source)
        scfm_df: SCFM growth aggregated data
        inhibition_df: PA inhibition aggregated data
        carbon_df: Carbon utilization aggregated data
        
    Returns:
        UICT DataFrame with one row per ASMA_id from taxonomy
    """
    # Start with taxonomy (left join - taxonomy is authoritative)
    uict = taxonomy_df.copy()
    
    # Rename taxonomy columns to match UICT schema (already in correct format)
    # Keep ASMA_id as the key
    
    # Merge SCFM data
    if not scfm_df.empty:
        uict = uict.merge(
            scfm_df,
            on='ASMA_id',
            how='left'
        )
    else:
        # Add empty SCFM columns (including Phase 1 metrics)
        scfm_cols = ['scfm_n_reps', 'scfm_delta_od_mean', 'scfm_delta_od_sd',
                     'scfm_delta_od_max', 'scfm_growth_class', 'scfm_last_assay_date',
                     # Phase 1 metrics
                     'scfm_od_24h_mean', 'scfm_od_24h_sd',
                     'scfm_od_48h_mean', 'scfm_od_48h_sd',
                     'scfm_delta_od_24h_mean', 'scfm_delta_od_24h_sd',
                     'scfm_delta_od_48h_mean', 'scfm_delta_od_48h_sd',
                     'scfm_growth_24h_n', 'scfm_growth_24h_pct',
                     'scfm_growth_48h_n', 'scfm_growth_48h_pct',
                     'scfm_od_max_yield_mean', 'scfm_od_max_yield_sd',
                     'scfm_time_max_yield_mean', 'scfm_time_max_yield_sd',
                     'scfm_mu_simple_mean', 'scfm_mu_simple_sd', 'scfm_mu_simple_n_reps',
                     'scfm_mu_simple_r2_mean', 'scfm_mu_simple_r2_sd']
        for col in scfm_cols:
            uict[col] = pd.NA
    
    # Merge inhibition data
    if not inhibition_df.empty:
        uict = uict.merge(
            inhibition_df,
            on='ASMA_id',
            how='left'
        )
    else:
        # Add empty inhibition columns
        inhib_cols = ['inhib_100x_n', 'inhib_100x_mean', 'inhib_100x_sd',
                      'pa_inhibition_class', 'inhib_last_assay_date']
        for col in inhib_cols:
            uict[col] = pd.NA
    
    # Merge carbon data
    if not carbon_df.empty:
        uict = uict.merge(
            carbon_df,
            on='ASMA_id',
            how='left'
        )
    else:
        # Add empty carbon columns (we don't know all substrates ahead of time,
        # so this is handled in the carbon processor)
        pass
    
    # Ensure all phenotype columns are properly typed
    # Integer columns
    int_cols = ['scfm_n_reps', 'inhib_100x_n',
                'scfm_growth_24h_n', 'scfm_growth_48h_n', 'scfm_mu_simple_n_reps']
    for col in int_cols:
        if col in uict.columns:
            uict[col] = pd.to_numeric(uict[col], errors='coerce').astype('Int64')
    
    # Float columns
    float_cols = ['scfm_delta_od_mean', 'scfm_delta_od_sd', 'scfm_delta_od_max',
                  'inhib_100x_mean', 'inhib_100x_sd',
                  # Phase 1 float columns
                  'scfm_od_24h_mean', 'scfm_od_24h_sd',
                  'scfm_od_48h_mean', 'scfm_od_48h_sd',
                  'scfm_delta_od_24h_mean', 'scfm_delta_od_24h_sd',
                  'scfm_delta_od_48h_mean', 'scfm_delta_od_48h_sd',
                  'scfm_growth_24h_pct', 'scfm_growth_48h_pct',
                  'scfm_od_max_yield_mean', 'scfm_od_max_yield_sd',
                  'scfm_time_max_yield_mean', 'scfm_time_max_yield_sd',
                  'scfm_mu_simple_mean', 'scfm_mu_simple_sd',
                  'scfm_mu_simple_r2_mean', 'scfm_mu_simple_r2_sd']
    for col in float_cols:
        if col in uict.columns:
            uict[col] = pd.to_numeric(uict[col], errors='coerce')
    
    return uict

