"""
Debug script to save transformed flight data to a JSON file for inspection.
"""
import json
import os
from datetime import datetime
from utils.data_transformer import transform_verteil_to_frontend, _extract_reference_data

def load_real_api_response():
    """Load the real API response from airshoping_response.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, 'airshoping_response.json')
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_transformed_output():
    """Load test data, transform it, and save to a file."""
    # Load test data
    test_data = load_real_api_response()
    
    # Extract reference data
    reference_data = _extract_reference_data(test_data)
    
    # Transform the data
    transformed_data = transform_verteil_to_frontend(test_data)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'debug_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'transformed_flights_{timestamp}.json')
    
    # Save the transformed data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'transformed_flights': transformed_data,
            'reference_data': reference_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Transformed data saved to: {output_file}")
    print(f"Number of transformed flights: {len(transformed_data) if transformed_data else 0}")
    
    # Also save a simplified version with just the first flight for easier inspection
    if transformed_data and len(transformed_data) > 0:
        simple_output_file = os.path.join(output_dir, f'simplified_transformed_flight_{timestamp}.json')
        with open(simple_output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_data[0], f, indent=2, ensure_ascii=False)
        print(f"Simplified output saved to: {simple_output_file}")

if __name__ == '__main__':
    save_transformed_output()
