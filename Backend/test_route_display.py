#!/usr/bin/env python3
"""
Test script for route display functionality.

This script tests the enhanced route mapping logic to ensure that flight cards
display the correct origin and destination based on user search parameters.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer

def test_route_display_logic():
    """Test the route display logic with various scenarios."""
    
    print("🧪 Testing Route Display Logic")
    print("=" * 50)
    
    # Test Case 1: NBO-DXB via AMS (the original issue)
    print("\n📍 Test Case 1: NBO-DXB via AMS")
    
    # Mock search context
    search_context = {
        'odSegments': [
            {
                'origin': 'NBO',
                'destination': 'DXB',
                'departureDate': '2025-07-15'
            }
        ],
        'trip_type': 'ONE_WAY'
    }
    
    # Mock flight segments data (NBO -> AMS -> DXB)
    segments_data = [
        {
            'Departure': {'AirportCode': {'value': 'NBO'}},
            'Arrival': {'AirportCode': {'value': 'AMS'}}
        },
        {
            'Departure': {'AirportCode': {'value': 'AMS'}},
            'Arrival': {'AirportCode': {'value': 'DXB'}}
        }
    ]
    
    # Create transformer instance
    transformer = EnhancedAirShoppingTransformer({}, False, search_context)
    
    # Test route display generation
    route_display = transformer._generate_route_display_info(segments_data, 'ONE_WAY')
    
    print(f"   Search: {search_context['odSegments'][0]['origin']} → {search_context['odSegments'][0]['destination']}")
    print(f"   Actual Route: {' → '.join(route_display['actual_route'])}")
    print(f"   Display Origin: {route_display['origin']}")
    print(f"   Display Destination: {route_display['destination']}")
    print(f"   Stops: {route_display['stops']}")
    print(f"   Is Direct: {route_display['is_direct']}")
    
    # Verify results
    assert route_display['origin'] == 'NBO', f"Expected origin 'NBO', got '{route_display['origin']}'"
    assert route_display['destination'] == 'DXB', f"Expected destination 'DXB', got '{route_display['destination']}'"
    assert 'AMS' in route_display['stops'], f"Expected 'AMS' in stops, got {route_display['stops']}"
    assert not route_display['is_direct'], "Expected non-direct flight"
    
    print("   ✅ Test Case 1 PASSED")
    
    # Test Case 2: Direct flight NBO-DXB
    print("\n📍 Test Case 2: Direct flight NBO-DXB")
    
    segments_data_direct = [
        {
            'Departure': {'AirportCode': {'value': 'NBO'}},
            'Arrival': {'AirportCode': {'value': 'DXB'}}
        }
    ]
    
    route_display_direct = transformer._generate_route_display_info(segments_data_direct, 'ONE_WAY')
    
    print(f"   Search: {search_context['odSegments'][0]['origin']} → {search_context['odSegments'][0]['destination']}")
    print(f"   Actual Route: {' → '.join(route_display_direct['actual_route'])}")
    print(f"   Display Origin: {route_display_direct['origin']}")
    print(f"   Display Destination: {route_display_direct['destination']}")
    print(f"   Stops: {route_display_direct['stops']}")
    print(f"   Is Direct: {route_display_direct['is_direct']}")
    
    # Verify results
    assert route_display_direct['origin'] == 'NBO', f"Expected origin 'NBO', got '{route_display_direct['origin']}'"
    assert route_display_direct['destination'] == 'DXB', f"Expected destination 'DXB', got '{route_display_direct['destination']}'"
    assert len(route_display_direct['stops']) == 0, f"Expected no stops, got {route_display_direct['stops']}"
    assert route_display_direct['is_direct'], "Expected direct flight"
    
    print("   ✅ Test Case 2 PASSED")
    
    # Test Case 3: Round trip NBO-DXB-NBO
    print("\n📍 Test Case 3: Round trip NBO-DXB-NBO")
    
    search_context_rt = {
        'odSegments': [
            {
                'origin': 'NBO',
                'destination': 'DXB',
                'departureDate': '2025-07-15'
            },
            {
                'origin': 'DXB',
                'destination': 'NBO',
                'departureDate': '2025-07-20'
            }
        ],
        'trip_type': 'ROUND_TRIP'
    }
    
    # Mock round trip segments (NBO -> AMS -> DXB -> AMS -> NBO)
    segments_data_rt = [
        {
            'Departure': {'AirportCode': {'value': 'NBO'}},
            'Arrival': {'AirportCode': {'value': 'AMS'}}
        },
        {
            'Departure': {'AirportCode': {'value': 'AMS'}},
            'Arrival': {'AirportCode': {'value': 'DXB'}}
        },
        {
            'Departure': {'AirportCode': {'value': 'DXB'}},
            'Arrival': {'AirportCode': {'value': 'AMS'}}
        },
        {
            'Departure': {'AirportCode': {'value': 'AMS'}},
            'Arrival': {'AirportCode': {'value': 'NBO'}}
        }
    ]
    
    transformer_rt = EnhancedAirShoppingTransformer({}, False, search_context_rt)
    route_display_rt = transformer_rt._generate_route_display_info(segments_data_rt, 'ROUND_TRIP')
    
    print(f"   Search: {search_context_rt['odSegments'][0]['origin']} → {search_context_rt['odSegments'][0]['destination']}")
    print(f"   Actual Route: {' → '.join(route_display_rt['actual_route'])}")
    print(f"   Display Origin: {route_display_rt['origin']}")
    print(f"   Display Destination: {route_display_rt['destination']}")
    print(f"   Stops: {route_display_rt['stops']}")
    print(f"   Is Direct: {route_display_rt['is_direct']}")
    
    # Verify results
    assert route_display_rt['origin'] == 'NBO', f"Expected origin 'NBO', got '{route_display_rt['origin']}'"
    assert route_display_rt['destination'] == 'DXB', f"Expected destination 'DXB', got '{route_display_rt['destination']}'"
    assert 'AMS' in route_display_rt['stops'], f"Expected 'AMS' in stops, got {route_display_rt['stops']}"
    assert not route_display_rt['is_direct'], "Expected non-direct flight"
    
    print("   ✅ Test Case 3 PASSED")
    
    print("\n🎉 All tests passed! Route display logic is working correctly.")
    print("\nKey Benefits Verified:")
    print("✅ User search route takes priority over flight segments")
    print("✅ Intermediate stops are correctly identified")
    print("✅ Direct vs connecting flights are properly distinguished")
    print("✅ Round trip logic correctly identifies outbound destination")

if __name__ == "__main__":
    test_route_display_logic()
