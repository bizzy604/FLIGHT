#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Backend.utils.data_transformer import transform_verteil_to_frontend, _extract_reference_data
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

# Extract reference data first
reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)

print("Available segments in reference data:")
for i, (segment_key, segment_data) in enumerate(reference_data.get('segments', {}).items()):
    departure = segment_data.get('Departure', {})
    arrival = segment_data.get('Arrival', {})
    
    dep_airport_obj = departure.get('AirportCode', {})
    arr_airport_obj = arrival.get('AirportCode', {})
    
    dep_airport = dep_airport_obj.get('value', '') if isinstance(dep_airport_obj, dict) else dep_airport_obj
    arr_airport = arr_airport_obj.get('value', '') if isinstance(arr_airport_obj, dict) else arr_airport_obj
    
    print(f"  {segment_key}: {dep_airport} -> {arr_airport}")
    if i >= 10:  # Limit output
        print(f"  ... and {len(reference_data.get('segments', {})) - 11} more segments")
        break

print("\n" + "="*50)
print("CHECKING PRICED OFFER ASSOCIATIONS")
print("="*50)

# Get the first priced offer to see what segments it references
data_lists = SAMPLE_VERTEIL_RESPONSE.get('DataLists', {})
priced_offers = data_lists.get('PricedOfferList', [])

if priced_offers:
    priced_offer = priced_offers[0]
    print(f"\nFirst priced offer ID: {priced_offer.get('OfferID')}")
    
    # Look for associations to see which segments are referenced
    offer_prices = priced_offer.get('OfferPrice', [])
    if offer_prices:
        offer_price = offer_prices[0]
        associations = offer_price.get('Associations', [])
        if not associations:
            associations = priced_offer.get('Associations', [])
        
        print(f"\nAssociations found: {len(associations)}")
        for i, assoc in enumerate(associations):
            if isinstance(assoc, dict):
                segment_refs = assoc.get('ApplicableFlight', {}).get('SegmentReferences', [])
                if not isinstance(segment_refs, list):
                    segment_refs = [segment_refs]
                
                print(f"\nAssociation {i+1} segment references:")
                for seg_ref in segment_refs:
                    ref_key = seg_ref.get('ref')
                    if ref_key:
                        segment_data = reference_data['segments'].get(ref_key, {})
                        departure = segment_data.get('Departure', {})
                        arrival = segment_data.get('Arrival', {})
                        
                        dep_airport_obj = departure.get('AirportCode', {})
                        arr_airport_obj = arrival.get('AirportCode', {})
                        
                        dep_airport = dep_airport_obj.get('value', '') if isinstance(dep_airport_obj, dict) else dep_airport_obj
                        arr_airport = arr_airport_obj.get('value', '') if isinstance(arr_airport_obj, dict) else arr_airport_obj
                        
                        print(f"    {ref_key}: {dep_airport} -> {arr_airport}")