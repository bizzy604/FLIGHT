"""
Tests for FlightPrice Ancillary Request Builder.

These tests verify the build_flightprice_ancillary_rq.py module which:
1. Detects when pricing is required (PricedInd=false)
2. Builds FlightPrice requests for unpriced items
3. Handles multi-airline scenarios
4. Extracts dynamic seat information
"""

import pytest
import json
import os
import copy
from scripts.build_flightprice_ancillary_rq import (
    build_flightprice_ancillary_request,
    detect_pricing_required,
    clean_airline_prefix_from_key,
    _extract_airline_from_flight_price_response,
    _is_multi_airline_flight_price_response,
    _extract_seat_data_from_response,
    _extract_seat_selection_info,
    normalize_to_list
)


def load_api_log(filename):
    """Load API log file from api_logs directory."""
    base_path = os.path.join(os.path.dirname(__file__), '..', 'api_logs')
    filepath = os.path.join(base_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Extract raw_response for FlightPrice
        if 'response' in data and 'raw_response' in data['response']:
            return data['response']['raw_response']
        return data.get('response', data)


class TestDetectPricingRequired:
    """Test the detect_pricing_required function with new default logic."""
    
    def test_services_with_explicit_priced_ind_false(self):
        """Services with PricedInd=false should require pricing."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Modify services to have PricedInd=false
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        # Set first 3 services to PricedInd=false
        for service in services[:3]:
            service['PricedInd'] = False
        
        selected_services = [s['ObjectKey'] for s in services[:3]]
        
        result = detect_pricing_required(
            servicelist_response=modified_servicelist,
            selected_services=selected_services
        )
        
        assert result['requires_pricing'] is True
        assert len(result['services_require_pricing']) == 3
        assert result['total_items_require_pricing'] == 3
    
    def test_services_missing_priced_ind_field(self):
        """Services without PricedInd field should default to requiring pricing."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Remove PricedInd field from first 2 services
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        for service in services[:2]:
            if 'PricedInd' in service:
                del service['PricedInd']
        
        selected_services = [s['ObjectKey'] for s in services[:2]]
        
        result = detect_pricing_required(
            servicelist_response=modified_servicelist,
            selected_services=selected_services
        )
        
        # Missing PricedInd should default to False (requires pricing)
        assert result['requires_pricing'] is True
        assert len(result['services_require_pricing']) == 2
    
    def test_seats_with_priced_ind_false(self):
        """Seats with PricedInd=false should require pricing."""
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Modify seats to have PricedInd=false
        modified_seatavailability = copy.deepcopy(seatavailability)
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        for seat in seats[:2]:
            seat['PricedInd'] = False
        
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        result = detect_pricing_required(
            seatavailability_response=modified_seatavailability,
            selected_seats=selected_seats
        )
        
        assert result['requires_pricing'] is True
        assert len(result['seats_require_pricing']) == 2
    
    def test_mixed_priced_and_unpriced_items(self):
        """Mix of priced and unpriced items should detect correctly."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Modify: 1 service unpriced, 1 seat unpriced
        modified_servicelist = copy.deepcopy(servicelist)
        modified_seatavailability = copy.deepcopy(seatavailability)
        
        services = modified_servicelist.get('Services', {}).get('Service', [])
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        # Find services that have PricedInd=true
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        
        if len(services_with_priced_true) >= 2:
            # Set first to false, keep second as true
            services_with_priced_true[0]['PricedInd'] = False
            selected_services = [s['ObjectKey'] for s in services_with_priced_true[:2]]
        else:
            selected_services = []
        
        # Set first seat to false
        seats[0]['PricedInd'] = False
        selected_seats = [seats[0]['ObjectKey'], seats[1]['ObjectKey']]
        
        result = detect_pricing_required(
            servicelist_response=modified_servicelist,
            seatavailability_response=modified_seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        assert result['requires_pricing'] is True
        if selected_services:
            assert len(result['services_require_pricing']) == 1
        assert len(result['seats_require_pricing']) == 1
    
    def test_no_pricing_required_when_all_priced(self):
        """Items with PricedInd=true should not require pricing."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Select only services/seats that have PricedInd=true
        services = servicelist.get('Services', {}).get('Service', [])
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        selected_services = [s['ObjectKey'] for s in services_with_priced_true[:3]]
        
        seats = seatavailability.get('Services', {}).get('Service', [])
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        result = detect_pricing_required(
            servicelist_response=servicelist,
            seatavailability_response=seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        assert result['requires_pricing'] is False
        assert len(result['services_require_pricing']) == 0
        assert len(result['seats_require_pricing']) == 0


class TestBuildFlightPriceAncillaryRequest:
    """Test building FlightPrice request for ancillary pricing."""
    
    def test_build_request_with_unpriced_services(self):
        """Build FlightPrice request for services with PricedInd=false."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Modify services to have PricedInd=false
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        for service in services[:2]:
            service['PricedInd'] = False
        
        selected_services = [s['ObjectKey'] for s in services[:2]]
        
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            servicelist_response=modified_servicelist,
            selected_services=selected_services
        )
        
        # Verify request structure
        assert 'Query' in request
        assert 'Offers' in request['Query']
        assert 'Offer' in request['Query']['Offers']
        
        offers = request['Query']['Offers']['Offer']
        assert len(offers) > 0
        
        # Verify OfferItemIDs include services
        offer = offers[0]
        offer_item_ids = offer.get('OfferItemIDs', {}).get('OfferItemID', [])
        
        # Should have flight + 2 services
        assert len(offer_item_ids) >= 3
        
        # Verify service ObjectKeys are in the request
        service_keys_in_request = [item.get('value') for item in offer_item_ids]
        for service_key in selected_services:
            assert service_key in service_keys_in_request
    
    def test_build_request_with_unpriced_seats(self):
        """Build FlightPrice request for seats with PricedInd=false."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Modify seats to have PricedInd=false
        modified_seatavailability = copy.deepcopy(seatavailability)
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        for seat in seats[:2]:
            seat['PricedInd'] = False
        
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            seatavailability_response=modified_seatavailability,
            selected_seats=selected_seats
        )
        
        # Verify seat ObjectKeys are in the request
        offers = request['Query']['Offers']['Offer']
        offer_item_ids = offers[0].get('OfferItemIDs', {}).get('OfferItemID', [])
        
        seat_keys_in_request = [item.get('value') for item in offer_item_ids]
        for seat_key in selected_seats:
            assert seat_key in seat_keys_in_request
        
        # Verify seats have SelectedSeat structure
        seat_items = [item for item in offer_item_ids if 'SelectedSeat' in item]
        assert len(seat_items) == 2
    
    def test_build_request_with_mixed_items(self):
        """Build FlightPrice request with both services and seats."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Modify to have some unpriced items
        modified_servicelist = copy.deepcopy(servicelist)
        modified_seatavailability = copy.deepcopy(seatavailability)
        
        services = modified_servicelist.get('Services', {}).get('Service', [])
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        services[0]['PricedInd'] = False
        seats[0]['PricedInd'] = False
        
        selected_services = [services[0]['ObjectKey']]
        selected_seats = [seats[0]['ObjectKey']]
        
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            servicelist_response=modified_servicelist,
            seatavailability_response=modified_seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        # Should have flight + 1 service + 1 seat
        offers = request['Query']['Offers']['Offer']
        offer_item_ids = offers[0].get('OfferItemIDs', {}).get('OfferItemID', [])
        
        assert len(offer_item_ids) >= 3
    
    def test_request_includes_travelers(self):
        """Verify request includes traveler information."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        services[0]['PricedInd'] = False
        
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            servicelist_response=modified_servicelist,
            selected_services=[services[0]['ObjectKey']]
        )
        
        # Verify Travelers section
        assert 'Travelers' in request
        assert 'Traveler' in request['Travelers']
        travelers = request['Travelers']['Traveler']
        assert len(travelers) > 0
        
        # Verify DataLists has AnonymousTravelerList
        assert 'DataLists' in request
        assert 'AnonymousTravelerList' in request['DataLists']
        anonymous_travelers = request['DataLists']['AnonymousTravelerList']['AnonymousTraveler']
        assert len(anonymous_travelers) > 0
    
    def test_request_includes_origin_destination(self):
        """Verify request includes flight segment information."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        services[0]['PricedInd'] = False
        
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            servicelist_response=modified_servicelist,
            selected_services=[services[0]['ObjectKey']]
        )
        
        # Verify OriginDestination
        assert 'Query' in request
        assert 'OriginDestination' in request['Query']
        origin_dests = request['Query']['OriginDestination']
        assert len(origin_dests) > 0
        
        # Verify flight details
        first_od = origin_dests[0]
        assert 'Flight' in first_od
        assert len(first_od['Flight']) > 0


class TestHelperFunctions:
    """Test helper functions in the module."""
    
    def test_clean_airline_prefix_from_key(self):
        """Test removing airline prefix from keys."""
        assert clean_airline_prefix_from_key('QR-PAX1', 'QR') == 'PAX1'
        assert clean_airline_prefix_from_key('26-SEG1', '26') == 'SEG1'
        assert clean_airline_prefix_from_key('PAX1', 'QR') == 'PAX1'
        assert clean_airline_prefix_from_key('', 'QR') == ''
        assert clean_airline_prefix_from_key('QR-PAX1', '') == 'QR-PAX1'
    
    def test_extract_airline_from_flight_price_response(self):
        """Test extracting airline code from response."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        airline_code = _extract_airline_from_flight_price_response(flight_price)
        
        # Should extract airline code (Qatar Airways = QR or similar)
        assert airline_code is not None
        assert isinstance(airline_code, str)
        assert len(airline_code) >= 2
    
    def test_is_multi_airline_flight_price_response(self):
        """Test detecting multi-airline responses."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        is_multi = _is_multi_airline_flight_price_response(flight_price)
        
        # Should return boolean
        assert isinstance(is_multi, bool)
    
    def test_extract_seat_data_from_response(self):
        """Test extracting seat data from SeatAvailability response."""
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        seat_data_map = _extract_seat_data_from_response(seatavailability)
        
        # Should return a dict mapping ObjectKeys to seat data
        assert isinstance(seat_data_map, dict)
        
        # Check structure of seat data
        if seat_data_map:
            first_key = list(seat_data_map.keys())[0]
            seat_data = seat_data_map[first_key]
            
            assert 'Location' in seat_data or 'ObjectKey' in seat_data
    
    def test_normalize_to_list(self):
        """Test normalize_to_list utility function."""
        # List input
        assert normalize_to_list([1, 2, 3]) == [1, 2, 3]
        
        # Dict input
        assert normalize_to_list({'key': 'value'}) == [{'key': 'value'}]
        
        # String input
        assert normalize_to_list('test') == ['test']
        
        # None input
        assert normalize_to_list(None) == []
        
        # Empty list
        assert normalize_to_list([]) == []


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_build_request_with_no_selected_items(self):
        """Build request should handle empty selections gracefully."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            servicelist_response=None,
            seatavailability_response=None,
            selected_services=[],
            selected_seats=[]
        )
        
        # Should still build valid request with just flight
        assert 'Query' in request
        assert 'Offers' in request['Query']
    
    def test_detect_pricing_with_none_responses(self):
        """Detect pricing should handle None responses."""
        result = detect_pricing_required(
            servicelist_response=None,
            seatavailability_response=None,
            selected_services=['some-key'],
            selected_seats=['some-seat']
        )
        
        assert result['requires_pricing'] is False
        assert result['total_items_require_pricing'] == 0
    
    def test_build_request_with_invalid_offer_index(self):
        """Build request should handle invalid offer index."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        with pytest.raises(ValueError):
            build_flightprice_ancillary_request(
                flight_price_response=flight_price,
                selected_offer_index=999
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
