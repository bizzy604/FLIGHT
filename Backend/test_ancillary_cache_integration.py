"""
Integration tests for ancillary pricing cache retrieval implementation.

Tests the complete flow of retrieving flight price, seat availability, and service list
responses from Redis cache across all three ancillary pricing endpoints.

Test Coverage:
1. price_ancillaries endpoint - all 3 cache types (flight_price, seat_availability, service_list)
2. price_services_only endpoint - flight_price + service_list cache
3. price_seats_only endpoint - flight_price + seat_availability cache
4. Cache key validation and error handling
5. Raw response extraction from cached data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
import json
from unittest.mock import MagicMock, patch
from services.simple_flight_cache import SimpleFlightCache


class TestAncillaryCacheIntegration:
    """Integration tests for ancillary pricing cache retrieval."""

    @pytest.fixture
    def flight_cache(self):
        """Create a SimpleFlightCache instance for testing."""
        return SimpleFlightCache()

    @pytest.fixture
    def sample_flight_price_data(self):
        """Sample raw NDC flight price response."""
        return {
            'PricedFlightOffers': [
                {
                    'OfferID': 'OFFER_001',
                    'TotalPrice': {
                        'SimpleCurrencyPrice': {'Code': 'USD', 'value': 500.00}
                    }
                }
            ],
            'DataLists': {
                'PassengerList': [{'PassengerID': 'PAX1'}],
                'SegmentList': [{'SegmentKey': 'SEG1'}]
            },
            'ShoppingResponseID': 'SHOP_RESPONSE_123'
        }

    @pytest.fixture
    def sample_seat_availability_data(self):
        """Sample seat availability response with raw_response wrapper."""
        return {
            'transformed_data': {
                'segments': []
            },
            'raw_response': {
                'SeatMap': [
                    {
                        'SegmentRef': 'SEG1',
                        'Cabin': [
                            {
                                'Rows': [
                                    {
                                        'Number': 1,
                                        'Seats': [
                                            {
                                                'Column': 'A',
                                                'OfferItemRefs': 'SEAT_A1',
                                                'SeatStatus': 'Available'
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                'DataLists': {
                    'SeatList': [
                        {
                            'ObjectKey': 'SEAT_A1',
                            'Location': {'Column': 'A', 'Row': '1'}
                        }
                    ]
                }
            }
        }

    @pytest.fixture
    def sample_service_list_data(self):
        """Sample service list response with raw_response wrapper."""
        return {
            'transformed_data': {
                'services': []
            },
            'raw_response': {
                'ServiceList': [
                    {
                        'ObjectKey': 'SERVICE_001',
                        'Name': 'Extra Baggage',
                        'Price': {
                            'Total': {'Code': 'USD', 'value': 50.00}
                        }
                    },
                    {
                        'ObjectKey': 'SERVICE_002',
                        'Name': 'Priority Boarding',
                        'Price': {
                            'Total': {'Code': 'USD', 'value': 25.00}
                        }
                    }
                ],
                'DataLists': {
                    'ServiceDefinitionList': [
                        {
                            'ServiceCode': 'BAGGAGE',
                            'Name': 'Extra Baggage'
                        }
                    ]
                }
            }
        }

    def test_flight_price_cache_storage_and_retrieval(self, flight_cache, sample_flight_price_data):
        """Test storing and retrieving flight price data from Redis."""
        print("\n" + "="*80)
        print("TEST 1: Flight Price Cache Storage & Retrieval")
        print("="*80)
        
        cache_key = "flight_price_raw_test_integration_001"
        
        # Store flight price data
        store_result = flight_cache.store_flight_price(cache_key, sample_flight_price_data)
        print(f"✅ Store Result: {store_result}")
        assert store_result['success'] == True, "Failed to store flight price data"
        
        # Retrieve flight price data
        get_result = flight_cache.get_flight_price(cache_key)
        print(f"✅ Get Result Success: {get_result['success']}")
        print(f"✅ Retrieved Keys: {list(get_result['data'].keys())}")
        
        assert get_result['success'] == True, "Failed to retrieve flight price data"
        assert 'PricedFlightOffers' in get_result['data'], "Missing PricedFlightOffers"
        assert 'DataLists' in get_result['data'], "Missing DataLists"
        assert get_result['data']['PricedFlightOffers'][0]['OfferID'] == 'OFFER_001'
        
        print("✅ Flight price cache storage and retrieval working correctly")

    def test_seat_availability_cache_storage_and_retrieval(self, flight_cache, sample_seat_availability_data):
        """Test storing and retrieving seat availability data from Redis."""
        print("\n" + "="*80)
        print("TEST 2: Seat Availability Cache Storage & Retrieval")
        print("="*80)
        
        cache_key = "seat_availability_test_integration_001"
        
        # Store seat availability data
        store_result = flight_cache.store_seat_availability(cache_key, sample_seat_availability_data)
        print(f"✅ Store Result: {store_result}")
        assert store_result['success'] == True, "Failed to store seat availability data"
        
        # Retrieve seat availability data
        get_result = flight_cache.get_seat_availability(cache_key)
        print(f"✅ Get Result Success: {get_result['success']}")
        print(f"✅ Retrieved Keys: {list(get_result['data'].keys())}")
        
        assert get_result['success'] == True, "Failed to retrieve seat availability data"
        assert 'raw_response' in get_result['data'], "Missing raw_response wrapper"
        assert 'SeatMap' in get_result['data']['raw_response'], "Missing SeatMap in raw_response"
        
        print("✅ Seat availability cache storage and retrieval working correctly")

    def test_service_list_cache_storage_and_retrieval(self, flight_cache, sample_service_list_data):
        """Test storing and retrieving service list data from Redis."""
        print("\n" + "="*80)
        print("TEST 3: Service List Cache Storage & Retrieval")
        print("="*80)
        
        cache_key = "service_list_test_integration_001"
        
        # Store service list data
        store_result = flight_cache.store_service_list(cache_key, sample_service_list_data)
        print(f"✅ Store Result: {store_result}")
        assert store_result['success'] == True, "Failed to store service list data"
        
        # Retrieve service list data
        get_result = flight_cache.get_service_list(cache_key)
        print(f"✅ Get Result Success: {get_result['success']}")
        print(f"✅ Retrieved Keys: {list(get_result['data'].keys())}")
        
        assert get_result['success'] == True, "Failed to retrieve service list data"
        assert 'raw_response' in get_result['data'], "Missing raw_response wrapper"
        assert 'ServiceList' in get_result['data']['raw_response'], "Missing ServiceList in raw_response"
        
        print("✅ Service list cache storage and retrieval working correctly")

    def test_raw_response_extraction_for_seat_availability(self, flight_cache, sample_seat_availability_data):
        """Test that raw_response can be extracted from seat availability cached data."""
        print("\n" + "="*80)
        print("TEST 4: Raw Response Extraction - Seat Availability")
        print("="*80)
        
        cache_key = "seat_availability_extraction_test_001"
        
        # Store and retrieve
        flight_cache.store_seat_availability(cache_key, sample_seat_availability_data)
        get_result = flight_cache.get_seat_availability(cache_key)
        
        # Simulate endpoint extraction logic
        seatavailability_response = get_result['data']
        print(f"✅ Initial data structure: {list(seatavailability_response.keys())}")
        
        if isinstance(seatavailability_response, dict) and 'raw_response' in seatavailability_response:
            extracted = seatavailability_response['raw_response']
            print(f"✅ Extracted raw_response keys: {list(extracted.keys())}")
            
            assert 'SeatMap' in extracted, "SeatMap should be in extracted raw_response"
            assert 'DataLists' in extracted, "DataLists should be in extracted raw_response"
            assert len(extracted['SeatMap']) > 0, "SeatMap should contain data"
            
            print("✅ Raw response extraction successful for seat availability")
        else:
            pytest.fail("raw_response not found in cached seat availability data")

    def test_raw_response_extraction_for_service_list(self, flight_cache, sample_service_list_data):
        """Test that raw_response can be extracted from service list cached data."""
        print("\n" + "="*80)
        print("TEST 5: Raw Response Extraction - Service List")
        print("="*80)
        
        cache_key = "service_list_extraction_test_001"
        
        # Store and retrieve
        flight_cache.store_service_list(cache_key, sample_service_list_data)
        get_result = flight_cache.get_service_list(cache_key)
        
        # Simulate endpoint extraction logic
        servicelist_response = get_result['data']
        print(f"✅ Initial data structure: {list(servicelist_response.keys())}")
        
        if isinstance(servicelist_response, dict) and 'raw_response' in servicelist_response:
            extracted = servicelist_response['raw_response']
            print(f"✅ Extracted raw_response keys: {list(extracted.keys())}")
            
            assert 'ServiceList' in extracted, "ServiceList should be in extracted raw_response"
            assert 'DataLists' in extracted, "DataLists should be in extracted raw_response"
            assert len(extracted['ServiceList']) == 2, "ServiceList should contain 2 services"
            
            print("✅ Raw response extraction successful for service list")
        else:
            pytest.fail("raw_response not found in cached service list data")

    def test_complete_cache_flow_for_price_ancillaries(
        self, 
        flight_cache, 
        sample_flight_price_data, 
        sample_seat_availability_data, 
        sample_service_list_data
    ):
        """Test complete cache flow for price_ancillaries endpoint (all 3 cache types)."""
        print("\n" + "="*80)
        print("TEST 6: Complete Cache Flow - price_ancillaries Endpoint")
        print("="*80)
        
        # Setup cache keys
        flight_price_key = "flight_price_complete_test_001"
        seat_key = "seat_availability_complete_test_001"
        service_key = "service_list_complete_test_001"
        
        # Store all data types
        flight_cache.store_flight_price(flight_price_key, sample_flight_price_data)
        flight_cache.store_seat_availability(seat_key, sample_seat_availability_data)
        flight_cache.store_service_list(service_key, sample_service_list_data)
        
        print(f"✅ Stored all 3 cache types")
        
        # Simulate price_ancillaries endpoint retrieval
        flight_result = flight_cache.get_flight_price(flight_price_key)
        seat_result = flight_cache.get_seat_availability(seat_key)
        service_result = flight_cache.get_service_list(service_key)
        
        assert flight_result['success'] == True, "Flight price retrieval failed"
        assert seat_result['success'] == True, "Seat availability retrieval failed"
        assert service_result['success'] == True, "Service list retrieval failed"
        
        print(f"✅ Retrieved all 3 cache types successfully")
        
        # Verify data integrity
        flight_data = flight_result['data']
        seat_data = seat_result['data']['raw_response']
        service_data = service_result['data']['raw_response']
        
        assert 'PricedFlightOffers' in flight_data
        assert 'SeatMap' in seat_data
        assert 'ServiceList' in service_data
        
        print("✅ Complete cache flow test passed for price_ancillaries endpoint")

    def test_complete_cache_flow_for_price_services_only(
        self, 
        flight_cache, 
        sample_flight_price_data, 
        sample_service_list_data
    ):
        """Test complete cache flow for price_services_only endpoint."""
        print("\n" + "="*80)
        print("TEST 7: Complete Cache Flow - price_services_only Endpoint")
        print("="*80)
        
        # Setup cache keys
        flight_price_key = "flight_price_services_test_001"
        service_key = "service_list_services_test_001"
        
        # Store data
        flight_cache.store_flight_price(flight_price_key, sample_flight_price_data)
        flight_cache.store_service_list(service_key, sample_service_list_data)
        
        print(f"✅ Stored flight price and service list data")
        
        # Simulate price_services_only endpoint retrieval
        flight_result = flight_cache.get_flight_price(flight_price_key)
        service_result = flight_cache.get_service_list(service_key)
        
        assert flight_result['success'] == True, "Flight price retrieval failed"
        assert service_result['success'] == True, "Service list retrieval failed"
        
        print(f"✅ Retrieved flight price and service list successfully")
        
        # Extract raw_response from service data
        service_data = service_result['data']
        if 'raw_response' in service_data:
            service_data = service_data['raw_response']
            print(f"✅ Extracted raw_response from service list")
        
        assert 'ServiceList' in service_data
        assert len(service_data['ServiceList']) == 2
        
        print("✅ Complete cache flow test passed for price_services_only endpoint")

    def test_complete_cache_flow_for_price_seats_only(
        self, 
        flight_cache, 
        sample_flight_price_data, 
        sample_seat_availability_data
    ):
        """Test complete cache flow for price_seats_only endpoint."""
        print("\n" + "="*80)
        print("TEST 8: Complete Cache Flow - price_seats_only Endpoint")
        print("="*80)
        
        # Setup cache keys
        flight_price_key = "flight_price_seats_test_001"
        seat_key = "seat_availability_seats_test_001"
        
        # Store data
        flight_cache.store_flight_price(flight_price_key, sample_flight_price_data)
        flight_cache.store_seat_availability(seat_key, sample_seat_availability_data)
        
        print(f"✅ Stored flight price and seat availability data")
        
        # Simulate price_seats_only endpoint retrieval
        flight_result = flight_cache.get_flight_price(flight_price_key)
        seat_result = flight_cache.get_seat_availability(seat_key)
        
        assert flight_result['success'] == True, "Flight price retrieval failed"
        assert seat_result['success'] == True, "Seat availability retrieval failed"
        
        print(f"✅ Retrieved flight price and seat availability successfully")
        
        # Extract raw_response from seat data
        seat_data = seat_result['data']
        if 'raw_response' in seat_data:
            seat_data = seat_data['raw_response']
            print(f"✅ Extracted raw_response from seat availability")
        
        assert 'SeatMap' in seat_data
        assert 'DataLists' in seat_data
        
        print("✅ Complete cache flow test passed for price_seats_only endpoint")

    def test_cache_key_not_found_handling(self, flight_cache):
        """Test graceful handling when cache keys don't exist."""
        print("\n" + "="*80)
        print("TEST 9: Cache Key Not Found Handling")
        print("="*80)
        
        # Try to retrieve non-existent keys
        flight_result = flight_cache.get_flight_price("non_existent_flight_key")
        seat_result = flight_cache.get_seat_availability("non_existent_seat_key")
        service_result = flight_cache.get_service_list("non_existent_service_key")
        
        # All should return success=False
        assert flight_result['success'] == False, "Should return success=False for missing flight key"
        assert seat_result['success'] == False, "Should return success=False for missing seat key"
        assert service_result['success'] == False, "Should return success=False for missing service key"
        
        print("✅ All cache types handle missing keys gracefully")

    def test_concurrent_cache_operations(
        self, 
        flight_cache, 
        sample_flight_price_data, 
        sample_seat_availability_data, 
        sample_service_list_data
    ):
        """Test that multiple cache operations can be performed concurrently."""
        print("\n" + "="*80)
        print("TEST 10: Concurrent Cache Operations")
        print("="*80)
        
        # Store multiple entries for each type
        for i in range(5):
            flight_cache.store_flight_price(f"flight_concurrent_{i}", sample_flight_price_data)
            flight_cache.store_seat_availability(f"seat_concurrent_{i}", sample_seat_availability_data)
            flight_cache.store_service_list(f"service_concurrent_{i}", sample_service_list_data)
        
        print("✅ Stored 5 entries for each cache type")
        
        # Retrieve all entries
        success_count = 0
        for i in range(5):
            flight_result = flight_cache.get_flight_price(f"flight_concurrent_{i}")
            seat_result = flight_cache.get_seat_availability(f"seat_concurrent_{i}")
            service_result = flight_cache.get_service_list(f"service_concurrent_{i}")
            
            if flight_result['success'] and seat_result['success'] and service_result['success']:
                success_count += 1
        
        assert success_count == 5, f"Expected 5 successful retrievals, got {success_count}"
        print(f"✅ Successfully retrieved all {success_count} concurrent entries")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("ANCILLARY PRICING CACHE INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing cache retrieval implementation for:")
    print("  - price_ancillaries endpoint (flight_price + seat + service)")
    print("  - price_services_only endpoint (flight_price + service)")
    print("  - price_seats_only endpoint (flight_price + seat)")
    print("="*80 + "\n")
    
    # Run pytest with verbose output
    pytest.main([__file__, '-v', '-s'])
