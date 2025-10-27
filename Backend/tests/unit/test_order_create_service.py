"""
Unit tests for OrderCreate Service

Tests VDC API integration, error handling, and response extraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import sys
from pathlib import Path

# Add Backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.order_create import OrderCreateService


class TestOrderCreateService:
    """Test OrderCreateService class."""
    
    @pytest.fixture
    def service(self):
        """Create service instance with mocked dependencies."""
        with patch('app.services.order_create.TokenManager') as mock_token_manager:
            # Mock token manager
            mock_instance = MagicMock()
            mock_instance.get_token = AsyncMock(return_value="test-token-123")
            mock_token_manager.get_instance.return_value = mock_instance
            
            service = OrderCreateService()
            return service
    
    @pytest.fixture
    def sample_flight_price_response(self):
        """Sample FlightPrice response."""
        return {
            "ShoppingResponseID": {"ResponseID": {"value": "test-response-123"}},
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferID": {"value": "offer-123", "Owner": "AF"},
                    "OfferPrice": [{
                        "OfferItemID": "item-1",
                        "RequestedDate": {
                            "PriceDetail": {
                                "BaseAmount": {"value": 500, "Code": "USD"},
                                "Taxes": {"Total": {"value": 50, "Code": "USD"}}
                            }
                        }
                    }]
                }]
            },
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [{"ObjectKey": "PAX1", "PTC": {"value": "ADT"}}]
                },
                "FlightSegmentList": {"FlightSegment": []},
                "FlightList": {"Flight": []},
                "OriginDestinationList": {"OriginDestination": []},
                "FareList": {},
                "PriceClassList": {}
            }
        }
    
    @pytest.fixture
    def sample_passengers(self):
        """Sample passenger data."""
        return [{
            "given_name": "John",
            "surname": "Doe",
            "email": "john@test.com",
            "phone": "1234567890",
            "gender": "Male",
            "dob": "1990-01-01",
            "passenger_type": "ADT"
        }]
    
    @pytest.fixture
    def sample_payment(self):
        """Sample payment data."""
        return {
            "card_number": "4111111111111111",
            "card_type": "Credit",
            "card_holder_name": "John Doe",
            "expiry_date": "12/25",
            "cvv": "123"
        }
    
    @pytest.fixture
    def sample_vdc_success_response(self):
        """Sample successful VDC OrderCreate response."""
        return {
            "OrderCreateRS": {
                "Order": {
                    "OrderID": {"value": "ORDER-123"},
                    "BookingReference": {
                        "ID": {"value": "BOOKING-ABC123"}
                    },
                    "TotalPrice": {
                        "Total": {"value": 550, "Code": "USD"}
                    }
                }
            }
        }
    
    def test_validate_inputs_success(
        self,
        service,
        sample_flight_price_response,
        sample_passengers,
        sample_payment
    ):
        """Test input validation passes with valid data."""
        # Should not raise
        service._validate_inputs(
            sample_flight_price_response,
            sample_passengers,
            sample_payment
        )
    
    def test_validate_inputs_missing_flight_price(
        self,
        service,
        sample_passengers,
        sample_payment
    ):
        """Test validation fails when flight_price_response is missing."""
        with pytest.raises(ValueError, match="flight_price_response is required"):
            service._validate_inputs(None, sample_passengers, sample_payment)
    
    def test_validate_inputs_missing_passengers(
        self,
        service,
        sample_flight_price_response,
        sample_payment
    ):
        """Test validation fails when passengers are missing."""
        with pytest.raises(ValueError, match="At least one passenger is required"):
            service._validate_inputs(sample_flight_price_response, [], sample_payment)
    
    def test_validate_inputs_missing_payment(
        self,
        service,
        sample_flight_price_response,
        sample_passengers
    ):
        """Test validation fails when payment is missing."""
        with pytest.raises(ValueError, match="payment information is required"):
            service._validate_inputs(sample_flight_price_response, sample_passengers, None)
    
    def test_validate_inputs_invalid_flight_price_structure(
        self,
        service,
        sample_passengers,
        sample_payment
    ):
        """Test validation fails with invalid flight_price structure."""
        invalid_flight_price = {"invalid": "structure"}
        
        with pytest.raises(ValueError, match="Invalid flight_price_response"):
            service._validate_inputs(invalid_flight_price, sample_passengers, sample_payment)
    
    def test_validate_inputs_invalid_passenger_structure(
        self,
        service,
        sample_flight_price_response,
        sample_payment
    ):
        """Test validation fails with invalid passenger structure."""
        invalid_passengers = [{"given_name": "John"}]  # Missing required fields
        
        with pytest.raises(ValueError, match="missing required field"):
            service._validate_inputs(sample_flight_price_response, invalid_passengers, sample_payment)
    
    def test_validate_inputs_invalid_payment_structure(
        self,
        service,
        sample_flight_price_response,
        sample_passengers
    ):
        """Test validation fails with invalid payment structure."""
        invalid_payment = {"card_number": "123"}  # Missing required fields
        
        with pytest.raises(ValueError, match="missing required field"):
            service._validate_inputs(sample_flight_price_response, sample_passengers, invalid_payment)
    
    def test_build_headers(self, service):
        """Test building request headers."""
        headers = service._build_headers("test-token")
        
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"
        assert headers["service"] == "OrderCreate"
        assert "OfficeId" in headers  # Should include OfficeId from config
    
    @pytest.mark.asyncio
    async def test_call_vdc_api_success(self, service):
        """Test successful VDC API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Order": {"BookingReference": "TEST-123"}}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await service._call_vdc_api(
                {"Query": {}},
                {"Authorization": "Bearer test"}
            )
            
            assert result == {"Order": {"BookingReference": "TEST-123"}}
    
    @pytest.mark.asyncio
    async def test_call_vdc_api_http_error(self, service):
        """Test VDC API call with HTTP error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Bad Request",
                    request=MagicMock(),
                    response=MagicMock(status_code=400, text="Invalid request")
                )
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await service._call_vdc_api(
                    {"Query": {}},
                    {"Authorization": "Bearer test"}
                )
    
    @pytest.mark.asyncio
    async def test_call_vdc_api_timeout(self, service):
        """Test VDC API call with timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            with pytest.raises(httpx.TimeoutException):
                await service._call_vdc_api(
                    {"Query": {}},
                    {"Authorization": "Bearer test"}
                )
    
    @pytest.mark.asyncio
    async def test_call_vdc_api_with_vdc_errors(self, service):
        """Test VDC API call returns errors in response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Errors": {"Error": {"Message": "Invalid offer"}}
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(ValueError, match="VDC API error"):
                await service._call_vdc_api(
                    {"Query": {}},
                    {"Authorization": "Bearer test"}
                )
    
    def test_extract_booking_details_format1(self, service, sample_vdc_success_response):
        """Test extraction from OrderCreateRS.Order format."""
        result = service._extract_booking_details(sample_vdc_success_response)
        
        assert result["success"] is True
        assert result["booking_reference"] == "BOOKING-ABC123"
        assert result["order_id"] == "ORDER-123"
        assert result["raw_response"] == sample_vdc_success_response
    
    def test_extract_booking_details_format2(self, service):
        """Test extraction from Order directly at root."""
        response = {
            "Order": {
                "OrderID": {"value": "ORDER-456"},
                "BookingReference": {"ID": {"value": "BOOKING-XYZ"}}
            }
        }
        
        result = service._extract_booking_details(response)
        
        assert result["success"] is True
        assert result["booking_reference"] == "BOOKING-XYZ"
        assert result["order_id"] == "ORDER-456"
    
    def test_extract_booking_details_missing_reference(self, service):
        """Test extraction when BookingReference is missing."""
        response = {"SomeField": "SomeValue"}
        
        result = service._extract_booking_details(response)
        
        assert result["success"] is True
        assert result["booking_reference"] == "UNKNOWN"
        assert result["order_id"] == "UNKNOWN"
    
    @pytest.mark.asyncio
    async def test_create_booking_success(
        self,
        service,
        sample_flight_price_response,
        sample_passengers,
        sample_payment,
        sample_vdc_success_response
    ):
        """Test successful end-to-end booking creation."""
        # Mock builder
        with patch.object(service.builder, 'build_request', return_value={"Query": {}}):
            # Mock API call
            with patch.object(service, '_call_vdc_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = sample_vdc_success_response
                
                result = await service.create_booking(
                    flight_price_response=sample_flight_price_response,
                    passengers=sample_passengers,
                    payment=sample_payment
                )
                
                assert result["success"] is True
                assert result["booking_reference"] == "BOOKING-ABC123"
                assert result["order_id"] == "ORDER-123"
                assert "raw_response" in result
    
    @pytest.mark.asyncio
    async def test_create_booking_validation_error(
        self,
        service,
        sample_passengers,
        sample_payment
    ):
        """Test booking creation with validation error."""
        result = await service.create_booking(
            flight_price_response=None,  # Invalid
            passengers=sample_passengers,
            payment=sample_payment
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result["error_type"] == "validation_error"
    
    @pytest.mark.asyncio
    async def test_create_booking_api_error(
        self,
        service,
        sample_flight_price_response,
        sample_passengers,
        sample_payment
    ):
        """Test booking creation with API error."""
        # Mock builder
        with patch.object(service.builder, 'build_request', return_value={"Query": {}}):
            # Mock API call to raise error
            with patch.object(service, '_call_vdc_api', new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = httpx.HTTPError("API Error")
                
                result = await service.create_booking(
                    flight_price_response=sample_flight_price_response,
                    passengers=sample_passengers,
                    payment=sample_payment
                )
                
                assert result["success"] is False
                assert "error" in result
                assert result["error_type"] == "http_error"
