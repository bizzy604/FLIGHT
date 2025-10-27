"""Test FlightPrice transformer with real VDC API responses."""

import json
from pathlib import Path
from app.transformers.flight_price import FlightPriceTransformer


def test_real_flight_price_response():
    """Test with actual FlightPrice response from Seats & Services folder."""
    
    # Load real API response
    response_file = Path(__file__).parent / "Seats & Services" / "4_FlightPriceRS.json"
    
    with open(response_file, 'r') as f:
        response = json.load(f)
    
    # Transform
    transformer = FlightPriceTransformer()
    result = transformer.transform(response)
    
    # Validate structure
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
    
    # Validate offer ID
    assert result["offer_id"] == "1H1QRZ_8XK86U1JW81EU8HFNXI06TA8PL6K"
    
    # Validate pricing (from actual response: 56415 INR total)
    assert result["pricing"]["total"] == 56415
    assert result["pricing"]["base_fare"] == 39510
    assert result["pricing"]["taxes"] == 18881
    assert result["pricing"]["currency"] == "INR"
    assert result["pricing"]["discount"] == 1976
    
    # Validate discount details
    assert result["pricing"]["discount_details"] is not None
    assert result["pricing"]["discount_details"]["percent"] == 5
    assert result["pricing"]["discount_details"]["code"] == "Disc_rea"
    
    # Validate breakdown (should have 1 OfferPrice for 1 passenger)
    assert len(result["breakdown"]) == 1
    assert result["breakdown"][0]["total"] == 56415
    assert result["breakdown"][0]["traveler_refs"] == ["PAX1"]
    assert "BOMLHR" in result["breakdown"][0]["origin_destination_refs"]
    
    # Validate tax breakdown (9 taxes in actual response)
    assert len(result["breakdown"][0]["tax_breakdown"]) == 9
    tax_codes = [t["code"] for t in result["breakdown"][0]["tax_breakdown"]]
    assert "YQ" in tax_codes
    assert "YR" in tax_codes
    
    # Validate fare details
    assert result["fare_details"]["fare_basis_code"] == "SJR4I1SI"
    assert result["fare_details"]["rbd"] == "S"
    assert result["fare_details"]["cabin_type"] == "Economy"
    assert result["fare_details"]["booking_class"]["code"] == "S"
    assert result["fare_details"]["booking_class"]["name"] == "ECO"
    
    # Validate penalties (8 penalties in actual response)
    assert "change" in result["penalties"]
    assert "cancel" in result["penalties"]
    assert len(result["penalties"]["change"]["fees"]) > 0
    assert len(result["penalties"]["cancel"]["fees"]) > 0
    
    # Validate baggage
    assert "checked" in result["baggage"]
    assert result["baggage"]["checked"]["weight"] == 30
    assert result["baggage"]["checked"]["unit"] == "Kilogram"
    
    assert "carry_on" in result["baggage"]
    assert result["baggage"]["carry_on"]["quantity"] == 1
    assert result["baggage"]["carry_on"]["weight"] == 7
    
    # Validate segments (2 segments: BOM-DOH, DOH-LHR)
    assert len(result["segments"]) == 2
    
    seg1 = result["segments"][0]
    assert seg1["segment_key"] == "SEG2"
    assert seg1["departure"]["airport"] == "BOM"
    assert seg1["arrival"]["airport"] == "DOH"
    assert seg1["marketing_carrier"]["airline"] == "QR"
    assert seg1["marketing_carrier"]["flight_number"] == "4791"
    
    seg2 = result["segments"][1]
    assert seg2["segment_key"] == "SEG5"
    assert seg2["departure"]["airport"] == "DOH"
    assert seg2["arrival"]["airport"] == "LHR"
    assert seg2["marketing_carrier"]["flight_number"] == "109"
    
    # Validate trip type (one OD: BOMLHR = one-way)
    assert result["trip_type"] == "one-way"
    
    # Validate time limits
    assert result["time_limits"]["offer_expiration"] == "2025-08-13T17:27:12.000"
    assert result["time_limits"]["payment_time_limit"] == "2025-08-14T16:57:00.000"
    
    # Validate metadata
    assert result["metadata"]["currency"] == "INR"
    assert "timestamp" in result["metadata"]
    
    print("✅ All validations passed!")
    print(f"\n📊 Transformed Offer Summary:")
    print(f"  Offer ID: {result['offer_id']}")
    print(f"  Total Price: {result['pricing']['total']} {result['pricing']['currency']}")
    print(f"  Trip Type: {result['trip_type']}")
    print(f"  Segments: {len(result['segments'])}")
    print(f"  Fare Class: {result['fare_details']['booking_class']['name']}")
    print(f"  Checked Baggage: {result['baggage']['checked']['weight']}{result['baggage']['checked']['unit']}")


if __name__ == "__main__":
    test_real_flight_price_response()
