# Backend/utils/air_shopping_transformer.py
# This transformer is ONLY for the Air-Shopping response (the flight results page).

from datetime import datetime
import logging
from .airline_data import get_airline_name, get_airline_logo_url

logger = logging.getLogger(__name__)

def _transform_departure_arrival(raw_data):
    """Transform raw departure/arrival data to frontend format."""
    if not raw_data:
        return None

    airport_code = raw_data.get('AirportCode', {})
    if isinstance(airport_code, dict):
        airport = airport_code.get('value', '')
    else:
        airport = airport_code

    datetime_str = raw_data.get('Date', '')
    time_str = raw_data.get('Time', '')

    terminal_data = raw_data.get('Terminal', {})
    terminal = None
    if isinstance(terminal_data, dict):
        terminal = terminal_data.get('Name')

    return {
        'airport': airport,
        'datetime': datetime_str,
        'time': time_str,
        'terminal': terminal,
        'airportName': None  # Will be populated by frontend if needed
    }

def _extract_simple_refs(response):
    """A very basic reference extractor for the results page."""
    data_lists = response.get('DataLists', {})
    segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
    return {
        'segments': {s.get('SegmentKey'): s for s in segments if s.get('SegmentKey')}
    }

def _transform_offer_for_results_page(priced_offer, refs, offer=None):
    """Transforms a single offer into the summary format for a flight card."""
    try:
        first_offer_price = priced_offer.get('OfferPrice', [{}])[0]
        price_detail = first_offer_price.get('RequestedDate', {}).get('PriceDetail', {})
        total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        
        all_segments_data = []
        for assoc in first_offer_price.get('RequestedDate', {}).get('Associations', []):
            for seg_ref in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
                segment_data = refs['segments'].get(seg_ref.get('ref'))
                if segment_data:
                    all_segments_data.append(segment_data)
        
        if not all_segments_data:
            return None

        # Sort segments by departure time to ensure correct order
        all_segments_data.sort(key=lambda s: s.get('Departure', {}).get('Date', ''))
        
        first_seg_data = all_segments_data[0]
        last_seg_data = all_segments_data[-1]
        
        airline_code = first_seg_data.get('MarketingCarrier', {}).get('AirlineID', {}).get('value', '??')
        
        # Simple duration and stops calculation for the summary card
        dep_time = datetime.fromisoformat(first_seg_data.get('Departure', {}).get('Date', ''))
        arr_time = datetime.fromisoformat(last_seg_data.get('Arrival', {}).get('Date', ''))
        duration_delta = arr_time - dep_time
        total_hours, remainder = divmod(duration_delta.total_seconds(), 3600)
        total_minutes, _ = divmod(remainder, 60)

        # Transform departure and arrival to frontend format
        departure_data = _transform_departure_arrival(first_seg_data.get('Departure'))
        arrival_data = _transform_departure_arrival(last_seg_data.get('Arrival'))

        # Transform segments to frontend format
        transformed_segments = []
        for segment in all_segments_data:
            seg_departure = _transform_departure_arrival(segment.get('Departure'))
            seg_arrival = _transform_departure_arrival(segment.get('Arrival'))

            # Get airline info for this segment
            marketing_carrier = segment.get('MarketingCarrier', {})
            seg_airline_code = marketing_carrier.get('AirlineID', {}).get('value', '??')
            flight_number_obj = marketing_carrier.get('FlightNumber', {})
            flight_number = flight_number_obj.get('value', '') if isinstance(flight_number_obj, dict) else flight_number_obj

            # Get duration for this segment
            flight_detail = segment.get('FlightDetail', {})
            duration_obj = flight_detail.get('FlightDuration', {})
            duration_value = duration_obj.get('Value', 'PT0M') if isinstance(duration_obj, dict) else duration_obj

            # Parse ISO duration (PT8H40M -> 8h 40m)
            duration_str = duration_value
            if duration_value.startswith('PT'):
                import re
                hours_match = re.search(r'(\d+)H', duration_value)
                minutes_match = re.search(r'(\d+)M', duration_value)
                hours = int(hours_match.group(1)) if hours_match else 0
                minutes = int(minutes_match.group(1)) if minutes_match else 0
                duration_str = f"{hours}h {minutes}m"

            # Get aircraft info
            equipment = segment.get('Equipment', {})
            aircraft_code = equipment.get('AircraftCode', {}).get('value', '') if isinstance(equipment.get('AircraftCode', {}), dict) else equipment.get('AircraftCode', '')

            transformed_segment = {
                'departure': seg_departure,
                'arrival': seg_arrival,
                'airline': {
                    'code': seg_airline_code,
                    'name': get_airline_name(seg_airline_code),
                    'logo': get_airline_logo_url(seg_airline_code),
                    'flightNumber': f"{seg_airline_code}{flight_number}"
                },
                'aircraft': {
                    'code': aircraft_code,
                    'name': aircraft_code  # Could be enhanced with aircraft name lookup
                },
                'duration': duration_str
            }
            transformed_segments.append(transformed_segment)

        # Calculate stop details
        stops_count = len(all_segments_data) - 1
        stop_details = []
        if stops_count > 0:
            for i in range(1, len(all_segments_data)):
                stop_airport = all_segments_data[i].get('Departure', {}).get('AirportCode', {})
                if isinstance(stop_airport, dict):
                    stop_code = stop_airport.get('value', '')
                else:
                    stop_code = stop_airport
                if stop_code:
                    stop_details.append(stop_code)

        # Extract offer ID from the offer parameter (AirlineOffer level), not priced_offer
        offer_id = None
        if offer:
            offer_id = offer.get('OfferID', {}).get('value')
            if not offer_id:
                offer_id = offer.get('OfferID', {}).get('ObjectKey')
            if not offer_id and isinstance(offer.get('OfferID'), str):
                offer_id = offer.get('OfferID')

        # Fallback to priced_offer if offer parameter not provided (backward compatibility)
        if not offer_id:
            offer_id = priced_offer.get('OfferID', {}).get('value')
            if not offer_id:
                offer_id = priced_offer.get('OfferID', {}).get('ObjectKey')
            if not offer_id and isinstance(priced_offer.get('OfferID'), str):
                offer_id = priced_offer.get('OfferID')

        return {
            "id": offer_id,
            "price": total_amount.get('value', 0),
            "currency": total_amount.get('Code', 'USD'),
            "airline": {
                "code": airline_code,
                "name": get_airline_name(airline_code),
                "logo": get_airline_logo_url(airline_code),
                "flightNumber": f"{airline_code}{first_seg_data.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', '')}"
            },
            "departure": departure_data,
            "arrival": arrival_data,
            "duration": f"{int(total_hours)}h {int(total_minutes)}m",
            "stops": stops_count,
            "stopDetails": stop_details,
            "segments": transformed_segments,
            # Add basic baggage info (can be enhanced later)
            "baggage": {
                "checked": {"pieces": 1, "weight": "23kg"},
                "carryon": {"pieces": 1, "weight": "7kg"}
            },
            # Add basic fare info
            "fare": {
                "type": "Economy",  # Can be enhanced based on cabin class
                "refundable": False,  # Default value
                "changeable": False   # Default value
            },
            # Add price breakdown for frontend display
            "priceBreakdown": {
                "baseFare": total_amount.get('value', 0) * 0.8,  # Estimate 80% as base fare
                "taxes": total_amount.get('value', 0) * 0.15,    # Estimate 15% as taxes
                "fees": total_amount.get('value', 0) * 0.05,     # Estimate 5% as fees
                "totalPrice": total_amount.get('value', 0),
                "currency": total_amount.get('Code', 'USD')
            }
        }
    except Exception as e:
        logger.error(f"Error transforming offer for results page: {e}", exc_info=True)
        return None

