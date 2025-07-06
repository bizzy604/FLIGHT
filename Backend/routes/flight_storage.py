"""
Flight Storage API Routes

This module provides API endpoints for storing and retrieving flight data
using Redis-based storage.
"""
from quart import Blueprint, request, jsonify
from quart_cors import cors
import logging

from services.redis_flight_storage import redis_flight_storage

logger = logging.getLogger(__name__)

# Create blueprint for flight storage routes
flight_storage_bp = Blueprint('flight_storage', __name__)
cors(flight_storage_bp)

@flight_storage_bp.route('/api/flight-storage/search', methods=['POST'])
async def store_flight_search():
    """
    Store flight search data in Redis.
    
    Expected payload:
    {
        "search_data": {...},  // Flight search response data
        "session_id": "optional-session-id",  // Optional, generates new if not provided
        "ttl": 1800  // Optional TTL in seconds, defaults to 30 minutes
    }
    """
    try:
        data = await request.get_json()
        
        if not data or 'search_data' not in data:
            return jsonify({
                'success': False,
                'error': 'search_data is required'
            }), 400
        
        search_data = data['search_data']
        session_id = data.get('session_id')
        ttl = data.get('ttl')
        
        result = redis_flight_storage.store_flight_search(
            search_data=search_data,
            session_id=session_id,
            ttl=ttl
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error storing flight search data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/search/<session_id>', methods=['GET'])
async def get_flight_search(session_id: str):
    """
    Retrieve flight search data from Redis.
    
    Args:
        session_id: Session ID to retrieve data for
    """
    try:
        result = redis_flight_storage.get_flight_search(session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error retrieving flight search data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/price', methods=['POST'])
async def store_flight_price():
    """
    Store flight price data in Redis.
    
    Expected payload:
    {
        "price_data": {...},  // Flight price response data
        "session_id": "required-session-id",  // Required session ID
        "ttl": 1800  // Optional TTL in seconds, defaults to 30 minutes
    }
    """
    try:
        data = await request.get_json()
        
        if not data or 'price_data' not in data or 'session_id' not in data:
            return jsonify({
                'success': False,
                'error': 'price_data and session_id are required'
            }), 400
        
        price_data = data['price_data']
        session_id = data['session_id']
        ttl = data.get('ttl')
        
        result = redis_flight_storage.store_flight_price(
            price_data=price_data,
            session_id=session_id,
            ttl=ttl
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error storing flight price data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/price/<session_id>', methods=['GET'])
async def get_flight_price(session_id: str):
    """
    Retrieve flight price data from Redis.
    
    Args:
        session_id: Session ID to retrieve data for
    """
    try:
        result = redis_flight_storage.get_flight_price(session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error retrieving flight price data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/booking', methods=['POST'])
async def store_booking_data():
    """
    Store booking data in Redis.
    
    Expected payload:
    {
        "booking_data": {...},  // Booking response data
        "session_id": "required-session-id",  // Required session ID
        "ttl": 1800  // Optional TTL in seconds, defaults to 30 minutes
    }
    """
    try:
        data = await request.get_json()
        
        if not data or 'booking_data' not in data or 'session_id' not in data:
            return jsonify({
                'success': False,
                'error': 'booking_data and session_id are required'
            }), 400
        
        booking_data = data['booking_data']
        session_id = data['session_id']
        ttl = data.get('ttl')
        
        result = redis_flight_storage.store_booking_data(
            booking_data=booking_data,
            session_id=session_id,
            ttl=ttl
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error storing booking data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/booking/<session_id>', methods=['GET'])
async def get_booking_data(session_id: str):
    """
    Retrieve booking data from Redis.
    
    Args:
        session_id: Session ID to retrieve data for
    """
    try:
        result = redis_flight_storage.get_booking_data(session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error retrieving booking data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/session/<session_id>', methods=['DELETE'])
async def delete_session_data(session_id: str):
    """
    Delete all flight data for a session.
    
    Args:
        session_id: Session ID to delete data for
    """
    try:
        result = redis_flight_storage.delete_session_data(session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error deleting session data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@flight_storage_bp.route('/api/flight-storage/health', methods=['GET'])
async def health_check():
    """
    Health check endpoint for flight storage service.
    """
    try:
        # Test Redis connection
        redis_flight_storage.redis_client.ping()
        
        return jsonify({
            'success': True,
            'message': 'Flight storage service is healthy',
            'redis_connected': True
        }), 200
        
    except Exception as e:
        logger.error(f"Flight storage health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Flight storage service is unhealthy',
            'redis_connected': False
        }), 500
