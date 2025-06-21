#!/usr/bin/env python3
"""
Test Dynamic ThirdPartyId Implementation

This module tests the dynamic thirdPartyId functionality for FlightPrice and OrderCreate operations.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the services to test
from services.flight.pricing import FlightPricingService
from services.flight.booking import FlightBookingService
from services.flight.core import FlightService

class TestDynamicThirdPartyId:
    """Test cases for dynamic thirdPartyId implementation."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'VERTEIL_API_BASE_URL': 'https://api.stage.verteil.com',
            'VERTEIL_USERNAME': 'test_user',
            'VERTEIL_PASSWORD': 'test_pass',
            'VERTEIL_TOKEN_ENDPOINT_PATH': '/oauth2/token',
            'VERTEIL_THIRD_PARTY_ID': 'EK',  # Default airline
            'VERTEIL_OFFICE_ID': 'TEST_OFFICE'
        }
    
    @pytest.fixture
    def sample_airshopping_response(self):
        """Sample AirShopping response with KQ airline."""
        return {
            'AirShoppingRS': {
                'OffersGroup': {
                    'AirlineOffers': [
                        {
                            'Owner': {'value': 'KQ'},
                            'AirlineOffer': [
                                {
                                    'OfferID': {
                                        'value': 'OFFER_KQ_123',
                                        'Owner': {'value': 'KQ'}
                                    },
                                    'Owner': {'value': 'KQ'},
                                    'OfferItem': [],
                                    'PricedOffer': {
                                        'OfferPrice': []
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
    
    @pytest.fixture
    def sample_flightprice_response(self):
        """Sample FlightPrice response with WY airline."""
        return {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {
                        'OfferID': {
                            'Owner': 'WY'
                        },
                        'OfferItem': []
                    }
                ]
            }
        }
    
    def test_extract_airline_code_from_offer_success(self, mock_config, sample_airshopping_response):
        """Test successful airline code extraction from AirShopping offer."""
        service = FlightPricingService(mock_config)
        
        airline_code = service._extract_airline_code_from_offer(
            sample_airshopping_response, 
            'OFFER_KQ_123'
        )
        
        assert airline_code == 'KQ'
    
    def test_extract_airline_code_from_offer_not_found(self, mock_config, sample_airshopping_response):
        """Test airline code extraction when offer not found."""
        service = FlightPricingService(mock_config)
        
        airline_code = service._extract_airline_code_from_offer(
            sample_airshopping_response, 
            'NONEXISTENT_OFFER'
        )
        
        assert airline_code is None
    
    def test_extract_airline_code_from_price_response_success(self, mock_config, sample_flightprice_response):
        """Test successful airline code extraction from FlightPrice response."""
        service = FlightBookingService(mock_config)
        
        airline_code = service._extract_airline_code_from_price_response(
            sample_flightprice_response
        )
        
        assert airline_code == 'WY'
    
    def test_extract_airline_code_from_price_response_not_found(self, mock_config):
        """Test airline code extraction when not found in FlightPrice response."""
        service = FlightBookingService(mock_config)
        
        empty_response = {'FlightPriceRS': {'PricedOffer': {}}}
        airline_code = service._extract_airline_code_from_price_response(empty_response)
        
        assert airline_code is None
    
    @pytest.mark.asyncio
    async def test_get_headers_with_dynamic_airline_code(self, mock_config):
        """Test that headers include dynamic airline code when provided."""
        service = FlightService(mock_config)
        
        # Mock the token manager
        with patch.object(service, '_get_access_token', return_value='mock_token'):
            # Test with dynamic airline code
            headers = await service._get_headers('FlightPrice', airline_code='KQ')
            assert headers['ThirdpartyId'] == 'KQ'
            
            # Test without dynamic airline code (should use default)
            headers = await service._get_headers('AirShopping')
            assert headers['ThirdpartyId'] == 'EK'  # Default from config
    
    @pytest.mark.asyncio
    async def test_pricing_service_uses_dynamic_airline_code(self, mock_config, sample_airshopping_response):
        """Test that FlightPricingService uses dynamic airline code in API calls."""
        service = FlightPricingService(mock_config)
        
        # Mock the _make_request method to capture the airline_code parameter
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = {'status': 'success'}
            
            # Mock the token manager
            with patch.object(service, '_get_access_token', return_value='mock_token'):
                await service.get_flight_price(
                    airshopping_response=sample_airshopping_response,
                    offer_id='OFFER_KQ_123',
                    shopping_response_id='SHOP_123',
                    currency='USD'
                )
                
                # Verify that _make_request was called with the correct airline_code
                mock_make_request.assert_called_once()
                call_kwargs = mock_make_request.call_args[1]
                assert call_kwargs['airline_code'] == 'KQ'
                assert call_kwargs['service_name'] == 'FlightPrice'
    
    @pytest.fixture
    def sample_passenger_data(self):
        return [
            {
                'type': 'adult',
                'title': 'mr',
                'firstName': 'John',
                'lastName': 'Doe',
                'gender': 'male',
                'nationality': 'US',
                'dob': {
                    'year': '1990',
                    'month': '01',
                    'day': '01'
                },
                'documentType': 'passport',
                'documentNumber': 'P123456789',
                'issuingCountry': 'US',
                'expiryDate': {
                    'year': '2030',
                    'month': '12',
                    'day': '31'
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_booking_service_uses_dynamic_airline_code(self, mock_config, sample_flightprice_response, sample_passenger_data):
        """Test that FlightBookingService uses dynamic airline code in API calls."""
        service = FlightBookingService(mock_config)
        
        # Mock the _make_request method to capture the airline_code parameter
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = {'status': 'success'}
            
            # Mock the token manager
            with patch.object(service, '_get_access_token', return_value='mock_token'):
                await service.create_booking(
                    flight_price_response=sample_flightprice_response,
                    passengers=sample_passenger_data,
                    payment_info={'card': '1234'},
                    contact_info={
                        'email': 'test@example.com',
                        'phone': '1234567890',
                        'phoneCountryCode': '+1',
                        'street': '123 Main St',
                        'city': 'New York',
                        'postalCode': '10001',
                        'countryCode': 'US'
                    }
                )
                
                # Verify that _make_request was called with the correct airline_code
                mock_make_request.assert_called_once()
                call_kwargs = mock_make_request.call_args[1]
                assert call_kwargs['airline_code'] == 'WY'
                assert call_kwargs['service_name'] == 'OrderCreate'
    
    def test_airline_code_extraction_error_handling(self, mock_config):
        """Test error handling in airline code extraction methods."""
        service = FlightPricingService(mock_config)
        
        # Test with malformed data
        malformed_response = {'invalid': 'structure'}
        airline_code = service._extract_airline_code_from_offer(malformed_response, 'test_offer')
        assert airline_code is None
        
        # Test with None input
        airline_code = service._extract_airline_code_from_offer(None, 'test_offer')
        assert airline_code is None

if __name__ == '__main__':
    pytest.main([__file__])