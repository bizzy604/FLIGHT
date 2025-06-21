#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend, _extract_reference_data
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE
import json

# Transform the sample response
result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)

print("Transformation result:")
print(f"Number of flight offers: {len(result)}")

if result:
    flight_offer = result[0]
    print(f"\nFirst flight offer:")
    print(f"  Departure: {flight_offer.get('departure')}")
    print(f"  Arrival: {flight_offer.get('arrival')}")
    print(f"  Segments: {len(flight_offer.get('segments', []))}")
    
    # Print all segments
    segments = flight_offer.get('segments', [])
    for i, segment in enumerate(segments):
        print(f"\n  Segment {i+1}:")
        print(f"    Departure: {segment.get('departure', {})}")
        print(f"    Arrival: {segment.get('arrival', {})}")
        print(f"    Flight Number: {segment.get('flightNumber')}")

# Let's also manually check what the first priced offer references
print("\n" + "="*60)
print("MANUAL PRICED OFFER ANALYSIS")
print("="*60)

reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
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
        
        print(f"\nFound {len(associations)} associations")
        
        all_segment_refs = []
        for i, assoc in enumerate(associations):
            if isinstance(assoc, dict):
                applicable_flight = assoc.get('ApplicableFlight', {})
                segment_refs = applicable_flight.get('SegmentReferences', [])
                if not isinstance(segment_refs, list):
                    segment_refs = [segment_refs]
                
                print(f"\nAssociation {i+1}:")
                print(f"  ApplicableFlight: {applicable_flight}")
                print(f"  Segment references: {len(segment_refs)}")
                
                for j, seg_ref in enumerate(segment_refs):
                    ref_key = seg_ref.get('ref')
                    if ref_key:
                        all_segment_refs.append(ref_key)
                        segment_data = reference_data['segments'].get(ref_key, {})
                        departure = segment_data.get('Departure', {})
                        arrival = segment_data.get('Arrival', {})
                        
                        dep_airport_obj = departure.get('AirportCode', {})
                        arr_airport_obj = arrival.get('AirportCode', {})
                        
                        dep_airport = dep_airport_obj.get('value', '') if isinstance(dep_airport_obj, dict) else dep_airport_obj
                        arr_airport = arr_airport_obj.get('value', '') if isinstance(arr_airport_obj, dict) else arr_airport_obj
                        
                        print(f"    Segment {j+1}: {ref_key} -> {dep_airport} to {arr_airport}")
        
        print(f"\nAll segment references for this offer: {all_segment_refs}")
        
        # Show what the first and last segments would be
        if all_segment_refs:
            first_ref = all_segment_refs[0]
            last_ref = all_segment_refs[-1]
            
            first_segment_data = reference_data['segments'].get(first_ref, {})
            last_segment_data = reference_data['segments'].get(last_ref, {})
            
            print(f"\nFirst segment ({first_ref}):")
            first_dep = first_segment_data.get('Departure', {})
            first_dep_airport_obj = first_dep.get('AirportCode', {})
            first_dep_airport = first_dep_airport_obj.get('value', '') if isinstance(first_dep_airport_obj, dict) else first_dep_airport_obj
            print(f"  Departure: {first_dep_airport}")
            
            print(f"\nLast segment ({last_ref}):")
            last_arr = last_segment_data.get('Arrival', {})
            last_arr_airport_obj = last_arr.get('AirportCode', {})
            last_arr_airport = last_arr_airport_obj.get('value', '') if isinstance(last_arr_airport_obj, dict) else last_arr_airport_obj
            print(f"  Arrival: {last_arr_airport}")