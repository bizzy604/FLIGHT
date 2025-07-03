"""
Enhanced Reference Extractor Module

This module provides functionality to extract and organize references from NDC
air shopping responses with support for both single-airline and multi-airline
responses. It follows PEP 8 standards and provides modular reference extraction.

Author: FLIGHT Application
Created: 2025-07-02
"""

import logging
from typing import Any, Dict, List, Optional

from .multi_airline_detector import MultiAirlineDetector

logger = logging.getLogger(__name__)


class EnhancedReferenceExtractor:
    """
    Enhanced reference extractor that handles both single-airline and
    multi-airline responses with airline-aware reference resolution.
    """
    
    def __init__(self, response: Dict[str, Any]):
        """
        Initialize the reference extractor.
        
        Args:
            response (Dict[str, Any]): The air shopping response dictionary
        """
        self.response = response
        self.is_multi_airline = MultiAirlineDetector.is_multi_airline_response(response)
        self._references_cache: Optional[Dict[str, Any]] = None
        
        logger.info(f"Initialized reference extractor for {'multi' if self.is_multi_airline else 'single'}-airline response")
    
    def extract_references(self) -> Dict[str, Any]:
        """
        Extract references with airline context awareness.
        
        Returns:
            Dict[str, Any]: Organized reference data structure
        """
        if self._references_cache is not None:
            return self._references_cache
        
        try:
            if self.is_multi_airline:
                self._references_cache = self._extract_multi_airline_refs()
            else:
                self._references_cache = self._extract_single_airline_refs()
            
            logger.info("Successfully extracted references")
            return self._references_cache
            
        except Exception as e:
            logger.error(f"Error extracting references: {e}")
            return self._get_empty_references_structure()
    
    def _extract_multi_airline_refs(self) -> Dict[str, Any]:
        """
        Extract airline-prefixed references for multi-airline responses.
        
        Returns:
            Dict[str, Any]: Multi-airline reference structure
        """
        logger.info("Extracting multi-airline references")
        
        # Initialize structure
        refs = {
            'type': 'multi_airline',
            'by_airline': {},
            'global': {},
            'airline_codes': [],
            'shopping_response_ids': {}
        }
        
        # Get airline codes
        refs['airline_codes'] = MultiAirlineDetector.extract_airline_codes(self.response)
        
        # Get shopping response IDs
        refs['shopping_response_ids'] = MultiAirlineDetector._extract_shopping_response_ids(self.response)
        
        # Extract references by type
        data_lists = self.response.get('DataLists', {})
        
        # Process each airline
        for airline_code in refs['airline_codes']:
            refs['by_airline'][airline_code] = {
                'segments': {},
                'passengers': {},
                'flights': {},
                'origins': {},
                'baggage': {},
                'services': {}
            }
        
        # Extract segments
        self._extract_segments_multi_airline(data_lists, refs)
        
        # Extract passengers
        self._extract_passengers_multi_airline(data_lists, refs)
        
        # Extract flights
        self._extract_flights_multi_airline(data_lists, refs)
        
        # Extract origins/destinations
        self._extract_origins_multi_airline(data_lists, refs)
        
        # Extract baggage
        self._extract_baggage_multi_airline(data_lists, refs)
        
        # Extract services
        self._extract_services_multi_airline(data_lists, refs)
        
        # Create global lookup for all references
        refs['global'] = self._create_global_lookup(refs['by_airline'])
        
        logger.info(f"Extracted multi-airline references for {len(refs['airline_codes'])} airlines")
        return refs
    
    def _extract_single_airline_refs(self) -> Dict[str, Any]:
        """
        Extract simple references for single-airline responses.
        
        Returns:
            Dict[str, Any]: Single-airline reference structure
        """
        logger.info("Extracting single-airline references")
        
        # Initialize structure
        refs = {
            'type': 'single_airline',
            'segments': {},
            'passengers': {},
            'flights': {},
            'origins': {},
            'baggage': {},
            'services': {},
            'shopping_response_id': ''
        }
        
        # Extract shopping response ID
        refs['shopping_response_id'] = self._extract_single_shopping_response_id()
        
        # Extract references by type
        data_lists = self.response.get('DataLists', {})
        
        # Extract segments
        self._extract_segments_single_airline(data_lists, refs)
        
        # Extract passengers
        self._extract_passengers_single_airline(data_lists, refs)
        
        # Extract flights
        self._extract_flights_single_airline(data_lists, refs)
        
        # Extract origins/destinations
        self._extract_origins_single_airline(data_lists, refs)
        
        # Extract baggage
        self._extract_baggage_single_airline(data_lists, refs)
        
        # Extract services
        self._extract_services_single_airline(data_lists, refs)
        
        logger.info("Extracted single-airline references")
        return refs
    
    def _extract_segments_multi_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract flight segments for multi-airline response."""
        segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        
        for segment in segments:
            segment_key = segment.get('SegmentKey', '')
            
            # Check if it's airline-prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(segment_key)
            if match:
                airline_code = match.group(1)
                if airline_code in refs['by_airline']:
                    refs['by_airline'][airline_code]['segments'][segment_key] = segment
            else:
                # Non-prefixed segment, add to global
                refs['global'].setdefault('segments', {})[segment_key] = segment
    
    def _extract_passengers_multi_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract passengers for multi-airline response."""
        passengers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        
        for passenger in passengers:
            object_key = passenger.get('ObjectKey', '')
            
            # Check if it's airline-prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(object_key)
            if match:
                airline_code = match.group(1)
                if airline_code in refs['by_airline']:
                    refs['by_airline'][airline_code]['passengers'][object_key] = passenger
            else:
                # Non-prefixed passenger, add to global
                refs['global'].setdefault('passengers', {})[object_key] = passenger
    
    def _extract_flights_multi_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract flights for multi-airline response."""
        flights = data_lists.get('FlightList', {}).get('Flight', [])
        
        for flight in flights:
            flight_key = flight.get('FlightKey', '')
            
            # Check if it's airline-prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(flight_key)
            if match:
                airline_code = match.group(1)
                if airline_code in refs['by_airline']:
                    refs['by_airline'][airline_code]['flights'][flight_key] = flight
            else:
                # Non-prefixed flight, add to global
                refs['global'].setdefault('flights', {})[flight_key] = flight
    
    def _extract_origins_multi_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract origin/destinations for multi-airline response."""
        origins = data_lists.get('OriginDestinationList', {}).get('OriginDestination', [])
        
        for origin in origins:
            origin_key = origin.get('OriginDestinationKey', '')
            
            # Check if it's airline-prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(origin_key)
            if match:
                airline_code = match.group(1)
                if airline_code in refs['by_airline']:
                    refs['by_airline'][airline_code]['origins'][origin_key] = origin
            else:
                # Non-prefixed origin, add to global
                refs['global'].setdefault('origins', {})[origin_key] = origin
    
    def _extract_baggage_multi_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract baggage information for multi-airline response."""
        baggage_list = data_lists.get('BaggageAllowanceList', {}).get('BaggageAllowance', [])
        
        for baggage in baggage_list:
            baggage_key = baggage.get('BaggageAllowanceID', '')
            
            # Check if it's airline-prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(baggage_key)
            if match:
                airline_code = match.group(1)
                if airline_code in refs['by_airline']:
                    refs['by_airline'][airline_code]['baggage'][baggage_key] = baggage
            else:
                # Non-prefixed baggage, add to global
                refs['global'].setdefault('baggage', {})[baggage_key] = baggage
    
    def _extract_services_multi_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract service information for multi-airline response."""
        services = data_lists.get('ServiceDefinitionList', {}).get('ServiceDefinition', [])
        
        for service in services:
            service_key = service.get('ServiceDefinitionID', '')
            
            # Check if it's airline-prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(service_key)
            if match:
                airline_code = match.group(1)
                if airline_code in refs['by_airline']:
                    refs['by_airline'][airline_code]['services'][service_key] = service
            else:
                # Non-prefixed service, add to global
                refs['global'].setdefault('services', {})[service_key] = service

    def _extract_segments_single_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract flight segments for single-airline response."""
        segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])

        for segment in segments:
            segment_key = segment.get('SegmentKey', '')
            if segment_key:
                refs['segments'][segment_key] = segment

    def _extract_passengers_single_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract passengers for single-airline response."""
        passengers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])

        for passenger in passengers:
            object_key = passenger.get('ObjectKey', '')
            if object_key:
                refs['passengers'][object_key] = passenger

    def _extract_flights_single_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract flights for single-airline response."""
        flights = data_lists.get('FlightList', {}).get('Flight', [])

        for flight in flights:
            flight_key = flight.get('FlightKey', '')
            if flight_key:
                refs['flights'][flight_key] = flight

    def _extract_origins_single_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract origin/destinations for single-airline response."""
        origins = data_lists.get('OriginDestinationList', {}).get('OriginDestination', [])

        for origin in origins:
            origin_key = origin.get('OriginDestinationKey', '')
            if origin_key:
                refs['origins'][origin_key] = origin

    def _extract_baggage_single_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract baggage information for single-airline response."""
        baggage_list = data_lists.get('BaggageAllowanceList', {}).get('BaggageAllowance', [])

        for baggage in baggage_list:
            baggage_key = baggage.get('BaggageAllowanceID', '')
            if baggage_key:
                refs['baggage'][baggage_key] = baggage

    def _extract_services_single_airline(self, data_lists: Dict, refs: Dict) -> None:
        """Extract service information for single-airline response."""
        services = data_lists.get('ServiceDefinitionList', {}).get('ServiceDefinition', [])

        for service in services:
            service_key = service.get('ServiceDefinitionID', '')
            if service_key:
                refs['services'][service_key] = service

    def _create_global_lookup(self, by_airline: Dict) -> Dict:
        """Create a global lookup table from airline-specific references."""
        global_refs = {
            'segments': {},
            'passengers': {},
            'flights': {},
            'origins': {},
            'baggage': {},
            'services': {}
        }

        for airline_code, airline_refs in by_airline.items():
            for ref_type, refs in airline_refs.items():
                global_refs[ref_type].update(refs)

        return global_refs

    def _extract_single_shopping_response_id(self) -> str:
        """Extract ShoppingResponseID for single-airline response."""
        try:
            return self.response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
        except Exception as e:
            logger.error(f"Error extracting single ShoppingResponseID: {e}")
            return ''

    def _get_empty_references_structure(self) -> Dict[str, Any]:
        """Return empty reference structure for error cases."""
        if self.is_multi_airline:
            return {
                'type': 'multi_airline',
                'by_airline': {},
                'global': {},
                'airline_codes': [],
                'shopping_response_ids': {}
            }
        else:
            return {
                'type': 'single_airline',
                'segments': {},
                'passengers': {},
                'flights': {},
                'origins': {},
                'baggage': {},
                'services': {},
                'shopping_response_id': ''
            }

    def get_reference_by_key(self, ref_key: str, ref_type: str = 'segments') -> Optional[Dict]:
        """
        Get a reference by key with airline-aware lookup.

        Args:
            ref_key (str): The reference key to look up
            ref_type (str): Type of reference ('segments', 'passengers', etc.)

        Returns:
            Optional[Dict]: The reference data or None if not found
        """
        refs = self.extract_references()

        if self.is_multi_airline:
            # Try global lookup first
            global_ref = refs.get('global', {}).get(ref_type, {}).get(ref_key)
            if global_ref:
                return global_ref

            # Try airline-specific lookup
            for airline_refs in refs.get('by_airline', {}).values():
                airline_ref = airline_refs.get(ref_type, {}).get(ref_key)
                if airline_ref:
                    return airline_ref
        else:
            # Single airline lookup
            return refs.get(ref_type, {}).get(ref_key)

        return None

    def get_airline_references(self, airline_code: str) -> Optional[Dict]:
        """
        Get all references for a specific airline.

        Args:
            airline_code (str): The airline code

        Returns:
            Optional[Dict]: Airline-specific references or None
        """
        if not self.is_multi_airline:
            return None

        refs = self.extract_references()
        return refs.get('by_airline', {}).get(airline_code)

    def get_shopping_response_id(self, airline_code: Optional[str] = None) -> str:
        """
        Get ShoppingResponseID for the specified airline or general ID.

        Args:
            airline_code (Optional[str]): Airline code for multi-airline responses

        Returns:
            str: The ShoppingResponseID
        """
        refs = self.extract_references()

        if self.is_multi_airline:
            shopping_ids = refs.get('shopping_response_ids', {})
            if airline_code and airline_code in shopping_ids:
                return shopping_ids[airline_code]
            elif shopping_ids:
                # Return first available if no specific airline requested
                return list(shopping_ids.values())[0]
            return ''
        else:
            return refs.get('shopping_response_id', '')

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the extracted references.

        Returns:
            Dict[str, Any]: Reference statistics
        """
        refs = self.extract_references()
        stats = {
            'type': refs.get('type'),
            'is_multi_airline': self.is_multi_airline
        }

        if self.is_multi_airline:
            stats['airline_count'] = len(refs.get('airline_codes', []))
            stats['airlines'] = refs.get('airline_codes', [])
            stats['by_airline'] = {}

            for airline, airline_refs in refs.get('by_airline', {}).items():
                stats['by_airline'][airline] = {
                    ref_type: len(ref_data)
                    for ref_type, ref_data in airline_refs.items()
                }

            # Global stats
            global_refs = refs.get('global', {})
            stats['global_totals'] = {
                ref_type: len(ref_data)
                for ref_type, ref_data in global_refs.items()
            }
        else:
            stats['totals'] = {
                ref_type: len(ref_data)
                for ref_type, ref_data in refs.items()
                if isinstance(ref_data, dict)
            }

        return stats
