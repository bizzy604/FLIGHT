"""
Comprehensive tests for FlightPrice transformer using REAL VDC API responses.

These tests use the actual VDC response structure from production data (4_FlightPriceRS.json)
rather than mocked data. This ensures 100% compatibility with real API.
"""

import pytest
import json
from pathlib import Path
from app.transformers.flight_price import FlightPriceTransformer


@pytest.fixture
def real_flight_price_response():
    """Load real FlightPrice response from Seats & Services folder."""
    response_file = Path(__file__).parent.parent.parent / "Seats & Services" / "4_FlightPriceRS.json"
    with open(response_file, 'r') as f:
        return json.load(f)


class TestFlightPriceTransformerRealData:
    """Test FlightPrice transformer with real VDC API responses."""
    
    def test_transform_real_response(self, real_flight_price_response):
        """Should successfully transform real VDC FlightPrice response."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        # Validate top-level structure
        assert "offer_id" in result
        assert "pricing" in result
        assert "breakdown" in result
        assert "fare_details" in result
        assert "penalties" in result
        assert "baggage" in result
        assert "segments" in result
        assert "trip_type" in result
        assert "time_limits" in result
        assert "metadata" in result
    
    def test_extract_offer_id(self, real_flight_price_response):
        """Should extract offer ID from real response."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        assert result["offer_id"] == "1H1QRZ_8XK86U1JW81EU8HFNXI06TA8PL6K"
    
    def test_extract_pricing(self, real_flight_price_response):
        """Should extract correct pricing from real response."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        pricing = result["pricing"]
        assert pricing["total"] == 56415.0
        assert pricing["base_fare"] == 39510.0
        assert pricing["taxes"] == 18881.0
        assert pricing["discount"] == 1976.0
        assert pricing["currency"] == "INR"
    
    def test_extract_discount_details(self, real_flight_price_response):
        """Should extract discount details from real response."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        discount_details = result["pricing"]["discount_details"]
        assert discount_details is not None
        assert discount_details["amount"] == 1976.0
        assert discount_details["percent"] == 5
        assert discount_details["code"] == "Disc_rea"
        assert discount_details["name"] == "ReaDiscount"
        assert discount_details["pre_discount_amount"] == 58391.0
    
    def test_extract_price_breakdown(self, real_flight_price_response):
        """Should extract per-passenger price breakdown."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        breakdown = result["breakdown"]
        assert len(breakdown) > 0
        
        first_item = breakdown[0]
        assert "total" in first_item
        assert "base_fare" in first_item
        assert "taxes" in first_item
        assert "tax_breakdown" in first_item
        assert "traveler_refs" in first_item
        assert "flight_refs" in first_item
        assert "origin_destination_refs" in first_item
    
    def test_extract_tax_breakdown(self, real_flight_price_response):
        """Should extract individual tax components."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        breakdown = result["breakdown"]
        taxes = breakdown[0]["tax_breakdown"]
        
        # Real response has 9 tax components
        assert len(taxes) == 9
        
        # Verify tax codes present
        tax_codes = [tax["code"] for tax in taxes]
        assert "YQ" in tax_codes
        assert "YR" in tax_codes
        assert "IN" in tax_codes
        
        # Verify first tax
        yq_tax = next(tax for tax in taxes if tax["code"] == "YQ")
        assert yq_tax["amount"] > 0
    
    def test_extract_fare_details(self, real_flight_price_response):
        """Should extract fare basis and cabin information."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        fare_details = result["fare_details"]
        assert fare_details["fare_basis_code"] == "SJR4I1SI"
        assert fare_details["rbd"] == "S"
        assert fare_details["cabin_type"] == "Economy"
        assert fare_details["booking_class"]["code"] == "S"
        assert fare_details["booking_class"]["name"] == "ECO"
    
    def test_extract_penalties(self, real_flight_price_response):
        """Should extract change and cancellation fees."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        penalties = result["penalties"]
        assert "change" in penalties
        assert "cancel" in penalties
        assert "refundable" in penalties
        
        # Should have penalty fees
        change_fees = penalties["change"]["fees"]
        cancel_fees = penalties["cancel"]["fees"]
        
        assert len(change_fees) > 0
        assert len(cancel_fees) > 0
        
        # Verify fee structure
        first_change_fee = change_fees[0]
        assert "max_amount" in first_change_fee
        assert "currency" in first_change_fee
        assert first_change_fee["max_amount"] > 0
    
    def test_extract_baggage_info(self, real_flight_price_response):
        """Should extract baggage allowances."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        baggage = result["baggage"]
        
        # Checked baggage
        assert "checked" in baggage
        checked = baggage["checked"]
        assert checked["weight"] == 30
        assert checked["unit"] == "Kilogram"
        
        # Carry-on baggage
        assert "carry_on" in baggage
        carry_on = baggage["carry_on"]
        assert carry_on["quantity"] == 1
        assert carry_on["weight"] == 7
        assert carry_on["unit"] == "Kilogram"
    
    def test_extract_segment_details(self, real_flight_price_response):
        """Should extract flight segment information."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        segments = result["segments"]
        assert len(segments) == 2
        
        # First segment (BOM-DOH)
        seg1 = segments[0]
        assert seg1["departure"]["airport"] == "BOM"
        assert seg1["arrival"]["airport"] == "DOH"
        assert seg1["marketing_carrier"]["airline"] == "QR"
        assert "duration" in seg1
        
        # Second segment (DOH-LHR)
        seg2 = segments[1]
        assert seg2["departure"]["airport"] == "DOH"
        assert seg2["arrival"]["airport"] == "LHR"
    
    def test_detect_trip_type(self, real_flight_price_response):
        """Should detect trip type from OriginDestination count."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        # Real response is one-way (BOM->LHR)
        assert result["trip_type"] == "one-way"
    
    def test_extract_time_limits(self, real_flight_price_response):
        """Should extract offer expiration and payment deadline."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        time_limits = result["time_limits"]
        assert "offer_expiration" in time_limits
        assert "payment_time_limit" in time_limits
        assert time_limits["offer_expiration"] != ""
    
    def test_extract_currency(self, real_flight_price_response):
        """Should extract currency code."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        assert result["metadata"]["currency"] == "INR"
    
    def test_metadata_timestamp(self, real_flight_price_response):
        """Should include timestamp in metadata."""
        transformer = FlightPriceTransformer()
        result = transformer.transform(real_flight_price_response)
        
        assert "timestamp" in result["metadata"]
        assert result["metadata"]["timestamp"] != ""


class TestFlightPriceTransformerEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_priced_offers(self):
        """Should handle empty priced offers."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": []
            },
            "DataLists": {}
        }
        
        transformer = FlightPriceTransformer()
        
        with pytest.raises(ValueError, match="No priced offers found"):
            transformer.transform(response)
    
    def test_missing_offer_price(self):
        """Should handle missing OfferPrice array."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "TEST"},
                        # Missing OfferPrice
                    }
                ]
            },
            "DataLists": {}
        }
        
        transformer = FlightPriceTransformer()
        result = transformer.transform(response)
        
        # Should return defaults for missing data
        assert result["pricing"]["total"] == 0.0
        assert result["pricing"]["currency"] == "USD"
    
    def test_missing_data_lists(self):
        """Should handle missing DataLists."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "TEST"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "SimpleCurrencyPrice": {"value": 1000, "Code": "USD"}
                                        },
                                        "BaseAmount": {"value": 800, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 200, "Code": "USD"}}
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
            # Missing DataLists
        }
        
        transformer = FlightPriceTransformer()
        result = transformer.transform(response)
        
        # Should still extract pricing
        assert result["pricing"]["total"] == 1000.0
        assert result["pricing"]["base_fare"] == 800.0
        
        # But no baggage/segments/penalties
        assert result["baggage"] == {}
        assert result["segments"] == []
        assert result["trip_type"] == "one-way"  # Default when no OD list
    
    def test_no_discount(self):
        """Should handle offers without discount."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "NO_DISCOUNT"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "SimpleCurrencyPrice": {"value": 1000, "Code": "USD"}
                                        },
                                        "BaseAmount": {"value": 800, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 200, "Code": "USD"}}
                                        # No Discount array
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            "DataLists": {}
        }
        
        transformer = FlightPriceTransformer()
        result = transformer.transform(response)
        
        assert result["pricing"]["discount"] == 0.0
        assert result["pricing"]["discount_details"] is None
    
    def test_round_trip_detection(self):
        """Should detect round-trip from 2 OriginDestinations."""
        response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "ROUND_TRIP"},
                        "OfferPrice": [
                            {
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "TotalAmount": {
                                            "SimpleCurrencyPrice": {"value": 2000, "Code": "USD"}
                                        },
                                        "BaseAmount": {"value": 1600, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 400, "Code": "USD"}}
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            "DataLists": {
                "OriginDestinationList": {
                    "OriginDestination": [
                        {"OriginDestinationKey": "OD1"},
                        {"OriginDestinationKey": "OD2"}
                    ]
                }
            }
        }
        
        transformer = FlightPriceTransformer()
        result = transformer.transform(response)
        
        assert result["trip_type"] == "round-trip"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
