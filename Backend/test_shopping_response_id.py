#!/usr/bin/env python3
"""
Test script to debug ShoppingResponseID extraction.
"""

import json
import sys
import os

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_test_data():
    """Load the multi-airline air shopping response test data."""
    try:
        with open("../postman/airshopingresponse.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: Test data file not found")
        return None

def test_reference_extractor_import():
    """Test if we can import the reference extractor."""
    print("=== TESTING REFERENCE EXTRACTOR IMPORT ===")
    
    try:
        from utils.reference_extractor import EnhancedReferenceExtractor
        print("✅ EnhancedReferenceExtractor imported successfully")
        return EnhancedReferenceExtractor
    except ImportError as e:
        print(f"❌ Failed to import EnhancedReferenceExtractor: {e}")
        return None

def test_shopping_response_id_extraction(airshopping_response):
    """Test ShoppingResponseID extraction."""
    print("\n=== TESTING SHOPPING RESPONSE ID EXTRACTION ===")
    
    # Try to import and use the reference extractor
    try:
        from utils.reference_extractor import EnhancedReferenceExtractor
        
        extractor = EnhancedReferenceExtractor(airshopping_response)
        refs = extractor.extract_references()
        shopping_ids = refs.get('shopping_response_ids', {})
        
        print(f"Extracted shopping response IDs: {shopping_ids}")
        
        # Test specific airlines
        test_airlines = ["KL", "LHG", "QR", "EK", "AF", "KQ", "ET"]
        for airline in test_airlines:
            airline_id = shopping_ids.get(airline, "NOT_FOUND")
            print(f"  {airline}: {airline_id}")
            
        return shopping_ids
        
    except ImportError as e:
        print(f"❌ Cannot import EnhancedReferenceExtractor: {e}")
        return None
    except Exception as e:
        print(f"❌ Error extracting shopping response IDs: {e}")
        return None

def check_metadata_structure(airshopping_response):
    """Check the Metadata structure for shopping response IDs."""
    print("\n=== CHECKING METADATA STRUCTURE ===")
    
    metadata = airshopping_response.get("Metadata", {})
    print(f"Metadata keys: {list(metadata.keys())}")
    
    # Look for shopping response IDs in different places
    other_metadata = metadata.get("Other", {})
    if other_metadata:
        print(f"Other metadata keys: {list(other_metadata.keys())}")
        
        # Check for AugPoint structure
        other_metadata_list = other_metadata.get("OtherMetadata", [])
        for i, item in enumerate(other_metadata_list):
            if "AugPoint" in item:
                aug_points = item["AugPoint"]["AugPoint"]
                print(f"  OtherMetadata[{i}] has {len(aug_points)} AugPoints")
                for j, aug_point in enumerate(aug_points[:3]):  # Show first 3
                    key = aug_point.get("Key", "")
                    owner = aug_point.get("Owner", "")
                    print(f"    AugPoint[{j}]: Key={key}, Owner={owner}")

def manual_shopping_response_id_extraction(airshopping_response):
    """Manually extract shopping response IDs from the structure."""
    print("\n=== MANUAL SHOPPING RESPONSE ID EXTRACTION ===")
    
    # Look in Metadata.Other.OtherMetadata for AugPoint structure
    try:
        metadata = airshopping_response.get("Metadata", {})
        other_metadata = metadata.get("Other", {}).get("OtherMetadata", [])
        
        shopping_ids = {}
        
        for item in other_metadata:
            if "AugPoint" in item:
                aug_points = item["AugPoint"]["AugPoint"]
                for aug_point in aug_points:
                    key = aug_point.get("Key", "")
                    owner = aug_point.get("Owner", "")
                    
                    if key and owner:
                        shopping_ids[owner] = key
        
        print(f"Manually extracted shopping IDs: {shopping_ids}")
        return shopping_ids
        
    except Exception as e:
        print(f"❌ Error in manual extraction: {e}")
        return {}

def main():
    """Main test function."""
    print("Testing ShoppingResponseID Extraction")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Test reference extractor import
    extractor_class = test_reference_extractor_import()
    
    # Test shopping response ID extraction
    shopping_ids = test_shopping_response_id_extraction(airshopping_response)
    
    # Check metadata structure
    check_metadata_structure(airshopping_response)
    
    # Manual extraction
    manual_ids = manual_shopping_response_id_extraction(airshopping_response)

if __name__ == "__main__":
    main()
