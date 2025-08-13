"""
Clean seat availability and service list routes - completely new implementation.
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

# Create a Blueprint with a different name to avoid conflicts
bp = Blueprint('clean_seat_service', __name__, url_prefix='/api/verteil')

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

@bp.route('/clean-test', methods=['GET'])
async def clean_test():
    """Test endpoint to verify clean routes work."""
    return jsonify({
        'status': 'success',
        'message': 'CLEAN ROUTES WORKING!',
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
    CLEAN seat availability endpoint - completely bypasses old problematic code.
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"CLEAN SEAT ENDPOINT HIT - Request ID: {request_id}")
        logger.info(f"CLEAN SeatAvailability request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        print(f"Getting TokenManager token...")
        # Get TokenManager token (same as other working endpoints)
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        print(f"Got token: {bearer_token[:20]}...")
        
        print(f"Building seat availability request...")
        # Build the request using the working script
        seatavailability_request = build_seatavailability_request(
            flight_price_response, selected_offer_index
        )
        print(f"Built request successfully")
        
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
        print(f"Making API call to: {api_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=seatavailability_request, timeout=30) as response:
                result = await response.json()
                
                print(f"API call successful - Status: {response.status}")
                logger.info(f"CLEAN SeatAvailability request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'request_id': request_id,
                    'message': 'CLEAN seat availability endpoint working!'
                })
                
    except Exception as e:
        print(f"ERROR in clean seat endpoint: {str(e)}")
        logger.error(f"CLEAN SeatAvailability request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"CLEAN SeatAvailability request failed: {str(e)}", 500, request_id))


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
    CLEAN service list endpoint - completely bypasses old problematic code.
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"CLEAN SERVICE ENDPOINT HIT - Request ID: {request_id}")
        logger.info(f"CLEAN ServiceList request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        selected_offer_index = data.get('selected_offer_index', 0)

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))

        print(f"Getting TokenManager token...")
        # Get TokenManager token (same as other working endpoints)
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        print(f"Got token: {bearer_token[:20]}...")
        
        print(f"Building service list request...")
        # Build the request using the working script
        servicelist_request = build_servicelist_request(
            flight_price_response, selected_offer_index
        )
        print(f"Built request successfully")
        
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
        print(f"Making API call to: {api_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=servicelist_request, timeout=30) as response:
                result = await response.json()
                
                print(f"API call successful - Status: {response.status}")
                logger.info(f"CLEAN ServiceList request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'request_id': request_id,
                    'message': 'CLEAN service list endpoint working!'
                })
                
    except Exception as e:
        print(f"ERROR in clean service endpoint: {str(e)}")
        logger.error(f"CLEAN ServiceList request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"CLEAN ServiceList request failed: {str(e)}", 500, request_id))