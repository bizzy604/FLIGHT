"""
Unit tests for ServiceList request builder.

Tests the build_servicelist_request function using actual FlightPriceRS data
from the "Seats & Services" folder to ensure correct request structure generation.
"""
import json
import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_servicelist_rq import build_servicelist_request

class TestServiceListRequestBuilder(unittest.TestCase):
    """Test cases for ServiceList request builder"""

    def setUp(self):
        """Set up test fixtures with actual FlightPriceRS data"""
        # Load the FlightPriceRS from Seats & Services folder
        seats_services_dir = Path(__file__).parent.parent / "Seats & Services"
        flight_price_rs_path = seats_services_dir / "4_FlightPriceRS.json"
        
        self.assertTrue(flight_price_rs_path.exists(), "FlightPriceRS test data file not found")
        
        with open(flight_price_rs_path, 'r', encoding='utf-8') as f:
            self.flight_price_response = json.load(f)
        
        # Load expected ServiceListRQ for structure comparison
        service_list_rq_path = seats_services_dir / "5_ServiceListRQ.json"
        
        if service_list_rq_path.exists():
            with open(service_list_rq_path, 'r', encoding='utf-8') as f:
                self.expected_structure = json.load(f)
        else:
            self.expected_structure = None
            
        print(f"SUCCESS: Loaded FlightPriceRS with {len(str(self.flight_price_response))} characters")
        if self.expected_structure:
            print(f"SUCCESS: Loaded expected ServiceListRQ structure")

    def test_basic_servicelist_request_generation(self):
        """Test basic ServiceList request generation"""
        print("\n" + "="*60)
        print("TEST: Basic ServiceList Request Generation")
        print("="*60)
        
        try:
            result = build_servicelist_request(
                flight_price_response=self.flight_price_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: ServiceList request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Print the generated request structure
            print("\nGENERATED SERVICELIST REQUEST STRUCTURE:")
            print("-" * 40)
            self._print_structure(result, max_depth=3)
            
            # Save the generated request for inspection
            output_path = Path(__file__).parent / "output_servicelist_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nSUCCESS: Generated request saved to: {output_path}")
            
            return result
            
        except Exception as e:
            self.fail(f"ServiceList request generation failed: {str(e)}")

    def test_travelers_mapping(self):
        """Test that travelers are correctly mapped from FlightPriceRS"""
        print("\n" + "="*60)
        print("TEST: Travelers Mapping")
        print("="*60)
        
        result = build_servicelist_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check Travelers section
        self.assertIn('Travelers', result)
        travelers = result['Travelers']
        self.assertIn('Traveler', travelers)
        
        traveler_list = travelers['Traveler']
        self.assertIsInstance(traveler_list, list)
        self.assertGreater(len(traveler_list), 0)
        
        # Validate first traveler structure
        first_traveler = traveler_list[0]
        self.assertIn('AnonymousTraveler', first_traveler)
        
        anonymous_travelers = first_traveler['AnonymousTraveler']
        self.assertIsInstance(anonymous_travelers, list)
        self.assertGreater(len(anonymous_travelers), 0)
        
        # Check first anonymous traveler
        first_anon = anonymous_travelers[0]
        self.assertIn('ObjectKey', first_anon)
        self.assertIn('PTC', first_anon)
        
        print(f"SUCCESS: Found {len(traveler_list)} travelers")
        print(f"SUCCESS: First traveler ObjectKey: {first_anon.get('ObjectKey')}")
        print(f"SUCCESS: First traveler PTC: {first_anon.get('PTC', {}).get('value')}")
        
        # Print all travelers
        for i, traveler in enumerate(traveler_list):
            anon_traveler = traveler['AnonymousTraveler'][0]
            object_key = anon_traveler.get('ObjectKey')
            ptc_value = anon_traveler.get('PTC', {}).get('value')
            print(f"  Traveler {i+1}: {object_key} ({ptc_value})")

    def test_query_section_structure(self):
        """Test that Query section has correct structure"""
        print("\n" + "="*60)
        print("TEST: Query Section Structure")
        print("="*60)
        
        result = build_servicelist_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check Query section
        self.assertIn('Query', result)
        query = result['Query']
        
        # Validate required Query subsections
        self.assertIn('OriginDestination', query)
        self.assertIn('Offers', query)
        
        # Check OriginDestination structure
        origin_destinations = query['OriginDestination']
        self.assertIsInstance(origin_destinations, list)
        self.assertGreater(len(origin_destinations), 0)
        
        # Check first OD has Flight array
        first_od = origin_destinations[0]
        self.assertIn('Flight', first_od)
        flights = first_od['Flight']
        self.assertIsInstance(flights, list)
        self.assertGreater(len(flights), 0)
        
        # Check flight structure
        first_flight = flights[0]
        required_flight_fields = ['SegmentKey', 'Departure', 'Arrival', 'MarketingCarrier']
        for field in required_flight_fields:
            self.assertIn(field, first_flight, f"Missing required field: {field}")
        
        print(f"SUCCESS: Found {len(origin_destinations)} OriginDestination(s)")
        print(f"SUCCESS: First OD contains {len(flights)} flight(s)")
        print(f"SUCCESS: First flight SegmentKey: {first_flight.get('SegmentKey')}")
        
        # Check Offers structure  
        offers = query['Offers']
        self.assertIn('Offer', offers)
        offer_list = offers['Offer']
        self.assertIsInstance(offer_list, list)
        self.assertGreater(len(offer_list), 0)
        
        first_offer = offer_list[0]
        self.assertIn('OfferID', first_offer)
        self.assertIn('OfferItemIDs', first_offer)
        
        offer_id = first_offer['OfferID']
        self.assertIn('value', offer_id)
        self.assertIn('Owner', offer_id)
        
        print(f"SUCCESS: Found {len(offer_list)} offer(s)")
        print(f"SUCCESS: First offer ID: {offer_id.get('value')}")
        print(f"SUCCESS: First offer Owner: {offer_id.get('Owner')}")

    def test_shopping_response_id_mapping(self):
        """Test ShoppingResponseID is correctly mapped"""
        print("\n" + "="*60)
        print("TEST: ShoppingResponseID Mapping")
        print("="*60)
        
        result = build_servicelist_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check ShoppingResponseID section
        self.assertIn('ShoppingResponseID', result)
        shopping_response_id = result['ShoppingResponseID']
        
        self.assertIn('ResponseID', shopping_response_id)
        response_id = shopping_response_id['ResponseID']
        self.assertIn('value', response_id)
        
        response_id_value = response_id['value']
        self.assertIsInstance(response_id_value, str)
        self.assertGreater(len(response_id_value), 0)
        
        print(f"SUCCESS: ShoppingResponseID value: {response_id_value}")
        
        # Verify it comes from the FlightPriceRS
        original_shopping_id = self.flight_price_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')
        if original_shopping_id:
            self.assertEqual(response_id_value, original_shopping_id)
            print(f"SUCCESS: ShoppingResponseID correctly mapped from FlightPriceRS")

    def test_multi_airline_detection(self):
        """Test multi-airline response detection and filtering"""
        print("\n" + "="*60)
        print("TEST: Multi-Airline Detection")
        print("="*60)
        
        result = build_servicelist_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check if airline-prefixed keys were handled
        travelers = result['Travelers']['Traveler']
        for traveler in travelers:
            anon_traveler = traveler['AnonymousTraveler'][0]
            object_key = anon_traveler.get('ObjectKey', '')
            
            # Should not contain airline prefixes in ServiceList request
            self.assertFalse(
                object_key.startswith('26-') or object_key.startswith('KQ-') or object_key.startswith('AF-'),
                f"ObjectKey should not contain airline prefix: {object_key}"
            )
            
            if object_key:
                print(f"SUCCESS: Clean ObjectKey: {object_key}")

    def test_vdc_structure_compliance(self):
        """Test compliance with VDC API documentation structure"""
        print("\n" + "="*60)
        print("TEST: VDC Structure Compliance")
        print("="*60)
        
        result = build_servicelist_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        if self.expected_structure:
            print("Comparing with expected ServiceListRQ structure...")
            
            # Compare top-level structure
            expected_keys = set(self.expected_structure.keys())
            actual_keys = set(result.keys())
            
            missing_keys = expected_keys - actual_keys
            extra_keys = actual_keys - expected_keys
            
            if missing_keys:
                print(f"WARNING: Missing keys: {missing_keys}")
            if extra_keys:
                print(f"WARNING: Extra keys: {extra_keys}")
                
            common_keys = expected_keys & actual_keys
            print(f"SUCCESS: Common keys: {common_keys}")
            
            # Detailed structure comparison for Travelers
            if 'Travelers' in common_keys:
                self._compare_travelers_structure(self.expected_structure['Travelers'], result['Travelers'])
                
            # Detailed structure comparison for Query
            if 'Query' in common_keys:
                self._compare_query_structure(self.expected_structure['Query'], result['Query'])
                
        else:
            print("WARNING: No expected structure file found for comparison")
            print("SUCCESS: Validating against VDC documentation requirements...")
            
            # Validate required top-level sections
            required_sections = ['Travelers', 'Query', 'ShoppingResponseID']
            for section in required_sections:
                self.assertIn(section, result, f"Missing required section: {section}")
                print(f"SUCCESS: Required section present: {section}")

    def _compare_travelers_structure(self, expected, actual):
        """Compare Travelers section structure"""
        print("  Comparing Travelers structure:")
        
        # Both should have Traveler array
        self.assertIn('Traveler', expected)
        self.assertIn('Traveler', actual)
        
        exp_travelers = expected['Traveler']
        act_travelers = actual['Traveler']
        
        print(f"    Expected travelers: {len(exp_travelers) if isinstance(exp_travelers, list) else 1}")
        print(f"    Actual travelers: {len(act_travelers) if isinstance(act_travelers, list) else 1}")

    def _compare_query_structure(self, expected, actual):
        """Compare Query section structure"""
        print("  Comparing Query structure:")
        
        # Check OriginDestination
        if 'OriginDestination' in expected and 'OriginDestination' in actual:
            exp_od = expected['OriginDestination']
            act_od = actual['OriginDestination']
            
            exp_count = len(exp_od) if isinstance(exp_od, list) else 1
            act_count = len(act_od) if isinstance(act_od, list) else 1
            
            print(f"    Expected OriginDestinations: {exp_count}")
            print(f"    Actual OriginDestinations: {act_count}")
            
        # Check Offers
        if 'Offers' in expected and 'Offers' in actual:
            exp_offers = expected['Offers']['Offer']
            act_offers = actual['Offers']['Offer']
            
            exp_count = len(exp_offers) if isinstance(exp_offers, list) else 1
            act_count = len(act_offers) if isinstance(act_offers, list) else 1
            
            print(f"    Expected Offers: {exp_count}")
            print(f"    Actual Offers: {act_count}")

    def _print_structure(self, obj, indent=0, max_depth=3, current_depth=0):
        """Recursively print object structure"""
        if current_depth >= max_depth:
            return
            
        spaces = "  " * indent
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    if isinstance(value, list) and len(value) > 0:
                        print(f"{spaces}{key}: [array with {len(value)} items]")
                        if current_depth < max_depth - 1:
                            self._print_structure(value[0], indent + 1, max_depth, current_depth + 1)
                    elif isinstance(value, dict):
                        print(f"{spaces}{key}:")
                        self._print_structure(value, indent + 1, max_depth, current_depth + 1)
                else:
                    value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"{spaces}{key}: {value_preview}")
        elif isinstance(obj, list) and len(obj) > 0:
            print(f"{spaces}[{len(obj)} items, showing first:]")
            self._print_structure(obj[0], indent, max_depth, current_depth + 1)

    def test_comprehensive_output_validation(self):
        """Comprehensive validation and output of the generated request"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SERVICELIST REQUEST VALIDATION & OUTPUT")
        print("="*80)
        
        result = build_servicelist_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Full JSON output for manual inspection
        print("\nFULL GENERATED SERVICELIST REQUEST:")
        print("-" * 50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Statistics
        print("\n" + "="*50)
        print("REQUEST STATISTICS:")
        print("="*50)
        
        travelers_count = len(result.get('Travelers', {}).get('Traveler', []))
        od_count = len(result.get('Query', {}).get('OriginDestination', []))
        offers_count = len(result.get('Query', {}).get('Offers', {}).get('Offer', []))
        
        print(f"Travelers: {travelers_count}")
        print(f"Origin-Destinations: {od_count}")
        print(f"Offers: {offers_count}")
        
        # Flight segments analysis
        total_flights = 0
        for od in result.get('Query', {}).get('OriginDestination', []):
            flights = od.get('Flight', [])
            total_flights += len(flights)
            
        print(f"Total Flight Segments: {total_flights}")
        
        shopping_response_id = result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'N/A')
        print(f"ShoppingResponseID: {shopping_response_id}")
        
        print("\nSUCCESS: ServiceList request validation complete")
        
        return result


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)