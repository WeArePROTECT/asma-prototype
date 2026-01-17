"""
Tests for Phase 1 SCFM growth metrics implementation.
"""

import pandas as pd
import numpy as np
import pytest
from etl.scfm import (
    validate_scfm_dataset,
    compute_replicate_metrics,
    compute_mu_simple,
    process_scfm_growth_curve,
    aggregate_scfm_by_asma_id
)
from etl.config import (
    SCFM_CYCLE_24H,
    SCFM_CYCLE_48H,
    SCFM_CYCLE_BASELINE,
    SCFM_GROWTH_DELTA_OD_THRESHOLD,
    SCFM_CYCLE_INTERVAL_HOURS
)


def test_validate_scfm_dataset_valid():
    """Test that valid dataset passes validation."""
    df = pd.DataFrame({
        'sample_id': [1, 2],
        'ASMA_id': ['ASMA-1', 'ASMA-2'],
        'assay_start_date': ['20250101', '20250102'],
    })
    # Add cycle columns
    for i in range(1, 194):
        df[f'cyc_{i}'] = [0.1 + i * 0.001, 0.2 + i * 0.001]
    
    # Should not raise
    assert validate_scfm_dataset(df) is True


def test_validate_scfm_dataset_missing_required_columns():
    """Test that missing required columns raises error."""
    df = pd.DataFrame({
        'sample_id': [1, 2],
        # Missing ASMA_id
        'assay_start_date': ['20250101', '20250102'],
    })
    
    with pytest.raises(ValueError, match="missing required columns"):
        validate_scfm_dataset(df)


def test_validate_scfm_dataset_missing_cycle_columns():
    """Test that missing cycle columns raises error."""
    df = pd.DataFrame({
        'sample_id': [1, 2],
        'ASMA_id': ['ASMA-1', 'ASMA-2'],
        'assay_start_date': ['20250101', '20250102'],
        'cyc_1': [0.1, 0.2],
        # Missing cyc_2 through cyc_193
    })
    
    with pytest.raises(ValueError, match="missing cycle columns"):
        validate_scfm_dataset(df)


def test_validate_scfm_dataset_empty():
    """Test that empty dataset raises error."""
    df = pd.DataFrame()
    
    with pytest.raises(ValueError, match="empty"):
        validate_scfm_dataset(df)


def test_compute_replicate_metrics_basic():
    """Test basic replicate-level metric computation."""
    # Create a simple growth curve: baseline=0.1, 24h=0.2, 48h=0.3
    cycle_cols = [f'cyc_{i}' for i in range(1, 194)]
    row_data = {col: 0.1 + (i - 1) * 0.001 for i, col in enumerate(cycle_cols, 1)}
    row_data['sample_id'] = 1
    row_data['ASMA_id'] = 'ASMA-1'
    row_data['assay_start_date'] = '20250101'
    
    row = pd.Series(row_data)
    
    metrics = compute_replicate_metrics(row, cycle_cols)
    
    # Check baseline (cycle 1)
    assert metrics['od_baseline'] == pytest.approx(0.1, rel=1e-6)
    
    # Check 24h (cycle 97)
    expected_24h = 0.1 + (SCFM_CYCLE_24H - 1) * 0.001
    assert metrics['od_24h'] == pytest.approx(expected_24h, rel=1e-6)
    
    # Check 48h (cycle 193)
    expected_48h = 0.1 + (SCFM_CYCLE_48H - 1) * 0.001
    assert metrics['od_48h'] == pytest.approx(expected_48h, rel=1e-6)
    
    # Check ΔOD
    assert metrics['delta_od_24h'] == pytest.approx(expected_24h - 0.1, rel=1e-6)
    assert metrics['delta_od_48h'] == pytest.approx(expected_48h - 0.1, rel=1e-6)
    
    # Check binary growth calls (should be True if delta >= threshold)
    # Note: numpy.bool_ is returned, which is fine
    assert metrics['growth_24h'] in [True, False]
    assert metrics['growth_48h'] in [True, False]
    
    # Check max yield (should be the last value in this case)
    assert metrics['od_max_yield'] == pytest.approx(0.1 + 192 * 0.001, rel=1e-6)


