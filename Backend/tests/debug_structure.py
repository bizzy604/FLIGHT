import json
import os

# Load the real API response directly
def load_real_api_response():
    """Load the real API response from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'tests', 'airshoping_response.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

SAMPLE_VERTEIL_RESPONSE = load_real_api_response()

# Debug the structure
print("=== TOP LEVEL KEYS ===")
print(list(SAMPLE_VERTEIL_RESPONSE.keys()))

print("\n=== OFFERS GROUP STRUCTURE ===")
offers_group = SAMPLE_VERTEIL_RESPONSE.get('OffersGroup', {})
print(f"OffersGroup keys: {list(offers_group.keys())}")

airline_offers = offers_group.get('AirlineOffers', [])
print(f"Number of AirlineOffers: {len(airline_offers)}")

if airline_offers:
    first_airline_offer_group = airline_offers[0]
    print(f"First AirlineOffer group keys: {list(first_airline_offer_group.keys())}")
    
    airline_offer_list = first_airline_offer_group.get('AirlineOffer', [])
    print(f"Number of AirlineOffer items: {len(airline_offer_list)}")
    
    if airline_offer_list:
        first_offer = airline_offer_list[0]
        print(f"First offer keys: {list(first_offer.keys())}")
        
        # Check for OfferID
        offer_id = first_offer.get('OfferID')
        print(f"OfferID structure: {offer_id}")
        
        # Check for OfferPrice
        offer_prices = first_offer.get('OfferPrice', [])
        print(f"Number of OfferPrice items: {len(offer_prices)}")
        
        # Check for PricedOffer instead
        priced_offer = first_offer.get('PricedOffer', {})
        print(f"PricedOffer structure: {type(priced_offer)}")
        if isinstance(priced_offer, dict):
            print(f"PricedOffer keys: {list(priced_offer.keys())}")
            
            # Check for OfferPrice within PricedOffer
            inner_offer_prices = priced_offer.get('OfferPrice', [])
            print(f"OfferPrice within PricedOffer: {len(inner_offer_prices)}")
            
            if inner_offer_prices:
                first_inner_price = inner_offer_prices[0]
                print(f"First inner OfferPrice keys: {list(first_inner_price.keys())}")
                
                # Check for Associations
                associations = first_inner_price.get('Associations', [])
                print(f"Associations in inner OfferPrice: {len(associations) if isinstance(associations, list) else 'Not a list'}")
                
                if associations:
                    print(f"First association keys: {list(associations[0].keys()) if associations else 'None'}")

print("\n=== DATA LISTS STRUCTURE ===")
data_lists = SAMPLE_VERTEIL_RESPONSE.get('DataLists', {})
print(f"DataLists keys: {list(data_lists.keys())}")

if 'FlightSegmentList' in data_lists:
    segments = data_lists['FlightSegmentList'].get('FlightSegment', [])
    print(f"Number of flight segments: {len(segments)}")
    if segments:
        print(f"First segment keys: {list(segments[0].keys())}")