#!/usr/bin/env python3
"""
Test script to make an actual API call with the fixed FlightPrice request.
"""

import json
import requests
import logging
from scripts.build_flightprice_rq import build_flight_price_request

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_call():
    """Test the fixed FlightPrice request with actual API call."""
    
    # Load test air shopping response
    try:
        with open('tests/airshopingRS.json', 'r') as f:
            air_shopping_response = json.load(f)
    except FileNotFoundError:
        logger.error("Test air shopping response file not found")
        return False
    
    # Test with KQ airline (index 0 - should be KQ based on the test data)
    try:
        logger.info("Building minimal FlightPrice request for KQ airline...")

        # Build flight price request for KQ (index 0)
        flight_price_request = build_flight_price_request(
            airshopping_response=air_shopping_response,
            selected_offer_index=0  # KQ airline
        )
        
        # Prepare API call
        url = "https://api.stage.verteil.com/entrygate/rest/request:flightPrice"
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "OfficeId": "OFF3746",
            "service": "FlightPrice",
            "User-Agent": "PostmanRuntime/7.41",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "ThirdpartyId": "KQ"
        }
        
        # Save the request
        request_data = {
            "timestamp": "2025-07-05T21:25:00.000000",
            "description": "Minimal FlightPrice API Request - KQ Test",
            "data": {
                "url": url,
                "method": "POST",
                "headers": headers,
                "payload": flight_price_request
            }
        }

        with open('Output/FlightPrice_REQUEST_MINIMAL_API_TEST.json', 'w') as f:
            json.dump(request_data, f, indent=2)

        logger.info("✅ Minimal FlightPrice request saved to: Output/FlightPrice_REQUEST_MINIMAL_API_TEST.json")
        
        # Make the API call
        logger.info("🚀 Making API call to Verteil...")
        response = requests.post(url, headers=headers, json=flight_price_request, timeout=30)
        
        # Save the response
        response_data = {
            "timestamp": "2025-07-05T21:25:00.000000",
            "description": "Minimal FlightPrice API Response - KQ Test",
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }

        with open('Output/FlightPrice_RESPONSE_MINIMAL_API_TEST.json', 'w') as f:
            json.dump(response_data, f, indent=2)

        logger.info(f"✅ Minimal FlightPrice response saved to: Output/FlightPrice_RESPONSE_MINIMAL_API_TEST.json")
        logger.info(f"📊 API Response Status: {response.status_code}")
        
        # Check if the response is successful
        if response.status_code == 200:
            response_json = response.json()
            if "Errors" in response_json:
                errors = response_json["Errors"]
                logger.error(f"❌ API returned errors: {errors}")
                return False
            else:
                logger.info("🎉 API call successful - no errors!")
                return True
        else:
            logger.error(f"❌ API call failed with status code: {response.status_code}")
            return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error during API call: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing API call: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api_call()
    if success:
        print("\n🎉 Minimal FlightPrice API call test SUCCESSFUL!")
    else:
        print("\n💥 Minimal FlightPrice API call test FAILED!")
