"""Data transformation utilities for converting Verteil API responses to frontend-compatible formats."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def transform_verteil_to_frontend(verteil_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform Verteil API air shopping response to frontend-compatible FlightOffer objects.
    
    Args:
        verteil_response: Raw response from Verteil API
        
    Returns:
        List of FlightOffer objects compatible with frontend interface
    """
    try:
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
            airline_code = airline_offer_group.get('Owner', {}).get('value', 'Unknown')
            airline_offers_list = airline_offer_group.get('AirlineOffer', [])
            logger.info(f"Processing airline offer group {i}: airline_code={airline_code}, offers_count={len(airline_offers_list) if isinstance(airline_offers_list, list) else 'Not a list'}")
            
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
        return flight_offers
        
    except Exception as e:
        logger.error(f"Error transforming Verteil response: {str(e)}")
        return []

def _extract_reference_data(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract reference data (flights, segments, airports, etc.) from Verteil response.
    """
    reference_data = {
        'flights': {},
        'segments': {},
        'airports': {},
        'aircraft': {},
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
                if flight_key:
                    reference_data['flights'][flight_key] = flight
        
        # Extract flight segment references - FlightSegmentList is inside DataLists
        segment_list = data_lists.get('FlightSegmentList', {})
        logger.info(f"FlightSegmentList found: {bool(segment_list)}")
        segments = segment_list.get('FlightSegment', [])
        logger.info(f"Found {len(segments)} flight segments in response")
        if isinstance(segments, list):
            for segment in segments:
                segment_key = segment.get('SegmentKey')
                if segment_key:
                    reference_data['segments'][segment_key] = segment
                    logger.info(f"Added segment {segment_key} to reference data")
                else:
                    logger.warning(f"Segment missing SegmentKey: {segment}")
        else:
            logger.warning(f"FlightSegment is not a list: {type(segments)}")
        
        logger.info(f"Total segments in reference_data: {len(reference_data['segments'])}")
        
        # Extract origin-destination references - OriginDestinationList is at root level in actual API response
        od_list = response.get('OriginDestinationList', {})
        origin_destinations = od_list.get('OriginDestination', [])
        logger.debug(f"Found {len(origin_destinations)} origin-destinations in response")
        if isinstance(origin_destinations, list):
            for od in origin_destinations:
                od_key = od.get('OriginDestinationKey')
                if od_key:
                    reference_data['airports'][od_key] = od
                    logger.debug(f"Added origin-destination {od_key} to reference data")
                
                # Also extract airport information from departure/arrival
                departure = od.get('Departure', {})
                arrival = od.get('Arrival', {})
                
                dep_airport = departure.get('AirportCode')
                arr_airport = arrival.get('AirportCode')
                
                if dep_airport:
                    reference_data['airports'][dep_airport] = {
                        'code': dep_airport,
                        'name': departure.get('AirportName', dep_airport),
                        'terminal': departure.get('Terminal')
                    }
                
                if arr_airport:
                    reference_data['airports'][arr_airport] = {
                        'code': arr_airport,
                        'name': arrival.get('AirportName', arr_airport),
                        'terminal': arrival.get('Terminal')
                    }
        
        # Extract carry-on allowance list
        carry_on_list = data_lists.get('CarryOnAllowanceList', {}).get('CarryOnAllowance', [])
        for carry_on in carry_on_list:
            list_key = carry_on.get('ListKey')
            if list_key:
                reference_data['carry_on_allowances'][list_key] = carry_on
        
        # Extract checked bag allowance list
        checked_bag_list = data_lists.get('CheckedBagAllowanceList', {}).get('CheckedBagAllowance', [])
        for checked_bag in checked_bag_list:
            list_key = checked_bag.get('ListKey')
            if list_key:
                reference_data['checked_bag_allowances'][list_key] = checked_bag
        
        # Extract penalty list
        penalty_list = data_lists.get('PenaltyList', {}).get('Penalty', [])
        for penalty in penalty_list:
            object_key = penalty.get('ObjectKey')
            if object_key:
                reference_data['penalties'][object_key] = penalty
        
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
        currency = 'USD'
        
        # Primary path: OfferPrice[0].RequestedDate.PriceDetail.TotalAmount.SimpleCurrencyPrice (as seen in actual JSON)
        price_detail = offer_price.get('RequestedDate', {}).get('PriceDetail', {})
        if price_detail:
            total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
            price = total_amount.get('value', 0)
            currency = total_amount.get('Code', 'USD')
            logger.info(f"Using OfferPrice PriceDetail: {price} {currency}")
        
        # Fallback to AirlineOffer level if OfferPrice price not found
        if price == 0 and airline_offer and 'TotalPrice' in airline_offer:
            total_price_obj = airline_offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
            price = total_price_obj.get('value', 0)
            currency = total_price_obj.get('Code', 'USD')
            logger.info(f"Using AirlineOffer TotalPrice: {price} {currency}")
        
        # Final fallback to PricedOffer level
        if price == 0:
            priced_offer_total = priced_offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
            price = priced_offer_total.get('value', 0)
            currency = priced_offer_total.get('Code', 'USD')
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
        
        # Calculate total duration (simplified)
        duration = _calculate_duration(first_segment, last_segment)
        
        # Generate unique offer ID
        offer_id = f"{airline_code}-{'-'.join(all_segment_refs)}-{price}"
        
        # Build price breakdown - pass airline_offer for correct price extraction
        price_breakdown = _build_price_breakdown(price_detail, priced_offer, airline_offer)
        
        # Build baggage information (simplified)
        baggage = {
            'carryOn': {
                'included': True,
                'weight': {'value': 7, 'unit': 'kg'},
                'dimensions': {'length': 56, 'width': 45, 'height': 25, 'unit': 'cm'}
            },
            'checked': {
                'included': True,
                'weight': {'value': 23, 'unit': 'kg'},
                'pieces': 1
            }
        }
        
        # Build airline details
        airline_details = {
            'code': airline_code,
            'name': _get_airline_name(airline_code),
            'logo': f'/airlines/{airline_code.lower()}.png',
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
    
    # Extract airline name using correct path: OperatingCarrier.Name
    airline_name = segment_data.get('OperatingCarrier', {}).get('Name', 'Unknown Airline')
    
    # Extract flight duration using correct path: FlightDetail.FlightDuration.Value
    flight_duration = segment_data.get('FlightDetail', {}).get('FlightDuration', {}).get('Value', 'N/A')
    
    return {
        'departure': {
            'airport': dep_airport,
            'datetime': dep_datetime,
            'terminal': dep_airport_info.get('terminal'),
            'airportName': dep_airport_info.get('name')
        },
        'arrival': {
            'airport': arr_airport,
            'datetime': arr_datetime,
            'terminal': arr_airport_info.get('terminal'),
            'airportName': arr_airport_info.get('name')
        },
        'flightNumber': segment_data.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', '001'),
        'aircraft': {
            'code': segment_data.get('Equipment', {}).get('AircraftCode', 'Unknown'),
            'name': 'Aircraft'
        },
        'airlineName': airline_name,
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
                    details = penalty_data.get('Details', {}).get('Detail', [])
                    for detail in details:
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
                        amounts = detail.get('Amounts', {}).get('Amount', [])
                        penalty_amount = 0
                        currency = 'USD'
                        remarks = []
                        
                        for amount in amounts:
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


def _get_airline_name(airline_code: str) -> str:
    """
    Get airline name from code. This could be expanded with a proper lookup table.
    """
    airline_names = {
        'KQ': 'Kenya Airways',
        'AA': 'American Airlines',
        'BA': 'British Airways',
        'LH': 'Lufthansa',
        'AF': 'Air France',
        'KL': 'KLM',
        'EK': 'Emirates',
        'QR': 'Qatar Airways'
    }
    return airline_names.get(airline_code, f"Airline {airline_code}")


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
        currency = penalty.get('currency', 'USD')
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