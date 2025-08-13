"""
Test FlightPrice request builder using the multi-airline AirShopping response.

This script tests the FlightPrice request builder with real multi-airline data
to ensure it works correctly with complex airline responses.
"""
import json
import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_flightprice_rq import build_flight_price_request

class TestFlightPriceRequestBuilder(unittest.TestCase):
    """Test cases for FlightPrice request builder using multi-airline AirShopping data"""

    def setUp(self):
        """Set up test fixtures with AirShopping response data"""
        # Load the AirShopping response data
        airshopping_path = Path(__file__).parent.parent / "Seats & Services" / "2_AirShoppingRS.json"
        
        self.assertTrue(airshopping_path.exists(), "AirShopping response test data file not found")
        
        with open(airshopping_path, 'r', encoding='utf-8') as f:
            self.airshopping_response = json.load(f)
            
        print(f"SUCCESS: Loaded AirShopping response with {len(str(self.airshopping_response))} characters")
        
        # Analyze the AirShopping data structure
        self._analyze_airshopping_data()

    def _analyze_airshopping_data(self):
        """Analyze the AirShopping response data structure"""
        print("\n" + "="*60)
        print("AIRSHOPPING RESPONSE DATA ANALYSIS")
        print("="*60)
        
        # Check for warnings
        warnings = self.airshopping_response.get('Warnings', {}).get('Warning', [])
        print(f"Warnings: {len(warnings)} warnings from airlines")
        for warning in warnings[:3]:  # Show first 3 warnings
            owner = warning.get('Owner', 'N/A')
            value = warning.get('value', 'N/A')
            print(f"  Warning from {owner}: {value}")
        
        # Check offers structure
        offers_group = self.airshopping_response.get('OffersGroup', {})
        airline_offers_list = offers_group.get('AirlineOffers', [])
        print(f"AirlineOffers entries: {len(airline_offers_list)}")
        
        if airline_offers_list:
            # Count total offers across all airlines
            total_offers = 0
            for airline_offers_node in airline_offers_list:
                airline_offers = airline_offers_node.get('AirlineOffer', [])
                if isinstance(airline_offers, list):
                    total_offers += len(airline_offers)
                elif airline_offers:  # Single offer as dict
                    total_offers += 1
            print(f"Total offers across all airlines: {total_offers}")
        
        # Check DataLists
        data_lists = self.airshopping_response.get('DataLists', {})
        print(f"DataLists sections: {list(data_lists.keys())}")
        
        # Travelers
        travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        print(f"Anonymous travelers: {len(travelers)}")
        
        # Flight segments
        segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        print(f"Flight segments: {len(segments)}")
        
        # Fare groups
        fare_groups = data_lists.get('FareList', {}).get('FareGroup', [])
        print(f"Fare groups: {len(fare_groups)}")
        
        # Check for errors
        errors = self.airshopping_response.get('Errors', {}).get('Error', [])
        print(f"Errors: {len(errors)} errors from airlines")
        error_owners = [error.get('Owner', 'Unknown') for error in errors[:10]]  # Show first 10
        print(f"  Error owners (first 10): {error_owners}")

    def test_flightprice_request_generation_first_offer(self):
        """Test FlightPrice request generation using the first available offer"""
        print("\n" + "="*70)
        print("TEST: FlightPrice Request Generation - First Offer")
        print("="*70)
        
        try:
            # Try to build FlightPrice request for first offer (index 0)
            result = build_flight_price_request(
                airshopping_response=self.airshopping_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Query', result)
            self.assertIn('DataLists', result)
            
            print("SUCCESS: FlightPrice request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            print(f"Top-level sections: {list(result.keys())}")
            
            # Analyze Query structure
            query = result.get('Query', {})
            if 'OriginDestination' in query:
                ods = query['OriginDestination']
                print(f"SUCCESS: {len(ods)} OriginDestination(s) in Query")
            
            if 'Offers' in query:
                offers = query['Offers'].get('Offer', [])
                print(f"SUCCESS: {len(offers)} Offer(s) in Query")
            
            # Analyze DataLists
            data_lists = result.get('DataLists', {})
            print(f"SUCCESS: DataLists contains {len(data_lists.keys())} sections: {list(data_lists.keys())}")
            
            # Check Travelers
            travelers = result.get('Travelers', {}).get('Traveler', [])
            print(f"SUCCESS: {len(travelers)} traveler(s)")
            
            # Save output
            output_path = Path(__file__).parent / "output_flightprice_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: FlightPrice request saved to: {output_path}")
            
            return result
            
        except Exception as e:
            print(f"ERROR: FlightPrice request generation failed: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            
            # Try to get more details about available offers
            try:
                offers_group = self.airshopping_response.get('OffersGroup', {})
                airline_offers_list = offers_group.get('AirlineOffers', [])
                
                print(f"\nDEBUG: Found {len(airline_offers_list)} AirlineOffers entries")
                
                for i, airline_offers_node in enumerate(airline_offers_list):
                    airline_offers = airline_offers_node.get('AirlineOffer', [])
                    if isinstance(airline_offers, list):
                        print(f"  AirlineOffers[{i}]: {len(airline_offers)} offers")
                        if airline_offers:
                            first_offer = airline_offers[0]
                            offer_id = first_offer.get('OfferID', {})
                            print(f"    First offer ID: {offer_id.get('value', 'N/A')} (Owner: {offer_id.get('Owner', 'N/A')})")
                    elif airline_offers:
                        print(f"  AirlineOffers[{i}]: 1 offer (dict format)")
                        offer_id = airline_offers.get('OfferID', {})
                        print(f"    Offer ID: {offer_id.get('value', 'N/A')} (Owner: {offer_id.get('Owner', 'N/A')})")
                    else:
                        print(f"  AirlineOffers[{i}]: No offers")
                        
            except Exception as debug_e:
                print(f"DEBUG ERROR: {debug_e}")
            
            # Re-raise the original exception for the test to fail
            raise e

    def test_flightprice_multiple_offers(self):
        """Test FlightPrice request generation for multiple offers if available"""
        print("\n" + "="*70)
        print("TEST: FlightPrice Request Generation - Multiple Offers")
        print("="*70)
        
        try:
            # Count total available offers
            offers_group = self.airshopping_response.get('OffersGroup', {})
            airline_offers_list = offers_group.get('AirlineOffers', [])
            
            total_offers = 0
            offer_details = []
            
            for airline_offers_node in airline_offers_list:
                airline_offers = airline_offers_node.get('AirlineOffer', [])
                if isinstance(airline_offers, list):
                    for offer in airline_offers:
                        offer_id = offer.get('OfferID', {})
                        offer_details.append({
                            'index': total_offers,
                            'id': offer_id.get('value', 'N/A'),
                            'owner': offer_id.get('Owner', 'N/A')
                        })
                        total_offers += 1
                elif airline_offers:  # Single offer as dict
                    offer_id = airline_offers.get('OfferID', {})
                    offer_details.append({
                        'index': total_offers,
                        'id': offer_id.get('value', 'N/A'),
                        'owner': offer_id.get('Owner', 'N/A')
                    })
                    total_offers += 1
            
            print(f"Total available offers: {total_offers}")
            
            # Test first few offers (up to 3)
            test_indices = list(range(min(3, total_offers)))
            successful_tests = 0
            
            for index in test_indices:
                try:
                    print(f"\nTesting offer {index}: {offer_details[index]['id']} ({offer_details[index]['owner']})")
                    
                    result = build_flight_price_request(
                        airshopping_response=self.airshopping_response,
                        selected_offer_index=index
                    )
                    
                    # Basic validation
                    self.assertIsInstance(result, dict)
                    self.assertIn('Query', result)
                    
                    query_offers = result.get('Query', {}).get('Offers', {}).get('Offer', [])
                    if query_offers:
                        selected_offer = query_offers[0]
                        selected_offer_id = selected_offer.get('OfferID', {}).get('value', 'N/A')
                        print(f"  SUCCESS: Generated request for offer {selected_offer_id}")
                        successful_tests += 1
                    
                except Exception as e:
                    print(f"  FAILED: Offer {index} failed with error: {str(e)}")
            
            print(f"\nSUMMARY: {successful_tests}/{len(test_indices)} offers tested successfully")
            self.assertGreater(successful_tests, 0, "At least one offer should generate successfully")
            
        except Exception as e:
            self.fail(f"Multiple offers test failed: {str(e)}")

    def test_flightprice_request_structure_validation(self):
        """Test comprehensive structure validation of generated FlightPrice request"""
        print("\n" + "="*70)
        print("TEST: FlightPrice Request Structure Validation")
        print("="*70)
        
        try:
            result = build_flight_price_request(
                airshopping_response=self.airshopping_response,
                selected_offer_index=0
            )
            
            # Validate top-level structure
            required_sections = ['Query', 'DataLists']
            for section in required_sections:
                self.assertIn(section, result, f"Missing required section: {section}")
                print(f"✓ Required section present: {section}")
            
            # Validate Query structure
            query = result['Query']
            self.assertIn('OriginDestination', query, "Query missing OriginDestination")
            self.assertIn('Offers', query, "Query missing Offers")
            print("✓ Query structure valid")
            
            # Validate Offers structure
            offers = query['Offers'].get('Offer', [])
            self.assertGreater(len(offers), 0, "No offers in Query")
            
            first_offer = offers[0]
            self.assertIn('OfferID', first_offer, "Offer missing OfferID")
            
            offer_id = first_offer['OfferID']
            self.assertIn('value', offer_id, "OfferID missing value")
            self.assertIn('Owner', offer_id, "OfferID missing Owner")
            print(f"✓ Offer structure valid: {offer_id['value']} (Owner: {offer_id['Owner']})")
            
            # Validate DataLists structure
            data_lists = result['DataLists']
            expected_datalists = ['FareGroup', 'AnonymousTravelerList']
            
            for section in expected_datalists:
                if section in data_lists:
                    print(f"✓ DataLists section present: {section}")
                else:
                    print(f"⚠ DataLists section missing: {section}")
            
            # Validate Travelers if present
            if 'Travelers' in result:
                travelers = result['Travelers'].get('Traveler', [])
                print(f"✓ Travelers present: {len(travelers)} traveler(s)")
                
                if travelers:
                    first_traveler = travelers[0]
                    self.assertIn('AnonymousTraveler', first_traveler, "Traveler missing AnonymousTraveler")
                    
                    anon_traveler = first_traveler['AnonymousTraveler'][0]
                    self.assertIn('ObjectKey', anon_traveler, "AnonymousTraveler missing ObjectKey")
                    self.assertIn('PTC', anon_traveler, "AnonymousTraveler missing PTC")
                    print(f"✓ Traveler structure valid: {anon_traveler['ObjectKey']}")
            
            # Validate ShoppingResponseID if present
            if 'ShoppingResponseID' in result:
                shopping_id = result['ShoppingResponseID']
                if 'value' in shopping_id:
                    print(f"✓ ShoppingResponseID present: {shopping_id['value']}")
                else:
                    print("⚠ ShoppingResponseID missing value")
            
            print("SUCCESS: FlightPrice request structure validation completed")
            
        except Exception as e:
            self.fail(f"Structure validation failed: {str(e)}")

    def test_flightprice_comprehensive_output(self):
        """Generate comprehensive FlightPrice request output and analysis"""
        print("\n" + "="*80)
        print("COMPREHENSIVE FLIGHTPRICE REQUEST OUTPUT")
        print("="*80)
        
        try:
            result = build_flight_price_request(
                airshopping_response=self.airshopping_response,
                selected_offer_index=0
            )
            
            print("\nFLIGHTPRICE REQUEST STATISTICS:")
            print("-" * 50)
            
            # Top-level sections
            print(f"Top-level sections: {list(result.keys())}")
            
            # Query analysis
            query = result.get('Query', {})
            if 'OriginDestination' in query:
                ods = query['OriginDestination']
                print(f"Origin-Destinations: {len(ods)}")
                
                # Analyze each OD
                for i, od in enumerate(ods):
                    flights = od.get('Flight', [])
                    print(f"  OD {i+1}: {len(flights)} flight(s)")
            
            if 'Offers' in query:
                offers = query['Offers'].get('Offer', [])
                print(f"Query Offers: {len(offers)}")
                
                for i, offer in enumerate(offers):
                    offer_id = offer.get('OfferID', {})
                    offer_items = offer.get('OfferItemIDs', {}).get('OfferItemID', [])
                    print(f"  Offer {i+1}: {offer_id.get('value', 'N/A')} ({offer_id.get('Owner', 'N/A')}) - {len(offer_items)} items")
            
            # DataLists analysis
            data_lists = result.get('DataLists', {})
            print(f"DataLists sections: {list(data_lists.keys())}")
            
            for section, content in data_lists.items():
                if isinstance(content, list):
                    print(f"  {section}: {len(content)} items")
                elif isinstance(content, dict):
                    if section == 'AnonymousTravelerList':
                        travelers = content.get('AnonymousTraveler', [])
                        print(f"  {section}: {len(travelers)} travelers")
                    else:
                        print(f"  {section}: 1 item (dict)")
                else:
                    print(f"  {section}: {type(content).__name__}")
            
            # Travelers analysis
            travelers = result.get('Travelers', {}).get('Traveler', [])
            print(f"Travelers: {len(travelers)}")
            
            # Metadata analysis
            if 'Metadata' in result:
                metadata = result['Metadata']
                print(f"Metadata sections: {list(metadata.keys())}")
            
            # ShoppingResponseID
            if 'ShoppingResponseID' in result:
                shopping_id = result['ShoppingResponseID'].get('value', 'N/A')
                print(f"ShoppingResponseID: {shopping_id}")
            
            print("\n" + "="*50)
            print("FULL FLIGHTPRICE REQUEST JSON:")
            print("="*50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"ERROR in comprehensive output: {str(e)}")
            raise e


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
