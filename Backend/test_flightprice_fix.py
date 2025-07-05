#!/usr/bin/env python3
"""
Test script to verify the FlightPrice request structure fix.
"""

import json
import logging
from scripts.build_flightprice_rq import build_flight_price_request

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_flightprice_structure():
    """Test the FlightPrice request structure with the latest air shopping response."""
    
    # Load test air shopping response
    try:
        with open('tests/airshopingresponse.json', 'r') as f:
            air_shopping_response = json.load(f)
    except FileNotFoundError:
        logger.error("Test air shopping response file not found")
        return False
    
    # Test with first offer (index 0)
    try:
        logger.info("Testing minimal FlightPrice request structure...")

        # Build flight price request
        flight_price_request = build_flight_price_request(
            airshopping_response=air_shopping_response,
            selected_offer_index=0  # First offer
        )
        
        # Validate the structure
        logger.info("Validating FlightPrice request structure...")
        
        # Check Query.OriginDestination structure
        query = flight_price_request.get('Query', {})
        origin_destinations = query.get('OriginDestination', [])
        
        if not origin_destinations:
            logger.error("❌ No OriginDestination found in Query")
            return False
        
        # Check if OriginDestination has correct structure
        for i, od in enumerate(origin_destinations):
            if 'Flight' in od:
                logger.error(f"❌ OriginDestination[{i}] has 'Flight' structure (old format)")
                logger.error(f"   Found: {list(od.keys())}")
                return False
            elif 'OriginDestinationKey' in od and 'FlightReferences' in od:
                logger.info(f"✅ OriginDestination[{i}] has correct structure")
                logger.info(f"   OriginDestinationKey: {od.get('OriginDestinationKey')}")
                logger.info(f"   FlightReferences: {od.get('FlightReferences', {}).get('value', [])}")
            else:
                logger.error(f"❌ OriginDestination[{i}] has unknown structure: {list(od.keys())}")
                return False
        
        # Check DataLists structure
        data_lists = flight_price_request.get('DataLists', {})
        required_sections = ['AnonymousTravelerList', 'FlightSegmentList', 'FlightList']
        
        for section in required_sections:
            if section in data_lists:
                logger.info(f"✅ DataLists contains {section}")
            else:
                logger.warning(f"⚠️  DataLists missing {section}")
        
        # Check that only mandatory sections are included
        expected_sections = ['FareGroup', 'AnonymousTravelerList']
        optional_sections = ['CarryOnAllowanceList', 'CheckedBagAllowanceList', 'FlightSegmentList', 'FlightList', 'OriginDestinationList']

        for section in expected_sections:
            if section in data_lists:
                logger.info(f"✅ DataLists contains mandatory {section}")
            else:
                logger.error(f"❌ DataLists missing mandatory {section}")
                return False

        for section in optional_sections:
            if section in data_lists:
                logger.warning(f"⚠️  DataLists contains optional {section} (should be minimal)")
            else:
                logger.info(f"✅ DataLists correctly excludes optional {section}")
        
        # Save the request for inspection
        output_file = 'Output/FlightPrice_REQUEST_MINIMAL_TEST.json'
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": "2025-07-05T21:09:00.000000",
                "description": "Fixed FlightPrice API Request Payload",
                "data": {
                    "url": "https://api.stage.verteil.com/entrygate/rest/request:flightPrice",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "*/*",
                        "OfficeId": "OFF3746",
                        "service": "FlightPrice",
                        "User-Agent": "PostmanRuntime/7.41",
                        "Cache-Control": "no-cache",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "ThirdpartyId": "KL"
                    },
                    "payload": flight_price_request
                }
            }, f, indent=2)
        
        logger.info(f"✅ Minimal FlightPrice request saved to: {output_file}")
        logger.info("🎯 Minimal FlightPrice request structure validation PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing FlightPrice structure: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_flightprice_structure()
    if success:
        print("\n🎉 FlightPrice structure fix validation SUCCESSFUL!")
    else:
        print("\n💥 FlightPrice structure fix validation FAILED!")
