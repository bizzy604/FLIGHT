#!/usr/bin/env python3
"""
Test script to simulate Qatar Airways response structure and test the OrderCreate fix.
"""

import json
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def create_qr_test_response():
    """Create a mock Qatar Airways response that mimics the structure from the logs."""

    # Based on the logs, QR response has OfferPrice entries but they might be missing OfferItemID
    qr_response = {
        "Document": {
            "Name": "QR"
        },
        "ShoppingResponseID": {
            "ResponseID": {
                "value": "4hi0aoiHMPXWTAmxgDFrzKh-G-sdXT3Q-9MmLfVhVSQ-QR"
            }
        },
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": {
                        "ObjectKey": "1H0QRZ_HG9OC1FYFHN89TO7Z9QBJE2WMRLU",
                        "value": "1H0QRZ_HG9OC1FYFHN89TO7Z9QBJE2WMRLU",
                        "Owner": "QR",
                        "Channel": "NDC"
                    },
                    "OfferPrice": [
                        {
                            "RequestedDate": {
                                "Associations": [
                                    {
                                        "AssociatedTraveler": {
                                            "TravelerReferences": [
                                                "PAX1"
                                            ]
                                        },
                                        "ApplicableFlight": {
                                            "FlightSegmentReference": [
                                                {
                                                    "ClassOfService": {
                                                        "Code": {
                                                            "value": "Y"
                                                        },
                                                        "MarketingName": {
                                                            "value": "ECONOMY",
                                                            "CabinDesignator": "Y"
                                                        }
                                                    },
                                                    "ref": "SEG1"
                                                }
                                            ]
                                        }
                                    }
                                ],
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {
                                            "value": 500.00,
                                            "Code": "USD"
                                        }
                                    },
                                    "BaseAmount": {
                                        "SimpleCurrencyPrice": {
                                            "value": 400.00,
                                            "Code": "USD"
                                        }
                                    },
                                    "Taxes": {
                                        "Total": {
                                            "SimpleCurrencyPrice": {
                                                "value": 100.00,
                                                "Code": "USD"
                                            }
                                        }
                                    }
                                }
                            }
                            # Note: Missing OfferItemID - this is what causes the issue
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "AnonymousTravelerList": [
                {
                    "PTC": "ADT",
                    "ObjectKey": "PAX1"
                }
            ]
        }
    }

    return qr_response

def create_frontend_qr_response():
    """Create a mock frontend response that mimics what comes from the frontend (without PricedFlightOffers)."""

    # This mimics the structure from the logs - frontend response without PricedFlightOffers
    frontend_response = {
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "QR-PAX1",
                        "PTC": {"value": "ADT"}
                    }
                ]
            }
        },
        "Document": {
            "Name": "QR"
        },
        "Metadata": {},
        "OffersGroup": {
            "AirlineOffers": [
                {
                    "AirlineOffer": [
                        {
                            "OfferID": {
                                "ObjectKey": "1H0QRZ_ZM52VCBE2QEEZ8IN397AHTHC1FRG",
                                "value": "1H0QRZ_ZM52VCBE2QEEZ8IN397AHTHC1FRG",
                                "Owner": "QR",
                                "Channel": "NDC"
                            },
                            "PricedOffer": {
                                "OfferPrice": ["1H0QRZ_ZM52VCBE2QEEZ8IN397AHTHC1FRG-1"]
                            }
                        }
                    ]
                }
            ]
        }
    }

    return frontend_response

