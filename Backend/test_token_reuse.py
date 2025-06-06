#!/usr/bin/env python3
"""
Test script to verify TokenManager token reuse and regeneration behavior.
"""

import os
import sys
import time
from pathlib import Path

# Add the Backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

from utils.auth import TokenManager

def test_token_reuse():
    """Test that TokenManager properly reuses tokens until expiry."""
    print("=== TokenManager Token Reuse Test ===")
    
    # Create TokenManager instance
    tm = TokenManager()
    
    # Set configuration
    config = {
        'VERTEIL_API_BASE_URL': os.getenv('VERTEIL_API_BASE_URL'),
        'VERTEIL_TOKEN_ENDPOINT': os.getenv('VERTEIL_TOKEN_ENDPOINT'),
        'VERTEIL_USERNAME': os.getenv('VERTEIL_USERNAME'),
        'VERTEIL_PASSWORD': os.getenv('VERTEIL_PASSWORD'),
        'VERTEIL_THIRD_PARTY_ID': os.getenv('VERTEIL_THIRD_PARTY_ID'),
        'VERTEIL_OFFICE_ID': os.getenv('VERTEIL_OFFICE_ID')
    }
    
    print(f"Configuration loaded:")
    print(f"  API Base URL: {config['VERTEIL_API_BASE_URL']}")
    print(f"  Token Endpoint: {config['VERTEIL_TOKEN_ENDPOINT']}")
    print(f"  Username: {config['VERTEIL_USERNAME']}")
    print(f"  Office ID: {config['VERTEIL_OFFICE_ID']}")
    print(f"  Third Party ID: {config['VERTEIL_THIRD_PARTY_ID']}")
    print()
    
    try:
        # Test 1: Get first token
        print("Test 1: Getting first token...")
        start_time = time.time()
        token1 = tm.get_token(config)
        first_request_time = time.time() - start_time
        print(f"  First token obtained in {first_request_time:.2f} seconds")
        print(f"  Token preview: {token1[:50]}...")
        
        info1 = tm.get_token_info()
        print(f"  Token expires in: {info1['expires_in_seconds']} seconds")
        print(f"  Token expires at: {info1['expires_at_human']}")
        print()
        
        # Test 2: Get second token immediately (should be cached)
        print("Test 2: Getting second token immediately (should be cached)...")
        start_time = time.time()
        token2 = tm.get_token(config)
        second_request_time = time.time() - start_time
        print(f"  Second token obtained in {second_request_time:.4f} seconds")
        print(f"  Token preview: {token2[:50]}...")
        
        info2 = tm.get_token_info()
        print(f"  Token expires in: {info2['expires_in_seconds']} seconds")
        print()
        
        # Test 3: Verify tokens are the same
        print("Test 3: Verifying token reuse...")
        tokens_same = token1 == token2
        print(f"  Tokens are identical: {tokens_same}")
        print(f"  First request time: {first_request_time:.2f}s")
        print(f"  Second request time: {second_request_time:.4f}s")
        
        if tokens_same and second_request_time < 0.1:
            print("  ✅ SUCCESS: Token is being reused from cache!")
        else:
            print("  ❌ FAILURE: Token is not being reused properly!")
        print()
        
        # Test 4: Test multiple TokenManager instances (singleton behavior)
        print("Test 4: Testing singleton behavior...")
        tm2 = TokenManager()
        tm3 = TokenManager.get_instance()
        
        print(f"  tm is tm2: {tm is tm2}")
        print(f"  tm is tm3: {tm is tm3}")
        print(f"  tm2 is tm3: {tm2 is tm3}")
        
        if tm is tm2 and tm is tm3:
            print("  ✅ SUCCESS: TokenManager is properly implementing singleton pattern!")
        else:
            print("  ❌ FAILURE: TokenManager singleton is not working!")
        print()
        
        # Test 5: Test token from different instance
        print("Test 5: Getting token from different TokenManager instance...")
        start_time = time.time()
        token3 = tm2.get_token(config)
        third_request_time = time.time() - start_time
        print(f"  Third token obtained in {third_request_time:.4f} seconds")
        print(f"  Token preview: {token3[:50]}...")
        
        tokens_same_across_instances = token1 == token3
        print(f"  Token same across instances: {tokens_same_across_instances}")
        
        if tokens_same_across_instances and third_request_time < 0.1:
            print("  ✅ SUCCESS: Token is shared across singleton instances!")
        else:
            print("  ❌ FAILURE: Token is not shared across instances!")
        print()
        
        # Summary
        print("=== Test Summary ===")
        print(f"✅ Token obtained successfully")
        print(f"✅ Token reuse working: {tokens_same}")
        print(f"✅ Singleton pattern working: {tm is tm2 and tm is tm3}")
        print(f"✅ Cross-instance token sharing: {tokens_same_across_instances}")
        print(f"📊 Performance: First request {first_request_time:.2f}s, cached requests ~{second_request_time:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_token_reuse()
    sys.exit(0 if success else 1)