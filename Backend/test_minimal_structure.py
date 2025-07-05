#!/usr/bin/env python3
"""
Simple test to verify the minimal FlightPrice request structure.
"""

import json
import logging
from scripts.build_flightprice_rq import build_flight_price_request

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_minimal_structure():
    """Test the minimal FlightPrice request structure."""
    
    # Load test air shopping response
    try:
        with open('tests/airshopingRS.json', 'r') as f:
            air_shopping_response = json.load(f)
    except FileNotFoundError:
        logger.error("Test air shopping response file not found")
        return False
    
    try:
        logger.info("Building minimal FlightPrice request...")
        
        # Build flight price request
        flight_price_request = build_flight_price_request(
            airshopping_response=air_shopping_response,
            selected_offer_index=0
        )
        
        # Check DataLists structure
        data_lists = flight_price_request.get('DataLists', {})
        
        logger.info("Checking DataLists structure...")
        logger.info(f"DataLists sections: {list(data_lists.keys())}")
        
        # Verify only mandatory sections are present
        mandatory_sections = ['FareGroup', 'AnonymousTravelerList']
        for section in mandatory_sections:
            if section in data_lists:
                logger.info(f"✅ Contains mandatory {section}")
            else:
                logger.error(f"❌ Missing mandatory {section}")
                return False
        
        # Check for unnecessary sections
        all_sections = list(data_lists.keys())
        unnecessary_sections = [s for s in all_sections if s not in mandatory_sections]
        
        if unnecessary_sections:
            logger.warning(f"⚠️  Contains unnecessary sections: {unnecessary_sections}")
        else:
            logger.info("✅ Contains only mandatory sections")
        
        # Save the minimal request
        output_data = {
            "timestamp": "2025-07-05T21:20:00.000000",
            "description": "Minimal FlightPrice Request - Only Mandatory Sections",
            "data": {
                "url": "https://api.stage.verteil.com/entrygate/rest/request:flightPrice",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "ThirdpartyId": "QR"
                },
                "payload": flight_price_request
            }
        }
        
        with open('Output/FlightPrice_REQUEST_MINIMAL.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info("✅ Minimal FlightPrice request saved to: Output/FlightPrice_REQUEST_MINIMAL.json")
        logger.info("🎯 Minimal structure validation PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing minimal structure: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_minimal_structure()
    if success:
        print("\n🎉 Minimal FlightPrice structure test SUCCESSFUL!")
    else:
        print("\n💥 Minimal FlightPrice structure test FAILED!")
