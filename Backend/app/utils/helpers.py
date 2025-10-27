"""Helper utility functions."""

from typing import Any, List, Union
from datetime import datetime, date


def normalize_to_list(value: Union[Any, List[Any]]) -> List[Any]:
    """
    Normalize a value to a list.
    
    Args:
        value: Single value or list of values
        
    Returns:
        List containing the value(s)
        
    Examples:
        >>> normalize_to_list("A")
        ["A"]
        >>> normalize_to_list(["A", "B"])
        ["A", "B"]
    """
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def format_date(dt: Union[date, datetime, str]) -> str:
    """
    Format date to YYYY-MM-DD string.
    
    Args:
        dt: Date, datetime, or string
        
    Returns:
        Formatted date string
    """
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    if isinstance(dt, date):
        return dt.strftime("%Y-%m-%d")
    raise ValueError(f"Invalid date type: {type(dt)}")


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search
        *keys: Sequence of keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at key path or default
        
    Examples:
        >>> safe_get({"a": {"b": {"c": 1}}}, "a", "b", "c")
        1
        >>> safe_get({"a": {"b": {}}}, "a", "b", "c", default=0)
        0
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default
