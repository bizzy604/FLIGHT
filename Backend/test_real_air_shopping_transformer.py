"""Test AirShopping transformer with real VDC API responses."""

import json
from pathlib import Path
from app.transformers.air_shopping import AirShoppingTransformer


def test_real_air_shopping_response():
    """Test with actual AirShopping response from Seats & Services folder."""
    
    # Load real API response
    response_file = Path(__file__).parent / "Seats & Services" / "2_AirShoppingRS.json"
    
    with open(response_file, 'r') as f:
        response = json.load(f)
    
    # Transform
    transformer = AirShoppingTransformer()
    result = transformer.transform(response)
    
    print("=" * 80)
    print("🔍 AIRSHOPPING TRANSFORMER - REAL VDC DATA TEST")
    print("=" * 80)
    
    # Validate structure
    print("\n✅ Checking response structure...")
    assert "airlines" in result, "Missing 'airlines' field"
    assert "trip_type" in result, "Missing 'trip_type' field"
    assert "metadata" in result, "Missing 'metadata' field"
    print("   ✓ Basic structure validated")
    
    # Validate trip type
    print(f"\n✅ Trip Type Detection...")
    assert result["trip_type"] == "one-way", f"Expected 'one-way', got '{result['trip_type']}'"
    print(f"   ✓ Trip Type: {result['trip_type']}")
    
    # Validate airlines
    print("\n✅ Validating airlines...")
    airlines = result["airlines"]
    assert len(airlines) > 0, "No airlines found in response"
    print(f"   ✓ Found {len(airlines)} airline(s)")
    
    # Check first airline (should be QR - Qatar Airways)
    first_airline = airlines[0]
    assert first_airline["code"] == "QR", f"Expected 'QR', got '{first_airline['code']}'"
    print(f"   ✓ Airline code: {first_airline['code']}")
    print(f"   ✓ Total offers: {first_airline['total_offers']}")
    
    # Validate offers
    print("\n✅ Validating offers...")
    offers = first_airline.get("offers", [])
    assert len(offers) > 0, "No offers found for first airline"
    assert len(offers) == 38, f"Expected 38 offers, got {len(offers)}"
    print(f"   ✓ Found {len(offers)} offer(s)")
    
    # Check first offer
    first_offer = offers[0]
    assert "offer_id" in first_offer, "Missing offer_id"
    assert "pricing" in first_offer, "Missing pricing"
    assert "flights" in first_offer, "Missing flights"
    assert "baggage" in first_offer, "Missing baggage"
    assert "fare_details" in first_offer, "Missing fare_details"
    assert "penalties" in first_offer, "Missing penalties"
    
    print(f"\n📊 First Offer Details:")
    print(f"   Offer ID: {first_offer['offer_id']}")
    
    # Validate pricing
    pricing = first_offer['pricing']
    assert pricing['total'] == 56415.0, f"Expected total 56415.0, got {pricing['total']}"
    assert pricing['base_fare'] == 39510.0, f"Expected base 39510.0, got {pricing['base_fare']}"
    assert pricing['taxes'] == 18881.0, f"Expected taxes 18881.0, got {pricing['taxes']}"
    assert pricing['discount'] == 1976.0, f"Expected discount 1976.0, got {pricing['discount']}"
    assert pricing['currency'] == "INR", f"Expected currency INR, got {pricing['currency']}"
    
    print(f"   ✓ Total Price: {pricing['total']} {pricing['currency']}")
    print(f"   ✓ Base Fare: {pricing['base_fare']}")
    print(f"   ✓ Taxes: {pricing['taxes']}")
    
    # Check discount details
    discount_details = pricing.get('discount_details')
    assert discount_details is not None, "Missing discount_details"
    assert discount_details['code'] == 'Disc_rea', f"Expected discount code 'Disc_rea', got '{discount_details['code']}'"
    assert discount_details['name'] == 'ReaDiscount', f"Expected discount name 'ReaDiscount', got '{discount_details['name']}'"
    assert discount_details['percent'] == 5, f"Expected 5% discount, got {discount_details['percent']}%"
    
    print(f"   ✓ Discount: {pricing['discount']} {pricing['currency']} ({discount_details['percent']}%)")
    print(f"      - Code: {discount_details['code']}")
    print(f"      - Name: {discount_details['name']}")
    print(f"      - Pre-discount: {discount_details['pre_discount_amount']}")
    
    # Validate breakdown
    print("\n✅ Validating price breakdown...")
    breakdown = first_offer.get("breakdown", [])
    assert len(breakdown) > 0, "No price breakdown found"
    print(f"   ✓ Found {len(breakdown)} price breakdown(s)")
    
    first_breakdown = breakdown[0]
    assert "tax_breakdown" in first_breakdown, "Missing tax_breakdown field"
    tax_breakdown = first_breakdown["tax_breakdown"]
    # Note: AirShopping may not have detailed tax breakdown (only total), unlike FlightPrice
    print(f"   ✓ Tax components: {len(tax_breakdown)} (may be 0 in AirShopping)")
    
    # Validate flights
    print("\n✅ Validating flights...")
    flights = first_offer.get("flights", [])
    assert len(flights) > 0, "No flights found in first offer"
    print(f"   ✓ Found {len(flights)} flight(s)")
    
    # Check first flight
    first_flight = flights[0]
    assert "segments" in first_flight, "Missing segments"
    
    segments = first_flight.get("segments", [])
    assert len(segments) == 2, f"Expected 2 segments, got {len(segments)}"
    print(f"   ✓ Segments: {len(segments)}")
    
    for idx, segment in enumerate(segments, 1):
        print(f"\n   Segment {idx}:")
        print(f"      {segment['departure']['airport']} → {segment['arrival']['airport']}")
        print(f"      Departure: {segment['departure']['date']} {segment['departure']['time']}")
        print(f"      Arrival: {segment['arrival']['date']} {segment['arrival']['time']}")
        print(f"      Carrier: {segment['marketing_carrier']['airline']} {segment['marketing_carrier']['flight_number']}")
        print(f"      Aircraft: {segment['aircraft']}")
        print(f"      Duration: {segment['duration']}")
        print(f"      Cabin: {segment.get('cabin_type', 'N/A')}")
        print(f"      RBD: {segment.get('rbd', 'N/A')}")
    
    # Validate baggage
    print("\n✅ Validating baggage...")
    baggage = first_offer.get("baggage", {})
    assert "checked" in baggage, "Missing checked baggage"
    assert "carry_on" in baggage, "Missing carry-on baggage"
    
    checked = baggage["checked"]
    assert checked['weight'] == 30, f"Expected 30kg checked, got {checked['weight']}"
    assert checked['unit'] == "Kilogram", f"Expected Kilogram, got {checked['unit']}"
    print(f"   ✓ Checked Baggage: {checked['weight']}{checked['unit']}")
    
    carry_on = baggage["carry_on"]
    assert carry_on['quantity'] == 1, f"Expected 1 carry-on, got {carry_on['quantity']}"
    assert carry_on['weight'] == 7, f"Expected 7kg carry-on, got {carry_on['weight']}"
    print(f"   ✓ Carry-On: {carry_on['quantity']} piece(s), {carry_on['weight']}{carry_on['unit']}")
    
    # Validate fare details
    print("\n✅ Checking fare details...")
    fare_details = first_offer.get("fare_details", {})
    assert fare_details, "Missing fare details"
    print(f"   ✓ Fare Basis: {fare_details.get('fare_basis_code', 'N/A')}")
    print(f"   ✓ RBD: {fare_details.get('rbd', 'N/A')}")
    print(f"   ✓ Cabin Type: {fare_details.get('cabin_type', 'N/A')}")
    
    # Validate penalties
    print("\n✅ Checking penalties/fare rules...")
    penalties = first_offer.get("penalties", {})
    assert penalties, "Missing penalties"
    
    if "change" in penalties:
        change_fees = penalties['change'].get('fees', [])
        print(f"   ✓ Change fees: {len(change_fees)} rule(s)")
        if change_fees:
            print(f"      - Max: {change_fees[0].get('max_amount', 0)} {change_fees[0].get('currency', 'USD')}")
    
    if "cancel" in penalties:
        cancel_fees = penalties['cancel'].get('fees', [])
        print(f"   ✓ Cancel fees: {len(cancel_fees)} rule(s)")
        if cancel_fees:
            print(f"      - Max: {cancel_fees[0].get('max_amount', 0)} {cancel_fees[0].get('currency', 'USD')}")
    
    print(f"   ✓ Refundable: {penalties.get('refundable', 'Unknown')}")
    
    # Validate time limits
    print("\n✅ Checking time limits...")
    time_limits = first_offer.get("time_limits", {})
    assert time_limits, "Missing time limits"
    print(f"   ✓ Offer Expiration: {time_limits.get('offer_expiration', 'N/A')}")
    
    # Metadata validation
    print("\n✅ Validating metadata...")
    metadata = result["metadata"]
    assert "timestamp" in metadata, "Missing timestamp in metadata"
    print(f"   ✓ Timestamp: {metadata['timestamp']}")
    print(f"   ✓ Reference Version: {metadata.get('reference_version', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✅ ALL VALIDATIONS PASSED!")
    print("=" * 80)
    
    # Summary
    print(f"\n📈 SUMMARY:")
    print(f"   Airlines: {len(airlines)}")
    print(f"   Total Offers: {sum(a['total_offers'] for a in airlines)}")
    print(f"   Trip Type: {result['trip_type']}")
    print(f"   Currency: {first_offer['pricing']['currency']}")
    print(f"   Price Range: {min(o['pricing']['total'] for a in airlines for o in a['offers'])} - {max(o['pricing']['total'] for a in airlines for o in a['offers'])} {pricing['currency']}")
    
    return result


if __name__ == "__main__":
    try:
        result = test_real_air_shopping_response()
        print("\n✅ Test completed successfully!")
    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


