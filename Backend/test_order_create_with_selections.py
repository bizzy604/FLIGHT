#!/usr/bin/env python3
"""
Test script to generate OrderCreate payload with selected services and seats.
"""

import json
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def main():
    """Generate OrderCreate payload with selected services and seats."""
    print("=" * 80)
    print("GENERATING ORDERCREATE PAYLOAD WITH SELECTED SERVICES AND SEATS")
    print("=" * 80)

    base_path = "c:\\Users\\User\\Desktop\\REA FLIGHT PORTAL\\Backend"

    try:
        # Load the actual API log files
        flight_price_file = os.path.join(base_path, 'api_logs', 'flight_price', 'FlightPrice_RS.json')
        service_list_file = os.path.join(base_path, 'api_logs', 'service_list', 'ServiceList_RS.json')
        seat_availability_file = os.path.join(base_path, 'api_logs', 'seat_availability', 'SeatAvailability_RS.json')

        print(f"Loading files:")
        print(f"  FlightPrice: {flight_price_file}")
        print(f"  ServiceList: {service_list_file}")
        print(f"  SeatAvailability: {seat_availability_file}")

        with open(flight_price_file, 'r', encoding='utf-8') as f:
            flight_price_response = json.load(f)

        with open(service_list_file, 'r', encoding='utf-8') as f:
            service_list_response = json.load(f)

        with open(seat_availability_file, 'r', encoding='utf-8') as f:
            seat_availability_response = json.load(f)

        print("✅ Successfully loaded all API response files")

        # Passenger data (using Kevin Amoni from the final_ordercreate_test_output.json)
        passengers_data = [
            {
                "ObjectKey": "PAX1",
                "PTC": "ADT",
                "Name": {
                    "Title": "Mr",
                    "Given": ["KEVIN"],
                    "Surname": "AMONI"
                },
                "Gender": "Female",
                "BirthDate": "1993-08-09",
                "Contacts": {
                    "Email": "kevin.amoni@example.com",
                    "Phone": {
                        "Number": "5551234567",
                        "CountryCode": "1"
                    },
                    "Address": {
                        "Street": ["123 Main St"],
                        "CityName": "New York",
                        "PostalCode": "10001",
                        "CountryCode": {"value": "US"}
                    }
                }
            }
        ]

        # Simple cash payment
        payment_data = {
            "MethodType": "CASH",
            "Details": {
                "CashInd": True
            }
        }

        # SELECTED SERVICES - Based on available services from ServiceList_RS.json
        # 1. Doha Convenience Pack (paid service) - ObjectKey: "1-ServiceIdQR-4"
        # 2. Weight System Charge (paid baggage service) - ObjectKey: "1-ServiceIdQR-5"
        selected_services = [
            "1-ServiceIdQR-3",  # DOHA CONVENIENCE PACK - ₹20,796
            "1-ServiceIdQR-4"   # WEIGHT SYSTEM CHARGE - ₹1,763
        ]

        # SELECTED SEATS - Based on available seats from SeatAvailability_RS.json
        # Since we don't have explicit seat pricing in the response, we'll assume some seats are available
        # Using format: "PRICE{number}-SEG{segment}" as seen in the original test
        selected_seats = [
            "PRICE1-SEG7",   # Another premium seat on segment 9
            "PRICE4-SEG7"    # Another premium seat on segment 9
        ]

        print("\n🔄 Generating OrderCreate payload with selections:")
        print(f"  - Services: {len(selected_services)} selected")
        for service in selected_services:
            print(f"    • {service}")
        print(f"  - Seats: {len(selected_seats)} selected")
        for seat in selected_seats:
            print(f"    • {seat}")

        # Generate OrderCreate request
        order_create_rq = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data,
            servicelist_response=service_list_response,
            seatavailability_response=seat_availability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )

        # Save the generated request to file
        output_file = os.path.join(base_path, 'final_ordercreate_with_selections.json')
        with open(output_file, 'w') as f:
            json.dump(order_create_rq, f, indent=2)

        print(f"\n✅ SUCCESS: OrderCreate request saved to: {output_file}")

        # Display basic structure information
        query = order_create_rq["Query"]
        print("\n📊 Generated payload structure:")
        print(f"  - Passengers: {len(query['Passengers']['Passenger'])}")
        print(f"  - OrderItems: {len(query['OrderItems']['OfferItem'])} total items")

        # Count different item types
        offer_items = query['OrderItems']['OfferItem']
        flight_items = [item for item in offer_items if "DetailedFlightItem" in item["OfferItemType"]]
        service_items = [item for item in offer_items if "OtherItem" in item["OfferItemType"]]
        seat_items = [item for item in offer_items if "SeatItem" in item["OfferItemType"]]

        print(f"    • Flight Items: {len(flight_items)}")
        print(f"    • Service Items: {len(service_items)}")
        print(f"    • Seat Items: {len(seat_items)}")

        if 'DataLists' in query:
            service_list_count = len(query['DataLists'].get('ServiceList', {}).get('Service', []))
            print(f"  - Services in DataLists: {service_list_count}")

        if 'Payments' in query and query['Payments']['Payment']:
            payment = query['Payments']['Payment'][0]
            amount = payment.get('Amount', {})
            print(f"  - Total Payment: {amount.get('Code', 'N/A')} {amount.get('value', 'N/A')}")

        print("\n🎉 SUCCESS: OrderCreate payload with selected services and seats generated!")
        print(f"   File size: {os.path.getsize(output_file)} bytes")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: Failed to generate OrderCreate payload: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
