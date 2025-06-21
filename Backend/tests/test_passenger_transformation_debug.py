import json
import sys
import os

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the transformation logic directly
from services.flight.booking import FlightBookingService

def test_passenger_transformation():
    """Test passenger transformation logic directly"""
    
    # Sample passenger data (frontend format) - using the format from the actual frontend
    passengers = [
        {
            "type": "adult",
            "title": "mr",
            "firstName": "John",
            "lastName": "Doe",
            "gender": "male",
            "dob": {
                "year": "1990",
                "month": "1",
                "day": "15"
            },
            "document_type": "passport",
            "document_number": "A12345678",
            "document_expiry": "2030-12-31",
            "document_country": "US"
        },
        {
            "type": "adult",
            "title": "ms",
            "firstName": "Jane",
            "lastName": "Smith",
            "gender": "female",
            "dob": {
                "year": "1985",
                "month": "5",
                "day": "20"
            },
            "document_type": "passport",
            "document_number": "B87654321",
            "document_expiry": "2029-08-15",
            "document_country": "US"
        }
    ]
    
    print("=== TESTING PASSENGER TRANSFORMATION ===")
    print("\n1. Original passenger data (frontend format):")
    for i, passenger in enumerate(passengers):
        print(f"Passenger {i+1}: {json.dumps(passenger, indent=2)}")
    
    print("\n2. Testing transformation process...")
    
    # Manually implement the transformation logic from booking.py
    transformed_passengers = []
    for passenger in passengers:
        # Map frontend passenger type to expected format
        pax_type = passenger.get('type', 'adult')
        ptc_mapping = {
            'adult': 'ADT',
            'child': 'CHD', 
            'infant': 'INF'
        }
        ptc = ptc_mapping.get(pax_type, 'ADT')
        
        # Format birth date from frontend dob object
        dob = passenger.get('dob', {})
        birth_date = None
        if dob and dob.get('year') and dob.get('month') and dob.get('day'):
            birth_date = f"{dob['year']}-{dob['month'].zfill(2)}-{dob['day'].zfill(2)}"
        
        # Map title from frontend
        title_mapping = {
            'mr': 'Mr',
            'ms': 'Ms', 
            'mrs': 'Mrs',
            'miss': 'Miss',
            'dr': 'Dr'
        }
        title = title_mapping.get(passenger.get('title', '').lower(), 
                                "Mr" if passenger.get('gender', '').lower() == 'male' else "Ms")
        
        # Transform to the structure expected by build_ordercreate_rq
        transformed_passenger = {
            'PTC': ptc,  # Direct value, not nested
            'Name': {
                'Title': title,
                'Given': [passenger.get('firstName', '')],  # List format expected
                'Surname': passenger.get('lastName', '')
            },
            'Gender': passenger.get('gender', '').capitalize(),
            'BirthDate': birth_date
        }
        
        # Add document information if available
        if passenger.get('document_type') and passenger.get('document_number'):
            doc_type_mapping = {
                'passport': 'PT',
                'national_id': 'NI', 
                'id_card': 'ID'
            }
            doc_type = doc_type_mapping.get(passenger.get('document_type'), 'PT')
            
            transformed_passenger['Documents'] = {
                'Type': doc_type,
                'ID': passenger.get('document_number'),
                'DateOfExpiration': passenger.get('document_expiry'),
                'CountryOfIssuance': passenger.get('document_country')
            }
        
        transformed_passengers.append(transformed_passenger)
    
    print("\n3. Transformation completed!")
    print("\n4. Transformed passenger data (backend format):")
    for i, passenger in enumerate(transformed_passengers):
        print(f"\nTransformed Passenger {i+1}:")
        print(json.dumps(passenger, indent=2))
        
        # Check for issues
        if not passenger.get('PTC'):
            print(f"WARNING: PTC is missing for passenger {i+1}")
        if not passenger.get('Name', {}).get('Given'):
            print(f"WARNING: Given name is empty for passenger {i+1}")
        if not passenger.get('Name', {}).get('Surname'):
            print(f"WARNING: Surname is missing for passenger {i+1}")
        if not passenger.get('BirthDate'):
            print(f"WARNING: BirthDate is missing for passenger {i+1}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_passenger_transformation()