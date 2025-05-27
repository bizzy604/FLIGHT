"""
Verteil NDC API integration routes.

This module contains routes for interacting with the Verteil NDC API.
"""
from flask import Blueprint, request, jsonify, current_app
from ..services import flight_service

# Create a Blueprint for Verteil flight routes
bp = Blueprint('verteil_flights', __name__, url_prefix='/api/verteil')

@bp.route('/air-shopping', methods=['POST'])
def air_shopping():
    """
    Handle flight search requests.
    
    Request body should contain:
    - origin: IATA code of origin airport
    - destination: IATA code of destination airport
    - departure_date: Departure date in YYYY-MM-DD format
    - return_date: Return date in YYYY-MM-DD format (optional)
    - adults: Number of adult passengers
    - children: Number of child passengers (optional)
    - infants: Number of infant passengers (optional)
    - cabin_class: Cabin class (e.g., ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
    """
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['origin', 'destination', 'departure_date', 'adults']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Call the flight service to process the search
        result = flight_service.process_air_shopping(data)
        
        if 'error' in result:
            return jsonify(result), 400
            
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in air_shopping: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

@bp.route('/flight-price', methods=['POST'])
def flight_price():
    """
    Get detailed pricing for a specific flight offer.
    
    Request body should contain:
    - offer_id: The offer ID from the AirShoppingRS
    - shopping_response_id: The ShoppingResponseID from the AirShoppingRS
    - air_shopping_rs: The full AirShoppingRS response (or relevant parts)
    """
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['offer_id', 'shopping_response_id', 'air_shopping_rs']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Call the flight service to get the price
        result = flight_service.process_flight_price(data)
        
        if 'error' in result:
            return jsonify(result), 400
            
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in flight_price: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

@bp.route('/order-create', methods=['POST'])
def order_create():
    """
    Create a booking order.
    
    Request body should contain:
    - flight_price_rs: The full FlightPriceRS response
    - passenger_details: List of passenger details
    - payment_details: Payment information
    - contact_information: Contact details
    """
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['flight_price_rs', 'passenger_details', 'payment_details', 'contact_information']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Call the flight service to create the order
        result = flight_service.process_order_create(data)
        
        if 'error' in result:
            return jsonify(result), 400
            
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in order_create: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request"}), 500
