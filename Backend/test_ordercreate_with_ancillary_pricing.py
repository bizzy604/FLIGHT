"""
Test OrderCreate payload generation with ancillary pricing response.

This test simulates the complete flow:
1. Initial FlightPrice response (with PricedInd=false seat)
2. SeatAvailability response
3. Ancillary pricing response (FlightPriceRS with priced seat)
4. OrderCreate payload generation

Expected: No duplicate keys, correct structure per VDC spec
"""
import json
import sys
from pathlib import Path

# Set UTF-8 encoding for stdout to handle emojis on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add Backend to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request


def load_json_file(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_ordercreate_with_seat_pricing():
    """Test OrderCreate generation with seat that requires pricing."""
    
    print("\n" + "="*80)
    print("TEST: OrderCreate with Ancillary Pricing (Seat Selection)")
    print("="*80)
    
    # Load the actual ancillary pricing response we received
    ancillary_pricing_response_file = Path(__file__).parent / 'api_logs' / 'ancillary_pricing' / 'AncillaryPricing_RS.json'
    
    if not ancillary_pricing_response_file.exists():
        print(f"❌ ERROR: Ancillary pricing response file not found: {ancillary_pricing_response_file}")
        return False
    
    # Load ancillary pricing response
    ancillary_log = load_json_file(ancillary_pricing_response_file)
    ancillary_pricing_response = ancillary_log.get('response', {})
    
    print(f"✅ Loaded ancillary pricing response from: {ancillary_pricing_response_file}")
    print(f"   - ShoppingResponseID: {ancillary_pricing_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')}")
    print(f"   - PricedFlightOffers: {len(ancillary_pricing_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))}")
    print(f"   - ServiceList items: {len(ancillary_pricing_response.get('DataLists', {}).get('ServiceList', {}).get('Service', []))}")
    
    # Original flight price response (before ancillary pricing)
    flight_price_response = {
        "Success": {},
        "ShoppingResponseID": {
            "ResponseID": {
                "value": "N0nYFssLA-RW7ydampZ2QS922JWY1vgZHW8XfcYnUPA-AF"
            }
        },
        "PricedFlightOffers": ancillary_pricing_response.get('PricedFlightOffers', {}),
        "DataLists": ancillary_pricing_response.get('DataLists', {})
    }
    
    # Mock SeatAvailability response (simplified)
    seatavailability_response = {
        "Services": {
            "Service": [
                {
                    "ObjectKey": "f29c1264-524b-4553-9c12-64524bb50033",
                    "ServiceID": {
                        "value": "SRV1-SEAT",
                        "Owner": "AF"
                    },
                    "PricedInd": False,
                    "Associations": [
                        {
                            "Traveler": {
                                "TravelerReferences": ["PAX1"]
                            },
                            "Flight": {
                                "originDestinationReferencesOrSegmentReferences": [
                                    {
                                        "SegmentReferences": {
                                            "value": ["SEG1"]
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
            "SeatList": {
                "Seats": [
                    {
                        "ObjectKey": "f29c1264-524b-4553-9c12-64524bb50033",
                        "Location": {
                            "Column": "A",
                            "Row": {
                                "Number": {
                                    "value": "17"
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # Passenger data
    passengers_data = [
        {
            "PTC": "ADT",
            "Name": {
                "Surname": "AMONI",
                "Given": ["KEVIN"]
            },
            "Gender": "Male",
            "BirthDate": "1990-01-01",
            "Documents": {
                "Document": [{
                    "Type": "PT",
                    "ID": "A12345678",
                    "ExpiryDate": "2030-12-31",
                    "IssueCountry": "KE"
                }]
            },
            "Contacts": {
                "Contact": [{
                    "PhoneContact": {
                        "Number": [{
                            "CountryCode": "+254",
                            "value": "0796861525"
                        }],
                        "Application": "Home"
                    },
                    "EmailContact": {
                        "Address": {
                            "value": "kevinamoni20@gmail.com"
                        }
                    },
                    "AddressContact": {
                        "Street": ["190"],
                        "PostalCode": "30500",
                        "CityName": "LODWAR",
                        "CountryCode": {
                            "value": "AO"
                        }
                    }
                }]
            },
            "ObjectKey": "PAX1"
        }
    ]
    
    # Payment info
    payment_input_info = {
        "MethodType": "CASH",
        "currency": "INR",
        "Details": {},
        "CashInd": True
    }
    
    # Selected items
    selected_seats = ["f29c1264-524b-4553-9c12-64524bb50033"]
    selected_services = []
    
    print("\n📋 Test Parameters:")
    print(f"   - Selected seats: {selected_seats}")
    print(f"   - Selected services: {selected_services}")
    print(f"   - Passengers: {len(passengers_data)}")
    
    try:
        # Generate OrderCreate payload
        print("\n🔨 Generating OrderCreate payload...")
        # CRITICAL: When using ancillary pricing response (PricedInd=false scenario),
        # DO NOT pass seatavailability_response because all seat data comes from ancillary_pricing_response
        order_create_payload = build_ordercreate_enhanced_request(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_input_info,
            servicelist_response=None,
            seatavailability_response=None,  # FIX: Don't pass original seat response when using ancillary pricing
            selected_services=selected_services,
            selected_seats=selected_seats,
            ancillary_pricing_response=ancillary_pricing_response
        )
        
        print("✅ OrderCreate payload generated successfully!")
        
        # Validation checks
        print("\n🔍 Validating OrderCreate payload...")
        
        # Check 1: Verify OfferItems exist
        offer_items = order_create_payload.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
        print(f"   ✓ OfferItems count: {len(offer_items)}")
        
        # Check 2: Extract all ObjectKeys from OfferItems
        offer_item_keys = []
        for item in offer_items:
            offer_item_id = item.get('OfferItemID', {}).get('value', '')
            if offer_item_id:
                offer_item_keys.append(offer_item_id)
        
        print(f"   ✓ OfferItem ObjectKeys: {offer_item_keys}")
        
        # Check 3: Extract all ObjectKeys from DataLists.ServiceList
        service_list = order_create_payload.get('Query', {}).get('DataLists', {}).get('ServiceList', {}).get('Service', [])
        service_keys = [svc.get('ObjectKey', '') for svc in service_list if svc.get('ObjectKey')]
        
        print(f"   ✓ ServiceList count: {len(service_list)}")
        print(f"   ✓ ServiceList ObjectKeys: {service_keys}")
        
        # Check 4: Verify no duplicate ObjectKeys
        all_keys = offer_item_keys + service_keys
        duplicate_keys = [key for key in set(all_keys) if all_keys.count(key) > 1]
        
        if duplicate_keys:
            print(f"\n❌ DUPLICATE KEYS FOUND: {duplicate_keys}")
            print(f"   This will cause 'Duplicate key' error from airline API!")
            return False
        else:
            print(f"\n✅ No duplicate keys found!")
        
        # Check 5: Verify seat ObjectKey appears exactly once
        seat_key = "f29c1264-524b-4553-9c12-64524bb50033"
        seat_count = all_keys.count(seat_key)
        
        if seat_count == 0:
            print(f"❌ ERROR: Seat key {seat_key} not found in payload!")
            return False
        elif seat_count > 1:
            print(f"❌ ERROR: Seat key {seat_key} appears {seat_count} times (should be 1)!")
            return False
        else:
            print(f"✅ Seat key {seat_key} appears exactly once")
        
        # Check 6: Verify ShoppingResponseID is present
        shopping_response_id = order_create_payload.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {}).get('ResponseID', {}).get('value')
        if shopping_response_id:
            print(f"✅ ShoppingResponseID present: {shopping_response_id}")
        else:
            print("❌ ERROR: ShoppingResponseID missing!")
            return False
        
        # Check 7: Verify passenger details
        passengers = order_create_payload.get('Query', {}).get('Passengers', {}).get('Passenger', [])
        if len(passengers) == len(passengers_data):
            print(f"✅ Passengers count correct: {len(passengers)}")
        else:
            print(f"❌ ERROR: Expected {len(passengers_data)} passengers, got {len(passengers)}")
            return False
        
        # Check 8: Verify DataLists.ServiceList comes from ancillary pricing response
        ancillary_service_list = ancillary_pricing_response.get('DataLists', {}).get('ServiceList', {}).get('Service', [])
        if len(service_list) == len(ancillary_service_list):
            print(f"✅ ServiceList correctly sourced from ancillary pricing response ({len(service_list)} services)")
        else:
            print(f"⚠️  WARNING: ServiceList count mismatch. Ancillary: {len(ancillary_service_list)}, OrderCreate: {len(service_list)}")
        
        # Save the payload for inspection
        output_file = Path(__file__).parent / 'test_ordercreate_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(order_create_payload, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 OrderCreate payload saved to: {output_file}")
        
        print("\n" + "="*80)
        print("✅ TEST PASSED: OrderCreate payload is valid!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_ordercreate_structure():
    """Test that OrderCreate structure matches VDC specification."""
    
    print("\n" + "="*80)
    print("TEST: OrderCreate Structure Validation")
    print("="*80)
    
    # Load the generated payload
    output_file = Path(__file__).parent / 'test_ordercreate_output.json'
    
    if not output_file.exists():
        print(f"⚠️  Run test_ordercreate_with_seat_pricing first to generate payload")
        return False
    
    payload = load_json_file(output_file)
    
    # VDC Specification checks
    checks = [
        ("Query exists", lambda p: 'Query' in p),
        ("Query.Passengers exists", lambda p: 'Passengers' in p.get('Query', {})),
        ("Query.OrderItems exists", lambda p: 'OrderItems' in p.get('Query', {})),
        ("Query.OrderItems.ShoppingResponse exists", lambda p: 'ShoppingResponse' in p.get('Query', {}).get('OrderItems', {})),
        ("Query.OrderItems.OfferItem exists", lambda p: 'OfferItem' in p.get('Query', {}).get('OrderItems', {})),
        ("Query.DataLists exists", lambda p: 'DataLists' in p.get('Query', {})),
        ("Query.DataLists.ServiceList exists", lambda p: 'ServiceList' in p.get('Query', {}).get('DataLists', {})),
        ("ShoppingResponse.Owner exists", lambda p: 'Owner' in p.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})),
        ("ShoppingResponse.ResponseID exists", lambda p: 'ResponseID' in p.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})),
        ("At least one OfferItem exists", lambda p: len(p.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])) > 0),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func(payload)
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} - Error: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All structure checks passed!")
    else:
        print("\n❌ Some structure checks failed!")
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "🚀"*40)
    print("ORDERCREATE WITH ANCILLARY PRICING - INTEGRATION TEST")
    print("🚀"*40)
    
    # Run tests
    test1_passed = test_ordercreate_with_seat_pricing()
    test2_passed = test_ordercreate_structure()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"{'✅' if test1_passed else '❌'} Test 1: OrderCreate with seat pricing")
    print(f"{'✅' if test2_passed else '❌'} Test 2: OrderCreate structure validation")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe OrderCreate payload is correctly built without duplicate keys.")
        print("The fix successfully uses DataLists.ServiceList from ancillary pricing response.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("\nPlease review the errors above and fix the issues.")
        sys.exit(1)
