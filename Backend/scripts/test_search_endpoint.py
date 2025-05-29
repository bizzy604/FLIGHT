"""
Test script for the flight search endpoint.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import after setting up the path
from services.flight_service import search_flights

def test_flight_search():
    """Test the flight search functionality."""
    try:
        logger.info("Testing flight search...")
        
        # Test parameters
        search_params = {
            'origin': 'JFK',
            'destination': 'LAX',
            'departure_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'return_date': (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d'),
            'adults': 1,
            'children': 0,
            'infants': 0,
            'cabin_class': 'ECONOMY',
            'trip_type': 'roundtrip'
        }
        
        logger.info(f"Search parameters: {json.dumps(search_params, indent=2)}")
        
        # Call the search function
        result = search_flights(**search_params)
        
        # Log the result
        logger.info("Search successful!")
        logger.info(f"Found {len(result.get('flightOffers', []))} flight offers")
        
        if 'flightOffers' in result and len(result['flightOffers']) > 0:
            offer = result['flightOffers'][0]
            logger.info(f"Sample offer:\n{json.dumps(offer, indent=2)}")
        
        return True
    
    except Exception as e:
        logger.error(f"Flight search test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_flight_search()
