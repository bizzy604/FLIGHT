import json
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

# Check the structure of segments
data_lists = SAMPLE_VERTEIL_RESPONSE.get('DataLists', {})
segment_list = data_lists.get('FlightSegmentList', {})
segments = segment_list.get('FlightSegment', [])

print(f"Type of segments: {type(segments)}")
print(f"Length of segments: {len(segments) if hasattr(segments, '__len__') else 'No length'}")

if segments and len(segments) > 0:
    print(f"Type of first segment: {type(segments[0])}")
    print(f"First segment content: {segments[0]}")
    
    if isinstance(segments[0], dict):
        print(f"First segment keys: {list(segments[0].keys())}")
    else:
        print("First segment is not a dictionary!")
else:
    print("No segments found")