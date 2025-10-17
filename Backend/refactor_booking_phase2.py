"""
Phase 2: Refactor _build_fallback_payload ID extraction
"""

import re

def refactor_fallback_payload():
    file_path = r"c:\Users\User\Desktop\REA FLIGHT PORTAL\Backend\services\flight\booking.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = len(content.split('\n'))
    print(f"Original file: {original_lines} lines")
    
    # Find the _build_fallback_payload method and refactor ID extraction
    # This is complex, so we'll do targeted replacements
    
    # 1. Replace ShoppingResponseID extraction (the massive if-elif chain)
    old_shopping_pattern = r"# Only try to extract IDs from response if we don't already have them\s+if not extracted_shopping_response_id:.*?logger\.info\(f\"\[DEBUG\] Found ShoppingResponseID in FlightPriceRS structure: {extracted_shopping_response_id}\"\)"
    
    new_shopping_code = """# Use navigator utility for ShoppingResponseID extraction
        if not extracted_shopping_response_id:
            extracted_shopping_response_id = self.navigator.extract_id(
                flight_price_response,
                'ShoppingResponseID',
                request_id
            )"""
    
    matches = list(re.finditer(old_shopping_pattern, content, flags=re.DOTALL))
    if matches:
        content = re.sub(old_shopping_pattern, new_shopping_code, content, flags=re.DOTALL)
        print(f"✓ Replaced ShoppingResponseID extraction in _build_fallback_payload ({len(matches)} match)")
    else:
        print("⚠ Could not find ShoppingResponseID extraction pattern in _build_fallback_payload")
    
    # 2. Replace OfferID extraction (another massive if-elif chain)
    old_offer_pattern = r"# Extract OfferID if not provided - check multiple possible paths\s+if not extracted_offer_id:.*?logger\.info\(f\"\[DEBUG\] Found OfferID in PricedFlightOffers structure: {extracted_offer_id}\"\)"
    
    new_offer_code = """# Use navigator utility for OfferID extraction
        if not extracted_offer_id:
            extracted_offer_id = self.navigator.extract_offer_id_from_priced_offers(
                flight_price_response,
                request_id
            )"""
    
    matches = list(re.finditer(old_offer_pattern, content, flags=re.DOTALL))
    if matches:
        content = re.sub(old_offer_pattern, new_offer_code, content, flags=re.DOTALL)
        print(f"✓ Replaced OfferID extraction in _build_fallback_payload ({len(matches)} match)")
    else:
        print("⚠ Could not find OfferID extraction pattern in _build_fallback_payload")
    
    # 3. Replace OfferItemIDs extraction (huge block with extract_offer_item_ids_from_structure function)
    old_offer_items_pattern = r"# Extract OfferItemIDs from the raw flight price response using multiple methods\s+offer_item_ids = \[\].*?logger\.info\(f\"\[DEBUG\] Final extracted OfferItemIDs: {offer_item_ids}\"\)"
    
    new_offer_items_code = """# Use navigator utility for OfferItemIDs extraction
        offer_item_ids = self.navigator.extract_offer_item_ids(
            flight_price_response,
            request_id
        )"""
    
    matches = list(re.finditer(old_offer_items_pattern, content, flags=re.DOTALL))
    if matches:
        content = re.sub(old_offer_items_pattern, new_offer_items_code, content, flags=re.DOTALL)
        print(f"✓ Replaced OfferItemIDs extraction in _build_fallback_payload ({len(matches)} match)")
    else:
        print("⚠ Could not find OfferItemIDs extraction pattern in _build_fallback_payload")
    
    # Save refactored content
    new_lines = len(content.split('\n'))
    lines_removed = original_lines - new_lines
    
    print(f"\nRefactored file: {new_lines} lines")
    print(f"Lines removed in this phase: {lines_removed}")
    
    # Write refactored content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Wrote refactored file")
    
    return lines_removed

if __name__ == "__main__":
    try:
        lines_removed = refactor_fallback_payload()
        print(f"\n✅ Phase 2 refactoring complete! Removed {lines_removed} duplicate lines.")
    except Exception as e:
        print(f"\n❌ Error during refactoring: {e}")
        import traceback
        traceback.print_exc()
