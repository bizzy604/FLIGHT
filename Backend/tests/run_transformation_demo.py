#!/usr/bin/env python3
"""
Demo script to run data transformation on the airshoping response
and output the results to see how the transformed response looks for the frontend.
"""

import json
import sys
import os
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from utils.data_transformer import transform_verteil_to_frontend

def main():
    # Load the airshoping response
    response_file = backend_dir / "tests" / "airshoping_response.json"
    
    if not response_file.exists():
        print(f"Error: Response file not found at {response_file}")
        return
    
    print("Loading airshoping response...")
    with open(response_file, 'r', encoding='utf-8') as f:
        raw_response = json.load(f)
    
    print(f"Raw response loaded. Size: {len(json.dumps(raw_response))} characters")
    
    # Transform without round trip enhancement (default behavior)
    print("\n=== Transforming with enableRoundtrip=False (default) ===")
    try:
        transformed_default = transform_verteil_to_frontend(raw_response, enable_roundtrip=False)
        print(f"Default transformation completed. Found {len(transformed_default)} offers")
        
        # Save default transformation result
        output_file_default = backend_dir / "transformation_result_default.json"
        with open(output_file_default, 'w', encoding='utf-8') as f:
            json.dump(transformed_default, f, indent=2, ensure_ascii=False)
        print(f"Default transformation saved to: {output_file_default}")
        
    except Exception as e:
        print(f"Error in default transformation: {e}")
        import traceback
        traceback.print_exc()
    
    # Transform with round trip enhancement
    print("\n=== Transforming with enableRoundtrip=True (enhanced) ===")
    try:
        transformed_enhanced = transform_verteil_to_frontend(raw_response, enable_roundtrip=True)
        print(f"Enhanced transformation completed. Found {len(transformed_enhanced)} offers")
        
        # Save enhanced transformation result
        output_file_enhanced = backend_dir / "transformation_result_enhanced.json"
        with open(output_file_enhanced, 'w', encoding='utf-8') as f:
            json.dump(transformed_enhanced, f, indent=2, ensure_ascii=False)
        print(f"Enhanced transformation saved to: {output_file_enhanced}")
        
    except Exception as e:
        print(f"Error in enhanced transformation: {e}")
        import traceback
        traceback.print_exc()
    
    # Compare results
    try:
        if 'transformed_default' in locals() and 'transformed_enhanced' in locals():
            print("\n=== Comparison Summary ===")
            print(f"Default transformation: {len(transformed_default)} offers")
            print(f"Enhanced transformation: {len(transformed_enhanced)} offers")
            print(f"Difference: +{len(transformed_enhanced) - len(transformed_default)} offers with round trip enhancement")
            
            # Show sample structure
            if transformed_enhanced:
                print("\n=== Sample Enhanced Offer Structure ===")
                sample_offer = transformed_enhanced[0]
                print(f"Sample offer keys: {list(sample_offer.keys())}")
                if 'segments' in sample_offer:
                    print(f"Sample segments count: {len(sample_offer['segments'])}")
                if 'isRoundTrip' in sample_offer:
                    print(f"Sample isRoundTrip: {sample_offer['isRoundTrip']}")
                if 'tripType' in sample_offer:
                    print(f"Sample tripType: {sample_offer['tripType']}")
    except Exception as e:
        print(f"Error in comparison: {e}")
    
    print("\n=== Transformation Demo Complete ===")
    print("Check the generated JSON files to see the complete transformed responses.")

if __name__ == "__main__":
    main()