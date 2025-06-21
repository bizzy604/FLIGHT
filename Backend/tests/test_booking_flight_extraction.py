import unittest
import pytest

class MockFlightBookingService:
    def _process_booking_response(self, response_data):
        processed = {
            'pricing': {},
            'outbound': None,
            'return': None,
            'passengers': [],
            'contact': {},
            'order_id': None,
            'booking_reference': None
        }

        # Extract order information
        order_data = response_data.get('Response', {}).get('Order', [{}])[0]
        
        # Extract Order ID and Booking Reference
        processed['order_id'] = order_data.get('OrderID', {}).get('value')
        booking_refs = order_data.get('BookingReferences', {}).get('BookingReference', [])
        if booking_refs:
            processed['booking_reference'] = booking_refs[0].get('ID')
        
        # Extract Total Order Price
        total_price = order_data.get('TotalOrderPrice', {}).get('SimpleCurrencyPrice', {}).get('value')
        processed['pricing']['total_price'] = total_price
        
        # Extract order items
        order_items = order_data.get('OrderItems', {}).get('OrderItem', [])
        
        for flight_item in order_items:
            if 'FlightItem' in flight_item:
                flight_item_data = flight_item['FlightItem']

                # Pricing Information (individual item pricing)
                price_data = flight_item_data.get('Price', {})
                base_amount = price_data.get('BaseAmount', {}).get('value')
                taxes_total = price_data.get('Taxes', {}).get('Total', {}).get('value')
                processed['pricing'].update({
                    'base_fare': base_amount,
                    'taxes': taxes_total
                })

                # Flight Segment Information - Extract complete route
                origin_destinations = flight_item_data.get('OriginDestination', [])
                if len(origin_destinations) > 0:
                    flights = origin_destinations[0].get('Flight', [])
                    if flights:
                        # For multi-segment flights, extract complete route
                        processed['outbound'] = self._extract_complete_route(flights)
                
                # Check for return flights (second OriginDestination)
                if len(origin_destinations) > 1:
                    return_flights = origin_destinations[1].get('Flight', [])
                    if return_flights:
                        processed['return'] = self._extract_complete_route(return_flights)
                
                # Break after processing the first flight item with valid data
                break

        # Passenger and Contact Information
        passengers_data = response_data.get('Response', {}).get('Passengers', {}).get('Passenger', [])
        for pax in passengers_data:
            passenger_info = {
                'name': f"{pax.get('Name', {}).get('Given', [{}])[0].get('value', '')} {pax.get('Name', {}).get('Surname', {}).get('value', '')}",
                'type': pax.get('PTC', {}).get('value'),
                'title': pax.get('Name', {}).get('Title')
            }
            processed['passengers'].append(passenger_info)

            if pax.get('Contacts'):
                contact_info = pax.get('Contacts', {}).get('Contact', [{}])[0]
                processed['contact'] = {
                    'email': contact_info.get('EmailContact', {}).get('Address', {}).get('value'),
                    'phone': contact_info.get('PhoneContact', {}).get('Number', [{}])[0].get('value')
                }

        return processed

    def _extract_complete_route(self, flights):
        """Extract complete route information for multi-segment flights"""
        if not flights:
            return None
            
        # For multi-segment flights, get origin from first flight and destination from last flight
        first_flight = flights[0]
        last_flight = flights[-1]
        
        # Extract airline with priority: Name first, then AirlineID as fallback
        marketing_carrier = first_flight.get('MarketingCarrier', {})
        airline = marketing_carrier.get('Name')
        if not airline:
            airline = marketing_carrier.get('AirlineID', {}).get('value')
        
        # Extract booking class from MarketingName
        booking_class = first_flight.get('ClassOfService', {}).get('MarketingName', {}).get('value')
        if not booking_class:
            # Fallback to Code if MarketingName is not available
            booking_class = first_flight.get('ClassOfService', {}).get('Code', {}).get('value')
        
        route_info = {
            'departure_airport': first_flight.get('Departure', {}).get('AirportCode', {}).get('value'),
            'departure_time': first_flight.get('Departure', {}).get('Date'),
            'arrival_airport': last_flight.get('Arrival', {}).get('AirportCode', {}).get('value'),
            'arrival_time': last_flight.get('Arrival', {}).get('Date'),
            'airline': airline,
            'flight_number': first_flight.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value'),
            'aircraft': first_flight.get('Equipment', {}).get('AircraftCode', {}).get('value', 'N/A'),
            'booking_class': booking_class,
            'segments': []
        }
        
        # Add all segments for detailed route information
        for flight in flights:
            segment_airline = flight.get('MarketingCarrier', {}).get('Name')
            if not segment_airline:
                segment_airline = flight.get('MarketingCarrier', {}).get('AirlineID', {}).get('value')
                
            segment = {
                'departure_airport': flight.get('Departure', {}).get('AirportCode', {}).get('value'),
                'departure_time': flight.get('Departure', {}).get('Date'),
                'arrival_airport': flight.get('Arrival', {}).get('AirportCode', {}).get('value'),
                'arrival_time': flight.get('Arrival', {}).get('Date'),
                'airline': segment_airline,
                'flight_number': flight.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value'),
                'aircraft': flight.get('Equipment', {}).get('AircraftCode', {}).get('value', 'N/A')
            }
            route_info['segments'].append(segment)
            
        return route_info

    def _extract_flight_details(self, flight):
        # Extract airline with priority: Name first, then AirlineID as fallback
        marketing_carrier = flight.get('MarketingCarrier', {})
        airline = marketing_carrier.get('Name')
        if not airline:
            airline = marketing_carrier.get('AirlineID', {}).get('value')
        
        # Extract booking class from MarketingName
        booking_class = flight.get('ClassOfService', {}).get('MarketingName', {}).get('value')
        if not booking_class:
            # Fallback to Code if MarketingName is not available
            booking_class = flight.get('ClassOfService', {}).get('Code', {}).get('value')
        
        return {
            'departure_airport': flight.get('Departure', {}).get('AirportCode', {}).get('value'),
            'departure_time': flight.get('Departure', {}).get('Date'),
            'arrival_airport': flight.get('Arrival', {}).get('AirportCode', {}).get('value'),
            'arrival_time': flight.get('Arrival', {}).get('Date'),
            'airline': airline,
            'flight_number': flight.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value'),
            'aircraft': flight.get('Equipment', {}).get('AircraftCode', {}).get('value', 'N/A'),
            'booking_class': booking_class
        }

