"""Debug FlightPrice API call."""

import asyncio
import json
from app.core.auth import VDCAuthClient
from app.services.flight_price import FlightPriceService
from app.core.http_client import get_http_client

async def main():
    """Test FlightPrice with saved AirShopping response."""
    
    # Load saved search response
    with open("tests/integration/live_test_data/route_1_flight_only_search.json") as f:
        search_data = json.load(f)
    
    raw_response = search_data["raw_response"]
    airline_code = search_data["airlines"][0]["code"]
    
    print(f"Testing FlightPrice for airline: {airline_code}, offer index: 0")
    
    # Create auth client and service
    auth_client = VDCAuthClient()
    http_client = get_http_client()
    service = FlightPriceService(auth_client=auth_client, http_client=http_client)
    
    try:
        # Make FlightPrice call
        result = await service.execute(
            offer_index=0,
            airline_owner=airline_code,
            air_shopping_response=raw_response
        )
        
        print("\n✅ FlightPrice Success!")
        print(json.dumps(result, indent=2))
        
        # Save result
        with open("debug_flight_price_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"\n❌ FlightPrice Failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await http_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
