"""
Tests for SCFM growth processing.
"""

import pandas as pd
import pytest
from etl.scfm import classify_growth_class, process_scfm_growth_curve, aggregate_scfm_by_asma_id


def test_classify_growth_class():
    """Test SCFM growth class thresholds."""
    # Test thresholds
    assert classify_growth_class(0.03) == "no_growth"  # < 0.05
    assert classify_growth_class(0.05) == "poor"       # 0.05 <= x < 0.1
    assert classify_growth_class(0.07) == "poor"
    assert classify_growth_class(0.1) == "normal"      # 0.1 <= x < 0.2
    assert classify_growth_class(0.15) == "normal"
    assert classify_growth_class(0.2) == "robust"       # >= 0.2
    assert classify_growth_class(0.5) == "robust"


def test_process_scfm_growth_curve():
    """Test SCFM growth curve processing."""
    # Create synthetic data
    df = pd.DataFrame({
        'sample_id': [1, 2, 3],
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-2'],
        'assay_start_date': ['20250101', '20250102', '20250101'],
        'cyc_1': [0.1, 0.1, 0.1],
        'cyc_2': [0.2, 0.15, 0.3],
        'cyc_3': [0.3, 0.2, 0.5],
    })
    
    result = process_scfm_growth_curve(df)
    
    assert len(result) == 3
    assert 'delta_od' in result.columns
    assert 'growth_class' in result.columns
    
    # Check first row: min=0.1, max=0.3, delta=0.2 -> "normal"
    assert result.iloc[0]['od_min'] == 0.1
    assert result.iloc[0]['od_max'] == 0.3
    assert result.iloc[0]['delta_od'] == pytest.approx(0.2, rel=1e-6)
    assert result.iloc[0]['growth_class'] == "normal"


def test_process_scfm_filters_blank():
    """Test that BLANK rows are filtered out."""
    df = pd.DataFrame({
        'sample_id': [1, 2],
        'ASMA_id': ['ASMA-1', 'BLANK'],
        'assay_start_date': ['20250101', '20250101'],
        'cyc_1': [0.1, 0.1],
        'cyc_2': [0.2, 0.2],
    })
    
    result = process_scfm_growth_curve(df)
    
    assert len(result) == 1
    assert result.iloc[0]['ASMA_id'] == 'ASMA-1'


def test_aggregate_scfm_by_asma_id():
    """Test SCFM aggregation by ASMA_id."""
    df = pd.DataFrame({
        'sample_id': [1, 2, 3],
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-2'],
        'assay_start_date': ['20250101', '20250102', '20250101'],
        'od_min': [0.1, 0.1, 0.1],
        'od_max': [0.3, 0.25, 0.5],
        'delta_od': [0.2, 0.15, 0.4],
        'growth_class': ['normal', 'normal', 'robust'],
    })
    
    result = aggregate_scfm_by_asma_id(df)
    
    assert len(result) == 2
    assert 'ASMA-1' in result['ASMA_id'].values
    assert 'ASMA-2' in result['ASMA_id'].values
    
    # Check ASMA-1 aggregation
    asma1 = result[result['ASMA_id'] == 'ASMA-1'].iloc[0]
    assert asma1['scfm_n_reps'] == 2
    assert asma1['scfm_delta_od_mean'] == 0.175  # (0.2 + 0.15) / 2
    assert asma1['scfm_delta_od_max'] == 0.2
    assert asma1['scfm_growth_class'] == "normal"  # 0.175 is in "normal" range

