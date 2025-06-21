import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestPassengerTransformationRefactor:
    """Test suite for the passenger transformation refactor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock service instance to test the transformation logic
        self.service = Mock()
        
        # Import and bind the actual method we want to test
        from services.flight.booking import FlightBookingService
        self.service._build_booking_payload = FlightBookingService._build_booking_payload.__get__(self.service, FlightBookingService)
    
    def test_frontend_passenger_format_transformation(self):
        """Test that service correctly transforms frontend passenger format."""
        # Frontend passenger format (as received from API endpoint)
        frontend_passengers = [
            {
                'type': 'adult',
                'firstName': 'John',
                'lastName': 'Doe',
                'gender': 'male',
                'dob': {
                    'year': '1990',
                    'month': '5',
                    'day': '15'
                },
                'nationality': 'US',
                'documentNumber': 'P123456789',
                'issuingCountry': 'US',
                'expiryDate': {
                    'year': '2030',
                    'month': '12',
                    'day': '31'
                }
            },
            {
                'type': 'child',
                'firstName': 'Jane',
                'lastName': 'Doe',
                'gender': 'female',
                'dob': {
                    'year': '2015',
                    'month': '3',
                    'day': '10'
                },
                'nationality': 'US'
            }
        ]
        
        flight_price_response = {
            'shopping_response_id': 'test-shopping-123',
            'offer_id': 'test-offer-456'
        }
        
        payment_info = {
            'payment_method': 'PaymentCard',
            'currency': 'USD',
            'card_type': 'Visa',
            'card_number': '4111111111111111',
            'expiry_date': '12/25',
            'cvv': '123',
            'card_holder_name': 'John Doe'
        }
        
        contact_info = {
            'email': 'john.doe@example.com',
            'phone': '+1234567890'
        }
        
        # Mock the generate_order_create_rq function
        with patch('services.flight.booking.generate_order_create_rq') as mock_generate:
            mock_generate.return_value = {'test': 'payload'}
            
            # Call the method
            result = self.service._build_booking_payload(
                flight_price_response,
                frontend_passengers,
                payment_info,
                contact_info,
                'test-request-123'
            )
            
            # Verify the function was called
            assert mock_generate.called
            
            # Get the arguments passed to generate_order_create_rq
            call_args = mock_generate.call_args
            passengers_data = call_args.kwargs['passengers_data']
            
            # Verify adult passenger transformation
            adult_passenger = passengers_data[0]
            assert adult_passenger['type'] == 'ADT'
            assert adult_passenger['title'] == 'Mr'
            assert adult_passenger['first_name'] == 'John'
            assert adult_passenger['last_name'] == 'Doe'
            assert adult_passenger['date_of_birth'] == '1990-05-15'
            assert adult_passenger['gender'] == 'male'
            assert adult_passenger['nationality'] == 'US'
            
            # Verify document information
            assert len(adult_passenger['documents']) == 1
            document = adult_passenger['documents'][0]
            assert document['type'] == 'Passport'
            assert document['number'] == 'P123456789'
            assert document['expiry_date'] == '2030-12-31'
            assert document['issuing_country'] == 'US'
            
            # Verify contact info is added to first passenger
            assert 'contact' in adult_passenger
            assert adult_passenger['contact']['email'] == 'john.doe@example.com'
            assert adult_passenger['contact']['phone'] == '+1234567890'
            
            # Verify child passenger transformation
            child_passenger = passengers_data[1]
            assert child_passenger['type'] == 'CHD'
            assert child_passenger['title'] == 'Ms'
            assert child_passenger['first_name'] == 'Jane'
            assert child_passenger['last_name'] == 'Doe'
            assert child_passenger['date_of_birth'] == '2015-03-10'
            assert child_passenger['gender'] == 'female'
            assert child_passenger['nationality'] == 'US'
            
            # Verify no documents for child (not provided)
            assert 'documents' not in child_passenger or len(child_passenger.get('documents', [])) == 0
            
            # Verify no contact info for second passenger
            assert 'contact' not in child_passenger
    
    def test_passenger_type_mapping(self):
        """Test that passenger types are correctly mapped."""
        test_cases = [
            ('adult', 'ADT'),
            ('child', 'CHD'),
            ('infant', 'INF'),
            ('unknown', 'ADT')  # Default fallback
        ]
        
        for frontend_type, expected_ptc in test_cases:
            frontend_passengers = [{
                'type': frontend_type,
                'firstName': 'Test',
                'lastName': 'User',
                'gender': 'male'
            }]
            
            with patch('services.flight.booking.generate_order_create_rq') as mock_generate:
                mock_generate.return_value = {'test': 'payload'}
                
                self.service._build_booking_payload(
                    {'shopping_response_id': 'test'},
                    frontend_passengers,
                    {'payment_method': 'PaymentCard'},
                    {'email': 'test@example.com'},
                    'test-request'
                )
                
                call_args = mock_generate.call_args
                passengers_data = call_args.kwargs['passengers_data']
                assert passengers_data[0]['type'] == expected_ptc
    
    def test_date_formatting(self):
        """Test that dates are correctly formatted from frontend objects."""
        frontend_passengers = [{
            'type': 'adult',
            'firstName': 'Test',
            'lastName': 'User',
            'gender': 'male',
            'dob': {
                'year': '1985',
                'month': '1',
                'day': '5'
            },
            'documentNumber': 'P123456',
            'expiryDate': {
                'year': '2025',
                'month': '11',
                'day': '3'
            }
        }]
        
        with patch('services.flight.booking.generate_order_create_rq') as mock_generate:
            mock_generate.return_value = {'test': 'payload'}
            
            self.service._build_booking_payload(
                {'shopping_response_id': 'test'},
                frontend_passengers,
                {'payment_method': 'PaymentCard'},
                {'email': 'test@example.com'},
                'test-request'
            )
            
            call_args = mock_generate.call_args
            passengers_data = call_args.kwargs['passengers_data']
            passenger = passengers_data[0]
            
            # Test birth date formatting (zero-padded)
            assert passenger['date_of_birth'] == '1985-01-05'
            
            # Test expiry date formatting (zero-padded)
            assert passenger['documents'][0]['expiry_date'] == '2025-11-03'
    
    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        # Minimal passenger data
        frontend_passengers = [{
            'type': 'adult',
            'firstName': 'Test',
            'lastName': 'User'
        }]
        
        with patch('services.flight.booking.generate_order_create_rq') as mock_generate:
            mock_generate.return_value = {'test': 'payload'}
            
            self.service._build_booking_payload(
                {'shopping_response_id': 'test'},
                frontend_passengers,
                {'payment_method': 'PaymentCard'},
                {'email': 'test@example.com'},
                'test-request'
            )
            
            call_args = mock_generate.call_args
            passengers_data = call_args.kwargs['passengers_data']
            passenger = passengers_data[0]
            
            # Verify defaults and empty values
            assert passenger['type'] == 'ADT'
            assert passenger['first_name'] == 'Test'
            assert passenger['last_name'] == 'User'
            assert passenger['date_of_birth'] is None
            assert passenger['gender'] == ''
            assert passenger['nationality'] == ''
            assert 'documents' not in passenger or len(passenger.get('documents', [])) == 0


if __name__ == '__main__':
    pytest.main([__file__])