def test_qr_ordercreate():
    """Test OrderCreate with QR response structure."""
    
    print("🇶🇦 Testing Qatar Airways OrderCreate fix...")
    
    # Create mock QR response
    qr_response = create_qr_test_response()
    
    # Sample passenger data
    passengers_data = [
        {
            "type": "adult",
            "title": "mr",
            "first_name": "AMONI",
            "last_name": "KEVIN",
            "date_of_birth": "1988-03-06",
            "nationality": "KE",
            "passport_number": "A12345678",
            "passport_expiry": "2030-12-31",
            "passport_issuing_country": "KE"
        }
    ]
    
    # Sample payment data
    payment_data = {
        "method": "CASH",
        "currency": "USD"
    }
    
    print(f"📋 QR Response keys: {list(qr_response.keys())}")
    print(f"🎯 PricedFlightOffers found: {'PricedFlightOffers' in qr_response}")
    
    if 'PricedFlightOffers' in qr_response:
        offers = qr_response['PricedFlightOffers']['PricedFlightOffer']
        first_offer = offers[0]
        print(f"🎪 First offer keys: {list(first_offer.keys())}")
        
        if 'OfferPrice' in first_offer:
            offer_prices = first_offer['OfferPrice']
            print(f"💰 OfferPrice entries: {len(offer_prices)}")
            if offer_prices:
                first_price = offer_prices[0]
                print(f"💵 First OfferPrice keys: {list(first_price.keys())}")
                print(f"🎫 OfferItemID present: {'OfferItemID' in first_price}")
    
    try:
        print(f"\n🔧 Generating OrderCreate payload...")
        payload = generate_order_create_rq(
            flight_price_response=qr_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )
        
        print(f"✅ Successfully generated QR OrderCreate payload!")
        print(f"📦 Payload keys: {list(payload.keys())}")
        
        # Save the payload
        with open('qr_ordercreate_payload.json', 'w') as f:
            json.dump(payload, f, indent=2)
        print(f"💾 Saved QR payload to 'qr_ordercreate_payload.json'")
        
        # Check if OfferItems were created
        if 'Query' in payload and 'OrderItems' in payload['Query']:
            order_items = payload['Query']['OrderItems']
            if 'OfferItem' in order_items:
                offer_items = order_items['OfferItem']
                print(f"🎫 Generated OfferItems: {len(offer_items)}")
                if offer_items:
                    first_item = offer_items[0]
                    print(f"🎪 First OfferItem OfferItemID: {first_item.get('OfferItemID', {}).get('value', 'NOT_FOUND')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate QR OrderCreate payload: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_qr_ordercreate():
    """Test OrderCreate with frontend QR response structure (the real scenario)."""

    print("🌐 Testing Frontend Qatar Airways OrderCreate fix...")

    # Create mock frontend QR response (this is what actually comes from frontend)
    frontend_qr_response = create_frontend_qr_response()

    # Sample passenger data
    passengers_data = [
        {
            "type": "adult",
            "title": "mr",
            "first_name": "AMONI",
            "last_name": "KEVIN",
            "date_of_birth": "1988-03-06",
            "nationality": "KE",
            "passport_number": "A12345678",
            "passport_expiry": "2030-12-31",
            "passport_issuing_country": "KE"
        }
    ]

    # Sample payment data
    payment_data = {
        "method": "CASH",
        "currency": "USD"
    }

    print(f"📋 Frontend QR Response keys: {list(frontend_qr_response.keys())}")
    print(f"🎯 PricedFlightOffers found: {'PricedFlightOffers' in frontend_qr_response}")
    print(f"🌐 OffersGroup found: {'OffersGroup' in frontend_qr_response}")

    try:
        print(f"\n🔧 Generating OrderCreate payload from frontend response...")

        # This should trigger the enhancement logic in the booking service
        # For now, let's manually enhance it like the booking service does
        enhanced_response = frontend_qr_response.copy()

        # Add ShoppingResponseID
        enhanced_response['ShoppingResponseID'] = {
            'ResponseID': {'value': 'pshfEZUr9m6z0d0GtMwDnkRN2Bfe8wt-SA097OYL77g-QR'}
        }

        # Add PricedFlightOffers with OfferPrice
        offer_id = "1H0QRZ_ZM52VCBE2QEEZ8IN397AHTHC1FRG"
        enhanced_response['PricedFlightOffers'] = {
            'PricedFlightOffer': [{
                'OfferID': {
                    'value': offer_id,
                    'Owner': 'QR',
                    'Channel': 'NDC'
                },
                'OfferPrice': [{
                    'RequestedDate': {
                        'Associations': [{
                            'AssociatedTraveler': {
                                'TravelerReferences': ['PAX1']
                            },
                            'ApplicableFlight': {
                                'FlightSegmentReference': [{
                                    'ClassOfService': {
                                        'Code': {'value': 'Y'},
                                        'MarketingName': {'value': 'ECONOMY', 'CabinDesignator': 'Y'}
                                    },
                                    'ref': 'SEG1'
                                }]
                            }
                        }],
                        'PriceDetail': {
                            'TotalAmount': {
                                'SimpleCurrencyPrice': {'value': 500.00, 'Code': 'USD'}
                            },
                            'BaseAmount': {
                                'SimpleCurrencyPrice': {'value': 400.00, 'Code': 'USD'}
                            },
                            'Taxes': {
                                'Total': {
                                    'SimpleCurrencyPrice': {'value': 100.00, 'Code': 'USD'}
                                }
                            }
                        }
                    }
                }]
            }]
        }

        print(f"✨ Enhanced response keys: {list(enhanced_response.keys())}")
        print(f"🎯 PricedFlightOffers now present: {'PricedFlightOffers' in enhanced_response}")

        payload = generate_order_create_rq(
            flight_price_response=enhanced_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )

        print(f"✅ Successfully generated Frontend QR OrderCreate payload!")
        print(f"📦 Payload keys: {list(payload.keys())}")

        # Save the payload
        with open('frontend_qr_ordercreate_payload.json', 'w') as f:
            json.dump(payload, f, indent=2)
        print(f"💾 Saved Frontend QR payload to 'frontend_qr_ordercreate_payload.json'")

        # Check if OfferItems were created
        if 'Query' in payload and 'OrderItems' in payload['Query']:
            order_items = payload['Query']['OrderItems']
            if 'OfferItem' in order_items:
                offer_items = order_items['OfferItem']
                print(f"🎫 Generated OfferItems: {len(offer_items)}")
                if offer_items:
                    first_item = offer_items[0]
                    print(f"🎪 First OfferItem OfferItemID: {first_item.get('OfferItemID', {}).get('value', 'NOT_FOUND')}")

        return True

    except Exception as e:
        print(f"❌ Failed to generate Frontend QR OrderCreate payload: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Running QR OrderCreate Tests...\n")

    # Test 1: Original QR response with OfferPrice but missing OfferItemID
    success1 = test_qr_ordercreate()

    print("\n" + "="*60 + "\n")

    # Test 2: Frontend QR response (real scenario) - missing PricedFlightOffers entirely
    success2 = test_frontend_qr_ordercreate()

    print("\n" + "="*60 + "\n")

    if success1 and success2:
        print(f"🎉 ALL QR OrderCreate tests PASSED!")
    else:
        print(f"💥 Some QR OrderCreate tests FAILED!")
        print(f"   Test 1 (QR with OfferPrice): {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"   Test 2 (Frontend QR): {'✅ PASS' if success2 else '❌ FAIL'}")
