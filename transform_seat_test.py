#!/usr/bin/env python3
"""
Test script to transform the seat availability response using the existing transformer.
"""

import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

from utils.seat_availability_transformer import transform_seat_availability_lean_frontend

def main():
    # Read the API response
    response_file = r"Backend\api_logs\seat_availability\20250815_213456_8da7d8be-343a-4b7c-8daf-70aa1708f8c5_response.json"
    
    try:
        with open(response_file, 'r', encoding='utf-8') as f:
            api_response_data = json.load(f)
            
        # Extract just the response part (not the metadata)
        api_response = api_response_data.get('response', api_response_data)
        
        print("Processing seat availability response...")
        print(f"Input data keys: {list(api_response.keys())}")
        
        # Transform the response
        result = transform_seat_availability_lean_frontend(api_response)
        
        print(f"\nTransformation status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            data = result['data']
            
            # Count seats
            total_seats = 0
            seat_count_by_cabin = []
            
            if 'dataLists' in data and 'seatList' in data['dataLists'] and 'seats' in data['dataLists']['seatList']:
                seats = data['dataLists']['seatList']['seats']
                total_seats = len(seats)
                
                print(f"\nSEAT COUNT ANALYSIS:")
                print(f"Total seats generated: {total_seats}")
                
                # Analyze by cabin/row ranges
                if 'flights' in data and len(data['flights']) > 0 and 'cabin' in data['flights'][0]:
                    cabins = data['flights'][0]['cabin']
                    print(f"Number of cabins: {len(cabins)}")
                    
                    for i, cabin in enumerate(cabins):
                        if 'seatDisplay' in cabin and 'rows' in cabin['seatDisplay']:
                            rows = cabin['seatDisplay']['rows']
                            first_row = rows.get('first', 0)
                            last_row = rows.get('last', 0)
                            columns = cabin['seatDisplay'].get('columns', [])
                            
                            seats_in_cabin = len([s for s in seats if 
                                                first_row <= int(s['location']['row']['number']['value']) <= last_row])
                            
                            print(f"  Cabin {i+1}: Rows {first_row}-{last_row}, {len(columns)} columns, {seats_in_cabin} seats")
                            seat_count_by_cabin.append({
                                'cabin': i+1,
                                'rows': f"{first_row}-{last_row}",
                                'columns': len(columns),
                                'seats': seats_in_cabin
                            })
                
                # Sample seat data
                print(f"\nSAMPLE SEATS (first 5):")
                for i, seat in enumerate(seats[:5]):
                    seat_id = seat.get('objectKey', 'unknown')
                    row = seat.get('location', {}).get('row', {}).get('number', {}).get('value', 'unknown')
                    column = seat.get('location', {}).get('column', 'unknown')
                    availability = seat.get('availability', 'unknown')
                    price = seat.get('price', {}).get('total', {}).get('value', 'free') if seat.get('price') else 'free'
                    
                    print(f"  {i+1}. {seat_id}: {row}{column} - {availability} - {price}")
                
            else:
                print("\nNo seats found in transformed data")
                
        else:
            print(f"\nTransformation failed: {result.get('message', 'Unknown error')}")
            if 'error' in result:
                print(f"Error details: {result['error']}")
        
        # Write the full result to file
        output_file = "seat_transformation_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"\nFull transformation result written to: {output_file}")
        print(f"File size: {os.path.getsize(output_file)} bytes")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()