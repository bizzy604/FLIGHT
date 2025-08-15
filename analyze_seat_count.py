#!/usr/bin/env python3
"""
Detailed analysis of the seat transformation result
"""

import json

def main():
    # Read the transformation result
    with open('seat_transformation_result.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    if result.get('status') != 'success':
        print("Transformation was not successful")
        return
    
    data = result['data']
    
    # Get all seats
    seats = data['dataLists']['seatList']['seats']
    total_seats = len(seats)
    
    print(f"DETAILED SEAT ANALYSIS")
    print(f"=" * 50)
    print(f"Total seats generated: {total_seats}")
    
    # Analyze the original API response structure
    print(f"\nOriginal API Response Analysis:")
    print(f"Number of flights: {len(data.get('flights', []))}")
    
    if 'flights' in data and len(data['flights']) > 0:
        flight = data['flights'][0]
        cabins = flight.get('cabin', [])
        print(f"Number of cabin sections: {len(cabins)}")
        
        for i, cabin in enumerate(cabins):
            if 'seatDisplay' in cabin:
                seat_display = cabin['seatDisplay']
                rows = seat_display.get('rows', {})
                columns = seat_display.get('columns', [])
                
                first_row = rows.get('first', 0)
                last_row = rows.get('last', 0)
                upper_deck = rows.get('upperDeckInd', False)
                
                print(f"\nCabin {i+1}:")
                print(f"  Rows: {first_row} to {last_row} {'(Upper Deck)' if upper_deck else ''}")
                print(f"  Columns: {len(columns)} -> {[col['value'] for col in columns]}")
                print(f"  Theoretical max seats: {(last_row - first_row + 1) * len(columns)}")
                
                # Count actual seats in this range
                actual_seats = [s for s in seats if 
                               first_row <= int(s['location']['row']['number']['value']) <= last_row]
                print(f"  Actual seats generated: {len(actual_seats)}")
                
                # Analyze by row
                row_counts = {}
                for seat in actual_seats:
                    row_num = int(seat['location']['row']['number']['value'])
                    if row_num not in row_counts:
                        row_counts[row_num] = 0
                    row_counts[row_num] += 1
                
                print(f"  Seats per row breakdown:")
                for row in sorted(row_counts.keys()):
                    print(f"    Row {row}: {row_counts[row]} seats")
    
    # Analyze seat characteristics
    print(f"\nSeat Characteristics Analysis:")
    availability_counts = {}
    price_counts = {'free': 0, 'paid': 0}
    
    for seat in seats:
        # Availability
        availability = seat.get('availability', 'unknown')
        if availability not in availability_counts:
            availability_counts[availability] = 0
        availability_counts[availability] += 1
        
        # Pricing
        if seat.get('price'):
            price_counts['paid'] += 1
        else:
            price_counts['free'] += 1
    
    print(f"Availability breakdown:")
    for status, count in availability_counts.items():
        print(f"  {status}: {count} seats")
    
    print(f"\nPricing breakdown:")
    for price_type, count in price_counts.items():
        print(f"  {price_type}: {count} seats")
    
    # Sample of different seat types
    print(f"\nSample seats from different rows:")
    sample_rows = [40, 50, 63, 75, 25] # Different cabin sections
    for row in sample_rows:
        row_seats = [s for s in seats if int(s['location']['row']['number']['value']) == row]
        if row_seats:
            print(f"  Row {row}: {len(row_seats)} seats -> {[s['location']['column'] for s in row_seats[:10]]}")

if __name__ == "__main__":
    main()