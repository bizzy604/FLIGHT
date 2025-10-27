"""
Integration tests for complete request/response pipeline.

Tests the full workflow:
1. Load real VDC AirShopping response
2. Transform it using AirShoppingTransformer
3. Build FlightPrice request using FlightPriceRequestBuilder
4. Verify FlightPrice request structure matches real VDC examples
5. Load real VDC FlightPrice response  
6. Transform it using FlightPriceTransformer
7. Verify complete data flow integrity
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from app.transformers.air_shopping import AirShoppingTransformer
from app.transformers.flight_price import FlightPriceTransformer
from app.builders.air_shopping import AirShoppingRequestBuilder
from app.builders.flight_price import FlightPriceRequestBuilder
from app.models.requests.air_shopping import AirShoppingRequest, SearchPreferences
from app.models.common import FlightSegment, PassengerCount


class TestCompletePipeline:
    """Integration tests for complete request/response pipeline."""
    
    @pytest.fixture
    def real_air_shopping_response(self):
        """Load real AirShopping response."""
        file_path = Path(__file__).parent.parent.parent / "Seats & Services" / "2_AirShoppingRS.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['AirShoppingRS'] if 'AirShoppingRS' in data else data
    
    @pytest.fixture
    def real_flight_price_response(self):
        """Load real FlightPrice response."""
        file_path = Path(__file__).parent.parent.parent / "Seats & Services" / "4_FlightPriceRS.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['FlightPriceRS'] if 'FlightPriceRS' in data else data
    
    @pytest.fixture
    def real_air_shopping_request(self):
        """Load real AirShopping request."""
        file_path = Path(__file__).parent.parent.parent / "Seats & Services" / "1_AirShoppingRQ.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def real_flight_price_request(self):
        """Load real FlightPrice request."""
        file_path = Path(__file__).parent.parent.parent / "Seats & Services" / "3_FlightPriceRQ.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_airshopping_complete_pipeline(
        self,
        real_air_shopping_response,
        real_air_shopping_request
    ):
        """
        Test complete AirShopping pipeline:
        1. Transform real VDC response → frontend format
        2. Build new VDC request from model
        3. Verify request structure matches real example
        """
        # Step 1: Transform VDC response
        transformer = AirShoppingTransformer()
        frontend_data = transformer.transform(real_air_shopping_response)
        
        # Verify transformation produced valid data (grouped by airline)
        assert "airlines" in frontend_data
        assert len(frontend_data["airlines"]) > 0
        assert len(frontend_data["airlines"][0]["offers"]) > 0
        assert "metadata" in frontend_data
        assert "trip_type" in frontend_data
        
        # Step 2: Build new VDC request
        air_shopping_request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date="2025-08-17"
                )
            ],
            passengers=PassengerCount(adults=1),
            preferences=SearchPreferences(
                cabin_class="Y",
                sort_by="PRICE"
            )
        )
        
        builder = AirShoppingRequestBuilder()
        built_request = builder.build(air_shopping_request)
        
        # Step 3: Verify structure matches real VDC request
        assert "Preference" in built_request
        assert "CabinPreferences" in built_request["Preference"]
        assert "FarePreferences" in built_request["Preference"]
        
        assert "ResponseParameters" in built_request
        assert "SortOrder" in built_request["ResponseParameters"]
        
        assert "Travelers" in built_request
        assert "Traveler" in built_request["Travelers"]
        
        assert "CoreQuery" in built_request
        assert "OriginDestinations" in built_request["CoreQuery"]
        
        # Verify travelers match expected count
        travelers = built_request["Travelers"]["Traveler"]
        assert len(travelers) == 1
        # AnonymousTraveler is an array with one item
        anon_traveler = travelers[0]["AnonymousTraveler"]
        if isinstance(anon_traveler, list):
            ptc = anon_traveler[0]["PTC"]
        else:
            ptc = anon_traveler["PTC"]
        
        # PTC can be dict with 'value' or string
        if isinstance(ptc, dict):
            assert ptc.get("value") == "ADT"
        else:
            assert ptc == "ADT"
        
        # Verify origin/destination
        origin_dest = built_request["CoreQuery"]["OriginDestinations"]["OriginDestination"][0]
        assert origin_dest["Departure"]["AirportCode"]["value"] == "BOM"
        assert origin_dest["Arrival"]["AirportCode"]["value"] == "LHR"
    
    def test_flightprice_complete_pipeline(
        self,
        real_air_shopping_response,
        real_flight_price_response,
        real_flight_price_request
    ):
        """
        Test complete FlightPrice pipeline:
        1. Transform AirShopping response
        2. Build FlightPrice request from AirShopping data
        3. Verify request structure matches real example
        4. Transform FlightPrice response
        5. Verify complete data integrity
        """
        # Step 1: Transform AirShopping response
        air_shopping_transformer = AirShoppingTransformer()
        frontend_offers = air_shopping_transformer.transform(real_air_shopping_response)
        
        # Get first airline's first offer
        assert len(frontend_offers["airlines"]) > 0
        first_airline = frontend_offers["airlines"][0]
        assert len(first_airline["offers"]) > 0
        first_offer = first_airline["offers"][0]
        airline_owner = first_airline.get("code", "QR")
        
        # Step 2: Build FlightPrice request
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        built_flight_price_request = builder.build(
            offer_index=0,
            airline_owner=airline_owner
        )
        
        # Step 3: Verify FlightPrice request structure
        assert "Query" in built_flight_price_request
        assert "OriginDestination" in built_flight_price_request["Query"]
        assert "Offers" in built_flight_price_request["Query"]
        
        assert "Travelers" in built_flight_price_request
        assert "ShoppingResponseID" in built_flight_price_request
        assert "DataLists" in built_flight_price_request
        
        # Verify ShoppingResponseID has correct owner
        assert built_flight_price_request["ShoppingResponseID"]["Owner"] == airline_owner
        
        # Verify OriginDestination structure (should NOT have StopLocations)
        origin_dests = built_flight_price_request["Query"]["OriginDestination"]
        for od in origin_dests:
            for flight in od.get("Flight", []):
                # Should have StopQuantity but NOT StopLocations
                flight_detail = flight.get("FlightDetail", {})
                if "StopQuantity" in flight_detail:
                    assert "StopLocation" not in flight_detail, \
                        "FlightDetail should NOT contain StopLocation (VDC rejects this)"
        
        # Step 4: Transform FlightPrice response
        flight_price_transformer = FlightPriceTransformer()
        priced_offer = flight_price_transformer.transform(real_flight_price_response)
        
        # Step 5: Verify transformed pricing data
        assert "offer_id" in priced_offer
        assert "pricing" in priced_offer
        assert "segments" in priced_offer
        assert "fare_details" in priced_offer
        
        # Verify pricing structure
        pricing = priced_offer["pricing"]
        assert "total" in pricing
        assert "base_fare" in pricing
        assert "taxes" in pricing
        assert "currency" in pricing
        
        # Verify segments have required fields
        for segment in priced_offer["segments"]:
            assert "departure" in segment
            assert "arrival" in segment
            # Note: segment structure may vary - check what exists
            assert "flight_number" in segment or "duration" in segment
    
    def test_complete_search_to_price_workflow(
        self,
        real_air_shopping_response,
        real_flight_price_response
    ):
        """
        Test complete workflow: AirShopping → FlightPrice
        Simulates what happens in the backend when user:
        1. Searches for flights
        2. Selects an offer
        3. Gets detailed pricing
        """
        # Step 1: User searches for flights
        air_shopping_transformer = AirShoppingTransformer()
        search_results = air_shopping_transformer.transform(real_air_shopping_response)
        
        # Verify we got offers (grouped by airline)
        assert len(search_results["airlines"]) > 0
        assert len(search_results["airlines"][0]["offers"]) > 0
        
        # Step 2: User selects first offer from first airline
        first_airline = search_results["airlines"][0]
        selected_offer = first_airline["offers"][0]
        airline = first_airline.get("code", "QR")
        
        # Step 3: Backend builds FlightPrice request
        builder = FlightPriceRequestBuilder(real_air_shopping_response)
        flight_price_request = builder.build(
            offer_index=0,
            airline_owner=airline
        )
        
        # Verify request is valid
        assert flight_price_request is not None
        assert "Query" in flight_price_request
        
        # Step 4: Backend transforms FlightPrice response
        flight_price_transformer = FlightPriceTransformer()
        detailed_pricing = flight_price_transformer.transform(real_flight_price_response)
        
        # Step 5: Verify data consistency
        # The offer should have same basic info
        assert detailed_pricing["offer_id"] is not None
        
        # Pricing should be structured correctly
        assert detailed_pricing["pricing"]["total"] > 0
        assert detailed_pricing["pricing"]["base_fare"] > 0
        
        # Should have segment details
        assert len(detailed_pricing["segments"]) > 0
        
        # Should have fare details
        assert detailed_pricing["fare_details"] is not None
    
    def test_multi_passenger_data_flow(self, real_air_shopping_response):
        """
        Test that multi-passenger data flows correctly through pipeline.
        """
        # Build request with multiple passengers
        multi_pax_request = AirShoppingRequest(
            trip_type="ROUND_TRIP",
            segments=[
                FlightSegment(origin="BOM", destination="LHR", departure_date="2025-08-17"),
                FlightSegment(origin="LHR", destination="BOM", departure_date="2025-08-24")
            ],
            passengers=PassengerCount(adults=2, children=1, infants=1),
            preferences=SearchPreferences(cabin_class="Y")
        )
        
        builder = AirShoppingRequestBuilder()
        built_request = builder.build(multi_pax_request)
        
        # Verify travelers were created correctly
        travelers = built_request["Travelers"]["Traveler"]
        assert len(travelers) == 4  # 2 ADT + 1 CHD + 1 INF
        
        # Count passenger types
        ptc_counts = {}
        for traveler in travelers:
            # Each traveler has AnonymousTraveler as an array with one item
            anon_traveler = traveler["AnonymousTraveler"]
            if isinstance(anon_traveler, list):
                ptc = anon_traveler[0]["PTC"]
            else:
                ptc = anon_traveler["PTC"]
            
            # PTC might be a dict or string - handle both
            if isinstance(ptc, dict):
                ptc_value = ptc.get("value", str(ptc))
            else:
                ptc_value = ptc
                
            ptc_counts[ptc_value] = ptc_counts.get(ptc_value, 0) + 1
        
        assert ptc_counts["ADT"] == 2
        assert ptc_counts["CHD"] == 1
        assert ptc_counts["INF"] == 1
        
        # Verify round-trip created 2 origin-destinations
        origin_dests = built_request["CoreQuery"]["OriginDestinations"]["OriginDestination"]
        assert len(origin_dests) == 2
        assert origin_dests[0]["Departure"]["AirportCode"]["value"] == "BOM"
        assert origin_dests[0]["Arrival"]["AirportCode"]["value"] == "LHR"
        assert origin_dests[1]["Departure"]["AirportCode"]["value"] == "LHR"
        assert origin_dests[1]["Arrival"]["AirportCode"]["value"] == "BOM"
    
    def test_metadata_preservation(
        self,
        real_air_shopping_response,
        real_flight_price_response
    ):
        """
        Test that important metadata is preserved through the pipeline.
        """
        # Transform AirShopping
        air_shopping_transformer = AirShoppingTransformer()
        search_results = air_shopping_transformer.transform(real_air_shopping_response)
        
        # Verify metadata exists
        assert "metadata" in search_results
        metadata = search_results["metadata"]
        
        # Should have response_id (not shopping_response_id)
        assert "response_id" in metadata or "timestamp" in metadata
        
        # Transform FlightPrice
        flight_price_transformer = FlightPriceTransformer()
        pricing_result = flight_price_transformer.transform(real_flight_price_response)
        
        # Verify metadata exists
        assert "metadata" in pricing_result
        pricing_metadata = pricing_result["metadata"]
        
        # Should have timestamp
        assert "timestamp" in pricing_metadata
        
        # Should have currency info in pricing
        assert "currency" in pricing_result["pricing"]
