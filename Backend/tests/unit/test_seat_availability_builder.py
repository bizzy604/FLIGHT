"""
Unit tests for SeatAvailability Request Builder.

Tests VDC-compliant payload generation using real FlightPrice responses.
"""

import pytest
import json
from pathlib import Path
from app.builders.seat_availability import SeatAvailabilityRequestBuilder


@pytest.fixture
def real_flight_price_response():
    """Load real FlightPrice response."""
    response_file = Path(__file__).parent.parent.parent / "Seats & Services" / "4_FlightPriceRS.json"
    with open(response_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def real_seat_availability_request():
    """Load real SeatAvailability request for comparison."""
    request_file = Path(__file__).parent.parent.parent / "Seats & Services" / "7_SeatAvailabilityRQ.json"
    with open(request_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def multi_airline_flight_price_response():
    """Mock multi-airline FlightPrice response with airline prefixes."""
    return {
        "PricedFlightOffers": {
            "PricedFlightOffer": {
                "OfferID": {
                    "value": "OFFER123",
                    "Owner": "KL",
                    "Channel": "NDC"
                },
                "OfferPrice": [
                    {"OfferItemID": "ITEM1"},
                    {"OfferItemID": "ITEM2"}
                ]
            }
        },
        "ShoppingResponseID": {
            "ResponseID": {"value": "SHOP123"},
            "Owner": "KL"
        },
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "KL-PAX1",
                        "PTC": {"value": "ADT"}
                    },
                    {
                        "ObjectKey": "KL-PAX2",
                        "PTC": {"value": "CHD"}
                    }
                ]
            },
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "KL-SEG1",
                        "Departure": {
                            "AirportCode": {"value": "AMS"},
                            "Date": "2025-08-20",
                            "Time": "10:00"
                        },
                        "Arrival": {
                            "AirportCode": {"value": "JFK"},
                            "Date": "2025-08-20",
                            "Time": "13:00"
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "KL"},
                            "FlightNumber": {"value": "644"}
                        },
                        "Equipment": {"AircraftCode": {"value": "789"}},
                        "FlightDetail": {"FlightDuration": {"value": "PT8H0M"}}
                    }
                ]
            },
            "FareList": {
                "FareGroup": [
                    {
                        "ListKey": "KL-FARE1",
                        "Fare": {
                            "FareCode": {"value": "Y"}
                        },
                        "FareBasisCode": {"Code": "YRT"}
                    }
                ]
            }
        }
    }


