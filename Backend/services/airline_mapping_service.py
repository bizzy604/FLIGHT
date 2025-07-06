"""
Airline Code Mapping Service

This module provides functionality to map airline codes to ThirdParty IDs and
manage airline-related configurations for NDC API calls. It follows PEP 8
standards and provides modular airline mapping capabilities.

Author: FLIGHT Application
Created: 2025-07-02
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AirlineMappingService:
    """
    Service class for mapping airline codes to ThirdParty IDs and managing
    airline-related configurations for NDC API interactions.
    """
    
    # Airline code to ThirdParty ID mappings
    # This mapping defines which ThirdParty ID to use for each airline in API calls
    AIRLINE_TO_THIRD_PARTY_ID = {
        # Major European Airlines
        'KL': 'KL',          # KLM Royal Dutch Airlines
        'AF': 'AF',          # Air France
        'LHG': 'LHG',        # Lufthansa Group
        
        # Middle Eastern Airlines
        'QR': 'QR',          # Qatar Airways
        'EK': 'EK',          # Emirates
        'EY': 'EY',          # Etihad Airways
        
        # African Airlines
        'KQ': 'KQ',          # Kenya Airways
        'ET': 'ET',          # Ethiopian Airlines
        
        # Asian Airlines
        '6E': '6E',          # IndiGo
        'IX': 'IX',          # Air India Express
        'TK': 'TK',          # Turkish Airlines
        'SQ': 'SQ',          # Singapore Airlines

        # Other Airlines
        'GF': 'GF',          # Gulf Air
        'BA': 'BA',          # British Airways
        'CX': 'CX',          # Cathay Pacific Airways
        'WY': 'WY',          # Oman Air
    }
    
    # Airline display names for user interfaces
    AIRLINE_DISPLAY_NAMES = {
        'KL': 'KLM Royal Dutch Airlines',
        'AF': 'Air France',
        'LHG': 'Lufthansa Group',
        'QR': 'Qatar Airways',
        'EK': 'Emirates',
        'EY': 'Etihad Airways',
        'KQ': 'Kenya Airways',
        'ET': 'Ethiopian Airlines',
        '6E': 'IndiGo',
        'IX': 'Air India Express',
        'TK': 'Turkish Airlines',
        'SQ': 'Singapore Airlines',
        'GF': 'Gulf Air',
        'BA': 'British Airways',
        'CX': 'Cathay Pacific Airways',
        'WY': 'Oman Air',
    }
    
    # Airline regions for grouping and filtering
    AIRLINE_REGIONS = {
        'Europe': ['KL', 'AF', 'LHG', 'BA'],
        'Middle East': ['QR', 'EK', 'EY', 'GF', 'WY'],
        'Africa': ['KQ', 'ET'],
        'Asia': ['6E', 'IX', 'TK', 'SQ', 'CX'],
    }
    
    # Airlines that support specific features
    FEATURE_SUPPORT = {
        'multi_airline_shopping': ['KL', 'AF', 'LHG', 'QR', 'EK', 'EY', 'KQ', 'ET', '6E', 'IX', 'TK', 'SQ', 'GF', 'BA', 'CX', 'WY'],
        'flight_pricing': ['KL', 'AF', 'LHG', 'QR', 'EK', 'EY', 'KQ', 'ET', '6E', 'IX', 'TK', 'SQ', 'GF', 'BA', 'CX', 'WY'],
        'order_creation': ['KL', 'AF', 'LHG', 'QR', 'EK', 'EY', 'KQ', 'ET', '6E', 'IX', 'TK', 'SQ', 'GF', 'BA', 'CX', 'WY'],
        'baggage_services': ['KL', 'AF', 'LHG', 'QR', 'EK', 'EY', 'KQ', 'ET', 'IX', 'BA', 'CX', 'WY'],
        'seat_selection': ['KL', 'AF', 'LHG', 'QR', 'EK', 'EY', 'IX', 'BA', 'CX'],
    }
    
    @classmethod
    def get_third_party_id(cls, airline_code: str) -> str:
        """
        Map airline code to ThirdParty ID for API calls.
        
        Args:
            airline_code (str): The airline code (e.g., 'KL', 'QR')
            
        Returns:
            str: The corresponding ThirdParty ID
        """
        if not airline_code:
            logger.warning("Empty airline code provided")
            return 'UNKNOWN'
        
        # Normalize airline code (uppercase, strip whitespace)
        normalized_code = airline_code.strip().upper()
        
        third_party_id = cls.AIRLINE_TO_THIRD_PARTY_ID.get(normalized_code)
        
        if third_party_id:
            logger.debug(f"Mapped airline code '{normalized_code}' to ThirdParty ID '{third_party_id}'")
            return third_party_id
        else:
            logger.warning(f"No ThirdParty ID mapping found for airline code '{normalized_code}'")
            return normalized_code  # Return the original code as fallback
    
    @classmethod
    def validate_airline_code(cls, airline_code: str) -> bool:
        """
        Validate if airline code is supported.
        
        Args:
            airline_code (str): The airline code to validate
            
        Returns:
            bool: True if airline is supported, False otherwise
        """
        if not airline_code:
            return False
        
        normalized_code = airline_code.strip().upper()
        is_valid = normalized_code in cls.AIRLINE_TO_THIRD_PARTY_ID
        
        if is_valid:
            logger.debug(f"Airline code '{normalized_code}' is valid")
        else:
            logger.debug(f"Airline code '{normalized_code}' is not supported (filtered out)")
        
        return is_valid
    
    @classmethod
    def get_supported_airlines(cls) -> List[str]:
        """
        Get list of all supported airline codes.
        
        Returns:
            List[str]: List of supported airline codes
        """
        return list(cls.AIRLINE_TO_THIRD_PARTY_ID.keys())
    
    @classmethod
    def get_airline_display_name(cls, airline_code: str) -> str:
        """
        Get display name for airline code.
        
        Args:
            airline_code (str): The airline code
            
        Returns:
            str: The airline display name
        """
        if not airline_code:
            return 'Unknown Airline'
        
        normalized_code = airline_code.strip().upper()
        display_name = cls.AIRLINE_DISPLAY_NAMES.get(normalized_code)
        
        if display_name:
            return display_name
        else:
            logger.warning(f"No display name found for airline code '{normalized_code}'")
            return f"Airline {normalized_code}"
    
    @classmethod
    def get_airlines_by_region(cls, region: str) -> List[str]:
        """
        Get airline codes for a specific region.
        
        Args:
            region (str): The region name (e.g., 'Europe', 'Middle East')
            
        Returns:
            List[str]: List of airline codes in the region
        """
        if not region:
            return []
        
        region_airlines = cls.AIRLINE_REGIONS.get(region, [])
        logger.debug(f"Found {len(region_airlines)} airlines in region '{region}'")
        return region_airlines.copy()
    
    @classmethod
    def get_all_regions(cls) -> List[str]:
        """
        Get list of all available regions.
        
        Returns:
            List[str]: List of region names
        """
        return list(cls.AIRLINE_REGIONS.keys())
    
    @classmethod
    def supports_feature(cls, airline_code: str, feature: str) -> bool:
        """
        Check if airline supports a specific feature.
        
        Args:
            airline_code (str): The airline code
            feature (str): The feature name
            
        Returns:
            bool: True if airline supports the feature, False otherwise
        """
        if not airline_code or not feature:
            return False
        
        normalized_code = airline_code.strip().upper()
        feature_airlines = cls.FEATURE_SUPPORT.get(feature, [])
        
        supports = normalized_code in feature_airlines
        logger.debug(f"Airline '{normalized_code}' {'supports' if supports else 'does not support'} feature '{feature}'")
        
        return supports
    
    @classmethod
    def get_airlines_supporting_feature(cls, feature: str) -> List[str]:
        """
        Get list of airlines that support a specific feature.
        
        Args:
            feature (str): The feature name
            
        Returns:
            List[str]: List of airline codes supporting the feature
        """
        if not feature:
            return []
        
        feature_airlines = cls.FEATURE_SUPPORT.get(feature, [])
        logger.debug(f"Found {len(feature_airlines)} airlines supporting feature '{feature}'")
        return feature_airlines.copy()
    
    @classmethod
    def get_available_features(cls) -> List[str]:
        """
        Get list of all available features.
        
        Returns:
            List[str]: List of feature names
        """
        return list(cls.FEATURE_SUPPORT.keys())
    
    @classmethod
    def get_airline_info(cls, airline_code: str) -> Dict[str, any]:
        """
        Get comprehensive information about an airline.
        
        Args:
            airline_code (str): The airline code
            
        Returns:
            Dict[str, any]: Comprehensive airline information
        """
        if not airline_code:
            return {}
        
        normalized_code = airline_code.strip().upper()
        
        if not cls.validate_airline_code(normalized_code):
            return {
                'code': normalized_code,
                'is_supported': False,
                'error': 'Airline not supported'
            }
        
        # Find region
        region = None
        for region_name, airlines in cls.AIRLINE_REGIONS.items():
            if normalized_code in airlines:
                region = region_name
                break
        
        # Get supported features
        supported_features = [
            feature for feature, airlines in cls.FEATURE_SUPPORT.items()
            if normalized_code in airlines
        ]
        
        return {
            'code': normalized_code,
            'display_name': cls.get_airline_display_name(normalized_code),
            'third_party_id': cls.get_third_party_id(normalized_code),
            'region': region,
            'is_supported': True,
            'supported_features': supported_features,
            'feature_count': len(supported_features)
        }
    
    @classmethod
    def bulk_validate_airlines(cls, airline_codes: List[str]) -> Dict[str, bool]:
        """
        Validate multiple airline codes at once.
        
        Args:
            airline_codes (List[str]): List of airline codes to validate
            
        Returns:
            Dict[str, bool]: Mapping of airline codes to validation results
        """
        if not airline_codes:
            return {}
        
        results = {}
        for code in airline_codes:
            results[code] = cls.validate_airline_code(code)
        
        valid_count = sum(results.values())
        logger.info(f"Validated {len(airline_codes)} airline codes: {valid_count} valid, {len(airline_codes) - valid_count} invalid")
        
        return results
    
    @classmethod
    def get_mapping_statistics(cls) -> Dict[str, any]:
        """
        Get statistics about the airline mapping configuration.
        
        Returns:
            Dict[str, any]: Mapping statistics
        """
        total_airlines = len(cls.AIRLINE_TO_THIRD_PARTY_ID)
        
        # Count airlines by region
        region_counts = {
            region: len(airlines) 
            for region, airlines in cls.AIRLINE_REGIONS.items()
        }
        
        # Count airlines by feature support
        feature_counts = {
            feature: len(airlines) 
            for feature, airlines in cls.FEATURE_SUPPORT.items()
        }
        
        return {
            'total_airlines': total_airlines,
            'total_regions': len(cls.AIRLINE_REGIONS),
            'total_features': len(cls.FEATURE_SUPPORT),
            'airlines_by_region': region_counts,
            'airlines_by_feature': feature_counts,
            'all_airline_codes': cls.get_supported_airlines()
        }
