#!/usr/bin/env python3
"""
Test script to verify TokenManager token access works
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def test_token_access():
    """Test that we can access the TokenManager token directly"""
    try:
        from utils.auth import TokenManager
        
        # Get the TokenManager instance
        token_manager = TokenManager.get_instance()
        
        print("Testing TokenManager token access...")
        
        # Check if token is available
        token_info = token_manager.get_token_info()
        print(f"Token available: {token_info['has_token']}")
        print(f"Token valid: {token_info['is_valid']}")
        print(f"Expires in: {token_info['expires_in']} seconds")
        
        if token_info['has_token'] and token_info['is_valid']:
            # Get the actual token
            bearer_token = token_manager.get_token()
            print(f"Token format: {bearer_token[:20]}...")
            print("TokenManager works perfectly!")
            return True
        else:
            print("Token not available or invalid")
            return False
            
    except Exception as e:
        print(f"Error accessing TokenManager: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_token_access())
    if result:
        print("\nSUCCESS: TokenManager token access works!")
        print("The issue must be in the route error handling or module caching.")
    else:
        print("\nFAILED: TokenManager token access failed")