def _extract_shopping_response_id(response: dict) -> dict:
    """
    Extract ShoppingResponseID from the Metadata section and add it to the response.
    """
    try:
        # Check if ShoppingResponseID already exists at top level
        if response.get("ShoppingResponseID"):
            return response

        # Extract from Metadata section
        metadata_section = response.get("Metadata", {})
        other_metadata_list = metadata_section.get("Other", {}).get("OtherMetadata", [])

        if isinstance(other_metadata_list, list):
            for other_metadata in other_metadata_list:
                if isinstance(other_metadata, dict):
                    desc_metadatas = other_metadata.get("DescriptionMetadatas", {})
                    desc_metadata_list = desc_metadatas.get("DescriptionMetadata", [])

                    if isinstance(desc_metadata_list, list):
                        for desc_metadata in desc_metadata_list:
                            if isinstance(desc_metadata, dict) and desc_metadata.get("MetadataKey") == "SHOPPING_RESPONSE_IDS":
                                aug_points = desc_metadata.get("AugmentationPoint", {}).get("AugPoint", [])
                                if isinstance(aug_points, list) and len(aug_points) > 0:
                                    # Use the first available ShoppingResponseID
                                    aug_point = aug_points[0]
                                    if isinstance(aug_point, dict):
                                        sr_id_val = aug_point.get("Key")
                                        sr_owner_val = aug_point.get("Owner")
                                        if sr_id_val and sr_owner_val:
                                            # Add ShoppingResponseID to the response
                                            response_copy = response.copy()
                                            response_copy["ShoppingResponseID"] = {
                                                "Owner": sr_owner_val,
                                                "ResponseID": {"value": sr_id_val}
                                            }
                                            logger.info(f"Extracted ShoppingResponseID for airline {sr_owner_val}: {sr_id_val}")
                                            return response_copy

        # Fallback: try the original logic for backward compatibility
        try:
            sr_id_val = response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Key"]
            sr_owner_val = response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Owner"]
            response_copy = response.copy()
            response_copy["ShoppingResponseID"] = {
                "Owner": sr_owner_val,
                "ResponseID": {"value": sr_id_val}
            }
            logger.info(f"Fallback: Extracted ShoppingResponseID for owner: {sr_owner_val}")
            return response_copy
        except (KeyError, IndexError, TypeError):
            logger.warning("Could not extract ShoppingResponseID from Metadata section")

    except Exception as e:
        logger.error(f"Error extracting ShoppingResponseID: {e}")

    return response

