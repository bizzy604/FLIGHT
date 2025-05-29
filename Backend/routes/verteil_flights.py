"""
Verteil NDC API integration routes.

This module contains routes for interacting with the Verteil NDC API.
"""
import asyncio
import uuid
from datetime import datetime
from quart import Blueprint, request, jsonify, current_app, make_response
from quart_cors import cors
from Backend.services.flight_service import (
    search_flights,
    get_flight_price as get_flight_price_service,
    process_order_create,
    process_air_shopping,
    FlightServiceError
)

# Create a Blueprint for Verteil flight routes
bp = Blueprint('verteil_flights', __name__, url_prefix='/api/verteil')

@bp.route('/air-shopping', methods=['POST', 'OPTIONS'])
async def air_shopping():
    if request.method == 'OPTIONS':
        response = await make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response
    """
    Handle flight search requests with caching and rate limiting.
    
    Request body should contain:
    - tripType: Type of trip (ONE_WAY, ROUND_TRIP, MULTI_CITY)
    - odSegments: List of origin-destination segments
    - numAdults: Number of adult passengers
    - numChildren: Number of child passengers (optional, default: 0)
    - numInfants: Number of infant passengers (optional, default: 0)
    - cabinPreference: Cabin class preference (e.g., ECONOMY, BUSINESS)
    """
    try:
        data = await request.get_json()
        
        # Log the incoming request for debugging
        current_app.logger.info(f"Air shopping request received: {data}")
        
        # Basic validation
        required_fields = ['tripType', 'odSegments', 'numAdults']
        for field in required_fields:
            if field not in data:
                error_msg = f"Missing required field: {field}"
                current_app.logger.error(error_msg)
                return await jsonify({"error": error_msg}), 400
                
        # Validate odSegments
        if not isinstance(data['odSegments'], list) or not data['odSegments']:
            error_msg = "odSegments must be a non-empty array"
            current_app.logger.error(error_msg)
            return await jsonify({"error": error_msg}), 400
            
        # Generate a unique request ID for tracking
        request_id = str(uuid.uuid4())
        current_app.logger.info(f"Request ID: {request_id}")
        
        # Extract search parameters
        trip_type = data['tripType']
        od_segments = data['odSegments']
        num_adults = int(data['numAdults'])
        num_children = int(data.get('numChildren', 0))
        num_infants = int(data.get('numInfants', 0))
        cabin_preference = data.get('cabinPreference', 'ECONOMY')
        
        # Log the parsed parameters
        current_app.logger.info(f"Parsed parameters - Type: {trip_type}, Adults: {num_adults}, Children: {num_children}, Infants: {num_infants}, Cabin: {cabin_preference}")
        current_app.logger.info(f"OD Segments: {od_segments}")
        
        # Prepare search criteria for the flight service
        search_criteria = {
            'trip_type': trip_type,
            'od_segments': od_segments,
            'num_adults': num_adults,
            'num_children': num_children,
            'num_infants': num_infants,
            'cabin_preference': cabin_preference,
            'request_id': request_id
        }
        
        current_app.logger.info(f"Calling process_air_shopping with criteria: {search_criteria}")
        
        try:
            # Call the flight service to process the air shopping request
            search_results = await process_air_shopping(search_criteria)
            
            # Log the search results for debugging
            current_app.logger.info(f"Search results: {search_results}")
            
            # Check if we have valid results
            if isinstance(search_results, dict) and 'error' in search_results:
                current_app.logger.error(f"Error in search results: {search_results['error']}")
                return jsonify({
                    "status": "error",
                    "message": search_results.get('error', 'An error occurred while searching for flights'),
                    "request_id": request_id
                }), 400
                
            # search_results is already the list of offers
            offers = search_results if isinstance(search_results, list) else []
            
            # Log the offers for debugging
            current_app.logger.info(f"Returning {len(offers)} offers")
            for i, offer in enumerate(offers[:5]):  # Log first 5 offers to avoid too much logging
                current_app.logger.info(f"Offer {i+1}: {offer.get('id', 'No ID')} - "
                                     f"{offer.get('airline', 'No Airline')} - "
                                     f"{len(offer.get('segments', []))} segments")
            
            # Ensure the response is a list of offers
            if not isinstance(offers, list):
                current_app.logger.error(f"Expected offers to be a list, got {type(offers)}")
                return jsonify({
                    "status": "error",
                    "message": "Invalid response format from flight service",
                    "request_id": request_id
                }), 500
                
            # Return the offers as a JSON response
            current_app.logger.info("Sending response back to client")
            return jsonify(offers), 200
            
        except Exception as e:
            current_app.logger.error(f"Unexpected error in air_shopping: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "request_id": request_id
            }), 500
        
    except Exception as e:
        error_msg = f"Error processing air shopping request: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return jsonify({"error": error_msg, "status": "error"}), 500

@bp.route('/flight-price', methods=['POST'])
async def flight_price():
    """
    Get detailed pricing for a specific flight offer with caching.
    
    Request body should contain:
    - offer_id: The offer ID from the AirShoppingRS
    - shopping_response_id: The ShoppingResponseID from the AirShoppingRS
    - air_shopping_rs: The full AirShoppingRS response (or relevant parts)
    """
    try:
        data = await request.get_json()
        
        # Basic validation
        required_fields = ['offer_id', 'shopping_response_id', 'air_shopping_rs']
        for field in required_fields:
            if field not in data:
                return await jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate a unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Call the flight service to get the price
        price_results = await get_flight_price_service(
            airshopping_response=data['air_shopping_rs'],
            offer_id=data['offer_id'],
            shopping_response_id=data['shopping_response_id'],
            request_id=request_id
        )
        
        # Add metadata to the response
        response = {
            "request_id": request_id,
            "status": "success",
            "message": "Flight pricing retrieved successfully",
            "results": price_results
        }
        
        return await jsonify(response)
        
    except Exception as e:
        error_msg = f"Error getting flight price: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return await jsonify({"error": error_msg, "status": "error"}), 500

@bp.route('/order-create', methods=['POST'])
async def order_create():
    """
    Create a booking order with rate limiting.
    
    Request body should contain:
    - flight_offer: The flight offer details from FlightPriceRS
    - passengers: List of passenger details
    - payment: Payment information
    - contact_info: Contact details
    """
    try:
        data = await request.get_json()
        
        # Basic validation
        required_fields = ['flight_offer', 'passengers', 'payment', 'contact_info']
        for field in required_fields:
            if field not in data:
                return await jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate a unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Call the flight service to create the order
        order_result = await process_order_create(
            flight_offer=data['flight_offer'],
            passengers=data['passengers'],
            payment=data['payment'],
            contact_info=data['contact_info'],
            request_id=request_id
        )
        
        # Add metadata to the response
        response = {
            "request_id": request_id,
            "status": "success",
            "message": "Order created successfully",
            "results": order_result
        }
        
        return await jsonify(response)
        
    except FlightServiceError as e:
        error_msg = f"Flight service error in order_create: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return await jsonify({"error": str(e), "status": "error"}), 400
        
    except Exception as e:
        error_msg = f"Unexpected error in order_create: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return await jsonify({"error": "An unexpected error occurred while processing your order", "status": "error"}), 500
