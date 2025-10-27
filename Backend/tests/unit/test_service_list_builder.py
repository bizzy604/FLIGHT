"""
Unit tests for ServiceList Request Builder.

Tests VDC-compliant payload generation using real FlightPrice responses.
"""

import pytest
import json
from pathlib import Path
from app.builders.service_list import ServiceListRequestBuilder


@pytest.fixture
def real_flight_price_response():
    """Load real FlightPrice response."""
    response_file = Path(__file__).parent.parent.parent / "Seats & Services" / "4_FlightPriceRS.json"
    with open(response_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def real_service_list_request():
    """Load real ServiceList request for comparison."""
    request_file = Path(__file__).parent.parent.parent / "Seats & Services" / "5_ServiceListRQ.json"
    with open(request_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def multi_airline_flight_price_response():
    """Mock multi-airline FlightPrice response with airline prefixes."""
    return {
        "PricedFlightOffers": {
            "PricedFlightOffer": {
                "OfferID": {
                    "value": "OFFER456",
                    "Owner": "BA",
                    "Channel": "NDC"
                },
                "OfferPrice": [
                    {"OfferItemID": "ITEM1"},
                    {"OfferItemID": "ITEM2"}
                ]
            }
        },
        "ShoppingResponseID": {
            "ResponseID": {"value": "SHOP456"},
            "Owner": "BA"
        },
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "BA-PAX1",
                        "PTC": {"value": "ADT"}
                    }
                ]
            },
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "BA-SEG1",
                        "Departure": {
                            "AirportCode": {"value": "LHR"},
                            "Date": "2025-09-15",
                            "Time": "14:00",
                            "AirportName": "London Heathrow",
                            "Terminal": {"Name": "5"}
                        },
                        "Arrival": {
                            "AirportCode": {"value": "JFK"},
                            "Date": "2025-09-15",
                            "Time": "17:00",
                            "AirportName": "New York JFK",
                            "Terminal": {"Name": "7"}
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "BA"},
                            "FlightNumber": {"value": "117"}
                        },
                        "Equipment": {"AircraftCode": {"value": "77W"}},
                        "FlightDetail": {"FlightDuration": {"value": "PT7H0M"}}
                    },
                    {
                        "SegmentKey": "BA-SEG2",
                        "Departure": {
                            "AirportCode": {"value": "JFK"},
                            "Date": "2025-09-20",
                            "Time": "20:00",
                            "AirportName": "New York JFK"
                        },
                        "Arrival": {
                            "AirportCode": {"value": "LHR"},
                            "Date": "2025-09-21",
                            "Time": "08:00",
                            "AirportName": "London Heathrow"
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "BA"},
                            "FlightNumber": {"value": "112"}
                        },
                        "Equipment": {"AircraftCode": {"value": "77W"}},
                        "FlightDetail": {"FlightDuration": {"value": "PT7H0M"}}
                    }
                ]
            }
        }
    }


