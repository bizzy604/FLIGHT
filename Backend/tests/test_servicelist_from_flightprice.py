"""
Test ServiceList request builder using the FlightPriceRS response.

This script tests the ServiceList request builder with real FlightPrice data
to ensure it works correctly with Brussels Airlines response.
"""
import json
import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_servicelist_rq import build_servicelist_request

class TestServiceListFromFlightPrice(unittest.TestCase):
    """Test cases for ServiceList request builder using FlightPriceRS data"""

    def setUp(self):
        """Set up test fixtures with FlightPriceRS response data"""
        # Load the FlightPriceRS response data
        flightprice_path = Path(__file__).parent.parent / "Seats & Services" / "4_FlightPriceRS.json"
        
        self.assertTrue(flightprice_path.exists(), "FlightPrice response test data file not found")
        
        with open(flightprice_path, 'r', encoding='utf-8') as f:
            self.flightprice_response = json.load(f)
            
        print(f"SUCCESS: Loaded FlightPrice response with {len(str(self.flightprice_response))} characters")
        
        # Analyze the FlightPrice data structure
        self._analyze_flightprice_data()

    def _analyze_flightprice_data(self):
        """Analyze the FlightPrice response data structure"""
        print("\n" + "="*60)
        print("FLIGHTPRICE RESPONSE DATA ANALYSIS")
        print("="*60)
        
        # Check for warnings
        warnings = self.flightprice_response.get('Warnings', {}).get('Warning', [])
        print(f"Warnings: {len(warnings)} warnings")
        for warning in warnings:
            short_text = warning.get('ShortText', 'N/A')
            print(f"  Warning: {short_text}")
        
        # Check ShoppingResponseID
        shopping_response_id = self.flightprice_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'N/A')
        print(f"ShoppingResponseID: {shopping_response_id}")
        
        # Check PricedFlightOffers
        priced_offers = self.flightprice_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        print(f"PricedFlightOffers: {len(priced_offers)} offer(s)")
        
        if priced_offers:
            first_offer = priced_offers[0]
            offer_id = first_offer.get('OfferID', {})
            print(f"First offer ID: {offer_id.get('value', 'N/A')} (Owner: {offer_id.get('Owner', 'N/A')})")
            
            # Check offer prices
            offer_prices = first_offer.get('OfferPrice', [])
            print(f"Offer prices: {len(offer_prices)} price item(s)")
            
            if offer_prices:
                first_price = offer_prices[0].get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                print(f"Total amount: {first_price.get('value', 'N/A')} {first_price.get('Code', 'N/A')}")
        
        # Check DataLists
        data_lists = self.flightprice_response.get('DataLists', {})
        print(f"DataLists sections: {list(data_lists.keys())}")
        
        # Travelers
        travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        print(f"Anonymous travelers: {len(travelers)}")
        if travelers:
            for i, traveler in enumerate(travelers):
                object_key = traveler.get('ObjectKey', 'N/A')
                ptc = traveler.get('PTC', {}).get('value', 'N/A')
                print(f"  Traveler {i+1}: {object_key} ({ptc})")
        
        # Flight segments
        segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        print(f"Flight segments: {len(segments)}")
        if segments:
            for i, segment in enumerate(segments):
                segment_key = segment.get('SegmentKey', 'N/A')
                departure = segment.get('Departure', {}).get('AirportCode', {}).get('value', 'N/A')
                arrival = segment.get('Arrival', {}).get('AirportCode', {}).get('value', 'N/A')
                flight_num = segment.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', 'N/A')
                aircraft = segment.get('Equipment', {}).get('Name', 'N/A')
                print(f"  Segment {i+1}: {segment_key} - {departure} to {arrival} (Flight {flight_num}, {aircraft})")
        
        # Services
        services = data_lists.get('ServiceList', {}).get('Service', [])
        print(f"Services: {len(services)}")
        if services:
            for i, service in enumerate(services):
                service_name = service.get('Name', {}).get('value', 'N/A')
                service_id = service.get('ServiceID', {}).get('value', 'N/A')
                print(f"  Service {i+1}: {service_name} (ID: {service_id})")

    def test_servicelist_request_generation(self):
        """Test ServiceList request generation from FlightPriceRS"""
        print("\n" + "="*70)
        print("TEST: ServiceList Request Generation from FlightPriceRS")
        print("="*70)
        
        try:
            # Build ServiceList request for first offer (index 0)
            result = build_servicelist_request(
                flight_price_response=self.flightprice_response,
                selected_offer_index=0
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Travelers', result)
            self.assertIn('Query', result)
            self.assertIn('ShoppingResponseID', result)
            
            print("SUCCESS: ServiceList request generated successfully")
            print(f"SUCCESS: Request contains {len(result.keys())} top-level sections")
            print(f"Top-level sections: {list(result.keys())}")
            
            # Analyze Travelers
            travelers = result.get('Travelers', {}).get('Traveler', [])
            print(f"SUCCESS: Generated {len(travelers)} traveler(s)")
            
            for i, traveler in enumerate(travelers):
                anon_traveler = traveler['AnonymousTraveler'][0]
                object_key = anon_traveler.get('ObjectKey')
                ptc_value = anon_traveler.get('PTC', {}).get('value')
                print(f"  Traveler {i+1}: {object_key} ({ptc_value})")
            
            # Analyze Query structure
            query = result.get('Query', {})
            if 'OriginDestination' in query:
                ods = query['OriginDestination']
                print(f"SUCCESS: {len(ods)} OriginDestination(s)")
                
                # Analyze flights in each OD
                total_flights = 0
                for i, od in enumerate(ods):
                    flights = od.get('Flight', [])
                    total_flights += len(flights)
                    print(f"  OD {i+1}: {len(flights)} flight(s)")
                    
                    for j, flight in enumerate(flights):
                        segment_key = flight.get('SegmentKey')
                        departure = flight.get('Departure', {}).get('AirportCode', {}).get('value')
                        arrival = flight.get('Arrival', {}).get('AirportCode', {}).get('value')
                        flight_num = flight.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value')
                        print(f"    Flight {j+1}: {segment_key} - {departure} to {arrival} (Flight {flight_num})")
                
                print(f"SUCCESS: {total_flights} total flight segments")
            
            if 'Offers' in query:
                offers = query['Offers'].get('Offer', [])
                print(f"SUCCESS: {len(offers)} offer(s)")
                
                for i, offer in enumerate(offers):
                    offer_id = offer.get('OfferID', {})
                    offer_items = offer.get('OfferItemIDs', {}).get('OfferItemID', [])
                    print(f"  Offer {i+1}: {offer_id.get('value', 'N/A')} ({offer_id.get('Owner', 'N/A')}) - {len(offer_items)} items")
            
            # Check ShoppingResponseID
            shopping_id = result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')
            print(f"SUCCESS: ShoppingResponseID: {shopping_id}")
            
            # Save output
            output_path = Path(__file__).parent / "output_servicelist_from_flightprice.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: ServiceList request saved to: {output_path}")
            
            return result
            
        except Exception as e:
            print(f"ERROR: ServiceList request generation failed: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise e

    def test_servicelist_structure_validation(self):
        """Test comprehensive structure validation of generated ServiceList request"""
        print("\n" + "="*70)
        print("TEST: ServiceList Request Structure Validation")
        print("="*70)
        
        try:
            result = build_servicelist_request(
                flight_price_response=self.flightprice_response,
                selected_offer_index=0
            )
            
            # Validate top-level structure
            required_sections = ['Travelers', 'Query', 'ShoppingResponseID']
            for section in required_sections:
                self.assertIn(section, result, f"Missing required section: {section}")
                print(f"✓ Required section present: {section}")
            
            # Validate Travelers structure
            travelers = result['Travelers'].get('Traveler', [])
            self.assertGreater(len(travelers), 0, "No travelers in request")
            
            first_traveler = travelers[0]
            self.assertIn('AnonymousTraveler', first_traveler, "Traveler missing AnonymousTraveler")
            
            anon_traveler = first_traveler['AnonymousTraveler'][0]
            self.assertIn('ObjectKey', anon_traveler, "AnonymousTraveler missing ObjectKey")
            self.assertIn('PTC', anon_traveler, "AnonymousTraveler missing PTC")
            print(f"✓ Travelers structure valid: {anon_traveler['ObjectKey']}")
            
            # Validate Query structure
            query = result['Query']
            self.assertIn('OriginDestination', query, "Query missing OriginDestination")
            self.assertIn('Offers', query, "Query missing Offers")
            print("✓ Query structure valid")
            
            # Validate OriginDestination structure
            ods = query['OriginDestination']
            self.assertGreater(len(ods), 0, "No OriginDestinations in Query")
            
            first_od = ods[0]
            self.assertIn('Flight', first_od, "OriginDestination missing Flight")
            
            flights = first_od['Flight']
            self.assertGreater(len(flights), 0, "No flights in OriginDestination")
            
            first_flight = flights[0]
            required_flight_fields = ['SegmentKey', 'Departure', 'Arrival', 'MarketingCarrier']
            for field in required_flight_fields:
                self.assertIn(field, first_flight, f"Flight missing {field}")
            print("✓ OriginDestination structure valid")
            
            # Validate Offers structure
            offers = query['Offers'].get('Offer', [])
            self.assertGreater(len(offers), 0, "No offers in Query")
            
            first_offer = offers[0]
            self.assertIn('OfferID', first_offer, "Offer missing OfferID")
            self.assertIn('OfferItemIDs', first_offer, "Offer missing OfferItemIDs")
            
            offer_id = first_offer['OfferID']
            required_offer_fields = ['value', 'Owner', 'Channel']
            for field in required_offer_fields:
                self.assertIn(field, offer_id, f"OfferID missing {field}")
            print(f"✓ Offers structure valid: {offer_id['value']} (Owner: {offer_id['Owner']})")
            
            # Validate ShoppingResponseID structure
            shopping_id = result['ShoppingResponseID']
            self.assertIn('ResponseID', shopping_id, "ShoppingResponseID missing ResponseID")
            
            response_id = shopping_id['ResponseID']
            self.assertIn('value', response_id, "ResponseID missing value")
            print(f"✓ ShoppingResponseID structure valid: {response_id['value']}")
            
            print("SUCCESS: ServiceList request structure validation completed")
            
        except Exception as e:
            self.fail(f"Structure validation failed: {str(e)}")

    def test_servicelist_comprehensive_output(self):
        """Generate comprehensive ServiceList request output and analysis"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SERVICELIST REQUEST OUTPUT")
        print("="*80)
        
        try:
            result = build_servicelist_request(
                flight_price_response=self.flightprice_response,
                selected_offer_index=0
            )
            
            print("\nSERVICELIST REQUEST STATISTICS:")
            print("-" * 50)
            
            # Top-level sections
            print(f"Top-level sections: {list(result.keys())}")
            
            # Travelers analysis
            travelers = result.get('Travelers', {}).get('Traveler', [])
            print(f"Travelers: {len(travelers)}")
            
            for i, traveler in enumerate(travelers):
                anon_traveler = traveler['AnonymousTraveler'][0]
                object_key = anon_traveler.get('ObjectKey')
                ptc_value = anon_traveler.get('PTC', {}).get('value')
                print(f"  Traveler {i+1}: {object_key} ({ptc_value})")
            
            # Query analysis
            query = result.get('Query', {})
            if 'OriginDestination' in query:
                ods = query['OriginDestination']
                print(f"Origin-Destinations: {len(ods)}")
                
                # Flight details
                total_flights = 0
                for i, od in enumerate(ods):
                    flights = od.get('Flight', [])
                    total_flights += len(flights)
                    print(f"  OD {i+1}: {len(flights)} flight(s)")
                    
                    for j, flight in enumerate(flights):
                        segment_key = flight.get('SegmentKey')
                        departure = flight.get('Departure', {}).get('AirportCode', {}).get('value')
                        arrival = flight.get('Arrival', {}).get('AirportCode', {}).get('value')
                        flight_num = flight.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value')
                        airline = flight.get('MarketingCarrier', {}).get('Name')
                        aircraft = flight.get('Equipment', {}).get('Name')
                        duration = flight.get('FlightDetail', {}).get('FlightDuration', {}).get('Value')
                        
                        print(f"    Flight {j+1}: {flight_num} ({airline})")
                        print(f"      Route: {departure} → {arrival}")
                        print(f"      Aircraft: {aircraft}")
                        print(f"      Duration: {duration}")
                        print(f"      SegmentKey: {segment_key}")
                
                print(f"Total Flight Segments: {total_flights}")
            
            if 'Offers' in query:
                offers = query['Offers'].get('Offer', [])
                print(f"Query Offers: {len(offers)}")
                
                for i, offer in enumerate(offers):
                    offer_id = offer.get('OfferID', {})
                    offer_items = offer.get('OfferItemIDs', {}).get('OfferItemID', [])
                    print(f"  Offer {i+1}: {offer_id.get('value', 'N/A')} ({offer_id.get('Owner', 'N/A')})")
                    print(f"    Channel: {offer_id.get('Channel', 'N/A')}")
                    print(f"    OfferItems: {len(offer_items)}")
                    
                    for j, item in enumerate(offer_items):
                        print(f"      Item {j+1}: {item.get('value', 'N/A')}")
            
            # ShoppingResponseID
            shopping_id = result.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value')
            print(f"ShoppingResponseID: {shopping_id}")
            
            print("\n" + "="*50)
            print("FULL SERVICELIST REQUEST JSON:")
            print("="*50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"ERROR in comprehensive output: {str(e)}")
            raise e


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
