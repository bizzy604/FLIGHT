"""
Unit tests for OrderCreate Transformer

Tests response transformation, data extraction, and error handling.
"""

import pytest
import sys
from pathlib import Path

# Add Backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.transformers.order_create import OrderCreateTransformer


class TestOrderCreateTransformer:
    """Test OrderCreateTransformer class."""
    
    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return OrderCreateTransformer()
    
    @pytest.fixture
    def sample_vdc_response(self):
        """Sample VDC OrderCreateRS response."""
        return {
            "OrderCreateRS": {
                "Order": {
                    "OrderID": {"value": "ORDER-123"},
                    "BookingReference": {
                        "ID": {"value": "BOOKING-ABC123"}
                    },
                    "TotalPrice": {
                        "Total": {"value": 550.00, "Code": "USD"},
                        "BaseAmount": {"value": 500.00, "Code": "USD"},
                        "Taxes": {
                            "Total": {"value": 50.00, "Code": "USD"}
                        }
                    },
                    "Passengers": {
                        "Passenger": [{
                            "ObjectKey": "PAX1",
                            "Name": {
                                "Given": [{"value": "John"}],
                                "Surname": {"value": "Doe"}
                            },
                            "PTC": {"value": "ADT"}
                        }]
                    },
                    "DataLists": {
                        "FlightSegmentList": {
                            "FlightSegment": [{
                                "SegmentKey": "SEG1",
                                "Departure": {
                                    "AirportCode": {"value": "JFK"},
                                    "Date": "2025-11-01T10:00:00"
                                },
                                "Arrival": {
                                    "AirportCode": {"value": "LAX"},
                                    "Date": "2025-11-01T13:00:00"
                                },
                                "OperatingCarrier": {
                                    "AirlineID": {"value": "AA"}
                                },
                                "MarketingCarrier": {
                                    "FlightNumber": {"value": "100"}
                                }
                            }]
                        }
                    },
                    "OrderItems": {
                        "OrderItem": [
                            {
                                "OrderItemID": {"value": "ITEM1"},
                                "PassengerReferences": {"value": "PAX1"},
                                "OfferItemType": {
                                    "DetailedFlightItem": {}
                                }
                            },
                            {
                                "OrderItemID": {"value": "ITEM2"},
                                "PassengerReferences": {"value": "PAX1"},
                                "OfferItemType": {
                                    "SeatItem": [{
                                        "SeatReference": {
                                            "Row": {"Number": {"value": "12"}},
                                            "Column": "A"
                                        },
                                        "SegmentRef": "SEG1"
                                    }]
                                },
                                "Price": {
                                    "Total": {"value": 50.00, "Code": "USD"}
                                }
                            }
                        ]
                    }
                }
            }
        }
    
    def test_transform_success(self, transformer, sample_vdc_response):
        """Test successful transformation of VDC response."""
        result = transformer.transform(sample_vdc_response)
        
        assert result["success"] is True
        assert result["booking_reference"] == "BOOKING-ABC123"
        assert result["order_id"] == "ORDER-123"
        assert "raw_response" in result
    
    def test_extract_order_format1(self, transformer, sample_vdc_response):
        """Test extracting Order from OrderCreateRS.Order format."""
        order = transformer._extract_order(sample_vdc_response)
        
        assert order is not None
        assert "OrderID" in order
        assert order["OrderID"]["value"] == "ORDER-123"
    
    def test_extract_order_format2(self, transformer):
        """Test extracting Order from root level."""
        response = {
            "Order": {
                "OrderID": {"value": "ORDER-456"}
            }
        }
        
        order = transformer._extract_order(response)
        
        assert order is not None
        assert order["OrderID"]["value"] == "ORDER-456"
    
    def test_extract_order_missing(self, transformer):
        """Test extracting Order when not present."""
        response = {"SomeField": "SomeValue"}
        
        order = transformer._extract_order(response)
        
        assert order is None
    
    def test_extract_booking_reference(self, transformer):
        """Test extracting booking reference."""
        order = {
            "BookingReference": {
                "ID": {"value": "BOOKING-XYZ"}
            }
        }
        
        result = transformer._extract_booking_reference(order)
        
        assert result == "BOOKING-XYZ"
    
    def test_extract_booking_reference_missing(self, transformer):
        """Test extracting booking reference when missing."""
        order = {}
        
        result = transformer._extract_booking_reference(order)
        
        assert result == "UNKNOWN"
    
    def test_extract_order_id(self, transformer):
        """Test extracting order ID."""
        order = {
            "OrderID": {"value": "ORDER-789"}
        }
        
        result = transformer._extract_order_id(order)
        
        assert result == "ORDER-789"
    
    def test_extract_order_id_missing(self, transformer):
        """Test extracting order ID when missing."""
        order = {}
        
        result = transformer._extract_order_id(order)
        
        assert result == "UNKNOWN"
    
    def test_extract_total_price(self, transformer):
        """Test extracting total price information."""
        order = {
            "TotalPrice": {
                "Total": {"value": 600.00, "Code": "EUR"},
                "BaseAmount": {"value": 550.00, "Code": "EUR"},
                "Taxes": {
                    "Total": {"value": 50.00, "Code": "EUR"}
                }
            }
        }
        
        result = transformer._extract_total_price(order)
        
        assert result["amount"] == 600.00
        assert result["currency"] == "EUR"
        assert result["base_amount"] == 550.00
        assert result["taxes"] == 50.00
    
    def test_extract_total_price_missing(self, transformer):
        """Test extracting price when missing (returns defaults)."""
        order = {}
        
        result = transformer._extract_total_price(order)
        
        assert result["amount"] == 0.0
        assert result["currency"] == "USD"
    
    def test_extract_passengers(self, transformer):
        """Test extracting passenger information."""
        vdc_response = {
            "Passengers": {
                "Passenger": [{
                    "ObjectKey": "PAX1",
                    "Name": {
                        "Given": [{"value": "Jane"}],
                        "Surname": {"value": "Smith"}
                    },
                    "PTC": {"value": "ADT"}
                }]
            }
        }
        
        order = {}  # Order can be empty for passenger extraction
        
        result = transformer._extract_passengers(vdc_response, order)
        
        assert len(result) == 1
        assert result[0]["passenger_id"] == "PAX1"
        assert result[0]["name"] == "Jane Smith"
        assert result[0]["type"] == "ADT"
    
    def test_extract_passengers_multiple(self, transformer):
        """Test extracting multiple passengers."""
        vdc_response = {
            "Passengers": {
                "Passenger": [
                    {
                        "ObjectKey": "PAX1",
                        "Name": {
                            "Given": [{"value": "John"}],
                            "Surname": {"value": "Doe"}
                        },
                        "PTC": {"value": "ADT"}
                    },
                    {
                        "ObjectKey": "PAX2",
                        "Name": {
                            "Given": [{"value": "Jane"}],
                            "Surname": {"value": "Doe"}
                        },
                        "PTC": {"value": "CHD"}
                    }
                ]
            }
        }
        
        order = {}  # Order can be empty
        
        result = transformer._extract_passengers(vdc_response, order)
        
        assert len(result) == 2
        assert result[0]["name"] == "John Doe"
        assert result[1]["name"] == "Jane Doe"
        assert result[1]["type"] == "CHD"
    
    def test_extract_passenger_name(self, transformer):
        """Test extracting passenger name."""
        passenger = {
            "Name": {
                "Given": [{"value": "Alice"}],
                "Surname": {"value": "Johnson"}
            }
        }
        
        result = transformer._extract_passenger_name(passenger)
        
        assert result == "Alice Johnson"
    
    def test_extract_passenger_name_missing(self, transformer):
        """Test extracting name when missing."""
        passenger = {}
        
        result = transformer._extract_passenger_name(passenger)
        
        assert result == "Unknown"
    
    def test_extract_flights(self, transformer):
        """Test extracting flight information."""
        vdc_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": [{
                        "SegmentKey": "SEG1",
                        "Departure": {
                            "AirportCode": {"value": "ORD"},
                            "Date": "2025-11-15T08:00:00",
                            "Time": "08:00:00"
                        },
                        "Arrival": {
                            "AirportCode": {"value": "SFO"},
                            "Date": "2025-11-15T11:00:00",
                            "Time": "11:00:00"
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "UA"},
                            "FlightNumber": {"value": "200"}
                        }
                    }]
                }
            }
        }
        
        result = transformer._extract_flights(vdc_response)
        
        assert len(result) == 1
        assert result[0]["origin"] == "ORD"
        assert result[0]["destination"] == "SFO"
        assert result[0]["carrier"] == "UA"
        assert result[0]["flight_number"] == "200"
    
    def test_extract_ancillaries_seats(self, transformer):
        """Test extracting seat ancillaries."""
        order = {
            "OrderItems": {
                "OrderItem": [{
                    "OrderItemID": {"value": "ITEM1"},
                    "PassengerReferences": {"value": "PAX1"},
                    "OfferItemType": {
                        "SeatItem": [{
                            "SeatReference": {
                                "Row": {"Number": {"value": "15"}},
                                "Column": "C"
                            },
                            "SegmentRef": "SEG1"
                        }]
                    },
                    "Price": {
                        "Total": {"value": 75.00, "Code": "USD"}
                    }
                }]
            }
        }
        
        result = transformer._extract_ancillaries(order)
        
        assert len(result["seats"]) == 1
        assert result["seats"][0]["seat_number"] == "15C"
        assert result["seats"][0]["price"]["amount"] == 75.00
    
    def test_extract_ancillaries_services(self, transformer):
        """Test extracting service ancillaries."""
        order = {
            "OrderItems": {
                "OrderItem": [{
                    "OrderItemID": {"value": "ITEM1"},
                    "PassengerReferences": {"value": "PAX1"},
                    "OfferItemType": {
                        "ServiceItem": [{
                            "ServiceDefinitionRef": "MEAL-HOT",
                            "Name": "Hot Meal"
                        }]
                    },
                    "Price": {
                        "Total": {"value": 25.00, "Code": "USD"}
                    }
                }]
            }
        }
        
        result = transformer._extract_ancillaries(order)
        
        assert len(result["services"]) == 1
        assert result["services"][0]["service_code"] == "MEAL-HOT"
        assert result["services"][0]["name"] == "Hot Meal"
    
    def test_extract_seat_number(self, transformer):
        """Test extracting seat number from SeatItem."""
        seat_item = {
            "SeatReference": {
                "Row": {"Number": {"value": "22"}},
                "Column": "F"
            }
        }
        
        result = transformer._extract_seat_number(seat_item)
        
        assert result == "22F"
    
    def test_extract_seat_number_missing(self, transformer):
        """Test extracting seat number when missing."""
        seat_item = {}
        
        result = transformer._extract_seat_number(seat_item)
        
        assert result == "UNKNOWN"
    
    def test_transform_no_order(self, transformer):
        """Test transformation when Order is missing."""
        response = {"SomeField": "SomeValue"}
        
        result = transformer.transform(response)
        
        assert result["success"] is False
        assert "error" in result
        assert result["raw_response"] == response
    
    def test_transform_error_handling(self, transformer):
        """Test transformation handles errors gracefully."""
        # Invalid response that will cause extraction errors
        response = {
            "OrderCreateRS": {
                "Order": {
                    "TotalPrice": "invalid"  # Invalid structure
                }
            }
        }
        
        result = transformer.transform(response)
        
        # Should still return success with defaults
        assert result["success"] is True
        assert "raw_response" in result
