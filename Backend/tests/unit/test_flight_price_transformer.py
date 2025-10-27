"""Tests for FlightPrice response transformer."""

import pytest
from app.transformers.flight_price import FlightPriceTransformer


@pytest.fixture
def sample_flight_price_response():
    """Sample FlightPrice response for testing."""
    return {
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": {"value": "PRICE_OFFER_123", "Owner": "EK"},
                    "OfferPrice": [
                        {
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "DetailCurrencyPrice": {
                                            "Total": {"value": 1500.00},
                                            "Taxes": {
                                                "Total": {"value": 300.00},
                                                "Breakdown": {
                                                    "Tax": [
                                                        {"TaxCode": "YQ", "Amount": {"value": 150.00}},
                                                        {"TaxCode": "YR", "Amount": {"value": 150.00}}
                                                    ]
                                                }
                                            }
                                        },
                                        "BaseAmount": {"value": 1200.00},
                                        "SimpleCurrencyPrice": {"value": 1500.00}
                                    }
                                }
                            },
                            "FareDetail": {
                                "FareComponent": [
                                    {
                                        "CabinType": {"CabinTypeName": "Economy"},
                                        "FareBasis": {"FareBasisCode": {"Code": "YLOW"}},
                                        "FareRules": {
                                            "Penalty": {
                                                "Details": "Non-refundable. Change fee: 100 USD",
                                                "CancelFeeInd": True,
                                                "ChangeFeeInd": True,
                                                "CancelFee": {
                                                    "Amount": {"value": 200.00},
                                                    "Application": "Before Departure"
                                                },
                                                "ChangeFee": {
                                                    "Amount": {"value": 100.00},
                                                    "Application": "Anytime"
                                                }
                                            }
                                        },
                                        "ClassOfService": {"Code": "Y", "MarketingName": "Economy Flex"}
                                    }
                                ]
                            }
                        },
                        {
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "DetailCurrencyPrice": {
                                            "Total": {"value": 750.00},
                                            "Taxes": {
                                                "Total": {"value": 150.00},
                                                "Breakdown": {
                                                    "Tax": [
                                                        {"TaxCode": "YQ", "Amount": {"value": 75.00}},
                                                        {"TaxCode": "YR", "Amount": {"value": 75.00}}
                                                    ]
                                                }
                                            }
                                        },
                                        "BaseAmount": {"value": 600.00}
                                    }
                                }
                            }
                        }
                    ],
                    "BaggageAllowance": [
                        {
                            "BaggageAllowanceRef": "BAG1",
                            "PieceAllowance": {
                                "TotalQuantity": 2,
                                "PieceMeasurements": {
                                    "Weight": {"value": 23, "UOM": "KG"}
                                }
                            },
                            "TypeCode": "Checked",
                            "PassengerType": "ADT"
                        },
                        {
                            "BaggageAllowanceRef": "BAG2",
                            "PieceAllowance": {
                                "TotalQuantity": 1,
                                "PieceMeasurements": {
                                    "Weight": {"value": 7, "UOM": "KG"}
                                }
                            },
                            "TypeCode": "CarryOn",
                            "PassengerType": "ADT"
                        }
                    ],
                    "FlightSegment": [
                        {
                            "SegmentKey": "SEG1",
                            "Departure": {
                                "AirportCode": {"value": "DXB"},
                                "Date": "2025-12-01",
                                "Time": "14:30"
                            },
                            "Arrival": {
                                "AirportCode": {"value": "LHR"},
                                "Date": "2025-12-01",
                                "Time": "18:45"
                            },
                            "MarketingCarrier": {
                                "AirlineID": {"value": "EK"},
                                "FlightNumber": {"value": "001"}
                            },
                            "refs": ["SERVICE1", "SERVICE2"]
                        }
                    ]
                }
            ]
        },
        "PaymentFunctions": {
            "PaymentProcessingDetails": {
                "Amount": {
                    "DetailCurrencyPrice": {
                        "Total": {"value": 1500.00},
                        "Taxes": {"Total": {"value": 300.00}}
                    }
                }
            }
        },
        "Metadata": {
            "CurrencyMetadata": [
                {
                    "MetadataKey": "CUR1",
                    "Decimals": 2,
                    "Application": {
                        "CurrencyCode": "USD"
                    }
                }
            ]
        }
    }


