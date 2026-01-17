"""
Tests for PA inhibition processing.
"""

import pandas as pd
import pytest
from etl.inhibition import (
    process_inhibition_control,
    process_pairwise_interactions,
    classify_inhibition_class,
    aggregate_pa_inhibition_by_asma_id
)


def test_classify_inhibition_class():
    """Test inhibition class mapping."""
    assert classify_inhibition_class(10.0) == "none"   # < 25
    assert classify_inhibition_class(25.0) == "weak"   # 25 <= x < 50
    assert classify_inhibition_class(30.0) == "weak"
    assert classify_inhibition_class(50.0) == "strong" # >= 50
    assert classify_inhibition_class(75.0) == "strong"
    assert classify_inhibition_class(pd.NA) == "none"


def test_process_inhibition_control():
    """Test control data processing."""
    df = pd.DataFrame({
        'sample_id': [1, 2, 3, 4],
        'ASMA_id': ['REP1', 'REP2', 'REP3', 'REP4'],
        'type': ['reporter', 'reporter', 'reporter', 'other'],
        'assay_start_date': ['20250101', '20250101', '20250102', '20250101'],
        'starting_OD': [0.001, 0.001, 0.001, 0.001],
        'gain': [150, 150, 150, 150],
        'raw_RFU': [1000, 1100, 1200, 1300],
    })
    
    result = process_inhibition_control(df)
    
    assert len(result) == 1
    assert result.iloc[0]['starting_OD'] == 0.001
    # Mean of 1000, 1100, 1200 = 1100
    assert result.iloc[0]['rfu_reporter_mean'] == pytest.approx(1100, rel=1e-3)


def test_process_pairwise_interactions():
    """Test pairwise interaction processing with 100:1 ratio detection."""
    # Control data
    control_df = pd.DataFrame({
        'starting_OD': [0.001],
        'rfu_reporter_mean': [1000.0]
    })
    
    # Pairwise data with exact 100:1 ratio
    pairwise_df = pd.DataFrame({
        'sample_id': [1, 2],
        'bacterium_1_ASMA_id': ['ASMA-1', 'ASMA-1'],
        'bacterium_2_ASMA_id': ['PA14_KEH108_Reporter', 'PA14_KEH108_Reporter'],
        'assay_start_date': ['20250101', '20250102'],
        'bacterium_1_starting_OD': [0.1, 0.1],
        'bacterium_2_starting_OD': [0.001, 0.001],
        'gain': [150, 150],
        'raw_RFU': [500, 600],  # 50% and 40% inhibition
    })
    
    result = process_pairwise_interactions(pairwise_df, control_df)
    
    assert len(result) == 2
    assert all(result['ASMA_id'] == 'ASMA-1')
    
    # Check inhibition percentages
    # inhibition_pct = 100 - (raw_RFU / rfu_reporter_mean) * 100
    # Row 1: 100 - (500/1000)*100 = 50
    # Row 2: 100 - (600/1000)*100 = 40
    assert result.iloc[0]['inhibition_pct'] == pytest.approx(50.0, rel=1e-3)
    assert result.iloc[1]['inhibition_pct'] == pytest.approx(40.0, rel=1e-3)


def test_aggregate_pa_inhibition_by_asma_id():
    """Test PA inhibition aggregation."""
    df = pd.DataFrame({
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-2'],
        'inhibition_pct': [50.0, 40.0, 20.0],
        'pa_starting_od': [0.001, 0.001, 0.001],
        'assay_start_date': ['20250101', '20250102', '20250101'],
    })
    
    result = aggregate_pa_inhibition_by_asma_id(df)
    
    assert len(result) == 2
    
    # Check ASMA-1: mean of 50 and 40 = 45, which is "weak"
    asma1 = result[result['ASMA_id'] == 'ASMA-1'].iloc[0]
    assert asma1['inhib_100x_n'] == 2
    assert asma1['inhib_100x_mean'] == pytest.approx(45.0, rel=1e-3)
    assert asma1['pa_inhibition_class'] == "weak"
    
    # Check ASMA-2: mean of 20 = 20, which is "none"
    asma2 = result[result['ASMA_id'] == 'ASMA-2'].iloc[0]
    assert asma2['inhib_100x_n'] == 1
    assert asma2['inhib_100x_mean'] == pytest.approx(20.0, rel=1e-3)
    assert asma2['pa_inhibition_class'] == "none"

