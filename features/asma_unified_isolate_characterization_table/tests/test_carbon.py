"""
Tests for carbon utilization processing.
"""

import pandas as pd
import pytest
from etl.carbon import process_carbon_utilization


def test_carbon_utilization_utilizes():
    """Test carbon utilization call: utilizes."""
    # Create data where mean_C > mean_no_carbon + 2*sd_no_carbon
    df = pd.DataFrame({
        'sample_id': [1, 2, 3],
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-1'],
        'assay_start_date': ['20250101', '20250101', '20250101'],
        'No_carbon': [0.1, 0.12, 0.11],  # mean=0.11, sd≈0.008
        'Glucose': [0.2, 0.21, 0.19],   # mean=0.20, clearly > 0.11 + 2*0.008 = 0.126
    })
    
    result = process_carbon_utilization(df)
    
    assert len(result) == 1
    assert result.iloc[0]['ASMA_id'] == 'ASMA-1'
    assert result.iloc[0]['glucose_utilization_call'] == "utilizes"


def test_carbon_utilization_no_growth():
    """Test carbon utilization call: no_growth."""
    # Create data where mean_C <= mean_no_carbon + 2*sd_no_carbon
    df = pd.DataFrame({
        'sample_id': [1, 2, 3],
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-1'],
        'assay_start_date': ['20250101', '20250101', '20250101'],
        'No_carbon': [0.1, 0.12, 0.11],  # mean=0.11, sd≈0.008
        'Glucose': [0.11, 0.12, 0.11],   # mean=0.113, not > 0.126
    })
    
    result = process_carbon_utilization(df)
    
    assert len(result) == 1
    assert result.iloc[0]['glucose_utilization_call'] == "no_growth"


def test_carbon_utilization_uncertain():
    """Test carbon utilization call: uncertain (insufficient replicates)."""
    # Create data with < 3 replicates
    df = pd.DataFrame({
        'sample_id': [1, 2],
        'ASMA_id': ['ASMA-1', 'ASMA-1'],
        'assay_start_date': ['20250101', '20250101'],
        'No_carbon': [0.1, 0.12],
        'Glucose': [0.2, 0.21],
    })
    
    result = process_carbon_utilization(df)
    
    assert len(result) == 1
    assert result.iloc[0]['glucose_utilization_call'] == "uncertain"


def test_carbon_utilization_filters_blank():
    """Test that BLANK rows are filtered out."""
    df = pd.DataFrame({
        'sample_id': [1, 2],
        'ASMA_id': ['ASMA-1', 'BLANK'],
        'assay_start_date': ['20250101', '20250101'],
        'No_carbon': [0.1, 0.1],
        'Glucose': [0.2, 0.2],
    })
    
    result = process_carbon_utilization(df)
    
    assert len(result) == 1
    assert result.iloc[0]['ASMA_id'] == 'ASMA-1'


def test_carbon_utilization_date_aware():
    """Test that carbon utilization respects assay_date."""
    # Create data with two different dates
    # Date 1: Glucose utilizes
    # Date 2: Glucose does not utilize
    # Final result should be "utilizes" (if ANY date passes)
    df = pd.DataFrame({
        'sample_id': [1, 2, 3, 4, 5, 6],
        'ASMA_id': ['ASMA-1', 'ASMA-1', 'ASMA-1', 'ASMA-1', 'ASMA-1', 'ASMA-1'],
        'assay_start_date': ['20250101', '20250101', '20250101', '20250102', '20250102', '20250102'],
        'No_carbon': [0.1, 0.12, 0.11, 0.1, 0.12, 0.11],
        'Glucose': [0.2, 0.21, 0.19,  # Date 1: utilizes
                    0.11, 0.12, 0.11], # Date 2: no_growth
    })
    
    result = process_carbon_utilization(df)
    
    assert len(result) == 1
    # Should be "utilizes" because Date 1 passes threshold
    assert result.iloc[0]['glucose_utilization_call'] == "utilizes"

