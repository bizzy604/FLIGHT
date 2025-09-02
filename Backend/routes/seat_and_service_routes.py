"""
Seat availability and service list routes.
These endpoints follow the same pattern as air-shopping and flight-price.
"""
import json
import logging
import uuid
from quart import Blueprint, request, jsonify, current_app
from quart_cors import route_cors
from utils.auth import TokenManager
from scripts.build_seatavailability_rq import build_seatavailability_request
from scripts.build_servicelist_rq import build_servicelist_request
import aiohttp

logger = logging.getLogger(__name__)

# Create a Blueprint for seat and service routes
bp = Blueprint('seat_service', __name__, url_prefix='/api/verteil')

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

@bp.route('/test-new-routes', methods=['GET'])
async def test_new_routes():
    """Test endpoint to verify new routes are working."""
    return jsonify({
        'status': 'success',
        'message': '🔥 NEW ROUTES ARE WORKING! 🔥',
        'timestamp': str(uuid.uuid4())
    })

@bp.route('/seat-availability', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def get_seat_availability():
    """
    Get available seats for a flight offer.
    
    POST JSON Body:
    - flight_price_response: The FlightPrice response from which to build the request
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Seat availability data
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"NEW CLEAN SeatAvailability endpoint reached - Request ID: {request_id}")
        print(f"🔥 NEW ENDPOINT HIT: SeatAvailability - Request ID: {request_id}")  # Force console output
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        # Get TokenManager token (same as other working endpoints)
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build the request using the working script
        seatavailability_request = build_seatavailability_request(
            flight_price_response, selected_offer_index
        )
        
        # Create headers like other working endpoints
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'SeatAvailability',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preSeatAvailability"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=seatavailability_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"SeatAvailability request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"SeatAvailability request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"SeatAvailability request failed: {str(e)}", 500, request_id))


@bp.route('/service-list', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def get_service_list():
    """
    Get available ancillary services for a flight offer.
    
    POST JSON Body:
    - flight_price_response: The FlightPrice response from which to build the request
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Service list data
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"ServiceList request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        # Get TokenManager token (same as other working endpoints)
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build the request using the working script
        servicelist_request = build_servicelist_request(
            flight_price_response, selected_offer_index
        )
        
        # Create headers like other working endpoints
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'ServiceList',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preServiceList"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=servicelist_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"ServiceList request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"ServiceList request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"ServiceList request failed: {str(e)}", 500, request_id))