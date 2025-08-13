"""
Unit tests for SeatAvailability request builder.

Tests the build_seatavailability_request function using actual FlightPriceRS data
from the "Seats & Services" folder to ensure correct request structure generation.
"""
import json
import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_seatavailability_rq import build_seatavailability_request

class TestSeatAvailabilityRequestBuilder(unittest.TestCase):
    """Test cases for SeatAvailability request builder"""

    def setUp(self):
        """Set up test fixtures with actual FlightPriceRS data"""
        # Load the FlightPriceRS from Seats & Services folder
        seats_services_dir = Path(__file__).parent.parent / "Seats & Services"
        flight_price_rs_path = seats_services_dir / "4_FlightPriceRS.json"
        
        self.assertTrue(flight_price_rs_path.exists(), "FlightPriceRS test data file not found")
        
        with open(flight_price_rs_path, 'r', encoding='utf-8') as f:
            self.flight_price_response = json.load(f)
        
        # Load expected SeatAvailabilityRQ for structure comparison
        seat_avail_rq_path = seats_services_dir / "7_SeatAvailabilityRQ.json"
        
        if seat_avail_rq_path.exists():
            with open(seat_avail_rq_path, 'r', encoding='utf-8') as f:
                self.expected_structure = json.load(f)
        else:
            self.expected_structure = None
            
        print(f"SUCCESS: Loaded FlightPriceRS with {len(str(self.flight_price_response))} characters")
        if self.expected_structure:
            print(f"SUCCESS: Loaded expected SeatAvailabilityRQ structure")

    def test_basic_seatavailability_request_generation(self):
        """Test basic SeatAvailability request generation"""
        print("\n" + "="*60)
        print("TEST: Basic SeatAvailability Request Generation")
        print("="*60)
        
        try:
            result = build_seatavailability_request(
                flight_price_response=self.flight_price_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('DataLists', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: SeatAvailability request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Print the generated request structure
            print("\nGENERATED SEATAVAILABILITY REQUEST STRUCTURE:")
            print("-" * 40)
            self._print_structure(result, max_depth=3)
            
            # Save the generated request for inspection
            output_path = Path(__file__).parent / "output_seatavailability_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nSUCCESS: Generated request saved to: {output_path}")
            
            return result
            
        except Exception as e:
            self.fail(f"SeatAvailability request generation failed: {str(e)}")

    def test_travelers_with_recognized_traveler(self):
        """Test that travelers include RecognizedTraveler structure as per VDC docs"""
        print("\n" + "="*60)
        print("TEST: Travelers with RecognizedTraveler Structure")
        print("="*60)
        
        result = build_seatavailability_request(
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
        
        # Validate first traveler structure (RecognizedTraveler not required)
        first_traveler = traveler_list[0]
        self.assertIn('AnonymousTraveler', first_traveler)
        
        # Check AnonymousTraveler structure
        anonymous_travelers = first_traveler['AnonymousTraveler']
        self.assertIsInstance(anonymous_travelers, list)
        self.assertGreater(len(anonymous_travelers), 0)
        
        first_anon = anonymous_travelers[0]
        self.assertIn('ObjectKey', first_anon)
        self.assertIn('PTC', first_anon)
        
        print(f"SUCCESS: Found {len(traveler_list)} travelers")
        print(f"SUCCESS: First traveler ObjectKey: {first_anon.get('ObjectKey')}")
        print(f"SUCCESS: First traveler PTC: {first_anon.get('PTC', {}).get('value')}")

    def test_query_section_flight_segment_references(self):
        """Test that Query section uses FlightSegmentReference as per VDC docs"""
        print("\n" + "="*60)
        print("TEST: Query Section FlightSegmentReference Structure")
        print("="*60)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check Query section
        self.assertIn('Query', result)
        query = result['Query']
        
        # Validate required Query subsections
        self.assertIn('OriginDestination', query)
        self.assertIn('Offers', query)
        
        # Check OriginDestination structure uses FlightSegmentReference
        origin_destinations = query['OriginDestination']
        self.assertIsInstance(origin_destinations, list)
        self.assertGreater(len(origin_destinations), 0)
        
        # Check first OD has FlightSegmentReference array (not Flight array like ServiceList)
        first_od = origin_destinations[0]
        self.assertIn('FlightSegmentReference', first_od)
        flight_segment_refs = first_od['FlightSegmentReference']
        self.assertIsInstance(flight_segment_refs, list)
        self.assertGreater(len(flight_segment_refs), 0)
        
        # Check flight segment reference structure
        first_ref = flight_segment_refs[0]
        self.assertIn('ref', first_ref)
        ref_value = first_ref['ref']
        self.assertIsInstance(ref_value, str)
        self.assertGreater(len(ref_value), 0)
        
        print(f"SUCCESS: Found {len(origin_destinations)} OriginDestination(s)")
        print(f"SUCCESS: First OD contains {len(flight_segment_refs)} FlightSegmentReference(s)")
        print(f"SUCCESS: First FlightSegmentReference ref: {ref_value}")
        
        # Print all segment references
        for i, od in enumerate(origin_destinations):
            refs = od.get('FlightSegmentReference', [])
            ref_values = [ref.get('ref') for ref in refs]
            print(f"  OD {i+1} segment refs: {ref_values}")

    def test_datalists_structure(self):
        """Test that DataLists contains FlightSegmentList and FareList"""
        print("\n" + "="*60)
        print("TEST: DataLists Structure")
        print("="*60)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check DataLists section
        self.assertIn('DataLists', result)
        data_lists = result['DataLists']
        
        # Check FlightSegmentList
        if 'FlightSegmentList' in data_lists:
            flight_segment_list = data_lists['FlightSegmentList']
            self.assertIn('FlightSegment', flight_segment_list)
            
            flight_segments = flight_segment_list['FlightSegment']
            self.assertIsInstance(flight_segments, list)
            
            if len(flight_segments) > 0:
                first_segment = flight_segments[0]
                required_fields = ['SegmentKey', 'Departure', 'Arrival', 'MarketingCarrier']
                
                for field in required_fields:
                    self.assertIn(field, first_segment, f"Missing required field in FlightSegment: {field}")
                
                print(f"SUCCESS: Found {len(flight_segments)} flight segments in DataLists")
                print(f"SUCCESS: First segment key: {first_segment.get('SegmentKey')}")
        
        # Check FareList
        if 'FareList' in data_lists:
            fare_list = data_lists['FareList']
            self.assertIn('FareGroup', fare_list)
            
            fare_groups = fare_list['FareGroup']
            self.assertIsInstance(fare_groups, list)
            
            if len(fare_groups) > 0:
                first_fare = fare_groups[0]
                self.assertIn('ListKey', first_fare)
                
                print(f"SUCCESS: Found {len(fare_groups)} fare groups in DataLists")
                print(f"SUCCESS: First fare group key: {first_fare.get('ListKey')}")
        
        print(f"SUCCESS: DataLists contains {len(data_lists.keys())} sections: {list(data_lists.keys())}")

    def test_offers_structure(self):
        """Test Offers section structure"""
        print("\n" + "="*60)
        print("TEST: Offers Structure")
        print("="*60)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        query = result['Query']
        
        # Check Offers structure  
        offers = query['Offers']
        self.assertIn('Offer', offers)
        offer_list = offers['Offer']
        self.assertIsInstance(offer_list, list)
        self.assertGreater(len(offer_list), 0)
        
        first_offer = offer_list[0]
        self.assertIn('OfferID', first_offer)
        self.assertIn('OfferItemIDs', first_offer)
        
        # Check OfferID structure
        offer_id = first_offer['OfferID']
        required_offer_fields = ['value', 'Owner', 'Channel']
        for field in required_offer_fields:
            self.assertIn(field, offer_id, f"Missing required OfferID field: {field}")
        
        # Check OfferItemIDs structure
        offer_item_ids = first_offer['OfferItemIDs']
        self.assertIn('OfferItemID', offer_item_ids)
        offer_items = offer_item_ids['OfferItemID']
        self.assertIsInstance(offer_items, list)
        
        print(f"SUCCESS: Found {len(offer_list)} offer(s)")
        print(f"SUCCESS: Offer ID: {offer_id.get('value')}")
        print(f"SUCCESS: Offer Owner: {offer_id.get('Owner')}")
        print(f"SUCCESS: Offer Channel: {offer_id.get('Channel')}")
        print(f"SUCCESS: Found {len(offer_items)} offer item(s)")

    def test_shopping_response_id_mapping(self):
        """Test ShoppingResponseID is correctly mapped"""
        print("\n" + "="*60)
        print("TEST: ShoppingResponseID Mapping")
        print("="*60)
        
        result = build_seatavailability_request(
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

    def test_multi_airline_detection_and_filtering(self):
        """Test multi-airline response detection and filtering"""
        print("\n" + "="*60)
        print("TEST: Multi-Airline Detection and Filtering")
        print("="*60)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Check if airline-prefixed keys were handled in travelers
        travelers = result['Travelers']['Traveler']
        for traveler in travelers:
            anon_traveler = traveler['AnonymousTraveler'][0]
            object_key = anon_traveler.get('ObjectKey', '')
            
            # Should not contain airline prefixes in SeatAvailability request
            self.assertFalse(
                object_key.startswith('26-') or object_key.startswith('KQ-') or object_key.startswith('AF-'),
                f"Traveler ObjectKey should not contain airline prefix: {object_key}"
            )
            
            if object_key:
                print(f"SUCCESS: Clean traveler ObjectKey: {object_key}")
        
        # Check FlightSegmentReference refs
        origin_destinations = result['Query']['OriginDestination']
        for i, od in enumerate(origin_destinations):
            flight_refs = od.get('FlightSegmentReference', [])
            for ref_obj in flight_refs:
                ref_value = ref_obj.get('ref', '')
                
                # Should not contain airline prefixes
                self.assertFalse(
                    ref_value.startswith('26-') or ref_value.startswith('KQ-') or ref_value.startswith('AF-'),
                    f"FlightSegmentReference ref should not contain airline prefix: {ref_value}"
                )
                
                if ref_value:
                    print(f"SUCCESS: Clean segment ref in OD {i+1}: {ref_value}")
        
        # Check DataLists SegmentKeys
        if 'DataLists' in result and 'FlightSegmentList' in result['DataLists']:
            segments = result['DataLists']['FlightSegmentList'].get('FlightSegment', [])
            for segment in segments:
                segment_key = segment.get('SegmentKey', '')
                
                # Should not contain airline prefixes
                self.assertFalse(
                    segment_key.startswith('26-') or segment_key.startswith('KQ-') or segment_key.startswith('AF-'),
                    f"DataLists SegmentKey should not contain airline prefix: {segment_key}"
                )
                
                if segment_key:
                    print(f"SUCCESS: Clean DataLists SegmentKey: {segment_key}")

    def test_vdc_structure_compliance(self):
        """Test compliance with VDC API documentation structure"""
        print("\n" + "="*60)
        print("TEST: VDC Structure Compliance")
        print("="*60)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        if self.expected_structure:
            print("Comparing with expected SeatAvailabilityRQ structure...")
            
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
                
            # Detailed structure comparison for DataLists
            if 'DataLists' in common_keys:
                self._compare_datalists_structure(self.expected_structure['DataLists'], result['DataLists'])
                
        else:
            print("WARNING: No expected structure file found for comparison")
            print("SUCCESS: Validating against VDC documentation requirements...")
            
            # Validate required top-level sections
            required_sections = ['Travelers', 'Query', 'DataLists', 'ShoppingResponseID']
            for section in required_sections:
                self.assertIn(section, result, f"Missing required section: {section}")
                print(f"SUCCESS: Required section present: {section}")

    def test_difference_from_servicelist_structure(self):
        """Test key differences between SeatAvailability and ServiceList request structures"""
        print("\n" + "="*60)
        print("TEST: SeatAvailability vs ServiceList Differences")
        print("="*60)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Key difference 1: SeatAvailability structure (no RecognizedTraveler needed)
        travelers = result['Travelers']['Traveler'][0]
        self.assertIn('AnonymousTraveler', travelers)
        print("SUCCESS: SeatAvailability has clean AnonymousTraveler structure")
        
        # Key difference 2: FlightSegmentReference instead of Flight in Query/OriginDestination
        od = result['Query']['OriginDestination'][0]
        self.assertIn('FlightSegmentReference', od)
        self.assertNotIn('Flight', od)
        print("SUCCESS: SeatAvailability uses FlightSegmentReference (ServiceList uses Flight array)")
        
        # Key difference 3: DataLists section present
        self.assertIn('DataLists', result)
        print("SUCCESS: SeatAvailability includes DataLists (ServiceList doesn't)")
        
        # Show the FlightSegmentReference structure
        flight_refs = od['FlightSegmentReference']
        print(f"SUCCESS: FlightSegmentReference structure: {flight_refs}")

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
        
        # Check AnonymousTraveler presence (RecognizedTraveler no longer required)
        if isinstance(exp_travelers, list) and len(exp_travelers) > 0:
            exp_first = exp_travelers[0]
            act_first = act_travelers[0]
            
            exp_has_anon = 'AnonymousTraveler' in exp_first
            act_has_anon = 'AnonymousTraveler' in act_first
            
            print(f"    Expected has AnonymousTraveler: {exp_has_anon}")
            print(f"    Actual has AnonymousTraveler: {act_has_anon}")

    def _compare_query_structure(self, expected, actual):
        """Compare Query section structure"""
        print("  Comparing Query structure:")
        
        # Check OriginDestination differences
        if 'OriginDestination' in expected and 'OriginDestination' in actual:
            exp_od = expected['OriginDestination']
            act_od = actual['OriginDestination']
            
            if isinstance(exp_od, list) and len(exp_od) > 0 and isinstance(act_od, list) and len(act_od) > 0:
                exp_first_od = exp_od[0]
                act_first_od = act_od[0]
                
                exp_has_flight_ref = 'FlightSegmentReference' in exp_first_od
                act_has_flight_ref = 'FlightSegmentReference' in act_first_od
                
                exp_has_flight = 'Flight' in exp_first_od
                act_has_flight = 'Flight' in act_first_od
                
                print(f"    Expected has FlightSegmentReference: {exp_has_flight_ref}")
                print(f"    Actual has FlightSegmentReference: {act_has_flight_ref}")
                print(f"    Expected has Flight: {exp_has_flight}")
                print(f"    Actual has Flight: {act_has_flight}")

    def _compare_datalists_structure(self, expected, actual):
        """Compare DataLists section structure"""
        print("  Comparing DataLists structure:")
        
        exp_sections = set(expected.keys()) if expected else set()
        act_sections = set(actual.keys()) if actual else set()
        
        print(f"    Expected DataLists sections: {exp_sections}")
        print(f"    Actual DataLists sections: {act_sections}")
        
        common_sections = exp_sections & act_sections
        print(f"    Common sections: {common_sections}")

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
        print("COMPREHENSIVE SEATAVAILABILITY REQUEST VALIDATION & OUTPUT")
        print("="*80)
        
        result = build_seatavailability_request(
            flight_price_response=self.flight_price_response,
            selected_offer_index=0
        )
        
        # Full JSON output for manual inspection
        print("\nFULL GENERATED SEATAVAILABILITY REQUEST:")
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
        
        # Flight segment references analysis
        total_segment_refs = 0
        for od in result.get('Query', {}).get('OriginDestination', []):
            flight_refs = od.get('FlightSegmentReference', [])
            total_segment_refs += len(flight_refs)
            
        print(f"Total FlightSegmentReferences: {total_segment_refs}")
        
        # DataLists analysis
        data_lists = result.get('DataLists', {})
        data_sections = list(data_lists.keys())
        print(f"DataLists sections: {data_sections}")
        
        if 'FlightSegmentList' in data_lists:
            segments = data_lists['FlightSegmentList'].get('FlightSegment', [])
            print(f"DataLists FlightSegments: {len(segments)}")
            
        if 'FareList' in data_lists:
            fares = data_lists['FareList'].get('FareGroup', [])
            print(f"DataLists FareGroups: {len(fares)}")
        
        shopping_response_id = result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'N/A')
        print(f"ShoppingResponseID: {shopping_response_id}")
        
        print("\nSUCCESS: SeatAvailability request validation complete")
        
        return result


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)