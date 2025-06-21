import json
from utils.data_transformer import _extract_reference_data, _transform_segment
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

# Extract reference data
reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)

# Get the first segment
data_lists = SAMPLE_VERTEIL_RESPONSE.get('DataLists', {})
segment_list = data_lists.get('FlightSegmentList', {})
segments = segment_list.get('FlightSegment', [])

if segments and len(segments) > 0:
    first_segment = segments[0]
    segment_key = first_segment.get('SegmentKey')
    
    if segment_key:
        # Get the actual segment data from reference_data
        segment_data = reference_data['segments'].get(segment_key, {})
        if segment_data:
            result = _transform_segment(segment_data, reference_data)
            
            print("Transformed segment result:")
            print(json.dumps(result, indent=2))
            
            print("\nDeparture keys:", list(result['departure'].keys()))
            print("Arrival keys:", list(result['arrival'].keys()))
        else:
            print("No segment data found")
    else:
        print("No segment key found")
else:
    print("No segments found")