class TestBookingFlightExtraction(unittest.TestCase):
    def setUp(self):
        self.service = MockFlightBookingService()

    def test_flight_details_extraction_with_real_api_response(self):
        import json
        import os
        test_file_path = os.path.join(os.path.dirname(__file__), 'OrdercreateRS.json')
        with open(test_file_path, 'r') as f:
            real_response = json.load(f)

        result = self.service._process_booking_response(real_response)

        self.assertIsNotNone(result['outbound'])
        self.assertEqual(result['outbound']['departure_airport'], 'BLR')
        self.assertEqual(result['outbound']['arrival_airport'], 'LHR')  # Final destination
        self.assertEqual(result['outbound']['airline'], 'KL')
        self.assertEqual(result['outbound']['flight_number'], '880')
        self.assertEqual(result['outbound']['aircraft'], '772')
        self.assertEqual(result['outbound']['booking_class'], 'ECONOMY')  # MarketingName

        # Test segments for complete route
        self.assertEqual(len(result['outbound']['segments']), 2)
        self.assertEqual(result['outbound']['segments'][0]['departure_airport'], 'BLR')
        self.assertEqual(result['outbound']['segments'][0]['arrival_airport'], 'AMS')
        self.assertEqual(result['outbound']['segments'][1]['departure_airport'], 'AMS')
        self.assertEqual(result['outbound']['segments'][1]['arrival_airport'], 'LHR')

        # This is a one-way trip, so return should be None
        self.assertIsNone(result['return'])

        self.assertEqual(result['pricing']['base_fare'], 5480.0)
        self.assertEqual(result['pricing']['taxes'], 274.0)
        self.assertEqual(result['pricing']['total_price'], 217713.0)

        # Test order information
        self.assertEqual(result['order_id'], 'OPNXAL')
        self.assertEqual(result['booking_reference'], '1749029')

        self.assertEqual(len(result['passengers']), 4)
        self.assertEqual(result['contact']['email'], 'kevinamoni20@example.com')

    def test_flight_details_extraction_with_missing_data(self):
        mock_response = {
            'Response': {
                'Order': [{
                    'OrderItems': {
                        'OrderItem': [{
                            'FlightItem': {
                                'OriginDestination': [{
                                    'Flight': [{
                                        'Departure': {
                                            'AirportCode': {'value': 'JFK'}
                                        },
                                        'Arrival': {
                                            'AirportCode': {'value': 'LAX'}
                                        }
                                    }]
                                }]
                            }
                        }]
                    }
                }]
            }
        }
        result = self.service._process_booking_response(mock_response)
        self.assertIsNotNone(result['outbound'])
        self.assertEqual(result['outbound']['departure_airport'], 'JFK')
        self.assertEqual(result['outbound']['arrival_airport'], 'LAX')
        self.assertIsNone(result['return'])

    def test_roundtrip_flight_extraction(self):
        mock_response = {
            'Response': {
                'Order': [{
                    'OrderItems': {
                        'OrderItem': [{
                            'FlightItem': {
                                'OriginDestination': [
                                    {
                                        'Flight': [{
                                            'Departure': {
                                                'AirportCode': {'value': 'JFK'}
                                            },
                                            'Arrival': {
                                                'AirportCode': {'value': 'LAX'}
                                            }
                                        }]
                                    },
                                    {
                                        'Flight': [{
                                            'Departure': {
                                                'AirportCode': {'value': 'LAX'}
                                            },
                                            'Arrival': {
                                                'AirportCode': {'value': 'JFK'}
                                            }
                                        }]
                                    }
                                ]
                            }
                        }]
                    }
                }]
            }
        }
        result = self.service._process_booking_response(mock_response)
        self.assertIsNotNone(result['outbound'])
        self.assertEqual(result['outbound']['departure_airport'], 'JFK')
        self.assertEqual(result['outbound']['arrival_airport'], 'LAX')
        self.assertIsNotNone(result['return'])
        self.assertEqual(result['return']['departure_airport'], 'LAX')
        self.assertEqual(result['return']['arrival_airport'], 'JFK')

if __name__ == '__main__':
    unittest.main()