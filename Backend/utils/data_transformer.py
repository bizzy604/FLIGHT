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
        
        # Navigate to the offers in the response
        offers_group = verteil_response.get('OffersGroup', {})
        airline_offers = offers_group.get('AirlineOffers', [])
        
        # Extract reference data for lookups
        reference_data = _extract_reference_data(verteil_response)
        
        for airline_offer_group in airline_offers:
            airline_code = airline_offer_group.get('Owner', {}).get('value', 'Unknown')
            airline_offers_list = airline_offer_group.get('AirlineOffer', [])
            
            for offer in airline_offers_list:
                priced_offers = offer.get('PricedOffer', [])
                if not isinstance(priced_offers, list):
                    priced_offers = [priced_offers]
                    
                for priced_offer in priced_offers:
                    flight_offer = _transform_single_offer(
                        priced_offer, 
                        airline_code, 
                        reference_data
                    )
                    if flight_offer:
                        flight_offers.append(flight_offer)
        
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
        'aircraft': {}
    }
    
    try:
        # Extract flight references
        flight_list = response.get('FlightList', {})
        flights = flight_list.get('Flight', [])
        if not isinstance(flights, list):
            flights = [flights]
            
        for flight in flights:
            flight_key = flight.get('FlightKey')
            if flight_key:
                reference_data['flights'][flight_key] = flight
        
        # Extract segment references
        flight_segment_list = response.get('FlightSegmentList', {})
        segments = flight_segment_list.get('FlightSegment', [])
        if not isinstance(segments, list):
            segments = [segments]
            
        for segment in segments:
            segment_key = segment.get('SegmentKey')
            if segment_key:
                reference_data['segments'][segment_key] = segment
        
        # Extract airport references
        origin_dest_list = response.get('OriginDestinationList', {})
        origin_dests = origin_dest_list.get('OriginDestination', [])
        if not isinstance(origin_dests, list):
            origin_dests = [origin_dests]
            
        for od in origin_dests:
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
        
    except Exception as e:
        logger.warning(f"Error extracting reference data: {str(e)}")
    
    return reference_data

def _transform_single_offer(
    priced_offer: Dict[str, Any], 
    airline_code: str, 
    reference_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Transform a single priced offer to FlightOffer format.
    """
    try:
        offer_prices = priced_offer.get('OfferPrice', [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices]
        
        if not offer_prices:
            return None
            
        # Use the first offer price for now
        offer_price = offer_prices[0]
        
        # Extract price information
        price_detail = offer_price.get('PriceDetail', {})
        total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        price = total_amount.get('value', 0)
        currency = total_amount.get('Code', 'USD')
        
        # Extract flight associations
        associations = offer_price.get('Associations', [])
        if not isinstance(associations, list):
            associations = [associations]
        
        # Get flight segments and build flight details
        segments = []
        all_segment_refs = []
        
        for assoc in associations:
            applicable_flight = assoc.get('ApplicableFlight', {})
            segment_refs = applicable_flight.get('FlightSegmentReference', [])
            if not isinstance(segment_refs, list):
                segment_refs = [segment_refs]
            
            for seg_ref in segment_refs:
                ref_key = seg_ref.get('ref')
                if ref_key:
                    all_segment_refs.append(ref_key)
                    segment_data = reference_data['segments'].get(ref_key, {})
                    if segment_data:
                        segments.append(_transform_segment(segment_data, reference_data))
        
        if not segments:
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
        
        # Build price breakdown
        price_breakdown = _build_price_breakdown(price_detail)
        
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
            'baggage': baggage,
            'segments': segments,
            'priceBreakdown': price_breakdown
        }
        
        return flight_offer
        
    except Exception as e:
        logger.error(f"Error transforming single offer: {str(e)}")
        return None

def _transform_segment(segment_data: Dict[str, Any], reference_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a flight segment to the expected format.
    """
    departure = segment_data.get('Departure', {})
    arrival = segment_data.get('Arrival', {})
    
    dep_airport = departure.get('AirportCode', '')
    arr_airport = arrival.get('AirportCode', '')
    
    # Get airport details from reference data
    dep_airport_info = reference_data['airports'].get(dep_airport, {'code': dep_airport, 'name': dep_airport})
    arr_airport_info = reference_data['airports'].get(arr_airport, {'code': arr_airport, 'name': arr_airport})
    
    return {
        'departure': {
            'airport': dep_airport,
            'datetime': departure.get('Date', '') + 'T' + departure.get('Time', '00:00'),
            'terminal': dep_airport_info.get('terminal'),
            'airportName': dep_airport_info.get('name')
        },
        'arrival': {
            'airport': arr_airport,
            'datetime': arrival.get('Date', '') + 'T' + arrival.get('Time', '00:00'),
            'terminal': arr_airport_info.get('terminal'),
            'airportName': arr_airport_info.get('name')
        },
        'flightNumber': segment_data.get('MarketingCarrier', {}).get('FlightNumber', '001'),
        'aircraft': {
            'code': segment_data.get('Equipment', {}).get('AircraftCode', 'Unknown'),
            'name': 'Aircraft'
        }
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

def _build_price_breakdown(price_detail: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build price breakdown from Verteil price detail.
    """
    total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
    base_amount = price_detail.get('BaseAmount', {})
    taxes = price_detail.get('Taxes', {}).get('Total', {})
    
    total_price = total_amount.get('value', 0)
    base_fare = base_amount.get('value', 0)
    tax_amount = taxes.get('value', 0)
    currency = total_amount.get('Code', 'USD')
    
    return {
        'baseFare': base_fare,
        'taxes': tax_amount,
        'fees': 0,
        'totalPrice': total_price,
        'currency': currency
    }

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