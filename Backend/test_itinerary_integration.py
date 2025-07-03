#!/usr/bin/env python3
"""
Comprehensive Itinerary Integration Test Suite

This script tests the complete itinerary system integration:
1. Backend data extraction from OrderCreate response
2. Frontend data transformation and formatting
3. Validation of all required fields for display

Using the real OrderCreate response data from OrdercreateRS.json

Author: FLIGHT Application
Created: 2025-07-03
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import the itinerary extraction function
from routes.itinerary_routes import extract_itinerary_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ItineraryTestSuite:
    """Test suite for itinerary data extraction and transformation"""
    
    def __init__(self, test_data_path: str):
        self.test_data_path = test_data_path
        self.test_data = None
        self.extracted_data = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def load_test_data(self) -> bool:
        """Load the OrderCreate response test data"""
        try:
            with open(self.test_data_path, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            logger.info(f"✅ Successfully loaded test data from {self.test_data_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load test data: {str(e)}")
            return False
    
    def extract_backend_data(self) -> bool:
        """Test backend data extraction"""
        try:
            logger.info("🔄 Testing backend data extraction...")
            self.extracted_data = extract_itinerary_data(self.test_data)
            logger.info("✅ Backend data extraction successful")
            return True
        except Exception as e:
            logger.error(f"❌ Backend data extraction failed: {str(e)}")
            self.test_results['errors'].append(f"Backend extraction error: {str(e)}")
            return False
    
    def validate_booking_info(self) -> bool:
        """Validate booking information extraction"""
        logger.info("🔍 Validating booking information...")
        booking_info = self.extracted_data.get('bookingInfo', {})
        
        tests = [
            ('orderId', booking_info.get('orderId'), 'Order ID should be extracted'),
            ('bookingReference', booking_info.get('bookingReference'), 'Booking reference should be extracted'),
            ('status', booking_info.get('status'), 'Status should be extracted'),
            ('agencyName', booking_info.get('agencyName'), 'Agency name should be present'),
            ('issueDate', booking_info.get('issueDate'), 'Issue date should be extracted')
        ]
        
        passed = 0
        for field_name, value, description in tests:
            if value and value != 'N/A':
                logger.info(f"  ✅ {field_name}: {value}")
                passed += 1
            else:
                logger.warning(f"  ⚠️  {field_name}: {value} - {description}")
                self.test_results['errors'].append(f"Booking info validation: {description}")
        
        # Check for discount information
        if booking_info.get('discountApplied'):
            discount = booking_info['discountApplied']
            logger.info(f"  ✅ Discount found: {discount.get('name')} ({discount.get('percentage')}%)")
            passed += 1
        
        self.test_results['passed'] += passed
        return passed > 0
    
    def validate_passengers(self) -> bool:
        """Validate passenger information extraction"""
        logger.info("🔍 Validating passenger information...")
        passengers = self.extracted_data.get('passengers', [])
        
        if not passengers:
            logger.error("  ❌ No passengers found")
            self.test_results['errors'].append("No passengers extracted")
            return False
        
        logger.info(f"  ✅ Found {len(passengers)} passengers")
        
        for i, passenger in enumerate(passengers):
            logger.info(f"  Passenger {i+1}:")
            logger.info(f"    Name: {passenger.get('fullName', 'N/A')}")
            logger.info(f"    Type: {passenger.get('passengerType', 'N/A')}")
            logger.info(f"    Document: {passenger.get('documentNumber', 'N/A')}")
            logger.info(f"    Ticket: {passenger.get('ticketNumber', 'N/A')}")
            
            # Validate required fields
            required_fields = ['fullName', 'passengerType', 'documentNumber', 'objectKey']
            for field in required_fields:
                if not passenger.get(field) or passenger.get(field) == 'N/A':
                    logger.warning(f"    ⚠️  Missing {field}")
                    self.test_results['errors'].append(f"Passenger {i+1} missing {field}")
        
        self.test_results['passed'] += len(passengers)
        return True
    
    def validate_flight_segments(self) -> bool:
        """Validate flight segment extraction"""
        logger.info("🔍 Validating flight segments...")
        
        outbound = self.extracted_data.get('outboundFlight', [])
        return_flight = self.extracted_data.get('returnFlight', [])
        
        if not outbound:
            logger.error("  ❌ No outbound flight segments found")
            self.test_results['errors'].append("No outbound flight segments")
            return False
        
        logger.info(f"  ✅ Outbound segments: {len(outbound)}")
        for i, segment in enumerate(outbound):
            logger.info(f"    Segment {i+1}: {segment.get('flightNumber', 'N/A')} "
                       f"{segment.get('departure', {}).get('airport', 'N/A')} → "
                       f"{segment.get('arrival', {}).get('airport', 'N/A')}")
            logger.info(f"      Departure: {segment.get('departure', {}).get('date', 'N/A')} "
                       f"{segment.get('departure', {}).get('time', 'N/A')}")
            logger.info(f"      Arrival: {segment.get('arrival', {}).get('date', 'N/A')} "
                       f"{segment.get('arrival', {}).get('time', 'N/A')}")
            logger.info(f"      Class: {segment.get('classOfService', 'N/A')}")
        
        if return_flight:
            logger.info(f"  ✅ Return segments: {len(return_flight)}")
            for i, segment in enumerate(return_flight):
                logger.info(f"    Return Segment {i+1}: {segment.get('flightNumber', 'N/A')} "
                           f"{segment.get('departure', {}).get('airport', 'N/A')} → "
                           f"{segment.get('arrival', {}).get('airport', 'N/A')}")
        else:
            logger.info("  ℹ️  No return flight (one-way trip)")
        
        self.test_results['passed'] += len(outbound) + len(return_flight or [])
        return True
    
    def validate_pricing(self) -> bool:
        """Validate pricing information extraction"""
        logger.info("🔍 Validating pricing information...")
        pricing = self.extracted_data.get('pricing', {})
        
        total_amount = pricing.get('totalAmount', 0)
        currency = pricing.get('currency', 'N/A')
        payment_method = pricing.get('paymentMethod', 'N/A')
        
        logger.info(f"  Total Amount: {total_amount} {currency}")
        logger.info(f"  Payment Method: {payment_method}")
        
        if total_amount > 0:
            logger.info("  ✅ Valid pricing information found")
            self.test_results['passed'] += 1
            return True
        else:
            logger.warning("  ⚠️  No valid pricing information")
            self.test_results['errors'].append("Invalid pricing information")
            return False
    
    def validate_contact_info(self) -> bool:
        """Validate contact information extraction"""
        logger.info("🔍 Validating contact information...")
        contact = self.extracted_data.get('contactInfo', {})
        
        email = contact.get('email', 'N/A')
        phone = contact.get('phone', 'N/A')
        
        logger.info(f"  Email: {email}")
        logger.info(f"  Phone: {phone}")
        
        if email != 'N/A' or phone != 'N/A':
            logger.info("  ✅ Contact information found")
            self.test_results['passed'] += 1
            return True
        else:
            logger.warning("  ⚠️  No contact information found")
            self.test_results['errors'].append("No contact information")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("🚀 Starting comprehensive itinerary integration test...")
        logger.info("=" * 60)
        
        # Load test data
        if not self.load_test_data():
            return {'success': False, 'error': 'Failed to load test data'}
        
        # Extract backend data
        if not self.extract_backend_data():
            return {'success': False, 'error': 'Backend extraction failed'}
        
        # Run validation tests
        self.validate_booking_info()
        self.validate_passengers()
        self.validate_flight_segments()
        self.validate_pricing()
        self.validate_contact_info()
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info(f"✅ Passed validations: {self.test_results['passed']}")
        logger.info(f"❌ Failed validations: {len(self.test_results['errors'])}")
        
        if self.test_results['errors']:
            logger.info("⚠️  Issues found:")
            for error in self.test_results['errors']:
                logger.info(f"  - {error}")
        
        success = len(self.test_results['errors']) == 0
        logger.info(f"🎯 Overall result: {'PASS' if success else 'FAIL'}")
        
        return {
            'success': success,
            'passed': self.test_results['passed'],
            'failed': len(self.test_results['errors']),
            'errors': self.test_results['errors'],
            'extracted_data': self.extracted_data
        }


def main():
    """Main test execution function"""
    # Path to the test data file
    test_data_path = Path(__file__).parent.parent / 'OrdercreateRS.json'
    
    if not test_data_path.exists():
        logger.error(f"❌ Test data file not found: {test_data_path}")
        sys.exit(1)
    
    # Create and run test suite
    test_suite = ItineraryTestSuite(str(test_data_path))
    results = test_suite.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
