"""
Unit tests for AncillaryPricingRequestBuilder.

Tests the builder that constructs FlightPrice requests with ancillary selections
(seats and services) for pricing scenarios where PricedInd=false.
"""
import json
import pytest
from pathlib import Path

from app.builders.ancillary_pricing import AncillaryPricingRequestBuilder
from app.core.exceptions import BusinessLogicError


@pytest.fixture
def live_flight_price_response():
    """Load actual FlightPrice response from live test data."""
    data_file = Path(__file__).parent / "integration" / "live_test_data" / "route_2_ancillary_price.json"
    if not data_file.exists():
        pytest.skip(f"Live test data not found: {data_file}")
    
    with open(data_file, 'r') as f:
        transformed = json.load(f)
    
    # Extract raw VDC response
    raw_response = transformed.get('raw_response', {})
    if not raw_response or 'PricedFlightOffers' not in raw_response:
        pytest.skip("Raw FlightPrice response not available in test data")
    
    return raw_response


@pytest.fixture
def live_service_list_response():
    """Load actual ServiceList response from live test data."""
    data_file = Path(__file__).parent / "integration" / "live_test_data" / "route_2_ancillary_services.json"
    if not data_file.exists():
        pytest.skip(f"Live test data not found: {data_file}")
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    return data


@pytest.fixture
def sample_flight_price_response():
    """Minimal FlightPrice response for testing."""
    return {
        "ShoppingResponseID": {
            "ResponseID": {
                "value": "test-response-id-123"
            }
        },
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": {
                        "value": "OFFER123",
                        "Owner": "EY"
                    },
                    "OfferPrice": [
                        {
                            "FareDetail": {
                                "OfferItemIDs": {
                                    "OfferItemID": [
                                        {
                                            "value": "FLIGHT-ITEM-1"
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "FlightSegmentList": {
                "FlightSegment": []
            }
        }
    }


class TestAncillaryPricingRequestBuilder:
    """Test suite for AncillaryPricingRequestBuilder."""
    
    def test_builder_initialization(self):
        """Test that builder initializes correctly."""
        builder = AncillaryPricingRequestBuilder()
        assert builder is not None
    
    def test_build_flight_only_no_ancillaries(self, sample_flight_price_response):
        """Test building request with only flight (no ancillaries selected)."""
        builder = AncillaryPricingRequestBuilder()
        
        result = builder.build(
            flight_price_response=sample_flight_price_response,
            selected_services=[],
            selected_seats=[]
        )
        
        # Should have Query.Offers.Offer structure
        assert "Query" in result
        assert "Offers" in result["Query"]
        assert "Offer" in result["Query"]["Offers"]
        
        offers = result["Query"]["Offers"]["Offer"]
        assert len(offers) == 1
        
        offer = offers[0]
        assert "OfferID" in offer
        assert offer["OfferID"]["value"] == "OFFER123"
        
        # Should have OfferItemIDs with just the flight item
        assert "OfferItemIDs" in offer
        assert "OfferItemID" in offer["OfferItemIDs"]
        
        items = offer["OfferItemIDs"]["OfferItemID"]
        assert len(items) == 1
        assert items[0]["value"] == "FLIGHT-ITEM-1"
    
    def test_build_with_service_selection(self, sample_flight_price_response):
        """Test building request with service selection."""
        builder = AncillaryPricingRequestBuilder()
        
        result = builder.build(
            flight_price_response=sample_flight_price_response,
            selected_services=["SER1-ServiceIdEY-1"],
            selected_seats=[]
        )
        
        items = result["Query"]["Offers"]["Offer"][0]["OfferItemIDs"]["OfferItemID"]
        
        # Should have flight + 1 service = 2 items
        assert len(items) == 2
        assert items[0]["value"] == "FLIGHT-ITEM-1"
        assert items[1]["value"] == "SER1-ServiceIdEY-1"
        assert items[1]["Quantity"] == 1
    
    def test_build_with_seat_selection(self, sample_flight_price_response):
        """Test building request with seat selection."""
        builder = AncillaryPricingRequestBuilder()
        
        result = builder.build(
            flight_price_response=sample_flight_price_response,
            selected_services=[],
            selected_seats=["SEAT-1A"]
        )
        
        items = result["Query"]["Offers"]["Offer"][0]["OfferItemIDs"]["OfferItemID"]
        
        # Should have flight + 1 seat = 2 items
        assert len(items) == 2
        assert items[0]["value"] == "FLIGHT-ITEM-1"
        assert items[1]["value"] == "SEAT-1A"
        assert items[1]["Quantity"] == 1
    
    def test_build_with_both_seat_and_service(self, sample_flight_price_response):
        """Test building request with both seat and service selections."""
        builder = AncillaryPricingRequestBuilder()
        
        result = builder.build(
            flight_price_response=sample_flight_price_response,
            selected_services=["SER1-ServiceIdEY-1", "SER2-ServiceIdEY-2"],
            selected_seats=["SEAT-1A", "SEAT-2B"]
        )
        
        items = result["Query"]["Offers"]["Offer"][0]["OfferItemIDs"]["OfferItemID"]
        
        # Should have flight + 2 seats + 2 services = 5 items
        assert len(items) == 5
        assert items[0]["value"] == "FLIGHT-ITEM-1"
        
        # Seats come after flight
        assert items[1]["value"] == "SEAT-1A"
        assert items[2]["value"] == "SEAT-2B"
        
        # Services come after seats
        assert items[3]["value"] == "SER1-ServiceIdEY-1"
        assert items[4]["value"] == "SER2-ServiceIdEY-2"
    
    def test_build_preserves_datalists_and_shopping_id(self, sample_flight_price_response):
        """Test that DataLists and ShoppingResponseID are preserved."""
        builder = AncillaryPricingRequestBuilder()
        
        result = builder.build(
            flight_price_response=sample_flight_price_response,
            selected_services=["SER1-ServiceIdEY-1"],
            selected_seats=[]
        )
        
        # Should preserve DataLists
        assert "DataLists" in result
        assert result["DataLists"] == sample_flight_price_response["DataLists"]
        
        # Should preserve ShoppingResponseID
        assert "ShoppingResponseID" in result
        assert result["ShoppingResponseID"] == sample_flight_price_response["ShoppingResponseID"]
    
    def test_build_with_invalid_offer_index(self, sample_flight_price_response):
        """Test that invalid offer index raises error."""
        builder = AncillaryPricingRequestBuilder()
        
        with pytest.raises(BusinessLogicError, match="Invalid selected_offer_index"):
            builder.build(
                flight_price_response=sample_flight_price_response,
                selected_offer_index=99
            )
    
    def test_build_with_no_priced_offers(self):
        """Test that missing PricedFlightOffers raises error."""
        builder = AncillaryPricingRequestBuilder()
        
        invalid_response = {
            "ShoppingResponseID": {"ResponseID": {"value": "test"}},
            "DataLists": {}
        }
        
        with pytest.raises(BusinessLogicError, match="Invalid selected_offer_index"):
            builder.build(flight_price_response=invalid_response)
    
    def test_build_with_empty_priced_offers(self):
        """Test that empty PricedFlightOffers raises error."""
        builder = AncillaryPricingRequestBuilder()
        
        invalid_response = {
            "ShoppingResponseID": {"ResponseID": {"value": "test"}},
            "PricedFlightOffers": {"PricedFlightOffer": []},
            "DataLists": {}
        }
        
        with pytest.raises(BusinessLogicError, match="Invalid selected_offer_index"):
            builder.build(flight_price_response=invalid_response)


class TestAncillaryPricingBuilderWithLiveData:
    """Test builder with actual live API responses."""
    
    def test_build_with_real_flight_price_response(self, live_flight_price_response):
        """Test builder with real FlightPrice response from live API."""
        builder = AncillaryPricingRequestBuilder()
        
        # Build with no ancillaries (just verify it works with real data)
        result = builder.build(
            flight_price_response=live_flight_price_response,
            selected_services=[],
            selected_seats=[]
        )
        
        # Basic structure validation
        assert "Query" in result
        assert "Offers" in result["Query"]
        assert "Offer" in result["Query"]["Offers"]
        
        offers = result["Query"]["Offers"]["Offer"]
        assert len(offers) == 1
        
        # Should have extracted a flight item ID
        items = offers[0]["OfferItemIDs"]["OfferItemID"]
        assert len(items) >= 1  # At least the flight item
        assert "value" in items[0]
        
        print(f"✅ Built request with flight item: {items[0]['value']}")
    
    def test_build_with_real_service_selection(self, live_flight_price_response, live_service_list_response):
        """Test builder with real FlightPrice and ServiceList responses."""
        builder = AncillaryPricingRequestBuilder()
        
        # Extract first service ObjectKey from live data
        services_data = live_service_list_response.get('data', {})
        services = services_data.get('Services', {}).get('Service', [])
        
        if not services:
            pytest.skip("No services in live data")
        
        first_service_key = services[0].get('ObjectKey')
        assert first_service_key, "First service should have ObjectKey"
        
        print(f"🔍 Using service: {first_service_key}")
        
        # Build with service selection
        result = builder.build(
            flight_price_response=live_flight_price_response,
            servicelist_response=live_service_list_response,
            selected_services=[first_service_key],
            selected_seats=[]
        )
        
        items = result["Query"]["Offers"]["Offer"][0]["OfferItemIDs"]["OfferItemID"]
        
        # Should have flight + service
        assert len(items) >= 2
        
        # Last item should be the service
        service_item = items[-1]
        assert service_item["value"] == first_service_key
        assert service_item["Quantity"] == 1
        
        print(f"✅ Built request with flight + service")
        print(f"   Flight item: {items[0]['value']}")
        print(f"   Service item: {service_item['value']}")
    
    def test_build_output_structure_matches_canonical_format(self, live_flight_price_response):
        """Verify output structure matches canonical FlightPriceRQ format."""
        builder = AncillaryPricingRequestBuilder()
        
        result = builder.build(
            flight_price_response=live_flight_price_response,
            selected_services=["SER1-ServiceIdEY-1"],
            selected_seats=[]
        )
        
        # Validate canonical structure per 9_FlightPriceRQ.json
        assert "Query" in result
        assert "Offers" in result["Query"]
        assert "Offer" in result["Query"]["Offers"]
        assert isinstance(result["Query"]["Offers"]["Offer"], list)
        
        offer = result["Query"]["Offers"]["Offer"][0]
        assert "OfferID" in offer
        assert "OfferItemIDs" in offer
        assert "OfferItemID" in offer["OfferItemIDs"]
        assert isinstance(offer["OfferItemIDs"]["OfferItemID"], list)
        
        # Each OfferItemID should have value
        for item in offer["OfferItemIDs"]["OfferItemID"]:
            assert "value" in item
            assert isinstance(item["value"], str)
        
        # Should have DataLists and ShoppingResponseID
        assert "DataLists" in result
        assert "ShoppingResponseID" in result
        
        print(f"✅ Output structure matches canonical FlightPriceRQ format")
        print(f"   Offer count: {len(result['Query']['Offers']['Offer'])}")
        print(f"   OfferItemID count: {len(offer['OfferItemIDs']['OfferItemID'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
