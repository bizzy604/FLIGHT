"""
Multi-Airline Detection Module

This module provides functionality to detect and analyze multi-airline responses
from NDC air shopping APIs. It follows PEP 8 standards and provides modular
detection capabilities.

Author: FLIGHT Application
Created: 2025-07-02
"""

import logging
import re
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MultiAirlineDetector:
    """
    Detector class for identifying multi-airline responses and extracting
    airline-related information from NDC air shopping responses.
    """
    
    # Known airline codes pattern (2-3 characters)
    AIRLINE_CODE_PATTERN = re.compile(r'^[A-Z0-9]{2,3}$')
    
    # Airline-prefixed reference pattern (e.g., "KL-SEG1", "LHG-PAX1")
    PREFIXED_REFERENCE_PATTERN = re.compile(r'^([A-Z0-9]{2,3})-(.+)$')
    
    @staticmethod
    def is_multi_airline_response(response: Dict) -> bool:
        """
        Detect if the response contains multiple airlines.

        Args:
            response (Dict): The air shopping response dictionary

        Returns:
            bool: True if multi-airline response, False otherwise
        """
        try:
            logger.info(f"[DEBUG] Checking multi-airline response. Top-level keys: {list(response.keys())}")

            # Method 1: Check for airline-prefixed references in DataLists
            if MultiAirlineDetector._has_airline_prefixed_references(response):
                logger.info("Multi-airline response detected via prefixed references")
                return True

            # Method 2: Check for multiple airline owners in warnings
            if MultiAirlineDetector._has_multiple_airline_warnings(response):
                logger.info("Multi-airline response detected via multiple warning owners")
                return True
            
            # Method 3: Check for multiple ShoppingResponseIDs
            if MultiAirlineDetector._has_multiple_shopping_response_ids(response):
                logger.info("Multi-airline response detected via multiple ShoppingResponseIDs")
                return True
            
            logger.info("Single-airline response detected")
            return False
            
        except Exception as e:
            logger.error(f"Error detecting multi-airline response: {e}")
            # Default to single-airline for safety
            return False
    
    @staticmethod
    def extract_airline_codes(response: Dict) -> List[str]:
        """
        Extract all airline codes present in the response.
        
        Args:
            response (Dict): The air shopping response dictionary
            
        Returns:
            List[str]: List of unique airline codes found
        """
        airline_codes: Set[str] = set()
        
        try:
            # Extract from warnings
            warnings = response.get('Warnings', {}).get('Warning', [])
            for warning in warnings:
                owner = warning.get('Owner')
                if owner and MultiAirlineDetector.AIRLINE_CODE_PATTERN.match(owner):
                    airline_codes.add(owner)
            
            # Extract from prefixed references in DataLists
            data_lists = response.get('DataLists', {})
            
            # Check AnonymousTravelerList
            travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
            for traveler in travelers:
                object_key = traveler.get('ObjectKey', '')
                match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(object_key)
                if match:
                    airline_codes.add(match.group(1))
            
            # Check FlightSegmentList
            segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
            for segment in segments:
                segment_key = segment.get('SegmentKey', '')
                match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(segment_key)
                if match:
                    airline_codes.add(match.group(1))
            
            # Extract from ShoppingResponseIDs metadata
            shopping_ids = MultiAirlineDetector._extract_shopping_response_ids(response)
            airline_codes.update(shopping_ids.keys())
            
            result = sorted(list(airline_codes))
            logger.info(f"Extracted airline codes: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting airline codes: {e}")
            return []
    
    @staticmethod
    def get_airline_prefixed_references(response: Dict) -> Dict[str, List[str]]:
        """
        Group references by airline prefix.
        
        Args:
            response (Dict): The air shopping response dictionary
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping airline codes to their references
        """
        airline_refs: Dict[str, List[str]] = {}
        
        try:
            data_lists = response.get('DataLists', {})
            
            # Process all reference types
            reference_lists = [
                ('travelers', data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])),
                ('segments', data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])),
                ('flights', data_lists.get('FlightList', {}).get('Flight', [])),
                ('origins', data_lists.get('OriginDestinationList', {}).get('OriginDestination', [])),
            ]
            
            for ref_type, ref_list in reference_lists:
                for item in ref_list:
                    # Get the key field based on reference type
                    key_field = MultiAirlineDetector._get_key_field_for_type(ref_type)
                    ref_key = item.get(key_field, '')
                    
                    match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(ref_key)
                    if match:
                        airline_code = match.group(1)
                        if airline_code not in airline_refs:
                            airline_refs[airline_code] = []
                        airline_refs[airline_code].append(ref_key)
            
            logger.info(f"Grouped references by airline: {list(airline_refs.keys())}")
            return airline_refs
            
        except Exception as e:
            logger.error(f"Error grouping airline prefixed references: {e}")
            return {}
    
    @staticmethod
    def _has_airline_prefixed_references(response: Dict) -> bool:
        """Check if response contains airline-prefixed references."""
        try:
            data_lists = response.get('DataLists', {})
            logger.info(f"[DEBUG] DataLists keys: {list(data_lists.keys())}")

            # Check travelers
            travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
            logger.info(f"[DEBUG] Found {len(travelers)} travelers")
            for i, traveler in enumerate(travelers[:3]):  # Log first 3 travelers
                object_key = traveler.get('ObjectKey', '')
                logger.info(f"[DEBUG] Traveler {i} ObjectKey: {object_key}")
                if MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(object_key):
                    logger.info(f"[DEBUG] Found airline-prefixed traveler: {object_key}")
                    return True

            # Check segments
            segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
            logger.info(f"[DEBUG] Found {len(segments)} segments")
            for i, segment in enumerate(segments[:3]):  # Log first 3 segments
                segment_key = segment.get('SegmentKey', '')
                logger.info(f"[DEBUG] Segment {i} SegmentKey: {segment_key}")
                if MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(segment_key):
                    logger.info(f"[DEBUG] Found airline-prefixed segment: {segment_key}")
                    return True

            logger.info("[DEBUG] No airline-prefixed references found")
            return False

        except Exception as e:
            logger.error(f"[DEBUG] Error in _has_airline_prefixed_references: {e}")
            return False
    
    @staticmethod
    def _has_multiple_airline_warnings(response: Dict) -> bool:
        """Check if response has warnings from multiple airlines."""
        try:
            warnings = response.get('Warnings', {}).get('Warning', [])
            airline_owners = set()
            
            for warning in warnings:
                owner = warning.get('Owner')
                if owner and MultiAirlineDetector.AIRLINE_CODE_PATTERN.match(owner):
                    airline_owners.add(owner)
            
            return len(airline_owners) > 1
            
        except Exception:
            return False
    
    @staticmethod
    def _has_multiple_shopping_response_ids(response: Dict) -> bool:
        """Check if response has multiple ShoppingResponseIDs."""
        try:
            shopping_ids = MultiAirlineDetector._extract_shopping_response_ids(response)
            return len(shopping_ids) > 1
            
        except Exception:
            return False
    
    @staticmethod
    def _extract_shopping_response_ids(response: Dict) -> Dict[str, str]:
        """Extract ShoppingResponseIDs by airline."""
        shopping_ids = {}
        
        try:
            metadata_section = response.get("Metadata", {})
            other_metadata_list = metadata_section.get("Other", {}).get("OtherMetadata", [])
            
            for other_metadata in other_metadata_list:
                desc_metadatas = other_metadata.get("DescriptionMetadatas", {})
                desc_metadata_list = desc_metadatas.get("DescriptionMetadata", [])
                
                for desc_metadata in desc_metadata_list:
                    if desc_metadata.get("MetadataKey") == "SHOPPING_RESPONSE_IDS":
                        aug_points = desc_metadata.get("AugmentationPoint", {}).get("AugPoint", [])
                        
                        for aug_point in aug_points:
                            owner = aug_point.get("Owner")
                            key = aug_point.get("Key")
                            if owner and key:
                                shopping_ids[owner] = key
                                
        except Exception as e:
            logger.error(f"Error extracting ShoppingResponseIDs: {e}")
        
        return shopping_ids
    
    @staticmethod
    def _get_key_field_for_type(ref_type: str) -> str:
        """Get the appropriate key field name for each reference type."""
        key_mapping = {
            'travelers': 'ObjectKey',
            'segments': 'SegmentKey',
            'flights': 'FlightKey',
            'origins': 'OriginDestinationKey',
        }
        return key_mapping.get(ref_type, 'ObjectKey')