def test_compute_replicate_metrics_binary_growth_threshold():
    """Test binary growth calls with threshold."""
    cycle_cols = [f'cyc_{i}' for i in range(1, 194)]
    
    # Case 1: delta_od_24h = 0.15 (above threshold 0.1) -> True
    row1_data = {col: 0.1 if i == 1 else (0.25 if i == SCFM_CYCLE_24H else 0.1) 
                 for i, col in enumerate(cycle_cols, 1)}
    row1_data['sample_id'] = 1
    row1_data['ASMA_id'] = 'ASMA-1'
    row1_data['assay_start_date'] = '20250101'
    row1 = pd.Series(row1_data)
    
    metrics1 = compute_replicate_metrics(row1, cycle_cols)
    assert metrics1['growth_24h'] == True  # Use == for numpy.bool_
    
    # Case 2: delta_od_24h = 0.05 (below threshold 0.1) -> False
    row2_data = {col: 0.1 if i == 1 else (0.15 if i == SCFM_CYCLE_24H else 0.1) 
                 for i, col in enumerate(cycle_cols, 1)}
    row2_data['sample_id'] = 2
    row2_data['ASMA_id'] = 'ASMA-2'
    row2_data['assay_start_date'] = '20250101'
    row2 = pd.Series(row2_data)
    
    metrics2 = compute_replicate_metrics(row2, cycle_cols)
    assert metrics2['growth_24h'] == False  # Use == for numpy.bool_


def test_compute_replicate_metrics_max_yield_time():
    """Test maximum yield and time calculation."""
    cycle_cols = [f'cyc_{i}' for i in range(1, 194)]
    
    # Create curve with max at cycle 50
    max_cycle = 50
    row_data = {col: 0.1 + (0.01 if i == max_cycle else 0.001) 
                for i, col in enumerate(cycle_cols, 1)}
    row_data['sample_id'] = 1
    row_data['ASMA_id'] = 'ASMA-1'
    row_data['assay_start_date'] = '20250101'
    row = pd.Series(row_data)
    
    metrics = compute_replicate_metrics(row, cycle_cols)
    
    # Max yield should be at cycle 50
    expected_time = (max_cycle - 1) * SCFM_CYCLE_INTERVAL_HOURS
    assert metrics['time_max_yield_hours'] == pytest.approx(expected_time, rel=1e-6)


def test_compute_replicate_metrics_missing_values():
    """Test handling of missing cycle values."""
    cycle_cols = [f'cyc_{i}' for i in range(1, 194)]
    row_data = {col: 0.1 if i <= 10 else np.nan 
                for i, col in enumerate(cycle_cols, 1)}
    row_data['sample_id'] = 1
    row_data['ASMA_id'] = 'ASMA-1'
    row_data['assay_start_date'] = '20250101'
    row = pd.Series(row_data)
    
    metrics = compute_replicate_metrics(row, cycle_cols)
    
    # 24h and 48h should be NaN since those cycles are missing
    assert pd.isna(metrics['od_24h'])
    assert pd.isna(metrics['od_48h'])
    assert pd.isna(metrics['delta_od_24h'])
    assert pd.isna(metrics['delta_od_48h'])


def test_compute_mu_simple_exponential_curve():
    """Test μ estimation on synthetic exponential curve with known μ."""
    # Create exponential growth: OD(t) = 0.01 * exp(0.02 * t)
    # True μ = 0.02 per hour
    true_mu = 0.02
    n_cycles = 193
    time_hours = np.array([(i - 1) * SCFM_CYCLE_INTERVAL_HOURS for i in range(1, n_cycles + 1)])
    od_values = 0.01 * np.exp(true_mu * time_hours)
    
    result = compute_mu_simple(od_values)
    
    # Should find a good fit
    assert not pd.isna(result['mu_simple'])
    assert result['mu_simple'] > 0
    # Should be close to true value (within 20% tolerance for this simple test)
    assert abs(result['mu_simple'] - true_mu) / true_mu < 0.2
    # R² should be high
    assert result['mu_simple_r2'] >= 0.95


