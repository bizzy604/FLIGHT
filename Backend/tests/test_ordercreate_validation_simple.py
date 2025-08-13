"""
Comprehensive validation test for OrderCreate request builder using actual Seats & Services data.

This test uses the actual files from the Seats & Services folder:
- 4_FlightPriceRS.json as input
- 6_ServiceListRS.json for services 
- 9_OrderCreateRQ.json as expected output for comparison

The test validates that our build_ordercreate_rq.py script generates the correct structure.
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


class TestOrderCreateValidation(unittest.TestCase):
    """Comprehensive validation test for OrderCreate request builder"""

    def setUp(self):
        """Set up test fixtures with actual data from Seats & Services folder"""
        self.tests_dir = Path(__file__).parent
        self.seats_services_dir = self.tests_dir.parent / "Seats & Services"
        
        print("\n" + "="*100)
        print("COMPREHENSIVE ORDERCREATE VALIDATION TEST")
        print("="*100)
        print(f"Loading actual data from: {self.seats_services_dir}")
        
        # Load actual files from Seats & Services folder
        self.flight_price_response = self._load_json_file("4_FlightPriceRS.json")
        self.servicelist_response = self._load_json_file("6_ServiceListRS.json")
        
        # Load expected output for comparison
        self.expected_ordercreate_rq = self._load_json_file("9_OrderCreateRQ.json")
        
        # Extract passenger data from expected output to match structure
        self.passenger_details = self._extract_passenger_data_from_expected()
        
        # Extract payment info from expected output to match structure
        self.payment_info = self._extract_payment_info_from_expected()
        
        # Extract selected services from expected output
        self.selected_services = self._extract_selected_services_from_expected()
        
        print(f"[OK] Loaded FlightPriceRS: {len(str(self.flight_price_response))} chars")
        print(f"[OK] Loaded ServiceListRS: {len(str(self.servicelist_response))} chars") 
        print(f"[OK] Loaded Expected OrderCreateRQ: {len(str(self.expected_ordercreate_rq))} chars")
        print(f"[OK] Extracted {len(self.passenger_details)} passengers")
        print(f"[OK] Extracted selected services: {self.selected_services}")

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file from the Seats & Services folder"""
        file_path = self.seats_services_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Required test file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return json.loads(content)
        except Exception as e:
            raise Exception(f"Error loading {filename}: {str(e)}")

    def _extract_passenger_data_from_expected(self) -> List[Dict[str, Any]]:
        """Extract passenger data from expected OrderCreateRQ to match structure"""
        passengers = self.expected_ordercreate_rq.get("Query", {}).get("Passengers", {}).get("Passenger", [])
        
        passenger_data = []
        for passenger in passengers:
            passenger_info = {
                "ObjectKey": passenger.get("ObjectKey"),
                "PTC": passenger.get("PTC", {}).get("value", "ADT"),
                "Name": {
                    "Title": passenger.get("Name", {}).get("Title"),
                    "Given": passenger.get("Name", {}).get("Given", [{}])[0].get("value"),
                    "Surname": passenger.get("Name", {}).get("Surname", {}).get("value")
                },
                "Gender": passenger.get("Gender", {}).get("value"),
                "BirthDate": passenger.get("Age", {}).get("BirthDate", {}).get("value"),
                "Contacts": passenger.get("Contacts", {})
            }
            passenger_data.append(passenger_info)
            
        return passenger_data

    def _extract_payment_info_from_expected(self) -> Dict[str, Any]:
        """Extract payment info from expected OrderCreateRQ to match structure"""
        payments = self.expected_ordercreate_rq.get("Query", {}).get("Payments", {}).get("Payment", [])
        
        if payments:
            payment = payments[0]
            method = payment.get("Method", {})
            
            if "Cash" in method:
                return {
                    "MethodType": "CASH",
                    "CashInd": True
                }
        
        # Default to cash
        return {
            "MethodType": "CASH", 
            "CashInd": True
        }

    def _extract_selected_services_from_expected(self) -> List[str]:
        """Extract selected services from expected OrderCreateRQ"""
        offer_items = self.expected_ordercreate_rq.get("Query", {}).get("OrderItems", {}).get("OfferItem", [])
        
        selected_services = []
        
        for item in offer_items:
            offer_item_type = item.get("OfferItemType", {})
            
            if "OtherItem" in offer_item_type:
                # This is a service item
                refs = offer_item_type.get("OtherItem", [{}])[0].get("refs", [])
                for ref in refs:
                    if ref.startswith("1-ServiceId"):
                        selected_services.append(ref)
        
        return selected_services

    def test_comprehensive_ordercreate_validation(self):
        """
        Comprehensive validation test that compares our generated OrderCreate request
        with the expected structure from 9_OrderCreateRQ.json
        """
        print("\n" + "-"*80)
        print("RUNNING COMPREHENSIVE VALIDATION")
        print("-"*80)
        
        try:
            # Generate OrderCreate request using our builder
            print("[INFO] Generating OrderCreate request using our builder...")
            
            generated_request = generate_order_create_rq(
                flight_price_response=self.flight_price_response,
                passengers_data=self.passenger_details,
                payment_input_info=self.payment_info,
                servicelist_response=self.servicelist_response,
                selected_services=self.selected_services
            )
            
            print("[SUCCESS] OrderCreate request generated successfully")
            
            # Save generated output for manual inspection
            output_path = self.tests_dir / "output_validation_generated_ordercreate.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(generated_request, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Generated request saved to: {output_path}")
            
            # Save expected output for comparison
            expected_output_path = self.tests_dir / "output_validation_expected_ordercreate.json"
            with open(expected_output_path, 'w', encoding='utf-8') as f:
                json.dump(self.expected_ordercreate_rq, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Expected request saved to: {expected_output_path}")
            
            # Perform basic structure validation
            self._validate_basic_structure(generated_request)
            
            # Perform detailed comparison
            self._perform_detailed_comparison(generated_request)
            
            # Analyze differences
            self._analyze_structure_differences(generated_request)
            
            print("\n[SUCCESS] COMPREHENSIVE VALIDATION COMPLETED!")
            print("[INFO] Review the saved output files for detailed comparison")
            
            return generated_request
            
        except Exception as e:
            self.fail(f"Comprehensive validation failed: {str(e)}")

    def _validate_basic_structure(self, generated_request: Dict[str, Any]) -> None:
        """Validate basic structure of generated request"""
        print("\n[INFO] Validating basic structure...")
        
        # Basic structure checks
        self.assertIsInstance(generated_request, dict)
        self.assertIn('Query', generated_request)
        
        query = generated_request['Query']
        self.assertIn('Passengers', query)
        self.assertIn('OrderItems', query) 
        self.assertIn('Payments', query)
        
        # OrderItems structure
        order_items = query['OrderItems']
        self.assertIn('ShoppingResponse', order_items)
        self.assertIn('OfferItem', order_items)
        
        # Validate passenger count
        passengers = query['Passengers']['Passenger']
        expected_passengers = self.expected_ordercreate_rq['Query']['Passengers']['Passenger']
        self.assertEqual(len(passengers), len(expected_passengers))
        
        print("[SUCCESS] Basic structure validation passed")

    def _perform_detailed_comparison(self, generated_request: Dict[str, Any]) -> None:
        """Perform detailed comparison between generated and expected requests"""
        print("\n[INFO] Performing detailed comparison...")
        
        # Compare high-level sections
        generated_query = generated_request.get('Query', {})
        expected_query = self.expected_ordercreate_rq.get('Query', {})
        
        # Compare section keys
        generated_sections = set(generated_query.keys())
        expected_sections = set(expected_query.keys())
        
        missing_sections = expected_sections - generated_sections
        extra_sections = generated_sections - expected_sections
        
        if missing_sections:
            print(f"[WARNING] Missing sections: {missing_sections}")
        
        if extra_sections:
            print(f"[INFO] Extra sections: {extra_sections}")
        
        # Compare Passengers structure
        self._compare_passengers(generated_query, expected_query)
        
        # Compare OrderItems structure
        self._compare_order_items(generated_query, expected_query)
        
        # Compare Payments structure
        self._compare_payments(generated_query, expected_query)
        
        print("[SUCCESS] Detailed comparison completed")

    def _compare_passengers(self, generated_query: Dict[str, Any], expected_query: Dict[str, Any]) -> None:
        """Compare Passengers section"""
        print("\n[INFO] Comparing Passengers section...")
        
        gen_passengers = generated_query.get('Passengers', {}).get('Passenger', [])
        exp_passengers = expected_query.get('Passengers', {}).get('Passenger', [])
        
        self.assertEqual(len(gen_passengers), len(exp_passengers), 
                        f"Passenger count mismatch: got {len(gen_passengers)}, expected {len(exp_passengers)}")
        
        for i, (gen_pax, exp_pax) in enumerate(zip(gen_passengers, exp_passengers)):
            print(f"  Passenger {i+1}: ObjectKey={gen_pax.get('ObjectKey')} vs {exp_pax.get('ObjectKey')}")
            
            # Compare key fields
            self.assertEqual(gen_pax.get('ObjectKey'), exp_pax.get('ObjectKey'))
            self.assertEqual(gen_pax.get('PTC', {}).get('value'), exp_pax.get('PTC', {}).get('value'))
        
        print("[SUCCESS] Passengers comparison passed")

    def _compare_order_items(self, generated_query: Dict[str, Any], expected_query: Dict[str, Any]) -> None:
        """Compare OrderItems section"""
        print("\n[INFO] Comparing OrderItems section...")
        
        gen_order_items = generated_query.get('OrderItems', {})
        exp_order_items = expected_query.get('OrderItems', {})
        
        # Compare ShoppingResponse
        gen_shopping_response = gen_order_items.get('ShoppingResponse', {})
        exp_shopping_response = exp_order_items.get('ShoppingResponse', {})
        
        print(f"  ShoppingResponse Owner: {gen_shopping_response.get('Owner')} vs {exp_shopping_response.get('Owner')}")
        
        # Compare OfferItems
        gen_offer_items = gen_order_items.get('OfferItem', [])
        exp_offer_items = exp_order_items.get('OfferItem', [])
        
        print(f"  OfferItem count: {len(gen_offer_items)} vs {len(exp_offer_items)}")
        
        # Analyze OfferItem types
        gen_flight_items = [item for item in gen_offer_items if 'DetailedFlightItem' in item.get('OfferItemType', {})]
        gen_service_items = [item for item in gen_offer_items if 'OtherItem' in item.get('OfferItemType', {})]
        gen_seat_items = [item for item in gen_offer_items if 'SeatItem' in item.get('OfferItemType', {})]
        
        exp_flight_items = [item for item in exp_offer_items if 'DetailedFlightItem' in item.get('OfferItemType', {})]
        exp_service_items = [item for item in exp_offer_items if 'OtherItem' in item.get('OfferItemType', {})]
        exp_seat_items = [item for item in exp_offer_items if 'SeatItem' in item.get('OfferItemType', {})]
        
        print(f"    Flight items: {len(gen_flight_items)} vs {len(exp_flight_items)}")
        print(f"    Service items: {len(gen_service_items)} vs {len(exp_service_items)}")
        print(f"    Seat items: {len(gen_seat_items)} vs {len(exp_seat_items)}")
        
        print("[SUCCESS] OrderItems comparison completed")

    def _compare_payments(self, generated_query: Dict[str, Any], expected_query: Dict[str, Any]) -> None:
        """Compare Payments section"""
        print("\n[INFO] Comparing Payments section...")
        
        gen_payments = generated_query.get('Payments', {}).get('Payment', [])
        exp_payments = expected_query.get('Payments', {}).get('Payment', [])
        
        self.assertEqual(len(gen_payments), len(exp_payments),
                        f"Payment count mismatch: got {len(gen_payments)}, expected {len(exp_payments)}")
        
        if gen_payments and exp_payments:
            gen_payment = gen_payments[0]
            exp_payment = exp_payments[0]
            
            gen_amount = gen_payment.get('Amount', {}).get('value')
            exp_amount = exp_payment.get('Amount', {}).get('value')
            
            print(f"  Payment amount: {gen_amount} vs {exp_amount}")
            print(f"  Payment currency: {gen_payment.get('Amount', {}).get('Code')} vs {exp_payment.get('Amount', {}).get('Code')}")
        
        print("[SUCCESS] Payments comparison passed")

    def _analyze_structure_differences(self, generated_request: Dict[str, Any]) -> None:
        """Analyze structural differences between generated and expected requests"""
        print("\n[INFO] STRUCTURE ANALYSIS SUMMARY")
        print("-" * 50)
        
        # Manual comparison
        gen_query = generated_request.get('Query', {})
        exp_query = self.expected_ordercreate_rq.get('Query', {})
        
        # Compare top-level sections
        gen_sections = set(gen_query.keys())
        exp_sections = set(exp_query.keys())
        
        missing_sections = exp_sections - gen_sections
        extra_sections = gen_sections - exp_sections
        common_sections = gen_sections & exp_sections
        
        if missing_sections:
            print(f"[MISSING] Missing sections: {missing_sections}")
        
        if extra_sections:
            print(f"[EXTRA] Extra sections: {extra_sections}")
            
        print(f"[COMMON] Common sections: {common_sections}")
        
        # Summary statistics
        print(f"\n[STATS] SUMMARY STATISTICS:")
        print(f"  Generated request size: {len(str(generated_request))} characters")
        print(f"  Expected request size: {len(str(self.expected_ordercreate_rq))} characters")
        print(f"  Size difference: {len(str(generated_request)) - len(str(self.expected_ordercreate_rq))}")
        
        print(f"  Generated sections: {list(gen_sections)}")
        print(f"  Expected sections: {list(exp_sections)}")

        # Key matching analysis
        print(f"\n[ANALYSIS] KEY MATCHING ANALYSIS:")
        
        # Analyze DataLists
        gen_data_lists = gen_query.get('DataLists', {})
        exp_data_lists = exp_query.get('DataLists', {})
        
        if gen_data_lists and exp_data_lists:
            gen_dl_keys = set(gen_data_lists.keys())
            exp_dl_keys = set(exp_data_lists.keys())
            
            print(f"  DataLists - Generated: {gen_dl_keys}")
            print(f"  DataLists - Expected: {exp_dl_keys}")
            
            missing_dl = exp_dl_keys - gen_dl_keys
            extra_dl = gen_dl_keys - exp_dl_keys
            
            if missing_dl:
                print(f"  DataLists Missing: {missing_dl}")
            if extra_dl:
                print(f"  DataLists Extra: {extra_dl}")
        
        print(f"\n[RESULT] Structure analysis completed")


if __name__ == '__main__':
    # Run the validation test
    unittest.main(verbosity=2)