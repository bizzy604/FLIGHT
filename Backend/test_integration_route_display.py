#!/usr/bin/env python3
"""
Integration test for route display functionality.

This script tests the complete flow from search parameters to flight card generation
to ensure the route display works correctly in the full system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers.enhanced_air_shopping_transformer import transform_air_shopping_for_results_enhanced
from utils.air_shopping_transformer import transform_air_shopping_for_results

def create_mock_air_shopping_response():
    """Create a mock air shopping response for testing."""
    return {
        "OffersGroup": {
            "AirlineOffers": [
                {
                    "AirlineOffer": [
                        {
                            "OfferID": {
                                "Owner": "KL",
                                "value": "OFFER_KL_001"
                            },
                            "PricedOffer": {
                                "OfferPrice": [
                                    {
                                        "RequestedDate": {
                                            "PriceDetail": {
                                                "TotalAmount": {
                                                    "SimpleCurrencyPrice": {
                                                        "value": 850.00,
                                                        "Code": "USD"
                                                    }
                                                }
                                            },
                                            "Associations": [
                                                {
                                                    "ApplicableFlight": {
                                                        "FlightSegmentReference": [
                                                            {"ref": "SEG_1"},
                                                            {"ref": "SEG_2"}
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "SEG_1",
                        "Departure": {
                            "AirportCode": {"value": "NBO"},
                            "Date": "2025-07-15T10:30:00Z",
                            "Time": "10:30"
                        },
                        "Arrival": {
                            "AirportCode": {"value": "AMS"},
                            "Date": "2025-07-15T16:45:00Z",
                            "Time": "16:45"
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "KL"},
                            "FlightNumber": {"value": "566"},
                            "Name": "KLM Royal Dutch Airlines"
                        },
                        "FlightDetail": {
                            "FlightDuration": {"value": "PT8H15M"}
                        }
                    },
                    {
                        "SegmentKey": "SEG_2",
                        "Departure": {
                            "AirportCode": {"value": "AMS"},
                            "Date": "2025-07-15T18:20:00Z",
                            "Time": "18:20"
                        },
                        "Arrival": {
                            "AirportCode": {"value": "DXB"},
                            "Date": "2025-07-16T05:35:00Z",
                            "Time": "05:35"
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "KL"},
                            "FlightNumber": {"value": "443"},
                            "Name": "KLM Royal Dutch Airlines"
                        },
                        "FlightDetail": {
                            "FlightDuration": {"value": "PT6H15M"}
                        }
                    }
                ]
            }
        }
    }

def test_enhanced_transformer_integration():
    """Test the enhanced transformer with route display."""
    
    print("🧪 Testing Enhanced Transformer Integration")
    print("=" * 60)
    
    # Create mock response
    mock_response = create_mock_air_shopping_response()
    
    # Create search context (user searched NBO -> DXB)
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
    
    print(f"🔍 User Search: {search_context['odSegments'][0]['origin']} → {search_context['odSegments'][0]['destination']}")
    print(f"✈️  Actual Flight: NBO → AMS → DXB")
    
    # Transform using enhanced transformer
    result = transform_air_shopping_for_results_enhanced(
        mock_response, 
        filter_unsupported_airlines=False,
        search_context=search_context
    )
    
    # Verify the result
    offers = result.get('offers', [])
    assert len(offers) > 0, "Expected at least one offer"
    
    first_offer = offers[0]
    route_display = first_offer.get('route_display')
    
    print(f"\n📊 Results:")
    print(f"   Number of offers: {len(offers)}")
    print(f"   Route display present: {route_display is not None}")
    
    if route_display:
        print(f"   Display Origin: {route_display['origin']}")
        print(f"   Display Destination: {route_display['destination']}")
        print(f"   Actual Route: {' → '.join(route_display['actual_route'])}")
        print(f"   Stops: {route_display['stops']}")
        print(f"   Is Direct: {route_display['is_direct']}")
        
        # Verify correct route display
        assert route_display['origin'] == 'NBO', f"Expected origin 'NBO', got '{route_display['origin']}'"
        assert route_display['destination'] == 'DXB', f"Expected destination 'DXB', got '{route_display['destination']}'"
        assert 'AMS' in route_display['stops'], f"Expected 'AMS' in stops, got {route_display['stops']}"
        assert not route_display['is_direct'], "Expected non-direct flight"
        
        print(f"   ✅ Route display is correct!")
    else:
        print(f"   ❌ Route display missing!")
        return False
    
    return True

def test_basic_transformer_integration():
    """Test the basic transformer with route display."""
    
    print("\n🧪 Testing Basic Transformer Integration")
    print("=" * 60)
    
    # Create mock response
    mock_response = create_mock_air_shopping_response()
    
    # Create search context
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
    
    print(f"🔍 User Search: {search_context['odSegments'][0]['origin']} → {search_context['odSegments'][0]['destination']}")
    print(f"✈️  Actual Flight: NBO → AMS → DXB")
    
    # Transform using basic transformer
    result = transform_air_shopping_for_results(mock_response, search_context)
    
    # Verify the result
    offers = result.get('offers', [])
    assert len(offers) > 0, "Expected at least one offer"
    
    first_offer = offers[0]
    route_display = first_offer.get('route_display')
    
    print(f"\n📊 Results:")
    print(f"   Number of offers: {len(offers)}")
    print(f"   Route display present: {route_display is not None}")
    
    if route_display:
        print(f"   Display Origin: {route_display['origin']}")
        print(f"   Display Destination: {route_display['destination']}")
        print(f"   Actual Route: {' → '.join(route_display['actual_route'])}")
        print(f"   Stops: {route_display['stops']}")
        print(f"   Is Direct: {route_display['is_direct']}")
        
        # Verify correct route display
        assert route_display['origin'] == 'NBO', f"Expected origin 'NBO', got '{route_display['origin']}'"
        assert route_display['destination'] == 'DXB', f"Expected destination 'DXB', got '{route_display['destination']}'"
        assert 'AMS' in route_display['stops'], f"Expected 'AMS' in stops, got {route_display['stops']}"
        assert not route_display['is_direct'], "Expected non-direct flight"
        
        print(f"   ✅ Route display is correct!")
    else:
        print(f"   ❌ Route display missing!")
        return False
    
    return True

def main():
    """Run all integration tests."""
    
    print("🚀 Starting Route Display Integration Tests")
    print("=" * 70)
    
    try:
        # Test enhanced transformer
        enhanced_success = test_enhanced_transformer_integration()
        
        # Test basic transformer
        basic_success = test_basic_transformer_integration()
        
        if enhanced_success and basic_success:
            print("\n🎉 All Integration Tests PASSED!")
            print("\n✅ Key Achievements:")
            print("   • Backend transformers correctly include route display information")
            print("   • User search parameters take priority over flight segment routing")
            print("   • Intermediate stops are properly identified and displayed")
            print("   • Both enhanced and basic transformers work correctly")
            print("   • The solution fixes the NBO-AMS vs NBO-DXB display issue")
            
            print("\n🔧 Next Steps:")
            print("   • Frontend will now display 'NBO → DXB (via AMS)' instead of 'NBO → AMS'")
            print("   • Users will see their intended route clearly")
            print("   • Stop information is informative and accurate")
            
            return True
        else:
            print("\n❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
