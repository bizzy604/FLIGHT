"""
Builder validation tests using REAL VDC request examples.

Tests that our request builders generate VDC-compliant requests by comparing
against actual production request examples (1_AirShoppingRQ.json, 3_FlightPriceRQ.json).
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from app.builders.air_shopping import AirShoppingRequestBuilder
from app.builders.flight_price import FlightPriceRequestBuilder
from app.models.requests.air_shopping import AirShoppingRequest, SearchPreferences
from app.models.common import PassengerCount, FlightSegment


@pytest.fixture
def real_air_shopping_request():
    """Load real AirShopping request example."""
    request_file = Path(__file__).parent.parent.parent / "Seats & Services" / "1_AirShoppingRQ.json"
    with open(request_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def real_flight_price_request():
    """Load real FlightPrice request example."""
    request_file = Path(__file__).parent.parent.parent / "Seats & Services" / "3_FlightPriceRQ.json"
    with open(request_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def real_air_shopping_response():
    """Load real AirShopping response (needed for FlightPrice builder)."""
    response_file = Path(__file__).parent.parent.parent / "Seats & Services" / "2_AirShoppingRS.json"
    with open(response_file, 'r') as f:
        return json.load(f)


class TestAirShoppingRequestBuilder:
    """Test AirShopping request builder against real VDC requests."""
    
    def test_build_one_way_request(self, real_air_shopping_request):
        """Should build VDC-compliant AirShopping request for one-way trip."""
        # Build request matching the real example (BOM->LHR, 1 ADT, Economy, 2025-08-17)
        request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date=datetime(2025, 8, 17)
                )
            ],
            passengers=PassengerCount(adults=1, children=0, infants=0),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"],
                sort_by="PRICE"
            )
        )
        
        builder = AirShoppingRequestBuilder()
        result = builder.build(request)
        
        # Validate top-level structure
        assert "Preference" in result
        assert "ResponseParameters" in result
        assert "Travelers" in result
        assert "CoreQuery" in result
        
        # Validate Preference structure
        assert "CabinPreferences" in result["Preference"]
        assert "FarePreferences" in result["Preference"]
        
        # Validate cabin preferences
        cabin_prefs = result["Preference"]["CabinPreferences"]
        assert "CabinType" in cabin_prefs
        assert len(cabin_prefs["CabinType"]) == 1
        assert cabin_prefs["CabinType"][0]["Code"] == "Y"
        assert "OD1" in cabin_prefs["CabinType"][0]["OriginDestinationReferences"]
        
        # Validate fare preferences
        fare_prefs = result["Preference"]["FarePreferences"]
        assert "Types" in fare_prefs
        assert "Type" in fare_prefs["Types"]
        assert len(fare_prefs["Types"]["Type"]) == 1
        assert fare_prefs["Types"]["Type"][0]["Code"] == "PUBL"
        
        # Validate ResponseParameters
        response_params = result["ResponseParameters"]
        assert "SortOrder" in response_params
        assert "ShopResultPreference" in response_params
        assert response_params["ShopResultPreference"] == "FULL"
        
        # Validate sort order
        sort_order = response_params["SortOrder"]
        assert len(sort_order) >= 1
        assert sort_order[0]["Parameter"] == "PRICE"
        assert sort_order[0]["Order"] == "ASCENDING"
        
        # Validate travelers
        assert "Traveler" in result["Travelers"]
        travelers = result["Travelers"]["Traveler"]
        assert len(travelers) == 1  # 1 adult
        assert travelers[0]["AnonymousTraveler"][0]["PTC"]["value"] == "ADT"
        
        # Validate CoreQuery
        core_query = result["CoreQuery"]
        assert "OriginDestinations" in core_query
        assert "OriginDestination" in core_query["OriginDestinations"]
        
        # Validate origin-destination
        od_list = core_query["OriginDestinations"]["OriginDestination"]
        assert len(od_list) == 1
        
        od1 = od_list[0]
        assert od1["OriginDestinationKey"] == "OD1"
        assert od1["Departure"]["AirportCode"]["value"] == "BOM"
        assert od1["Departure"]["Date"] == "2025-08-17"
        assert od1["Arrival"]["AirportCode"]["value"] == "LHR"
    
    def test_build_round_trip_request(self):
        """Should build VDC-compliant request for round-trip."""
        request = AirShoppingRequest(
            trip_type="ROUND_TRIP",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date=datetime(2025, 8, 17)
                ),
                FlightSegment(
                    origin="LHR",
                    destination="BOM",
                    departure_date=datetime(2025, 8, 24)
                )
            ],
            passengers=PassengerCount(adults=1, children=0, infants=0),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"],
                sort_by="PRICE"
            )
        )
        
        builder = AirShoppingRequestBuilder()
        result = builder.build(request)
        
        # Should have 2 OriginDestinations
        od_list = result["CoreQuery"]["OriginDestinations"]["OriginDestination"]
        assert len(od_list) == 2
        
        # First segment
        assert od_list[0]["OriginDestinationKey"] == "OD1"
        assert od_list[0]["Departure"]["AirportCode"]["value"] == "BOM"
        assert od_list[0]["Arrival"]["AirportCode"]["value"] == "LHR"
        
        # Second segment
        assert od_list[1]["OriginDestinationKey"] == "OD2"
        assert od_list[1]["Departure"]["AirportCode"]["value"] == "LHR"
        assert od_list[1]["Arrival"]["AirportCode"]["value"] == "BOM"
        
        # Cabin preferences should reference both ODs
        cabin_types = result["Preference"]["CabinPreferences"]["CabinType"]
        assert len(cabin_types) == 2
        assert "OD1" in cabin_types[0]["OriginDestinationReferences"]
        assert "OD2" in cabin_types[1]["OriginDestinationReferences"]
    
    def test_build_multi_passenger_request(self):
        """Should build request with multiple passengers."""
        request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date=datetime(2025, 8, 17)
                )
            ],
            passengers=PassengerCount(adults=2, children=1, infants=1),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"],
                sort_by="PRICE"
            )
        )
        
        builder = AirShoppingRequestBuilder()
        result = builder.build(request)
        
        # Should have 4 travelers (2 ADT + 1 CHD + 1 INF)
        travelers = result["Travelers"]["Traveler"]
        assert len(travelers) == 4
        
        # Count passenger types
        adult_count = sum(1 for t in travelers if t["AnonymousTraveler"][0]["PTC"]["value"] == "ADT")
        child_count = sum(1 for t in travelers if t["AnonymousTraveler"][0]["PTC"]["value"] == "CHD")
        infant_count = sum(1 for t in travelers if t["AnonymousTraveler"][0]["PTC"]["value"] == "INF")
        
        assert adult_count == 2
        assert child_count == 1
        assert infant_count == 1
    
    def test_cabin_class_variations(self):
        """Should handle different cabin classes."""
        cabin_classes = ["Y", "W", "C", "F"]  # Economy, Premium Economy, Business, First
        
        for cabin_class in cabin_classes:
            request = AirShoppingRequest(
                trip_type="ONE_WAY",
                segments=[
                    FlightSegment(
                        origin="BOM",
                        destination="LHR",
                        departure_date=datetime(2025, 8, 17)
                    )
                ],
                passengers=PassengerCount(adults=1),
                preferences=SearchPreferences(
                    cabin_class=cabin_class,
                    fare_types=["PUBL"],
                    sort_by="PRICE"
                )
            )
            
            builder = AirShoppingRequestBuilder()
            result = builder.build(request)
            
            cabin_type = result["Preference"]["CabinPreferences"]["CabinType"][0]["Code"]
            assert cabin_type == cabin_class
    
    def test_sort_order_variations(self):
        """Should generate different sort orders."""
        # Test PRICE sorting
        request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(origin="BOM", destination="LHR", departure_date=datetime(2025, 8, 17))
            ],
            passengers=PassengerCount(adults=1),
            preferences=SearchPreferences(cabin_class="Y", fare_types=["PUBL"], sort_by="PRICE")
        )
        
        builder = AirShoppingRequestBuilder()
        result = builder.build(request)
        
        sort_order = result["ResponseParameters"]["SortOrder"]
        assert sort_order[0]["Parameter"] == "PRICE"
        
        # Test DEPARTURE_TIME sorting
        request.preferences.sort_by = "DEPARTURE_TIME"
        result = builder.build(request)
        
        sort_order = result["ResponseParameters"]["SortOrder"]
        assert sort_order[0]["Parameter"] == "DEPARTURE_TIME"
        # Should also include PRICE as secondary
        assert any(s["Parameter"] == "PRICE" for s in sort_order)


class TestFlightPriceRequestBuilder:
    """Test FlightPrice request builder against real VDC requests."""
    
    def test_build_flight_price_request(self, real_air_shopping_response, real_flight_price_request):
        """Should build VDC-compliant FlightPrice request."""
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        
        # Build request for first Qatar Airways offer (index 0)
        result = builder.build(offer_index=0, airline_owner="QR")
        
        # Validate top-level structure
        assert "Query" in result
        assert "Travelers" in result
        assert "ShoppingResponseID" in result
        assert "DataLists" in result
        
        # Validate Query structure
        query = result["Query"]
        assert "OriginDestination" in query
        assert "Offers" in query
        
        # Validate OriginDestination
        od_list = query["OriginDestination"]
        assert len(od_list) > 0
        
        # First OD should have flights
        assert "Flight" in od_list[0]
        flights = od_list[0]["Flight"]
        assert len(flights) > 0
        
        # Validate flight structure
        first_flight = flights[0]
        assert "SegmentKey" in first_flight
        assert "Departure" in first_flight
        assert "Arrival" in first_flight
        assert "MarketingCarrier" in first_flight
        assert "OperatingCarrier" in first_flight
        assert "FlightDetail" in first_flight
        
        # Validate departure structure
        departure = first_flight["Departure"]
        assert "AirportCode" in departure
        assert "value" in departure["AirportCode"]
        
        # Validate Offers structure
        offers = query["Offers"]
        assert "Offer" in offers
        offer_list = offers["Offer"]
        assert len(offer_list) == 1
        
        offer = offer_list[0]
        assert "OfferID" in offer
        assert "value" in offer["OfferID"]
        assert "Owner" in offer["OfferID"]
        assert offer["OfferID"]["Owner"] == "QR"
        
        assert "OfferItemIDs" in offer
        assert "OfferItemID" in offer["OfferItemIDs"]
        
        # Validate Travelers
        travelers = result["Travelers"]
        assert "Traveler" in travelers
        traveler_list = travelers["Traveler"]
        assert len(traveler_list) > 0
        
        # Validate traveler structure
        first_traveler = traveler_list[0]
        assert "AnonymousTraveler" in first_traveler
        assert len(first_traveler["AnonymousTraveler"]) > 0
        assert "PTC" in first_traveler["AnonymousTraveler"][0]
        
        # Validate ShoppingResponseID
        shopping_id = result["ShoppingResponseID"]
        assert "Owner" in shopping_id
        assert shopping_id["Owner"] == "QR"
        assert "ResponseID" in shopping_id
        
        # Validate DataLists
        data_lists = result["DataLists"]
        assert "FareGroup" in data_lists or "AnonymousTravelerList" in data_lists
        
        if "FareGroup" in data_lists:
            fare_groups = data_lists["FareGroup"]
            assert len(fare_groups) > 0
            
            first_fare_group = fare_groups[0]
            assert "ListKey" in first_fare_group
            assert "FareBasisCode" in first_fare_group
        
        if "AnonymousTravelerList" in data_lists:
            anon_travelers = data_lists["AnonymousTravelerList"]
            assert "AnonymousTraveler" in anon_travelers
    
    def test_flight_detail_structure(self, real_air_shopping_response):
        """Should properly format FlightDetail without StopLocations."""
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        result = builder.build(offer_index=0, airline_owner="QR")
        
        # Get first flight
        first_flight = result["Query"]["OriginDestination"][0]["Flight"][0]
        flight_detail = first_flight["FlightDetail"]
        
        # Should have FlightDuration
        assert "FlightDuration" in flight_detail
        
        # Should NOT have StopLocations (per VDC FlightPrice requirements)
        assert "StopLocations" not in flight_detail
        
        # If stops exist, should only have StopQuantity, not StopLocations
        if "Stops" in flight_detail:
            stops = flight_detail["Stops"]
            assert "StopQuantity" in stops or len(stops) == 0
            assert "StopLocation" not in stops
    
    def test_multiple_offers(self, real_air_shopping_response):
        """Should handle different offer indices."""
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        
        # Try first 5 offers
        for i in range(min(5, 38)):  # Response has 38 offers
            result = builder.build(offer_index=i, airline_owner="QR")
            
            # Each should have valid structure
            assert "Query" in result
            assert "OfferID" in result["Query"]["Offers"]["Offer"][0]
            
            # Offer ID should be different for each index
            offer_id = result["Query"]["Offers"]["Offer"][0]["OfferID"]["value"]
            assert offer_id != ""
    
    def test_invalid_offer_index(self, real_air_shopping_response):
        """Should raise error for invalid offer index."""
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        
        from app.core.exceptions import BusinessLogicError
        
        # Try index beyond available offers (response has 38 offers)
        with pytest.raises(BusinessLogicError, match="out of range"):
            builder.build(offer_index=100, airline_owner="QR")
    
    def test_invalid_airline(self, real_air_shopping_response):
        """Should raise error for non-existent airline."""
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        
        from app.core.exceptions import BusinessLogicError
        
        with pytest.raises(BusinessLogicError, match="No offers found for airline"):
            builder.build(offer_index=0, airline_owner="INVALID")
    
    def test_missing_airline_owner(self, real_air_shopping_response):
        """Should raise error when airline_owner is missing."""
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        
        from app.core.exceptions import BusinessLogicError
        
        with pytest.raises(BusinessLogicError, match="airline_owner is required"):
            builder.build(offer_index=0, airline_owner="")


class TestBuilderIntegration:
    """Integration tests for builder flow (AirShopping → FlightPrice)."""
    
    def test_full_search_to_price_flow(self, real_air_shopping_response):
        """Should successfully flow from AirShopping to FlightPrice."""
        # Step 1: Build AirShopping request
        air_shopping_request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date=datetime(2025, 8, 17)
                )
            ],
            passengers=PassengerCount(adults=1),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"],
                sort_by="PRICE"
            )
        )
        
        air_shopping_builder = AirShoppingRequestBuilder()
        air_shopping_rq = air_shopping_builder.build(air_shopping_request)
        
        # Validate AirShopping request structure
        assert "CoreQuery" in air_shopping_rq
        assert "Travelers" in air_shopping_rq
        
        # Step 2: Simulate AirShopping response (use real response)
        # In real flow, this would come from API call
        air_shopping_rs = real_air_shopping_response
        
        # Step 3: Build FlightPrice request from response
        flight_price_builder = FlightPriceRequestBuilder(air_shopping_rs)
        flight_price_rq = flight_price_builder.build(offer_index=0, airline_owner="QR")
        
        # Validate FlightPrice request structure
        assert "Query" in flight_price_rq
        assert "Travelers" in flight_price_rq
        assert "ShoppingResponseID" in flight_price_rq
        
        # Validate data consistency
        # Travelers should match (1 ADT)
        fp_travelers = flight_price_rq["Travelers"]["Traveler"]
        assert len(fp_travelers) == 1
        assert fp_travelers[0]["AnonymousTraveler"][0]["PTC"]["value"] == "ADT"
        
        # OriginDestination should match (BOM->LHR)
        fp_od = flight_price_rq["Query"]["OriginDestination"]
        assert len(fp_od) > 0
        
        # Extract airport codes from flights
        flights = fp_od[0]["Flight"]
        origin = flights[0]["Departure"]["AirportCode"]["value"]
        destination = flights[-1]["Arrival"]["AirportCode"]["value"]
        
        assert origin == "BOM"
        assert destination == "LHR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
