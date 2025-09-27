"""
Ancillary pricing routes for handling PricedInd=false scenarios.
These endpoints handle additional FlightPrice calls for pricing selected services and seats.
"""
import json
import logging
import uuid
from quart import Blueprint, request, jsonify, current_app
from quart_cors import route_cors
from utils.auth import TokenManager
from scripts.build_flightprice_ancillary_rq import (
    build_flightprice_ancillary_request,
    detect_pricing_required
)
import aiohttp

logger = logging.getLogger(__name__)

# Create a Blueprint for ancillary pricing routes
bp = Blueprint('ancillary_pricing', __name__, url_prefix='/api/verteil')

# Allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
    "http://localhost:3001", 
    "http://127.0.0.1:3001",
    "https://flight-pearl.vercel.app"
]

def _get_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def _create_error_response(message: str, status_code: int = 400, request_id: str = None) -> dict:
    """Create a standardized error response."""
    return {
        'status': 'error',
        'message': message,
        'request_id': request_id or _get_request_id()
    }

@bp.route('/pricing/check-requirements', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_pricing_requirements():
    """
    Check if selected services and seats require additional pricing.
    
    POST JSON Body:
    - servicelist_response: ServiceList response data
    - seatavailability_response: SeatAvailability response data
    - selected_services: List of selected service ObjectKeys
    - selected_seats: List of selected seat ObjectKeys
    
    Returns:
    - Pricing requirements analysis
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Checking pricing requirements - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])

        # Detect pricing requirements
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        logger.info(f"Pricing requirements check completed - Request ID: {request_id}")
        
        return jsonify({
            'status': 'success',
            'data': pricing_info,
            'request_id': request_id
        })
                
    except Exception as e:
        logger.error(f"Pricing requirements check failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Pricing requirements check failed: {str(e)}", 500, request_id))

@bp.route('/pricing/price-ancillaries', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def price_ancillaries():
    """
    Price selected services and seats using FlightPrice API.
    
    POST JSON Body:
    - flight_price_response: Original FlightPrice response
    - servicelist_response: ServiceList response data
    - seatavailability_response: SeatAvailability response data
    - selected_services: List of selected service ObjectKeys
    - selected_seats: List of selected seat ObjectKeys
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Priced FlightPrice response with selected services and seats
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Pricing ancillaries request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        # Check if pricing is actually required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        if not pricing_info['requires_pricing']:
            logger.info(f"No pricing required, returning original response - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': flight_price_response,
                'pricing_info': pricing_info,
                'request_id': request_id,
                'message': 'No additional pricing required'
            })

        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build the ancillary pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats,
            selected_offer_index=selected_offer_index
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'FlightPrice',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ancillary_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Ancillary pricing request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Ancillary pricing request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Ancillary pricing request failed: {str(e)}", 500, request_id))

@bp.route('/pricing/price-services-only', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def price_services_only():
    """
    Price only selected services (no seats).
    
    POST JSON Body:
    - flight_price_response: Original FlightPrice response
    - servicelist_response: ServiceList response data
    - selected_services: List of selected service ObjectKeys
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Priced FlightPrice response with selected services
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Pricing services only request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        servicelist_response = data.get('servicelist_response')
        selected_services = data.get('selected_services', [])
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        # Check if pricing is required for services
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        if not pricing_info['requires_pricing']:
            logger.info(f"No service pricing required - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': flight_price_response,
                'pricing_info': pricing_info,
                'request_id': request_id,
                'message': 'No additional pricing required for services'
            })

        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build the service pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            servicelist_response=servicelist_response,
            selected_services=selected_services,
            selected_offer_index=selected_offer_index
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'FlightPrice',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ancillary_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Service pricing request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Service pricing request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Service pricing request failed: {str(e)}", 500, request_id))

@bp.route('/pricing/price-seats-only', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def price_seats_only():
    """
    Price only selected seats (no services).
    
    POST JSON Body:
    - flight_price_response: Original FlightPrice response
    - seatavailability_response: SeatAvailability response data
    - selected_seats: List of selected seat ObjectKeys
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Priced FlightPrice response with selected seats
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Pricing seats only request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_seats = data.get('selected_seats', [])
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        # Check if pricing is required for seats
        pricing_info = detect_pricing_required(
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        if not pricing_info['requires_pricing']:
            logger.info(f"No seat pricing required - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': flight_price_response,
                'pricing_info': pricing_info,
                'request_id': request_id,
                'message': 'No additional pricing required for seats'
            })

        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build the seat pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats,
            selected_offer_index=selected_offer_index
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'FlightPrice',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ancillary_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Seat pricing request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Seat pricing request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Seat pricing request failed: {str(e)}", 500, request_id))
