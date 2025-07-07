#!/usr/bin/env python3
"""
Test script to verify token persistence across server restarts.

This script tests:
1. Token generation and disk persistence
2. Token loading from disk on restart
3. Token expiry handling
4. File cleanup on token clear
"""

import sys
import os
import time
import tempfile
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = os.path.dirname(__file__)
sys.path.insert(0, backend_dir)

from utils.auth import TokenManager
from config import Config

def test_token_persistence():
    """Test token persistence functionality."""
    print("🔍 Testing Token Persistence...")
    
    # Test 1: Generate and save token
    print("\n1️⃣ Testing token generation and persistence...")
    
    # Clear any existing singleton instance for clean test
    TokenManager._instance = None
    
    # Create first instance and get token
    tm1 = TokenManager.get_instance()
    
    # Set real configuration
    config = Config()
    if config.VERTEIL_USERNAME and config.VERTEIL_PASSWORD:
        auth_config = {
            'VERTEIL_API_BASE_URL': config.VERTEIL_API_BASE_URL,
            'VERTEIL_TOKEN_ENDPOINT': '/oauth2/token',
            'VERTEIL_USERNAME': config.VERTEIL_USERNAME,
            'VERTEIL_PASSWORD': config.VERTEIL_PASSWORD,
            'OAUTH2_TOKEN_EXPIRY_BUFFER': 60
        }
        tm1.set_config(auth_config)
        
        try:
            print("Generating new token...")
            token1 = tm1.get_token()
            print(f"✅ Token generated: {token1[:20]}...")
            
            # Check if token file exists
            token_file = tm1._get_token_file_path()
            if os.path.exists(token_file):
                print(f"✅ Token saved to disk: {token_file}")
            else:
                print("❌ Token file not found on disk")
                return False
                
        except Exception as e:
            print(f"❌ Failed to generate token: {e}")
            return False
    else:
        print("⚠️ No credentials found, using mock test...")
        # Mock test without real API call
        tm1._token = "mock_token_12345"
        tm1._token_data = {"access_token": "mock_token_12345", "expires_in": 43200}
        tm1._token_expiry = int(time.time()) + 43200
        tm1._save_token_to_disk()
        token_file = tm1._get_token_file_path()
        print(f"✅ Mock token saved to disk: {token_file}")
    
    # Test 2: Simulate server restart by creating new instance
    print("\n2️⃣ Testing token loading after 'server restart'...")
    
    # Clear singleton to simulate restart
    original_token = tm1._token
    original_expiry = tm1._token_expiry
    TokenManager._instance = None
    
    # Create new instance (simulates server restart)
    tm2 = TokenManager.get_instance()
    
    if tm2._token:
        print(f"✅ Token loaded from disk: {tm2._token[:20]}...")
        print(f"✅ Token expiry: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tm2._token_expiry))}")
        
        # Verify it's the same token
        if tm2._token == original_token and tm2._token_expiry == original_expiry:
            print("✅ Loaded token matches original token")
        else:
            print("❌ Loaded token doesn't match original")
            return False
    else:
        print("❌ No token loaded from disk")
        return False
    
    # Test 3: Test token clearing removes file
    print("\n3️⃣ Testing token cleanup...")
    
    token_file = tm2._get_token_file_path()
    tm2.clear_token()
    
    if not os.path.exists(token_file):
        print("✅ Token file cleaned up after clear_token()")
    else:
        print("❌ Token file still exists after clear_token()")
        return False
    
    if not tm2._token:
        print("✅ In-memory token cleared")
    else:
        print("❌ In-memory token not cleared")
        return False
    
    print("\n🎉 All token persistence tests passed!")
    return True

def test_token_expiry_handling():
    """Test handling of expired tokens."""
    print("\n🔍 Testing expired token handling...")
    
    # Clear singleton
    TokenManager._instance = None
    
    tm = TokenManager.get_instance()
    
    # Create an expired token file
    token_file = tm._get_token_file_path()
    expired_token_data = {
        'access_token': 'expired_token_12345',
        'token_data': {'access_token': 'expired_token_12345', 'expires_in': 3600},
        'token_expiry': int(time.time()) - 3600,  # Expired 1 hour ago
        'saved_at': int(time.time()) - 7200  # Saved 2 hours ago
    }
    
    # Write expired token to file
    import json
    with open(token_file, 'w') as f:
        json.dump(expired_token_data, f)
    
    print(f"Created expired token file: {token_file}")
    
    # Clear singleton and create new instance
    TokenManager._instance = None
    tm = TokenManager.get_instance()
    
    # Check that expired token was not loaded
    if not tm._token:
        print("✅ Expired token was not loaded")
    else:
        print("❌ Expired token was incorrectly loaded")
        return False
    
    # Check that expired token file was cleaned up
    if not os.path.exists(token_file):
        print("✅ Expired token file was cleaned up")
    else:
        print("❌ Expired token file was not cleaned up")
        return False
    
    print("✅ Expired token handling test passed!")
    return True

def test_persistence_disable():
    """Test disabling persistence via environment variable."""
    print("\n🔍 Testing persistence disable...")
    
    # Set environment variable to disable persistence
    os.environ['DISABLE_TOKEN_PERSISTENCE'] = 'true'
    
    # Clear singleton
    TokenManager._instance = None
    
    tm = TokenManager.get_instance()
    
    if not tm._enable_persistence:
        print("✅ Persistence disabled via environment variable")
    else:
        print("❌ Persistence not disabled")
        return False
    
    # Clean up
    del os.environ['DISABLE_TOKEN_PERSISTENCE']
    
    print("✅ Persistence disable test passed!")
    return True

def main():
    """Run all persistence tests."""
    print("🚀 Starting Token Persistence Tests...\n")
    
    try:
        # Run all tests
        test1_passed = test_token_persistence()
        test2_passed = test_token_expiry_handling()
        test3_passed = test_persistence_disable()
        
        if test1_passed and test2_passed and test3_passed:
            print("\n🎉 All token persistence tests completed successfully!")
            print("\n📋 Summary:")
            print("✅ Tokens are now persisted to disk")
            print("✅ Tokens survive server restarts")
            print("✅ Expired tokens are properly handled")
            print("✅ Token cleanup works correctly")
            print("✅ Persistence can be disabled if needed")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