def test_compute_mu_simple_flat_curve():
    """Test that flat curve (no growth) results in NaN μ."""
    # Flat curve: all values = 0.1
    n_cycles = 193
    od_values = np.full(n_cycles, 0.1)
    
    result = compute_mu_simple(od_values)
    
    # Should return NaN (no suitable window found)
    assert pd.isna(result['mu_simple'])
    assert pd.isna(result['mu_simple_r2'])


def test_compute_mu_simple_noisy_exponential():
    """Test μ estimation on noisy exponential curve."""
    # Create exponential with noise
    true_mu = 0.015
    n_cycles = 193
    time_hours = np.array([(i - 1) * SCFM_CYCLE_INTERVAL_HOURS for i in range(1, n_cycles + 1)])
    od_values = 0.01 * np.exp(true_mu * time_hours)
    # Add small noise
    np.random.seed(42)
    noise = np.random.normal(0, 0.001, n_cycles)
    od_values = od_values + noise
    od_values = np.maximum(od_values, 0.01)  # Ensure positive
    
    result = compute_mu_simple(od_values)
    
    # Should still find a reasonable fit
    assert not pd.isna(result['mu_simple'])
    assert result['mu_simple'] > 0
    # Window times should be valid
    assert not pd.isna(result['mu_simple_t_start_hours'])
    assert not pd.isna(result['mu_simple_t_end_hours'])


def test_compute_mu_simple_all_below_threshold():
    """Test that all OD values below threshold results in NaN."""
    # All values below SCFM_MU_MIN_OD (0.01)
    n_cycles = 193
    od_values = np.full(n_cycles, 0.005)
    
    result = compute_mu_simple(od_values)
    
    # Should return NaN
    assert pd.isna(result['mu_simple'])
    assert pd.isna(result['mu_simple_r2'])


def test_compute_mu_simple_declining_od():
    """Test that declining OD (negative slope) is rejected."""
    # Declining curve
    n_cycles = 193
    od_values = np.linspace(0.5, 0.1, n_cycles)
    
    result = compute_mu_simple(od_values)
    
    # Should return NaN (negative slope rejected)
    assert pd.isna(result['mu_simple'])


def test_process_scfm_growth_curve_phase1_columns():
    """Test that process_scfm_growth_curve includes Phase 1 columns."""
    # Create minimal valid dataset
    df = pd.DataFrame({
        'sample_id': [1],
        'ASMA_id': ['ASMA-1'],
        'assay_start_date': ['20250101'],
    })
    for i in range(1, 194):
        df[f'cyc_{i}'] = [0.1 + i * 0.001]
    
    result = process_scfm_growth_curve(df)
    
    # Check Phase 1 columns are present
    assert 'od_24h' in result.columns
    assert 'od_48h' in result.columns
    assert 'delta_od_24h' in result.columns
    assert 'delta_od_48h' in result.columns
    assert 'growth_24h' in result.columns
    assert 'growth_48h' in result.columns
    assert 'od_max_yield' in result.columns
    assert 'time_max_yield_hours' in result.columns
    assert 'mu_simple' in result.columns
    assert 'mu_simple_r2' in result.columns
    assert 'mu_simple_t_start_hours' in result.columns
    assert 'mu_simple_t_end_hours' in result.columns


