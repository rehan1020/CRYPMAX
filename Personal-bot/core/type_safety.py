# bot/type_safety.py
"""
Type safety utilities for handling pandas/numpy type conversions
"""

import numpy as np
import pandas as pd
from typing import Union, Any


def safe_array_conversion(data: Any, dtype=np.float64) -> np.ndarray:
    """Safely convert pandas Series/DataFrame values to numpy array"""
    try:
        if hasattr(data, 'values'):
            return np.array(data.values, dtype=dtype)
        else:
            return np.array(data, dtype=dtype)
    except (ValueError, TypeError):
        # Fallback for problematic data
        if hasattr(data, 'values'):
            return np.array(data.values, dtype=np.float64)
        return np.array(data, dtype=np.float64)


def safe_float_conversion(value: Any) -> float:
    """Safely convert any numeric value to float"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif hasattr(value, 'item'):  # numpy scalar
            return float(value.item())
        elif isinstance(value, (list, tuple, np.ndarray)) and len(value) > 0:
            return float(value[0])
        else:
            return float(value)  # type: ignore
    except (ValueError, TypeError, IndexError):
        return 0.0


def safe_pandas_access(series_or_df: Union[pd.Series, pd.DataFrame], index: int = -1) -> float:
    """Safely access pandas Series or DataFrame values"""
    try:
        if isinstance(series_or_df, pd.Series):
            if len(series_or_df) > abs(index):
                return float(series_or_df.iloc[index])
            return 0.0
        elif isinstance(series_or_df, pd.DataFrame):
            if not series_or_df.empty and len(series_or_df) > abs(index):
                return float(series_or_df.iloc[index, 0])
            return 0.0
        elif hasattr(series_or_df, '__getitem__'):
            return float(series_or_df[index])
        else:
            return float(series_or_df)
    except (IndexError, ValueError, TypeError):
        return 0.0