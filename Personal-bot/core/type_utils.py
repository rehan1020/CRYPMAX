# Type annotation utilities for CryptoPulse project
from typing import Optional, Union, Any, Dict, List
from datetime import datetime

def safe_float(value: Any) -> float:
    """Safely convert any value to float"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_str(value: Any) -> str:
    """Safely convert any value to string"""
    if value is None:
        return ""
    try:
        return str(value)
    except (ValueError, TypeError):
        return ""

def safe_datetime_str(value: Any) -> Optional[str]:
    """Safely convert datetime to ISO format string"""
    if value is None:
        return None
    
    # Handle datetime object
    if isinstance(value, datetime):
        return value.isoformat()
    
    # Handle string representation
    return str(value)

def safe_bool(value: Any) -> bool:
    """Safely convert any value to bool"""
    if value is None:
        return False
    
    return bool(value)

# Import safety helpers
def safe_import(module_name: str, fallback_value: Any = None):
    """Safely import a module with fallback"""
    try:
        return __import__(module_name)
    except ImportError:
        return fallback_value

# Common fixes for external library issues
EXCHANGE_IMPORT_FIXES = {
    'bitget': 'from bitget.client import Client'
}

def create_safe_exchange_import(exchange_name: str) -> str:
    """Create safe import statement for exchange"""
    import_stmt = EXCHANGE_IMPORT_FIXES.get(exchange_name, '')
    
    return f"""
try:
    {import_stmt}
    {exchange_name.upper()}_AVAILABLE = True
except ImportError:
    {exchange_name.upper()}_AVAILABLE = False
    Client = None
"""

print("Type utilities created successfully!")
print("Use these functions to safely handle type conversions and imports.")