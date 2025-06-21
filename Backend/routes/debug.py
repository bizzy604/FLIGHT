from quart import Blueprint, jsonify, current_app
from utils.auth import TokenManager
import time

# Create a Blueprint for debug routes
debug_bp = Blueprint('debug', __name__)

def get_token_manager():
    """Helper function to get a token manager instance with app context."""
    # Get configuration from the app context
    config = {
        'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
        'VERTEIL_TOKEN_ENDPOINT': current_app.config.get('VERTEIL_TOKEN_ENDPOINT', '/api/v1/oauth/token'),
        'VERTEIL_USERNAME': current_app.config.get('VERTEIL_USERNAME'),
        'VERTEIL_PASSWORD': current_app.config.get('VERTEIL_PASSWORD'),
        'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
        'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
        'OAUTH2_TOKEN_EXPIRY_BUFFER': current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 300)
    }
    
    # Create and configure the token manager
    token_manager = TokenManager.get_instance()
    token_manager.set_config(config)
    return token_manager

@debug_bp.route('/api/debug/token', methods=['GET'])
async def get_token_status():
    """
    Debug endpoint to check the current token status.
    This helps verify that token caching and refresh are working correctly.
    """
    try:
        token_manager = get_token_manager()
        token_info = token_manager.get_token_info()
        
        # Get a fresh token to show the current state (will use cached if valid)
        try:
            token = token_manager.get_token()
            token_info['token_available'] = bool(token)
            # Don't expose the actual token in the response for security
            token_info['token_preview'] = f"{token[:10]}..." if token else None
        except Exception as e:
            token_info['error'] = str(e)
        
        return jsonify({
            'status': 'success',
            'data': token_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@debug_bp.route('/api/debug/clear-token', methods=['POST'])
async def clear_token():
    """
    Debug endpoint to clear the current token, forcing a refresh on next request.
    Note: In production, you should add authentication to this endpoint.
    """
    try:
        token_manager = get_token_manager()
        token_manager.clear_token()
        
        return jsonify({
            'status': 'success',
            'message': 'Token cache cleared. A new token will be generated on the next request.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
