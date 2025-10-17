"""
Automated Refactoring Script for booking.py

This script performs the following refactorings:
1. Removes duplicate airline extraction methods
2. Replaces ID extraction logic with navigator calls
3. Replaces PricedFlightOffer patterns with navigator calls
"""

import re

def refactor_booking_file():
    file_path = r"c:\Users\User\Desktop\REA FLIGHT PORTAL\Backend\services\flight\booking.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = len(content.split('\n'))
    print(f"Original file: {original_lines} lines")
    
    # 1. Remove the three duplicate methods (lines 279-435 approximately)
    # Find and remove _is_multi_airline_flight_price_response
    pattern1 = r'    def _is_multi_airline_flight_price_response\(self, flight_price_response.*?\n        except Exception as e:\n            logger\.error.*?\n            return False\n\n'
    content = re.sub(pattern1, '', content, flags=re.DOTALL)
    
    # Find and remove _extract_airline_from_multi_airline_price_response  
    pattern2 = r'    def _extract_airline_from_multi_airline_price_response\(self, flight_price_response.*?\n        except Exception as e:\n            logger\.error.*?\n            return None\n\n'
    content = re.sub(pattern2, '', content, flags=re.DOTALL)
    
    # Find and remove _extract_airline_code_from_price_response
    pattern3 = r'    def _extract_airline_code_from_price_response\(self, flight_price_response.*?\n        except Exception as e:\n            logger\.error.*?\n            return None\n\n'
    content = re.sub(pattern3, '', content, flags=re.DOTALL)
    
    print("✓ Removed duplicate airline extraction methods")
    
    # 2. Replace ID extraction patterns
    # Replace ShoppingResponseID extraction in _build_booking_payload
    old_shopping_id_extraction = r"# FIXED: Always try to extract ShoppingResponseID from the response structure\s+if not shopping_response_id:.*?logger\.info\(f\"\[DEBUG\] Extracted ShoppingResponseID from data: {shopping_response_id} \(ReqID: {request_id}\)\"\)"
    
    new_shopping_id_extraction = """# Use navigator utility for ShoppingResponseID extraction
            if not shopping_response_id:
                shopping_response_id = self.navigator.extract_id(
                    enhanced_flight_price_response,
                    'ShoppingResponseID',
                    request_id
                )"""
    
    content = re.sub(old_shopping_id_extraction, new_shopping_id_extraction, content, flags=re.DOTALL)
    print("✓ Replaced ShoppingResponseID extraction in _build_booking_payload")
    
    # 3. Replace PricedFlightOffer patterns
    # Pattern: get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    # Replace with: self.navigator.get_priced_flight_offers(...)
    
    # This pattern is tricky because we need context, so we'll do selective replacements
    
    # In _build_booking_payload around line 1249
    pattern_offers_1 = r"priced_offers = enhanced_flight_price_response\['PricedFlightOffers'\]\.get\('PricedFlightOffer', \[\]\)"
    replacement_offers_1 = "priced_offers = self.navigator.get_priced_flight_offers(enhanced_flight_price_response)"
    content = re.sub(pattern_offers_1, replacement_offers_1, content)
    
    print("✓ Replaced some PricedFlightOffer patterns")
    
    # Save refactored content
    new_lines = len(content.split('\n'))
    lines_removed = original_lines - new_lines
    
    print(f"\nRefactored file: {new_lines} lines")
    print(f"Lines removed: {lines_removed}")
    
    # Create backup
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(open(file_path, 'r', encoding='utf-8').read())
    print(f"✓ Created backup at {backup_path}")
    
    # Write refactored content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Wrote refactored file")
    
    return lines_removed

if __name__ == "__main__":
    try:
        lines_removed = refactor_booking_file()
        print(f"\n✅ Refactoring complete! Removed {lines_removed} duplicate lines.")
    except Exception as e:
        print(f"\n❌ Error during refactoring: {e}")
        import traceback
        traceback.print_exc()
