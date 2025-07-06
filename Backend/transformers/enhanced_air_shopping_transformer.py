"""
Enhanced Air Shopping Response Transformer

This module provides enhanced transformation functionality for air shopping responses
with support for both single-airline and multi-airline responses. It integrates with
the Phase 1 core infrastructure modules for airline detection, reference extraction,
and airline mapping.

Author: FLIGHT Application
Created: 2025-07-02
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import Phase 1 core infrastructure modules
from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor
from services.airline_mapping_service import AirlineMappingService

# Import existing utilities for backward compatibility
from utils.air_shopping_transformer import _transform_departure_arrival
from utils.airline_data import get_airline_name, get_airline_logo_url

logger = logging.getLogger(__name__)


class EnhancedAirShoppingTransformer:
    """
    Enhanced transformer for air shopping responses with multi-airline support.
    """
    
    def __init__(self, response: Dict[str, Any], filter_unsupported_airlines: bool = False):
        """
        Initialize the enhanced transformer.

        Args:
            response (Dict[str, Any]): The raw air shopping response
            filter_unsupported_airlines (bool): Whether to filter out unsupported airlines.
                                               Default False to include all airlines from API response.
        """
        self.response = response
        self.filter_unsupported_airlines = filter_unsupported_airlines
        self.is_multi_airline = MultiAirlineDetector.is_multi_airline_response(response)
        self.reference_extractor = EnhancedReferenceExtractor(response)
        self.refs = self.reference_extractor.extract_references()

        logger.info(f"Initialized enhanced transformer for {'multi' if self.is_multi_airline else 'single'}-airline response")
        if not filter_unsupported_airlines:
            logger.info("Airline filtering disabled - all airlines from API response will be included")
    
    def transform_for_results(self) -> Dict[str, Any]:
        """
        Transform the air shopping response for the results page.
        
        Returns:
            Dict[str, Any]: Transformed response with flight offers
        """
        try:
            offers = []
            
            if self.is_multi_airline:
                offers = self._transform_multi_airline_offers()
            else:
                offers = self._transform_single_airline_offers()
            
            # For multi-airline, use the raw_response_index; for single-airline, use enumeration
            if self.is_multi_airline:
                # Multi-airline: raw_response_index is already set during transformation
                for offer in offers:
                    if 'raw_response_index' not in offer:
                        logger.debug("Setting default raw_response_index for multi-airline offer")
                        offer['raw_response_index'] = 0
            else:
                # Single-airline: assign original indices before sorting
                for index, offer in enumerate(offers):
                    offer['raw_response_index'] = index

            # DO NOT SORT - Display flights in raw response order to maintain proper index mapping
            # offers.sort(key=lambda x: float(x.get('price', 0)))

            # Add frontend display IDs (for UI) and preserve original indices for backend mapping
            for display_index, offer in enumerate(offers):
                offer['id'] = str(display_index)              # Frontend uses this for URL routing (display order)
                offer['display_index'] = display_index        # For frontend display order
                # Use raw_response_index for backend mapping to raw response
                offer['original_index'] = offer['raw_response_index']  # Backend needs raw response index
                offer['offer_index'] = offer['raw_response_index']     # Backward compatibility
            
            result = {
                'offers': offers,
                'raw_response': self.response,
                'metadata': {
                    'is_multi_airline': self.is_multi_airline,
                    'airline_count': len(self.refs.get('airline_codes', [])) if self.is_multi_airline else 1,
                    'total_offers': len(offers),
                    'transformation_timestamp': datetime.now().isoformat(),
                    'airline_filtering_enabled': self.filter_unsupported_airlines
                }
            }
            
            if self.is_multi_airline:
                airline_codes = self.refs.get('airline_codes', [])
                if self.filter_unsupported_airlines:
                    result['metadata']['supported_airlines'] = [
                        code for code in airline_codes
                        if AirlineMappingService.validate_airline_code(code)
                    ]
                    result['metadata']['filtered_airlines'] = [
                        code for code in airline_codes
                        if not AirlineMappingService.validate_airline_code(code)
                    ]
                else:
                    result['metadata']['supported_airlines'] = airline_codes  # All airlines included
                    result['metadata']['filtered_airlines'] = []  # No filtering applied

                result['metadata']['shopping_response_ids'] = self.refs.get('shopping_response_ids', {})
            
            logger.info(f"Successfully transformed {len(offers)} offers for results page")
            return result
            
        except Exception as e:
            logger.error(f"Error transforming air shopping response: {e}", exc_info=True)
            return {
                'offers': [],
                'raw_response': self.response,
                'error': str(e),
                'metadata': {
                    'is_multi_airline': self.is_multi_airline,
                    'transformation_failed': True
                }
            }
    
    def _transform_multi_airline_offers(self) -> List[Dict[str, Any]]:
        """
        Transform offers for multi-airline response.

        Returns:
            List[Dict[str, Any]]: List of transformed offers
        """
        logger.info("Transforming multi-airline offers")
        offers = []

        # Get offers from the response - handle both direct and nested structures
        offers_group = self.response.get('OffersGroup', {})
        if not offers_group and 'data' in self.response:
            offers_group = self.response.get('data', {}).get('OffersGroup', {})

        airline_offers_list = offers_group.get('AirlineOffers', [])

        if not isinstance(airline_offers_list, list):
            airline_offers_list = [airline_offers_list] if airline_offers_list else []

        # Track the original index in the raw response
        raw_offer_index = 0

        for airline_offer_group in airline_offers_list:
            # Transform offers for this airline
            airline_offers = airline_offer_group.get('AirlineOffer', [])
            if not isinstance(airline_offers, list):
                airline_offers = [airline_offers] if airline_offers else []

            for offer in airline_offers:
                priced_offer = offer.get('PricedOffer')
                if priced_offer:
                    # Primary: Use OfferID.Owner as the authoritative airline code
                    airline_code = offer.get('OfferID', {}).get('Owner', '??')

                    # If no owner found, fallback to operating carrier
                    if airline_code == '??':
                        airline_code = self._extract_operating_carrier_from_offer(offer)
                        logger.debug(f"Using operating carrier as fallback: {airline_code}")
                    else:
                        logger.debug(f"Using OfferID.Owner as airline code: {airline_code}")

                    # Validate airline is supported (only if filtering is enabled)
                    if self.filter_unsupported_airlines and not AirlineMappingService.validate_airline_code(airline_code):
                        logger.warning(f"Skipping unsupported airline: {airline_code} (filtering enabled)")
                        raw_offer_index += 1  # Still increment for skipped offers
                        continue

                    # Get airline-specific references
                    airline_refs = self.reference_extractor.get_airline_references(airline_code)
                    if not airline_refs:
                        # Skip airlines without complete DataLists - only process real API data
                        logger.warning(f"Skipping airline {airline_code} - no reference data available (not in actual API response)")
                        raw_offer_index += 1
                        continue

                    transformed = self._transform_offer_with_airline_context(
                        priced_offer, airline_code, airline_refs, offer
                    )
                    if transformed:
                        # Store the original index from the raw response
                        transformed['raw_response_index'] = raw_offer_index
                        offers.append(transformed)

                raw_offer_index += 1  # Increment for every offer in raw response

        logger.info(f"Transformed {len(offers)} multi-airline offers")
        return offers
    
    def _transform_single_airline_offers(self) -> List[Dict[str, Any]]:
        """
        Transform offers for single-airline response (backward compatibility).
        
        Returns:
            List[Dict[str, Any]]: List of transformed offers
        """
        logger.info("Transforming single-airline offers")
        offers = []
        
        # Use global references for single-airline
        global_refs = {
            'segments': self.refs.get('segments', {}),
            'passengers': self.refs.get('passengers', {}),
            'flights': self.refs.get('flights', {})
        }
        
        # Get offers from the response
        offers_group = self.response.get('OffersGroup', {})
        airline_offers_list = offers_group.get('AirlineOffers', [])
        
        if not isinstance(airline_offers_list, list):
            airline_offers_list = [airline_offers_list] if airline_offers_list else []

        # Track the original index in the raw response
        raw_offer_index = 0

        for airline_offer_group in airline_offers_list:
            airline_offers = airline_offer_group.get('AirlineOffer', [])
            if not isinstance(airline_offers, list):
                airline_offers = [airline_offers] if airline_offers else []

            for offer in airline_offers:
                priced_offer = offer.get('PricedOffer')
                if priced_offer:
                    # Primary: Use OfferID.Owner as the authoritative airline code
                    airline_code = offer.get('OfferID', {}).get('Owner', '??')

                    # If no owner found, fallback to operating carrier
                    if airline_code == '??':
                        airline_code = self._extract_operating_carrier_from_offer(offer)
                        logger.debug(f"Using operating carrier as fallback: {airline_code}")
                    else:
                        logger.debug(f"Using OfferID.Owner as airline code: {airline_code}")

                    # Transform offer using airline context - skip if transformation fails
                    try:
                        transformed = self._transform_offer_with_airline_context(
                            priced_offer, airline_code, global_refs, offer
                        )
                    except Exception as e:
                        logger.warning(f"Failed to transform offer for {airline_code}: {e}")
                        transformed = None
                    if transformed:
                        # Store the original index from the raw response
                        transformed['raw_response_index'] = raw_offer_index
                        offers.append(transformed)

                raw_offer_index += 1  # Increment for every offer in raw response
        
        logger.info(f"Transformed {len(offers)} single-airline offers")
        return offers
    
    def _transform_offer_with_airline_context(
        self, 
        priced_offer: Dict[str, Any], 
        airline_code: str, 
        refs: Dict[str, Any], 
        offer: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transform a single offer with airline context.
        
        Args:
            priced_offer: The priced offer data
            airline_code: The airline code for this offer
            refs: Reference data (airline-specific or global)
            offer: The original offer data
            
        Returns:
            Optional[Dict[str, Any]]: Transformed offer or None if transformation fails
        """
        try:
            # Extract price information by aggregating across all PTCs
            total_price = 0.0
            currency = None

            # Iterate through all OfferPrice entries to aggregate pricing across PTCs
            for offer_price in priced_offer.get('OfferPrice', []):
                price_detail = offer_price.get('RequestedDate', {}).get('PriceDetail', {})
                price_info = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                per_pax_price = float(price_info.get('value', 0))

                if currency is None:
                    currency = price_info.get('Code')

                # Count UNIQUE travelers in this OfferPrice by examining TravelerReferences
                # For round-trip flights, each passenger appears twice (outbound + return)
                # We need to count unique passenger IDs only
                unique_travelers = set()
                for assoc in offer_price.get('RequestedDate', {}).get('Associations', []):
                    raw_refs = assoc.get('AssociatedTraveler', {}).get('TravelerReferences', [])
                    # Handle both string and list formats for TravelerReferences
                    if isinstance(raw_refs, str):
                        unique_travelers.add(raw_refs)
                    elif isinstance(raw_refs, list):
                        for ref in raw_refs:
                            if ref:  # Only add non-empty references
                                unique_travelers.add(ref)

                # Count unique travelers for this OfferPrice
                traveler_count = len(unique_travelers)

                # Add this OfferPrice's contribution to total
                total_price += per_pax_price * max(1, traveler_count)  # Ensure at least 1 traveler

            # Create total_amount structure for backward compatibility
            total_amount = {
                'value': total_price,
                'Code': currency
            }
            
            # Extract segments for this offer
            all_segments_data = []
            # Use the first OfferPrice for segment extraction (segments are same across all OfferPrices)
            first_offer_price = priced_offer.get('OfferPrice', [{}])[0]
            for assoc in first_offer_price.get('RequestedDate', {}).get('Associations', []):
                for seg_ref in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
                    segment_key = seg_ref.get('ref')

                    # Try to get segment from airline-specific refs first, then global
                    segment_data = None
                    if isinstance(refs, dict) and 'segments' in refs:
                        segment_data = refs['segments'].get(segment_key)

                    # Fallback to global lookup if not found
                    if not segment_data and self.is_multi_airline:
                        segment_data = self.reference_extractor.get_reference_by_key(segment_key, 'segments')

                    if segment_data:
                        all_segments_data.append(segment_data)
            
            if not all_segments_data:
                logger.warning(f"No segments found for offer from airline {airline_code}")
                return None
            
            # Sort segments by departure time
            all_segments_data.sort(key=lambda s: s.get('Departure', {}).get('Date', ''))
            
            first_seg_data = all_segments_data[0]
            last_seg_data = all_segments_data[-1]
            
            # Calculate duration and stops
            dep_time = datetime.fromisoformat(first_seg_data.get('Departure', {}).get('Date', ''))
            arr_time = datetime.fromisoformat(last_seg_data.get('Arrival', {}).get('Date', ''))
            duration_delta = arr_time - dep_time
            total_hours, remainder = divmod(duration_delta.total_seconds(), 3600)
            total_minutes, _ = divmod(remainder, 60)
            
            stops_count = len(all_segments_data) - 1
            
            # Build stop details
            stop_details = []
            if stops_count > 0:
                for i in range(len(all_segments_data) - 1):
                    current_seg = all_segments_data[i]
                    next_seg = all_segments_data[i + 1]
                    
                    stop_airport = current_seg.get('Arrival', {}).get('AirportCode', {}).get('value', '')
                    arr_time_stop = datetime.fromisoformat(current_seg.get('Arrival', {}).get('Date', ''))
                    dep_time_stop = datetime.fromisoformat(next_seg.get('Departure', {}).get('Date', ''))
                    layover_duration = dep_time_stop - arr_time_stop
                    layover_hours, layover_remainder = divmod(layover_duration.total_seconds(), 3600)
                    layover_minutes, _ = divmod(layover_remainder, 60)
                    
                    stop_details.append({
                        'airport': stop_airport,
                        'duration': f"{int(layover_hours)}h {int(layover_minutes)}m"
                    })
            
            # Transform segments for detailed view
            transformed_segments = []
            for seg_data in all_segments_data:
                transformed_segments.append({
                    'departure': _transform_departure_arrival(seg_data.get('Departure', {})),
                    'arrival': _transform_departure_arrival(seg_data.get('Arrival', {})),
                    'airline': {
                        'code': airline_code,
                        'name': AirlineMappingService.get_airline_display_name(airline_code),
                        'flightNumber': f"{airline_code}{seg_data.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', '')}"
                    },
                    'aircraft': seg_data.get('Equipment', {}).get('AircraftCode', {}).get('value', 'Unknown'),
                    'duration': seg_data.get('FlightDetail', {}).get('FlightDuration', {}).get('value', 'Unknown')
                })
            
            # Get offer ID
            offer_id = offer.get('OfferID', {}).get('value', f"offer_{airline_code}_{len(all_segments_data)}")
            
            # Build departure and arrival data
            departure_data = _transform_departure_arrival(first_seg_data.get('Departure', {}))
            arrival_data = _transform_departure_arrival(last_seg_data.get('Arrival', {}))
            
            # Get ThirdParty ID for this airline
            third_party_id = AirlineMappingService.get_third_party_id(airline_code)
            
            # Get airline-specific ShoppingResponseID
            shopping_response_id = self.reference_extractor.get_shopping_response_id(airline_code)
            
            return {
                "id": offer_id,
                "price": total_amount.get('value', 0),
                "currency": total_amount.get('Code'),
                "airline": {
                    "code": airline_code,
                    "name": AirlineMappingService.get_airline_display_name(airline_code),
                    "logo": get_airline_logo_url(airline_code),
                    "flightNumber": f"{airline_code}{first_seg_data.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', '')}"
                },
                "departure": departure_data,
                "arrival": arrival_data,
                "duration": f"{int(total_hours)}h {int(total_minutes)}m",
                "stops": stops_count,
                "stopDetails": stop_details,
                "segments": transformed_segments,
                # Essential airline context for multi-airline support
                "airline_context": {
                    "third_party_id": third_party_id,
                    "shopping_response_id": shopping_response_id
                },
                # Store original offer ID for reference
                "original_offer_id": offer_id
            }
            
        except Exception as e:
            logger.error(f"Error transforming offer for airline {airline_code}: {e}", exc_info=True)
            return None
    
    def _extract_airline_code_from_offer_group(self, airline_offer_group: Dict[str, Any]) -> str:
        """
        Extract airline code from airline offer group using operating carrier information.

        Args:
            airline_offer_group: The airline offer group data

        Returns:
            str: The airline code from operating carrier
        """
        # Try to get from first offer in the group
        airline_offers = airline_offer_group.get('AirlineOffer', [])
        if not isinstance(airline_offers, list):
            airline_offers = [airline_offers] if airline_offers else []

        if airline_offers:
            first_offer = airline_offers[0]

            # Primary: Use OfferID.Owner as the authoritative airline code
            airline_code = first_offer.get('OfferID', {}).get('Owner', '??')
            if airline_code and airline_code != '??':
                return airline_code

            # Fallback to operating carrier if no owner found
            airline_code = self._extract_operating_carrier_from_offer(first_offer)
            return airline_code

        return '??'

    def _extract_operating_carrier_from_offer(self, offer: Dict[str, Any]) -> str:
        """
        Extract airline code from operating carrier in flight segments.
        Handles codeshare flights and multi-segment journeys.

        Args:
            offer: The airline offer data

        Returns:
            str: The operating carrier airline code or '??'
        """
        try:
            priced_offer = offer.get('PricedOffer', {})

            # Get segment references from the offer
            segment_refs = set()
            for offer_price in priced_offer.get('OfferPrice', []):
                for assoc in offer_price.get('RequestedDate', {}).get('Associations', []):
                    for seg_ref in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
                        if 'ref' in seg_ref:
                            segment_refs.add(seg_ref['ref'])

            if not segment_refs:
                logger.debug("No segment references found in offer")
                return '??'

            # Look up segments in DataLists to find operating carrier
            data_lists = self.response.get('DataLists', {})
            segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
            if not isinstance(segments, list):
                segments = [segments] if segments else []

            # Collect all carriers from relevant segments
            operating_carriers = []
            marketing_carriers = []

            for segment in segments:
                segment_key = segment.get('SegmentKey', '')
                if segment_key in segment_refs:
                    # Extract OperatingCarrier
                    operating_carrier = segment.get('OperatingCarrier', {})
                    if operating_carrier:
                        airline_id = operating_carrier.get('AirlineID', {})
                        if isinstance(airline_id, dict):
                            airline_code = airline_id.get('value')
                        else:
                            airline_code = airline_id

                        if airline_code and airline_code not in operating_carriers:
                            operating_carriers.append(airline_code)

                    # Extract MarketingCarrier as fallback
                    marketing_carrier = segment.get('MarketingCarrier', {})
                    if marketing_carrier:
                        airline_id = marketing_carrier.get('AirlineID', {})
                        if isinstance(airline_id, dict):
                            airline_code = airline_id.get('value')
                        else:
                            airline_code = airline_id

                        if airline_code and airline_code not in marketing_carriers:
                            marketing_carriers.append(airline_code)

            # Return the primary operating carrier (first one found)
            if operating_carriers:
                primary_carrier = operating_carriers[0]
                logger.debug(f"Found operating carrier: {primary_carrier} (from {len(operating_carriers)} segments)")
                return primary_carrier

            # Fallback to marketing carrier
            if marketing_carriers:
                primary_carrier = marketing_carriers[0]
                logger.debug(f"Found marketing carrier: {primary_carrier} (from {len(marketing_carriers)} segments)")
                return primary_carrier

            logger.debug("No operating or marketing carrier found in segments")
            return '??'

        except Exception as e:
            logger.error(f"Error extracting operating carrier from offer: {e}")
            return '??'







    def get_airline_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about airlines in the response.
        
        Returns:
            Dict[str, Any]: Airline statistics
        """
        if self.is_multi_airline:
            airline_codes = self.refs.get('airline_codes', [])
            supported_airlines = [
                code for code in airline_codes
                if AirlineMappingService.validate_airline_code(code)
            ]
            
            return {
                'total_airlines': len(airline_codes),
                'supported_airlines': len(supported_airlines),
                'airline_codes': airline_codes,
                'supported_codes': supported_airlines,
                'unsupported_codes': [code for code in airline_codes if code not in supported_airlines]
            }
        else:
            return {
                'total_airlines': 1,
                'supported_airlines': 1,
                'is_single_airline': True
            }


def transform_air_shopping_for_results_enhanced(response: Dict[str, Any], filter_unsupported_airlines: bool = False) -> Dict[str, Any]:
    """
    Enhanced transformation function for air shopping responses.

    This function serves as the main entry point for transforming air shopping
    responses with multi-airline support while maintaining backward compatibility.

    Args:
        response (Dict[str, Any]): The raw air shopping response
        filter_unsupported_airlines (bool): Whether to filter out unsupported airlines.
                                           Default False to include all airlines from API response.

    Returns:
        Dict[str, Any]: Transformed response with flight offers
    """
    transformer = EnhancedAirShoppingTransformer(response, filter_unsupported_airlines)
    return transformer.transform_for_results()
