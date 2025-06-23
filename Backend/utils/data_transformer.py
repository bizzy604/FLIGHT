"""Data transformation utilities for converting Verteil API responses to frontend-compatible formats."""

import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def transform_verteil_to_frontend(
    verteil_response: Dict[str, Any], 
    enable_roundtrip: bool = False,
    frontend_offer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform Verteil API air shopping response to frontend-compatible FlightOffer objects.
    
    Args:
        verteil_response: Raw response from Verteil API
        enable_roundtrip: Whether to enable round trip transformation logic
        frontend_offer_id: The offer ID from the frontend to prioritize in transformation
        
    Returns:
        Dictionary with 'offers' and 'reference_data' keys
    """
    logger = logging.getLogger(__name__)
    
    try:
        # If roundtrip transformation is enabled, use the enhanced roundtrip logic
        if enable_roundtrip:
            from utils.data_transformer_roundtrip import transform_verteil_to_frontend_with_roundtrip
            return transform_verteil_to_frontend_with_roundtrip(verteil_response)
        
        flight_offers = []
        
        # Debug logging to understand the response structure
        logger.info("=" * 50)
        logger.info("STARTING TRANSFORMATION")
        logger.info("=" * 50)
        logger.info(f"Top-level response keys: {list(verteil_response.keys())}")
        
        # Log the structure of the response for debugging
        logger.debug("Response structure sample:" + "\n" + 
                    "\n".join(f"- {k}: {type(v).__name__}" for k, v in verteil_response.items()))
        
        # Check for PricedFlightOffers at root level (new structure)
        if 'PricedFlightOffers' in verteil_response and 'PricedFlightOffer' in verteil_response['PricedFlightOffers']:
            logger.info("Found PricedFlightOffers at root level")
            priced_offers = verteil_response['PricedFlightOffers']['PricedFlightOffer']
            if not isinstance(priced_offers, list):
                priced_offers = [priced_offers]
                
            logger.info(f"Found {len(priced_offers)} PricedFlightOffer(s)")
            
            # Extract reference data for lookups
            reference_data = _extract_reference_data(verteil_response)
            logger.info(f"Extracted reference data: {len(reference_data.get('flights', {}))} flights, "
                       f"{len(reference_data.get('segments', {}))} segments")
            
            # Process each priced offer
            for i, priced_offer in enumerate(priced_offers):
                try:
                    # Extract airline code from the offer
                    airline_code = priced_offer.get('OfferID', {}).get('Owner', 'UNKNOWN')
                    logger.info(f"Processing PricedFlightOffer {i+1}, airline: {airline_code}")
                    
                    # Transform the offer, passing the frontend_offer_id if available
                    flight_offer = _transform_single_offer(
                        priced_offer=priced_offer,
                        airline_code=airline_code,
                        reference_data=reference_data,
                        airline_offer=priced_offer,  # Pass the full offer for price extraction
                        frontend_offer_id=frontend_offer_id
                    )
                    
                    if flight_offer:
                        flight_offers.append(flight_offer)
                        logger.info(f"Successfully transformed PricedFlightOffer {i+1}")
                    else:
                        logger.warning(f"Failed to transform PricedFlightOffer {i+1}")
                        
                except Exception as e:
                    logger.error(f"Error processing PricedFlightOffer {i+1}: {str(e)}", exc_info=True)
                    continue
        
        # Check for legacy OffersGroup structure
        if not flight_offers and 'OffersGroup' in verteil_response:
            logger.info("Processing legacy OffersGroup structure")
            offers_group = verteil_response.get('OffersGroup', {})
            logger.info(f"OffersGroup found: {offers_group is not None}, keys: {list(offers_group.keys()) if offers_group else 'None'}")
            
            airline_offers = offers_group.get('AirlineOffers', [])
            if not isinstance(airline_offers, list):
                airline_offers = [airline_offers] if airline_offers else []
                
            logger.info(f"AirlineOffers found: {len(airline_offers) if isinstance(airline_offers, list) else 'Not a list' if airline_offers else 'None'}")
            
            # Extract reference data for lookups if not already done
            if 'reference_data' not in locals():
                reference_data = _extract_reference_data(verteil_response)
                logger.info(f"Reference data extracted: flights={len(reference_data.get('flights', {}))}, segments={len(reference_data.get('segments', {}))}")
            
            for i, airline_offer_group in enumerate(airline_offers):
                # Skip if not a dictionary
                if not isinstance(airline_offer_group, dict):
                    logger.warning(f"Skipping invalid airline_offer_group at index {i}: {type(airline_offer_group)}")
                    continue
                    
                # Extract airline code using robust method
                airline_code = _extract_airline_code_robust(airline_offer_group)
                airline_offers_list = airline_offer_group.get('AirlineOffer', [])
                
                # Ensure airline_offers_list is a list
                if not isinstance(airline_offers_list, list):
                    airline_offers_list = [airline_offers_list] if airline_offers_list else []
                    
                logger.info(f"Processing airline offer group {i}: airline_code={airline_code}, offers_count={len(airline_offers_list)}")
                
                # Debug the airline offer group structure
                logger.info(f"Airline offer group keys: {list(airline_offer_group.keys())}")
                
                for j, offer in enumerate(airline_offers_list):
                    try:
                        if not isinstance(offer, dict):
                            logger.warning(f"Skipping invalid offer at index {j} in airline_offer_group {i}: {type(offer)}")
                            continue
                            
                        # Transform the offer - pass the PricedOffer if it exists, otherwise the offer itself
                        priced_offer = offer.get('PricedOffer', offer)
                        logger.info(f"Processing offer {j} in airline_offer_group {i}, priced_offer keys: {list(priced_offer.keys()) if isinstance(priced_offer, dict) else 'Not a dict'})")
                        
                        # Ensure we're passing the correct airline_offer structure
                        airline_offer = offer  # The full AirlineOffer from AirlineOffers list
                        
                        flight_offer = _transform_single_offer(
                            priced_offer=priced_offer,
                            airline_code=airline_code,
                            reference_data=reference_data,
                            airline_offer=airline_offer,  # Pass the full AirlineOffer for ID extraction
                            frontend_offer_id=frontend_offer_id
                        )
                        
                        if flight_offer:
                            flight_offers.append(flight_offer)
                            logger.info(f"Successfully transformed offer {j+1} in airline_offer_group {i}")
                        else:
                            logger.warning(f"Failed to transform offer {j+1} in airline_offer_group {i}")
                            
                    except Exception as e:
                        logger.error(f"Error processing offer {j+1} in airline_offer_group {i}: {str(e)}", exc_info=True)
                        continue
        
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
    airline_offer: Dict[str, Any] = None,
    frontend_offer_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Transform a single priced offer to FlightOffer format.
    """
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"=== Starting transformation for airline {airline_code} ===")
        logger.info(f"priced_offer keys: {list(priced_offer.keys())}")
        
        # Log the full priced_offer for debugging
        logger.debug(f"Full priced_offer: {json.dumps(priced_offer, indent=2, default=str)}")
        
        # Get offer prices - handle both list and single object cases
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
        
        # Extract flight associations - check in RequestedDate first, then OfferPrice, then PricedOffer level
        associations = []
        
        # 1. Check in RequestedDate
        requested_date = offer_price.get('RequestedDate', {})
        if requested_date and isinstance(requested_date, dict):
            associations = requested_date.get('Associations', [])
        
        # 2. If not found, check directly in OfferPrice
        if not associations:
            associations = offer_price.get('Associations', [])
            
        # 3. If still not found, check in PricedOffer
        if not associations:
            associations = priced_offer.get('Associations', [])
        
        # Ensure associations is a list
        if not isinstance(associations, list):
            associations = [associations] if associations is not None else []
            
        logger.info(f"Found {len(associations)} associations in RequestedDate/OfferPrice/PricedOffer")
        
        logger.info(f"Found associations: {len(associations)}, structure: {[list(a.keys()) if isinstance(a, dict) else type(a) for a in associations]}")
        
        # Get flight segments and build flight details
        segments = []
        all_segment_refs = []
        
        logger.info(f"Processing {len(associations)} associations")
        logger.info(f"Available segment references in reference_data: {list(reference_data['segments'].keys())}")
        
        for assoc in associations:
            applicable_flight = assoc.get('ApplicableFlight', {})
            logger.info(f"Processing ApplicableFlight: {applicable_flight.keys()}")
            
            segment_refs = applicable_flight.get('FlightSegmentReference', [])
            if not isinstance(segment_refs, list):
                segment_refs = [segment_refs] if segment_refs else []
            
            logger.info(f"Found {len(segment_refs)} segment references in this association")
            
            for seg_ref in segment_refs:
                if not isinstance(seg_ref, dict):
                    logger.warning(f"Unexpected segment reference type: {type(seg_ref)}, value: {seg_ref}")
                    continue
                    
                ref_key = seg_ref.get('ref')
                if ref_key:
                    all_segment_refs.append(ref_key)
                    segment_data = reference_data['segments'].get(ref_key)
                    
                    if segment_data:
                        logger.info(f"Found segment data for ref {ref_key}")
                        try:
                            transformed_segment = _transform_segment(segment_data, reference_data)
                            segments.append(transformed_segment)
                            logger.info(f"Successfully transformed segment {ref_key}")
                        except Exception as e:
                            logger.error(f"Error transforming segment {ref_key}: {str(e)}", exc_info=True)
                    else:
                        logger.warning(f"No segment data found in reference_data['segments'] for ref: {ref_key}")
                        logger.debug(f"Available segment refs: {list(reference_data['segments'].keys())}")
                else:
                    logger.warning(f"No ref key found in segment reference: {seg_ref}")
                    logger.debug(f"Segment reference structure: {json.dumps(seg_ref, indent=2, default=str)}")
        
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
        
        # 0. First priority: Use the offer ID from the frontend if provided
        if frontend_offer_id and not frontend_offer_id.startswith('fallback_'):
            offer_id = frontend_offer_id
            logger.info(f"Using offer ID from frontend: {offer_id}")
        else:
            # 1. Try to get OfferID from the correct path: AirlineOffer.OfferID.value
            offer_id = None
            
            # First try to get from airline_offer if available (most likely location in AirShopping response)
            if airline_offer and 'OfferID' in airline_offer:
                if isinstance(airline_offer['OfferID'], dict) and 'value' in airline_offer['OfferID']:
                    offer_id = airline_offer['OfferID']['value']
                    logger.info(f"Using OfferID from airline_offer.OfferID.value: {offer_id}")
                elif isinstance(airline_offer['OfferID'], str):
                    offer_id = airline_offer['OfferID']
                    logger.info(f"Using string OfferID from airline_offer: {offer_id}")
            
            # 2. If not found, try to get from priced_offer
            if not offer_id and 'OfferID' in priced_offer:
                if isinstance(priced_offer['OfferID'], dict) and 'value' in priced_offer['OfferID']:
                    offer_id = priced_offer['OfferID']['value']
                    logger.info(f"Using OfferID from priced_offer.OfferID.value: {offer_id}")
                elif isinstance(priced_offer['OfferID'], str):
                    offer_id = priced_offer['OfferID']
                    logger.info(f"Using string OfferID from priced_offer: {offer_id}")
            
            # 3. Try OfferRefID as fallback
            if not offer_id and airline_offer and 'OfferRefID' in airline_offer:
                offer_id = airline_offer['OfferRefID']
                logger.info(f"Using OfferRefID from airline_offer as fallback: {offer_id}")
            
            # 4. Generate fallback ID if still not found
            if not offer_id:
                import uuid
                offer_id = f"fallback_{str(uuid.uuid4())[:8]}"
                logger.warning(f"No valid OfferID found, generated fallback ID: {offer_id}")
        
        # Ensure we have a string ID even if it's a fallback
        offer_id = str(offer_id)
            
        # Log the final offer ID being used
        logger.info(f"Final OfferID: {offer_id}")
        
        # Store the offer ID in the priced_offer for reference
        if 'OfferID' not in priced_offer:
            priced_offer['OfferID'] = {'value': offer_id}
        
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
        
        # Initialize fare_rules with default values
        fare_rules = _create_segment_fare_rules()
        
        # Extract penalty information using the dedicated function
        penalty_info = _extract_penalty_info(priced_offer, reference_data)
        
        # Ensure penalty_info is a list before checking its length
        if not isinstance(penalty_info, list):
            logger.warning(f"Expected list of penalties but got {type(penalty_info)}. Converting to empty list.")
            penalty_info = []
            
        logger.info(f"Extracted {len(penalty_info)} penalty entries from reference data")
        
        if penalty_info:
            # Log the first penalty for debugging
            logger.info(f"Processing {len(penalty_info)} penalties. First penalty: {json.dumps(penalty_info[0], indent=2, default=str) if penalty_info else 'None'}")
            
            try:
                # Transform penalties to fare rules
                fare_rules = _transform_penalties_to_fare_rules(penalty_info)
                logger.info(f"Successfully transformed penalties to fare rules")
                
                # Log a summary of the fare rules
                if fare_rules.get('changeFee') or fare_rules.get('cancelFee') or fare_rules.get('refundable'):
                    logger.info(f"Fare rules summary - Change allowed: {fare_rules.get('changeable')}, "
                                f"Refundable: {fare_rules.get('refundable')}, "
                                f"Change fee: {fare_rules.get('changeFee')}, "
                                f"Cancel fee: {fare_rules.get('cancelFee')}")
            except Exception as e:
                logger.error(f"Error transforming penalties to fare rules: {e}", exc_info=True)
                # Return default fare rules on error
                fare_rules = _create_segment_fare_rules()
        else:
            logger.warning("No penalty information found in the offer")
            fare_rules = _create_segment_fare_rules()
        
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
    
    Args:
        priced_offer: The PricedOffer dictionary from the API response
        reference_data: Dictionary containing reference data including penalties
        
    Returns:
        List of penalty dictionaries with segment references
    """
    logger = logging.getLogger(__name__)
    penalties = []
    
    try:
        logger.info("=== Starting penalty info extraction ===")
        logger.info(f"Reference data has {len(reference_data.get('penalties', {}))} penalties available")
        
        # Log the structure of the priced_offer for debugging
        logger.debug(f"Priced offer keys: {list(priced_offer.keys())}")
        if 'OfferPrice' in priced_offer:
            logger.debug(f"OfferPrice type: {type(priced_offer['OfferPrice'])}")
            if isinstance(priced_offer['OfferPrice'], list) and priced_offer['OfferPrice']:
                logger.debug(f"First OfferPrice keys: {list(priced_offer['OfferPrice'][0].keys())}")
                if 'FareDetail' in priced_offer['OfferPrice'][0]:
                    logger.debug(f"FareDetail type: {type(priced_offer['OfferPrice'][0]['FareDetail'])}")
        
        # Navigate to penalty references: PricedOffer.OfferPrice[0].FareDetail.FareComponent[0].FareRules.Penalty.refs
        offer_prices = priced_offer.get('OfferPrice', [])
        if not offer_prices:
            logger.debug("No OfferPrice found in priced_offer")
            return penalties
        
        logger.debug(f"Found {len(offer_prices)} offer prices")
        offer_price = offer_prices[0]  # Take first offer price
        
        fare_detail = offer_price.get('FareDetail', {})
        if not fare_detail:
            logger.debug("No FareDetail found in offer price")
            return penalties
            
        fare_components = fare_detail.get('FareComponent', [])
        if not fare_components:
            logger.debug("No FareComponent found in fare detail")
            return penalties
            
        logger.debug(f"Processing {len(fare_components)} fare components")
        
        # Process each fare component to get segment-specific penalties
        for i, fare_component in enumerate(fare_components):
            try:
                if not isinstance(fare_component, dict):
                    logger.warning(f"Fare component {i} is not a dictionary")
                    continue
                    
                logger.debug(f"Processing fare component {i}")
                
                # Get segment references from fare component
                segment_refs = []
                if 'refs' in fare_component:
                    segment_refs = [fare_component['refs']] if isinstance(fare_component['refs'], str) else fare_component['refs']
                logger.debug(f"Segment refs for component {i}: {segment_refs}")
                
                # Get penalty references from fare rules
                fare_rules = fare_component.get('FareRules', {})
                penalty_refs = []
                
                # Handle different possible structures of penalty references
                if isinstance(fare_rules, dict):
                    penalty_data = fare_rules.get('Penalty', {})
                    if isinstance(penalty_data, dict):
                        penalty_refs = penalty_data.get('refs', [])
                        if not isinstance(penalty_refs, list):
                            penalty_refs = [penalty_refs] if penalty_refs else []
                
                logger.debug(f"Found {len(penalty_refs)} penalty refs in fare component {i}")
                
                # Map penalty references to actual penalty data with segment references
                if penalty_refs and reference_data.get('penalties'):
                    for penalty_ref in penalty_refs:
                        if not penalty_ref or not isinstance(penalty_ref, str):
                            logger.warning(f"Skipping invalid penalty ref: {penalty_ref}")
                            continue
                            
                        penalty_data = reference_data['penalties'].get(penalty_ref)
                        if not penalty_data or not isinstance(penalty_data, dict):
                            logger.debug(f"No penalty data found for ref: {penalty_ref}")
                            continue
                            
                        logger.debug(f"Processing penalty data for ref {penalty_ref}")
                        
                        # Extract penalty details
                        details_data = penalty_data.get('Details', {})
                        details = []
                        
                        if isinstance(details_data, dict):
                            details_list = details_data.get('Detail', [])
                            if isinstance(details_list, list):
                                details = [d for d in details_list if isinstance(d, dict)]
                            elif isinstance(details_list, dict):
                                details = [details_list]
                        
                        if not details:
                            logger.debug(f"No valid details found for penalty ref: {penalty_ref}")
                            continue
                            
                        for detail in details:
                            try:
                                penalty_type = detail.get('Type', 'Unknown')
                                application_code = str(detail.get('Application', {}).get('Code', ''))
                                
                                # Map application codes based on official documentation
                                application_mapping = {
                                    '1': 'After Departure',  # Post-departure
                                    '2': 'Before Departure',  # Pre-departure
                                    '3': 'No Show',
                                    '4': 'Unknown'  # Default to most restrictive
                                }
                                
                                application_desc = application_mapping.get(application_code, f"Code {application_code}")
                                logger.debug(f"Mapped penalty code {application_code} to: {application_desc}")
                                
                                # Extract penalty amounts
                                amounts_data = detail.get('Amounts', {})
                                amounts = []
                                
                                if isinstance(amounts_data, dict):
                                    amounts_list = amounts_data.get('Amount', [])
                                    if isinstance(amounts_list, list):
                                        amounts = [a for a in amounts_list if isinstance(a, dict)]
                                    elif isinstance(amounts_list, dict):
                                        amounts = [amounts_list]
                                
                                penalty_amount = 0.0
                                currency = 'USD'  # Default currency
                                remarks = []
                                
                                # Process amounts to get the highest penalty
                                for amount in amounts:
                                    try:
                                        currency_amount = amount.get('CurrencyAmountValue', {})
                                        if not isinstance(currency_amount, dict):
                                            continue
                                            
                                        amount_value = float(currency_amount.get('value', 0))
                                        amount_currency = currency_amount.get('Code', 'USD')
                                        
                                        # Track the highest penalty amount
                                        if amount_value > penalty_amount:
                                            penalty_amount = amount_value
                                            currency = amount_currency
                                            
                                        # Extract remarks
                                        fee_remarks = amount.get('ApplicableFeeRemarks', {})
                                        remark_list = fee_remarks.get('Remark', [])
                                        if isinstance(remark_list, list):
                                            for remark in remark_list:
                                                if isinstance(remark, dict):
                                                    remark_text = remark.get('value', '')
                                                else:
                                                    remark_text = str(remark)
                                                if remark_text and remark_text not in remarks:
                                                    remarks.append(remark_text)
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"Error processing amount: {e}")
                                        continue
                                
                                # Create penalty with segment references
                                penalty = {
                                    'type': str(penalty_type),
                                    'application': application_desc,
                                    'amount': penalty_amount,
                                    'currency': currency,
                                    'remarks': remarks,
                                    'refundable': bool(penalty_data.get('RefundableInd', False)),
                                    'cancelFee': bool(penalty_data.get('CancelFeeInd', False)),
                                    'segment_refs': segment_refs  # Add segment references
                                }
                                
                                penalties.append(penalty)
                                logger.debug(f"Added penalty: {penalty}")
                                
                            except Exception as e:
                                logger.error(f"Error processing penalty detail: {e}", exc_info=True)
                                continue
                                
            except Exception as e:
                logger.error(f"Error processing fare component {i}: {e}", exc_info=True)
                continue
    
    except Exception as e:
        logger.error(f"Error extracting penalty info: {e}", exc_info=True)
    
    logger.info(f"Extracted {len(penalties)} penalties")
    
    # Ensure we always return a list, even if empty
    if not isinstance(penalties, list):
        logger.warning(f"Penalties is not a list: {type(penalties)}. Converting to empty list.")
        return []
        
    # Ensure all items in the list are dictionaries
    valid_penalties = []
    for i, penalty in enumerate(penalties):
        if isinstance(penalty, dict):
            valid_penalties.append(penalty)
        else:
            logger.warning(f"Skipping non-dict penalty at index {i}: {penalty}")
    
    logger.info(f"Returning {len(valid_penalties)} valid penalties")
    return valid_penalties


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

def _organize_penalties_by_segment(penalties: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Organize penalties by segment reference.
    
    Args:
        penalties: List of penalty dictionaries with segment references
        
    Returns:
        Dictionary mapping segment references to their penalties
    """
    segment_penalties = {}
    
    for penalty in penalties:
        segment_refs = penalty.get('segment_refs', [])
        if not segment_refs:
            # If no segment reference, apply to all segments
            segment_refs = ['all']
            
        for segment_ref in segment_refs:
            if segment_ref not in segment_penalties:
                segment_penalties[segment_ref] = []
            segment_penalties[segment_ref].append(penalty)
            
    return segment_penalties

