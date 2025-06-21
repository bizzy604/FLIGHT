#!/usr/bin/env python
"""
Integration Test Script for Verteil Flight API Endpoints

This script tests the complete flow: air-shopping → flight-price → order-create
ensuring all endpoints work correctly together with proper data dependencies.
"""
import os
import sys
import json
import logging
import asyncio
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the project root to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_tests")

# Import the app for testing
from app import create_app
from quart.testing import QuartClient

class TestVerteilEndpointsIntegration(unittest.TestCase):
    """
    Integration tests for the Verteil flight API endpoints.
    Tests the complete flow: air-shopping → flight-price → order-create
    """
    
    async def asyncSetUp(self):
        """Set up the test client and other test variables."""
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()
        self.base_url = "/api/verteil"
        
        # Store test data that will be shared across tests
        self.test_data = {
            "air_shopping_response": None,
            "selected_offer": None,
            "flight_price_response": None,
            "order_create_response": None
        }
        
        logger.info("Test setup complete")
    
    async def asyncTearDown(self):
        """Clean up after tests."""
        logger.info("Test teardown complete")
    
    def _get_tomorrow_date(self) -> str:
        """Get tomorrow's date in YYYY-MM-DD format."""
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")
    
    def _get_next_week_date(self) -> str:
        """Get date one week from now in YYYY-MM-DD format."""
        next_week = datetime.now() + timedelta(days=7)
        return next_week.strftime("%Y-%m-%d")
    
    def _create_air_shopping_payload(self) -> Dict[str, Any]:
        """Create a sample air shopping request payload."""
        return {
            "tripType": "ONE_WAY",
            "odSegments": [
                {
                    "origin": "LHR",
                    "destination": "BOM",
                    "departureDate": self._get_tomorrow_date()
                }
            ],
            "numAdults": 1,
            "numChildren": 0,
            "numInfants": 0,
            "cabinPreference": "ECONOMY",
            "directOnly": False
        }
    
    def _create_flight_price_payload(self, air_shopping_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a flight price request payload based on air shopping response.
        
        Args:
            air_shopping_response: The response from the air-shopping endpoint
            
        Returns:
            Dict containing the flight price request payload
        """
        # Extract the first offer from the air shopping response
        offers = air_shopping_response.get("data", {}).get("offers", [])
        if not offers:
            raise ValueError("No offers found in air shopping response")
        
        selected_offer = offers[0]
        self.test_data["selected_offer"] = selected_offer
        
        return {
            "offer_id": selected_offer.get("id"),
            "shopping_response_id": air_shopping_response.get("data", {}).get("shopping_response_id"),
            "air_shopping_rs": air_shopping_response.get("data", {})
        }
    
    def _create_order_create_payload(self, flight_price_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an order create request payload based on flight price response.
        
        Args:
            flight_price_response: The response from the flight-price endpoint
            
        Returns:
            Dict containing the order create request payload
        """
        # Create sample passenger data
        passengers = [
            {
                "type": "ADT",  # Adult
                "title": "MR",
                "firstName": "John",
                "lastName": "Doe",
                "dateOfBirth": "1985-01-15",
                "gender": "M",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "nationality": "US",
                "documentType": "PASSPORT",
                "documentNumber": "AB123456",
                "documentExpiryDate": "2030-01-01",
                "documentIssuingCountry": "US"
            }
        ]
        
        # Create sample payment data
        payment = {
            "type": "CREDIT_CARD",
            "cardNumber": "4111111111111111",
            "cardHolderName": "John Doe",
            "expiryMonth": "12",
            "expiryYear": "2030",
            "cvv": "123"
        }
        
        # Create sample contact information
        contact_info = {
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        }
        
        return {
            "flight_offer": self.test_data["selected_offer"],
            "passengers": passengers,
            "payment": payment,
            "contact_info": contact_info
        }
    
    def _validate_response_format(self, response_data: Dict[str, Any], endpoint: str) -> None:
        """
        Validate the format of the response from an endpoint.
        
        Args:
            response_data: The response data to validate
            endpoint: The endpoint name for logging
        """
        # Check common fields
        self.assertIn("status", response_data)
        self.assertIn("request_id", response_data)
        
        # Endpoint-specific validation
        if endpoint == "air-shopping":
            self.assertIn("data", response_data)
            data = response_data["data"]
            self.assertIn("offers", data)
            self.assertIsInstance(data["offers"], list)
            
        elif endpoint == "flight-price":
            self.assertIn("data", response_data)
            data = response_data["data"]
            self.assertIn("price", data)
            
        elif endpoint == "order-create":
            self.assertIn("data", response_data)
            data = response_data["data"]
            self.assertIn("booking_reference", data)
    
    async def test_01_air_shopping(self):
        """Test the air-shopping endpoint."""
        logger.info("Testing air-shopping endpoint...")
        
        # Create payload
        payload = self._create_air_shopping_payload()
        logger.info(f"Air shopping request payload: {json.dumps(payload, indent=2)}")
        
        # Make request
        response = await self.client.post(
            f"{self.base_url}/air-shopping",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = await response.get_json()
        logger.info(f"Air shopping response status: {response.status_code}")
        
        # Validate response format
        self._validate_response_format(response_data, "air-shopping")
        
        # Store response for next test
        self.test_data["air_shopping_response"] = response_data
        
        # Ensure we have offers
        self.assertTrue(len(response_data.get("data", {}).get("offers", [])) > 0)
        logger.info(f"Found {len(response_data.get('data', {}).get('offers', []))} offers")
        
        return response_data
    
    async def test_02_flight_price(self):
        """Test the flight-price endpoint using data from air-shopping."""
        logger.info("Testing flight-price endpoint...")
        
        # Ensure we have air shopping data
        if not self.test_data["air_shopping_response"]:
            logger.info("No air shopping data available. Running air-shopping test first...")
            self.test_data["air_shopping_response"] = await self.test_01_air_shopping()
        
        # Create payload
        payload = self._create_flight_price_payload(self.test_data["air_shopping_response"])
        logger.info(f"Flight price request payload: {json.dumps(payload, indent=2)}")
        
        # Make request
        response = await self.client.post(
            f"{self.base_url}/flight-price",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = await response.get_json()
        logger.info(f"Flight price response status: {response.status_code}")
        
        # Validate response format
        self._validate_response_format(response_data, "flight-price")
        
        # Store response for next test
        self.test_data["flight_price_response"] = response_data
        
        return response_data
    
    async def test_03_order_create(self):
        """Test the order-create endpoint using data from flight-price."""
        logger.info("Testing order-create endpoint...")
        
        # Ensure we have flight price data
        if not self.test_data["flight_price_response"]:
            logger.info("No flight price data available. Running flight-price test first...")
            self.test_data["flight_price_response"] = await self.test_02_flight_price()
        
        # Create payload
        payload = self._create_order_create_payload(self.test_data["flight_price_response"])
        logger.info(f"Order create request payload: {json.dumps(payload, indent=2)}")
        
        # Make request
        response = await self.client.post(
            f"{self.base_url}/order-create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = await response.get_json()
        logger.info(f"Order create response status: {response.status_code}")
        
        # Validate response format
        self._validate_response_format(response_data, "order-create")
        
        # Store response
        self.test_data["order_create_response"] = response_data
        
        return response_data
    
    async def test_04_complete_flow(self):
        """Test the complete booking flow from air-shopping to order-create."""
        logger.info("Testing complete booking flow...")
        
        # Step 1: Air Shopping
        air_shopping_response = await self.test_01_air_shopping()
        self.assertIsNotNone(air_shopping_response)
        
        # Step 2: Flight Price
        flight_price_response = await self.test_02_flight_price()
        self.assertIsNotNone(flight_price_response)
        
        # Step 3: Order Create
        order_create_response = await self.test_03_order_create()
        self.assertIsNotNone(order_create_response)
        
        logger.info("Complete booking flow test successful!")
        
        return {
            "air_shopping": air_shopping_response,
            "flight_price": flight_price_response,
            "order_create": order_create_response
        }
    
    async def test_05_error_handling_missing_fields(self):
        """Test error handling for missing required fields."""
        logger.info("Testing error handling for missing fields...")
        
        # Test air-shopping with missing fields
        response = await self.client.post(
            f"{self.base_url}/air-shopping",
            json={"tripType": "ONE_WAY"},  # Missing required fields
            headers={"Content-Type": "application/json"}
        )
        self.assertNotEqual(response.status_code, 200)
        response_data = await response.get_json()
        self.assertEqual(response_data["status"], "error")
        
        # Test flight-price with missing fields
        response = await self.client.post(
            f"{self.base_url}/flight-price",
            json={"offer_id": "123"},  # Missing required fields
            headers={"Content-Type": "application/json"}
        )
        self.assertNotEqual(response.status_code, 200)
        response_data = await response.get_json()
        self.assertEqual(response_data["status"], "error")
        
        # Test order-create with missing fields
        response = await self.client.post(
            f"{self.base_url}/order-create",
            json={"passengers": []},  # Missing required fields
            headers={"Content-Type": "application/json"}
        )
        self.assertNotEqual(response.status_code, 200)
        response_data = await response.get_json()
        self.assertEqual(response_data["status"], "error")
        
        logger.info("Error handling tests completed successfully")

async def run_tests():
    """Run the integration tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()
    
    # Add tests in specific order
    test_names = [
        'test_01_air_shopping',
        'test_02_flight_price',
        'test_03_order_create',
        'test_04_complete_flow',
        'test_05_error_handling_missing_fields'
    ]
    
    for test_name in test_names:
        test_suite.addTest(TestVerteilEndpointsIntegration(test_name))
    
    # Create test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Initialize test class
    test_case = TestVerteilEndpointsIntegration()
    await test_case.asyncSetUp()
    
    try:
        # Run tests
        for test in test_suite:
            await getattr(test_case, test._testMethodName)()
    finally:
        # Clean up
        await test_case.asyncTearDown()

if __name__ == "__main__":
    logger.info("Starting Verteil API integration tests")
    asyncio.run(run_tests())
    logger.info("All integration tests completed")
