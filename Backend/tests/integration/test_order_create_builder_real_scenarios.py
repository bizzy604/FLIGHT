"""
Real-World Scenario Tests for OrderCreate Request Builder

Tests builder with realistic VDC-style responses covering:
1. Flight-only bookings
2. Flight + priced ancillaries (pricedInd=true)
3. Flight + unpriced ancillaries (pricedInd=false)
4. Multiple passengers (ADT, CHD, INF)
5. Payment calculations
6. Mixed pricing scenarios

Based on actual VDC API response patterns.
"""

import pytest
from app.builders.order_create import OrderCreateRequestBuilder


class TestOrderCreateBuilderRealScenarios:
    """Real-world scenario tests with VDC-style responses."""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance."""
        return OrderCreateRequestBuilder()
    
    @pytest.fixture
    def real_flight_price_single_pax(self):
        """Real VDC FlightPrice response (LHR→SIN, 1 ADT, INR 116,048)."""
        return {
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": "5YiZCzyv2bHyx3am5-w7Ut0juOuEIRTN6AfZM3w7pa8-26"
                }
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferID": {
                        "value": "1H026Z_6H2QTPKN9LZ3U31LWRIYC9BG73B7",
                        "Owner": "26",
                        "Channel": "NDC"
                    },
                    "OfferPrice": [{
                        "OfferItemID": "1H026Z_6H2QTPKN9LZ3U31LWRIYC9BG73B7-1-1",
                        "RequestedDate": {
                            "PriceDetail": {
                                "BaseAmount": {
                                    "value": 99720,
                                    "Code": "INR"
                                },
                                "Taxes": {
                                    "Total": {
                                        "value": 16328,
                                        "Code": "INR"
                                    }
                                },
                                "TotalAmount": {
                                    "SimpleCurrencyPrice": {
                                        "value": 116048,
                                        "Code": "INR"
                                    }
                                }
                            }
                        },
                        "FareDetail": {
                            "FareComponent": [{
                                "FareBasis": {
                                    "FareBasisCode": {"Code": "E12GBOLPO"},
                                    "RBD": "E"
                                },
                                "refs": ["SEG2"]
                            }]
                        }
                    }],
                    "PricedInd": True
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
                    "FlightSegment": [{
                        "SegmentKey": "SEG2",
                        "Departure": {
                            "AirportCode": {"value": "LHR"},
                            "Date": "2025-05-13",
                            "Time": "09:25",
                            "Terminal": {"Name": "2"}
                        },
                        "Arrival": {
                            "AirportCode": {"value": "SIN"},
                            "Date": "2025-05-14",
                            "Time": "05:30",
                            "Terminal": {"Name": "0"}
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "26"},
                            "FlightNumber": {"value": "305"}
                        },
                        "Equipment": {"AircraftCode": {"value": "77W"}},
                        "ClassOfService": {
                            "Code": {"value": "E"},
                            "MarketingName": {"value": "ECO", "CabinDesignator": "Y"}
                        }
                    }]
                },
                "OriginDestinationList": {
                    "OriginDestination": [{
                        "OriginDestinationID": "OD1",
                        "FlightReferences": {"value": "SEG2"}
                    }]
                },
                "FareList": {},
                "PriceClassList": {}
            }
        }
    
    @pytest.fixture
    def single_adult_passenger(self):
        """Single adult passenger."""
        return [{
            "passenger_type": "ADT",
            "given_name": "JOHN",
            "surname": "DOE",
            "title": "Mr",
            "gender": "Male",
            "date_of_birth": "1992-06-10",
            "email": "john.doe@email.com",
            "phone": "9987655232",
            "phone_country_code": "91",
            "address": {
                "street": ["Infopark Campus"],
                "city": "Cochin",
                "postal_code": "673328",
                "country_code": "IN"
            }
        }]
    
    @pytest.fixture
    def family_passengers(self):
        """Family: 2 ADT, 1 CHD, 1 INF."""
        return [
            {
                "passenger_type": "ADT",
                "given_name": "JOHN",
                "surname": "DOE",
                "title": "Mr",
                "gender": "Male",
                "date_of_birth": "1985-03-15",
                "email": "john@example.com",
                "phone": "1234567890",
                "phone_country_code": "91"
            },
            {
                "passenger_type": "ADT",
                "given_name": "JANE",
                "surname": "DOE",
                "title": "Mrs",
                "gender": "Female",
                "date_of_birth": "1987-07-22",
                "email": "jane@example.com",
                "phone": "9876543210",
                "phone_country_code": "91"
            },
            {
                "passenger_type": "CHD",
                "given_name": "JIMMY",
                "surname": "DOE",
                "title": "Master",
                "gender": "Male",
                "date_of_birth": "2015-05-10"
            },
            {
                "passenger_type": "INF",
                "given_name": "BABY",
                "surname": "DOE",
                "title": "Miss",
                "gender": "Female",
                "date_of_birth": "2024-01-15"
            }
        ]
    
    @pytest.fixture
    def cash_payment(self):
        """Cash payment."""
        return {
            "method": "cash",
            "amount": 116048.0,
            "currency": "INR"
        }
    
    @pytest.fixture
    def credit_card_payment(self):
        """Credit card payment."""
        return {
            "method": "credit_card",
            "card_number": "4111111111111111",
            "card_type": "Credit",
            "card_holder_name": "JOHN DOE",
            "expiry_date": "1226",
            "cvv": "123",
            "amount": 116048.0,
            "currency": "INR"
        }
    
    @pytest.fixture
    def seat_availability_priced(self):
        """SeatAvailability with priced seat (pricedInd=true, free seat)."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "PRICE1-SEG2-44K",
                    "PricedInd": True,
                    "Price": {
                        "Total": {
                            "value": 0,
                            "Code": "INR"
                        }
                    },
                    "Definition": {
                        "Seat": {
                            "Row": {"Number": {"value": "44"}},
                            "Column": "K",
                            "Characteristics": {
                                "Chargeable": "N"
                            }
                        }
                    }
                }]
            }
        }
    
    @pytest.fixture
    def seat_availability_unpriced(self):
        """SeatAvailability with unpriced seat (pricedInd=false)."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "SEAT-SEG1-6F",
                    "PricedInd": False,
                    "Definition": {
                        "Seat": {
                            "Row": {"Number": {"value": "6"}},
                            "Column": "F",
                            "Characteristics": {
                                "Chargeable": "Y"
                            }
                        }
                    }
                }]
            }
        }
    
    @pytest.fixture
    def service_list_priced(self):
        """ServiceList with priced meal (pricedInd=true, free meal)."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "MEAL-SEG2-LFML",
                    "PricedInd": True,
                    "Name": "LOW FAT MEAL",
                    "Price": {
                        "Total": {
                            "value": 0,
                            "Code": "INR"
                        }
                    },
                    "Descriptions": {
                        "Description": [{
                            "Text": "Low fat meal option"
                        }]
                    }
                }]
            }
        }
    
    @pytest.fixture
    def service_list_unpriced(self):
        """ServiceList with unpriced baggage (pricedInd=false)."""
        return {
            "Services": {
                "Service": [{
                    "ObjectKey": "BAG-SEG1-ABAG",
                    "PricedInd": False,
                    "Name": "FIRST ADDITIONAL BAG",
                    "Descriptions": {
                        "Description": [{
                            "Text": "1 ABAG x 23 KG"
                        }]
                    }
                }]
            }
        }
    
    @pytest.fixture
    def ancillary_pricing_seat_1703_bag_4625(self):
        """Ancillary pricing response with seat (INR 1,703) and baggage (INR 4,625).
        
        Uses TotalAmount.SimpleCurrencyPrice per VDC spec (includes all taxes/fees).
        """
        return {
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferPrice": [
                        {
                            "OfferItemID": "SEAT-SEG1-6F",
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {
                                            "value": 1703,
                                            "Code": "INR"
                                        }
                                    }
                                }
                            }
                        },
                        {
                            "OfferItemID": "BAG-SEG1-ABAG",
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {
                                            "value": 4625,
                                            "Code": "INR"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }]
            }
        }
    
    # ==================== SCENARIO 1: Flight Only ==================== #
    
    def test_flight_only_single_passenger(self, builder, real_flight_price_single_pax, 
                                           single_adult_passenger, cash_payment):
        """
        Scenario 1: Flight-only booking with single adult
        - 1 Passenger: ADT
        - No ancillaries  
        - Payment: INR 116,048 (TotalAmount includes base + taxes)
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment
        )
        
        # Validate structure
        assert "Query" in result
        assert "Passengers" in result["Query"]
        assert "OrderItems" in result["Query"]
        assert "DataLists" in result["Query"]
        assert "Payments" in result["Query"]
        
        # Validate passenger
        passengers = result["Query"]["Passengers"]["Passenger"]
        assert len(passengers) == 1
        assert passengers[0]["PTC"]["value"] == "ADT"
        assert passengers[0]["Name"]["Given"][0]["value"] == "JOHN"
        assert passengers[0]["Name"]["Surname"]["value"] == "DOE"
        
        # Validate order items - should have only flight item
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        assert len(offer_items) >= 1  # At least the flight item
        
        # Validate payment amount (now uses TotalAmount which includes taxes)
        payment = result["Query"]["Payments"]["Payment"][0]
        assert payment["Amount"]["value"] == 116048  # TotalAmount (base 99,720 + taxes 16,328)
        assert payment["Amount"]["Code"] == "INR"
    
    def test_flight_only_family_passengers(self, builder, real_flight_price_single_pax, 
                                            family_passengers, cash_payment):
        """
        Scenario 2: Flight-only with family (2 ADT, 1 CHD, 1 INF)
        - Tests multiple passenger types
        - Validates passenger type mapping
        """
        # Update FlightPrice to have 4 passengers
        flight_price = real_flight_price_single_pax.copy()
        flight_price["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"] = [
            {"ObjectKey": "PAX1", "PTC": {"value": "ADT"}},
            {"ObjectKey": "PAX2", "PTC": {"value": "ADT"}},
            {"ObjectKey": "PAX3", "PTC": {"value": "CHD"}},
            {"ObjectKey": "PAX4", "PTC": {"value": "INF"}}
        ]
        
        result = builder.build_request(
            flight_price_response=flight_price,
            passengers=family_passengers,
            payment=cash_payment
        )
        
        # Validate passengers
        passengers = result["Query"]["Passengers"]["Passenger"]
        assert len(passengers) == 4
        
        # Validate passenger types  (builder uses passenger_type field)
        ptc_list = [p["PTC"]["value"] for p in passengers]
        assert ptc_list.count("ADT") == 2
        assert ptc_list.count("CHD") == 1
        assert ptc_list.count("INF") == 1
    
    # ==================== SCENARIO 2: Flight + Priced Ancillaries ==================== #
    
    def test_flight_with_priced_seat(self, builder, real_flight_price_single_pax,
                                      single_adult_passenger, seat_availability_priced, 
                                      cash_payment):
        """
        Scenario 3: Flight + priced seat (pricedInd=true)
        - Free seat (INR 0)
        - Payment amount = flight base only
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            seatavailability_response=seat_availability_priced,
            selected_seats=["PRICE1-SEG2-44K"]
        )
        
        # Validate order items contain seat
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) == 1
        
        # Validate seat details (VDC uses Location, not SeatDefinition)
        seat_item = seat_items[0]["OfferItemType"]["SeatItem"][0]
        seat_location = seat_item.get("Location", {})  # Location, not SeatDefinition
        assert seat_location.get("Row", {}).get("Number", {}).get("value") == "44"
        assert seat_location.get("Column") == "K"
        
        # Seat price should be 0 (free)
        price = seat_item.get("Price", {})
        assert price.get("Total", {}).get("value") == 0
    
    def test_flight_with_priced_service(self, builder, real_flight_price_single_pax,
                                         single_adult_passenger, service_list_priced,
                                         cash_payment):
        """
        Scenario 4: Flight + priced service (pricedInd=true)
        - Free meal (INR 0)
        - Payment amount = flight base only
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            servicelist_response=service_list_priced,
            selected_services=["MEAL-SEG2-LFML"]
        )
        
        # Validate order items contain service
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        service_items = [item for item in offer_items if "OtherItem" in item.get("OfferItemType", {})]
        
        assert len(service_items) == 1
        
        # Service price should be 0 (free) - uses SimpleCurrencyPrice per VDC spec
        service_item = service_items[0]["OfferItemType"]["OtherItem"][0]
        price = service_item.get("Price", {}).get("SimpleCurrencyPrice", {})
        assert price.get("value") == 0
        assert price.get("Code") == "INR"
    
    def test_flight_with_priced_seat_and_service(self, builder, real_flight_price_single_pax,
                                                   single_adult_passenger, seat_availability_priced,
                                                   service_list_priced, cash_payment):
        """
        Scenario 5: Flight + priced seat + priced service
        - Free seat (INR 0) + free meal (INR 0)
        - Both pricedInd=true
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            seatavailability_response=seat_availability_priced,
            servicelist_response=service_list_priced,
            selected_seats=["PRICE1-SEG2-44K"],
            selected_services=["MEAL-SEG2-LFML"]
        )
        
        # Validate both seat and service present
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        service_items = [item for item in offer_items if "OtherItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) == 1
        assert len(service_items) == 1
    
    # ==================== SCENARIO 3: Flight + Unpriced Ancillaries ==================== #
    
    def test_flight_with_unpriced_seat(self, builder, real_flight_price_single_pax,
                                        single_adult_passenger, seat_availability_unpriced,
                                        ancillary_pricing_seat_1703_bag_4625, cash_payment):
        """
        Scenario 6: Flight + unpriced seat (pricedInd=false)
        - Paid seat (INR 1,703)
        - Requires ancillary pricing response
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            seatavailability_response=seat_availability_unpriced,
            selected_seats=["SEAT-SEG1-6F"],
            ancillary_pricing_response=ancillary_pricing_seat_1703_bag_4625
        )
        
        # Validate seat item
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) == 1
        
        # Seat price should be 1703 (from ancillary pricing)
        seat_item = seat_items[0]["OfferItemType"]["SeatItem"][0]
        price = seat_item.get("Price", {})
        assert price.get("Total", {}).get("value") == 1703
    
    def test_flight_with_unpriced_service(self, builder, real_flight_price_single_pax,
                                           single_adult_passenger, service_list_unpriced,
                                           ancillary_pricing_seat_1703_bag_4625, cash_payment):
        """
        Scenario 7: Flight + unpriced service (pricedInd=false)
        - Paid baggage (INR 4,625)
        - Requires ancillary pricing response
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            servicelist_response=service_list_unpriced,
            selected_services=["BAG-SEG1-ABAG"],
            ancillary_pricing_response=ancillary_pricing_seat_1703_bag_4625
        )
        
        # Validate service item
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        service_items = [item for item in offer_items if "OtherItem" in item.get("OfferItemType", {})]
        
        assert len(service_items) == 1
        
        # Service price should be 4625 (from ancillary pricing) - uses SimpleCurrencyPrice
        service_item = service_items[0]["OfferItemType"]["OtherItem"][0]
        price = service_item.get("Price", {}).get("SimpleCurrencyPrice", {})
        assert price.get("value") == 4625
        assert price.get("Code") == "INR"
    
    def test_flight_with_unpriced_seat_and_service(self, builder, real_flight_price_single_pax,
                                                     single_adult_passenger, seat_availability_unpriced,
                                                     service_list_unpriced, 
                                                     ancillary_pricing_seat_1703_bag_4625, cash_payment):
        """
        Scenario 8: Flight + unpriced seat + unpriced service
        - Paid seat (INR 1,703) + paid baggage (INR 4,625)
        - Total ancillaries: INR 6,328
        - Tests mixed unpriced ancillaries
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            seatavailability_response=seat_availability_unpriced,
            servicelist_response=service_list_unpriced,
            selected_seats=["SEAT-SEG1-6F"],
            selected_services=["BAG-SEG1-ABAG"],
            ancillary_pricing_response=ancillary_pricing_seat_1703_bag_4625
        )
        
        # Validate both seat and service with correct prices
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        service_items = [item for item in offer_items if "OtherItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) == 1
        assert len(service_items) == 1
        
        # Validate prices (seat uses Total, service uses SimpleCurrencyPrice per VDC spec)
        seat_price = seat_items[0]["OfferItemType"]["SeatItem"][0]["Price"]["Total"]["value"]
        service_price = service_items[0]["OfferItemType"]["OtherItem"][0]["Price"]["SimpleCurrencyPrice"]["value"]
        
        assert seat_price == 1703
        assert service_price == 4625
    
    # ==================== SCENARIO 4: Payment Methods ==================== #
    
    def test_payment_method_credit_card(self, builder, real_flight_price_single_pax,
                                         single_adult_passenger, credit_card_payment):
        """
        Scenario 9: Credit card payment method
        - Tests payment structure with card details
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=credit_card_payment
        )
        
        # Validate payment structure
        payment = result["Query"]["Payments"]["Payment"][0]
        assert "PaymentCard" in payment["Method"]
        
        payment_card = payment["Method"]["PaymentCard"]
        assert payment_card["CardNumber"] == "4111111111111111"
        assert payment_card["CardType"]["value"] == "Credit"
        assert payment_card["CardHolderName"] == "JOHN DOE"
        assert payment_card["ExpiryDate"] == "1226"
        assert payment_card["SeriesCode"] == "123"
    
    # ==================== SCENARIO 5: Mixed Pricing ==================== #
    
    def test_mixed_priced_and_unpriced_ancillaries(self, builder, real_flight_price_single_pax,
                                                     single_adult_passenger, seat_availability_priced,
                                                     service_list_unpriced,
                                                     ancillary_pricing_seat_1703_bag_4625, cash_payment):
        """
        Scenario 10: Mixed pricing - priced seat (free) + unpriced service (paid)
        - Free seat (INR 0, pricedInd=true)
        - Paid baggage (INR 4,625, pricedInd=false)
        - Tests mixed pricing scenario
        """
        result = builder.build_request(
            flight_price_response=real_flight_price_single_pax,
            passengers=single_adult_passenger,
            payment=cash_payment,
            seatavailability_response=seat_availability_priced,
            servicelist_response=service_list_unpriced,
            selected_seats=["PRICE1-SEG2-44K"],
            selected_services=["BAG-SEG1-ABAG"],
            ancillary_pricing_response=ancillary_pricing_seat_1703_bag_4625
        )
        
        # Validate both ancillaries present
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        service_items = [item for item in offer_items if "OtherItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) == 1
        assert len(service_items) == 1
        
        # Validate prices: seat free (uses Total), service paid (uses SimpleCurrencyPrice)
        seat_price = seat_items[0]["OfferItemType"]["SeatItem"][0]["Price"]["Total"]["value"]
        service_price = service_items[0]["OfferItemType"]["OtherItem"][0]["Price"]["SimpleCurrencyPrice"]["value"]
        
        assert seat_price == 0  # Free priced seat
        assert service_price == 4625  # Paid unpriced service


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
