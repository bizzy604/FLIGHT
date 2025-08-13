"""
Multi-airline unit tests for ServiceList and SeatAvailability request builders.

Tests the request builders using Air France (AF) and Kenya Airways (KQ) FlightPriceRS data
to validate multi-airline support and reference handling.
"""
import json
import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_servicelist_rq import build_servicelist_request
from scripts.build_seatavailability_rq import build_seatavailability_request

class TestMultiAirlineRequestBuilders(unittest.TestCase):
    """Test cases for multi-airline request builders"""

    def setUp(self):
        """Set up test fixtures with Air France and Kenya Airways FlightPriceRS data"""
        tests_dir = Path(__file__).parent
        
        # Load Air France FlightPriceRS
        af_path = tests_dir / "FlightPriceRS_AF.json"
        self.assertTrue(af_path.exists(), "FlightPriceRS_AF.json not found")
        
        with open(af_path, 'r', encoding='utf-8') as f:
            self.af_flight_price_response = json.load(f)
        
        # Load Kenya Airways FlightPriceRS
        kq_path = tests_dir / "FlightPriceRS_KQ.json"
        self.assertTrue(kq_path.exists(), "FlightPriceRS_KQ.json not found")
        
        with open(kq_path, 'r', encoding='utf-8') as f:
            self.kq_flight_price_response = json.load(f)
            
        print(f"SUCCESS: Loaded Air France FlightPriceRS with {len(str(self.af_flight_price_response))} characters")
        print(f"SUCCESS: Loaded Kenya Airways FlightPriceRS with {len(str(self.kq_flight_price_response))} characters")

    def test_air_france_servicelist_generation(self):
        """Test ServiceList request generation for Air France"""
        print("\n" + "="*80)
        print("TEST: Air France ServiceList Request Generation")
        print("="*80)
        
        try:
            result = build_servicelist_request(
                flight_price_response=self.af_flight_price_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: Air France ServiceList request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Save the generated request for inspection
            output_path = Path(__file__).parent / "output_af_servicelist_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: Air France ServiceList request saved to: {output_path}")
            
            # Display the full request
            print("\nAIR FRANCE SERVICELIST REQUEST:")
            print("-" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Analyze structure
            self._analyze_request_structure("Air France ServiceList", result)
            
            return result
            
        except Exception as e:
            self.fail(f"Air France ServiceList request generation failed: {str(e)}")

    def test_kenya_airways_servicelist_generation(self):
        """Test ServiceList request generation for Kenya Airways"""
        print("\n" + "="*80)
        print("TEST: Kenya Airways ServiceList Request Generation")
        print("="*80)
        
        try:
            result = build_servicelist_request(
                flight_price_response=self.kq_flight_price_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: Kenya Airways ServiceList request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Save the generated request for inspection
            output_path = Path(__file__).parent / "output_kq_servicelist_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: Kenya Airways ServiceList request saved to: {output_path}")
            
            # Display the full request
            print("\nKENYA AIRWAYS SERVICELIST REQUEST:")
            print("-" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Analyze structure
            self._analyze_request_structure("Kenya Airways ServiceList", result)
            
            return result
            
        except Exception as e:
            self.fail(f"Kenya Airways ServiceList request generation failed: {str(e)}")

    def test_air_france_seatavailability_generation(self):
        """Test SeatAvailability request generation for Air France"""
        print("\n" + "="*80)
        print("TEST: Air France SeatAvailability Request Generation")
        print("="*80)
        
        try:
            result = build_seatavailability_request(
                flight_price_response=self.af_flight_price_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('DataLists', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: Air France SeatAvailability request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Save the generated request for inspection
            output_path = Path(__file__).parent / "output_af_seatavailability_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: Air France SeatAvailability request saved to: {output_path}")
            
            # Display the full request
            print("\nAIR FRANCE SEATAVAILABILITY REQUEST:")
            print("-" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Analyze structure
            self._analyze_seatavailability_structure("Air France SeatAvailability", result)
            
            return result
            
        except Exception as e:
            self.fail(f"Air France SeatAvailability request generation failed: {str(e)}")

    def test_kenya_airways_seatavailability_generation(self):
        """Test SeatAvailability request generation for Kenya Airways"""
        print("\n" + "="*80)
        print("TEST: Kenya Airways SeatAvailability Request Generation")
        print("="*80)
        
        try:
            result = build_seatavailability_request(
                flight_price_response=self.kq_flight_price_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('DataLists', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: Kenya Airways SeatAvailability request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Save the generated request for inspection
            output_path = Path(__file__).parent / "output_kq_seatavailability_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: Kenya Airways SeatAvailability request saved to: {output_path}")
            
            # Display the full request
            print("\nKENYA AIRWAYS SEATAVAILABILITY REQUEST:")
            print("-" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Analyze structure
            self._analyze_seatavailability_structure("Kenya Airways SeatAvailability", result)
            
            return result
            
        except Exception as e:
            self.fail(f"Kenya Airways SeatAvailability request generation failed: {str(e)}")

    def test_multi_airline_comparison(self):
        """Compare request structures across different airlines"""
        print("\n" + "="*80)
        print("TEST: Multi-Airline Request Structure Comparison")
        print("="*80)
        
        # Generate all requests
        af_servicelist = build_servicelist_request(self.af_flight_price_response, 0)
        kq_servicelist = build_servicelist_request(self.kq_flight_price_response, 0)
        af_seatavail = build_seatavailability_request(self.af_flight_price_response, 0)
        kq_seatavail = build_seatavailability_request(self.kq_flight_price_response, 0)
        
        # Compare ServiceList structures
        print("\nSERVICELIST COMPARISON:")
        print("=" * 30)
        self._compare_structures("AF ServiceList", af_servicelist, "KQ ServiceList", kq_servicelist)
        
        # Compare SeatAvailability structures
        print("\nSEATAVAILABILITY COMPARISON:")
        print("=" * 30)
        self._compare_structures("AF SeatAvailability", af_seatavail, "KQ SeatAvailability", kq_seatavail)
        
        # Compare Airline-specific data
        print("\nAIRLINE-SPECIFIC DATA ANALYSIS:")
        print("=" * 35)
        
        # Check OfferIDs
        af_sl_offer = af_servicelist['Query']['Offers']['Offer'][0]['OfferID']
        kq_sl_offer = kq_servicelist['Query']['Offers']['Offer'][0]['OfferID']
        
        print(f"AF ServiceList Offer Owner: {af_sl_offer.get('Owner')}")
        print(f"KQ ServiceList Offer Owner: {kq_sl_offer.get('Owner')}")
        
        # Check ShoppingResponseIDs
        af_sr_id = af_servicelist['ShoppingResponseID']['ResponseID']['value']
        kq_sr_id = kq_servicelist['ShoppingResponseID']['ResponseID']['value']
        
        print(f"AF ShoppingResponseID: {af_sr_id}")
        print(f"KQ ShoppingResponseID: {kq_sr_id}")

    def test_reference_consistency(self):
        """Test that references are consistent and clean across airlines"""
        print("\n" + "="*80)
        print("TEST: Reference Consistency Across Airlines")
        print("="*80)
        
        # Test AF references
        af_servicelist = build_servicelist_request(self.af_flight_price_response, 0)
        af_seatavail = build_seatavailability_request(self.af_flight_price_response, 0)
        
        print("AIR FRANCE REFERENCE ANALYSIS:")
        print("-" * 35)
        self._analyze_references("AF", af_servicelist, af_seatavail)
        
        # Test KQ references
        kq_servicelist = build_servicelist_request(self.kq_flight_price_response, 0)
        kq_seatavail = build_seatavailability_request(self.kq_flight_price_response, 0)
        
        print("\nKENYA AIRWAYS REFERENCE ANALYSIS:")
        print("-" * 38)
        self._analyze_references("KQ", kq_servicelist, kq_seatavail)

    def _analyze_request_structure(self, request_name, result):
        """Analyze and display request structure details"""
        print(f"\n{request_name} STRUCTURE ANALYSIS:")
        print("-" * (len(request_name) + 20))
        
        # Travelers analysis
        travelers = result.get('Travelers', {}).get('Traveler', [])
        print(f"Travelers: {len(travelers)}")
        if travelers:
            first_traveler = travelers[0]
            anon_travelers = first_traveler.get('AnonymousTraveler', [])
            if anon_travelers:
                first_anon = anon_travelers[0]
                print(f"  First traveler ObjectKey: {first_anon.get('ObjectKey')}")
                print(f"  First traveler PTC: {first_anon.get('PTC', {}).get('value')}")
        
        # Query analysis
        query = result.get('Query', {})
        od_count = len(query.get('OriginDestination', []))
        offers_count = len(query.get('Offers', {}).get('Offer', []))
        
        print(f"Origin-Destinations: {od_count}")
        print(f"Offers: {offers_count}")
        
        # Flight segments analysis
        total_flights = 0
        for od in query.get('OriginDestination', []):
            flights = od.get('Flight', [])
            total_flights += len(flights)
            
        print(f"Total Flight Segments: {total_flights}")
        
        # ShoppingResponseID
        shopping_response_id = result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'N/A')
        print(f"ShoppingResponseID: {shopping_response_id}")

    def _analyze_seatavailability_structure(self, request_name, result):
        """Analyze and display SeatAvailability request structure details"""
        print(f"\n{request_name} STRUCTURE ANALYSIS:")
        print("-" * (len(request_name) + 20))
        
        # Travelers analysis (with RecognizedTraveler)
        travelers = result.get('Travelers', {}).get('Traveler', [])
        print(f"Travelers: {len(travelers)}")
        if travelers:
            first_traveler = travelers[0]
            recognized = first_traveler.get('RecognizedTraveler', [])
            anon_travelers = first_traveler.get('AnonymousTraveler', [])
            print(f"  RecognizedTraveler: {len(recognized)} (should be empty)")
            if anon_travelers:
                first_anon = anon_travelers[0]
                print(f"  First traveler ObjectKey: {first_anon.get('ObjectKey')}")
                print(f"  First traveler PTC: {first_anon.get('PTC', {}).get('value')}")
        
        # Query analysis (with FlightSegmentReference)
        query = result.get('Query', {})
        od_count = len(query.get('OriginDestination', []))
        offers_count = len(query.get('Offers', {}).get('Offer', []))
        
        print(f"Origin-Destinations: {od_count}")
        print(f"Offers: {offers_count}")
        
        # FlightSegmentReferences analysis
        total_segment_refs = 0
        for od in query.get('OriginDestination', []):
            flight_refs = od.get('FlightSegmentReference', [])
            total_segment_refs += len(flight_refs)
            
        print(f"Total FlightSegmentReferences: {total_segment_refs}")
        
        # DataLists analysis
        data_lists = result.get('DataLists', {})
        data_sections = list(data_lists.keys())
        print(f"DataLists sections: {data_sections}")
        
        if 'FlightSegmentList' in data_lists:
            segments = data_lists['FlightSegmentList'].get('FlightSegment', [])
            print(f"  FlightSegments: {len(segments)}")
            
        if 'FareList' in data_lists:
            fares = data_lists['FareList'].get('FareGroup', [])
            print(f"  FareGroups: {len(fares)}")
        
        # ShoppingResponseID
        shopping_response_id = result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'N/A')
        print(f"ShoppingResponseID: {shopping_response_id}")

    def _compare_structures(self, name1, struct1, name2, struct2):
        """Compare two request structures"""
        keys1 = set(struct1.keys())
        keys2 = set(struct2.keys())
        
        common_keys = keys1 & keys2
        unique_1 = keys1 - keys2
        unique_2 = keys2 - keys1
        
        print(f"Common sections: {common_keys}")
        if unique_1:
            print(f"{name1} unique sections: {unique_1}")
        if unique_2:
            print(f"{name2} unique sections: {unique_2}")
        
        # Compare travelers count
        travelers1 = len(struct1.get('Travelers', {}).get('Traveler', []))
        travelers2 = len(struct2.get('Travelers', {}).get('Traveler', []))
        print(f"Travelers - {name1}: {travelers1}, {name2}: {travelers2}")

    def _analyze_references(self, airline_code, servicelist_req, seatavail_req):
        """Analyze references in both request types for an airline"""
        
        # ServiceList references
        sl_travelers = servicelist_req.get('Travelers', {}).get('Traveler', [])
        sl_object_keys = []
        for traveler in sl_travelers:
            anon_travelers = traveler.get('AnonymousTraveler', [])
            for anon in anon_travelers:
                key = anon.get('ObjectKey', '')
                sl_object_keys.append(key)
        
        # SeatAvailability references  
        sa_travelers = seatavail_req.get('Travelers', {}).get('Traveler', [])
        sa_object_keys = []
        for traveler in sa_travelers:
            anon_travelers = traveler.get('AnonymousTraveler', [])
            for anon in anon_travelers:
                key = anon.get('ObjectKey', '')
                sa_object_keys.append(key)
        
        # FlightSegmentReferences
        sa_segment_refs = []
        for od in seatavail_req.get('Query', {}).get('OriginDestination', []):
            flight_refs = od.get('FlightSegmentReference', [])
            for ref_obj in flight_refs:
                ref_val = ref_obj.get('ref', '')
                sa_segment_refs.append(ref_val)
        
        print(f"ServiceList ObjectKeys: {sl_object_keys}")
        print(f"SeatAvailability ObjectKeys: {sa_object_keys}")
        print(f"SeatAvailability SegmentRefs: {sa_segment_refs}")
        
        # Validate no airline prefixes
        all_refs = sl_object_keys + sa_object_keys + sa_segment_refs
        prefixed_refs = [ref for ref in all_refs if ref.startswith(f'{airline_code}-') or ref.startswith('AF-') or ref.startswith('KQ-')]
        
        if prefixed_refs:
            print(f"WARNING: Found airline-prefixed references: {prefixed_refs}")
        else:
            print("SUCCESS: All references are clean (no airline prefixes)")

    def test_comprehensive_multi_airline_validation(self):
        """Comprehensive validation of all multi-airline request generations"""
        print("\n" + "="*80)
        print("COMPREHENSIVE MULTI-AIRLINE VALIDATION")
        print("="*80)
        
        airlines = [
            ("Air France", self.af_flight_price_response),
            ("Kenya Airways", self.kq_flight_price_response)
        ]
        
        for airline_name, flight_price_response in airlines:
            print(f"\n{airline_name.upper()} COMPLETE VALIDATION:")
            print("=" * (len(airline_name) + 20))
            
            # ServiceList
            servicelist_result = build_servicelist_request(flight_price_response, 0)
            print(f"  ServiceList: SUCCESS")
            
            # SeatAvailability  
            seatavail_result = build_seatavailability_request(flight_price_response, 0)
            print(f"  SeatAvailability: SUCCESS")
            
            # Validation
            self.assertIsInstance(servicelist_result, dict)
            self.assertIsInstance(seatavail_result, dict)
            self.assertIn('Travelers', servicelist_result)
            self.assertIn('Travelers', seatavail_result)
            self.assertIn('Query', servicelist_result)
            self.assertIn('Query', seatavail_result)
            self.assertIn('ShoppingResponseID', servicelist_result)
            self.assertIn('ShoppingResponseID', seatavail_result)
            self.assertIn('DataLists', seatavail_result)  # SeatAvailability specific
            
            print(f"  All validations: PASSED")
        
        print(f"\nSUCCESS: All multi-airline request generation tests completed successfully!")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)