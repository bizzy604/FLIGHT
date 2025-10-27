"""
Integration tests for OrderCreate flow using real VDC API responses.

This module tests the complete OrderCreate flow with actual API responses:
1. Scenario 1: Priced ancillaries (pricedInd=true) - From "Seats & Services" folder
2. Scenario 2: Unpriced ancillaries (pricedInd=false) - From "Shopping and booking..." folder

Tests validate:
- Builder correctly processes real VDC responses  
- Service orchestration with real data
- Transformer extracts booking details from real OrderCreateRS
- Price calculations using TotalAmount
- Ancillary structures (OtherItem, Location)
"""

import json
import pytest
import sys
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# Add Backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.builders.order_create import OrderCreateRequestBuilder
from app.services.order_create import OrderCreateService
from app.transformers.order_create import OrderCreateTransformer


# Path to real API responses
BACKEND_DIR = Path(__file__).parent.parent.parent
PRICED_FOLDER = BACKEND_DIR / "Seats & Services"
UNPRICED_FOLDER = BACKEND_DIR / "Shopping and booking with Seat and Ancillary where both of them requires pricing"


# ============================================================================
# FIXTURES - Load Real API Responses
# ============================================================================

@pytest.fixture
def priced_flight_price_response():
    """Load FlightPriceRS from Seats & Services (priced ancillaries)."""
    with open(PRICED_FOLDER / "4_FlightPriceRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def priced_service_list_response():
    """Load ServiceListRS from Seats & Services (priced ancillaries)."""
    with open(PRICED_FOLDER / "6_ServiceListRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def priced_seat_availability_response():
    """Load SeatAvailabilityRS from Seats & Services (priced ancillaries)."""
    with open(PRICED_FOLDER / "8_SeatAvailabilityRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def priced_order_create_response():
    """Load OrderCreateRS from Seats & Services (priced ancillaries)."""
    with open(PRICED_FOLDER / "10_OrderCreateRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def unpriced_flight_price_response():
    """Load initial FlightPriceRS from Shopping folder (unpriced ancillaries)."""
    with open(UNPRICED_FOLDER / "4_FlightPriceRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def unpriced_service_list_response():
    """Load ServiceListRS from Shopping folder (unpriced ancillaries)."""
    with open(UNPRICED_FOLDER / "6_ServiceListRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def unpriced_seat_availability_response():
    """Load SeatAvailabilityRS from Shopping folder (unpriced ancillaries)."""
    with open(UNPRICED_FOLDER / "8_SeatAvailabilityRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def unpriced_ancillary_pricing_response():
    """Load FlightPriceRS after ancillary pricing (10_FlightPriceRS.json)."""
    with open(UNPRICED_FOLDER / "10_FlightPriceRS.json", "r") as f:
        return json.load(f)


@pytest.fixture
def unpriced_order_create_response():
    """Load OrderCreateRS from Shopping folder (unpriced ancillaries)."""
    with open(UNPRICED_FOLDER / "12_OrderViewRS.json", "r") as f:
        return json.load(f)


# ============================================================================
# SCENARIO 1: PRICED ANCILLARIES (pricedInd=true)
# ============================================================================

class TestPricedAncillariesFlow:
    """Test complete OrderCreate flow with priced ancillaries (Seats & Services folder)."""

    @pytest.fixture
    def sample_payment(self):
        """Payment information."""
        return {
            "method": "CASH",
            "amount": 56415,
            "currency": "INR",
            "card_number": "4111111111111111",
            "card_type": "VI",
            "card_holder_name": "JOHN DOE",
            "expiry_date": "12/25"
        }

    def test_builder_with_priced_ancillaries(
        self,
        priced_flight_price_response,
        priced_service_list_response,
        priced_seat_availability_response,
        sample_payment
    ):
        """
        Test OrderCreate builder with priced ancillaries from real VDC responses.
        
        Validates:
        - Builder processes real FlightPriceRS structure
        - Extracts TotalAmount.SimpleCurrencyPrice for pricing
        - Creates valid OrderCreate request structure
        - Payment amount matches TotalAmount (56415 INR)
        """
        builder = OrderCreateRequestBuilder()
        
        # Passengers matching the real response
        passengers = [
            {
                "id": "PAX1",
                "type": "ADT",
                "given_name": "JOHN",
                "surname": "DOE",
                "gender": "Male",
                "birthdate": "1990-01-15",
                "email": "john.doe@example.com",
                "phone": "+1234567890"
            }
        ]
        
        # Build OrderCreate request
        request = builder.build_request(
            flight_price_response=priced_flight_price_response,
            passengers=passengers,
            payment=sample_payment,
            seatavailability_response=priced_seat_availability_response,
            servicelist_response=priced_service_list_response,
            selected_seats=["30F"],  # ObjectKey format
            selected_services=["SRV4"]  # ObjectKey format
        )
        
        # Validate Query structure exists
        assert "Query" in request
        query = request["Query"]
        
        # Validate Passengers
        assert "Passengers" in query
        assert "Passenger" in query["Passengers"]
        assert len(query["Passengers"]["Passenger"]) == 1
        pax = query["Passengers"]["Passenger"][0]
        assert pax["ObjectKey"] == "PAX1"
        assert pax["Name"]["Given"][0]["value"] == "JOHN"
        assert pax["Name"]["Surname"]["value"] == "DOE"
        
        # Validate OrderItems exist
        assert "OrderItems" in query
        assert "OfferItem" in query["OrderItems"]
        offer_items = query["OrderItems"]["OfferItem"]
        
        # Should have at least flight item
        assert len(offer_items) >= 1
        
        # Find flight item
        flight_item = next(
            (item for item in offer_items 
             if "DetailedFlightItem" in item.get("OfferItemType", {})),
            None
        )
        assert flight_item is not None, "Flight item should be present"
        
        # Validate Payments - should use TotalAmount
        assert "Payments" in query
        assert "Payment" in query["Payments"]
        payment = query["Payments"]["Payment"][0]
        
        # Expected total: 56415 (TotalAmount from FlightPriceRS)
        assert "Amount" in payment
        assert payment["Amount"]["value"] == 56415  # TotalAmount from response
        assert payment["Amount"]["Code"] == "INR"

    @pytest.mark.asyncio
    async def test_transformer_with_priced_order_response(
        self,
        priced_order_create_response
    ):
        """
        Test OrderCreate transformer with real OrderCreateRS.
        
        Validates extraction of:
        - Booking reference
        - Order ID
        - Total price
        - Passengers
        - Flights
        """
        transformer = OrderCreateTransformer()
        
        # Transform response
        result = transformer.transform(priced_order_create_response)
        
        # Validate success
        assert result["success"] is True
        
        # Validate booking reference (flat structure, not nested)
        assert "booking_reference" in result
        assert result["booking_reference"] is not None
        assert result["booking_reference"] != ""
        
        # Validate order ID
        assert "order_id" in result
        assert result["order_id"] is not None
        
        # Validate total price
        assert "total_price" in result
        total_price = result["total_price"]
        assert "amount" in total_price
        assert total_price["amount"] > 0
        assert total_price["currency"] == "INR"
        
        # Validate passengers exist
        assert "passengers" in result
        assert len(result["passengers"]) > 0
        
        # Validate flights exist
        assert "flights" in result


# ============================================================================
# SCENARIO 2: UNPRICED ANCILLARIES (pricedInd=false)
# ============================================================================

class TestUnpricedAncillariesFlow:
    """Test complete OrderCreate flow with unpriced ancillaries (Shopping folder)."""

    @pytest.fixture
    def sample_payment(self):
        """Payment information for unpriced scenario."""
        return {
            "method": "CASH",
            "amount": 12577,
            "currency": "INR",
            "card_number": "4111111111111111",
            "card_type": "VI",
            "card_holder_name": "JANE SMITH",
            "expiry_date": "12/25"
        }

    def test_builder_with_unpriced_ancillaries(
        self,
        unpriced_flight_price_response,
        unpriced_service_list_response,
        unpriced_seat_availability_response,
        unpriced_ancillary_pricing_response,
        sample_payment
    ):
        """
        Test OrderCreate builder with unpriced ancillaries (requires ancillary pricing).
        
        Validates:
        - Builder uses ancillary_pricing_response for pricing
        - Prices extracted from TotalAmount
        - Valid OrderCreate structure created
        """
        builder = OrderCreateRequestBuilder()
        
        passengers = [
            {
                "id": "PAX1",
                "type": "ADT",
                "given_name": "JANE",
                "surname": "SMITH",
                "gender": "Female",
                "birthdate": "1985-05-20",
                "email": "jane.smith@example.com",
                "phone": "+9876543210"
            }
        ]
        
        # Build OrderCreate request with ancillary pricing
        request = builder.build_request(
            flight_price_response=unpriced_flight_price_response,
            passengers=passengers,
            payment=sample_payment,
            seatavailability_response=unpriced_seat_availability_response,
            servicelist_response=unpriced_service_list_response,
            selected_seats=["15A"],
            selected_services=["SRV2"],
            ancillary_pricing_response=unpriced_ancillary_pricing_response
        )
        
        # Validate structure
        assert "Query" in request
        query = request["Query"]
        
        # Validate Passengers
        assert "Passengers" in query
        assert len(query["Passengers"]["Passenger"]) == 1
        pax = query["Passengers"]["Passenger"][0]
        assert pax["ObjectKey"] == "PAX1"
        assert pax["Name"]["Given"][0]["value"] == "JANE"
        
        # Validate OrderItems exist
        assert "OrderItems" in query
        offer_items = query["OrderItems"]["OfferItem"]
        assert len(offer_items) >= 1
        
        # Find flight item
        flight_item = next(
            (item for item in offer_items 
             if "DetailedFlightItem" in item.get("OfferItemType", {})),
            None
        )
        assert flight_item is not None
        
        # Validate payment amount
        payment = query["Payments"]["Payment"][0]
        assert payment["Amount"]["value"] >= 12577  # At least base flight cost
        assert payment["Amount"]["Code"] == "INR"

    @pytest.mark.asyncio
    async def test_transformer_with_unpriced_order_response(
        self,
        unpriced_order_create_response
    ):
        """
        Test OrderCreate transformer with real OrderViewRS.
        
        Validates extraction of booking details.
        """
        transformer = OrderCreateTransformer()
        
        # Transform response
        result = transformer.transform(unpriced_order_create_response)
        
        # Validate success
        assert result["success"] is True
        
        # Validate booking reference
        assert "booking_reference" in result
        assert result["booking_reference"] is not None
        
        # Validate order ID
        assert "order_id" in result
        assert result["order_id"] is not None
        
        # Validate price exists
        assert "total_price" in result


# ============================================================================
# SCENARIO 3: SERVICE INTEGRATION TEST
# ============================================================================

class TestOrderCreateServiceIntegration:
    """Test OrderCreate service with real responses (mocked HTTP calls)."""

    @pytest.fixture
    def mock_token_manager(self):
        """Mock TokenManager for authentication."""
        with patch('app.services.order_create.TokenManager') as mock:
            instance = MagicMock()
            instance.get_token = AsyncMock(return_value="mock_token_12345")
            mock.get_instance.return_value = instance
            yield mock

    @pytest.mark.asyncio
    async def test_service_create_booking_with_priced_ancillaries(
        self,
        mock_token_manager,
        priced_flight_price_response,
        priced_order_create_response
    ):
        """
        Test OrderCreateService.create_booking() with priced ancillaries.
        
        Mocks HTTP call, validates service orchestration.
        """
        service = OrderCreateService()
        
        # Mock HTTP client to return OrderCreateRS
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = priced_order_create_response
        mock_response.raise_for_status = Mock()
        
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Create booking
            result = await service.create_booking(
                flight_price_response=priced_flight_price_response,
                passengers=[{
                    "id": "PAX1",
                    "type": "ADT",
                    "given_name": "JOHN",
                    "surname": "DOE",
                    "gender": "Male",
                    "birthdate": "1990-01-15",
                    "email": "john@example.com",
                    "phone": "+1234567890"
                }],
                payment={
                    "method": "CASH",
                    "amount": 56415,
                    "currency": "INR",
                    "card_number": "4111111111111111",
                    "card_type": "VI",
                    "card_holder_name": "JOHN DOE",
                    "expiry_date": "12/25"
                }
            )
        
        # Validate result structure
        assert "success" in result
        assert result["success"] is True
        
        # Validate booking details exist
        assert "booking_reference" in result
        assert "order_id" in result
        
        # Validate HTTP call was made
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_create_booking_with_unpriced_ancillaries(
        self,
        mock_token_manager,
        unpriced_flight_price_response,
        unpriced_ancillary_pricing_response,
        unpriced_order_create_response
    ):
        """
        Test OrderCreateService.create_booking() with unpriced ancillaries.
        """
        service = OrderCreateService()
        
        # Mock HTTP client
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = unpriced_order_create_response
        mock_response.raise_for_status = Mock()
        
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await service.create_booking(
                flight_price_response=unpriced_flight_price_response,
                passengers=[{
                    "id": "PAX1",
                    "type": "ADT",
                    "given_name": "JANE",
                    "surname": "SMITH",
                    "gender": "Female",
                    "birthdate": "1985-05-20",
                    "email": "jane@example.com",
                    "phone": "+9876543210"
                }],
                payment={
                    "method": "CASH",
                    "amount": 12577,
                    "currency": "INR",
                    "card_number": "4111111111111111",
                    "card_type": "VI",
                    "card_holder_name": "JANE SMITH",
                    "expiry_date": "12/25"
                },
                seatavailability_response=None,
                servicelist_response=None,
                ancillary_pricing_response=unpriced_ancillary_pricing_response
            )
        
        # Validate result
        assert result["success"] is True
        assert "booking_reference" in result
        
        # Validate HTTP call
        mock_client.post.assert_called_once()


# ============================================================================
# ERROR SCENARIOS
# ============================================================================

class TestOrderCreateErrorScenarios:
    """Test error handling in OrderCreate flow."""

    def test_builder_missing_required_fields(self):
        """Test builder validation with missing required fields."""
        builder = OrderCreateRequestBuilder()
        
        with pytest.raises((ValueError, KeyError, TypeError)):
            # Missing passengers
            builder.build_request(
                flight_price_response={},
                passengers=[],  # Empty passengers
                payment={}
            )

    def test_builder_invalid_flight_price_response(self):
        """Test builder with invalid FlightPriceRS structure."""
        builder = OrderCreateRequestBuilder()
        
        with pytest.raises((ValueError, KeyError, TypeError)):
            builder.build_request(
                flight_price_response={"invalid": "structure"},
                passengers=[{
                    "id": "PAX1",
                    "type": "ADT",
                    "given_name": "TEST",
                    "surname": "USER"
                }],
                payment={"method": "CASH", "amount": 100, "currency": "INR"}
            )

    @pytest.mark.asyncio
    async def test_service_api_error_handling(self):
        """Test service handles API errors correctly."""
        service = OrderCreateService()
        
        # Mock HTTP error
        with patch('app.services.order_create.TokenManager') as mock_tm:
            instance = MagicMock()
            instance.get_token = AsyncMock(return_value="mock_token")
            mock_tm.get_instance.return_value = instance
            
            # Mock HTTP client with error response
            mock_client = Mock(spec=httpx.AsyncClient)
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_response.json.return_value = {
                "Errors": {"Error": [{"value": "Invalid request"}]}
            }
            mock_response.raise_for_status = Mock(
                side_effect=httpx.HTTPStatusError(
                    "Bad Request", 
                    request=Mock(), 
                    response=mock_response
                )
            )
            
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                # Service catches exceptions and returns error dict
                result = await service.create_booking(
                    flight_price_response={},
                    passengers=[],
                    payment={}
                )
                
                # Should return error result
                assert result["success"] is False
                assert "error" in result
                assert result["error_type"] == "validation_error"

    def test_transformer_invalid_response(self):
        """Test transformer handles invalid OrderCreateRS."""
        transformer = OrderCreateTransformer()
        
        # Invalid response should return error result
        result = transformer.transform({"invalid": "response"})
        
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
