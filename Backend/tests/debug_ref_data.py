import json
from utils.data_transformer import _extract_reference_data

# Load the real API response
with open('tests/airshoping_response.json', 'r') as f:
    data = json.load(f)

# Extract reference data
ref = _extract_reference_data(data)

print(f"Segments: {len(ref['segments'])}")
print(f"Airports: {len(ref['airports'])}")
print(f"Sample segment keys: {list(ref['segments'].keys())[:3]}")
print(f"Sample airport keys: {list(ref['airports'].keys())[:3]}")

# Check if DataLists exists
data_lists = data.get('DataLists', {})
print(f"DataLists exists: {bool(data_lists)}")
print(f"DataLists keys: {list(data_lists.keys())}")

# Check FlightSegmentList
segment_list = data_lists.get('FlightSegmentList', {})
print(f"FlightSegmentList exists: {bool(segment_list)}")
if segment_list:
    segments = segment_list.get('FlightSegment', [])
    print(f"FlightSegment count: {len(segments) if isinstance(segments, list) else 'Not a list'}")
    if segments and len(segments) > 0:
        print(f"First segment keys: {list(segments[0].keys()) if isinstance(segments[0], dict) else 'Not a dict'}")