class TestServiceListRequestBuilder:
    """Test ServiceList request builder."""
    
    def test_build_service_list_request(self, real_flight_price_response, real_service_list_request):
        """Should build VDC-compliant ServiceList request from FlightPrice response."""
        builder = ServiceListRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        # Validate top-level structure
        assert "Travelers" in result
        assert "Query" in result
        assert "ShoppingResponseID" in result
        
        # ServiceList does NOT have DataLists (unlike SeatAvailability)
        # This is a key difference between the two APIs
        
        # Validate structure matches real request
        assert result["Travelers"]["Traveler"] is not None
        assert isinstance(result["Travelers"]["Traveler"], list)
        
        # Validate Query structure
        assert "OriginDestination" in result["Query"]
        assert "Offers" in result["Query"]
        
        # Validate OriginDestination has Flight details (not FlightSegmentReference)
        od_list = result["Query"]["OriginDestination"]
        assert isinstance(od_list, list)
        assert len(od_list) > 0
        assert "Flight" in od_list[0]
        
        # Validate Offers structure
        offers = result["Query"]["Offers"]["Offer"]
        assert isinstance(offers, list)
        assert len(offers) == 1
        
        offer = offers[0]
        assert "OfferID" in offer
        assert "OfferItemIDs" in offer
        assert offer["OfferID"]["value"] is not None
        assert offer["OfferID"]["Owner"] is not None
        
        print(f"\n✅ Built ServiceList request with:")
        print(f"   - {len(result['Travelers']['Traveler'])} traveler(s)")
        print(f"   - {len(od_list)} origin-destination(s)")
        flights_count = sum(len(od.get('Flight', [])) for od in od_list)
        print(f"   - {flights_count} flight(s)")
    
    def test_travelers_section_structure(self, real_flight_price_response):
        """Should create separate Traveler object for each passenger (different from SeatAvailability)."""
        builder = ServiceListRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        travelers = result["Travelers"]["Traveler"]
        
        # ServiceList: each traveler gets its own Traveler object
        # (Different from SeatAvailability which groups all into one)
        assert isinstance(travelers, list)
        assert len(travelers) > 0
        
        # Each Traveler should have AnonymousTraveler array
        for traveler in travelers:
            assert "AnonymousTraveler" in traveler
            anonymous_list = traveler["AnonymousTraveler"]
            assert isinstance(anonymous_list, list)
            assert len(anonymous_list) == 1  # One entry per Traveler object
            
            # Each AnonymousTraveler should have ObjectKey and PTC
            anonymous_traveler = anonymous_list[0]
            assert "ObjectKey" in anonymous_traveler
            assert "PTC" in anonymous_traveler
            assert "value" in anonymous_traveler["PTC"]
    
    def test_origin_destination_with_flight_details(self, real_flight_price_response):
        """Should build OriginDestination with full Flight details."""
        builder = ServiceListRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        od_list = result["Query"]["OriginDestination"]
        
        # Each OD should have Flight array (not FlightSegmentReference)
        for od in od_list:
            assert "Flight" in od
            flights = od["Flight"]
            assert isinstance(flights, list)
            assert len(flights) > 0
            
            # Validate flight structure
            for flight in flights:
                assert "SegmentKey" in flight
                assert "Departure" in flight
                assert "Arrival" in flight
                assert "MarketingCarrier" in flight
                assert "Equipment" in flight
                assert "FlightDetail" in flight
                
                # Validate Departure structure
                dep = flight["Departure"]
                assert "AirportCode" in dep
                assert "Date" in dep
                assert "Time" in dep
                
                # Validate Arrival structure
                arr = flight["Arrival"]
                assert "AirportCode" in arr
                assert "Date" in arr
                assert "Time" in arr
    
    def test_origin_destination_grouping_by_airport_pairs(self, multi_airline_flight_price_response):
        """Should group segments by origin-destination airport pairs."""
        builder = ServiceListRequestBuilder()
        result = builder.build(multi_airline_flight_price_response)
        
        od_list = result["Query"]["OriginDestination"]
        
        # With 2 segments (LHR->JFK and JFK->LHR), we expect 2 ODs
        assert len(od_list) == 2
        
        # First OD: LHR->JFK
        od1_flights = od_list[0]["Flight"]
        assert len(od1_flights) == 1
        assert od1_flights[0]["Departure"]["AirportCode"]["value"] == "LHR"
        assert od1_flights[0]["Arrival"]["AirportCode"]["value"] == "JFK"
        
        # Second OD: JFK->LHR
        od2_flights = od_list[1]["Flight"]
        assert len(od2_flights) == 1
        assert od2_flights[0]["Departure"]["AirportCode"]["value"] == "JFK"
        assert od2_flights[0]["Arrival"]["AirportCode"]["value"] == "LHR"
    
    def test_flight_entry_optional_fields(self, multi_airline_flight_price_response):
        """Should include optional fields like AirportName and Terminal when present."""
        builder = ServiceListRequestBuilder()
        result = builder.build(multi_airline_flight_price_response)
        
        flight = result["Query"]["OriginDestination"][0]["Flight"][0]
        
        # Check optional fields are included
        assert "AirportName" in flight["Departure"]
        assert flight["Departure"]["AirportName"] == "London Heathrow"
        
        assert "Terminal" in flight["Departure"]
        assert flight["Departure"]["Terminal"]["Name"] == "5"
        
        assert "AirportName" in flight["Arrival"]
        assert flight["Arrival"]["AirportName"] == "New York JFK"
    
    def test_shopping_response_id_mapping(self, real_flight_price_response):
        """Should correctly map ShoppingResponseID."""
        builder = ServiceListRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        shopping_response_id = result["ShoppingResponseID"]
        assert "ResponseID" in shopping_response_id
        assert "value" in shopping_response_id["ResponseID"]
        assert shopping_response_id["ResponseID"]["value"] is not None
        assert len(shopping_response_id["ResponseID"]["value"]) > 0
    
    def test_offer_item_ids_mapping(self, real_flight_price_response):
        """Should correctly map OfferItemIDs from OfferPrice."""
        builder = ServiceListRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        offer = result["Query"]["Offers"]["Offer"][0]
        offer_item_ids = offer["OfferItemIDs"]["OfferItemID"]
        
        assert isinstance(offer_item_ids, list)
        assert len(offer_item_ids) > 0
        
        # Each OfferItemID should have 'value' field
        for item_id in offer_item_ids:
            assert "value" in item_id
            assert item_id["value"] is not None
    
    def test_multi_airline_detection(self, multi_airline_flight_price_response):
        """Should detect multi-airline response from airline prefixes."""
        builder = ServiceListRequestBuilder()
        
        is_multi = builder._is_multi_airline_response(multi_airline_flight_price_response)
        assert is_multi is True
    
    def test_airline_code_extraction(self, multi_airline_flight_price_response):
        """Should extract airline code from multi-airline response."""
        builder = ServiceListRequestBuilder()
        
        airline_code = builder._extract_airline_code(multi_airline_flight_price_response)
        assert airline_code == "BA"
    
    def test_airline_prefix_filtering(self, multi_airline_flight_price_response):
        """Should filter and remove airline prefixes from multi-airline response."""
        builder = ServiceListRequestBuilder()
        
        filtered = builder._filter_airline_data(multi_airline_flight_price_response, "BA")
        
        # Check travelers are filtered and prefixes removed
        travelers = filtered["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"]
        assert len(travelers) == 1
        assert travelers[0]["ObjectKey"] == "PAX1"  # Prefix removed
        
        # Check segments are filtered and prefixes removed
        segments = filtered["DataLists"]["FlightSegmentList"]["FlightSegment"]
        assert len(segments) == 2
        assert segments[0]["SegmentKey"] == "SEG1"  # Prefix removed
        assert segments[1]["SegmentKey"] == "SEG2"  # Prefix removed
    
    def test_missing_offer_id_raises_error(self):
        """Should raise ValueError when OfferID is missing."""
        builder = ServiceListRequestBuilder()
        
        invalid_response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": {
                    "OfferID": {},  # Missing value and Owner
                    "OfferPrice": []
                }
            },
            "ShoppingResponseID": {"ResponseID": {"value": "SHOP123"}},
            "DataLists": {}
        }
        
        with pytest.raises(ValueError, match="OfferID value or Owner missing"):
            builder.build(invalid_response)
    
    def test_missing_shopping_response_id_raises_error(self):
        """Should raise ValueError when ShoppingResponseID is missing."""
        builder = ServiceListRequestBuilder()
        
        invalid_response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": {
                    "OfferID": {"value": "OFFER123", "Owner": "BA"},
                    "OfferPrice": []
                }
            },
            "ShoppingResponseID": {},  # Missing ResponseID
            "DataLists": {}
        }
        
        with pytest.raises(ValueError, match="ShoppingResponseID missing"):
            builder.build(invalid_response)
    
    def test_no_priced_offers_raises_error(self):
        """Should raise ValueError when no PricedFlightOffers present."""
        builder = ServiceListRequestBuilder()
        
        invalid_response = {
            "PricedFlightOffers": {},  # No offers
            "ShoppingResponseID": {"ResponseID": {"value": "SHOP123"}},
            "DataLists": {}
        }
        
        with pytest.raises(ValueError, match="No PricedFlightOffers found"):
            builder.build(invalid_response)
    
    def test_builder_idempotency(self, real_flight_price_response):
        """Should produce same output for same input (idempotent)."""
        builder = ServiceListRequestBuilder()
        
        result1 = builder.build(real_flight_price_response)
        result2 = builder.build(real_flight_price_response)
        
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)
    
    def test_no_datalists_in_output(self, real_flight_price_response):
        """Should NOT include DataLists in output (key difference from SeatAvailability)."""
        builder = ServiceListRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        # ServiceList request does NOT have DataLists
        assert "DataLists" not in result
        
        # But it should have complete Flight details in OriginDestination
        assert "Query" in result
        assert "OriginDestination" in result["Query"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
