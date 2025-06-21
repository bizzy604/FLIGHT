"""Data transformation utilities for converting Verteil API responses to frontend-compatible formats."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def transform_verteil_to_frontend(verteil_response: Dict[str, Any], enable_roundtrip: bool = False) -> List[Dict[str, Any]]:
    """
    Transform Verteil API air shopping response to frontend-compatible FlightOffer objects.
    
    Args:
        verteil_response: Raw response from Verteil API
        enable_roundtrip: Whether to enable round trip transformation logic
        
    Returns:
        List of FlightOffer objects compatible with frontend interface
    """
    try:
        # If roundtrip transformation is enabled, use the enhanced roundtrip logic
        if enable_roundtrip:
            from utils.data_transformer_roundtrip import transform_verteil_to_frontend_with_roundtrip
            return transform_verteil_to_frontend_with_roundtrip(verteil_response)
        
        flight_offers = []
        
        # Debug logging to understand the response structure
        logger.info(f"Received response with keys: {list(verteil_response.keys())}")
        
        # Navigate to the offers in the response
        offers_group = verteil_response.get('OffersGroup', {})
        logger.info(f"OffersGroup found: {offers_group is not None}, keys: {list(offers_group.keys()) if offers_group else 'None'}")
        
        airline_offers = offers_group.get('AirlineOffers', [])
        logger.info(f"AirlineOffers found: {len(airline_offers) if isinstance(airline_offers, list) else 'Not a list' if airline_offers else 'None'}")
        
        # Extract reference data for lookups
        reference_data = _extract_reference_data(verteil_response)
        logger.info(f"Reference data extracted: flights={len(reference_data['flights'])}, segments={len(reference_data['segments'])}")
        
        for i, airline_offer_group in enumerate(airline_offers):
            # Extract airline code using robust method
            airline_code = _extract_airline_code_robust(airline_offer_group)
            airline_offers_list = airline_offer_group.get('AirlineOffer', [])
            logger.info(f"Processing airline offer group {i}: airline_code={airline_code}, offers_count={len(airline_offers_list) if isinstance(airline_offers_list, list) else 'Not a list'}")
            
            # Debug the airline offer group structure
            logger.info(f"Airline offer group keys: {list(airline_offer_group.keys())}")
            
            for j, offer in enumerate(airline_offers_list):
                priced_offer = offer.get('PricedOffer', {})
                logger.info(f"Processing offer {j}: priced_offer_keys={list(priced_offer.keys()) if isinstance(priced_offer, dict) else 'Not a dict'}")
                    
                if priced_offer:
                    flight_offer = _transform_single_offer(
                        priced_offer, 
                        airline_code, 
                        reference_data,
                        offer  # Pass the full AirlineOffer for price extraction
                    )
                    if flight_offer:
                        flight_offers.append(flight_offer)
                        logger.info(f"Successfully transformed offer {j} into flight offer")
                    else:
                        logger.warning(f"Failed to transform offer {j}")
                else:
                    logger.warning(f"No PricedOffer found in offer {j}")
        
        logger.info(f"Transformed {len(flight_offers)} flight offers from Verteil response")
        return {
            'offers': flight_offers,
            'reference_data': reference_data
        }
        
    except Exception as e:
        logger.error(f"Error transforming Verteil response: {str(e)}")
        return {
            'offers': [],
            'reference_data': {}
        }

def _extract_airline_code_robust(airline_offer_group: Dict[str, Any]) -> str:
    """Robust airline code extraction with multiple fallbacks and detailed logging."""
    logger.info(f"Extracting airline code from offer group with keys: {list(airline_offer_group.keys()) if isinstance(airline_offer_group, dict) else 'Not a dict'}")
    
    # Primary method: Extract from OfferID.Owner in individual offers
    airline_offers_list = airline_offer_group.get('AirlineOffer', [])
    logger.info(f"Found {len(airline_offers_list) if isinstance(airline_offers_list, list) else 'invalid'} airline offers")
    
    if isinstance(airline_offers_list, list) and airline_offers_list:
        first_offer = airline_offers_list[0]
        if isinstance(first_offer, dict):
            # Check OfferID structure for Owner field
            offer_id_data = first_offer.get('OfferID')
            logger.info(f"OfferID data: {offer_id_data}, type: {type(offer_id_data)}")
            
            if isinstance(offer_id_data, dict):
                owner = offer_id_data.get('Owner')
                logger.info(f"OfferID.Owner: {owner}, type: {type(owner)}")
                
                if owner and isinstance(owner, str) and owner.strip():
                    airline_code = owner.strip()
                    logger.info(f"Successfully extracted airline code from OfferID.Owner: {airline_code}")
                    return airline_code
                else:
                    logger.warning(f"OfferID.Owner is empty or invalid: {owner}")
            
            # Fallback: Check if OfferID is a string and extract pattern
            elif isinstance(offer_id_data, str) and len(offer_id_data) >= 2:
                # Many airline codes are 2-3 characters at the start of offer IDs
                potential_code = offer_id_data[:2].upper()
                if potential_code.isalpha():
                    logger.info(f"Extracted potential airline code from OfferID string: {potential_code}")
                    return potential_code
    
    # Legacy fallback: Check Owner at airline_offer_group level (for backward compatibility)
    owner_data = airline_offer_group.get('Owner')
    logger.info(f"Checking legacy Owner data: {owner_data}, type: {type(owner_data)}")
    
    if isinstance(owner_data, dict):
        value = owner_data.get('value')
        if value and isinstance(value, str) and value.strip():
            airline_code = value.strip()
            logger.info(f"Successfully extracted airline code from legacy Owner.value: {airline_code}")
            return airline_code
    elif isinstance(owner_data, str) and owner_data.strip():
        airline_code = owner_data.strip()
        logger.info(f"Successfully extracted airline code from legacy Owner string: {airline_code}")
        return airline_code
    
    # Final fallback
    logger.error("Could not extract airline code from any source, using 'Unknown'")
    return 'Unknown'

def _extract_reference_data(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract reference data (flights, segments, airports, etc.) from Verteil response.
    """
    reference_data = {
        'flights': {},
        'segments': {},
        'airports': {},
        'aircraft': {},
        'airlines': {},
        'default_airline': None,  # Will store the default airline info
        'carry_on_allowances': {},
        'checked_bag_allowances': {},
        'penalties': {}
    }
    
    try:
        # Extract flight references - FlightList is inside DataLists
        data_lists = response.get('DataLists', {})
        flight_list = data_lists.get('FlightList', {})
        flights = flight_list.get('Flight', [])
        if isinstance(flights, list):
            for flight in flights:
                flight_key = flight.get('FlightKey')
                # Ensure flight_key is a valid string for use as dictionary key
                if flight_key and isinstance(flight_key, str):
                    reference_data['flights'][flight_key] = flight
                elif flight_key:
                    logger.warning(f"Invalid FlightKey type: {type(flight_key)} - {flight_key}")
        
        # Extract flight segment references - FlightSegmentList is inside DataLists
        segment_list = data_lists.get('FlightSegmentList', {})
        logger.info(f"FlightSegmentList found: {bool(segment_list)}")
        segments = segment_list.get('FlightSegment', [])
        logger.info(f"Found {len(segments)} flight segments in response")
        if isinstance(segments, list):
            logger.info(f"Processing {len(segments)} segments")
            for i, segment in enumerate(segments[:2]):  # Log first 2 segments for debugging
                logger.info(f"Segment {i} structure: {json.dumps(segment, indent=2)}")
                
            for segment in segments:
                segment_key = segment.get('SegmentKey')
                # Ensure segment_key is a valid string for use as dictionary key
                if segment_key and isinstance(segment_key, str):
                    reference_data['segments'][segment_key] = segment
                    logger.info(f"Added segment {segment_key} to reference data")
                    
                    # Extract airline information from the segment
                    for carrier_type in ['MarketingCarrier', 'OperatingCarrier']:
                            carrier = segment.get(carrier_type, {})
                            if not carrier:
                                logger.debug(f"No {carrier_type} in segment {segment_key}")
                                continue
                                
                            logger.info(f"Processing {carrier_type} for segment {segment_key}")
                            logger.info(f"Carrier data: {carrier}")
                            
                            airline_id = carrier.get('AirlineID', {})
                            logger.info(f"AirlineID: {airline_id}")
                            
                            # Extract airline code safely, ensuring it's always a string
                            if isinstance(airline_id, dict):
                                airline_code = airline_id.get('value')
                            else:
                                airline_code = airline_id
                            
                            # Ensure airline_code is a string and not None or empty
                            if not airline_code or not isinstance(airline_code, str):
                                logger.warning(f"Invalid airline_code extracted: {airline_code} (type: {type(airline_code)})")
                                continue
                                
                            airline_name = carrier.get('Name')
                            
                            logger.info(f"Extracted - Code: {airline_code}, Name: {airline_name}")
                            
                            if not airline_code:
                                logger.warning(f"Missing airline code in carrier data")
                                continue
                                
                            # Use the name from the API if available, otherwise look it up
                            if not airline_name:
                                airline_name = get_airline_name(airline_code, log_missing=False)
                                logger.debug(f"Looked up airline name for {airline_code}: {airline_name}")
                            
                            # Initialize airlines dictionary if it doesn't exist
                            if 'airlines' not in reference_data:
                                reference_data['airlines'] = {}
                            
                            # Store the airline info - we have a code and either have a name or looked it up
                            reference_data['airlines'][airline_code] = airline_name
                            logger.info(f"Added airline {airline_code}: {airline_name} from {carrier_type}")
                            
                            # Set default airline if not set yet (first airline found)
                            if reference_data['default_airline'] is None:
                                reference_data['default_airline'] = {
                                    'code': airline_code,
                                    'name': airline_name
                                }
                elif segment_key:
                    logger.warning(f"Invalid SegmentKey type: {type(segment_key)} - {segment_key}")
                else:
                    logger.warning(f"Segment missing SegmentKey: {segment}")
        else:
            logger.warning(f"FlightSegment is not a list: {type(segments)}")
        
        logger.info(f"Total segments in reference_data: {len(reference_data['segments'])}")
        
        # Extract airport information from FlightSegmentList
        for segment in reference_data['segments'].values():
            # Extract departure airport
            dep_airport_raw = segment.get('Departure', {}).get('AirportCode')
            # Handle airport code extraction similar to airline code
            if isinstance(dep_airport_raw, dict):
                dep_airport = dep_airport_raw.get('value')
            else:
                dep_airport = dep_airport_raw
            
            # Ensure dep_airport is a valid string for use as dictionary key
            if dep_airport and isinstance(dep_airport, str):
                reference_data['airports'][dep_airport] = {
                    'code': dep_airport,
                    'name': segment['Departure'].get('AirportName', dep_airport),
                    'terminal': segment['Departure'].get('Terminal')
                }
            elif dep_airport_raw:
                logger.warning(f"Invalid departure AirportCode extraction: {type(dep_airport_raw)} - {dep_airport_raw}")
            
            # Extract arrival airport
            arr_airport_raw = segment.get('Arrival', {}).get('AirportCode')
            # Handle airport code extraction similar to airline code
            if isinstance(arr_airport_raw, dict):
                arr_airport = arr_airport_raw.get('value')
            else:
                arr_airport = arr_airport_raw
            
            # Ensure arr_airport is a valid string for use as dictionary key
            if arr_airport and isinstance(arr_airport, str):
                reference_data['airports'][arr_airport] = {
                    'code': arr_airport,
                    'name': segment['Arrival'].get('AirportName', arr_airport),
                    'terminal': segment['Arrival'].get('Terminal')
                }
            elif arr_airport_raw:
                logger.warning(f"Invalid arrival AirportCode extraction: {type(arr_airport_raw)} - {arr_airport_raw}")
        
        # Also try to extract from OriginDestinationList if available
        od_list = response.get('OriginDestinationList', {})
        origin_destinations = od_list.get('OriginDestination', [])
        logger.debug(f"Found {len(origin_destinations)} origin-destinations in response")
        
        if isinstance(origin_destinations, list):
            for od in origin_destinations:
                # Extract departure airport
                dep = od.get('Departure', {})
                dep_airport_raw = dep.get('AirportCode')
                # Handle airport code extraction similar to airline code
                if isinstance(dep_airport_raw, dict):
                    dep_airport = dep_airport_raw.get('value')
                else:
                    dep_airport = dep_airport_raw
                
                # Ensure dep_airport is a valid string for use as dictionary key
                if dep_airport and isinstance(dep_airport, str) and dep_airport not in reference_data['airports']:
                    reference_data['airports'][dep_airport] = {
                        'code': dep_airport,
                        'name': dep.get('AirportName', dep_airport),
                        'terminal': dep.get('Terminal')
                    }
                elif dep_airport_raw and not isinstance(dep_airport, str):
                    logger.warning(f"Invalid departure AirportCode extraction in OriginDestination: {type(dep_airport_raw)} - {dep_airport_raw}")
                
                # Extract arrival airport
                arr = od.get('Arrival', {})
                arr_airport_raw = arr.get('AirportCode')
                # Handle airport code extraction similar to airline code
                if isinstance(arr_airport_raw, dict):
                    arr_airport = arr_airport_raw.get('value')
                else:
                    arr_airport = arr_airport_raw
                
                # Ensure arr_airport is a valid string for use as dictionary key
                if arr_airport and isinstance(arr_airport, str) and arr_airport not in reference_data['airports']:
                    reference_data['airports'][arr_airport] = {
                        'code': arr_airport,
                        'name': arr.get('AirportName', arr_airport),
                        'terminal': arr.get('Terminal')
                    }
                elif arr_airport_raw and not isinstance(arr_airport, str):
                    logger.warning(f"Invalid arrival AirportCode extraction in OriginDestination: {type(arr_airport_raw)} - {arr_airport_raw}")
        
        # Extract carry-on allowance list
        carry_on_list = data_lists.get('CarryOnAllowanceList', {}).get('CarryOnAllowance', [])
        for carry_on in carry_on_list:
            list_key = carry_on.get('ListKey')
            # Ensure list_key is a valid string for use as dictionary key
            if list_key and isinstance(list_key, str):
                reference_data['carry_on_allowances'][list_key] = carry_on
            elif list_key:
                logger.warning(f"Invalid ListKey type for carry-on allowance: {type(list_key)} - {list_key}")
        
        # Extract checked bag allowance list
        checked_bag_list = data_lists.get('CheckedBagAllowanceList', {}).get('CheckedBagAllowance', [])
        for checked_bag in checked_bag_list:
            list_key = checked_bag.get('ListKey')
            # Ensure list_key is a valid string for use as dictionary key
            if list_key and isinstance(list_key, str):
                reference_data['checked_bag_allowances'][list_key] = checked_bag
            elif list_key:
                logger.warning(f"Invalid ListKey type for checked bag allowance: {type(list_key)} - {list_key}")
        
        # Extract penalty list
        penalty_list = data_lists.get('PenaltyList', {}).get('Penalty', [])
        for penalty in penalty_list:
            object_key = penalty.get('ObjectKey')
            # Ensure object_key is a valid string for use as dictionary key
            if object_key and isinstance(object_key, str):
                reference_data['penalties'][object_key] = penalty
            elif object_key:
                logger.warning(f"Invalid ObjectKey type for penalty: {type(object_key)} - {object_key}")
        
    except Exception as e:
        logger.warning(f"Error extracting reference data: {str(e)}")
    
    return reference_data