def _create_segment_fare_rules() -> Dict[str, Any]:
    """
    Create a new segment fare rules structure.
    
    Returns:
        Dictionary with initialized fare rules for a segment
    """
    return {
        # Change rules
        'changeBeforeDeparture': {
            'allowed': False,
            'fee': 0,
            'currency': '',
            'conditions': []
        },
        'changeAfterDeparture': {
            'allowed': False,
            'fee': 0,
            'currency': '',
            'conditions': []
        },
        'changeNoShow': {
            'allowed': False,
            'fee': 0,
            'currency': '',
            'conditions': []
        },
        
        # Cancel rules
        'cancelBeforeDeparture': {
            'allowed': False,
            'refundPercentage': 0,
            'fee': 0,
            'currency': '',
            'conditions': []
        },
        'cancelAfterDeparture': {
            'allowed': False,
            'refundPercentage': 0,
            'fee': 0,
            'currency': '',
            'conditions': []
        },
        'cancelNoShow': {
            'allowed': False,
            'refundPercentage': 0,
            'fee': 0,
            'currency': '',
            'conditions': []
        },
        
        # No show rules
        'noShow': {
            'allowed': False,
            'refundable': False,
            'conditions': []
        },
        
        # Additional fields
        'changeFee': False,
        'refundable': False,
        'exchangeable': False,
        'changeable': False,
        'penalties': [],
        'additionalRestrictions': []
    }

