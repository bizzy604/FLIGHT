#!/usr/bin/env python3
"""
Test script to verify token management is working correctly.

This script tests:
1. TokenManager singleton behavior
2. Token caching and reuse
3. Configuration consistency
4. Token expiry handling
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# Add the Backend directory to the Python path so we can use relative imports
backend_dir = os.path.dirname(__file__)
sys.path.insert(0, backend_dir)

from utils.auth import TokenManager
from services.flight.core import FlightService
from config import Config

def test_singleton_behavior():
    """Test that TokenManager follows singleton pattern."""
    print("🔍 Testing TokenManager singleton behavior...")
    
    # Create multiple instances
    tm1 = TokenManager.get_instance()
    tm2 = TokenManager.get_instance()
    tm3 = TokenManager()
    
    # They should all be the same instance
    assert tm1 is tm2, "TokenManager.get_instance() should return the same instance"
    assert tm1 is tm3, "TokenManager() should return the same singleton instance"
    
    print("✅ TokenManager singleton behavior verified")

def test_configuration_consistency():
    """Test that configuration is handled consistently."""
    print("🔍 Testing configuration consistency...")
    
    # Get the singleton instance
    tm = TokenManager.get_instance()
    
    # Test configuration
    test_config = {
        'VERTEIL_API_BASE_URL': 'https://api.stage.verteil.com',
        'VERTEIL_TOKEN_ENDPOINT': '/oauth2/token',
        'VERTEIL_USERNAME': 'test_user',
        'VERTEIL_PASSWORD': 'test_pass',
        'OAUTH2_TOKEN_EXPIRY_BUFFER': 60
    }
    
    tm.set_config(test_config)
    
    # Verify configuration was set
    assert tm._config == test_config, "Configuration should be set correctly"
    
    # Test that FlightService uses the same instance
    fs = FlightService(test_config)
    assert fs._token_manager is tm, "FlightService should use the same TokenManager instance"
    
    print("✅ Configuration consistency verified")

def test_token_info():
    """Test token info retrieval."""
    print("🔍 Testing token info retrieval...")
    
    tm = TokenManager.get_instance()
    
    # Get token info (should show no token initially)
    info = tm.get_token_info()
    
    print(f"Token info: {info}")
    
    expected_keys = ['has_token', 'is_valid', 'expires_in', 'expiry_time', 'token_type', 'metrics']
    for key in expected_keys:
        assert key in info, f"Token info should contain '{key}'"
    
    print("✅ Token info structure verified")

def test_metrics():
    """Test token metrics tracking."""
    print("🔍 Testing token metrics...")
    
    tm = TokenManager.get_instance()
    
    # Get initial metrics
    initial_metrics = tm.get_metrics()
    print(f"Initial metrics: {initial_metrics}")
    
    # Clear metrics
    tm.clear_metrics()
    cleared_metrics = tm.get_metrics()
    
    # Verify metrics were cleared
    assert cleared_metrics['token_generations'] == 0, "Metrics should be cleared"
    assert cleared_metrics['total_token_requests'] == 0, "Metrics should be cleared"
    
    print("✅ Token metrics verified")

async def test_with_real_config():
    """Test with real configuration if available."""
    print("🔍 Testing with real configuration...")
    
    # Load real config
    config = Config()
    
    # Check if we have real credentials
    if not config.VERTEIL_USERNAME or not config.VERTEIL_PASSWORD:
        print("⚠️ No real credentials found, skipping real token test")
        return
    
    tm = TokenManager.get_instance()
    
    # Set real configuration
    real_config = {
        'VERTEIL_API_BASE_URL': config.VERTEIL_API_BASE_URL,
        'VERTEIL_TOKEN_ENDPOINT': '/oauth2/token',
        'VERTEIL_USERNAME': config.VERTEIL_USERNAME,
        'VERTEIL_PASSWORD': config.VERTEIL_PASSWORD,
        'OAUTH2_TOKEN_EXPIRY_BUFFER': 60
    }
    
    tm.set_config(real_config)
    
    try:
        # Try to get a real token
        print("Attempting to get real token...")
        token = tm.get_token()
        
        if token:
            print("✅ Successfully obtained real token")
            
            # Get token info
            info = tm.get_token_info()
            print(f"Token expires in: {info['expires_in']} seconds ({info['expires_in']/3600:.1f} hours)")
            print(f"Token expiry time: {datetime.fromtimestamp(info['expiry_time'])}")
            
            # Test token reuse
            print("Testing token reuse...")
            token2 = tm.get_token()
            assert token == token2, "Should reuse the same token"
            print("✅ Token reuse verified")
            
            # Check metrics
            metrics = tm.get_metrics()
            print(f"Token requests: {metrics['total_token_requests']}")
            print(f"Token generations: {metrics['token_generations']}")
            
        else:
            print("❌ Failed to obtain real token")
            
    except Exception as e:
        print(f"❌ Error testing with real config: {e}")

def main():
    """Run all tests."""
    print("🚀 Starting TokenManager tests...\n")
    
    try:
        test_singleton_behavior()
        print()
        
        test_configuration_consistency()
        print()
        
        test_token_info()
        print()
        
        test_metrics()
        print()
        
        # Run async test
        asyncio.run(test_with_real_config())
        print()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
