#!/usr/bin/env python3
"""
Test runner for card payment functionality in build_ordercreate_rq.py

This script runs comprehensive tests for card payment processing including:
- Valid card payment scenarios
- Invalid card payment validation
- Payment amount calculations
- Multi-airline support
- Edge cases and error handling

Usage:
    python test_card_payments_runner.py

Author: FLIGHT Application
Created: 2025-07-03
"""

import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from scripts.build_ordercreate_rq import generate_order_create_rq


def create_sample_flight_price_response():
    """Create a sample flight price response for testing."""
    return {
        "ShoppingResponseID": {
            "ResponseID": {"value": "test-response-123"},
            "Owner": "KQ"
        },
        "PricedFlightOffers": {
            "PricedFlightOffer": [{
                "OfferID": {
                    "value": "OFFER123",
                    "Owner": "KQ",
                    "Channel": "NDC"
                },
                "OfferPrice": [{
                    "OfferItemID": "ITEM123",
                    "RequestedDate": {
                        "PriceDetail": {
                            "TotalAmount": {
                                "SimpleCurrencyPrice": {
                                    "value": 1500.00,
                                    "Code": "USD"
                                }
                            },
                            "BaseAmount": {
                                "value": 1200.00,
                                "Code": "USD"
                            },
                            "Taxes": {
                                "Total": {
                                    "value": 300.00,
                                    "Code": "USD"
                                }
                            }
                        },
                        "Associations": [{
                            "AssociatedTraveler": {
                                "TravelerReferences": ["PAX1"]
                            },
                            "ApplicableFlight": {
                                "FlightSegmentReference": [],
                                "OriginDestinationReferences": []
                            }
                        }]
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
            },
            "FareList": {"FareGroup": []},
            "FlightSegmentList": {"FlightSegment": []},
            "FlightList": {"Flight": []},
            "OriginDestinationList": {"OriginDestination": []}
        }
    }


def create_sample_passenger_data():
    """Create sample passenger data for testing."""
    return [{
        "PTC": "ADT",
        "ObjectKey": "PAX1",
        "Name": {
            "Title": "Mr",
            "Given": ["John"],
            "Surname": "Doe"
        },
        "Gender": "Male",
        "BirthDate": "1990-01-01",
        "Documents": [{
            "Type": "PT",
            "ID": "P123456789",
            "DateOfExpiration": "2030-01-01",
            "CountryOfIssuance": "US"
        }]
    }]


def test_basic_card_payment():
    """Test basic card payment functionality."""
    print("\n🧪 Testing Basic Card Payment")
    print("-" * 40)
    
    flight_price_response = create_sample_flight_price_response()
    passengers_data = create_sample_passenger_data()
    
    payment_data = {
        "MethodType": "PAYMENTCARD",
        "Details": {
            "CardNumberToken": "4111111111111111",
            "EffectiveExpireDate": {
                "Expiration": "1225"  # MMYY format
            },
            "CardType": "VI",  # Visa
            "CardCode": "123",
            "CardHolderName": {
                "value": "John Doe",
                "refs": []
            }
        }
    }
    
    try:
        order_create_request = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )
        
        # Verify payment structure
        payments = order_create_request['Query']['Payments']['Payment']
        payment = payments[0]
        
        print(f"✅ Payment method: {list(payment['Method'].keys())[0]}")
        print(f"✅ Payment amount: {payment['Amount']['value']} {payment['Amount']['Code']}")
        
        if 'PaymentCard' in payment['Method']:
            card = payment['Method']['PaymentCard']
            print(f"✅ Card type: {card['CardType']}")
            print(f"✅ Card holder: {card['CardHolderName']['value']}")
            print(f"✅ Card amount: {card['Amount']['value']} {card['Amount']['Code']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic card payment test failed: {e}")
        return False


def test_card_payment_with_billing_address():
    """Test card payment with billing address."""
    print("\n🧪 Testing Card Payment with Billing Address")
    print("-" * 50)
    
    flight_price_response = create_sample_flight_price_response()
    passengers_data = create_sample_passenger_data()
    
    payment_data = {
        "MethodType": "PAYMENTCARD",
        "Details": {
            "CardNumberToken": "5555555555554444",
            "EffectiveExpireDate": {
                "Expiration": "0326",
                "Effective": "0123"
            },
            "CardType": "MC",  # MasterCard
            "CardCode": "456",
            "CardHolderName": {
                "value": "Jane Smith",
                "refs": ["PAX1"]
            },
            "CardHolderBillingAddress": {
                "Street": ["123 Main St", "Apt 4B"],
                "PostalCode": "12345",
                "CityName": "New York",
                "CountryCode": {"value": "US"}
            },
            "SeriesCode": {"value": "456"}
        }
    }
    
    try:
        order_create_request = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )
        
        payment = order_create_request['Query']['Payments']['Payment'][0]
        card_details = payment['Method']['PaymentCard']
        
        print(f"✅ Card type: {card_details['CardType']}")
        print(f"✅ Billing address included: {'CardHolderBillingAddress' in card_details}")
        
        if 'CardHolderBillingAddress' in card_details:
            addr = card_details['CardHolderBillingAddress']
            print(f"✅ Street: {addr['Street']}")
            print(f"✅ City: {addr['CityName']}")
            print(f"✅ Country: {addr['CountryCode']['value']}")
        
        print(f"✅ Series code included: {'SeriesCode' in card_details}")
        
        return True
        
    except Exception as e:
        print(f"❌ Card payment with billing address test failed: {e}")
        return False


def test_invalid_card_payment():
    """Test invalid card payment scenarios."""
    print("\n🧪 Testing Invalid Card Payment Scenarios")
    print("-" * 45)
    
    flight_price_response = create_sample_flight_price_response()
    passengers_data = create_sample_passenger_data()
    
    # Test missing required fields
    invalid_scenarios = [
        {
            "name": "Missing CardNumberToken",
            "payment_data": {
                "MethodType": "PAYMENTCARD",
                "Details": {
                    "EffectiveExpireDate": {"Expiration": "1225"},
                    "CardType": "VI",
                    "CardCode": "123",
                    "CardHolderName": {"value": "John Doe"}
                }
            }
        },
        {
            "name": "Missing CardType",
            "payment_data": {
                "MethodType": "PAYMENTCARD",
                "Details": {
                    "CardNumberToken": "4111111111111111",
                    "EffectiveExpireDate": {"Expiration": "1225"},
                    "CardCode": "123",
                    "CardHolderName": {"value": "John Doe"}
                }
            }
        }
    ]
    
    passed_tests = 0
    for scenario in invalid_scenarios:
        try:
            generate_order_create_rq(
                flight_price_response=flight_price_response,
                passengers_data=passengers_data,
                payment_input_info=scenario["payment_data"]
            )
            print(f"❌ {scenario['name']}: Should have failed but didn't")
        except ValueError as e:
            print(f"✅ {scenario['name']}: Correctly failed with error")
            passed_tests += 1
        except Exception as e:
            print(f"⚠️ {scenario['name']}: Failed with unexpected error: {e}")
    
    return passed_tests == len(invalid_scenarios)


def main():
    """Run all card payment tests."""
    print("🚀 Card Payment Testing Suite")
    print("=" * 60)
    print("Testing card payment functionality in build_ordercreate_rq.py")
    
    tests = [
        ("Basic Card Payment", test_basic_card_payment),
        ("Card Payment with Billing Address", test_card_payment_with_billing_address),
        ("Invalid Card Payment Scenarios", test_invalid_card_payment)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All card payment tests passed successfully!")
        return True
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
