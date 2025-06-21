#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import _extract_reference_data
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

# Extract reference data
reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)

print("Reference data segments:")
print(f"Number of segments: {len(reference_data.get('segments', {}))}")

for i, (segment_key, segment_data) in enumerate(reference_data.get('segments', {}).items()):
    print(f"\nSegment {i+1} (Key: {segment_key}):")
    print(f"  Departure: {segment_data.get('departure', {})}")
    print(f"  Arrival: {segment_data.get('arrival', {})}")
    if i >= 4:  # Limit output to first 5 segments
        print(f"... and {len(reference_data.get('segments', {})) - 5} more segments")
        break

# Now let's see what segments are used in the flight offer transformation
print("\n" + "="*50)
print("FLIGHT OFFER TRANSFORMATION DEBUG")
print("="*50)

# Get the first priced offer to see what segments it references
data_lists = SAMPLE_VERTEIL_RESPONSE.get('DataLists', {})
priced_offers = data_lists.get('PricedOfferList', [])

if priced_offers:
    priced_offer = priced_offers[0]
    print(f"\nFirst priced offer keys: {list(priced_offer.keys())}")
    
    # Look for associations to see which segments are referenced
    offer_prices = priced_offer.get('OfferPrice', [])
    if offer_prices:
        offer_price = offer_prices[0]
        associations = offer_price.get('Associations', [])
        if not associations:
            associations = priced_offer.get('Associations', [])
        
        print(f"\nAssociations found: {len(associations)}")
        for i, assoc in enumerate(associations):
            print(f"Association {i+1}: {assoc}")
            if i >= 2:  # Limit output
                break