def _apply_penalty_to_rules(penalty: Union[Dict[str, Any], str], rules: Dict[str, Any]) -> None:
    """
    Apply a single penalty to the given rules with enhanced logging and support for all penalty types.
    
    Args:
        penalty: Dictionary or string containing penalty details. If dict, should contain:
                - type: Type of penalty (change, cancel, no-show, etc.)
                - application: When the penalty applies (before/after departure, no-show)
                - amount: Fee amount
                - currency: Currency code
                - remarks: List of remarks or conditions
                - refundable: Whether the penalty is refundable
                - segment_ref: Optional segment reference for per-segment penalties
        rules: Rules dictionary to update with penalty information
    
    Returns:
        None: Modifies the rules dictionary in place
    """
    logger = logging.getLogger(__name__)
    
    # Input validation
    if penalty is None:
        logger.warning("Received None penalty, skipping")
        return
        
    # Handle string penalties by converting to a dictionary
    if isinstance(penalty, str):
        logger.warning(f"Received string penalty, converting to dict: {penalty}")
        penalty = {'type': penalty, 'application': '', 'amount': 0, 'currency': 'USD', 'remarks': []}
    
    if not isinstance(penalty, dict):
        logger.error(f"Invalid penalty type: {type(penalty)}. Expected dict or str.")
        return
    
    if not isinstance(rules, dict):
        logger.error(f"Invalid rules type: {type(rules)}. Expected dict.")
        return
    
    # Extract and normalize penalty data with type checking
    try:
        penalty_type = str(penalty.get('type', '')).strip()
        application = str(penalty.get('application', '')).strip()
        
        # Safely convert amount to float with error handling
        try:
            amount = float(penalty.get('amount', 0) or 0)
        except (ValueError, TypeError):
            logger.warning(f"Invalid penalty amount: {penalty.get('amount')}. Defaulting to 0.")
            amount = 0.0
            
        currency = str(penalty.get('currency', '')).strip().upper() or 'USD'  # Default to USD if not specified
        
        # Ensure remarks is a list of strings
        remarks = penalty.get('remarks', [])
        if isinstance(remarks, str):
            remarks = [remarks] if remarks.strip() else []
        elif not isinstance(remarks, list):
            logger.warning(f"Unexpected remarks type: {type(remarks)}. Converting to list.")
            remarks = [str(remarks)] if remarks else []
            
        # Clean up remarks
        remarks = [str(r).strip() for r in remarks if r and str(r).strip()]
        
        refundable = bool(penalty.get('refundable', False))
        segment_ref = penalty.get('segment_ref')
        
    except Exception as e:
        logger.error(f"Error processing penalty data: {e}", exc_info=True)
        return
    
    # Normalize values for case-insensitive comparison
    penalty_type_lower = penalty_type.lower()
    application_lower = application.lower()
    
    # Log penalty processing details
    logger.debug(
        f"Applying penalty - Type: '{penalty_type}', Application: '{application}', "
        f"Amount: {amount} {currency}, Refundable: {refundable}, "
        f"Segment: {segment_ref or 'All'}"
    )
    
    # Process NoShow penalties (both as type and application)
    is_noshow = ('noshow' in penalty_type_lower or 'no show' in penalty_type_lower or 
                'noshow' in application_lower or 'no show' in application_lower)
    
    if is_noshow:
        try:
            logger.debug(f"Processing NoShow penalty: {penalty}")
            
            # Initialize noShow section if it doesn't exist
            if 'noShow' not in rules:
                rules['noShow'] = {
                    'allowed': False, 
                    'refundable': False, 
                    'fee': 0.0,
                    'currency': currency or 'USD',
                    'conditions': []
                }
            
            target = rules['noShow']
            target['allowed'] = True
            target['refundable'] = target.get('refundable', False) or refundable
            
            # Update fee if higher than current
            if amount > target.get('fee', 0):
                target['fee'] = amount
                target['currency'] = currency or target.get('currency', 'USD')
            
            # Add remarks as conditions if they don't exist
            for remark in remarks:
                if remark and remark not in target['conditions']:
                    target['conditions'].append(remark)
            
            # Also update the legacy penalties list
            penalty_desc = f"NoShow: {amount} {currency}"
            if refundable:
                penalty_desc += " (Refundable)"
            
            # Ensure penalties list exists
            if 'penalties' not in rules:
                rules['penalties'] = []
                
            if penalty_desc not in rules['penalties']:
                rules['penalties'].append(penalty_desc)
            
            # Ensure additionalRestrictions exists
            if 'additionalRestrictions' not in rules:
                rules['additionalRestrictions'] = []
                
            # Add to additional restrictions if not already present
            for remark in remarks:
                if remark and remark not in rules['additionalRestrictions']:
                    rules['additionalRestrictions'].append(remark)
            
            logger.debug(f"Updated noShow rules: {target}")
            return
            
        except Exception as e:
            logger.error(f"Error processing NoShow penalty: {e}", exc_info=True)
            return
    
    try:
        # Process Change penalties
        if 'change' in penalty_type_lower:
            try:
                rules['exchangeable'] = True
                rules['changeable'] = True
                
                if amount > 0:
                    rules['changeFee'] = True
                
                # Determine the target rule based on application time
                target_key = None
                if 'before departure' in application_lower:
                    target_key = 'changeBeforeDeparture'
                elif 'after departure' in application_lower:
                    target_key = 'changeAfterDeparture'
                elif 'no show' in application_lower:
                    target_key = 'changeNoShow'
                
                if target_key:
                    # Ensure target key exists in rules
                    if target_key not in rules:
                        rules[target_key] = {
                            'allowed': False,
                            'fee': 0.0,
                            'currency': currency or 'USD',
                            'conditions': []
                        }
                    
                    target = rules[target_key]
                    target['allowed'] = True
                    
                    # Only update fee if it's higher than current
                    if amount > target.get('fee', 0):
                        target['fee'] = amount
                        target['currency'] = currency or target.get('currency', 'USD')
                    
                    # Add remarks as conditions
                    for remark in remarks:
                        if remark and remark not in target['conditions']:
                            target['conditions'].append(remark)
                    
                    logger.debug(f"Updated {target_key} rules: {target}")
            except Exception as e:
                logger.error(f"Error processing change penalty: {e}", exc_info=True)
        
        # Process Cancel penalties
        elif 'cancel' in penalty_type_lower:
            try:
                if refundable:
                    rules['refundable'] = True
                
                # Calculate refund percentage (100% if no fee, 0% otherwise)
                refund_percentage = 100 if amount == 0 else 0
                
                # Determine the target rule based on application time
                target_key = None
                if 'before departure' in application_lower:
                    target_key = 'cancelBeforeDeparture'
                elif 'after departure' in application_lower:
                    target_key = 'cancelAfterDeparture'
                elif 'no show' in application_lower:
                    target_key = 'cancelNoShow'
                
                if target_key:
                    # Ensure target key exists in rules
                    if target_key not in rules:
                        rules[target_key] = {
                            'allowed': False,
                            'fee': 0.0,
                            'currency': currency or 'USD',
                            'refundPercentage': 0,
                            'conditions': []
                        }
                    
                    target = rules[target_key]
                    target['allowed'] = True
                    
                    # Only update fee if it's higher than current
                    if amount > target.get('fee', 0):
                        target['fee'] = amount
                        target['currency'] = currency or target.get('currency', 'USD')
                    
                    # Update refund percentage if more favorable
                    if refund_percentage > target.get('refundPercentage', 0):
                        target['refundPercentage'] = refund_percentage
                    
                    # Add remarks as conditions
                    for remark in remarks:
                        if remark and remark not in target['conditions']:
                            target['conditions'].append(remark)
                    
                    logger.debug(f"Updated {target_key} rules: {target}")
            except Exception as e:
                logger.error(f"Error processing cancel penalty: {e}", exc_info=True)
        
        # Add to legacy penalties list for backward compatibility
        try:
            penalty_desc = f"{penalty_type.capitalize()} - {application}: {amount} {currency}"
            if refundable and ('cancel' in penalty_type_lower or 'refund' in penalty_type_lower):
                penalty_desc += " (Refundable)"
            
            # Ensure penalties list exists
            if 'penalties' not in rules:
                rules['penalties'] = []
            
            if penalty_desc not in rules['penalties']:
                rules['penalties'].append(penalty_desc)
            
            # Ensure additionalRestrictions exists
            if 'additionalRestrictions' not in rules:
                rules['additionalRestrictions'] = []
            
            # Add remarks to additional restrictions if not already added
            for remark in remarks:
                if remark and remark not in rules['additionalRestrictions']:
                    rules['additionalRestrictions'].append(remark)
            
            logger.debug(f"Final penalty processing complete for {penalty_type}")
            
        except Exception as e:
            logger.error(f"Error updating legacy penalty information: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in penalty processing: {e}", exc_info=True)

