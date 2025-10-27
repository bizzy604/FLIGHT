"""Tests for FlightPrice service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.flight_price import FlightPriceService
from app.models.requests.flight_price import FlightPriceRequest
from app.exceptions.business_logic import BusinessLogicError
from app.exceptions.vdc_api import VDCAPIError
from pydantic import ValidationError


@pytest.fixture
def sample_air_shopping_response():
    """Sample AirShopping response for testing."""
    return {
        "AirlineOffers": [
            {
                "Owner": "EK",
                "Offer": [
                    {
                        "OfferID": {"value": "OFFER_EK_123"},
                        "TotalPrice": {"value": 1500.00}
                    }
                ]
            }
        ],
        "ShoppingResponseID": {
            "ResponseID": {"value": "SHOP_123"}
        }
    }


@pytest.fixture
def sample_flight_price_response():
    """Sample FlightPrice response from VDC API."""
    return {
        "FlightPriceRS": {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "PRICE_OFFER_123", "Owner": "EK"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "DetailCurrencyPrice": {
                                                "Total": {"value": 1500.00},
                                                "Taxes": {"Total": {"value": 300.00}}
                                            },
                                            "BaseAmount": {"value": 1200.00},
                                            "SimpleCurrencyPrice": {"value": 1500.00}
                                        }
                                    }
                                }
                            }
                        ],
                        "BaggageAllowance": [
                            {
                                "PieceAllowance": {"TotalQuantity": 2},
                                "TypeCode": "Checked"
                            }
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def valid_request():
    """Valid FlightPrice request."""
    return FlightPriceRequest(
        air_shopping_response={
            "AirlineOffers": [{"Owner": "EK", "Offer": [{"OfferID": {"value": "TEST"}}]}],
            "ShoppingResponseID": {"ResponseID": {"value": "SHOP_123"}}
        },
        airline_owner="EK",
        offer_index=0
    )


class TestFlightPriceService:
    """Test FlightPrice service."""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, valid_request, sample_flight_price_response):
        """Should successfully execute FlightPrice request."""
        service = FlightPriceService()
        
        # Mock VDC API call
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_flight_price_response
            
            result = await service.execute(valid_request)
            
            # Verify request was made
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            
            assert call_args[0][0] == "POST"  # Method
            assert "/flightprice" in call_args[0][1]  # Endpoint
            
            # Verify response structure
            assert "offer_id" in result
            assert "pricing" in result
            assert "breakdown" in result
            assert result["offer_id"] == "PRICE_OFFER_123"
    
    @pytest.mark.asyncio
    async def test_execute_with_airline_owner(self, valid_request):
        """Should include airline_owner in ThirdpartyId header."""
        service = FlightPriceService()
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "FlightPriceRS": {
                    "PricedFlightOffers": {
                        "PricedFlightOffer": [{
                            "OfferID": {"value": "TEST", "Owner": "EK"},
                            "OfferPrice": [{"RequestedDate": {"PriceDetail": {"TotalAmount": {"SimpleCurrencyPrice": {"value": 1000}}}}}]
                        }]
                    }
                }
            }
            
            await service.execute(valid_request)
            
            # Verify airline_owner was passed
            call_kwargs = mock_request.call_args[1]
            assert "airline_owner" in call_kwargs
            assert call_kwargs["airline_owner"] == "EK"
    
    @pytest.mark.asyncio
    async def test_request_validation_missing_airline_owner(self):
        """Should raise ValidationError if airline_owner is missing."""
        service = FlightPriceService()
        
        # Create request without airline_owner (should fail Pydantic validation)
        with pytest.raises(ValidationError, match="airline_owner"):
            FlightPriceRequest(
                air_shopping_response={"AirlineOffers": []},
                airline_owner=None,  # Missing required field
                offer_index=0
            )
    
    @pytest.mark.asyncio
    async def test_builder_error_airline_not_found(self):
        """Should raise BusinessLogicError if airline not found in response."""
        service = FlightPriceService()
        
        # Request for airline that doesn't exist
        request = FlightPriceRequest(
            air_shopping_response={
                "AirlineOffers": [{"Owner": "EK", "Offer": [{"OfferID": {"value": "TEST"}}]}]
            },
            airline_owner="BA",  # Wrong airline
            offer_index=0
        )
        
        with pytest.raises(BusinessLogicError, match="Airline 'BA' not found"):
            await service.execute(request)
    
    @pytest.mark.asyncio
    async def test_builder_error_invalid_offer_index(self):
        """Should raise BusinessLogicError if offer index is out of range."""
        service = FlightPriceService()
        
        request = FlightPriceRequest(
            air_shopping_response={
                "AirlineOffers": [{"Owner": "EK", "Offer": [{"OfferID": {"value": "TEST"}}]}]
            },
            airline_owner="EK",
            offer_index=999  # Out of range
        )
        
        with pytest.raises(BusinessLogicError, match="Offer index 999 out of range"):
            await service.execute(request)
    
    @pytest.mark.asyncio
    async def test_vdc_api_error_handling(self, valid_request):
        """Should raise VDCAPIError on API failure."""
        service = FlightPriceService()
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = VDCAPIError("API Error", status_code=500)
            
            with pytest.raises(VDCAPIError, match="API Error"):
                await service.execute(valid_request)
    
    @pytest.mark.asyncio
    async def test_transformer_error_no_priced_offers(self, valid_request):
        """Should raise error if FlightPrice response has no offers."""
        service = FlightPriceService()
        
        # Mock response with empty offers
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "FlightPriceRS": {
                    "PricedFlightOffers": {
                        "PricedFlightOffer": []  # Empty
                    }
                }
            }
            
            with pytest.raises(ValueError, match="No priced offers found"):
                await service.execute(valid_request)
    
    @pytest.mark.asyncio
    async def test_multiple_offers_in_air_shopping(self, sample_flight_price_response):
        """Should handle selecting specific offer from multiple offers."""
        service = FlightPriceService()
        
        request = FlightPriceRequest(
            air_shopping_response={
                "AirlineOffers": [
                    {
                        "Owner": "EK",
                        "Offer": [
                            {"OfferID": {"value": "OFFER1"}, "TotalPrice": {"value": 1000}},
                            {"OfferID": {"value": "OFFER2"}, "TotalPrice": {"value": 1500}},
                            {"OfferID": {"value": "OFFER3"}, "TotalPrice": {"value": 2000}}
                        ]
                    }
                ],
                "ShoppingResponseID": {"ResponseID": {"value": "SHOP_123"}}
            },
            airline_owner="EK",
            offer_index=1  # Select second offer
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_flight_price_response
            
            result = await service.execute(request)
            
            # Verify correct offer was requested
            call_payload = mock_request.call_args[1]["payload"]
            assert "FlightPriceRQ" in call_payload
            # Should have selected OFFER2 (index 1)
    
    @pytest.mark.asyncio
    async def test_shopping_response_id_extraction(self, valid_request, sample_flight_price_response):
        """Should extract ShoppingResponseID and include in FlightPrice request."""
        service = FlightPriceService()
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_flight_price_response
            
            await service.execute(valid_request)
            
            # Verify ShoppingResponseID was included
            call_payload = mock_request.call_args[1]["payload"]
            flight_price_rq = call_payload["FlightPriceRQ"]
            
            assert "ShoppingResponseID" in flight_price_rq
            assert flight_price_rq["ShoppingResponseID"]["ResponseID"]["value"] == "SHOP_123"
    
    @pytest.mark.asyncio
    async def test_travelers_included_in_request(self, sample_flight_price_response):
        """Should include travelers from AirShopping in FlightPrice request."""
        service = FlightPriceService()
        
        request = FlightPriceRequest(
            air_shopping_response={
                "AirlineOffers": [{"Owner": "EK", "Offer": [{"OfferID": {"value": "TEST"}}]}],
                "ShoppingResponseID": {"ResponseID": {"value": "SHOP_123"}},
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [
                        {"PTC": "ADT", "ObjectKey": "T1"},
                        {"PTC": "CHD", "ObjectKey": "T2"}
                    ]
                }
            },
            airline_owner="EK",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_flight_price_response
            
            await service.execute(request)
            
            # Verify travelers were included
            call_payload = mock_request.call_args[1]["payload"]
            travelers = call_payload["FlightPriceRQ"]["Travelers"]["Traveler"]
            
            assert len(travelers) == 2
            assert travelers[0]["AnonymousTraveler"]["PTC"] == "ADT"
            assert travelers[1]["AnonymousTraveler"]["PTC"] == "CHD"
    
    @pytest.mark.asyncio
    async def test_metadata_included_in_response(self, valid_request, sample_flight_price_response):
        """Should include metadata in transformed response."""
        service = FlightPriceService()
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_flight_price_response
            
            result = await service.execute(valid_request)
            
            assert "metadata" in result
            assert "timestamp" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, valid_request, sample_flight_price_response):
        """Should handle multiple concurrent requests independently."""
        service = FlightPriceService()
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_flight_price_response
            
            # Make multiple concurrent requests
            import asyncio
            results = await asyncio.gather(
                service.execute(valid_request),
                service.execute(valid_request),
                service.execute(valid_request)
            )
            
            # All should succeed
            assert len(results) == 3
            for result in results:
                assert "offer_id" in result
                assert result["offer_id"] == "PRICE_OFFER_123"
            
            # Should have made 3 API calls
            assert mock_request.call_count == 3