class TestSeatAvailabilityRequestBuilder:
    """Test SeatAvailability request builder."""
    
    def test_build_seat_availability_request(self, real_flight_price_response, real_seat_availability_request):
        """Should build VDC-compliant SeatAvailability request from FlightPrice response."""
        builder = SeatAvailabilityRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        # Validate top-level structure
        assert "Travelers" in result
        assert "Query" in result
        assert "DataLists" in result
        assert "ShoppingResponseID" in result
        
        # Validate structure matches real request
        assert result["Travelers"]["Traveler"] is not None
        assert isinstance(result["Travelers"]["Traveler"], list)
        
        # Validate Query structure
        assert "OriginDestination" in result["Query"]
        assert "Offers" in result["Query"]
        
        # Validate OriginDestination has FlightSegmentReference
        od_list = result["Query"]["OriginDestination"]
        assert isinstance(od_list, list)
        assert len(od_list) > 0
        assert "FlightSegmentReference" in od_list[0]
        
        # Validate Offers structure
        offers = result["Query"]["Offers"]["Offer"]
        assert isinstance(offers, list)
        assert len(offers) == 1
        
        offer = offers[0]
        assert "OfferID" in offer
        assert "OfferItemIDs" in offer
        assert offer["OfferID"]["value"] is not None
        assert offer["OfferID"]["Owner"] is not None
        
        # Validate DataLists has FlightSegmentList and FareList
        assert "FlightSegmentList" in result["DataLists"]
        assert "FareList" in result["DataLists"]
        
        print(f"\n✅ Built SeatAvailability request with:")
        print(f"   - {len(result['Travelers']['Traveler'][0]['AnonymousTraveler'])} travelers")
        print(f"   - {len(od_list)} origin-destination(s)")
        print(f"   - {len(result['DataLists']['FlightSegmentList']['FlightSegment'])} segment(s)")
    
    def test_travelers_section_structure(self, real_flight_price_response):
        """Should group all travelers into single Traveler object."""
        builder = SeatAvailabilityRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        travelers = result["Travelers"]["Traveler"]
        
        # Should have exactly one Traveler object containing all AnonymousTraveler entries
        assert len(travelers) == 1
        assert "AnonymousTraveler" in travelers[0]
        
        anonymous_travelers = travelers[0]["AnonymousTraveler"]
        assert isinstance(anonymous_travelers, list)
        assert len(anonymous_travelers) > 0
        
        # Each AnonymousTraveler should have ObjectKey and PTC
        for traveler in anonymous_travelers:
            assert "ObjectKey" in traveler
            assert "PTC" in traveler
            assert "value" in traveler["PTC"]
    
    def test_origin_destination_with_flight_segment_reference(self, real_flight_price_response):
        """Should build OriginDestination with FlightSegmentReference."""
        builder = SeatAvailabilityRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        od_list = result["Query"]["OriginDestination"]
        
        # Each OD should have FlightSegmentReference
        for od in od_list:
            assert "FlightSegmentReference" in od
            segment_refs = od["FlightSegmentReference"]
            assert isinstance(segment_refs, list)
            assert len(segment_refs) > 0
            
            # Each reference should have 'ref' field
            for ref in segment_refs:
                assert "ref" in ref
                assert ref["ref"] is not None
    
    def test_datalists_flight_segment_structure(self, real_flight_price_response):
        """Should include complete FlightSegment details in DataLists."""
        builder = SeatAvailabilityRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        segments = result["DataLists"]["FlightSegmentList"]["FlightSegment"]
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        # Validate first segment structure
        segment = segments[0]
        assert "SegmentKey" in segment
        assert "Departure" in segment
        assert "Arrival" in segment
        assert "MarketingCarrier" in segment
        assert "Equipment" in segment
        assert "FlightDetail" in segment
        
        # Validate Departure structure
        dep = segment["Departure"]
        assert "AirportCode" in dep
        assert "Date" in dep
        assert "Time" in dep
        
        # Validate Arrival structure
        arr = segment["Arrival"]
        assert "AirportCode" in arr
        assert "Date" in arr
        assert "Time" in arr
    
    def test_datalists_fare_group_structure(self, real_flight_price_response):
        """Should include FareList with proper structure (FareCode only, no FareDetail)."""
        builder = SeatAvailabilityRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        fare_groups = result["DataLists"]["FareList"]["FareGroup"]
        assert isinstance(fare_groups, list)
        assert len(fare_groups) > 0
        
        # Validate FareGroup structure per VDC spec
        fare_group = fare_groups[0]
        assert "ListKey" in fare_group
        assert "Fare" in fare_group
        assert "FareBasisCode" in fare_group
        
        # VDC spec: Fare should only have FareCode, not FareDetail
        fare = fare_group["Fare"]
        if fare:  # Can be empty dict
            assert "FareCode" in fare or len(fare) == 0
            # Should NOT have FareDetail
            assert "FareDetail" not in fare
    
    def test_shopping_response_id_mapping(self, real_flight_price_response):
        """Should correctly map ShoppingResponseID."""
        builder = SeatAvailabilityRequestBuilder()
        result = builder.build(real_flight_price_response)
        
        shopping_response_id = result["ShoppingResponseID"]
        assert "ResponseID" in shopping_response_id
        assert "value" in shopping_response_id["ResponseID"]
        assert shopping_response_id["ResponseID"]["value"] is not None
        assert len(shopping_response_id["ResponseID"]["value"]) > 0
    
    def test_offer_item_ids_mapping(self, real_flight_price_response):
        """Should correctly map OfferItemIDs from OfferPrice."""
        builder = SeatAvailabilityRequestBuilder()
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
        builder = SeatAvailabilityRequestBuilder()
        
        is_multi = builder._is_multi_airline_response(multi_airline_flight_price_response)
        assert is_multi is True
    
    def test_airline_code_extraction(self, multi_airline_flight_price_response):
        """Should extract airline code from multi-airline response."""
        builder = SeatAvailabilityRequestBuilder()
        
        airline_code = builder._extract_airline_code(multi_airline_flight_price_response)
        assert airline_code == "KL"
    
    def test_airline_prefix_filtering(self, multi_airline_flight_price_response):
        """Should filter and remove airline prefixes from multi-airline response."""
        builder = SeatAvailabilityRequestBuilder()
        
        filtered = builder._filter_airline_data(multi_airline_flight_price_response, "KL")
        
        # Check travelers are filtered and prefixes removed
        travelers = filtered["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"]
        assert len(travelers) == 2
        assert travelers[0]["ObjectKey"] == "PAX1"  # Prefix removed
        assert travelers[1]["ObjectKey"] == "PAX2"  # Prefix removed
        
        # Check segments are filtered and prefixes removed
        segments = filtered["DataLists"]["FlightSegmentList"]["FlightSegment"]
        assert len(segments) == 1
        assert segments[0]["SegmentKey"] == "SEG1"  # Prefix removed
        
        # Check fare groups are filtered and prefixes removed
        fare_groups = filtered["DataLists"]["FareList"]["FareGroup"]
        assert len(fare_groups) == 1
        assert fare_groups[0]["ListKey"] == "FARE1"  # Prefix removed
    
    def test_round_trip_detection(self):
        """Should detect round-trip from segment patterns."""
        builder = SeatAvailabilityRequestBuilder()
        
        # Round-trip segments (BOM -> LHR -> BOM)
        round_trip_segments = [
            {
                "SegmentKey": "SEG1",
                "Departure": {"AirportCode": {"value": "BOM"}},
                "Arrival": {"AirportCode": {"value": "LHR"}}
            },
            {
                "SegmentKey": "SEG2",
                "Departure": {"AirportCode": {"value": "LHR"}},
                "Arrival": {"AirportCode": {"value": "BOM"}}
            }
        ]
        
        is_round_trip = builder._detect_round_trip(round_trip_segments)
        assert is_round_trip is True
        
        # One-way segments (BOM -> LHR)
        one_way_segments = [
            {
                "SegmentKey": "SEG1",
                "Departure": {"AirportCode": {"value": "BOM"}},
                "Arrival": {"AirportCode": {"value": "LHR"}}
            }
        ]
        
        is_round_trip = builder._detect_round_trip(one_way_segments)
        assert is_round_trip is False
    
    def test_round_trip_segment_grouping(self):
        """Should correctly group segments into outbound and return."""
        builder = SeatAvailabilityRequestBuilder()
        
        segments = [
            {
                "SegmentKey": "SEG1",
                "Departure": {"AirportCode": {"value": "BOM"}},
                "Arrival": {"AirportCode": {"value": "LHR"}}
            },
            {
                "SegmentKey": "SEG2",
                "Departure": {"AirportCode": {"value": "LHR"}},
                "Arrival": {"AirportCode": {"value": "BOM"}}
            }
        ]
        
        outbound, return_segs = builder._group_round_trip_segments(segments)
        
        assert len(outbound) == 1
        assert len(return_segs) == 1
        assert outbound[0]["SegmentKey"] == "SEG1"
        assert return_segs[0]["SegmentKey"] == "SEG2"
    
    def test_missing_offer_id_raises_error(self):
        """Should raise ValueError when OfferID is missing."""
        builder = SeatAvailabilityRequestBuilder()
        
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
        builder = SeatAvailabilityRequestBuilder()
        
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
        builder = SeatAvailabilityRequestBuilder()
        
        invalid_response = {
            "PricedFlightOffers": {},  # No offers
            "ShoppingResponseID": {"ResponseID": {"value": "SHOP123"}},
            "DataLists": {}
        }
        
        with pytest.raises(ValueError, match="No PricedFlightOffers found"):
            builder.build(invalid_response)
    
    def test_builder_idempotency(self, real_flight_price_response):
        """Should produce same output for same input (idempotent)."""
        builder = SeatAvailabilityRequestBuilder()
        
        result1 = builder.build(real_flight_price_response)
        result2 = builder.build(real_flight_price_response)
        
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
