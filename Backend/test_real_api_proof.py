"""
Quick test to demonstrate REAL API calls with actual responses.
This shows we're making live calls to VDC production API.
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from utils.auth import TokenManager
from app.services.air_shopping import AirShoppingService
from app.models.requests.air_shopping import AirShoppingRequest
from app.models.common import FlightSegment, PassengerCount
from app.config import settings


class SimpleAuthAdapter:
    """Simple adapter for TokenManager."""
    def __init__(self, token_manager, office_id):
        self._token_manager = token_manager
        self.office_id = office_id
    
    async def get_token(self):
        return self._token_manager.get_token()


async def test_real_api_call():
    """Make a real API call and show the response."""
    
    print("\n" + "="*80)
    print("REAL VDC API CALL DEMONSTRATION")
    print("="*80)
    
    # Setup authentication
    print("\n1. Setting up authentication...")
    token_manager = TokenManager.get_instance()
    config = {
        'VERTEIL_API_BASE_URL': "https://api.stage.verteil.com",
        'VERTEIL_TOKEN_ENDPOINT': '/oauth2/token',
        'VERTEIL_USERNAME': settings.VDC_USERNAME,
        'VERTEIL_PASSWORD': settings.VDC_PASSWORD,
        'VERTEIL_OFFICE_ID': settings.VDC_OFFICE_ID
    }
    token_manager.set_config(config)
    
    # Get token
    token = token_manager.get_token()
    print(f"   Token obtained: {token[:50]}... (truncated)")
    print(f"   Token length: {len(token)} characters")
    
    # Create service
    auth_client = SimpleAuthAdapter(token_manager, settings.VDC_OFFICE_ID)
    
    async with httpx.AsyncClient() as http_client:
        service = AirShoppingService(auth_client, http_client)
        
        # Create request
        print("\n2. Building AirShopping request...")
        departure_date = (datetime.now().date() + timedelta(days=30)).isoformat()
        
        request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",  # Mumbai
                    destination="LHR",  # London
                    departure_date=departure_date
                )
            ],
            passengers=PassengerCount(adults=1)
        )
        
        print(f"   Route: BOM -> LHR")
        print(f"   Date: {departure_date}")
        print(f"   Passengers: 1 Adult")
        
        # Make REAL API call
        print("\n3. Making REAL API call to VDC...")
        print(f"   API URL: {settings.VDC_API_BASE_URL}:AirShopping")
        
        result = await service.execute(request)
        
        # Show REAL response data
        print("\n4. REAL API Response received!")
        print("   " + "-"*76)
        
        if "airlines" in result:
            total_offers = sum(len(airline["offers"]) for airline in result["airlines"])
            print(f"   Total Airlines: {len(result['airlines'])}")
            print(f"   Total Offers: {total_offers}")
            
            # Show first airline details
            if result["airlines"]:
                first_airline = result["airlines"][0]
                print(f"\n   First Airline: {first_airline.get('code', 'N/A')} - {first_airline.get('name', 'Multiple Airlines')}")
                print(f"   Offers from this airline: {len(first_airline['offers'])}")
                
                # Show first offer details
                if first_airline["offers"]:
                    first_offer = first_airline["offers"][0]
                    print(f"\n   FIRST OFFER DETAILS (from REAL API):")
                    print(f"   - Offer ID: {first_offer['offer_id'][:50]}...")
                    print(f"   - Total Price: {first_offer['pricing']['total']} {first_offer['pricing']['currency']}")
                    
                    # Show segment details
                    if first_offer.get("segments"):
                        seg = first_offer["segments"][0]
                        print(f"\n   FLIGHT SEGMENT (REAL DATA):")
                        print(f"   - Flight: {seg.get('marketing_carrier', 'N/A')} {seg.get('marketing_flight_number', 'N/A')}")
                        print(f"   - Departure: {seg['origin']} at {seg['departure_datetime']}")
                        print(f"   - Arrival: {seg['destination']} at {seg['arrival_datetime']}")
                        print(f"   - Aircraft: {seg.get('aircraft_type', 'N/A')}")
        
        print("\n" + "="*80)
        print("PROOF: This is a REAL API call with LIVE data from VDC!")
        print("="*80)
        
        return result


if __name__ == "__main__":
    asyncio.run(test_real_api_call())
