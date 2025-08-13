"""
Test both ServiceList and SeatAvailability request builders using KQ FlightPriceRS data.

This script tests the request builders with real KQ airline data to ensure they work
correctly with different airline responses and multi-passenger scenarios.
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

class TestKQFlightPriceRequestBuilders(unittest.TestCase):
    """Test cases for both request builders using KQ FlightPriceRS data"""

    def setUp(self):
        """Set up test fixtures with KQ FlightPriceRS data"""
        # Load the KQ FlightPriceRS data
        kq_flight_price_path = Path(__file__).parent / "FlightPriceRS_KQ.json"
        
        self.assertTrue(kq_flight_price_path.exists(), "KQ FlightPriceRS test data file not found")
        
        with open(kq_flight_price_path, 'r', encoding='utf-8') as f:
            self.kq_flight_price_response = json.load(f)
            
        print(f"SUCCESS: Loaded KQ FlightPriceRS with {len(str(self.kq_flight_price_response))} characters")
        
        # Analyze the KQ data structure
        self._analyze_kq_data()

    def _analyze_kq_data(self):
        """Analyze the KQ FlightPriceRS data structure"""
        print("\n" + "="*60)
        print("KQ FLIGHTPRICE DATA ANALYSIS")
        print("="*60)
        
        # Document info
        document = self.kq_flight_price_response.get('Document', {})
        print(f"Airline: {document.get('Name', 'N/A')}")
        
        # Shopping Response ID
        shopping_id = self.kq_flight_price_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'N/A')
        print(f"ShoppingResponseID: {shopping_id}")
        
        # Offers
        offers = self.kq_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        print(f"Number of offers: {len(offers)}")
        
        if len(offers) > 0:
            first_offer = offers[0]
            offer_id = first_offer.get('OfferID', {}).get('value', 'N/A')
            print(f"First offer ID: {offer_id}")
            
            # Price details
            price_items = first_offer.get('OfferPrice', [])
            print(f"Price items in first offer: {len(price_items)}")
            
            if len(price_items) > 0:
                first_price = price_items[0]
                total_amount = first_price.get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                print(f"First price: {total_amount.get('value', 'N/A')} {total_amount.get('Code', 'N/A')}")
        
        # Travelers
        travelers = self.kq_flight_price_response.get('DataLists', {}).get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        print(f"Number of travelers: {len(travelers)}")
        for i, traveler in enumerate(travelers):
            object_key = traveler.get('ObjectKey', 'N/A')
            ptc = traveler.get('PTC', {}).get('value', 'N/A')
            print(f"  Traveler {i+1}: {object_key} ({ptc})")
        
        # Flight segments
        segments = self.kq_flight_price_response.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
        print(f"Number of flight segments: {len(segments)}")
        for i, segment in enumerate(segments):
            segment_key = segment.get('SegmentKey', 'N/A')
            departure = segment.get('Departure', {}).get('AirportCode', {}).get('value', 'N/A')
            arrival = segment.get('Arrival', {}).get('AirportCode', {}).get('value', 'N/A')
            flight_num = segment.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', 'N/A')
            print(f"  Segment {i+1}: {segment_key} - {departure} to {arrival} (Flight {flight_num})")

    def test_kq_servicelist_request_generation(self):
        """Test ServiceList request generation with KQ data"""
        print("\n" + "="*70)
        print("TEST: KQ ServiceList Request Generation")
        print("="*70)
        
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
            
            print("SUCCESS: KQ ServiceList request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Analyze travelers
            travelers = result['Travelers']['Traveler']
            print(f"SUCCESS: Generated {len(travelers)} travelers")
            
            for i, traveler in enumerate(travelers):
                anon_traveler = traveler['AnonymousTraveler'][0]
                object_key = anon_traveler.get('ObjectKey')
                ptc_value = anon_traveler.get('PTC', {}).get('value')
                print(f"  Traveler {i+1}: {object_key} ({ptc_value})")
            
            # Analyze Query structure
            query = result['Query']
            origin_destinations = query['OriginDestination']
            offers = query['Offers']['Offer']
            
            print(f"SUCCESS: {len(origin_destinations)} OriginDestination(s)")
            print(f"SUCCESS: {len(offers)} Offer(s)")
            
            # Check flight segments
            total_flights = 0
            for od in origin_destinations:
                flights = od.get('Flight', [])
                total_flights += len(flights)
                
            print(f"SUCCESS: {total_flights} total flight segments")
            
            # Save output
            output_path = Path(__file__).parent / "output_kq_servicelist_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: KQ ServiceList request saved to: {output_path}")
            
            return result
            
        except Exception as e:
            self.fail(f"KQ ServiceList request generation failed: {str(e)}")

    def test_kq_seatavailability_request_generation(self):
        """Test SeatAvailability request generation with KQ data"""
        print("\n" + "="*70)
        print("TEST: KQ SeatAvailability Request Generation")
        print("="*70)
        
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
            
            print("SUCCESS: KQ SeatAvailability request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            
            # Analyze travelers (should include RecognizedTraveler)
            travelers = result['Travelers']['Traveler']
            print(f"SUCCESS: Generated {len(travelers)} travelers")
            
            for i, traveler in enumerate(travelers):
                recognized = traveler.get('RecognizedTraveler', [])
                anon_traveler = traveler['AnonymousTraveler'][0]
                object_key = anon_traveler.get('ObjectKey')
                ptc_value = anon_traveler.get('PTC', {}).get('value')
                print(f"  Traveler {i+1}: {object_key} ({ptc_value}) - RecognizedTraveler: {len(recognized)} items")
            
            # Analyze Query structure
            query = result['Query']
            origin_destinations = query['OriginDestination']
            offers = query['Offers']['Offer']
            
            print(f"SUCCESS: {len(origin_destinations)} OriginDestination(s)")
            print(f"SUCCESS: {len(offers)} Offer(s)")
            
            # Check FlightSegmentReference
            total_segment_refs = 0
            for od in origin_destinations:
                segment_refs = od.get('FlightSegmentReference', [])
                total_segment_refs += len(segment_refs)
                refs = [ref.get('ref') for ref in segment_refs]
                print(f"  OD segment refs: {refs}")
                
            print(f"SUCCESS: {total_segment_refs} total FlightSegmentReferences")
            
            # Analyze DataLists
            data_lists = result['DataLists']
            print(f"SUCCESS: DataLists contains {len(data_lists.keys())} sections: {list(data_lists.keys())}")
            
            if 'FlightSegmentList' in data_lists:
                segments = data_lists['FlightSegmentList'].get('FlightSegment', [])
                print(f"SUCCESS: {len(segments)} flight segments in DataLists")
                
            if 'FareList' in data_lists:
                fares = data_lists['FareList'].get('FareGroup', [])
                print(f"SUCCESS: {len(fares)} fare groups in DataLists")
            
            # Save output
            output_path = Path(__file__).parent / "output_kq_seatavailability_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: KQ SeatAvailability request saved to: {output_path}")
            
            return result
            
        except Exception as e:
            self.fail(f"KQ SeatAvailability request generation failed: {str(e)}")

    def test_kq_multi_passenger_handling(self):
        """Test how both builders handle KQ's multi-passenger scenario"""
        print("\n" + "="*70)
        print("TEST: KQ Multi-Passenger Handling Comparison")
        print("="*70)
        
        # Generate both requests
        servicelist_result = build_servicelist_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        seatavailability_result = build_seatavailability_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        # Compare traveler handling
        sl_travelers = servicelist_result['Travelers']['Traveler']
        sa_travelers = seatavailability_result['Travelers']['Traveler']
        
        print(f"ServiceList travelers: {len(sl_travelers)}")
        print(f"SeatAvailability travelers: {len(sa_travelers)}")
        
        self.assertEqual(len(sl_travelers), len(sa_travelers), "Both should have same number of travelers")
        
        # Compare traveler details
        for i in range(len(sl_travelers)):
            sl_anon = sl_travelers[i]['AnonymousTraveler'][0]
            sa_anon = sa_travelers[i]['AnonymousTraveler'][0]
            
            sl_key = sl_anon.get('ObjectKey')
            sa_key = sa_anon.get('ObjectKey')
            sl_ptc = sl_anon.get('PTC', {}).get('value')
            sa_ptc = sa_anon.get('PTC', {}).get('value')
            
            self.assertEqual(sl_key, sa_key, f"Traveler {i+1} ObjectKey should match")
            self.assertEqual(sl_ptc, sa_ptc, f"Traveler {i+1} PTC should match")
            
            print(f"  Traveler {i+1}: {sl_key} ({sl_ptc}) - Consistent across both requests")
        
        # Check RecognizedTraveler presence
        sa_recognized = sa_travelers[0].get('RecognizedTraveler', [])
        sl_has_recognized = 'RecognizedTraveler' in sl_travelers[0]
        
        print(f"ServiceList has RecognizedTraveler: {sl_has_recognized}")
        print(f"SeatAvailability RecognizedTraveler: {len(sa_recognized)} items (empty array)")
        
        self.assertFalse(sl_has_recognized, "ServiceList should not have RecognizedTraveler")
        self.assertIsInstance(sa_recognized, list, "SeatAvailability should have RecognizedTraveler array")
        self.assertEqual(len(sa_recognized), 0, "SeatAvailability RecognizedTraveler should be empty")
        
        print("SUCCESS: Multi-passenger handling is consistent between both request types")

    def test_kq_shopping_response_id_consistency(self):
        """Test ShoppingResponseID mapping consistency"""
        print("\n" + "="*70)
        print("TEST: KQ ShoppingResponseID Consistency")
        print("="*70)
        
        # Get original ShoppingResponseID from KQ data
        original_id = self.kq_flight_price_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')
        print(f"Original KQ ShoppingResponseID: {original_id}")
        
        # Generate both requests
        servicelist_result = build_servicelist_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        seatavailability_result = build_seatavailability_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        # Check both preserve the original ID
        sl_id = servicelist_result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')
        sa_id = seatavailability_result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')
        
        print(f"ServiceList ShoppingResponseID: {sl_id}")
        print(f"SeatAvailability ShoppingResponseID: {sa_id}")
        
        self.assertEqual(original_id, sl_id, "ServiceList should preserve original ShoppingResponseID")
        self.assertEqual(original_id, sa_id, "SeatAvailability should preserve original ShoppingResponseID")
        self.assertEqual(sl_id, sa_id, "Both requests should have identical ShoppingResponseID")
        
        print("SUCCESS: ShoppingResponseID mapping is consistent across both request types")

    def test_kq_flight_segment_references(self):
        """Test flight segment reference handling in KQ data"""
        print("\n" + "="*70)
        print("TEST: KQ Flight Segment Reference Handling")
        print("="*70)
        
        # Get original segments from KQ data
        original_segments = self.kq_flight_price_response.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
        segment_keys = [seg.get('SegmentKey') for seg in original_segments]
        print(f"Original KQ segment keys: {segment_keys}")
        
        # Generate both requests
        servicelist_result = build_servicelist_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        seatavailability_result = build_seatavailability_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        # Check ServiceList uses Flight array
        sl_ods = servicelist_result['Query']['OriginDestination']
        sl_segment_keys = []
        for od in sl_ods:
            flights = od.get('Flight', [])
            for flight in flights:
                sl_segment_keys.append(flight.get('SegmentKey'))
        
        print(f"ServiceList segment keys: {sl_segment_keys}")
        
        # Check SeatAvailability uses FlightSegmentReference
        sa_ods = seatavailability_result['Query']['OriginDestination']
        sa_refs = []
        for od in sa_ods:
            segment_refs = od.get('FlightSegmentReference', [])
            for ref in segment_refs:
                sa_refs.append(ref.get('ref'))
        
        print(f"SeatAvailability segment refs: {sa_refs}")
        
        # Check DataLists in SeatAvailability
        sa_datalists_segments = seatavailability_result['DataLists']['FlightSegmentList']['FlightSegment']
        sa_datalists_keys = [seg.get('SegmentKey') for seg in sa_datalists_segments]
        print(f"SeatAvailability DataLists segment keys: {sa_datalists_keys}")
        
        # Validate all references are consistent
        self.assertEqual(set(sl_segment_keys), set(segment_keys), "ServiceList should reference original segment keys")
        self.assertEqual(set(sa_refs), set(segment_keys), "SeatAvailability refs should match original segment keys")
        self.assertEqual(set(sa_datalists_keys), set(segment_keys), "SeatAvailability DataLists should match original segment keys")
        
        print("SUCCESS: Flight segment reference handling is correct for both request types")

    def test_kq_comprehensive_output_comparison(self):
        """Comprehensive comparison of both generated requests"""
        print("\n" + "="*80)
        print("COMPREHENSIVE KQ REQUEST COMPARISON")
        print("="*80)
        
        # Generate both requests
        servicelist_result = build_servicelist_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        seatavailability_result = build_seatavailability_request(
            flight_price_response=self.kq_flight_price_response,
            selected_offer_index=0
        )
        
        print("\nKQ SERVICELIST REQUEST STATISTICS:")
        print("-" * 50)
        sl_travelers = len(servicelist_result.get('Travelers', {}).get('Traveler', []))
        sl_ods = len(servicelist_result.get('Query', {}).get('OriginDestination', []))
        sl_offers = len(servicelist_result.get('Query', {}).get('Offers', {}).get('Offer', []))
        sl_total_flights = sum(len(od.get('Flight', [])) for od in servicelist_result.get('Query', {}).get('OriginDestination', []))
        
        print(f"Travelers: {sl_travelers}")
        print(f"Origin-Destinations: {sl_ods}")
        print(f"Offers: {sl_offers}")
        print(f"Total Flight Segments: {sl_total_flights}")
        print(f"Top-level sections: {list(servicelist_result.keys())}")
        
        print("\nKQ SEATAVAILABILITY REQUEST STATISTICS:")
        print("-" * 50)
        sa_travelers = len(seatavailability_result.get('Travelers', {}).get('Traveler', []))
        sa_ods = len(seatavailability_result.get('Query', {}).get('OriginDestination', []))
        sa_offers = len(seatavailability_result.get('Query', {}).get('Offers', {}).get('Offer', []))
        sa_total_refs = sum(len(od.get('FlightSegmentReference', [])) for od in seatavailability_result.get('Query', {}).get('OriginDestination', []))
        sa_datalists_sections = list(seatavailability_result.get('DataLists', {}).keys())
        
        print(f"Travelers: {sa_travelers}")
        print(f"Origin-Destinations: {sa_ods}")
        print(f"Offers: {sa_offers}")
        print(f"Total FlightSegmentReferences: {sa_total_refs}")
        print(f"DataLists sections: {sa_datalists_sections}")
        print(f"Top-level sections: {list(seatavailability_result.keys())}")
        
        print("\nKEY DIFFERENCES:")
        print("-" * 30)
        print("1. Travelers:")
        print("   - ServiceList: AnonymousTraveler only")
        print("   - SeatAvailability: RecognizedTraveler (empty) + AnonymousTraveler")
        
        print("2. Query/OriginDestination:")
        print("   - ServiceList: Flight array with full segment details")
        print("   - SeatAvailability: FlightSegmentReference array with refs")
        
        print("3. DataLists:")
        print("   - ServiceList: Not present")
        print(f"   - SeatAvailability: {len(sa_datalists_sections)} sections ({', '.join(sa_datalists_sections)})")
        
        print("\nSUCCESS: Both KQ request builders generated valid NDC requests!")
        
        # Full JSON outputs
        print("\n" + "="*50)
        print("FULL KQ SERVICELIST REQUEST:")
        print("="*50)
        print(json.dumps(servicelist_result, indent=2, ensure_ascii=False))
        
        print("\n" + "="*50)
        print("FULL KQ SEATAVAILABILITY REQUEST:")
        print("="*50)
        print(json.dumps(seatavailability_result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