def _transform_penalties_to_fare_rules(penalties: Union[List[Dict[str, Any]], Any]) -> Dict[str, Any]:
    """
    Transform penalty list into structured FareRules format expected by frontend.
    
    Handles different penalty types and application times according to documentation:
    - Change fees (before/after departure, no-show)
    - Cancel fees (before/after departure, no-show)
    - Refund information
    - No-show penalties
    
    Supports per-segment penalties and includes comprehensive penalty details.
    
    Args:
        penalties: List of penalty dictionaries from _extract_penalty_info, or any other type
        
    Returns:
        Dict containing structured fare rules for frontend with per-segment penalties
    """
    logger = logging.getLogger(__name__)
    
    # Handle case where penalties is not a list
    if not isinstance(penalties, list):
        logger.warning(f"Expected list of penalties but got {type(penalties)}. Converting to empty list.")
        penalties = []
    
    # Filter out any non-dict items from penalties
    valid_penalties = []
    for i, penalty in enumerate(penalties):
        if isinstance(penalty, dict):
            valid_penalties.append(penalty)
        else:
            logger.warning(f"Skipping non-dict penalty at index {i}: {penalty}")
    
    logger.info(f"Transforming {len(valid_penalties)} valid penalties to fare rules")
    
    # Initialize fare rules structure
    fare_rules = {
        'changeable': False,
        'refundable': False,
        'exchangeable': False,
        'cancelFee': False,
        'changeFee': False,
        'changeBeforeDeparture': None,
        'changeAfterDeparture': None,
        'cancelBeforeDeparture': None,
        'cancelAfterDeparture': None,
        'noShow': None,
        'penalties': [],
        'changeConditions': [],
        'cancelConditions': [],
        'noShowConditions': [],
        'additionalRestrictions': [],
        'segmentRules': {}
    }
    
    # If no penalties, return default rules
    if not penalties:
        logger.debug("No penalties to process, returning default rules")
        return fare_rules
    
    # Organize penalties by segment first
    try:
        segment_penalties = {}
        for penalty in penalties:
            if not isinstance(penalty, dict):
                logger.warning(f"Skipping invalid penalty (not a dict): {penalty}")
                continue
                
            # Get segment references from penalty, default to ['all'] if not specified
            segment_refs = penalty.get('segment_refs', ['all'])
            if not isinstance(segment_refs, list):
                segment_refs = [segment_refs]
                
            for segment_ref in segment_refs:
                if segment_ref not in segment_penalties:
                    segment_penalties[segment_ref] = []
                segment_penalties[segment_ref].append(penalty)
        
        logger.debug(f"Organized penalties into {len(segment_penalties)} segment groups")
        
    except Exception as e:
        logger.error(f"Error organizing penalties by segment: {e}")
        return fare_rules  # Return default rules if we can't organize penalties
    
    cancel_fees = []
    change_fees = []
    
    # Process penalties for each segment
    for segment_ref, seg_penalties in segment_penalties.items():
        logger.info(f"Processing penalties for segment {segment_ref}")
        # Create a new segment rules structure
        segment_rules = _create_segment_fare_rules()
        
        # Log the penalties being processed
        logger.info(f"Processing {len(seg_penalties)} penalties for segment {segment_ref}")
        
        # Ensure all penalties are dictionaries before processing
        processed_penalties = []
        for penalty in seg_penalties:
            if isinstance(penalty, str):
                logger.warning(f"Found string penalty, converting to dict: {penalty}")
                processed_penalties.append({
                    'type': penalty,
                    'application': 'UNKNOWN',
                    'amount': 0,
                    'currency': 'USD',
                    'remarks': [f"Converted from string: {penalty}"],
                    'refundable': False,
                    'segment_refs': [segment_ref]
                })
            elif isinstance(penalty, dict):
                processed_penalties.append(penalty)
            else:
                logger.warning(f"Skipping invalid penalty type: {type(penalty)}")
        
        # Process each penalty
        for i, penalty in enumerate(processed_penalties, 1):
            try:
                logger.info(f"Processing penalty {i}/{len(processed_penalties)}: {json.dumps(penalty, indent=2, default=str)}")
                _apply_penalty_to_rules(penalty, segment_rules)
            except Exception as e:
                logger.error(f"Error applying penalty: {e}", exc_info=True)
                # Continue with other penalties instead of failing the whole process
                continue
            
        # Track fees for overall fare rules
        for penalty in seg_penalties:
            try:
                if not isinstance(penalty, dict):
                    logger.warning(f"Skipping non-dict penalty in fee tracking: {penalty}")
                    continue
                
                penalty_type = str(penalty.get('type', '')).lower()
                if not penalty_type:
                    logger.warning(f"Penalty missing type: {penalty}")
                    continue
                    
                if 'change' in penalty_type:
                    fee = float(penalty.get('amount', 0) or 0)
                    if fee > 0:
                        change_fees.append(fee)
                        fare_rules['changeCurrency'] = str(penalty.get('currency', ''))
                elif 'cancel' in penalty_type:
                    fee = float(penalty.get('amount', 0) or 0)
                    if fee > 0:
                        cancel_fees.append(fee)
                        fare_rules['cancelCurrency'] = str(penalty.get('currency', ''))
            except Exception as e:
                logger.error(f"Error processing penalty for fee tracking: {e}", exc_info=True)
                continue
        
        # Add segment rules to the main rules
        fare_rules['segmentRules'][segment_ref] = segment_rules
        
        # Update overall rules based on segment rules
        fare_rules['changeable'] = fare_rules['changeable'] or segment_rules.get('changeable', False)
        fare_rules['changeFee'] = fare_rules['changeFee'] or segment_rules.get('changeFee', False)
        fare_rules['refundable'] = fare_rules['refundable'] or segment_rules.get('refundable', False)
        fare_rules['exchangeable'] = fare_rules['exchangeable'] or segment_rules.get('exchangeable', False)
        
        # Log the updated rules for this segment
        logger.debug(f"Updated fare rules after segment {segment_ref}: {segment_rules}")
        
        # Merge penalties and additional restrictions
        for penalty in segment_rules.get('penalties', []):
            try:
                # Skip if penalty is not a dictionary
                if not isinstance(penalty, dict):
                    logger.warning(f"Skipping non-dict penalty in segment rules: {penalty}")
                    continue
                    
                # Skip if we've already processed this penalty
                if penalty in fare_rules['penalties']:
                    continue
                    
                # Add the penalty to our list
                fare_rules['penalties'].append(penalty)
                
                # Safely extract penalty type and conditions
                penalty_type = str(penalty.get('type', '')).lower()
                conditions = penalty.get('conditions', [])
                if not isinstance(conditions, list):
                    conditions = []
                
                # Categorize penalty conditions based on type
                if 'change' in penalty_type:
                    fare_rules['changeConditions'].extend(
                        str(c) for c in conditions 
                        if str(c) not in fare_rules['changeConditions'] and c is not None
                    )
                elif 'cancel' in penalty_type:
                    fare_rules['cancelConditions'].extend(
                        str(c) for c in conditions 
                        if str(c) not in fare_rules['cancelConditions'] and c is not None
                    )
                elif 'no show' in penalty_type or 'noshow' in penalty_type:
                    fare_rules['noShowConditions'].extend(
                        str(c) for c in conditions 
                        if str(c) not in fare_rules['noShowConditions'] and c is not None
                    )
            except Exception as e:
                logger.error(f"Error processing penalty in segment rules: {e}", exc_info=True)
                continue
        
        for restriction in segment_rules.get('additionalRestrictions', []):
            if restriction not in fare_rules['additionalRestrictions']:
                fare_rules['additionalRestrictions'].append(restriction)
    
    # Set min/max fees for overall fare rules
    if change_fees:
        fare_rules['changeFeeBeforeDeparture'] = min(change_fees)
        fare_rules['changeFeeAfterDeparture'] = max(change_fees)
        fare_rules['changeFeeNoShow'] = max(change_fees)  # Default to max for no-show
        
    if cancel_fees:
        fare_rules['cancelFeeBeforeDeparture'] = min(cancel_fees)
        fare_rules['cancelFeeAfterDeparture'] = max(cancel_fees)
        fare_rules['cancelFeeNoShow'] = max(cancel_fees)  # Default to max for no-show
    
    # Initialize refund conditions set with any existing refund conditions
    refund_conditions = set(fare_rules.get('refundConditions', []))
    
    # Include cancel conditions if the fare is refundable
    if fare_rules.get('refundable', False):
        refund_conditions.update(fare_rules.get('cancelConditions', []))
    
    # Add refund conditions from penalties
    for penalty in penalties:
        if not isinstance(penalty, dict):
            continue
            
        # If penalty is refundable, add its remarks as refund conditions
        if penalty.get('refundable', False):
            # Handle different types of remarks
            remarks = penalty.get('remarks', [])
            if isinstance(remarks, list):
                refund_conditions.update(str(r) for r in remarks if r)
            elif remarks:  # Handle case where remarks is a single string
                refund_conditions.add(str(remarks))
            
            # Also add any conditions from the penalty
            conditions = penalty.get('conditions', [])
            if isinstance(conditions, list):
                refund_conditions.update(str(c) for c in conditions if c)
            elif conditions:
                refund_conditions.add(str(conditions))
    
    # Add any additional restrictions that might be relevant
    additional_restrictions = fare_rules.get('additionalRestrictions', [])
    if isinstance(additional_restrictions, list):
        refund_conditions.update(str(r) for r in additional_restrictions if r and 'refund' in str(r).lower())
    
    # Set default message if no conditions found but fare is refundable
    if not refund_conditions and fare_rules.get('refundable', False):
        refund_conditions.add("Refundable")
    elif not refund_conditions:
        refund_conditions.add("Non-refundable")
    
    # Update fare rules with refund conditions
    fare_rules['refundConditions'] = [c for c in refund_conditions if c]  # Remove any empty strings
    
    # Final cleanup and validation
    _cleanup_fare_rules(fare_rules)
    
    # Log the transformed fare rules for debugging
    logger.debug(f"Transformed fare rules: {json.dumps(fare_rules, indent=2, default=str)}")
    
    return fare_rules

