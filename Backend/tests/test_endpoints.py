"""
Integration tests for the Verteil NDC API endpoints.

This script tests the complete flow from flight search to booking creation.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
import unittest
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TestVerteilEndpoints(unittest.TestCase):    
    """Test cases for Verteil NDC API endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before any tests are run."""
        cls.base_url = "http://localhost:5000/api/verteil"
        
        # Test data
        cls.test_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        cls.return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
        
        # Sample passenger data
        cls.passenger_data = [
            {
                "type": "ADT",
                "title": "MR",
                "firstName": "John",
                "lastName": "Doe",
                "gender": "M",
                "dateOfBirth": "1990-01-01",
                "documents": [
                    {
                        "type": "PASSPORT",
                        "number": "AB1234567",
                        "expiryDate": "2030-12-31",
                        "issuanceCountry": "US"
                    }
                ]
            }
        ]
        
        # Sample contact info
        cls.contact_info = {
            "email": "test@example.com",
            "phoneNumber": "+1234567890",
            "phoneCountryCode": "1"
        }
        
        # Sample payment info (in a real scenario, use a test payment method)
        cls.payment_info = {
            "paymentMethod": "CREDIT_CARD",
            "cardNumber": "4111111111111111",
            "expiryDate": "12/30",
            "cvv": "123",
            "cardHolderName": "John Doe"
        }
    
    def test_1_air_shopping(self):
        """Test the air shopping endpoint."""
        logger.info("\n=== Testing AirShopping Endpoint ===")
        
        # Prepare request data
        search_data = {
            "origin": "JFK",
            "destination": "LAX",
            "departure_date": self.test_date,
            "return_date": self.return_date,
            "adults": 1,
            "children": 0,
            "infants": 0,
            "cabin_class": "ECONOMY",
            "trip_type": "roundtrip"
        }
        
        # Make the request
        response = requests.post(
            f"{self.base_url}/air-shopping",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, 
                        f"Expected status code 200, got {response.status_code}. Response: {response.text}")
        
        # Parse response
        data = response.json()
        self.assertIn("data", data, "Response missing 'data' field")
        self.assertIn("flight_offers", data["data"], "Response missing 'flight_offers' field")
        
        # Save offer data for next test
        if data["data"]["flight_offers"]:
            self.offer = data["data"]["flight_offers"][0]
            logger.info(f"Found {len(data['data']['flight_offers'])} flight offers")
        else:
            self.skipTest("No flight offers returned, cannot continue with remaining tests")
    
    def test_2_flight_price(self):
        """Test the flight price endpoint."""
        if not hasattr(self, 'offer'):
            self.skipTest("No offer available from previous test")
            
        logger.info("\n=== Testing FlightPrice Endpoint ===")
        
        # Prepare request data
        price_data = {
            "offer_id": self.offer["id"],
            "shopping_response_id": self.offer.get("shopping_response_id", ""),
            "air_shopping_rs": self.offer.get("air_shopping_rs", {})
        }
        
        # Make the request
        response = requests.post(
            f"{self.base_url}/flight-price",
            json=price_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, 
                        f"Expected status code 200, got {response.status_code}. Response: {response.text}")
        
        # Parse response
        data = response.json()
        self.assertIn("data", data, "Response missing 'data' field")
        
        # Save pricing data for next test
        self.pricing_data = data["data"]
        logger.info(f"Pricing data received: {json.dumps(self.pricing_data, indent=2)}")
    
    @unittest.skip("Enable this test when you want to test actual booking creation")
    def test_3_order_create(self):
        """Test the order creation endpoint."""
        if not hasattr(self, 'pricing_data'):
            self.skipTest("No pricing data available from previous test")
            
        logger.info("\n=== Testing OrderCreate Endpoint ===")
        
        # Prepare request data
        order_data = {
            "flight_price_rs": self.pricing_data.get("flight_price_rs", {}),
            "passenger_details": self.passenger_data,
            "payment_details": self.payment_info,
            "contact_information": self.contact_info
        }
        
        # Make the request
        response = requests.post(
            f"{self.base_url}/order-create",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, 
                        f"Expected status code 200, got {response.status_code}. Response: {response.text}")
        
        # Parse response
        data = response.json()
        self.assertIn("data", data, "Response missing 'data' field")
        self.assertIn("booking_reference", data["data"], "Response missing 'booking_reference'")
        
        logger.info(f"Booking created successfully. Reference: {data['data']['booking_reference']}")

if __name__ == "__main__":
    # Run tests
    unittest.main()
