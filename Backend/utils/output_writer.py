"""
Output Writer Utility

This module provides functionality to write only API payloads and responses to the outputs folder
for debugging and testing purposes. Only essential data (payload and response) is written.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Base output directory
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"

def ensure_output_dir():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(exist_ok=True)

def write_api_data(
    service_name: str,
    request_id: str,
    payload: Dict[str, Any],
    response: Dict[str, Any],
    endpoint: str = None
) -> None:
    """
    Write only API payload and response data to the outputs folder.

    Args:
        service_name: Name of the service (e.g., 'AirShopping', 'FlightPrice', 'OrderCreate')
        request_id: Unique request identifier
        payload: Request payload data
        response: Response data
        endpoint: Optional endpoint path for additional context
    """
    try:
        ensure_output_dir()

        # Create timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean request_id for filename (remove special characters)
        clean_request_id = "".join(c for c in request_id if c.isalnum() or c in ('-', '_'))[:20]

        # Create base filename
        base_filename = f"{service_name}_{timestamp}_{clean_request_id}"

        # Write payload
        payload_file = OUTPUT_DIR / f"{base_filename}_payload.json"
        with open(payload_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

        # Write response
        response_file = OUTPUT_DIR / f"{base_filename}_response.json"
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"API payload and response written - Service: {service_name}, "
                   f"Request ID: {request_id}, Files: {base_filename}_payload.json, {base_filename}_response.json")

    except Exception as e:
        logger.error(f"Failed to write API data to outputs folder - Service: {service_name}, "
                    f"Request ID: {request_id}, Error: {e}")

def write_payload_only(
    service_name: str,
    request_id: str,
    payload: Dict[str, Any],
    endpoint: str = None
) -> None:
    """
    Write only the API payload to the outputs folder.
    
    Args:
        service_name: Name of the service
        request_id: Unique request identifier
        payload: Request payload data
        endpoint: Optional endpoint path for additional context
    """
    try:
        ensure_output_dir()
        
        # Create timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean request_id for filename
        clean_request_id = "".join(c for c in request_id if c.isalnum() or c in ('-', '_'))[:20]
        
        # Create filename
        filename = f"{service_name}_{timestamp}_{clean_request_id}_payload.json"
        file_path = OUTPUT_DIR / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"API payload written to outputs folder - Service: {service_name}, "
                   f"Request ID: {request_id}, File: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to write API payload to outputs folder - Service: {service_name}, "
                    f"Request ID: {request_id}, Error: {e}")

def write_response_only(
    service_name: str,
    request_id: str,
    response: Dict[str, Any],
    endpoint: str = None
) -> None:
    """
    Write only the API response to the outputs folder.
    
    Args:
        service_name: Name of the service
        request_id: Unique request identifier
        response: Response data
        endpoint: Optional endpoint path for additional context
    """
    try:
        ensure_output_dir()
        
        # Create timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean request_id for filename
        clean_request_id = "".join(c for c in request_id if c.isalnum() or c in ('-', '_'))[:20]
        
        # Create filename
        filename = f"{service_name}_{timestamp}_{clean_request_id}_response.json"
        file_path = OUTPUT_DIR / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"API response written to outputs folder - Service: {service_name}, "
                   f"Request ID: {request_id}, File: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to write API response to outputs folder - Service: {service_name}, "
                    f"Request ID: {request_id}, Error: {e}")


