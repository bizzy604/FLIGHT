"""
Unit tests for OrderCreate Request Builder

Tests all methods and pricing scenarios (pricedInd=true/false/mixed).
"""

import pytest
import sys
from pathlib import Path

# Add Backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.builders.order_create import OrderCreateRequestBuilder, normalize_to_list


class TestNormalizeToList:
    """Test the normalize_to_list utility function."""
    
    def test_normalize_dict_to_list(self):
        """Should convert dict to list."""
        result = normalize_to_list({"key": "value"})
        assert result == [{"key": "value"}]
    
    def test_normalize_list_unchanged(self):
        """Should keep list unchanged."""
        data = [1, 2, 3]
        result = normalize_to_list(data)
        assert result == [1, 2, 3]
    
    def test_normalize_none_to_empty_list(self):
        """Should convert None to empty list."""
        result = normalize_to_list(None)
        assert result == []
    
    def test_normalize_empty_string_to_empty_list(self):
        """Should convert empty string to empty list."""
        result = normalize_to_list("")
        assert result == []
    
    def test_normalize_single_value_to_list(self):
        """Should wrap single value in list."""
        result = normalize_to_list("test")
        assert result == ["test"]


class TestOrderCreateRequestBuilder:
    """Test OrderCreateRequestBuilder class."""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance."""
        return OrderCreateRequestBuilder()
    
    @pytest.fixture
    def sample_flight_price_response(self):
        """Sample FlightPrice response.
        
        Uses TotalAmount.SimpleCurrencyPrice (VDC spec for total price including taxes/fees).
        """
        return {
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": "test-shopping-response-123"
                }
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferID": {
                        "value": "offer-123",
                        "Owner": "AF",
                        "Channel": "NDC"
                    },
                    "OfferPrice": [{
                        "OfferItemID": "offer-item-1",
                        "RequestedDate": {
                            "PriceDetail": {
                                "BaseAmount": {
                                    "value": 450,
                                    "Code": "USD"
                                },
                                "Taxes": {
                                    "Total": {
                                        "value": 50,
                                        "Code": "USD"
                                    }
                                },
                                "TotalAmount": {
                                    "SimpleCurrencyPrice": {
                                        "value": 500,
                                        "Code": "USD"
                                    }
                                }
                            }
                        },
                        "FareDetail": {}
                    }]
                }]
            },
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [{
                        "ObjectKey": "PAX1",
                        "PTC": {"value": "ADT"}
                    }]
                },
                "FlightSegmentList": {
                    "FlightSegment": []
                },
                "FlightList": {
                    "Flight": []
                },
                "OriginDestinationList": {
                    "OriginDestination": [{
                        "FlightReferences": {"value": ["FL1"]}
                    }]
                },
                "FareList": {},
                "PriceClassList": {}
            }
        }
    
    @pytest.fixture
    def sample_passengers(self):
        """Sample passenger data."""
        return [{
            "given_name": "John",
            "surname": "Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "gender": "Male",
            "dob": "1990-01-01",
            "passenger_type": "ADT",
            "title": "Mr",
            "country_code": "1"
        }]
    
    @pytest.fixture
    def sample_payment(self):
        """Sample payment data."""
        return {
            "card_number": "4111111111111111",
            "card_type": "Credit",
            "card_holder_name": "John Doe",
            "expiry_date": "12/25",
            "cvv": "123"
        }
    
    @pytest.fixture
    def sample_seatavailability_priced(self):
        """Sample SeatAvailability with pricedInd=true."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "SEAT-SEG1-12A",
                    "PricedInd": True,
                    "Price": {
                        "Total": {
                            "value": 50,
                            "Code": "USD"
                        }
                    },
                    "Definition": {
                        "Seat": {
                            "Row": {"Number": {"value": "12"}},
                            "Column": "A",
                            "Characteristics": {}
                        }
                    }
                }]
            }
        }
    
    @pytest.fixture
    def sample_seatavailability_unpriced(self):
        """Sample SeatAvailability with pricedInd=false."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "SEAT-SEG1-12A",
                    "PricedInd": False,
                    "Definition": {
                        "Seat": {
                            "Row": {"Number": {"value": "12"}},
                            "Column": "A",
                            "Characteristics": {}
                        }
                    }
                }]
            }
        }
    
    @pytest.fixture
    def sample_servicelist_priced(self):
        """Sample ServiceList with pricedInd=true."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "MEAL-SEG1-HOT",
                    "PricedInd": True,
                    "Name": "Hot Meal",
                    "Price": {
                        "Total": {
                            "value": 25,
                            "Code": "USD"
                        }
                    },
                    "Descriptions": {
                        "Description": [{
                            "Text": "Delicious hot meal"
                        }]
                    }
                }]
            }
        }
    
    @pytest.fixture
    def sample_ancillary_pricing_response(self):
        """Sample ancillary pricing FlightPrice response.
        
        Uses TotalAmount.SimpleCurrencyPrice per VDC spec (includes all taxes/fees/discounts).
        """
        return {
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferPrice": [
                        {
                            "OfferItemID": "offer-item-1",
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {"value": 500, "Code": "USD"}
                                    }
                                }
                            }
                        },
                        {
                            "OfferItemID": "SEAT-SEG1-12A",
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {"value": 50, "Code": "USD"}
                                    }
                                }
                            }
                        }
                    ]
                }]
            }
        }
    
    def test_detect_pricing_scenario_priced_ind_true(self, builder, sample_seatavailability_priced):
        """Test detection of pricedInd=true scenario."""
        result = builder._detect_pricing_scenario(
            seatavailability_response=sample_seatavailability_priced,
            selected_seats=["SEAT-SEG1-12A"]
        )
        
        assert result["scenario"] == "priced_ind_true"
        assert "SEAT-SEG1-12A" in result["seats_priced"]
        assert len(result["seats_unpriced"]) == 0
    
    def test_detect_pricing_scenario_priced_ind_false(self, builder, sample_seatavailability_unpriced):
        """Test detection of pricedInd=false scenario."""
        result = builder._detect_pricing_scenario(
            seatavailability_response=sample_seatavailability_unpriced,
            selected_seats=["SEAT-SEG1-12A"]
        )
        
        assert result["scenario"] == "priced_ind_false"
        assert "SEAT-SEG1-12A" in result["seats_unpriced"]
        assert len(result["seats_priced"]) == 0
    
    def test_detect_pricing_scenario_mixed(self, builder, sample_seatavailability_priced, sample_servicelist_priced):
        """Test detection of mixed scenario."""
        # Modify servicelist to have unpriced item
        servicelist_mixed = {
            "Services": {
                "Service": [
                    sample_servicelist_priced["Services"]["Service"][0],
                    {
                        "ObjectKey": "MEAL-SEG1-COLD",
                        "PricedInd": False,
                        "Name": "Cold Meal"
                    }
                ]
            }
        }
        
        result = builder._detect_pricing_scenario(
            seatavailability_response=sample_seatavailability_priced,
            servicelist_response=servicelist_mixed,
            selected_seats=["SEAT-SEG1-12A"],
            selected_services=["MEAL-SEG1-HOT", "MEAL-SEG1-COLD"]
        )
        
        assert result["scenario"] == "mixed"
        assert len(result["seats_priced"]) > 0
        assert len(result["services_unpriced"]) > 0
    
    def test_extract_selected_offer(self, builder, sample_flight_price_response):
        """Test extraction of selected offer."""
        offer = builder._extract_selected_offer(sample_flight_price_response)
        
        assert offer is not None
        assert offer["OfferID"]["value"] == "offer-123"
        assert offer["OfferID"]["Owner"] == "AF"
    
    def test_extract_selected_offer_no_offers(self, builder):
        """Test extraction when no offers exist."""
        response = {"PricedFlightOffers": {}}
        
        with pytest.raises(ValueError, match="No PricedFlightOffer found"):
            builder._extract_selected_offer(response)
    
    def test_build_passengers(self, builder, sample_passengers, sample_flight_price_response):
        """Test building passengers section."""
        result = builder._build_passengers(sample_passengers, sample_flight_price_response)
        
        assert len(result) == 1
        assert result[0]["ObjectKey"] == "PAX1"
        assert result[0]["Name"]["Given"][0]["value"] == "John"
        assert result[0]["Name"]["Surname"]["value"] == "Doe"
        assert result[0]["Gender"]["value"] == "Male"
        assert result[0]["AdditionalRoles"]["PaymentContactInd"] is True
    
    def test_build_passengers_multiple(self, builder, sample_flight_price_response):
        """Test building multiple passengers."""
        # Add second traveler
        sample_flight_price_response["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"].append({
            "ObjectKey": "PAX2",
            "PTC": {"value": "ADT"}
        })
        
        passengers = [
            {"given_name": "John", "surname": "Doe", "email": "john@test.com", "phone": "123", "gender": "Male"},
            {"given_name": "Jane", "surname": "Smith", "email": "jane@test.com", "phone": "456", "gender": "Female"}
        ]
        
        result = builder._build_passengers(passengers, sample_flight_price_response)
        
        assert len(result) == 2
        assert result[0]["ObjectKey"] == "PAX1"
        assert result[1]["ObjectKey"] == "PAX2"
        assert result[0]["AdditionalRoles"]["PaymentContactInd"] is True
        assert "AdditionalRoles" not in result[1]
    
    def test_build_shopping_response(self, builder, sample_flight_price_response):
        """Test building ShoppingResponse structure."""
        selected_offer = builder._extract_selected_offer(sample_flight_price_response)
        result = builder._build_shopping_response(sample_flight_price_response, selected_offer)
        
        assert result["Owner"] == "AF"
        assert result["ResponseID"]["value"] == "test-shopping-response-123"
        assert len(result["Offers"]["Offer"]) == 1
        assert result["Offers"]["Offer"][0]["OfferID"]["value"] == "offer-123"
    
    def test_build_flight_offer_item(self, builder, sample_flight_price_response, sample_passengers):
        """Test building flight offer item."""
        selected_offer = builder._extract_selected_offer(sample_flight_price_response)
        result = builder._build_flight_offer_item(
            selected_offer,
            sample_flight_price_response,
            sample_passengers
        )
        
        assert result["OfferItemID"]["value"] == "offer-item-1"
        assert result["OfferItemID"]["Owner"] == "AF"
        assert "DetailedFlightItem" in result["OfferItemType"]
        assert result["OfferItemType"]["DetailedFlightItem"][0]["refs"] == ["PAX1"]
    
    def test_extract_price_from_service(self, builder, sample_seatavailability_priced):
        """Test extracting price from service (pricedInd=true).
        
        Should return Total (includes all taxes/fees/discounts).
        """
        service = sample_seatavailability_priced["Services"]["Service"][0]
        result = builder._extract_price_from_service(service)
        
        assert result["Total"]["value"] == 50
        assert result["Total"]["Code"] == "USD"
    
    def test_extract_price_from_pricing_response(self, builder, sample_ancillary_pricing_response):
        """Test extracting price from ancillary pricing response (pricedInd=false).
        
        Should extract TotalAmount.SimpleCurrencyPrice and return as Total.
        """
        result = builder._extract_price_from_pricing_response(
            sample_ancillary_pricing_response,
            "SEAT-SEG1-12A"
        )
        
        assert result["Total"]["value"] == 50
        assert result["Total"]["Code"] == "USD"
    
    def test_extract_price_from_pricing_response_not_found(self, builder, sample_ancillary_pricing_response):
        """Test extracting price when item not found (should return zero Total)."""
        result = builder._extract_price_from_pricing_response(
            sample_ancillary_pricing_response,
            "NON-EXISTENT-ITEM"
        )
        
        assert result["Total"]["value"] == 0
    
    def test_extract_seat_definition(self, builder, sample_seatavailability_priced):
        """Test extracting seat definition."""
        service = sample_seatavailability_priced["Services"]["Service"][0]
        result = builder._extract_seat_definition(service)
        
        assert result["Row"]["Number"]["value"] == "12"
        assert result["Column"] == "A"
    
    def test_build_payments(self, builder, sample_payment, sample_flight_price_response):
        """Test building payments section."""
        result = builder._build_payments(
            sample_payment,
            sample_flight_price_response,
            None
        )
        
        assert len(result) == 1
        assert result[0]["Method"]["PaymentCard"]["CardNumber"] == "4111111111111111"
        assert result[0]["Amount"]["value"] == 500
        assert result[0]["Amount"]["Code"] == "USD"
    
    def test_build_request_flight_only(
        self,
        builder,
        sample_flight_price_response,
        sample_passengers,
        sample_payment
    ):
        """Test building OrderCreate request for flight only (no ancillaries)."""
        result = builder.build_request(
            flight_price_response=sample_flight_price_response,
            passengers=sample_passengers,
            payment=sample_payment
        )
        
        # Validate structure
        assert "Query" in result
        assert "Passengers" in result["Query"]
        assert "OrderItems" in result["Query"]
        assert "DataLists" in result["Query"]
        assert "Payments" in result["Query"]
        
        # Check passengers
        assert len(result["Query"]["Passengers"]["Passenger"]) == 1
        
        # Check order items (should have 1 flight item only)
        assert len(result["Query"]["OrderItems"]["OfferItem"]) == 1
    
    def test_build_request_with_priced_seats(
        self,
        builder,
        sample_flight_price_response,
        sample_passengers,
        sample_payment,
        sample_seatavailability_priced
    ):
        """Test building OrderCreate request with pricedInd=true seats."""
        result = builder.build_request(
            flight_price_response=sample_flight_price_response,
            passengers=sample_passengers,
            payment=sample_payment,
            seatavailability_response=sample_seatavailability_priced,
            selected_seats=["SEAT-SEG1-12A"]
        )
        
        # Should have 2 offer items: flight + seat
        assert len(result["Query"]["OrderItems"]["OfferItem"]) == 2
        
        # Second item should be seat
        seat_item = result["Query"]["OrderItems"]["OfferItem"][1]
        assert "SeatItem" in seat_item["OfferItemType"]
    
    def test_build_request_with_unpriced_seats_no_pricing_response(
        self,
        builder,
        sample_flight_price_response,
        sample_passengers,
        sample_payment,
        sample_seatavailability_unpriced
    ):
        """Test building request with unpriced seats but no pricing response (should fail)."""
        with pytest.raises(ValueError, match="requires pricing"):
            builder.build_request(
                flight_price_response=sample_flight_price_response,
                passengers=sample_passengers,
                payment=sample_payment,
                seatavailability_response=sample_seatavailability_unpriced,
                selected_seats=["SEAT-SEG1-12A"]
            )
    
    def test_build_request_with_unpriced_seats_with_pricing_response(
        self,
        builder,
        sample_flight_price_response,
        sample_passengers,
        sample_payment,
        sample_seatavailability_unpriced,
        sample_ancillary_pricing_response
    ):
        """Test building request with unpriced seats and pricing response.
        
        Should use TotalAmount from pricing response (50 USD).
        """
        result = builder.build_request(
            flight_price_response=sample_flight_price_response,
            passengers=sample_passengers,
            payment=sample_payment,
            seatavailability_response=sample_seatavailability_unpriced,
            selected_seats=["SEAT-SEG1-12A"],
            ancillary_pricing_response=sample_ancillary_pricing_response
        )
        
        # Should have 2 offer items: flight + seat
        assert len(result["Query"]["OrderItems"]["OfferItem"]) == 2
        
        # Seat price should come from ancillary pricing response (TotalAmount)
        seat_item = result["Query"]["OrderItems"]["OfferItem"][1]
        assert seat_item["OfferItemType"]["SeatItem"][0]["Price"]["Total"]["value"] == 50
    
    def test_validate_request_missing_passengers(self, builder):
        """Test validation fails when passengers missing."""
        request = {"Query": {}}
        
        with pytest.raises(ValueError, match="Passengers section is required"):
            builder._validate_request(request)
    
    def test_validate_request_missing_order_items(self, builder):
        """Test validation fails when OrderItems missing."""
        request = {
            "Query": {
                "Passengers": {"Passenger": []}
            }
        }
        
        with pytest.raises(ValueError, match="OrderItems section is required"):
            builder._validate_request(request)
    
    def test_validate_request_success(self, builder):
        """Test validation passes with complete request."""
        request = {
            "Query": {
                "Passengers": {"Passenger": [{}]},
                "OrderItems": {
                    "ShoppingResponse": {
                        "Owner": "AF",
                        "Offers": {"Offer": [{}]}
                    },
                    "OfferItem": [{}]
                },
                "DataLists": {
                    "AnonymousTravelerList": {},
                    "FlightSegmentList": {}
                },
                "Payments": {"Payment": [{}]}
            }
        }
        
        # Should not raise
        builder._validate_request(request)
