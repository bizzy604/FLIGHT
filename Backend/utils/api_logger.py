"""API Request/Response Logging Utility

This module provides centralized logging functionality for API requests and responses
to help with debugging and monitoring API interactions.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class APILogger:
    """Centralized API request/response logger for debugging purposes."""
    
    def __init__(self, base_dir: str = "api_logs"):
        """
        Initialize the API logger.
        
        Args:
            base_dir: Base directory for storing API logs
        """
        self.base_dir = Path(base_dir)
        self.enabled = self._is_logging_enabled()
        
        if self.enabled:
            self._ensure_directories()
    
    def _is_logging_enabled(self) -> bool:
        """Check if API logging is enabled via environment variable."""
        return os.getenv('API_DEBUG_LOGGING', 'false').lower() in ('true', '1', 'yes', 'on')
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.base_dir,
            self.base_dir / "air_shopping",
            self.base_dir / "flight_price", 
            self.base_dir / "booking"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_service_dir(self, service_name: str) -> Path:
        """Get the directory for a specific service."""
        service_mapping = {
            'AirShopping': 'air_shopping',
            'FlightPrice': 'flight_price',
            'OrderCreate': 'booking'
        }
        
        service_dir = service_mapping.get(service_name, service_name.lower())
        return self.base_dir / service_dir
    
    def _generate_filename(self, service_name: str, request_id: str, data_type: str) -> str:
        """Generate a filename for the log entry."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{request_id}_{data_type}.json"
    
    def log_request(self, service_name: str, request_id: str, payload: Dict[str, Any], 
                   endpoint: str, headers: Dict[str, str]) -> None:
        """
        Log API request data.
        
        Args:
            service_name: Name of the service (AirShopping, FlightPrice, OrderCreate)
            request_id: Unique request identifier
            payload: Request payload
            endpoint: API endpoint
            headers: Request headers (sensitive data will be masked)
        """
        if not self.enabled:
            return
        
        try:
            service_dir = self._get_service_dir(service_name)
            filename = self._generate_filename(service_name, request_id, "request")
            filepath = service_dir / filename
            
            # Mask sensitive headers
            safe_headers = self._mask_sensitive_headers(headers)
            
            request_data = {
                "timestamp": datetime.now().isoformat(),
                "service": service_name,
                "request_id": request_id,
                "endpoint": endpoint,
                "headers": safe_headers,
                "payload": payload
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API request logged: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to log API request for {service_name}: {e}")
    
    def log_response(self, service_name: str, request_id: str, response: Dict[str, Any],
                    status_code: int, response_time_ms: Optional[float] = None) -> None:
        """
        Log API response data.
        
        Args:
            service_name: Name of the service
            request_id: Unique request identifier
            response: Response data
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
        """
        if not self.enabled:
            return
        
        try:
            service_dir = self._get_service_dir(service_name)
            filename = self._generate_filename(service_name, request_id, "response")
            filepath = service_dir / filename
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "service": service_name,
                "request_id": request_id,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "response": response
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API response logged: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to log API response for {service_name}: {e}")
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive information in headers."""
        sensitive_keys = ['authorization', 'thirdpartyid', 'officeid']
        safe_headers = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                if key.lower() == 'authorization' and value.startswith('Bearer '):
                    safe_headers[key] = f"Bearer ***{value[-8:]}"  # Show last 8 chars
                else:
                    safe_headers[key] = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                safe_headers[key] = value
        
        return safe_headers
    
    def cleanup_old_logs(self, days_to_keep: int = 7) -> None:
        """
        Clean up log files older than specified days.
        
        Args:
            days_to_keep: Number of days to keep log files
        """
        if not self.enabled or not self.base_dir.exists():
            return
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for log_file in self.base_dir.rglob("*.json"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger.info(f"Cleaned up old log file: {log_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")

# Global instance
api_logger = APILogger()