def transform_air_shopping_for_results(response: dict) -> dict:
    """
    The main transformation function for the AirShopping response.
    """
    refs = _extract_simple_refs(response)
    offers = []
    
    # This logic handles the common structure of AirShoppingRS
    offers_group = response.get('OffersGroup', {})
    airline_offers_list = offers_group.get('AirlineOffers', [])
    if not isinstance(airline_offers_list, list):
        airline_offers_list = [airline_offers_list] if airline_offers_list else []
        
    for airline_offer_group in airline_offers_list:
        # Each group can have multiple fare families (AirlineOffer)
        for offer in airline_offer_group.get('AirlineOffer', []):
            priced_offer = offer.get('PricedOffer')
            if priced_offer:
                airline_code = offer.get('OfferID', {}).get('Owner', '??')  # Get from offer, not priced_offer
                transformed = _transform_offer_for_results_page(priced_offer, refs, offer)  # Pass both
                if transformed:
                    # Store original OfferID for reference and use index as ID
                    transformed['original_offer_id'] = transformed.get('id')  # Store original OfferID
                    transformed['id'] = str(len(offers))  # Use current length as index
                    transformed['offer_index'] = len(offers)  # Keep index for reference
                    offers.append(transformed)

    # Extract ShoppingResponseID and add it to the response
    response_with_sr_id = _extract_shopping_response_id(response)

    return {
        'offers': offers,
        'total_offers': len(offers),
        'ShoppingResponseID': response_with_sr_id.get('ShoppingResponseID'),
        'raw_response': response
    }