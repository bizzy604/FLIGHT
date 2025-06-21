"""
Utility functions for the Flight Service.

This module contains helper functions used across the flight service modules.
"""
from typing import Dict, Any, Optional, List, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def format_date(date_str: str, input_format: str = '%Y-%m-%d', output_format: str = '%Y-%m-%d') -> str:
    """
    Format a date string from one format to another.
    
    Args:
        date_str: Input date string
        input_format: Format of the input date string (default: '%Y-%m-%d')
        output_format: Desired output format (default: '%Y-%m-%d')
        
    Returns:
        Formatted date string
    """
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error formatting date '{date_str}': {str(e)}")
        return date_str

def deep_get(dictionary: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get a value from a nested dictionary using a list of keys.
    
    Args:
        dictionary: The dictionary to search in
        keys: List of keys representing the path to the desired value
        default: Default value to return if the path doesn't exist
        
    Returns:
        The value at the specified path or the default value
    """
    if not isinstance(dictionary, dict) or not keys:
        return default
        
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that all required fields are present in the data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of error messages for missing fields
    """
    errors = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors.append(f"Missing required field: {field}")
    return errors

def mask_sensitive_data(data: Union[Dict, str], fields_to_mask: List[str] = None) -> Union[Dict, str]:
    """
    Mask sensitive data in a dictionary or string.
    
    Args:
        data: Input data (dict or str)
        fields_to_mask: List of field names to mask (default: common sensitive fields)
        
    Returns:
        Data with sensitive fields masked
    """
    if fields_to_mask is None:
        fields_to_mask = [
            'password', 'api_key', 'api_secret', 'auth_token',
            'card_number', 'cvv', 'expiry_date', 'card_holder_name'
        ]
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(key, str) and any(field.lower() in key.lower() for field in fields_to_mask):
                result[key] = '***MASKED***'
            elif isinstance(value, (dict, list)):
                result[key] = mask_sensitive_data(value, fields_to_mask)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [mask_sensitive_data(item, fields_to_mask) for item in data]
    elif isinstance(data, str) and any(field in data.lower() for field in fields_to_mask):
        return '***MASKED***'
    return data

def generate_request_id(prefix: str = 'req') -> str:
    """
    Generate a unique request ID.
    
    Args:
        prefix: Optional prefix for the request ID
        
    Returns:
        A unique request ID string
    """
    import uuid
    from datetime import datetime
    
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4().hex)[:8]
    return f"{prefix}_{timestamp}_{unique_id}"

def parse_boolean(value: Any) -> bool:
    """
    Safely parse a boolean value from various input types.
    
    Args:
        value: Input value to parse
        
    Returns:
        Boolean representation of the input value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', 't', '1', 'yes', 'y')
    if isinstance(value, (int, float)):
        return bool(value)
    return False