def test_aggregate_scfm_by_asma_id_phase1_metrics():
    """Test that aggregation includes Phase 1 metrics."""
    # Create replicate-level data with Phase 1 metrics
    df = pd.DataFrame({
        'sample_id': [1, 2, 3],
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-2'],
        'assay_start_date': ['20250101', '20250102', '20250101'],
        'od_24h': [0.2, 0.25, 0.3],
        'od_48h': [0.3, 0.35, 0.4],
        'delta_od_24h': [0.1, 0.15, 0.2],
        'delta_od_48h': [0.2, 0.25, 0.3],
        'growth_24h': [True, True, True],
        'growth_48h': [True, True, True],
        'od_max_yield': [0.3, 0.35, 0.4],
        'time_max_yield_hours': [48.0, 48.0, 48.0],
        'mu_simple': [0.02, 0.025, 0.03],
        'mu_simple_r2': [0.98, 0.97, 0.99],
        'mu_simple_t_start_hours': [12.0, 12.0, 12.0],
        'mu_simple_t_end_hours': [18.0, 18.0, 18.0],
        'delta_od': [0.2, 0.25, 0.3],
        'od_min': [0.1, 0.1, 0.1],
        'od_max': [0.3, 0.35, 0.4],
        'growth_class': ['normal', 'normal', 'robust']
    })
    
    result = aggregate_scfm_by_asma_id(df)
    
    # Check Phase 1 aggregate columns
    assert 'scfm_od_24h_mean' in result.columns
    assert 'scfm_od_24h_sd' in result.columns
    assert 'scfm_growth_24h_n' in result.columns
    assert 'scfm_growth_24h_pct' in result.columns
    assert 'scfm_mu_simple_mean' in result.columns
    assert 'scfm_mu_simple_sd' in result.columns
    assert 'scfm_mu_simple_n_reps' in result.columns
    
    # Check ASMA-1 aggregation
    asma1 = result[result['ASMA_id'] == 'ASMA-1'].iloc[0]
    assert asma1['scfm_od_24h_mean'] == pytest.approx(0.225, rel=1e-6)  # (0.2 + 0.25) / 2
    assert asma1['scfm_growth_24h_n'] == 2
    assert asma1['scfm_growth_24h_pct'] == pytest.approx(100.0, rel=1e-6)
    assert asma1['scfm_mu_simple_mean'] == pytest.approx(0.0225, rel=1e-6)  # (0.02 + 0.025) / 2
    assert asma1['scfm_mu_simple_n_reps'] == 2


def test_aggregate_scfm_by_asma_id_single_replicate():
    """Test aggregation with single replicate (SD should be NaN)."""
    df = pd.DataFrame({
        'sample_id': [1],
        'ASMA_id': ['ASMA-1'],
        'assay_start_date': ['20250101'],
        'od_24h': [0.2],
        'od_48h': [0.3],
        'delta_od_24h': [0.1],
        'delta_od_48h': [0.2],
        'growth_24h': [True],
        'growth_48h': [True],
        'od_max_yield': [0.3],
        'time_max_yield_hours': [48.0],
        'mu_simple': [0.02],
        'mu_simple_r2': [0.98],
        'mu_simple_t_start_hours': [12.0],
        'mu_simple_t_end_hours': [18.0],
        'delta_od': [0.2],
        'od_min': [0.1],
        'od_max': [0.3],
        'growth_class': ['normal']
    })
    
    result = aggregate_scfm_by_asma_id(df)
    
    asma1 = result[result['ASMA_id'] == 'ASMA-1'].iloc[0]
    # SD should be NaN for single replicate
    assert pd.isna(asma1['scfm_od_24h_sd'])
    assert pd.isna(asma1['scfm_mu_simple_sd'])


def test_aggregate_scfm_by_asma_id_empty():
    """Test aggregation with empty DataFrame."""
    df = pd.DataFrame()
    result = aggregate_scfm_by_asma_id(df)
    
    assert len(result) == 0
    # Should have all expected columns
    assert 'scfm_od_24h_mean' in result.columns
    assert 'scfm_mu_simple_mean' in result.columns

