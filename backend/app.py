from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load sample flight data
def load_flight_data():
    try:
        # Check if we have the FlightPriceResponse.json file
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FlightPriceResponse.json'), 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        # Return mock data if file doesn't exist
        return {
            "flights": [
                {
                    "id": "1",
                    "airline": "SkyWings",
                    "flightNumber": "SW1234",
                    "departureTime": "08:30",
                    "departureAirport": "JFK",
                    "arrivalTime": "10:45",
                    "arrivalAirport": "LAX",
                    "duration": "2h 15m",
                    "price": 299.99,
                    "stops": 0,
                    "cabinClass": "ECONOMY"
                },
                {
                    "id": "2",
                    "airline": "GlobeAir",
                    "flightNumber": "GA5678",
                    "departureTime": "12:15",
                    "departureAirport": "JFK",
                    "arrivalTime": "15:30",
                    "arrivalAirport": "LAX",
                    "duration": "3h 15m",
                    "price": 249.99,
                    "stops": 1,
                    "cabinClass": "ECONOMY"
                }
            ]
        }

@app.route('/api/flights/search', methods=['POST'])
def search_flights():
    search_criteria = request.json
    print(f"Received search criteria: {search_criteria}")
    
    # Here you would typically query a database or external API
    # For this example, we'll use mock data
    
    # Get real flight data if available
    flight_data = load_flight_data()
    
    # In a real app, you would filter flights based on search criteria
    # For demo, we'll just return all flights and modify some fields
    
    # If we have data from FlightPriceResponse.json, adapt it to our frontend format
    if 'flights' not in flight_data:
        # This would be the case if we're using the real data from FlightPriceResponse.json
        # Extract and transform the relevant data from the response
        try:
            flights = []
            if 'data' in flight_data and 'flightOffers' in flight_data['data']:
                for idx, offer in enumerate(flight_data['data']['flightOffers']):
                    for segment in offer.get('itineraries', [])[0].get('segments', []):
                        flight = {
                            "id": str(idx + 1),
                            "airline": segment.get('carrierCode', 'Unknown'),
                            "flightNumber": segment.get('number', 'Unknown'),
                            "departureTime": segment.get('departure', {}).get('at', '').split('T')[1][:5],
                            "departureAirport": segment.get('departure', {}).get('iataCode', ''),
                            "arrivalTime": segment.get('arrival', {}).get('at', '').split('T')[1][:5],
                            "arrivalAirport": segment.get('arrival', {}).get('iataCode', ''),
                            "duration": segment.get('duration', '').replace('PT', '').lower(),
                            "price": float(offer.get('price', {}).get('total', 0)),
                            "stops": len(offer.get('itineraries', [])[0].get('segments', [])) - 1,
                            "cabinClass": segment.get('cabin', 'ECONOMY')
                        }
                        flights.append(flight)
            return jsonify(flights)
        except Exception as e:
            print(f"Error parsing flight data: {e}")
            # Fall back to mock data if parsing fails
            return jsonify(flight_data['flights'])
    else:
        # This is the case where we're using our mock data
        return jsonify(flight_data['flights'])

@app.route('/api/flights/book', methods=['POST'])
def book_flight():
    booking_data = request.json
    print(f"Received booking data: {booking_data}")
    
    # In a real app, you would create a booking in your database
    # For this demo, we'll just return a success message
    
    return jsonify({
        "success": True,
        "bookingId": "BOK12345",
        "message": "Flight booked successfully!"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
