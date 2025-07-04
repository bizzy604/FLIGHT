#!/usr/bin/env python3
"""
Comprehensive test suite for card payment functionality in build_ordercreate_rq.py

This test suite covers:
1. Valid card payment scenarios
2. Invalid card payment scenarios
3. Edge cases and error handling
4. Payment amount calculation
5. Multi-airline payment processing

Author: FLIGHT Application
Created: 2025-07-03
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_ordercreate_rq import (
    generate_order_create_rq,
    process_payments_for_order_create
)


class TestCardPayments(unittest.TestCase):
    """Test suite for card payment functionality."""

    def setUp(self):
        """Set up test data for each test."""
        # Sample flight price response with pricing data
        self.flight_price_response = {
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

        # Sample passenger data
        self.passengers_data = [{
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

    def test_valid_card_payment_basic(self):
        """Test basic valid card payment processing."""
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
                flight_price_response=self.flight_price_response,
                passengers_data=self.passengers_data,
                payment_input_info=payment_data
            )

            # Verify payment structure
            self.assertIn('Query', order_create_request)
            self.assertIn('Payments', order_create_request['Query'])
            payments = order_create_request['Query']['Payments']['Payment']
            self.assertEqual(len(payments), 1)

            payment = payments[0]
            self.assertIn('Method', payment)
            self.assertIn('PaymentCard', payment['Method'])

            card_details = payment['Method']['PaymentCard']
            self.assertEqual(card_details['CardNumber']['value'], "4111111111111111")
            self.assertEqual(card_details['CardType'], "VI")
            self.assertEqual(card_details['CardCode'], "123")
            self.assertEqual(card_details['CardHolderName']['value'], "John Doe")

            print("✅ Basic card payment test passed")

        except Exception as e:
            self.fail(f"Valid card payment test failed: {e}")

    def test_card_payment_with_billing_address(self):
        """Test card payment with billing address."""
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
                flight_price_response=self.flight_price_response,
                passengers_data=self.passengers_data,
                payment_input_info=payment_data
            )

            payment = order_create_request['Query']['Payments']['Payment'][0]
            card_details = payment['Method']['PaymentCard']

            # Verify billing address
            self.assertIn('CardHolderBillingAddress', card_details)
            billing_addr = card_details['CardHolderBillingAddress']
            self.assertEqual(billing_addr['Street'], ["123 Main St", "Apt 4B"])
            self.assertEqual(billing_addr['PostalCode'], "12345")
            self.assertEqual(billing_addr['CityName'], "New York")
            self.assertEqual(billing_addr['CountryCode']['value'], "US")

            # Verify series code
            self.assertIn('SeriesCode', card_details)
            self.assertEqual(card_details['SeriesCode']['value'], "456")

            print("✅ Card payment with billing address test passed")

        except Exception as e:
            self.fail(f"Card payment with billing address test failed: {e}")

    def test_invalid_card_payment_missing_required_fields(self):
        """Test card payment with missing required fields."""
        test_cases = [
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
                },
                "expected_error": "CardNumberToken mandatory"
            },
            {
                "name": "Missing Expiration Date",
                "payment_data": {
                    "MethodType": "PAYMENTCARD",
                    "Details": {
                        "CardNumberToken": "4111111111111111",
                        "CardType": "VI",
                        "CardCode": "123",
                        "CardHolderName": {"value": "John Doe"}
                    }
                },
                "expected_error": "EffectiveExpireDate.Expiration"
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
                },
                "expected_error": "CardType mandatory"
            },
            {
                "name": "Missing CardCode",
                "payment_data": {
                    "MethodType": "PAYMENTCARD",
                    "Details": {
                        "CardNumberToken": "4111111111111111",
                        "EffectiveExpireDate": {"Expiration": "1225"},
                        "CardType": "VI",
                        "CardHolderName": {"value": "John Doe"}
                    }
                },
                "expected_error": "CardCode mandatory"
            },
            {
                "name": "Missing CardHolderName",
                "payment_data": {
                    "MethodType": "PAYMENTCARD",
                    "Details": {
                        "CardNumberToken": "4111111111111111",
                        "EffectiveExpireDate": {"Expiration": "1225"},
                        "CardType": "VI",
                        "CardCode": "123"
                    }
                },
                "expected_error": "CardHolderName.value is mandatory"
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case["name"]):
                with self.assertRaises(ValueError) as context:
                    generate_order_create_rq(
                        flight_price_response=self.flight_price_response,
                        passengers_data=self.passengers_data,
                        payment_input_info=test_case["payment_data"]
                    )
                
                self.assertIn(test_case["expected_error"], str(context.exception))
                print(f"✅ {test_case['name']} validation test passed")

    def test_payment_amount_calculation(self):
        """Test that payment amount is correctly calculated from flight price response."""
        payment_data = {
            "MethodType": "PAYMENTCARD",
            "Details": {
                "CardNumberToken": "4111111111111111",
                "EffectiveExpireDate": {"Expiration": "1225"},
                "CardType": "VI",
                "CardCode": "123",
                "CardHolderName": {"value": "John Doe"}
            }
        }

        order_create_request = generate_order_create_rq(
            flight_price_response=self.flight_price_response,
            passengers_data=self.passengers_data,
            payment_input_info=payment_data
        )

        payment = order_create_request['Query']['Payments']['Payment'][0]
        
        # Verify payment amount matches flight price
        self.assertEqual(payment['Amount']['value'], 1500.00)
        self.assertEqual(payment['Amount']['Code'], "USD")
        
        # Verify card amount matches payment amount
        card_amount = payment['Method']['PaymentCard']['Amount']
        self.assertEqual(card_amount['value'], 1500.00)
        self.assertEqual(card_amount['Code'], "USD")

        print("✅ Payment amount calculation test passed")

    def test_payment_amount_validation(self):
        """Test payment amount validation and currency handling."""
        # Test with different currency
        flight_price_eur = self.flight_price_response.copy()
        flight_price_eur["PricedFlightOffers"]["PricedFlightOffer"][0]["OfferPrice"][0]["RequestedDate"]["PriceDetail"]["TotalAmount"]["SimpleCurrencyPrice"]["Code"] = "EUR"
        flight_price_eur["PricedFlightOffers"]["PricedFlightOffer"][0]["OfferPrice"][0]["RequestedDate"]["PriceDetail"]["TotalAmount"]["SimpleCurrencyPrice"]["value"] = 1350.00

        payment_data = {
            "MethodType": "PAYMENTCARD",
            "Details": {
                "CardNumberToken": "4111111111111111",
                "EffectiveExpireDate": {"Expiration": "1225"},
                "CardType": "VI",
                "CardCode": "123",
                "CardHolderName": {"value": "John Doe"}
            }
        }

        order_create_request = generate_order_create_rq(
            flight_price_response=flight_price_eur,
            passengers_data=self.passengers_data,
            payment_input_info=payment_data
        )

        payment = order_create_request['Query']['Payments']['Payment'][0]

        # Verify EUR currency is preserved
        self.assertEqual(payment['Amount']['value'], 1350.00)
        self.assertEqual(payment['Amount']['Code'], "EUR")
        self.assertEqual(payment['Method']['PaymentCard']['Amount']['Code'], "EUR")

        print("✅ Payment amount validation test passed")

    def test_card_payment_with_secure_payment_v2(self):
        """Test card payment with 3D Secure v2 authentication."""
        payment_data = {
            "MethodType": "PAYMENTCARD",
            "Details": {
                "CardNumberToken": "4111111111111111",
                "EffectiveExpireDate": {"Expiration": "1225"},
                "CardType": "VI",
                "CardCode": "123",
                "CardHolderName": {"value": "John Doe"},
                "SecurePaymentVersion2": {
                    "AuthenticationValue": "BwABBJQ1AgAAAAAgJDUCAAAAAAA=",
                    "DirectoryServerTransactionId": "8a880dc0-d2d2-4067-bcb1-b08d1690b26e",
                    "ElectronicCommerceIndicator": "05"
                }
            }
        }

        order_create_request = generate_order_create_rq(
            flight_price_response=self.flight_price_response,
            passengers_data=self.passengers_data,
            payment_input_info=payment_data
        )

        payment = order_create_request['Query']['Payments']['Payment'][0]
        card_details = payment['Method']['PaymentCard']

        # Verify 3D Secure v2 data is included
        self.assertIn('SecurePaymentVersion2', card_details)
        secure_payment = card_details['SecurePaymentVersion2']
        self.assertEqual(secure_payment['AuthenticationValue'], "BwABBJQ1AgAAAAAgJDUCAAAAAAA=")
        self.assertEqual(secure_payment['DirectoryServerTransactionId'], "8a880dc0-d2d2-4067-bcb1-b08d1690b26e")
        self.assertEqual(secure_payment['ElectronicCommerceIndicator'], "05")

        print("✅ 3D Secure v2 payment test passed")

    def test_card_payment_fallback_to_cash(self):
        """Test fallback to cash when payment data is invalid."""
        # Test with empty payment data
        empty_payment_data = {}

        order_create_request = generate_order_create_rq(
            flight_price_response=self.flight_price_response,
            passengers_data=self.passengers_data,
            payment_input_info=empty_payment_data
        )

        payment = order_create_request['Query']['Payments']['Payment'][0]

        # Should fallback to cash
        self.assertIn('Cash', payment['Method'])
        self.assertTrue(payment['Method']['Cash']['CashInd'])

        print("✅ Fallback to cash test passed")

    def test_card_payment_with_product_type_code(self):
        """Test card payment with product type code."""
        payment_data = {
            "MethodType": "PAYMENTCARD",
            "Details": {
                "CardNumberToken": "4111111111111111",
                "EffectiveExpireDate": {"Expiration": "1225"},
                "CardType": "VI",
                "CardCode": "123",
                "CardHolderName": {"value": "John Doe"},
                "ProductTypeCode": ["CREDIT", "REWARDS"]
            }
        }

        order_create_request = generate_order_create_rq(
            flight_price_response=self.flight_price_response,
            passengers_data=self.passengers_data,
            payment_input_info=payment_data
        )

        payment = order_create_request['Query']['Payments']['Payment'][0]
        card_details = payment['Method']['PaymentCard']

        # Verify product type code is included
        self.assertIn('ProductTypeCode', card_details)
        self.assertEqual(card_details['ProductTypeCode'], ["CREDIT", "REWARDS"])

        print("✅ Product type code test passed")

    def test_multi_airline_card_payment(self):
        """Test card payment processing with multi-airline flight price response."""
        # Create multi-airline flight price response
        multi_airline_response = self.flight_price_response.copy()
        multi_airline_response["ShoppingResponseID"]["ResponseID"]["value"] = "test-response-123-KQ"

        # Add airline prefix to traveler ObjectKey
        multi_airline_response["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"][0]["ObjectKey"] = "KQ-PAX1"

        payment_data = {
            "MethodType": "PAYMENTCARD",
            "Details": {
                "CardNumberToken": "4111111111111111",
                "EffectiveExpireDate": {"Expiration": "1225"},
                "CardType": "VI",
                "CardCode": "123",
                "CardHolderName": {"value": "John Doe"}
            }
        }

        # Update passenger data to match
        multi_airline_passengers = self.passengers_data.copy()
        multi_airline_passengers[0]["ObjectKey"] = "KQ-PAX1"

        order_create_request = generate_order_create_rq(
            flight_price_response=multi_airline_response,
            passengers_data=multi_airline_passengers,
            payment_input_info=payment_data
        )

        # Verify the request was generated successfully
        self.assertIn('Query', order_create_request)
        self.assertIn('Payments', order_create_request['Query'])

        payment = order_create_request['Query']['Payments']['Payment'][0]
        self.assertIn('PaymentCard', payment['Method'])

        print("✅ Multi-airline card payment test passed")


if __name__ == '__main__':
    print("🧪 Starting Card Payment Tests")
    print("=" * 50)

    unittest.main(verbosity=2)
