#!/usr/bin/env python3
"""
Enhanced data transformer with round trip support.

This module extends the existing data_transformer.py to properly handle round trip flights
by detecting multiple journey legs and creating separate flight offers for each direction.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def _get_airline_logo_url(airline_code):
    """Get the logo URL for an airline code."""
    if not airline_code:
        return None
    
    # Clean and normalize the airline code
    code = airline_code.strip().upper()
    
    # List of available logos
    available_logos = {"AA", "AC", "AF", "AI", "AS", "AV", "B6", "BA", "CM", "CX", "DL", "EK", "EY", "F9", "FR", "GA", "IB", "JL", "JQ", "KL", "KQ", "LA", "LH", "LX", "MH", "NK", "NZ", "OZ", "PR", "QF", "QR", "SK", "SQ", "SV", "TK", "TP", "UA", "UX", "VA", "VN", "VS", "WN", "WY"}
    
    if code in available_logos:
        return f"/airlines/{code}.svg"
    
    return None  # No logo available

def _detect_round_trip_segments(segments: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Detect if segments represent a round trip and split them into outbound and return legs.
    
    Args:
        segments: List of flight segments
        
    Returns:
        Tuple of (outbound_segments, return_segments)
        If not a round trip, return_segments will be empty
    """
    if len(segments) < 2:
        return segments, []
    
    # Check if this is a round trip by looking for a return to the origin
    first_departure = segments[0]['departure']['airport']
    last_arrival = segments[-1]['arrival']['airport']
    
    # If last arrival equals first departure, this might be a round trip
    if first_departure == last_arrival:
        # Find the midpoint where we switch from outbound to return
        # Look for the segment where arrival airport matches the last segment's departure
        final_destination = None
        split_point = None
        
        for i, segment in enumerate(segments):
            current_arrival = segment['arrival']['airport']
            
            # If this is not the last segment and the arrival doesn't match origin
            if i < len(segments) - 1 and current_arrival != first_departure:
                final_destination = current_arrival
            
            # If we found a segment that arrives at what we think is the final destination
            # and the next segment departs from the same place, this is our split point
            if (i < len(segments) - 1 and 
                current_arrival != first_departure and
                i + 1 < len(segments) and
                segments[i + 1]['departure']['airport'] == current_arrival):
                
                # Check if there's a significant time gap (layover vs connection)
                current_arrival_time = datetime.fromisoformat(segment['arrival']['datetime'].replace('Z', '+00:00'))
                next_departure_time = datetime.fromisoformat(segments[i + 1]['departure']['datetime'].replace('Z', '+00:00'))
                time_gap = next_departure_time - current_arrival_time
                
                # If there's more than 2 hours gap, consider this a potential split point
                if time_gap.total_seconds() > 2 * 3600:  # 2 hours
                    split_point = i + 1
                    break
        
        # If we found a split point, divide the segments
        if split_point is not None:
            outbound = segments[:split_point]
            return_segments = segments[split_point:]
            
            logger.info(f"Detected round trip: {len(outbound)} outbound segments, {len(return_segments)} return segments")
            logger.info(f"Outbound: {outbound[0]['departure']['airport']} -> {outbound[-1]['arrival']['airport']}")
            logger.info(f"Return: {return_segments[0]['departure']['airport']} -> {return_segments[-1]['arrival']['airport']}")
            
            return outbound, return_segments
    
    # Not a round trip, return all segments as outbound
    return segments, []

def _create_flight_offer_from_segments(segments: List[Dict], airline_code: str,
                                     price: float, currency: str, offer_id_suffix: str,
                                     price_detail: Dict, priced_offer: Dict, 
                                     airline_offer: Dict, reference_data: Dict, offer_price: Dict = None) -> Dict:
    """
    Create a flight offer from a list of segments (either outbound or return).
    
    This is extracted from the original _transform_single_offer function to handle
    both outbound and return legs separately.
    """
    if not segments:
        return None
        
    # Import the helper functions from the original module
    from utils.data_transformer import (
        _calculate_duration, _build_price_breakdown, _get_airline_name,
        _extract_baggage_info, _extract_penalty_info, _transform_penalties_to_fare_rules
    )
    
    # Determine departure and arrival from first and last segments
    first_segment = segments[0]
    last_segment = segments[-1]
    
    # Calculate stops
    stops = max(0, len(segments) - 1)
    stop_details = []
    if stops > 0:
        for i in range(1, len(segments)):
            stop_airport = segments[i]['departure']['airport']
            stop_details.append(stop_airport)
    
    # Calculate total duration
    duration = _calculate_duration(first_segment, last_segment)
    
    # Extract OfferID from the airline_offer (not priced_offer)
    offer_id = None
    if airline_offer:
        offer_id_obj = airline_offer.get('OfferID')
        if offer_id_obj and isinstance(offer_id_obj, dict):
            offer_id_value = offer_id_obj.get('value')
            if offer_id_value:
                offer_id = offer_id_value
                logger.info(f"Using OfferID from API: {offer_id}")
            else:
                logger.warning(f"OfferID object found but value is empty: {offer_id_obj}")
        elif isinstance(offer_id_obj, str) and offer_id_obj.strip():
            # Handle case where OfferID is a string directly
            offer_id = offer_id_obj.strip()
            logger.info(f"Using OfferID string from API: {offer_id}")
        else:
            logger.warning(f"OfferID not found or invalid in airline_offer: {offer_id_obj}")
    
    # Fallback to UUID-based ID if OfferID extraction failed
    if not offer_id:
        import uuid
        import time
        timestamp = int(time.time())
        offer_id = f"flight_{timestamp}_{str(uuid.uuid4())[:8]}"
        logger.warning(f"OfferID not found, generated fallback ID: {offer_id}")
        if airline_offer:
            logger.info(f"Available airline_offer keys: {list(airline_offer.keys())}")
        else:
            logger.warning("airline_offer parameter is None")
    
    # Build price breakdown
    price_breakdown = _build_price_breakdown(price_detail, priced_offer, airline_offer)
    
    # Build airline details
    airline_details = {
        'code': airline_code,
        'name': _get_airline_name(airline_code),
        'logo': _get_airline_logo_url(airline_code),
        'flightNumber': f"{airline_code}{segments[0].get('flightNumber', '001')}"
    }
    
    # Extract baggage and penalty information
    baggage_info = _extract_baggage_info(priced_offer, reference_data)
    penalty_info = _extract_penalty_info(priced_offer, reference_data)
    fare_rules = _transform_penalties_to_fare_rules(penalty_info)
    
    flight_offer = {
        'id': offer_id,
        'airline': airline_details,
        'departure': first_segment['departure'],
        'arrival': last_segment['arrival'],
        'duration': duration,
        'stops': stops,
        'stopDetails': stop_details,
        'price': price,
        'currency': currency,
        'baggage': baggage_info,
        'penalties': penalty_info,
        'fareRules': fare_rules,
        'segments': segments,
        'priceBreakdown': price_breakdown
    }
    
    return flight_offer

