import json

# Load service response
with open('tests/integration/live_test_data/route_2_ancillary_services.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("Service List Response Structure")
print("=" * 80)

# Check raw response
raw_response = data.get('data', {})
services_obj = raw_response.get('Services', {})
service_list = services_obj.get('Service', [])

print(f"\nFound {len(service_list)} services")
print(f"\nFirst service:")
if service_list:
    first = service_list[0]
    print(f"  ObjectKey: {first.get('ObjectKey')}")
    print(f"  ServiceID: {first.get('ServiceID', {}).get('value')}")
    print(f"  Name: {first.get('Name', {}).get('value')}")
    print(f"  Price: {first.get('Price', [{}])[0].get('Total', {}).get('value')} {first.get('Price', [{}])[0].get('Total', {}).get('Code')}")
    print(f"  PricedInd: {first.get('PricedInd')}")
