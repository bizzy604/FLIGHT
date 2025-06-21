import json
import os
from utils.data_transformer import _transform_single_offer, _extract_reference_data

# Load the real API response directly
def load_real_api_response():
    """Load the real API response from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'tests', 'airshoping_response.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

SAMPLE_VERTEIL_RESPONSE = load_real_api_response()

# Extract the data like the test does
airline_offer = SAMPLE_VERTEIL_RESPONSE['OffersGroup']['AirlineOffers'][0]['AirlineOffer'][0]
priced_offer = airline_offer['PricedOffer'].copy()
priced_offer['OfferID'] = airline_offer['OfferID']

# Extract reference data
reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)

# Extract airline code
airline_code = 'QR'  # From the debug output we saw Owner: 'QR'

print("=== DEBUGGING TRANSFORM FUNCTION ===")
print(f"PricedOffer keys: {list(priced_offer.keys())}")
print(f"Reference data keys: {list(reference_data.keys())}")
print(f"Airline code: {airline_code}")

# Check OfferPrice structure
offer_prices = priced_offer.get('OfferPrice', [])
print(f"Number of OfferPrice items: {len(offer_prices)}")
if offer_prices:
    print(f"First OfferPrice keys: {list(offer_prices[0].keys())}")
    
    # Check for Associations
    associations = offer_prices[0].get('Associations', [])
    print(f"Associations: {associations}")

# Try to transform
result = _transform_single_offer(
    priced_offer=priced_offer,
    airline_code=airline_code,
    reference_data=reference_data,
    airline_offer=airline_offer
)

print(f"\nTransform result: {result}")
if result:
    print(f"Result keys: {list(result.keys())}")
else:
    print("Transform returned None - check logs above for errors")