def transform_single_offer_with_roundtrip(airline_code: str, priced_offer: Dict, 
                                        airline_offer: Dict, reference_data: Dict) -> List[Dict]:
    """
    Enhanced version of _transform_single_offer that handles round trips.
    
    Returns a list of flight offers - one for outbound, and one for return if it's a round trip.
    """
    # Import the original transformation function to reuse its logic
    from utils.data_transformer import _transform_single_offer
    
    try:
        logger.info(f"Starting enhanced transformation for airline {airline_code}")
        
        # First, get the segments using the original logic
        original_offer = _transform_single_offer(priced_offer, airline_code, reference_data, airline_offer)
        
        if not original_offer or 'segments' not in original_offer:
            logger.warning("No segments found in original offer")
            return []
        
        segments = original_offer['segments']
        
        # Detect if this is a round trip
        outbound_segments, return_segments = _detect_round_trip_segments(segments)
        
        offers = []
        
        # Extract common data from original offer
        price = original_offer.get('price', 0)
        currency = original_offer.get('currency', 'USD')
        
        # Get the original price detail and offer data
        offer_prices = priced_offer.get('OfferPrice', [])
        if offer_prices:
            offer_price = offer_prices[0]
            price_detail = offer_price.get('RequestedDate', {}).get('PriceDetail', {})
        else:
            price_detail = {}
        
        # Create outbound offer
        if outbound_segments:
            outbound_offer = _create_flight_offer_from_segments(
                outbound_segments, airline_code, price, currency, "",
                price_detail, priced_offer, airline_offer, reference_data, offer_price
            )
            if outbound_offer:
                outbound_offer['tripType'] = 'round-trip' if return_segments else 'one-way'
                outbound_offer['direction'] = 'outbound'
                offers.append(outbound_offer)
        
        # Create return offer if this is a round trip
        if return_segments:
            return_offer = _create_flight_offer_from_segments(
                return_segments, airline_code, price, currency, "",
                price_detail, priced_offer, airline_offer, reference_data, offer_price
            )
            if return_offer:
                return_offer['tripType'] = 'round-trip'
                return_offer['direction'] = 'return'
                offers.append(return_offer)
        
        logger.info(f"Created {len(offers)} flight offers from segments")
        return offers
        
    except Exception as e:
        logger.error(f"Error in enhanced transformation: {str(e)}")
        return []

def transform_verteil_to_frontend_with_roundtrip(verteil_response: Dict) -> List[Dict]:
    """
    Enhanced version of transform_verteil_to_frontend that handles round trips.
    
    This function will return separate flight offers for outbound and return legs
    when a round trip is detected.
    """
    # Import the original functions
    from utils.data_transformer import _extract_reference_data
    
    try:
        logger.info("Starting enhanced Verteil to frontend transformation")
        
        # Extract reference data
        reference_data = _extract_reference_data(verteil_response)
        
        # Navigate to the offers in the response - use the correct structure
        offers_group = verteil_response.get('OffersGroup', {})
        airline_offers = offers_group.get('AirlineOffers', [])
        
        if not airline_offers:
            logger.warning("No airline offers found")
            return []
        
        all_offers = []
        
        # Process each airline offer group
        for airline_offer_group in airline_offers:
            # Use the robust airline code extraction from the main transformer
            from utils.data_transformer import _extract_airline_code_robust
            airline_code = _extract_airline_code_robust(airline_offer_group)
            airline_offers_list = airline_offer_group.get('AirlineOffer', [])
            
            logger.info(f"Processing airline {airline_code} with {len(airline_offers_list)} offers")
            
            # Process each offer in the group
            for offer in airline_offers_list:
                priced_offer = offer.get('PricedOffer', {})
                
                if priced_offer:
                    # Transform with round trip support
                    offers = transform_single_offer_with_roundtrip(
                        airline_code, priced_offer, offer, reference_data
                    )
                    
                    all_offers.extend(offers)
        
        logger.info(f"Total offers created: {len(all_offers)}")
        return {
            'offers': all_offers,
            'reference_data': reference_data
        }
        
    except Exception as e:
        logger.error(f"Error transforming Verteil response: {str(e)}")
        return []