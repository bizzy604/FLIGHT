#!/usr/bin/env python3
"""
Test script to verify that flight price request filtering works correctly for Emirates (EK).
This script tests that when a user selects an Emirates flight,
only Emirates data is included in the flight price request.
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


def test_emirates_filtering():
    """Test that flight price request only includes Emirates data when Emirates flight is selected."""
    
    # Load the actual multi-airline air shopping response data
    test_data_file = Path("Output/FRONTEND_FLIGHT_PRICE_REQUEST_20250705_203531.json")
    if not test_data_file.exists():
        logger.error(f"Test data file not found: {test_data_file}")
        return False
    
    with open(test_data_file, 'r') as f:
        frontend_request_data = json.load(f)
    
    # Extract the air shopping response
    airshopping_response = frontend_request_data["data"]["air_shopping_response"]
    logger.info("Loaded actual multi-airline air shopping response")
    
    # Check if it's a multi-airline response
    is_multi_airline = MultiAirlineDetector.is_multi_airline_response(airshopping_response)
    logger.info(f"Multi-airline response: {is_multi_airline}")
    
    if not is_multi_airline:
        logger.warning("Test data is not a multi-airline response")
        return False
    
    # Check what airlines are in the original data
    data_lists = airshopping_response.get("DataLists", {})
    travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    original_airlines = set()
    for traveler in travelers:
        object_key = traveler.get("ObjectKey", "")
        if "-" in object_key:
            airline = object_key.split("-")[0]
            original_airlines.add(airline)
    
    logger.info(f"Original airlines in air shopping response: {original_airlines}")
    
    # Test with Emirates offer indices (based on the search results, EK offers start around index 25)
    emirates_test_cases = [
        {"offer_index": 25, "description": "First Emirates offer (EK720)"},
        {"offer_index": 41, "description": "Second Emirates offer (EK720 with different route)"},
        {"offer_index": 94, "description": "Third Emirates offer (EK720 with different segments)"},
        {"offer_index": 117, "description": "Fourth Emirates offer (EK720)"}
    ]
    
    for test_case in emirates_test_cases:
        logger.info(f"\n--- Testing {test_case['description']} ---")
        
        try:
            # Build flight price request for Emirates offer
            flight_price_request = build_flight_price_request(
                airshopping_response=airshopping_response,
                selected_offer_index=test_case["offer_index"]
            )
            
            # Analyze the result
            data_lists = flight_price_request.get("DataLists", {})
            
            # Check all DataLists sections for airline filtering
            all_airlines_found = set()
            
            # Check AnonymousTravelerList
            travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
            if travelers:
                for traveler in travelers:
                    object_key = traveler.get("ObjectKey", "")
                    if "-" in object_key:
                        airline = object_key.split("-")[0]
                        all_airlines_found.add(airline)
            
            # Check CarryOnAllowanceList
            carry_on_allowances = data_lists.get("CarryOnAllowanceList", {}).get("CarryOnAllowance", [])
            if carry_on_allowances:
                for allowance in carry_on_allowances:
                    list_key = allowance.get("ListKey", "")
                    if "-" in list_key:
                        airline = list_key.split("-")[0]
                        all_airlines_found.add(airline)
            
            # Check CheckedBagAllowanceList
            checked_bag_allowances = data_lists.get("CheckedBagAllowanceList", {}).get("CheckedBagAllowance", [])
            if checked_bag_allowances:
                for allowance in checked_bag_allowances:
                    list_key = allowance.get("ListKey", "")
                    if "-" in list_key:
                        airline = list_key.split("-")[0]
                        all_airlines_found.add(airline)
            
            # Check FareGroup (FareList)
            fare_groups = data_lists.get("FareGroup", [])
            if fare_groups:
                for fare_group in fare_groups:
                    list_key = fare_group.get("ListKey", "")
                    if "-" in list_key:
                        airline = list_key.split("-")[0]
                        all_airlines_found.add(airline)
            
            # Check FlightSegmentList
            flight_segments = data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
            if flight_segments:
                for segment in flight_segments:
                    segment_key = segment.get("SegmentKey", "")
                    if "-" in segment_key:
                        airline = segment_key.split("-")[0]
                        all_airlines_found.add(airline)
            
            # Check FlightList
            flights = data_lists.get("FlightList", {}).get("Flight", [])
            if flights:
                for flight in flights:
                    flight_key = flight.get("FlightKey", "")
                    if "-" in flight_key:
                        airline = flight_key.split("-")[0]
                        all_airlines_found.add(airline)
            
            logger.info(f"Airlines found in flight price request: {all_airlines_found}")
            
            # Verify that only Emirates (EK) data is present
            if all_airlines_found == {"EK"}:
                logger.info(f"✅ SUCCESS: Only Emirates (EK) data found in flight price request")
            elif len(all_airlines_found) == 0:
                logger.warning("⚠️  WARNING: No airline data found")
                return False
            else:
                logger.error(f"❌ FAILURE: Multiple airlines found: {all_airlines_found}")
                logger.error("Flight price request should only contain Emirates (EK) data!")
                return False
            
            # Additional check: verify the offer ID belongs to Emirates
            query_offers = flight_price_request.get("Query", {}).get("Offers", {}).get("Offer", [])
            if query_offers:
                offer_id_node = query_offers[0].get("OfferID", {})
                owner = offer_id_node.get("Owner", "")
                if owner == "EK":
                    logger.info(f"✅ SUCCESS: Offer ID belongs to Emirates (Owner: {owner})")
                else:
                    logger.error(f"❌ FAILURE: Offer ID belongs to {owner}, not Emirates!")
                    return False
            
        except Exception as e:
            logger.error(f"❌ ERROR testing Emirates offer index {test_case['offer_index']}: {str(e)}")
            return False
    
    logger.info("\n🎉 All Emirates filtering tests passed! Only Emirates data is included when Emirates flight is selected.")
    return True


if __name__ == "__main__":
    success = test_emirates_filtering()
    sys.exit(0 if success else 1)
