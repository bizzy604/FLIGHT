#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer_roundtrip import transform_verteil_to_frontend_with_roundtrip
from utils.data_transformer import transform_verteil_to_frontend
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

# Compare the two approaches
original = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)
enhanced = transform_verteil_to_frontend_with_roundtrip(SAMPLE_VERTEIL_RESPONSE)

print(f"Original transformation: {len(original)} offers")
print(f"Enhanced transformation: {len(enhanced)} offers")

if original:
    print(f"\nOriginal first offer: {original[0]['departure']['airport']} -> {original[0]['arrival']['airport']}")

if enhanced:
    print(f"\nEnhanced offers:")
    for i, offer in enumerate(enhanced[:4]):  # Show first 4
        print(f"  {i+1}: {offer['departure']['airport']} -> {offer['arrival']['airport']} ({offer.get('direction', 'unknown')})")
    print(f"  ... and {len(enhanced)-4} more")