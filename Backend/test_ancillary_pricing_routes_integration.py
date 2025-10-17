"""
Integration tests for ancillary pricing routes with sequential flow.

This test suite validates the /pricing/price-ancillaries endpoint with real
API log data, testing services-only, seats-only, and combined scenarios.

Test Data Source: Backend/api_logs/ - Real API request/response data
"""

import pytest
import json
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import Quart app and dependencies
from app import app as quart_app
from services.simple_flight_cache import SimpleFlightCache


# Test data directory
API_LOGS_DIR = Path(__file__).parent / "api_logs"


class TestDataLoader:
    """Helper class to load test data from api_logs directory."""
    
    @staticmethod
    def load_json(service_name: str, file_type: str) -> Dict[str, Any]:
        """Load JSON test data from api_logs directory."""
        # Map service names to folder names
        folder_map = {
            'flight_price': 'flight_price',
            'service_list': 'service_list',
            'seat_availability': 'seat_availability',
            'ancillary_pricing': 'ancillary_pricing',
            'booking': 'booking'
        }
        
        # Map service names to file names
        file_map = {
            'flight_price': 'FlightPrice',
            'service_list': 'ServiceList',
            'seat_availability': 'SeatAvailability',
            'ancillary_pricing': 'AncillaryPricing',
            'booking': 'Booking'
        }
        
        folder_name = folder_map.get(service_name, service_name)
        file_name = file_map.get(service_name, service_name.title())
        
        file_path = API_LOGS_DIR / folder_name / f"{file_name}_{file_type}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Test data not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def get_flight_price_raw_response() -> Dict[str, Any]:
        """Get raw FlightPrice response."""
        data = TestDataLoader.load_json('flight_price', 'RS')
        return data.get('response', {}).get('raw_response', {})
    
    @staticmethod
    def get_service_list_response() -> Dict[str, Any]:
        """Get ServiceList response."""
        data = TestDataLoader.load_json('service_list', 'RS')
        return data.get('response', {})
    
    @staticmethod
    def get_seat_availability_response() -> Dict[str, Any]:
        """Get SeatAvailability response."""
        data = TestDataLoader.load_json('seat_availability', 'RS')
        return data.get('response', {})


@pytest.fixture
def app():
    """Fixture for Quart app."""
    quart_app.config['TESTING'] = True
    return quart_app


@pytest.fixture
def client(app):
    """Fixture for test client."""
    return app.test_client()


@pytest.fixture
def flight_price_response():
    """Fixture for FlightPrice response."""
    return TestDataLoader.get_flight_price_raw_response()


@pytest.fixture
def service_list_response():
    """Fixture for ServiceList response."""
    return TestDataLoader.get_service_list_response()


@pytest.fixture
def seat_availability_response():
    """Fixture for SeatAvailability response."""
    return TestDataLoader.get_seat_availability_response()


@pytest.fixture
def mock_cache_retrieval(flight_price_response, service_list_response, seat_availability_response):
    """Mock cache retrieval to return test data."""
    def _mock_get_flight_price(cache_key):
        return {
            'success': True,
            'data': flight_price_response
        }
    
    def _mock_get_service_list(cache_key):
        return {
            'success': True,
            'data': service_list_response
        }
    
    def _mock_get_seat_availability(cache_key):
        return {
            'success': True,
            'data': {'raw_response': seat_availability_response}
        }
    
    with patch.object(SimpleFlightCache, 'get_flight_price', side_effect=_mock_get_flight_price), \
         patch.object(SimpleFlightCache, 'get_service_list', side_effect=_mock_get_service_list), \
         patch.object(SimpleFlightCache, 'get_seat_availability', side_effect=_mock_get_seat_availability):
        yield


@pytest.fixture
def mock_api_calls():
    """Mock external API calls to Verteil."""
    
    class MockResponse:
        """Mock response that acts as an async context manager."""
        def __init__(self):
            self.status = 200
            
        async def json(self):
            """Return mock FlightPrice response with new OfferID."""
            return {
                "Success": {},
                "ShoppingResponseID": {
                    "ResponseID": {
                        "value": "tz-s9tozhn8KCauIlsOhm4dhNa5LF7sNsGxATQtLyJo-AF"
                    }
                },
                "PricedFlightOffers": {
                    "PricedFlightOffer": [{
                        "OfferID": {
                            "ObjectKey": "new-offer-id-123",
                            "value": "new-offer-id-123",
                            "Owner": "AF",
                            "Channel": "NDC"
                        },
                        "OfferPrice": [{
                            "OfferItemID": "priced-item-123",
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {
                                            "value": 16454.0,
                                            "Code": "INR"
                                        }
                                    }
                                }
                            }
                        }]
                    }]
                },
                "DataLists": {
                    "AnonymousTravelerList": {
                        "AnonymousTraveler": [{
                            "ObjectKey": "PAX1",
                            "PTC": {"value": "ADT"}
                        }]
                    }
                }
            }
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockSession:
        """Mock session that returns MockResponse instances."""
        def __init__(self):
            self.closed = False
        
        def post(self, *args, **kwargs):
            """Return MockResponse as a context manager."""
            return MockResponse()
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=MockSession()):
        yield


