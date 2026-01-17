"""
Data loading functions for UICT v1 ETL pipeline.
"""

import pandas as pd
from pathlib import Path
from typing import Dict


def load_taxonomy_table(filepath: str) -> pd.DataFrame:
    """
    Load taxonomy TSV file and validate required columns.
    
    Args:
        filepath: Path to taxonomy.tsv file
        
    Returns:
        DataFrame with taxonomy data, filtered to remove rows with missing ASMA_id
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Taxonomy file not found: {filepath}")
    
    df = pd.read_csv(filepath, sep='\t')
    
    # Validate required columns
    required_cols = ['ASMA_id', 'domain', 'phylum', 'class', 'order', 'family', 'genus', 'species']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in taxonomy file: {missing_cols}")
    
    # Filter out rows with missing ASMA_id
    df = df[df['ASMA_id'].notna()].copy()
    
    return df


def load_phenotype_excel(filepath: str) -> Dict[str, pd.DataFrame]:
    """
    Load phenotype Excel file and return all sheets as a dictionary.
    
    Args:
        filepath: Path to phenotype Excel file
        
    Returns:
        Dictionary with sheet names as keys and DataFrames as values
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Phenotype file not found: {filepath}")
    
    # Load all sheets
    excel_file = pd.ExcelFile(filepath)
    sheets = {}
    
    for sheet_name in excel_file.sheet_names:
        sheets[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    return sheets


def validate_taxonomy_data(df: pd.DataFrame) -> bool:
    """
    Validate taxonomy DataFrame structure.
    
    Args:
        df: Taxonomy DataFrame
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    if df.empty:
        raise ValueError("Taxonomy DataFrame is empty")
    
    if 'ASMA_id' not in df.columns:
        raise ValueError("Taxonomy DataFrame missing 'ASMA_id' column")
    
    if df['ASMA_id'].isna().any():
        raise ValueError("Taxonomy DataFrame contains rows with missing ASMA_id")
    
    return True


def validate_phenotype_data(sheets: Dict[str, pd.DataFrame]) -> bool:
    """
    Validate phenotype sheets structure.
    
    Args:
        sheets: Dictionary of sheet names to DataFrames
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    expected_sheets = ['SCFM_growth_curve', 'pairwise_interaction', 
                       'inhibition_standard_control', 'carbon_utilization']
    
    missing_sheets = [s for s in expected_sheets if s not in sheets]
    if missing_sheets:
        raise ValueError(f"Missing expected phenotype sheets: {missing_sheets}")
    
    return True


def filter_blank_rows(df: pd.DataFrame, asma_id_col: str = 'ASMA_id') -> pd.DataFrame:
    """
    Filter out rows where ASMA_id is "BLANK".
    
    Args:
        df: DataFrame to filter
        asma_id_col: Name of the ASMA_id column
        
    Returns:
        DataFrame with BLANK rows removed
    """
    if asma_id_col not in df.columns:
        return df
    
    return df[df[asma_id_col] != "BLANK"].copy()

