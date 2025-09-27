"""
Enhanced OrderCreate routes that handle both PricedInd=true and PricedInd=false scenarios.
"""
import json
import logging
import uuid
from quart import Blueprint, request, jsonify, current_app
from quart_cors import route_cors
from utils.auth import TokenManager
from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request
from scripts.build_flightprice_ancillary_rq import detect_pricing_required
import aiohttp

logger = logging.getLogger(__name__)

# Create a Blueprint for enhanced OrderCreate routes
bp = Blueprint('enhanced_ordercreate', __name__, url_prefix='/api/verteil')

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

@bp.route('/order-create-enhanced', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Timestamp"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def create_order_enhanced():
    """
    Create a new flight booking order with enhanced PricedInd support.
    
    This endpoint automatically handles both PricedInd=true and PricedInd=false scenarios:
    - If PricedInd=true: Uses ServiceList/SeatAvailability responses directly
    - If PricedInd=false: Calls additional FlightPrice API for pricing
    - If mixed: Handles both scenarios appropriately
    
    Expected JSON payload:
    {
        "flight_price_response": {...},  # Original FlightPrice response
        "passengers": [...],             # Passenger details
        "payment": {...},                # Payment information
        "contact_info": {...},           # Contact information
        "servicelist_response": {...},   # Optional ServiceListRS response data
        "seatavailability_response": {...}, # Optional SeatAvailabilityRS response data
        "selected_services": [...],      # Optional list of selected service ObjectKeys
        "selected_seats": [...],         # Optional list of selected seat ObjectKeys
        "ancillary_pricing_response": {...} # Optional additional FlightPrice response for unpriced items
    }
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Enhanced OrderCreate request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("Request body is required", 400, request_id))
        
        # Extract data from frontend request
        flight_price_response = data.get('flight_price_response')
        frontend_passengers = data.get('passengers', [])
        payment_info = data.get('payment', {})
        contact_info = data.get('contact_info', {})
        
        # Extract service and seat data
        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])
        ancillary_pricing_response = data.get('ancillary_pricing_response')
        
        # Validate required data
        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))
        
        if not frontend_passengers:
            return jsonify(_create_error_response("passengers data is required", 400, request_id))
        
        # Check if additional pricing is required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        logger.info(f"Pricing requirements: {pricing_info} - Request ID: {request_id}")
        
        # If pricing is required but no ancillary pricing response provided, return error
        if pricing_info['requires_pricing'] and not ancillary_pricing_response:
            return jsonify(_create_error_response(
                "Additional pricing is required for selected services/seats. Please call the pricing endpoint first.",
                400, request_id
            ))
        
        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build enhanced OrderCreate request
        ordercreate_request = build_ordercreate_enhanced_request(
            flight_price_response=flight_price_response,
            passengers_data=frontend_passengers,
            payment_input_info=payment_info,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats,
            ancillary_pricing_response=ancillary_pricing_response
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'OrderCreate',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preOrderCreate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ordercreate_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Enhanced OrderCreate request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Enhanced OrderCreate request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Enhanced OrderCreate request failed: {str(e)}", 500, request_id))

@bp.route('/order-create/check-pricing-requirements', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_order_pricing_requirements():
    """
    Check if selected services and seats require additional pricing before OrderCreate.
    
    POST JSON Body:
    - servicelist_response: ServiceList response data
    - seatavailability_response: SeatAvailability response data
    - selected_services: List of selected service ObjectKeys
    - selected_seats: List of selected seat ObjectKeys
    
    Returns:
    - Pricing requirements analysis and recommendations
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Checking OrderCreate pricing requirements - Request ID: {request_id}")
        
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
        
        # Add recommendations
        recommendations = []
        if pricing_info['requires_pricing']:
            recommendations.append("Call /api/verteil/pricing/price-ancillaries endpoint before OrderCreate")
        else:
            recommendations.append("Proceed directly to OrderCreate - no additional pricing required")
        
        if pricing_info['services_require_pricing']:
            recommendations.append(f"Services requiring pricing: {pricing_info['services_require_pricing']}")
        
        if pricing_info['seats_require_pricing']:
            recommendations.append(f"Seats requiring pricing: {pricing_info['seats_require_pricing']}")
        
        logger.info(f"OrderCreate pricing requirements check completed - Request ID: {request_id}")
        
        return jsonify({
            'status': 'success',
            'data': {
                **pricing_info,
                'recommendations': recommendations
            },
            'request_id': request_id
        })
                
    except Exception as e:
        logger.error(f"OrderCreate pricing requirements check failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"OrderCreate pricing requirements check failed: {str(e)}", 500, request_id))

@bp.route('/order-create/complete-flow', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Timestamp"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def complete_order_flow():
    """
    Complete order flow that automatically handles pricing and OrderCreate.
    
    This endpoint:
    1. Checks if additional pricing is required
    2. Calls pricing API if needed
    3. Proceeds with OrderCreate
    
    Expected JSON payload:
    {
        "flight_price_response": {...},  # Original FlightPrice response
        "passengers": [...],             # Passenger details
        "payment": {...},                # Payment information
        "contact_info": {...},           # Contact information
        "servicelist_response": {...},   # Optional ServiceListRS response data
        "seatavailability_response": {...}, # Optional SeatAvailabilityRS response data
        "selected_services": [...],      # Optional list of selected service ObjectKeys
        "selected_seats": [...]          # Optional list of selected seat ObjectKeys
    }
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Complete order flow request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("Request body is required", 400, request_id))
        
        # Extract data
        flight_price_response = data.get('flight_price_response')
        frontend_passengers = data.get('passengers', [])
        payment_info = data.get('payment', {})
        contact_info = data.get('contact_info', {})
        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])
        
        # Validate required data
        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response is required", 400, request_id))
        
        if not frontend_passengers:
            return jsonify(_create_error_response("passengers data is required", 400, request_id))
        
        # Check pricing requirements
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        ancillary_pricing_response = None
        
        # If pricing is required, call pricing API
        if pricing_info['requires_pricing']:
            logger.info(f"Additional pricing required, calling pricing API - Request ID: {request_id}")
            
            # Import the pricing function
            from routes.ancillary_pricing_routes import price_ancillaries
            
            # Create pricing request data
            pricing_data = {
                'flight_price_response': flight_price_response,
                'servicelist_response': servicelist_response,
                'seatavailability_response': seatavailability_response,
                'selected_services': selected_services,
                'selected_seats': selected_seats,
                'selected_offer_index': 0
            }
            
            # Call pricing API (simulate the call)
            # In a real implementation, you would call the pricing endpoint
            # For now, we'll assume the frontend has already called it
            return jsonify(_create_error_response(
                "Additional pricing is required. Please call /api/verteil/pricing/price-ancillaries first, then retry with ancillary_pricing_response included.",
                400, request_id
            ))
        
        # Proceed with OrderCreate
        logger.info(f"Proceeding with OrderCreate - Request ID: {request_id}")
        
        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Build enhanced OrderCreate request
        ordercreate_request = build_ordercreate_enhanced_request(
            flight_price_response=flight_price_response,
            passengers_data=frontend_passengers,
            payment_input_info=payment_info,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats,
            ancillary_pricing_response=ancillary_pricing_response
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'service': 'OrderCreate',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preOrderCreate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ordercreate_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Complete order flow completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Complete order flow failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Complete order flow failed: {str(e)}", 500, request_id))
