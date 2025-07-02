#!/usr/bin/env python3
"""
Test script for OfferID extraction logic.
This script tests the various methods of extracting OfferID from different flight price response structures.
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_offer_id_extraction_methods():
    """Test different OfferID extraction methods with various data structures."""
    
    # Test data structures that might be received from the frontend
    test_cases = [
        {
            "name": "Direct PricedFlightOffers structure",
            "data": {
                "PricedFlightOffers": {
                    "PricedFlightOffer": [
                        {
                            "OfferID": {
                                "value": "TEST_OFFER_ID_1"
                            },
                            "OfferPrice": [
                                {
                                    "OfferItemID": "ITEM_1"
                                }
                            ]
                        }
                    ]
                }
            },
            "expected_offer_id": "TEST_OFFER_ID_1"
        },
        {
            "name": "Nested data.raw_response structure",
            "data": {
                "data": {
                    "raw_response": {
                        "PricedFlightOffers": {
                            "PricedFlightOffer": [
                                {
                                    "OfferID": {
                                        "value": "TEST_OFFER_ID_2"
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            "expected_offer_id": "TEST_OFFER_ID_2"
        },
        {
            "name": "FlightPriceRS structure",
            "data": {
                "FlightPriceRS": {
                    "PricedFlightOffers": {
                        "PricedFlightOffer": [
                            {
                                "OfferID": {
                                    "value": "TEST_OFFER_ID_3"
                                }
                            }
                        ]
                    }
                }
            },
            "expected_offer_id": "TEST_OFFER_ID_3"
        },
        {
            "name": "Simple OfferID (no value wrapper)",
            "data": {
                "PricedFlightOffers": {
                    "PricedFlightOffer": [
                        {
                            "OfferID": "SIMPLE_OFFER_ID"
                        }
                    ]
                }
            },
            "expected_offer_id": "SIMPLE_OFFER_ID"
        },
        {
            "name": "Deep nested structure",
            "data": {
                "response": {
                    "body": {
                        "flight_data": {
                            "offers": {
                                "PricedFlightOffers": {
                                    "PricedFlightOffer": [
                                        {
                                            "OfferID": {
                                                "value": "DEEP_NESTED_OFFER_ID"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            "expected_offer_id": "DEEP_NESTED_OFFER_ID"
        }
    ]
    
    def extract_offer_id_method_1(flight_price_response):
        """Method 1: Direct PricedFlightOffers at top level"""
        priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
            offer_id_node = priced_offers[0].get('OfferID', {})
            if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                return offer_id_node['value']
            elif offer_id_node:
                return offer_id_node
        return None
    
    def extract_offer_id_method_2(flight_price_response):
        """Method 2: Try nested data.raw_response structure"""
        if 'data' in flight_price_response:
            data_section = flight_price_response['data']
            if 'raw_response' in data_section:
                raw_response = data_section['raw_response']
                priced_offers = raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
                if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                    offer_id_node = priced_offers[0].get('OfferID', {})
                    if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                        return offer_id_node['value']
        return None
    
    def extract_offer_id_method_3(flight_price_response):
        """Method 3: Try FlightPriceRS structure"""
        flight_price_rs = flight_price_response.get('FlightPriceRS', {})
        priced_offers = flight_price_rs.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
            offer_id_node = priced_offers[0].get('OfferID', {})
            if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                return offer_id_node['value']
        return None
    
    def extract_offer_id_recursive(obj, path=""):
        """Method 4: Recursive search for OfferID"""
        if isinstance(obj, dict):
            if 'OfferID' in obj:
                offer_id_node = obj['OfferID']
                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                    return offer_id_node['value'], f"{path}.OfferID.value"
                elif offer_id_node:
                    return offer_id_node, f"{path}.OfferID"
            
            for key, value in obj.items():
                result, result_path = extract_offer_id_recursive(value, f"{path}.{key}" if path else key)
                if result:
                    return result, result_path
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                result, result_path = extract_offer_id_recursive(item, f"{path}[{i}]")
                if result:
                    return result, result_path
        
        return None, ""
    
    # Test all methods against all test cases
    results = []
    
    for test_case in test_cases:
        logger.info(f"\n=== Testing: {test_case['name']} ===")
        data = test_case['data']
        expected = test_case['expected_offer_id']
        
        # Test Method 1
        result1 = extract_offer_id_method_1(data)
        logger.info(f"Method 1 result: {result1}")
        
        # Test Method 2
        result2 = extract_offer_id_method_2(data)
        logger.info(f"Method 2 result: {result2}")
        
        # Test Method 3
        result3 = extract_offer_id_method_3(data)
        logger.info(f"Method 3 result: {result3}")
        
        # Test Method 4 (Recursive)
        result4, path4 = extract_offer_id_recursive(data)
        logger.info(f"Method 4 result: {result4} (found at: {path4})")
        
        # Determine which method worked
        working_methods = []
        if result1 == expected:
            working_methods.append("Method 1")
        if result2 == expected:
            working_methods.append("Method 2")
        if result3 == expected:
            working_methods.append("Method 3")
        if result4 == expected:
            working_methods.append("Method 4")
        
        results.append({
            'test_case': test_case['name'],
            'expected': expected,
            'results': {
                'method1': result1,
                'method2': result2,
                'method3': result3,
                'method4': result4
            },
            'working_methods': working_methods
        })
        
        logger.info(f"Expected: {expected}")
        logger.info(f"Working methods: {working_methods}")
    
    # Summary
    logger.info(f"\n=== SUMMARY ===")
    for result in results:
        logger.info(f"{result['test_case']}: {result['working_methods']}")
    
    return results

def test_offer_item_ids_extraction():
    """Test OfferItemIDs extraction from different structures."""
    
    test_data = {
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": {"value": "TEST_OFFER"},
                    "OfferPrice": [
                        {"OfferItemID": "ITEM_1"},
                        {"OfferItemID": "ITEM_2"}
                    ]
                }
            ]
        }
    }
    
    logger.info(f"\n=== Testing OfferItemIDs Extraction ===")
    
    # Extract OfferItemIDs
    offer_item_ids = []
    priced_offers = test_data.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
        offer_prices = priced_offers[0].get('OfferPrice', [])
        for offer_price in offer_prices:
            if 'OfferItemID' in offer_price:
                offer_item_ids.append(offer_price['OfferItemID'])
    
    logger.info(f"Extracted OfferItemIDs: {offer_item_ids}")
    logger.info(f"Expected: ['ITEM_1', 'ITEM_2']")
    logger.info(f"Match: {offer_item_ids == ['ITEM_1', 'ITEM_2']}")
    
    return offer_item_ids

def test_realistic_frontend_structure():
    """Test with a structure that might actually come from the frontend."""

    # This simulates what we might actually receive from the frontend
    realistic_structure = {
        "data": {
            "transformed_flights": [
                {
                    "offer_id": "0",  # This is the frontend index, not the real OfferID
                    "price": "1234.56"
                }
            ],
            "raw_response": {
                "FlightPriceRS": {
                    "PricedFlightOffers": {
                        "PricedFlightOffer": [
                            {
                                "OfferID": {
                                    "value": "REAL_AIRLINE_OFFER_ID_ABC123"
                                },
                                "OfferPrice": [
                                    {
                                        "OfferItemID": "ITEM_ABC_1"
                                    },
                                    {
                                        "OfferItemID": "ITEM_ABC_2"
                                    }
                                ]
                            }
                        ]
                    },
                    "ShoppingResponseID": {
                        "ResponseID": {
                            "value": "SHOPPING_RESPONSE_ID_XYZ789"
                        }
                    }
                }
            }
        }
    }

    logger.info(f"\n=== Testing Realistic Frontend Structure ===")

    # Test our recursive extraction
    def extract_offer_id_recursive(obj, path=""):
        if isinstance(obj, dict):
            if 'OfferID' in obj:
                offer_id_node = obj['OfferID']
                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                    return offer_id_node['value'], f"{path}.OfferID.value"
                elif offer_id_node:
                    return offer_id_node, f"{path}.OfferID"

            for key, value in obj.items():
                result, result_path = extract_offer_id_recursive(value, f"{path}.{key}" if path else key)
                if result:
                    return result, result_path
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                result, result_path = extract_offer_id_recursive(item, f"{path}[{i}]")
                if result:
                    return result, result_path

        return None, ""

    # Extract the real OfferID
    real_offer_id, path = extract_offer_id_recursive(realistic_structure)
    logger.info(f"Real OfferID found: {real_offer_id}")
    logger.info(f"Found at path: {path}")

    # Extract OfferItemIDs using the same enhanced logic as in the backend
    offer_item_ids = []

    def extract_offer_item_ids_from_structure(data, path=""):
        """Extract OfferItemIDs from a PricedFlightOffers structure."""
        local_offer_item_ids = []
        try:
            priced_offers = data.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                offer_prices = priced_offers[0].get('OfferPrice', [])
                if not isinstance(offer_prices, list):
                    offer_prices = [offer_prices] if offer_prices else []

                for offer_price in offer_prices:
                    offer_item_id = offer_price.get('OfferItemID')
                    if offer_item_id:
                        local_offer_item_ids.append(offer_item_id)

                if local_offer_item_ids:
                    logger.info(f"Found OfferItemIDs at {path}: {local_offer_item_ids}")
        except Exception as e:
            logger.warning(f"Error extracting OfferItemIDs from {path}: {e}")

        return local_offer_item_ids

    # Try the FlightPriceRS structure (where we found the OfferID)
    if 'data' in realistic_structure and 'raw_response' in realistic_structure['data']:
        raw_response = realistic_structure['data']['raw_response']
        flight_price_rs = raw_response.get('FlightPriceRS', {})
        if flight_price_rs:
            offer_item_ids = extract_offer_item_ids_from_structure(flight_price_rs, "data.raw_response.FlightPriceRS")

    logger.info(f"OfferItemIDs found: {offer_item_ids}")

    # Extract ShoppingResponseID
    shopping_response_id = None
    try:
        shopping_id_node = realistic_structure['data']['raw_response']['FlightPriceRS']['ShoppingResponseID']
        if isinstance(shopping_id_node, dict) and 'ResponseID' in shopping_id_node:
            shopping_response_id = shopping_id_node['ResponseID'].get('value')
    except Exception as e:
        logger.error(f"Error extracting ShoppingResponseID: {e}")

    logger.info(f"ShoppingResponseID found: {shopping_response_id}")

    # Simulate what should happen vs what was happening
    frontend_offer_id = realistic_structure['data']['transformed_flights'][0]['offer_id']  # This would be "0"

    logger.info(f"\n=== Comparison ===")
    logger.info(f"Frontend OfferID (wrong): {frontend_offer_id}")
    logger.info(f"Real OfferID (correct): {real_offer_id}")
    logger.info(f"Should use real OfferID: {real_offer_id != frontend_offer_id}")

    return {
        'real_offer_id': real_offer_id,
        'offer_item_ids': offer_item_ids,
        'shopping_response_id': shopping_response_id,
        'frontend_offer_id': frontend_offer_id
    }

if __name__ == "__main__":
    logger.info("Starting OfferID extraction tests...")

    # Test OfferID extraction
    offer_id_results = test_offer_id_extraction_methods()

    # Test OfferItemIDs extraction
    offer_item_ids = test_offer_item_ids_extraction()

    # Test realistic frontend structure
    realistic_results = test_realistic_frontend_structure()

    logger.info(f"\nTests completed!")