def _transform_single_offer(
    priced_offer: Dict[str, Any], 
    airline_code: str, 
    reference_data: Dict[str, Any],
    airline_offer: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Transform a single priced offer to FlightOffer format.
    """
    try:
        logger.info(f"Starting transformation for airline {airline_code}, priced_offer keys: {list(priced_offer.keys())}")
        offer_prices = priced_offer.get('OfferPrice', [])
        
        logger.info(f"Found {len(offer_prices)} offer prices")
        if not offer_prices:
            logger.warning("No OfferPrice found, returning None")
            return None
        
        # Use the first offer price for now
        offer_price = offer_prices[0]
        
        # Extract price information using the correct path from actual JSON structure
        price = 0
        currency = ''
        
        # Primary path: OfferPrice[0].RequestedDate.PriceDetail.TotalAmount.SimpleCurrencyPrice (as seen in actual JSON)
        price_detail = offer_price.get('RequestedDate', {}).get('PriceDetail', {})
        if price_detail:
            total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
            price = total_amount.get('value', 0)
            currency = total_amount.get('Code', '')
            logger.info(f"Using OfferPrice PriceDetail: {price} {currency}")
        
        # Fallback to AirlineOffer level if OfferPrice price not found
        if price == 0 and airline_offer and 'TotalPrice' in airline_offer:
            total_price_obj = airline_offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
            price = total_price_obj.get('value', 0)
            currency = total_price_obj.get('Code', '')
            logger.info(f"Using AirlineOffer TotalPrice: {price} {currency}")
        
        # Final fallback to PricedOffer level
        if price == 0:
            priced_offer_total = priced_offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
            price = priced_offer_total.get('value', 0)
            currency = priced_offer_total.get('Code', '')
            logger.info(f"Using PricedOffer level price: {price} {currency}")
        
        # Extract flight associations - check both OfferPrice and PricedOffer level
        associations = offer_price.get('Associations', [])
        if not associations:
            # Check if associations are at PricedOffer level
            associations = priced_offer.get('Associations', [])
        
        if not isinstance(associations, list):
            associations = [associations]
        
        logger.info(f"Found associations: {len(associations)}, structure: {[list(a.keys()) if isinstance(a, dict) else type(a) for a in associations]}")
        
        # Get flight segments and build flight details
        segments = []
        all_segment_refs = []
        
        logger.info(f"Processing {len(associations)} associations")
        for assoc in associations:
            applicable_flight = assoc.get('ApplicableFlight', {})
            segment_refs = applicable_flight.get('FlightSegmentReference', [])
            if not isinstance(segment_refs, list):
                segment_refs = [segment_refs]
            
            logger.info(f"Found {len(segment_refs)} segment references")
            for seg_ref in segment_refs:
                ref_key = seg_ref.get('ref')
                if ref_key:
                    all_segment_refs.append(ref_key)
                    segment_data = reference_data['segments'].get(ref_key, {})
                    logger.info(f"Looking up segment {ref_key}: found={bool(segment_data)}")
                    if segment_data:
                        segments.append(_transform_segment(segment_data, reference_data))
                    else:
                        logger.warning(f"No segment data found for reference {ref_key}")
                else:
                    logger.warning(f"No ref key found in segment reference: {seg_ref}")
        
        logger.info(f"Total segments extracted: {len(segments)}")
        if not segments:
            logger.warning("No segments found, returning None")
            return None
        
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
        
        # Calculate total duration by summing individual segment durations
        total_duration_minutes = 0
        for segment in segments:
            segment_duration = segment.get('duration', 'PT0M')
            total_duration_minutes += _parse_iso_duration(segment_duration)
        
        # Convert total minutes back to "Xh Ym" format
        if total_duration_minutes > 0:
            hours = total_duration_minutes // 60
            minutes = total_duration_minutes % 60
            duration = f"{hours}h {minutes}m"
        else:
            # Fallback to datetime calculation
            duration = _calculate_duration(first_segment, last_segment)
        
        # Extract OfferID from the airline_offer (not priced_offer)
        offer_id = None
        if airline_offer:
            offer_id_obj = airline_offer.get('OfferID')
            if offer_id_obj and isinstance(offer_id_obj, dict):
                offer_id = offer_id_obj.get('value')
                if offer_id:
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
        
        # Build price breakdown - pass airline_offer for correct price extraction
        price_breakdown = _build_price_breakdown(price_detail, priced_offer, airline_offer)
        
        # Build baggage information (simplified)
        
        # Build airline details
        airline_details = {
            'code': airline_code,
            'name': _get_airline_name(airline_code, reference_data),
            'logo': _get_airline_logo_url(airline_code),
            'flightNumber': f"{airline_code}{segments[0].get('flightNumber', '001')}"
        }
        
        # Extract baggage and penalty information
        baggage_info = _extract_baggage_info(offer_price, reference_data)
        
        # Extract penalty information and transform to FareRules structure
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
            'seatsAvailable': 'Available',
            'baggage': baggage_info,
            'penalties': penalty_info,  # Keep original for backward compatibility
            'fareRules': fare_rules,    # New structured format
            'segments': segments,
            'priceBreakdown': price_breakdown
        }
        
        return flight_offer
        
    except Exception as e:
        logger.error(f"Error transforming single offer: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None

def _transform_segment(segment_data: Dict[str, Any], reference_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a flight segment to the expected format using correct JSON paths.
    """
    departure = segment_data.get('Departure', {})
    arrival = segment_data.get('Arrival', {})
    
    # Extract airport codes from the nested structure
    dep_airport_obj = departure.get('AirportCode', {})
    arr_airport_obj = arrival.get('AirportCode', {})
    
    dep_airport = dep_airport_obj.get('value', '') if isinstance(dep_airport_obj, dict) else dep_airport_obj
    arr_airport = arr_airport_obj.get('value', '') if isinstance(arr_airport_obj, dict) else arr_airport_obj
    
    # Get airport details from reference data
    dep_airport_info = reference_data['airports'].get(dep_airport, {'code': dep_airport, 'name': dep_airport})
    arr_airport_info = reference_data['airports'].get(arr_airport, {'code': arr_airport, 'name': arr_airport})
    
    # Extract dates and times - handle both separate time and datetime in date field
    dep_date_raw = departure.get('Date', '')
    dep_time_raw = departure.get('Time', '')
    arr_date_raw = arrival.get('Date', '')
    arr_time_raw = arrival.get('Time', '')
    
    # Handle datetime extraction - some airlines provide full datetime in Date field
    def extract_datetime(date_field, time_field):
        if 'T' in date_field and time_field:
            # Both full datetime and separate time available, use the full datetime
            return date_field
        elif 'T' in date_field:
            # Only full datetime available, extract from date field
            return date_field
        elif date_field and time_field:
            # Separate date and time fields
            return f"{date_field}T{time_field}"
        elif date_field:
            # Only date available, append default time
            return f"{date_field}T00:00"
        else:
            return ''
    
    dep_datetime = extract_datetime(dep_date_raw, dep_time_raw)
    arr_datetime = extract_datetime(arr_date_raw, arr_time_raw)
    
    # Extract time portion - prioritize separate Time field, fallback to datetime extraction
    def extract_time_with_priority(time_field, datetime_str):
        # First priority: use separate Time field if available
        if time_field and time_field.strip():
            # Handle both "HH:MM" and "HH:MM:SS" formats
            time_parts = time_field.split(':')
            if len(time_parts) == 2:
                return f"{time_field}:00"  # Add seconds if missing
            elif len(time_parts) == 3:
                return time_field  # Already has seconds
            else:
                return time_field  # Return as-is if unexpected format
        
        # Fallback: extract from datetime string
        if 'T' in datetime_str:
            time_part = datetime_str.split('T')[1]
            # Remove milliseconds if present
            if '.' in time_part:
                time_part = time_part.split('.')[0]
            return time_part
        return None
    
    dep_time = extract_time_with_priority(dep_time_raw, dep_datetime)
    arr_time = extract_time_with_priority(arr_time_raw, arr_datetime)
    
    # Get airline information with better fallback handling
    airline_code = 'Unknown'
    airline_name = 'Unknown Airline'
    
    # Try to get from MarketingCarrier first
    marketing_carrier = segment_data.get('MarketingCarrier', {})
    if marketing_carrier:
        airline_code = marketing_carrier.get('AirlineID', {}).get('value', 'Unknown')
        # Try to get name directly from segment first
        if 'Name' in marketing_carrier and marketing_carrier['Name']:
            airline_name = marketing_carrier['Name']
        else:
            airline_name = _get_airline_name(airline_code, reference_data)
    
    # Fallback to OperatingCarrier if needed
    if airline_name in ['Unknown', 'Unknown Airline', f"Airline {airline_code}"]:
        operating_carrier = segment_data.get('OperatingCarrier', {})
        if operating_carrier:
            operating_airline_code = operating_carrier.get('AirlineID', {}).get('value', 'Unknown')
            if 'Name' in operating_carrier and operating_carrier['Name']:
                airline_name = operating_carrier['Name']
            else:
                airline_name = _get_airline_name(operating_airline_code, reference_data)
            
            # If we got a valid name from operating carrier, update the code too
            if airline_name not in ['Unknown', 'Unknown Airline', f"Airline {operating_airline_code}"]:
                airline_code = operating_airline_code
    
    # Extract flight duration using correct path: FlightDetail.FlightDuration.Value
    flight_duration = segment_data.get('FlightDetail', {}).get('FlightDuration', {}).get('Value', 'N/A')
    
    # Get flight number
    flight_number = segment_data.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', '001')
    
    # Get airline logo
    airline_logo = _get_airline_logo_url(airline_code)
    
    # Get aircraft name from reference data if available
    aircraft_code_data = segment_data.get('Equipment', {}).get('AircraftCode', {})
    aircraft_code = aircraft_code_data.get('value', 'Unknown') if isinstance(aircraft_code_data, dict) else aircraft_code_data
    aircraft_name = reference_data.get('aircrafts', {}).get(aircraft_code, {}).get('name', aircraft_code)
    
    return {
        'departure': {
            'airport': dep_airport,
            'datetime': dep_datetime,
            'time': dep_time,
            'terminal': dep_airport_info.get('terminal'),
            'airportName': dep_airport_info.get('name')
        },
        'arrival': {
            'airport': arr_airport,
            'datetime': arr_datetime,
            'time': arr_time,
            'terminal': arr_airport_info.get('terminal'),
            'airportName': arr_airport_info.get('name')
        },
        'airline': {
            'name': airline_name,
            'code': airline_code,
            'flightNumber': flight_number,
            'logo': airline_logo
        },
        'aircraft': {
            'code': aircraft_code,
            'name': aircraft_name
        },
        'duration': flight_duration
    }

def _calculate_duration(first_segment: Dict[str, Any], last_segment: Dict[str, Any]) -> str:
    """
    Calculate flight duration between first departure and last arrival.
    """
    try:
        dep_time = first_segment['departure']['datetime']
        arr_time = last_segment['arrival']['datetime']
        
        # Parse datetime strings
        dep_dt = datetime.fromisoformat(dep_time.replace('T', ' '))
        arr_dt = datetime.fromisoformat(arr_time.replace('T', ' '))
        
        duration = arr_dt - dep_dt
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        return f"{hours}h {minutes}m"
    except Exception:
        return "N/A"

def _build_price_breakdown(price_detail: Dict[str, Any], priced_offer: Dict[str, Any] = None, airline_offer: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Build price breakdown using correct path from actual JSON structure
    """
    # Primary source: price_detail from OfferPrice.RequestedDate.PriceDetail (as seen in actual JSON)
    total_price = 0
    currency = 'USD'
    base_fare = 0
    tax_amount = 0
    
    if price_detail:
        total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        base_amount = price_detail.get('BaseAmount', {})
        taxes = price_detail.get('Taxes', {}).get('Total', {})
        
        total_price = total_amount.get('value', 0)
        base_fare = base_amount.get('value', 0)
        tax_amount = taxes.get('value', 0)
        currency = total_amount.get('Code', 'USD')
    
    # Fallback to AirlineOffer level if price_detail not available
    elif airline_offer and 'TotalPrice' in airline_offer:
        airline_offer_total = airline_offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
        total_price = airline_offer_total.get('value', 0)
        currency = airline_offer_total.get('Code', 'USD')
        # For AirlineOffer level, we don't have detailed breakdown, so use total as base fare
        base_fare = total_price
        tax_amount = 0
    
    # Final fallback to PricedOffer level
    elif priced_offer:
        priced_offer_total = priced_offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
        total_price = priced_offer_total.get('value', 0)
        currency = priced_offer_total.get('Code', 'USD')
        base_fare = total_price
        tax_amount = 0
    
    return {
        'baseFare': base_fare,
        'taxes': tax_amount,
        'fees': 0,
        'totalPrice': total_price,
        'currency': currency
    }

def _extract_baggage_info(offer_price: Dict[str, Any], reference_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract baggage information using references from OfferPrice.Associations.ApplicableFlight.FlightSegmentReference.BagDetailAssociation
    and mapping to DataLists.
    """
    baggage_info = {
        'carryOn': 'Not specified',
        'checked': 'Not specified'
    }
    
    try:
        # Get baggage references from OfferPrice.RequestedDate.Associations
        requested_date = offer_price.get('RequestedDate', {})
        associations = requested_date.get('Associations', [])
        if not associations:
            return baggage_info
        
        # Navigate through the correct structure: Associations -> ApplicableFlight -> FlightSegmentReference -> BagDetailAssociation
        for association in associations:
            applicable_flight = association.get('ApplicableFlight', {})
            flight_segment_refs = applicable_flight.get('FlightSegmentReference', [])
            
            for segment_ref in flight_segment_refs:
                bag_detail = segment_ref.get('BagDetailAssociation', {})
                
                # Extract carry-on references
                carry_on_refs = bag_detail.get('CarryOnReferences', [])
                if carry_on_refs and reference_data.get('carry_on_allowances') and baggage_info['carryOn'] == 'Not specified':
                    carry_on_ref = carry_on_refs[0] if isinstance(carry_on_refs, list) else carry_on_refs
                    carry_on_data = reference_data['carry_on_allowances'].get(carry_on_ref)
                    if carry_on_data:
                        description = carry_on_data.get('AllowanceDescription', {}).get('Descriptions', {}).get('Description', [])
                        if description and len(description) > 0:
                            baggage_info['carryOn'] = description[0].get('Text', {}).get('value', 'Not specified')
                
                # Extract checked bag references
                checked_bag_refs = bag_detail.get('CheckedBagReferences', [])
                if checked_bag_refs and reference_data.get('checked_bag_allowances') and baggage_info['checked'] == 'Not specified':
                    checked_ref = checked_bag_refs[0] if isinstance(checked_bag_refs, list) else checked_bag_refs
                    checked_data = reference_data['checked_bag_allowances'].get(checked_ref)
                    if checked_data:
                        description = checked_data.get('AllowanceDescription', {}).get('Descriptions', {}).get('Description', [])
                        if description and len(description) > 0:
                            baggage_info['checked'] = description[0].get('Text', {}).get('value', 'Not specified')
            
            # If we found both carry-on and checked bag info, we can break
            if baggage_info['carryOn'] != 'Not specified' and baggage_info['checked'] != 'Not specified':
                break
    
    except Exception as e:
        logger.error(f"Error extracting baggage info: {e}")
    
    return baggage_info


def _extract_penalty_info(priced_offer: Dict[str, Any], reference_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract penalty information using references from PricedOffer.OfferPrice.FareDetail.FareComponent.FareRules.Penalty.refs
    and mapping to DataLists.PenaltyList.
    """
    penalties = []
    
    try:
        # Navigate to penalty references: PricedOffer.OfferPrice[0].FareDetail.FareComponent[0].FareRules.Penalty.refs
        offer_prices = priced_offer.get('OfferPrice', [])
        if not offer_prices:
            return penalties
        
        offer_price = offer_prices[0]
        fare_detail = offer_price.get('FareDetail', {})
        fare_components = fare_detail.get('FareComponent', [])
        
        if not fare_components:
            return penalties
        
        fare_component = fare_components[0]
        fare_rules = fare_component.get('FareRules', {})
        penalty_refs = fare_rules.get('Penalty', {}).get('refs', [])
        
        # Map penalty references to actual penalty data
        if penalty_refs and reference_data.get('penalties'):
            for penalty_ref in penalty_refs:
                penalty_data = reference_data['penalties'].get(penalty_ref)
                if penalty_data:
                    details_data = penalty_data.get('Details', {})
                    details = details_data.get('Detail', []) if isinstance(details_data, dict) else []
                    for detail in details:
                        # Ensure detail is a dictionary before calling .get()
                        if not isinstance(detail, dict):
                            logger.warning(f"Invalid detail type: {type(detail)}, expected dict")
                            continue
                        penalty_type = detail.get('Type', 'Unknown')
                        application_code = detail.get('Application', {}).get('Code', '')
                        
                        # Map application codes as specified by user
                        application_desc = {
                            '1': 'After Departure NO Show',
                            '2': 'Prior to Departure',
                            '3': 'After Departure',
                            '4': 'Before Departure No Show'
                        }.get(application_code, f"Code {application_code}")
                        
                        # Extract penalty amounts
                        amounts_data = detail.get('Amounts', {})
                        amounts = amounts_data.get('Amount', []) if isinstance(amounts_data, dict) else []
                        penalty_amount = 0
                        currency = 'USD'  # Default currency
                        remarks = []
                        
                        # Try to get default currency from first amount if available
                        if amounts and isinstance(amounts, list) and len(amounts) > 0:
                            first_amount = amounts[0]
                            if isinstance(first_amount, dict):
                                currency_amount = first_amount.get('CurrencyAmountValue', {})
                                if isinstance(currency_amount, dict):
                                    currency = currency_amount.get('Code', 'USD')
                        
                        for amount in amounts:
                            # Ensure amount is a dictionary before calling .get()
                            if not isinstance(amount, dict):
                                logger.warning(f"Invalid amount type: {type(amount)}, expected dict")
                                continue
                                
                            currency_amount = amount.get('CurrencyAmountValue', {})
                            penalty_amount = currency_amount.get('value', 0)
                            currency = currency_amount.get('Code', 'USD')
                            
                            fee_remarks = amount.get('ApplicableFeeRemarks', {}).get('Remark', [])
                            for remark in fee_remarks:
                                if isinstance(remark, dict):
                                    remarks.append(remark.get('value', ''))
                                else:
                                    remarks.append(str(remark))
                        
                        penalties.append({
                            'type': penalty_type,
                            'application': application_desc,
                            'amount': penalty_amount,
                            'currency': currency,
                            'remarks': remarks,
                            'refundable': penalty_data.get('RefundableInd', False),
                            'cancelFee': penalty_data.get('CancelFeeInd', False)
                        })
    
    except Exception as e:
        logger.error(f"Error extracting penalty info: {e}")
    
    return penalties


from utils.airline_data import get_airline_name, AIRLINE_NAMES

def _get_airline_logo_url(airline_code):
    """Get the logo URL for an airline code.
    
    Args:
        airline_code: 2-letter IATA airline code
        
    Returns:
        str: URL to the airline logo or None if not available
    """
    if not airline_code:
        return None
    
    # Clean and normalize the airline code
    code = str(airline_code).strip().upper()
    
    # List of available logos - we can expand this as needed
    available_logos = {"AA", "AC", "AF", "AI", "AS", "AV", "B6", "BA", "CM", "CX", "DL", "EK", "EY", "F9", "FR", "GA", "IB", "JL", "JQ", "KL", "KQ", "LA", "LH", "LX", "MH", "NK", "NZ", "OZ", "PR", "QF", "QR", "SK", "SQ", "SV", "TK", "TP", "UA", "UX", "VA", "VN", "VS", "WN", "WY"}
    
    if code in available_logos:
        return f"/airlines/{code}.svg"
    
    return None  # No logo available

def _get_airline_name(airline_code: str, reference_data: Dict[str, Any] = None) -> str:
    """
    Get airline name by checking multiple sources in order:
    1. The airlines dictionary in reference_data
    2. MarketingCarrier in segments
    3. OperatingCarrier in segments
    4. Flight segments in reference data
    5. Known airline codes mapping from AIRLINE_NAMES
    6. Generic fallback with code
    
    Args:
        airline_code: 2-letter IATA airline code
        reference_data: Dictionary containing airlines and flight segments
        
    Returns:
        Airline name if found, or formatted code if not found
    """
    if not airline_code:
        logger.debug("Empty airline code provided")
        return "Unknown Airline"
        
    # Clean and normalize the code
    code = str(airline_code).strip().upper()
    
    # 0. First check if we have a direct mapping in AIRLINE_NAMES
    if code in AIRLINE_NAMES:
        return AIRLINE_NAMES[code]
    
    # 1. Check reference_data.airlines first (from segments)
    if reference_data and 'airlines' in reference_data and code in reference_data['airlines']:
        name = reference_data['airlines'][code]
        if name and name != 'None':
            return name
    
    # 2. Check reference_data.flights for marketing/operating carrier info
    if reference_data and 'flights' in reference_data:
        for flight_key, flight in reference_data['flights'].items():
            try:
                # Check marketing carrier
                marketing_carrier = flight.get('MarketingCarrier', {})
                if marketing_carrier:
                    carrier_code = marketing_carrier.get('AirlineID', {}).get('value') if isinstance(marketing_carrier.get('AirlineID'), dict) else marketing_carrier.get('AirlineID')
                    if carrier_code and str(carrier_code).strip().upper() == code and 'Name' in marketing_carrier:
                        name = marketing_carrier['Name']
                        if name and name != 'None':
                            return name
                
                # Check operating carrier
                operating_carrier = flight.get('OperatingCarrier', {})
                if operating_carrier:
                    carrier_code = operating_carrier.get('AirlineID', {}).get('value') if isinstance(operating_carrier.get('AirlineID'), dict) else operating_carrier.get('AirlineID')
                    if carrier_code and str(carrier_code).strip().upper() == code and 'Name' in operating_carrier:
                        name = operating_carrier['Name']
                        if name and name != 'None':
                            return name
            except (KeyError, AttributeError) as e:
                logger.debug(f"Error processing flight {flight_key}: {str(e)}")
    
    # 3. Check reference_data.segments for carrier info
    if reference_data and 'segments' in reference_data:
        for segment_key, segment in reference_data['segments'].items():
            try:
                # Check marketing carrier in segment
                marketing_carrier = segment.get('MarketingCarrier', {})
                if marketing_carrier:
                    carrier_code = marketing_carrier.get('AirlineID', {}).get('value') if isinstance(marketing_carrier.get('AirlineID'), dict) else marketing_carrier.get('AirlineID')
                    if carrier_code and str(carrier_code).strip().upper() == code and 'Name' in marketing_carrier:
                        name = marketing_carrier['Name']
                        if name and name != 'None':
                            return name
                            
                # Also check operating carrier in segment
                operating_carrier = segment.get('OperatingCarrier', {})
                if operating_carrier:
                    carrier_code = operating_carrier.get('AirlineID', {}).get('value') if isinstance(operating_carrier.get('AirlineID'), dict) else operating_carrier.get('AirlineID')
                    if carrier_code and str(carrier_code).strip().upper() == code and 'Name' in operating_carrier:
                        name = operating_carrier['Name']
                        if name and name != 'None':
                            return name
            except (KeyError, AttributeError) as e:
                logger.debug(f"Error processing segment {segment_key}: {str(e)}")
    
    # 4. Try to get from the imported get_airline_name function
    name = get_airline_name(code, log_missing=False)
    if name and name != f"Airline {code}":
        return name
    
    # 5. Final fallback - check if we have the code in our hardcoded AIRLINE_NAMES
    if code in AIRLINE_NAMES:
        return AIRLINE_NAMES[code]
    
    # 6. Last resort - return a generic name with the code
    logger.debug(f"Could not find airline name for code: {code}")
    return f"Airline {code}"

def _transform_penalties_to_fare_rules(penalties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transform penalty list into structured FareRules format expected by frontend.
    """
    fare_rules = {
        'changeFee': False,
        'refundable': False,
        'exchangeable': False,
        'penalties': [],
        'additionalRestrictions': []
    }
    
    for penalty in penalties:
        penalty_type = penalty.get('type', '').lower()
        application = penalty.get('application', '')
        amount = penalty.get('amount', 0)
        currency = penalty.get('currency', '')
        remarks = penalty.get('remarks', [])
        refundable = penalty.get('refundable', False)
        
        # Determine the category based on type and application
        if penalty_type == 'change':
            fare_rules['exchangeable'] = True
            if amount > 0:
                fare_rules['changeFee'] = True
            
            # Map to specific change categories
            if 'prior to departure' in application.lower():
                fare_rules['changeBeforeDeparture'] = {
                    'allowed': True,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None
                }
            elif 'after departure' in application.lower():
                fare_rules['changeAfterDeparture'] = {
                    'allowed': True,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None
                }
            elif 'no show' in application.lower():
                fare_rules['changeNoShow'] = {
                    'allowed': True,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None
                }
        
        elif penalty_type == 'cancel':
            fare_rules['refundable'] = refundable
            
            # Calculate refund percentage (simplified logic)
            refund_percentage = 100 if refundable and amount == 0 else (100 - (amount / 100)) if amount > 0 else 0
            
            # Map to specific cancel categories
            if 'prior to departure' in application.lower():
                fare_rules['cancelBeforeDeparture'] = {
                    'allowed': True,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None,
                    'refundPercentage': refund_percentage
                }
            elif 'after departure' in application.lower():
                fare_rules['cancelAfterDeparture'] = {
                    'allowed': True,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None,
                    'refundPercentage': refund_percentage
                }
            elif 'no show' in application.lower():
                fare_rules['cancelNoShow'] = {
                    'allowed': True,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None,
                    'refundPercentage': refund_percentage
                }
                # Also set noShow field
                fare_rules['noShow'] = {
                    'refundable': refundable,
                    'fee': amount,
                    'currency': currency,
                    'conditions': ', '.join(remarks) if remarks else None,
                    'refundPercentage': refund_percentage
                }
        
        # Add to penalties list for backward compatibility
        fare_rules['penalties'].append(f"{penalty_type.title()} - {application}: {amount} {currency}")
        
        # Add remarks to additional restrictions
        if remarks:
            fare_rules['additionalRestrictions'].extend(remarks)
    
    # Remove duplicates from additional restrictions
    fare_rules['additionalRestrictions'] = list(set(fare_rules['additionalRestrictions']))
    
    return fare_rules

def _parse_iso_duration(duration_str):
    """
    Parse ISO 8601 duration string (e.g., "PT2H45M") to total minutes.
    
    Args:
        duration_str (str): ISO 8601 duration string
        
    Returns:
        int: Total duration in minutes
    """
    if not duration_str or not duration_str.startswith('PT'):
        return 0
    
    import re
    
    # Remove 'PT' prefix
    duration_str = duration_str[2:]
    
    # Extract hours and minutes using regex
    hours_match = re.search(r'(\d+)H', duration_str)
    minutes_match = re.search(r'(\d+)M', duration_str)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    
    return hours * 60 + minutes