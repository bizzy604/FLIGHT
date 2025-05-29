"""
Test script to verify imports and basic functionality.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    # Test importing the app
    from Backend.app import create_app
    print("✅ Successfully imported create_app from Backend.app")
    
    # Test importing flight service
    from Backend.services.flight_service import search_flights
    print("✅ Successfully imported search_flights from Backend.services.flight_service")
    
    # Test importing routes
    from Backend.routes.verteil_flights import bp
    print("✅ Successfully imported bp from Backend.routes.verteil_flights")
    
    print("\n✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Python path: {sys.path}")
    raise
