import json
import os

# Load the real API response
test_file_path = os.path.join(os.path.dirname(__file__), 'OrdercreateRS.json')
with open(test_file_path, 'r') as f:
    data = json.load(f)

order_items = data['Response']['Order'][0]['OrderItems']['OrderItem']
print(f'Total order items: {len(order_items)}')

for i, item in enumerate(order_items):
    print(f'\nItem {i}:')
    print(f'  Keys: {list(item.keys())}')
    
    if 'FlightItem' in item:
        flight_item = item['FlightItem']
        print(f'  FlightItem found')
        
        if 'OriginDestination' in flight_item:
            origin_destinations = flight_item['OriginDestination']
            print(f'  Number of OriginDestinations: {len(origin_destinations)}')
            
            for j, od in enumerate(origin_destinations):
                print(f'    OD {j}: {od.get("DepartureCode", "?")} -> {od.get("ArrivalCode", "?")}')
                if 'Flight' in od:
                    flights = od['Flight']
                    print(f'      Flights: {len(flights)}')
                    for k, flight in enumerate(flights):
                        dep_code = flight.get('Departure', {}).get('AirportCode', {}).get('value', '?')
                        arr_code = flight.get('Arrival', {}).get('AirportCode', {}).get('value', '?')
                        flight_num = flight.get('FlightNumber', {}).get('value', '?')
                        print(f'        Flight {k}: {dep_code} -> {arr_code}, Flight #{flight_num}')