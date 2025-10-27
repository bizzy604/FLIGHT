import json

# Load the price response
with open('tests/integration/live_test_data/route_2_ancillary_price.json', 'r') as f:
    data = json.load(f)

raw = data.get('raw_response', {})
print("=" * 80)
print("Checking FlightPrice raw_response structure")
print("=" * 80)

# Check PricedFlightOffers
priced_flight_offers = raw.get('PricedFlightOffers')
print(f"\n1. PricedFlightOffers exists: {priced_flight_offers is not None}")
print(f"   Type: {type(priced_flight_offers)}")

if priced_flight_offers:
    priced_offer = priced_flight_offers.get('PricedFlightOffer')
    print(f"\n2. PricedFlightOffer exists: {priced_offer is not None}")
    print(f"   Type: {type(priced_offer)}")
    print(f"   Is list: {isinstance(priced_offer, list)}")
    
    if isinstance(priced_offer, list):
        print(f"   Length: {len(priced_offer)}")
        print(f"   Empty: {len(priced_offer) == 0}")
        
        if priced_offer:
            print(f"\n3. First offer keys: {list(priced_offer[0].keys())}")
            offer_id = priced_offer[0].get('OfferID', {})
            print(f"   OfferID.Owner: {offer_id.get('Owner')}")
    else:
        print(f"   Value: {priced_offer}")