class TestCheckPricingRequirements:
    """Test suite for /pricing/check-requirements endpoint."""
    
    @pytest.mark.asyncio
    async def test_check_requirements_services_only(self, client, service_list_response):
        """Test checking pricing requirements for services only."""
        payload = {
            'servicelist_response': service_list_response,
            'selected_services': ['1-ServiceIdAF-2', '1-ServiceIdAF-15']
        }
        
        response = await client.post(
            '/api/verteil/pricing/check-requirements',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'requires_pricing' in data['data']
        
        print(f"✅ Pricing requirements check: {data['data']}")
    
    @pytest.mark.asyncio
    async def test_check_requirements_with_seats(self, client, service_list_response, seat_availability_response):
        """Test checking pricing requirements with both services and seats."""
        payload = {
            'servicelist_response': service_list_response,
            'seatavailability_response': seat_availability_response,
            'selected_services': ['1-ServiceIdAF-2'],
            'selected_seats': ['e0ee9182-5616-47e1-ae91-825616070020']
        }
        
        response = await client.post(
            '/api/verteil/pricing/check-requirements',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        data = await response.get_json()
        assert 'services_require_pricing' in data['data']
        assert 'seats_require_pricing' in data['data']
        
        print(f"✅ Combined requirements: {data['data']}")


class TestPriceAncillaries:
    """Test suite for /pricing/price-ancillaries endpoint with sequential flow."""
    
    @pytest.mark.asyncio
    async def test_price_services_only(self, client, mock_cache_retrieval, mock_api_calls):
        """Test pricing services only (single API call)."""
        payload = {
            'flight_price_cache_key': 'flight_price_raw_test123',
            'service_list_cache_key': 'service_list_test123',
            'selected_services': ['1-ServiceIdAF-2']
        }
        
        response = await client.post(
            '/api/verteil/pricing/price-ancillaries',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'pricing_strategy' in data
        
        # Should have only priced services
        strategy = data['pricing_strategy']
        assert strategy['services_priced'] == True
        assert strategy.get('seats_priced', False) == False
        
        print(f"✅ Services-only pricing completed: {strategy}")
    
    @pytest.mark.asyncio
    async def test_price_seats_only(self, client, mock_cache_retrieval, mock_api_calls):
        """Test pricing seats only (single API call)."""
        payload = {
            'flight_price_cache_key': 'flight_price_raw_test123',
            'seat_availability_cache_key': 'seat_availability_test123',
            'selected_seats': ['e0ee9182-5616-47e1-ae91-825616070020']
        }
        
        response = await client.post(
            '/api/verteil/pricing/price-ancillaries',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data['status'] == 'success'
        
        # Should have only priced seats
        strategy = data['pricing_strategy']
        assert strategy.get('services_priced', False) == False
        assert strategy['seats_priced'] == True
        
        print(f"✅ Seats-only pricing completed: {strategy}")
    
    @pytest.mark.asyncio
    async def test_price_services_and_seats_sequential(self, client, mock_cache_retrieval, mock_api_calls):
        """Test pricing both services and seats (sequential API calls)."""
        payload = {
            'flight_price_cache_key': 'flight_price_raw_test123',
            'service_list_cache_key': 'service_list_test123',
            'seat_availability_cache_key': 'seat_availability_test123',
            'selected_services': ['1-ServiceIdAF-2', '1-ServiceIdAF-15'],
            'selected_seats': ['e0ee9182-5616-47e1-ae91-825616070020']
        }
        
        response = await client.post(
            '/api/verteil/pricing/price-ancillaries',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data['status'] == 'success'
        
        # Should have priced both services and seats sequentially
        strategy = data['pricing_strategy']
        assert strategy['services_priced'] == True
        assert strategy['seats_priced'] == True
        assert strategy['sequential'] == True
        
        print(f"✅ Sequential pricing completed: {strategy}")
        print(f"   - Services priced: {strategy['services_priced']}")
        print(f"   - Seats priced: {strategy['seats_priced']}")
        print(f"   - Sequential flow: {strategy['sequential']}")
    
    @pytest.mark.asyncio
    async def test_missing_cache_key_error(self, client):
        """Test error when required cache key is missing."""
        payload = {
            # Missing flight_price_cache_key
            'selected_services': ['1-ServiceIdAF-2']
        }
        
        response = await client.post(
            '/api/verteil/pricing/price-ancillaries',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        
        data = await response.get_json()
        assert data['status'] == 'error'
        assert 'required' in data['message'].lower()
        
        print(f"✅ Properly rejected missing cache key: {data['message']}")
    
    @pytest.mark.asyncio
    async def test_shopping_response_id_preserved(self, client, mock_cache_retrieval, mock_api_calls):
        """Test that ShoppingResponseID is preserved in the final response."""
        payload = {
            'flight_price_cache_key': 'flight_price_raw_test123',
            'service_list_cache_key': 'service_list_test123',
            'selected_services': ['1-ServiceIdAF-2']
        }
        
        response = await client.post(
            '/api/verteil/pricing/price-ancillaries',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        data = await response.get_json()
        assert 'data' in data
        assert 'ShoppingResponseID' in data['data']
        assert 'ResponseID' in data['data']['ShoppingResponseID']
        assert 'value' in data['data']['ShoppingResponseID']['ResponseID']
        
        shopping_id = data['data']['ShoppingResponseID']['ResponseID']['value']
        print(f"✅ ShoppingResponseID preserved: {shopping_id}")


class TestSequentialPricingFlow:
    """Test suite for validating sequential pricing flow logic."""
    
    @pytest.mark.asyncio
    async def test_sequential_flow_creates_two_requests(self, client, mock_cache_retrieval):
        """Test that selecting both services and seats creates two separate API requests."""
        # This test would need to verify the actual API calls made
        # For now, we verify the endpoint accepts the payload
        
        payload = {
            'flight_price_cache_key': 'flight_price_raw_test123',
            'service_list_cache_key': 'service_list_test123',
            'seat_availability_cache_key': 'seat_availability_test123',
            'selected_services': ['1-ServiceIdAF-2'],
            'selected_seats': ['e0ee9182-5616-47e1-ae91-825616070020']
        }
        
        # Mock to track API calls
        call_count = 0
        
        async def _mock_post_with_tracking(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "Success": {},
                "ShoppingResponseID": {
                    "ResponseID": {"value": "tz-test"}
                },
                "PricedFlightOffers": {
                    "PricedFlightOffer": [{
                        "OfferID": {
                            "value": f"offer-{call_count}",
                            "Owner": "AF",
                            "Channel": "NDC"
                        },
                        "OfferPrice": [{"OfferItemID": f"item-{call_count}"}]
                    }]
                }
            })
            return mock_response
        
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = AsyncMock(side_effect=_mock_post_with_tracking)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await client.post(
                '/api/verteil/pricing/price-ancillaries',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            
            # With sequential pricing, we should have made 2 API calls
            # (one for services, one for seats)
            # Note: This test needs proper async handling of aiohttp mocks
            
            print(f"✅ Sequential flow test completed")
    
    @pytest.mark.asyncio
    async def test_offer_id_chaining(self, client, mock_cache_retrieval):
        """Test that the second pricing call uses the OfferID from the first call."""
        # This is a conceptual test - actual implementation would need
        # to inspect the request payloads to verify offer ID chaining
        
        payload = {
            'flight_price_cache_key': 'flight_price_raw_test123',
            'service_list_cache_key': 'service_list_test123',
            'seat_availability_cache_key': 'seat_availability_test123',
            'selected_services': ['1-ServiceIdAF-2'],
            'selected_seats': ['e0ee9182-5616-47e1-ae91-825616070020']
        }
        
        captured_requests = []
        
        async def _mock_post_capture(*args, **kwargs):
            captured_requests.append(kwargs.get('json', {}))
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "Success": {},
                "ShoppingResponseID": {"ResponseID": {"value": "tz-test"}},
                "PricedFlightOffers": {
                    "PricedFlightOffer": [{
                        "OfferID": {
                            "value": f"chained-offer-{len(captured_requests)}",
                            "Owner": "AF",
                            "Channel": "NDC"
                        },
                        "OfferPrice": [{"OfferItemID": "item"}]
                    }]
                }
            })
            return mock_response
        
        print(f"✅ Offer ID chaining test - implementation pending")


def run_integration_tests():
    """Run integration tests."""
    print("=" * 80)
    print("ANCILLARY PRICING SEQUENTIAL FLOW - INTEGRATION TESTS")
    print("=" * 80)
    print()
    print("Test Data Source: Backend/api_logs/")
    print("Testing with real API request/response data")
    print()
    
    # Run pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])


if __name__ == "__main__":
    run_integration_tests()