@pytest.fixture
def minimal_flight_price_response():
    """Minimal FlightPrice response with only required fields."""
    return {
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": {"value": "MIN_OFFER", "Owner": "EK"},
                    "OfferPrice": [
                        {
                            "RequestedDate": {
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {"value": 1000.00}
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }


class TestFlightPriceTransformer:
    """Test FlightPrice response transformer."""
    
    def test_transform_valid_response(self, sample_flight_price_response):
        """Should transform valid FlightPrice response."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        
        # Verify main structure
        assert "offer_id" in result
        assert "pricing" in result
        assert "breakdown" in result
        assert "fare_details" in result
        assert "penalties" in result
        assert "baggage" in result
        assert "segments" in result
        assert "metadata" in result
    
    def test_extract_offer_id(self, sample_flight_price_response):
        """Should extract offer ID correctly."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        
        assert result["offer_id"] == "PRICE_OFFER_123"
    
    def test_extract_pricing(self, sample_flight_price_response):
        """Should extract main pricing information."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        pricing = result["pricing"]
        
        assert pricing["total"] == 1500.00
        assert pricing["base_fare"] == 1200.00
        assert pricing["taxes"] == 300.00
        assert pricing["currency"] == "USD"
    
    def test_extract_price_breakdown(self, sample_flight_price_response):
        """Should extract per-passenger price breakdown."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        breakdown = result["breakdown"]
        
        # Should have breakdown for each OfferPrice
        assert len(breakdown) == 2
        
        # First passenger/item
        assert breakdown[0]["total"] == 1500.00
        assert breakdown[0]["base_fare"] == 1200.00
        assert breakdown[0]["taxes"] == 300.00
        
        # Second passenger/item
        assert breakdown[1]["total"] == 750.00
        assert breakdown[1]["base_fare"] == 600.00
        assert breakdown[1]["taxes"] == 150.00
    
    def test_extract_tax_breakdown(self, sample_flight_price_response):
        """Should extract individual tax components."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        breakdown = result["breakdown"]
        
        # First passenger taxes
        taxes = breakdown[0]["tax_breakdown"]
        assert len(taxes) == 2
        
        assert taxes[0]["code"] == "YQ"
        assert taxes[0]["amount"] == 150.00
        
        assert taxes[1]["code"] == "YR"
        assert taxes[1]["amount"] == 150.00
    
    def test_extract_fare_details(self, sample_flight_price_response):
        """Should extract fare basis codes and cabin information."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        fare_details = result["fare_details"]
        
        assert "fare_basis_code" in fare_details
        assert fare_details["fare_basis_code"] == "YLOW"
        
        assert "cabin_type" in fare_details
        assert fare_details["cabin_type"] == "Economy"
        
        assert "booking_class" in fare_details
        assert fare_details["booking_class"]["code"] == "Y"
        assert fare_details["booking_class"]["name"] == "Economy Flex"
    
    def test_extract_penalties(self, sample_flight_price_response):
        """Should extract change and cancellation fees."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        penalties = result["penalties"]
        
        # Change fee
        assert "change_fee" in penalties
        assert penalties["change_fee"]["amount"] == 100.00
        assert penalties["change_fee"]["application"] == "Anytime"
        
        # Cancel fee
        assert "cancel_fee" in penalties
        assert penalties["cancel_fee"]["amount"] == 200.00
        assert penalties["cancel_fee"]["application"] == "Before Departure"
        
        # Conditions
        assert "conditions" in penalties
        assert penalties["conditions"] == "Non-refundable. Change fee: 100 USD"
    
    def test_extract_baggage_info(self, sample_flight_price_response):
        """Should extract baggage allowances."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        baggage = result["baggage"]
        
        # Checked baggage
        assert "checked" in baggage
        checked = baggage["checked"]
        assert checked["quantity"] == 2
        assert checked["weight"] == 23
        assert checked["unit"] == "KG"
        assert checked["passenger_type"] == "ADT"
        
        # Carry-on baggage
        assert "carry_on" in baggage
        carry_on = baggage["carry_on"]
        assert carry_on["quantity"] == 1
        assert carry_on["weight"] == 7
        assert carry_on["unit"] == "KG"
    
    def test_extract_segment_details(self, sample_flight_price_response):
        """Should extract flight segment information."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        segments = result["segments"]
        
        assert len(segments) == 1
        
        segment = segments[0]
        assert segment["segment_key"] == "SEG1"
        assert segment["departure"]["airport"] == "DXB"
        assert segment["departure"]["date"] == "2025-12-01"
        assert segment["departure"]["time"] == "14:30"
        assert segment["arrival"]["airport"] == "LHR"
        assert segment["marketing_carrier"]["airline"] == "EK"
        assert segment["marketing_carrier"]["flight_number"] == "001"
        
        # Service references
        assert "service_refs" in segment
        assert "SERVICE1" in segment["service_refs"]
        assert "SERVICE2" in segment["service_refs"]
    
    def test_extract_currency_metadata(self, sample_flight_price_response):
        """Should extract currency information from metadata."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        
        assert result["pricing"]["currency"] == "USD"
        assert result["metadata"]["currency"]["code"] == "USD"
        assert result["metadata"]["currency"]["decimals"] == 2
    
    def test_minimal_response(self, minimal_flight_price_response):
        """Should handle minimal response with only required fields."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(minimal_flight_price_response)
        
        # Should have basic structure
        assert result["offer_id"] == "MIN_OFFER"
        assert result["pricing"]["total"] == 1000.00
        
        # Optional fields should be empty/default
        assert result["breakdown"] == []
        assert result["fare_details"] == {}
        assert result["penalties"] == {}
        assert result["baggage"] == {}
        assert result["segments"] == []
    
    def test_empty_priced_offers(self):
        """Should raise error if no priced offers found."""
        response = {"PricedFlightOffers": {"PricedFlightOffer": []}}
        transformer = FlightPriceTransformer()
        
        with pytest.raises(ValueError, match="No priced offers found"):
            transformer.transform(response)
    
    def test_missing_offer_price(self):
        """Should handle missing OfferPrice gracefully."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "TEST", "Owner": "EK"}
                        # No OfferPrice
                    }
                ]
            }
        }
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(response)
        
        # Should still return basic structure
        assert result["offer_id"] == "TEST"
        assert result["breakdown"] == []
    
    def test_multiple_fare_components(self):
        """Should handle multiple fare components."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "MULTI", "Owner": "EK"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "SimpleCurrencyPrice": {"value": 1000.00}
                                        }
                                    }
                                },
                                "FareDetail": {
                                    "FareComponent": [
                                        {"FareBasis": {"FareBasisCode": {"Code": "Y1"}}},
                                        {"FareBasis": {"FareBasisCode": {"Code": "Y2"}}}
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(response)
        
        # Should use first fare component
        assert result["fare_details"]["fare_basis_code"] == "Y1"
    
    def test_missing_tax_breakdown(self):
        """Should handle missing tax breakdown."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "NO_TAX", "Owner": "EK"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "DetailCurrencyPrice": {
                                                "Total": {"value": 1000.00},
                                                "Taxes": {
                                                    "Total": {"value": 100.00}
                                                    # No Breakdown
                                                }
                                            },
                                            "BaseAmount": {"value": 900.00}
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(response)
        
        # Should still extract main pricing
        assert result["pricing"]["total"] == 1000.00
        assert result["pricing"]["taxes"] == 100.00
        
        # Tax breakdown should be empty
        assert result["breakdown"][0]["tax_breakdown"] == []
    
    def test_timestamp_in_metadata(self, sample_flight_price_response):
        """Should include timestamp in metadata."""
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(sample_flight_price_response)
        
        assert "timestamp" in result["metadata"]
        assert isinstance(result["metadata"]["timestamp"], str)
    
    def test_no_baggage_allowance(self):
        """Should handle response without baggage allowance."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "NO_BAG", "Owner": "EK"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "SimpleCurrencyPrice": {"value": 1000.00}
                                        }
                                    }
                                }
                            }
                        ]
                        # No BaggageAllowance
                    }
                ]
            }
        }
        transformer = FlightPriceTransformer()
        
        result = transformer.transform(response)
        
        assert result["baggage"] == {}
