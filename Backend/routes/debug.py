from quart import Blueprint, jsonify, current_app
from utils.auth import TokenManager
import time

# Create a Blueprint for debug routes
bp = Blueprint('debug', __name__)

def init_app(app):
    """Initialize the debug routes with the app."""
    # Any initialization can go here
    return app

def get_token_manager():
    """Helper function to get a token manager instance with app context."""
    # Get the singleton TokenManager instance
    token_manager = TokenManager.get_instance()

    # Only set config if TokenManager doesn't have one yet, to avoid overwriting
    # the centralized configuration
    if not token_manager._config:
        config = {
            'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
            'VERTEIL_TOKEN_ENDPOINT': current_app.config.get('VERTEIL_TOKEN_ENDPOINT') or current_app.config.get('VERTEIL_TOKEN_ENDPOINT_PATH', '/oauth2/token'),
            'VERTEIL_USERNAME': current_app.config.get('VERTEIL_USERNAME'),
            'VERTEIL_PASSWORD': current_app.config.get('VERTEIL_PASSWORD'),
            'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
            'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
            'OAUTH2_TOKEN_EXPIRY_BUFFER': current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 300)
        }
        token_manager.set_config(config)

    return token_manager

@bp.route('/debug/token', methods=['GET'])
async def get_token_status():
    """
    Debug endpoint to check the current token status.
    This helps verify that token caching and refresh are working correctly.
    """
    try:
        # Get a token manager instance with current app config
        token_manager = get_token_manager()
        
        # Get the current token (this will use cached or fetch new if needed)
        token = token_manager.get_token()

        # Get token info without triggering a refresh
        token_info = token_manager.get_token_info()
        
        return jsonify({
            'status': 'success',
            'token_available': token is not None,
            'token_info': token_info,
            'config': {
                'api_base': current_app.config.get('VERTEIL_API_BASE_URL'),
                'token_endpoint': current_app.config.get('VERTEIL_TOKEN_ENDPOINT'),
                'username_set': bool(current_app.config.get('VERTEIL_USERNAME')),
                'password_set': bool(current_app.config.get('VERTEIL_PASSWORD')),
                'token_expiry_buffer': current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER')
            },
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'config': {k: '***' if 'PASSWORD' in k or 'SECRET' in k or 'TOKEN' in k or 'KEY' in k else v 
                     for k, v in current_app.config.items()}
        }), 500

@bp.route('/debug/clear-token', methods=['POST'])
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
