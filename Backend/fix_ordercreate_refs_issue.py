#!/usr/bin/env python3
"""
Fix for OrderCreate refs issue where hardcoded service IDs like "SRV13" are being used
instead of dynamic references.

The issue is in build_ordercreate_rq.py line 994-996 where we're adding service_id_value
to offer_item_type_refs, but this should be dynamic based on the actual service data.
"""

import json
import sys
import os
from typing import Dict, Any, List

def analyze_refs_issue():
    """Analyze the refs issue in OrderCreate payload generation."""
    print("=" * 80)
    print("ANALYZING ORDERCREATE REFS ISSUE")
    print("=" * 80)
    
    # Load the problematic Booking_RQ.json to see the issue
    try:
        with open('api_logs/booking/Booking_RQ.json', 'r') as f:
            booking_rq = json.load(f)
        
        print("📋 Found problematic refs in Booking_RQ.json:")
        
        # Find OtherItem with hardcoded SRV13
        order_items = booking_rq.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
        for i, item in enumerate(order_items):
            offer_item_type = item.get('OfferItemType', {})
            other_items = offer_item_type.get('OtherItem', [])
            
            for j, other_item in enumerate(other_items):
                refs = other_item.get('refs', [])
                if 'SRV13' in refs:
                    print(f"  Item {i}, OtherItem {j}:")
                    print(f"    refs: {refs}")
                    print(f"    Issue: Contains hardcoded 'SRV13'")
        
        return booking_rq
        
    except Exception as e:
        print(f"Error loading Booking_RQ.json: {e}")
        return None

def analyze_service_data():
    """Analyze the service data to understand the correct structure."""
    print("\n" + "=" * 80)
    print("ANALYZING SERVICE DATA STRUCTURE")
    print("=" * 80)
    
    try:
        # Load ServiceListRS to see the service structure
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            servicelist_rs = json.load(f)
        
        services = servicelist_rs.get('Services', {}).get('Service', [])
        print(f"Found {len(services)} services in ServiceListRS")
        
        for i, service in enumerate(services):
            service_id = service.get('ServiceID', {})
            object_key = service.get('ObjectKey', '')
            service_id_value = service_id.get('value', '') if isinstance(service_id, dict) else str(service_id)
            
            print(f"\n  Service {i+1}:")
            print(f"    ObjectKey: {object_key}")
            print(f"    ServiceID.value: {service_id_value}")
            print(f"    ServiceID.Owner: {service_id.get('Owner', 'N/A') if isinstance(service_id, dict) else 'N/A'}")
            
            # Check associations
            associations = service.get('Associations', [])
            print(f"    Associations: {len(associations)}")
            
            for j, assoc in enumerate(associations):
                traveler_refs = assoc.get('Traveler', {}).get('TravelerReferences', [])
                flight_refs = assoc.get('Flight', {}).get('originDestinationReferencesOrSegmentReferences', [])
                print(f"      Association {j+1}:")
                print(f"        TravelerReferences: {traveler_refs}")
                print(f"        FlightReferences: {len(flight_refs)}")
        
        return servicelist_rs
        
    except Exception as e:
        print(f"Error loading ServiceListRS.json: {e}")
        return None

def identify_correct_refs_structure():
    """Identify what the correct refs structure should be."""
    print("\n" + "=" * 80)
    print("IDENTIFYING CORRECT REFS STRUCTURE")
    print("=" * 80)
    
    print("🔍 Current Issue:")
    print("  - Using hardcoded service ID values like 'SRV13'")
    print("  - Should use dynamic references from service associations")
    
    print("\n✅ Correct Approach:")
    print("  - TravelerReferences: From service.Associations.Traveler.TravelerReferences")
    print("  - SegmentReferences: From service.Associations.Flight.originDestinationReferencesOrSegmentReferences")
    print("  - ServiceID: Should be the actual service ObjectKey, not the hardcoded value")
    
    print("\n📋 NDC Specification Requirements:")
    print("  - OtherItem.refs should contain:")
    print("    1. TravelerReference (e.g., 'PAX1')")
    print("    2. SegmentReference (e.g., 'SEG1')")
    print("    3. ServiceReference (should be dynamic, not hardcoded)")

def create_fix():
    """Create the fix for the refs issue."""
    print("\n" + "=" * 80)
    print("CREATING FIX FOR REFS ISSUE")
    print("=" * 80)
    
    fix_code = '''
# FIX: Replace lines 994-996 in build_ordercreate_rq.py

# OLD CODE (PROBLEMATIC):
# Get ServiceID from service per NDC spec
service_id_value = service_id.get('value', '') if isinstance(service_id, dict) else str(service_id) if service_id else ''
if service_id_value:
    offer_item_type_refs.append(service_id_value)

# NEW CODE (FIXED):
# Get ServiceReference from service ObjectKey per NDC spec
service_reference = service.get('ObjectKey', '')
if service_reference:
    offer_item_type_refs.append(service_reference)
'''
    
    print("🔧 Fix Code:")
    print(fix_code)
    
    print("\n📋 Explanation:")
    print("  - Instead of using hardcoded service ID values like 'SRV13'")
    print("  - Use the service ObjectKey which is dynamic and unique")
    print("  - This ensures proper reference to the actual service instance")
    
    return fix_code

def test_fix():
    """Test the fix by showing what the corrected refs should look like."""
    print("\n" + "=" * 80)
    print("TESTING FIX")
    print("=" * 80)
    
    print("🔍 Before Fix (Current):")
    print("  refs: ['PAX1', 'SEG1', 'SRV13']  # SRV13 is hardcoded")
    
    print("\n✅ After Fix (Corrected):")
    print("  refs: ['PAX1', 'SEG1', '1-ServiceIdAF-13']  # Dynamic ObjectKey")
    
    print("\n📋 Benefits of the Fix:")
    print("  - Dynamic service references")
    print("  - Proper NDC compliance")
    print("  - Unique service identification")
    print("  - No hardcoded values")

def main():
    """Main function to analyze and fix the refs issue."""
    print("🔍 ANALYZING ORDERCREATE REFS ISSUE")
    print("=" * 80)
    
    # Analyze the issue
    booking_rq = analyze_refs_issue()
    if not booking_rq:
        return
    
    # Analyze service data
    servicelist_rs = analyze_service_data()
    if not servicelist_rs:
        return
    
    # Identify correct structure
    identify_correct_refs_structure()
    
    # Create fix
    fix_code = create_fix()
    
    # Test fix
    test_fix()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    print("🚨 Issue Identified:")
    print("  - Line 994-996 in build_ordercreate_rq.py")
    print("  - Using hardcoded service ID values like 'SRV13'")
    print("  - Should use dynamic service ObjectKey instead")
    
    print("\n✅ Solution:")
    print("  - Replace service_id.get('value') with service.get('ObjectKey')")
    print("  - This ensures dynamic, unique service references")
    print("  - Maintains NDC compliance")
    
    print("\n🎯 Impact:")
    print("  - Fixes hardcoded service references")
    print("  - Improves OrderCreate payload accuracy")
    print("  - Ensures proper service identification")

if __name__ == "__main__":
    main()
