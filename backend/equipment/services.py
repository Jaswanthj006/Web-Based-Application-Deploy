"""CSV parsing and analytics using Pandas."""
from __future__ import annotations
import pandas as pd
from pathlib import Path


EXPECTED_COLUMNS = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']
NUMERIC_COLUMNS = ['Flowrate', 'Pressure', 'Temperature']


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names (strip, handle common variants)."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    renames = {}
    for c in df.columns:
        lower = c.lower()
        if 'equipment' in lower and 'name' in lower:
            renames[c] = 'Equipment Name'
        elif c.lower() == 'type':
            renames[c] = 'Type'
        elif 'flow' in lower or c == 'Flowrate':
            renames[c] = 'Flowrate'
        elif 'pressure' in lower:
            renames[c] = 'Pressure'
        elif 'temp' in lower or 'temperature' in lower:
            renames[c] = 'Temperature'
    if renames:
        df = df.rename(columns=renames)
    return df


def parse_csv(file_path) -> tuple[pd.DataFrame, dict]:
    """
    Parse CSV and return (dataframe, summary_dict).
    Summary includes: total_count, averages (flowrate, pressure, temperature), type_distribution.
    """
    df = pd.read_csv(file_path)
    df = normalize_columns(df)

    # Ensure numeric columns are numeric
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    summary = {
        'total_count': len(df),
        'averages': {},
        'type_distribution': {},
    }

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            summary['averages'][col] = round(float(df[col].mean()), 2) if df[col].notna().any() else None

    if 'Type' in df.columns:
        summary['type_distribution'] = df['Type'].value_counts().to_dict()

    return df, summary


def dataframe_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts for API (NaN -> null)."""
    return df.fillna('').to_dict('records')
