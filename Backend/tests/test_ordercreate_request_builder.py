"""
Unit tests for OrderCreate request builder

This module tests the OrderCreate request builder functionality with support for
FlightPriceRS, ServiceListRS, and SeatAvailabilityRS integration.
"""
import json
import unittest
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_ordercreate_rq import generate_order_create_rq


class TestOrderCreateRequestBuilder(unittest.TestCase):
    """Test cases for OrderCreate request builder"""

    def setUp(self):
        """Set up test fixtures"""
        self.tests_dir = Path(__file__).parent
        self.seats_services_dir = self.tests_dir.parent / "Seats & Services"
        
        # Load real test data from Seats & Services directory
        self.flight_price_response = self._load_seats_services_file("4_FlightPriceRS.json")
        self.servicelist_response = self._load_seats_services_file("6_ServiceListRS.json")
        self.seatavailability_response = self._load_seats_services_file("8_SeatAvailabilityRS.json")
        self.expected_ordercreate_rq = self._load_seats_services_file("9_OrderCreateRQ.json")
        self.expected_ordercreate_rs = self._load_seats_services_file("10_OrderCreateRS.json")
        
        # Enhanced passenger details with comprehensive contact information
        self.passenger_details = [
            {
                "ObjectKey": "PAX1",
                "PTC": "ADT",
                "Name": {
                    "Title": "Mr",
                    "Given": ["John"],
                    "Surname": "Doe"
                },
                "Gender": "Male",
                "BirthDate": "1990-01-01",
                "Contacts": {
                    "Email": "john.doe@example.com",
                    "Phone": {
                        "Number": "9987655232",
                        "CountryCode": "91",
                        "Application": "Home"
                    },
                    "Address": {
                        "Street": ["Thapasya Building, 3rd Floor", "Infopark Campus"],
                        "CityName": "Cochin",
                        "PostalCode": "673328",
                        "CountryCode": {"value": "IN"},
                        "CountrySubDivisionCode": "KL"
                    }
                },
                "Documents": [
                    {
                        "Type": "PT",
                        "ID": "P123456789",
                        "DateOfExpiration": "2030-12-31",
                        "CountryOfIssuance": "US"
                    }
                ]
            }
        ]
        
        # Sample payment info (using PaymentCard to match real-world scenarios)
        self.payment_info = {
            "MethodType": "PAYMENTCARD",
            "Details": {
                "CardNumberToken": "1234567890123456",
                "CardType": "VI",
                "CardCode": "123",
                "EffectiveExpireDate": {
                    "Expiration": "1225"
                },
                "CardHolderName": {
                    "value": "John Doe"
                }
            }
        }
        
        print("SUCCESS: Test setup completed with real Seats & Services data")

    def _load_seats_services_file(self, filename: str) -> Dict[str, Any]:
        """Load a file from the Seats & Services directory"""
        file_path = self.seats_services_dir / filename
        
        if not file_path.exists():
            print(f"Warning: File {filename} not found in Seats & Services directory")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Replace Unicode checkmarks that cause encoding issues
                content = content.replace('✓', 'OK').replace('✗', 'X')
                data = json.loads(content)
                print(f"Successfully loaded {filename} from Seats & Services directory")
                return data
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            return {}

    def _load_test_file(self, filename: str) -> Dict[str, Any]:
        """Load a test file (deprecated - use _load_seats_services_file)"""
        return self._load_seats_services_file(filename)

    def test_basic_ordercreate_generation(self):
        """Test basic OrderCreate request generation without services or seats"""
        print("\n" + "="*80)
        print("TEST: Basic OrderCreate Request Generation")
        print("="*80)
        
        try:
            result = generate_order_create_rq(
                flight_price_response=self.flight_price_response,
                passengers_data=self.passenger_details,
                payment_input_info=self.payment_info
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Query', result)
            
            query = result['Query']
            self.assertIn('Passengers', query)
            self.assertIn('OrderItems', query)
            self.assertIn('Payments', query)
            
            # Validate OrderItems structure
            order_items = query['OrderItems']
            self.assertIn('ShoppingResponse', order_items)
            self.assertIn('OfferItem', order_items)
            
            # Validate Passengers
            passengers = query['Passengers']['Passenger']
            self.assertIsInstance(passengers, list)
            self.assertGreater(len(passengers), 0)
            
            # Save output for inspection
            output_path = self.tests_dir / "output_basic_ordercreate_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("SUCCESS: Basic OrderCreate request generated successfully")
            print(f"SUCCESS: Output saved to: {output_path}")
            print(f"SUCCESS: Request contains {len(query.keys())} main sections")
            
            return result
            
        except Exception as e:
            self.fail(f"Basic OrderCreate generation failed: {str(e)}")

    def test_ordercreate_with_services(self):
        """Test OrderCreate request generation with services"""
        print("\n" + "="*80)
        print("TEST: OrderCreate Request Generation with Services")
        print("="*80)
        
        try:
            # Use real ServiceListRS response from Seats & Services
            servicelist_response = self.servicelist_response
            if not servicelist_response:
                print("Warning: No ServiceListRS data available, skipping services test")
                return
            
            # Extract actual service ObjectKeys from the real data
            services = servicelist_response.get('Services', {}).get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []
            
            # Get the first available service ObjectKeys
            selected_services = [service.get('ObjectKey') for service in services[:2] if service.get('ObjectKey')]
            if not selected_services:
                print("Warning: No service ObjectKeys found in ServiceListRS, using sample keys")
                selected_services = ["SERVICE-1", "SERVICE-MEAL-1"]
            
            result = generate_order_create_rq(
                flight_price_response=self.flight_price_response,
                passengers_data=self.passenger_details,
                payment_input_info=self.payment_info,
                servicelist_response=servicelist_response,
                selected_services=selected_services
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Query', result)
            
            query = result['Query']
            self.assertIn('OrderItems', query)
            
            # Check if services were added to OfferItem
            offer_items = query['OrderItems']['OfferItem']
            self.assertIsInstance(offer_items, list)
            
            # Look for OtherItem (service) entries
            service_items = [item for item in offer_items if 'OtherItem' in item.get('OfferItemType', {})]
            
            if selected_services and servicelist_response:
                self.assertGreater(len(service_items), 0, "Expected service items in OfferItem list")
            
            # Check DataLists for ServiceList
            data_lists = query.get('DataLists', {})
            if selected_services and servicelist_response:
                self.assertIn('ServiceList', data_lists, "Expected ServiceList in DataLists")
            
            # Save output for inspection
            output_path = self.tests_dir / "output_ordercreate_with_services_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("SUCCESS: OrderCreate with services generated successfully")
            print(f"SUCCESS: Output saved to: {output_path}")
            print(f"SUCCESS: Found {len(service_items)} service items in request")
            
            return result
            
        except Exception as e:
            self.fail(f"OrderCreate with services generation failed: {str(e)}")

    def test_ordercreate_with_seats(self):
        """Test OrderCreate request generation with seat selection"""
        print("\n" + "="*80)
        print("TEST: OrderCreate Request Generation with Seats")
        print("="*80)
        
        try:
            # Use real SeatAvailabilityRS response from Seats & Services
            seatavailability_response = self.seatavailability_response
            if not seatavailability_response:
                print("Warning: No SeatAvailabilityRS data available, skipping seats test")
                return
            
            # Extract actual seat ObjectKeys from the real data
            seat_services = seatavailability_response.get('Services', {}).get('Service', [])
            if not isinstance(seat_services, list):
                seat_services = [seat_services] if seat_services else []
            
            # Get the first available seat ObjectKeys
            selected_seats = [service.get('ObjectKey') for service in seat_services[:2] if service.get('ObjectKey')]
            if not selected_seats:
                print("Warning: No seat ObjectKeys found in SeatAvailabilityRS, using sample keys")
                selected_seats = ["SEAT-1A", "SEAT-1B"]
            
            result = generate_order_create_rq(
                flight_price_response=self.flight_price_response,
                passengers_data=self.passenger_details,
                payment_input_info=self.payment_info,
                seatavailability_response=seatavailability_response,
                selected_seats=selected_seats
            )
            
            # Validate basic structure
            self.assertIsInstance(result, dict)
            self.assertIn('Query', result)
            
            query = result['Query']
            self.assertIn('OrderItems', query)
            
            # Check if seats were added to OfferItem
            offer_items = query['OrderItems']['OfferItem']
            self.assertIsInstance(offer_items, list)
            
            # Look for SeatItem entries
            seat_items = [item for item in offer_items if 'SeatItem' in item.get('OfferItemType', {})]
            
            if selected_seats and seatavailability_response:
                self.assertGreater(len(seat_items), 0, "Expected seat items in OfferItem list")
            
            # Save output for inspection
            output_path = self.tests_dir / "output_ordercreate_with_seats_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("SUCCESS: OrderCreate with seats generated successfully")
            print(f"SUCCESS: Output saved to: {output_path}")
            print(f"SUCCESS: Found {len(seat_items)} seat items in request")
            
            return result
            
        except Exception as e:
            self.fail(f"OrderCreate with seats generation failed: {str(e)}")

    def test_complete_ordercreate_with_services_and_seats(self):
        """Test complete OrderCreate request generation with both services and seats"""
        print("\n" + "="*80)
        print("TEST: Complete OrderCreate with Services and Seats")
        print("="*80)
        
        try:
            # Use real ServiceListRS and SeatAvailabilityRS responses from Seats & Services
            servicelist_response = self.servicelist_response
            seatavailability_response = self.seatavailability_response
            
            # Extract actual ObjectKeys from real data
            selected_services = []
            if servicelist_response:
                services = servicelist_response.get('Services', {}).get('Service', [])
                if not isinstance(services, list):
                    services = [services] if services else []
                selected_services = [service.get('ObjectKey') for service in services[:2] if service.get('ObjectKey')]
            
            selected_seats = []
            if seatavailability_response:
                seat_services = seatavailability_response.get('Services', {}).get('Service', [])
                if not isinstance(seat_services, list):
                    seat_services = [seat_services] if seat_services else []
                selected_seats = [service.get('ObjectKey') for service in seat_services[:1] if service.get('ObjectKey')]
            
            print(f"Using real data - Services: {selected_services}, Seats: {selected_seats}")
            
            result = generate_order_create_rq(
                flight_price_response=self.flight_price_response,
                passengers_data=self.passenger_details,
                payment_input_info=self.payment_info,
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=selected_seats
            )
            
            # Validate complete structure
            self.assertIsInstance(result, dict)
            self.assertIn('Query', result)
            
            query = result['Query']
            self.assertIn('Passengers', query)
            self.assertIn('OrderItems', query)
            self.assertIn('Payments', query)
            
            # Check OfferItems for all types
            offer_items = query['OrderItems']['OfferItem']
            self.assertIsInstance(offer_items, list)
            
            # Count different item types
            flight_items = [item for item in offer_items if 'DetailedFlightItem' in item.get('OfferItemType', {})]
            service_items = [item for item in offer_items if 'OtherItem' in item.get('OfferItemType', {})]
            seat_items = [item for item in offer_items if 'SeatItem' in item.get('OfferItemType', {})]
            
            self.assertGreater(len(flight_items), 0, "Expected at least one flight item")
            
            # Validate DataLists
            data_lists = query.get('DataLists', {})
            self.assertIsInstance(data_lists, dict)
            
            # Save output for inspection
            output_path = self.tests_dir / "output_complete_ordercreate_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("SUCCESS: Complete OrderCreate request generated successfully")
            print(f"SUCCESS: Output saved to: {output_path}")
            print(f"SUCCESS: Flight items: {len(flight_items)}, Service items: {len(service_items)}, Seat items: {len(seat_items)}")
            
            # Analyze and display structure
            self._analyze_request_structure("Complete OrderCreate", result)
            
            return result
            
        except Exception as e:
            self.fail(f"Complete OrderCreate generation failed: {str(e)}")

    def test_payment_methods(self):
        """Test OrderCreate with different payment methods"""
        print("\n" + "="*80)
        print("TEST: OrderCreate with Different Payment Methods")
        print("="*80)
        
        payment_methods = [
            {
                "name": "Cash",
                "payment": {
                    "MethodType": "CASH",
                    "CashInd": True
                }
            },
            {
                "name": "Credit Card",
                "payment": {
                    "MethodType": "PAYMENTCARD",
                    "CardNumberToken": "4111111111111111",
                    "CardType": "VI",
                    "CardHolderName": {
                        "value": "John Doe",
                        "refs": []
                    },
                    "EffectiveExpireDate": {
                        "Expiration": "1225"
                    },
                    "CardCode": "123"
                }
            },
            {
                "name": "EasyPay",
                "payment": {
                    "MethodType": "EASYPAY",
                    "AccountNumber": "12345678",
                    "ExpirationDate": "2025-12-31"
                }
            }
        ]
        
        for payment_method in payment_methods:
            print(f"\nTesting {payment_method['name']} payment method:")
            
            try:
                result = generate_order_create_rq(
                    flight_price_response=self.flight_price_response,
                    passengers_data=self.passenger_details,
                    payment_input_info=payment_method["payment"]
                )
                
                # Validate structure
                self.assertIsInstance(result, dict)
                self.assertIn('Query', result)
                self.assertIn('Payments', result['Query'])
                
                payments = result['Query']['Payments']['Payment']
                self.assertIsInstance(payments, list)
                self.assertGreater(len(payments), 0)
                
                # Save output
                output_path = self.tests_dir / f"output_ordercreate_{payment_method['name'].lower().replace(' ', '_')}_payment.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"  SUCCESS: {payment_method['name']} payment method processed")
                print(f"  SUCCESS: Output saved to: {output_path}")
                
            except Exception as e:
                self.fail(f"{payment_method['name']} payment method failed: {str(e)}")

    def test_ordercreate_with_real_data_validation(self):
        """Test OrderCreate generation using real Seats & Services data and validate structure"""
        print("\n" + "="*80)
        print("TEST: OrderCreate with Real Seats & Services Data Validation")
        print("="*80)
        
        try:
            # Extract services and seats from real data
            selected_services = []
            selected_seats = []
            
            if self.servicelist_response:
                services = self.servicelist_response.get('Services', {}).get('Service', [])
                if not isinstance(services, list):
                    services = [services] if services else []
                # Take first 2 services for testing
                selected_services = [service.get('ObjectKey') for service in services[:2] if service.get('ObjectKey')]
                print(f"Available services in real data: {[s.get('ObjectKey') for s in services]}")
            
            if self.seatavailability_response:
                seat_services = self.seatavailability_response.get('Services', {}).get('Service', [])
                if not isinstance(seat_services, list):
                    seat_services = [seat_services] if seat_services else []
                # Take first seat for testing
                selected_seats = [service.get('ObjectKey') for service in seat_services[:1] if service.get('ObjectKey')]
                print(f"Available seats in real data: {[s.get('ObjectKey') for s in seat_services]}")
            
            print(f"Testing with selected services: {selected_services}")
            print(f"Testing with selected seats: {selected_seats}")
            
            # Generate OrderCreate with real data
            result = generate_order_create_rq(
                flight_price_response=self.flight_price_response,
                passengers_data=self.passenger_details,
                payment_input_info=self.payment_info,
                servicelist_response=self.servicelist_response,
                seatavailability_response=self.seatavailability_response,
                selected_services=selected_services,
                selected_seats=selected_seats
            )
            
            # Validate the generated structure
            self.assertIsInstance(result, dict)
            self.assertIn('Query', result)
            
            query = result['Query']
            self.assertIn('Passengers', query)
            self.assertIn('OrderItems', query)
            self.assertIn('Payments', query)
            
            # Validate against expected structure if available
            if self.expected_ordercreate_rq:
                print("Comparing with expected OrderCreateRQ structure...")
                expected_query = self.expected_ordercreate_rq.get('Query', {})
                
                # Check main sections exist
                for section in ['Passengers', 'OrderItems', 'Payments']:
                    if section in expected_query:
                        self.assertIn(section, query, f"Missing {section} in generated request")
                
                # Check OrderItems structure
                if 'OrderItems' in expected_query:
                    expected_order_items = expected_query['OrderItems']
                    actual_order_items = query['OrderItems']
                    
                    for key in ['ShoppingResponse', 'OfferItem']:
                        if key in expected_order_items:
                            self.assertIn(key, actual_order_items, f"Missing {key} in OrderItems")
            
            # Save comprehensive output
            output_path = self.tests_dir / "output_real_data_ordercreate_request.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("SUCCESS: OrderCreate with real data generated and validated")
            print(f"SUCCESS: Output saved to: {output_path}")
            
            # Analyze the result
            self._analyze_real_data_structure(result)
            
            return result
            
        except Exception as e:
            self.fail(f"Real data OrderCreate generation failed: {str(e)}")
    
    def _analyze_real_data_structure(self, result: Dict[str, Any]) -> None:
        """Analyze the structure of OrderCreate generated from real data"""
        print("\nREAL DATA STRUCTURE ANALYSIS:")
        print("-" * 40)
        
        query = result.get('Query', {})
        
        # Analyze flight price data
        if self.flight_price_response:
            offers = self.flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            print(f"FlightPriceRS offers: {len(offers) if isinstance(offers, list) else 1}")
        
        # Analyze services data
        if self.servicelist_response:
            services = self.servicelist_response.get('Services', {}).get('Service', [])
            service_count = len(services) if isinstance(services, list) else 1 if services else 0
            print(f"ServiceListRS services: {service_count}")
        
        # Analyze seats data
        if self.seatavailability_response:
            seat_services = self.seatavailability_response.get('Services', {}).get('Service', [])
            seat_count = len(seat_services) if isinstance(seat_services, list) else 1 if seat_services else 0
            print(f"SeatAvailabilityRS seats: {seat_count}")
        
        # Analyze generated structure
        offer_items = query.get('OrderItems', {}).get('OfferItem', [])
        flight_items = [item for item in offer_items if 'DetailedFlightItem' in item.get('OfferItemType', {})]
        service_items = [item for item in offer_items if 'OtherItem' in item.get('OfferItemType', {})]
        seat_items = [item for item in offer_items if 'SeatItem' in item.get('OfferItemType', {})]
        
        print(f"Generated OfferItems: {len(offer_items)} total")
        print(f"  - Flight items: {len(flight_items)}")
        print(f"  - Service items: {len(service_items)}")  
        print(f"  - Seat items: {len(seat_items)}")
        
        # Analyze payment calculation
        payments = query.get('Payments', {}).get('Payment', [])
        if payments:
            total_amount = sum(p.get('Amount', {}).get('value', 0) for p in payments)
            currency = payments[0].get('Amount', {}).get('Code', 'Unknown') if payments else 'Unknown'
            print(f"Payment total: {total_amount} {currency}")

    def _create_sample_servicelist_response(self) -> Dict[str, Any]:
        """Create a sample ServiceListRS response for testing"""
        return {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "SERVICE-1",
                        "ServiceID": {
                            "ObjectKey": "SRV-001",
                            "value": "SRV1",
                            "Owner": "TEST"
                        },
                        "Name": {
                            "value": "Priority Boarding"
                        },
                        "Descriptions": {
                            "Description": [
                                {
                                    "Text": {
                                        "value": "Priority boarding service"
                                    }
                                }
                            ]
                        },
                        "Price": [
                            {
                                "Total": {
                                    "value": 25.00,
                                    "Code": "USD"
                                }
                            }
                        ],
                        "Associations": [
                            {
                                "Traveler": {
                                    "TravelerReferences": ["PAX1"]
                                }
                            }
                        ],
                        "PricedInd": True
                    },
                    {
                        "ObjectKey": "SERVICE-MEAL-1",
                        "ServiceID": {
                            "ObjectKey": "SRV-002",
                            "value": "MEAL1",
                            "Owner": "TEST"
                        },
                        "Name": {
                            "value": "Special Meal"
                        },
                        "Price": [
                            {
                                "Total": {
                                    "value": 15.00,
                                    "Code": "USD"
                                }
                            }
                        ],
                        "Associations": [
                            {
                                "Traveler": {
                                    "TravelerReferences": ["PAX1"]
                                }
                            }
                        ],
                        "PricedInd": True
                    }
                ]
            },
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": "SERVICELIST-RESPONSE-123"
                }
            }
        }

    def _create_sample_seatavailability_response(self) -> Dict[str, Any]:
        """Create a sample SeatAvailabilityRS response for testing"""
        return {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "SEAT-1A",
                        "ServiceID": {
                            "value": "SEAT-SERVICE-1"
                        },
                        "Name": {
                            "value": "Seat 1A"
                        },
                        "Price": [
                            {
                                "Total": {
                                    "value": 50.00,
                                    "Code": "USD"
                                }
                            }
                        ],
                        "Associations": [
                            {
                                "Traveler": {
                                    "TravelerReferences": ["PAX1"]
                                },
                                "Flight": {
                                    "originDestinationReferencesOrSegmentReferences": [
                                        {
                                            "SegmentReferences": {
                                                "value": ["SEG1"]
                                            }
                                        }
                                    ]
                                }
                            }
                        ],
                        "PricedInd": True
                    }
                ]
            },
            "DataLists": {
                "SeatList": {
                    "Seats": [
                        {
                            "ObjectKey": "SEAT-1A",
                            "Location": {
                                "Column": "A",
                                "Row": {
                                    "Number": {
                                        "value": "1"
                                    }
                                },
                                "Characteristics": {
                                    "Characteristic": [
                                        {
                                            "Code": "W"
                                        },
                                        {
                                            "Code": "CH"
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": "SEATAVAILABILITY-RESPONSE-123"
                }
            }
        }

    def _analyze_request_structure(self, request_name: str, result: Dict[str, Any]) -> None:
        """Analyze and display request structure details"""
        print(f"\n{request_name.upper()} STRUCTURE ANALYSIS:")
        print("-" * (len(request_name) + 20))
        
        query = result.get('Query', {})
        
        # Analyze Passengers
        passengers = query.get('Passengers', {}).get('Passenger', [])
        print(f"Passengers: {len(passengers)}")
        
        # Analyze OrderItems
        order_items = query.get('OrderItems', {})
        offer_items = order_items.get('OfferItem', [])
        
        flight_items = [item for item in offer_items if 'DetailedFlightItem' in item.get('OfferItemType', {})]
        service_items = [item for item in offer_items if 'OtherItem' in item.get('OfferItemType', {})]
        seat_items = [item for item in offer_items if 'SeatItem' in item.get('OfferItemType', {})]
        
        print(f"Total OfferItems: {len(offer_items)}")
        print(f"  - Flight items: {len(flight_items)}")
        print(f"  - Service items: {len(service_items)}")
        print(f"  - Seat items: {len(seat_items)}")
        
        # Analyze ShoppingResponse
        shopping_response = order_items.get('ShoppingResponse', {})
        offers = shopping_response.get('Offers', {}).get('Offer', [])
        print(f"ShoppingResponse Offers: {len(offers)}")
        
        # Analyze DataLists
        data_lists = query.get('DataLists', {})
        data_sections = list(data_lists.keys())
        print(f"DataLists sections: {data_sections}")
        
        # Analyze Payments
        payments = query.get('Payments', {}).get('Payment', [])
        print(f"Payment methods: {len(payments)}")
        if payments:
            payment_methods = []
            for payment in payments:
                method = payment.get('Method', {})
                if 'Cash' in method:
                    payment_methods.append('Cash')
                elif 'PaymentCard' in method:
                    payment_methods.append('PaymentCard')
                elif 'EasyPay' in method:
                    payment_methods.append('EasyPay')
                else:
                    payment_methods.append('Other')
            print(f"  - Methods: {payment_methods}")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)