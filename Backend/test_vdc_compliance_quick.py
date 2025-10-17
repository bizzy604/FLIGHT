"""Quick test to validate VDC compliance fixes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request

# Load ancillary response
ancillary_path = Path(__file__).parent / 'api_logs' / 'ancillary_pricing' / 'AncillaryPricing_RS.json'
with open(ancillary_path, 'r', encoding='utf-8') as f:
    ancillary_log = json.load(f)

ancillary_resp = ancillary_log.get('response', {})

# Create test data
flight_price_response = {
    "ShoppingResponseID": ancillary_resp.get('ShoppingResponseID', {}),
    "PricedFlightOffers": ancillary_resp.get('PricedFlightOffers', {}),
    "DataLists": ancillary_resp.get('DataLists', {})
}

passengers_data = [
    {
        "PTC": "ADT",
        "Name": {"Given": ["John"], "Surname": "Doe"},
        "Gender": "M",
        "BirthDate": "1990-01-01",
        "Documents": {"Document": [{"Type": "PT", "Number": "P123456"}]},
        "Contacts": {"Contact": [{"EmailContact": {"Address": {"value": "test@test.com"}}}]},
        "ObjectKey": "PAX1"
    }
]

payment_info = {"MethodType": "CASH", "currency": "INR", "CashInd": True}
selected_seats = ["f29c1264-524b-4553-9c12-64524bb50033"]

print("="*80)
print("VDC COMPLIANCE TEST")
print("="*80)
print(f"\nancillary_pricing_response: {'PROVIDED' if ancillary_resp else 'NONE'}")
print(f"selected_seats: {selected_seats}")

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Generate OrderCreate
result = build_ordercreate_enhanced_request(
    flight_price_response=flight_price_response,
    passengers_data=passengers_data,
    payment_input_info=payment_info,
    servicelist_response=None,
    seatavailability_response=None,
    selected_services=[],
    selected_seats=selected_seats,
    ancillary_pricing_response=ancillary_resp
)

# Validate
offer_items = result.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
service_list = result.get('Query', {}).get('DataLists', {}).get('ServiceList', {}).get('Service', [])

print(f"\n{'='*80}")
print("RESULTS:")
print(f"{'='*80}")
print(f"\nOfferItems: {len(offer_items)}")

seat_count = 0
for idx, item in enumerate(offer_items):
    item_type = list(item.get('OfferItemType', {}).keys())[0]
    refs = item.get('OfferItemID', {}).get('refs', [])
    print(f"  [{idx}] Type: {item_type}, Refs: {len(refs)}")
    
    if 'SeatItem' in item.get('OfferItemType', {}):
        seat_count += 1
        seat = item['OfferItemType']['SeatItem'][0]
        print(f"       SeatItem keys: {list(seat.keys())}")

print(f"\nServiceList: {len(service_list)} items")
for idx, svc in enumerate(service_list):
    print(f"  [{idx}] ObjectKey: {svc.get('ObjectKey')}")

print(f"\n{'='*80}")
print("VDC COMPLIANCE CHECK:")
print(f"{'='*80}")
print(f"✓ SeatItems: {seat_count}/1")
print(f"✓ ServiceList: {len(service_list)}/1")
print(f"✓ Items with refs: {sum(1 for item in offer_items if len(item.get('OfferItemID', {}).get('refs', [])) > 0)}/2")

if seat_count == 1 and len(service_list) == 1:
    print("\n✅ ALL VDC COMPLIANCE CHECKS PASSED!")
else:
    print("\n❌ VDC COMPLIANCE ISSUES REMAIN")
