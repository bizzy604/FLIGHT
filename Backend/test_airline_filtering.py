#!/usr/bin/env python3
"""
Test script to verify that flight price request filtering works correctly.
This script tests that when a user selects a specific airline flight,
only that airline's data is included in the flight price request.
"""

import json
import logging
import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from scripts.build_flightprice_rq import build_flight_price_request
from utils.multi_airline_detector import MultiAirlineDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_airline_filtering():
    """Test that flight price request only includes selected airline data."""
    
    # Load test data
    test_data_file = Path("tests/airshopingRS.json")
    if not test_data_file.exists():
        logger.error(f"Test data file not found: {test_data_file}")
        return False
    
    with open(test_data_file, 'r') as f:
        airshopping_response = json.load(f)
    
    logger.info("Loaded test data successfully")
    
    # Check if it's a multi-airline response
    is_multi_airline = MultiAirlineDetector.is_multi_airline_response(airshopping_response)
    logger.info(f"Multi-airline response: {is_multi_airline}")
    
    if not is_multi_airline:
        logger.warning("Test data is not a multi-airline response")
        return False
    
    # Test with different offer indices to simulate selecting different airlines
    test_cases = [
        {"offer_index": 0, "description": "First offer (should be KQ)"},
        {"offer_index": 50, "description": "Middle offer"},
        {"offer_index": 100, "description": "Later offer"}
    ]
    
    for test_case in test_cases:
        logger.info(f"\n--- Testing {test_case['description']} ---")
        
        try:
            # Build flight price request
            flight_price_request = build_flight_price_request(
                airshopping_response=airshopping_response,
                selected_offer_index=test_case["offer_index"]
            )
            
            # Analyze the result
            data_lists = flight_price_request.get("DataLists", {})
            
            # Check AnonymousTravelerList
            travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
            if travelers:
                traveler_airlines = set()
                for traveler in travelers:
                    object_key = traveler.get("ObjectKey", "")
                    if "-" in object_key:
                        airline = object_key.split("-")[0]
                        traveler_airlines.add(airline)
                
                logger.info(f"Traveler airlines found: {traveler_airlines}")
            
            # Check CarryOnAllowanceList
            carry_on_allowances = data_lists.get("CarryOnAllowanceList", {}).get("CarryOnAllowance", [])
            if carry_on_allowances:
                carry_on_airlines = set()
                for allowance in carry_on_allowances:
                    list_key = allowance.get("ListKey", "")
                    if "-" in list_key:
                        airline = list_key.split("-")[0]
                        carry_on_airlines.add(airline)
                
                logger.info(f"Carry-on allowance airlines found: {carry_on_airlines}")
            
            # Check CheckedBagAllowanceList
            checked_bag_allowances = data_lists.get("CheckedBagAllowanceList", {}).get("CheckedBagAllowance", [])
            if checked_bag_allowances:
                checked_bag_airlines = set()
                for allowance in checked_bag_allowances:
                    list_key = allowance.get("ListKey", "")
                    if "-" in list_key:
                        airline = list_key.split("-")[0]
                        checked_bag_airlines.add(airline)
                
                logger.info(f"Checked bag allowance airlines found: {checked_bag_airlines}")
            
            # Check FareList
            fare_groups = data_lists.get("FareGroup", [])
            if fare_groups:
                fare_airlines = set()
                for fare_group in fare_groups:
                    list_key = fare_group.get("ListKey", "")
                    if "-" in list_key:
                        airline = list_key.split("-")[0]
                        fare_airlines.add(airline)
                
                logger.info(f"Fare group airlines found: {fare_airlines}")
            
            # Check FlightSegmentList
            flight_segments = data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
            if flight_segments:
                segment_airlines = set()
                for segment in flight_segments:
                    segment_key = segment.get("SegmentKey", "")
                    if "-" in segment_key:
                        airline = segment_key.split("-")[0]
                        segment_airlines.add(airline)
                
                logger.info(f"Flight segment airlines found: {segment_airlines}")
            
            # Collect all airlines found
            all_airlines = set()
            if 'traveler_airlines' in locals():
                all_airlines.update(traveler_airlines)
            if 'carry_on_airlines' in locals():
                all_airlines.update(carry_on_airlines)
            if 'checked_bag_airlines' in locals():
                all_airlines.update(checked_bag_airlines)
            if 'fare_airlines' in locals():
                all_airlines.update(fare_airlines)
            if 'segment_airlines' in locals():
                all_airlines.update(segment_airlines)
            
            logger.info(f"All airlines found in flight price request: {all_airlines}")
            
            # Check if filtering worked (should only have one airline)
            if len(all_airlines) == 1:
                logger.info(f"✅ SUCCESS: Only one airline found: {list(all_airlines)[0]}")
            elif len(all_airlines) == 0:
                logger.warning("⚠️  WARNING: No airline data found")
            else:
                logger.error(f"❌ FAILURE: Multiple airlines found: {all_airlines}")
                logger.error("Flight price request should only contain data for the selected airline!")
                return False
            
        except Exception as e:
            logger.error(f"❌ ERROR testing offer index {test_case['offer_index']}: {str(e)}")
            return False
    
    logger.info("\n🎉 All tests passed! Airline filtering is working correctly.")
    return True


if __name__ == "__main__":
    success = test_airline_filtering()
    sys.exit(0 if success else 1)