def _cleanup_fare_rules(fare_rules: Dict[str, Any]) -> None:
    """
    Clean up and validate the fare rules structure.
    
    Args:
        fare_rules: The fare rules dictionary to clean up
    """
    if not isinstance(fare_rules, dict):
        logger.warning(f"Invalid fare_rules type: {type(fare_rules).__name__}. Expected dict.")
        return
    
    # Remove empty conditions lists
    for key in ['changeBeforeDeparture', 'changeAfterDeparture', 'changeNoShow',
               'cancelBeforeDeparture', 'cancelAfterDeparture', 'cancelNoShow', 'noShow']:
        try:
            rule = fare_rules.get(key)
            if isinstance(rule, dict) and 'conditions' in rule and not rule['conditions']:
                del rule['conditions']
        except Exception as e:
            logger.warning(f"Error cleaning up {key} conditions: {e}")
            continue
    
    # Ensure consistent refundable flag
    try:
        if fare_rules.get('refundable', False):
            # If any cancellation is allowed, ensure refundable is True
            cancel_before = fare_rules.get('cancelBeforeDeparture', {}) and fare_rules['cancelBeforeDeparture'].get('allowed', False)
            cancel_after = fare_rules.get('cancelAfterDeparture', {}) and fare_rules['cancelAfterDeparture'].get('allowed', False)
            cancel_noshow = fare_rules.get('cancelNoShow', {}) and fare_rules['cancelNoShow'].get('allowed', False)
            
            if any([cancel_before, cancel_after, cancel_noshow]):
                fare_rules['refundable'] = True
    except Exception as e:
        logger.warning(f"Error updating refundable flag: {e}")
    
    # Clean up empty additional restrictions if it exists
    try:
        if 'additionalRestrictions' in fare_rules and not fare_rules['additionalRestrictions']:
            del fare_rules['additionalRestrictions']
    except Exception as e:
        logger.warning(f"Error cleaning up additional restrictions: {e}")
    
    # Ensure exchangeable and changeable are in sync with proper null checks
    try:
        change_before = (isinstance(fare_rules.get('changeBeforeDeparture'), dict) and 
                         fare_rules['changeBeforeDeparture'].get('allowed', False)) or False
        change_after = (isinstance(fare_rules.get('changeAfterDeparture'), dict) and 
                        fare_rules['changeAfterDeparture'].get('allowed', False)) or False
        change_noshow = (isinstance(fare_rules.get('changeNoShow'), dict) and 
                         fare_rules['changeNoShow'].get('allowed', False)) or False
        
        is_changeable = any([change_before, change_after, change_noshow])
        fare_rules['exchangeable'] = fare_rules.get('exchangeable', False) or is_changeable
        fare_rules['changeable'] = fare_rules.get('changeable', False) or is_changeable
    except Exception as e:
        logger.warning(f"Error syncing exchangeable/changeable flags: {e}")
        fare_rules['exchangeable'] = fare_rules.get('exchangeable', False)
        fare_rules['changeable'] = fare_rules.get('changeable', False)

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