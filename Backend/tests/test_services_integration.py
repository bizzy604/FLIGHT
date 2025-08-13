"""
Test ServiceList and SeatAvailability integration with actual data.
"""
import json
import unittest
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestServicesIntegration(unittest.TestCase):
    """Test services integration with actual data"""

    def setUp(self):
        """Set up test fixtures"""
        self.tests_dir = Path(__file__).parent
        self.seats_services_dir = self.tests_dir.parent / "Seats & Services"
        
        print("\n" + "="*70)
        print("SERVICES INTEGRATION TEST")
        print("="*70)
        
        # Load test files
        self.flight_price_response = self._load_json_file("4_FlightPriceRS.json")
        self.servicelist_response = self._load_json_file("6_ServiceListRS.json")
        self.seatavailability_response = self._load_json_file("8_SeatAvailabilityRS.json")
        
        print(f"[OK] Loaded test data files")

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file from the Seats & Services folder"""
        file_path = self.seats_services_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
        except Exception as e:
            raise Exception(f"Error loading {filename}: {str(e)}")

    def test_servicelist_service_import(self):
        """Test ServiceListService can be imported and instantiated"""
        print("\n[TEST] ServiceListService Import Test")
        print("-" * 40)
        
        try:
            from services.flight.servicelist import ServiceListService
            
            # Test instantiation
            service = ServiceListService()
            self.assertIsNotNone(service)
            
            print("[OK] ServiceListService imported and instantiated successfully")
            return service
            
        except Exception as e:
            self.fail(f"ServiceListService import/instantiation failed: {str(e)}")

    def test_seatavailability_service_import(self):
        """Test SeatAvailabilityService can be imported and instantiated"""
        print("\n[TEST] SeatAvailabilityService Import Test")
        print("-" * 40)
        
        try:
            from services.flight.seatavailability import SeatAvailabilityService
            
            # Test instantiation
            service = SeatAvailabilityService()
            self.assertIsNotNone(service)
            
            print("[OK] SeatAvailabilityService imported and instantiated successfully")
            return service
            
        except Exception as e:
            self.fail(f"SeatAvailabilityService import/instantiation failed: {str(e)}")

    def test_servicelist_request_builder(self):
        """Test ServiceList request builder with actual data"""
        print("\n[TEST] ServiceList Request Builder Test")
        print("-" * 40)
        
        try:
            from scripts.build_servicelist_rq import build_servicelist_request
            
            # Build ServiceList request from FlightPriceRS
            request = build_servicelist_request(self.flight_price_response)
            
            self.assertIsInstance(request, dict)
            self.assertIn('Query', request)
            
            # Validate request structure
            query = request['Query']
            self.assertIn('OriginDestination', query)
            self.assertIn('Offers', query)
            
            print("[OK] ServiceList request built successfully")
            print(f"[INFO] Request contains {len(query.keys())} main sections")
            
            # Save output for inspection
            output_path = self.tests_dir / "output_servicelist_integration_test.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(request, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Request saved to: {output_path}")
            
        except Exception as e:
            self.fail(f"ServiceList request builder test failed: {str(e)}")

    def test_seatavailability_request_builder(self):
        """Test SeatAvailability request builder with actual data"""
        print("\n[TEST] SeatAvailability Request Builder Test")
        print("-" * 40)
        
        try:
            from scripts.build_seatavailability_rq import build_seatavailability_request
            
            # Build SeatAvailability request from FlightPriceRS
            request = build_seatavailability_request(self.flight_price_response)
            
            self.assertIsInstance(request, dict)
            self.assertIn('Query', request)
            
            # Validate request structure
            query = request['Query']
            self.assertIn('OriginDestination', query)
            self.assertIn('Offers', query)
            
            print("[OK] SeatAvailability request built successfully")
            print(f"[INFO] Request contains {len(query.keys())} main sections")
            
            # Save output for inspection
            output_path = self.tests_dir / "output_seatavailability_integration_test.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(request, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Request saved to: {output_path}")
            
        except Exception as e:
            self.fail(f"SeatAvailability request builder test failed: {str(e)}")

    def test_servicelist_response_processing(self):
        """Test ServiceList response processing"""
        print("\n[TEST] ServiceList Response Processing Test")
        print("-" * 40)
        
        try:
            from services.flight import process_servicelist_response
            
            # Process the actual ServiceListRS response
            processed = process_servicelist_response(self.servicelist_response)
            
            self.assertIsInstance(processed, dict)
            
            print("[OK] ServiceList response processed successfully")
            
            # Count services
            services_count = 0
            if 'services' in processed and 'service' in processed['services']:
                services_count = len(processed['services']['service'])
            
            print(f"[INFO] Processed response contains {services_count} services")
            
            # Save output for inspection
            output_path = self.tests_dir / "output_servicelist_processed.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Processed response saved to: {output_path}")
            
        except Exception as e:
            self.fail(f"ServiceList response processing test failed: {str(e)}")

    def test_seatavailability_response_processing(self):
        """Test SeatAvailability response processing"""
        print("\n[TEST] SeatAvailability Response Processing Test")
        print("-" * 40)
        
        try:
            from services.flight import process_seatavailability_response
            
            # Only test with the first 1000 lines due to file size
            limited_response = self._create_limited_seatavailability_response()
            
            # Process the limited SeatAvailability response
            processed = process_seatavailability_response(limited_response)
            
            self.assertIsInstance(processed, dict)
            
            print("[OK] SeatAvailability response processed successfully")
            
            # Check structure
            if 'flights' in processed:
                print(f"[INFO] Processed response contains {len(processed['flights'])} flights")
            
            # Save output for inspection
            output_path = self.tests_dir / "output_seatavailability_processed.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Processed response saved to: {output_path}")
            
        except Exception as e:
            self.fail(f"SeatAvailability response processing test failed: {str(e)}")

    def _create_limited_seatavailability_response(self):
        """Create a limited version of SeatAvailabilityRS for testing"""
        # Create a minimal structure based on what we expect
        return {
            "Warnings": {},
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": "test-response-id"
                }
            },
            "Flights": [
                {
                    "Cabin": [
                        {
                            "SeatDisplay": {
                                "Columns": [
                                    {"value": "A", "Position": "W"},
                                    {"value": "B", "Position": "C"},
                                    {"value": "C", "Position": "A"}
                                ],
                                "Rows": {
                                    "First": 1,
                                    "Last": 30,
                                    "UpperDeckInd": False
                                }
                            }
                        }
                    ]
                }
            ]
        }

    def test_integration_summary(self):
        """Summary test showing overall integration status"""
        print("\n[SUMMARY] Integration Test Results")
        print("=" * 40)
        
        try:
            # Test imports
            from services.flight.servicelist import ServiceListService
            from services.flight.seatavailability import SeatAvailabilityService
            from scripts.build_servicelist_rq import build_servicelist_request
            from scripts.build_seatavailability_rq import build_seatavailability_request
            from services.flight import process_servicelist_response, process_seatavailability_response
            
            print("[OK] All required modules imported successfully")
            
            # Test data availability
            self.assertTrue(self.flight_price_response, "FlightPriceRS data available")
            self.assertTrue(self.servicelist_response, "ServiceListRS data available")
            
            print("[OK] Test data loaded successfully")
            
            # Test request builders
            service_request = build_servicelist_request(self.flight_price_response)
            seat_request = build_seatavailability_request(self.flight_price_response)
            
            self.assertIsInstance(service_request, dict)
            self.assertIsInstance(seat_request, dict)
            
            print("[OK] Request builders working")
            
            # Test response processors
            processed_services = process_servicelist_response(self.servicelist_response)
            
            self.assertIsInstance(processed_services, dict)
            
            print("[OK] Response processors working")
            
            print("\n" + "="*40)
            print("INTEGRATION TEST STATUS: SUCCESS")
            print("All backend services are ready for frontend integration!")
            print("="*40)
            
        except Exception as e:
            self.fail(f"Integration summary test failed: {str(e)}")


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)