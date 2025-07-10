import sys
import os
import json
import pytest

# Add the project's root directory to the Python path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import all necessary functions from the refactored transformer
from Backend.utils.flight_price_transformer import (
    extract_reference_data, build_flight_segment, collect_all_offers,
    transform_for_frontend, _format_allowance_description,
    extract_baggage_from_association, VDCPenaltyInterpreter
)

# --- MOCK DATA FIXTURES ---

@pytest.fixture
def mock_refs():
    """Provides a basic reference dictionary for tests."""
    return {
        'carryon': {
            'CARRY1': {
                'PieceAllowance': [{'TotalQuantity': 1}],
                'WeightAllowance': {'MaximumWeight': [{'Value': 7, 'UOM': 'KG'}]}
            },
             'CARRY2': {
                'AllowanceDescription': {'Descriptions': {'Description': [{'Text': {'value': "1 Cabin Bag"}}]}}
            }
        },
        'checked': {
            'CHECK1': {'PieceAllowance': [{'TotalQuantity': 2}]},
            'CHECK2': {'AllowanceDescription': {'Descriptions': {'Description': [{'Text': {'value': "23kg per bag"}}]}}}
        },
        'price_classes': {
            'PC1': {'Name': 'Economy Light'},
            'PC2': {'Name': 'Business Flex'}
        },
        'segments': {
            'S1': {
                'SegmentKey': 'S1', 'Departure': {'AirportCode': {'value': 'JFK'}, 'Date': '2025-07-01T10:00:00'},
                'Arrival': {'AirportCode': {'value': 'LHR'}, 'Date': '2025-07-01T22:00:00'},
                'MarketingCarrier': {'AirlineID': {'value': 'BA'}, 'FlightNumber': {'value': '175'}}
            }
        },
        'penalties': {}
    }

@pytest.fixture
def mock_af_style_response():
    """Mocks a response with both PricedFlightOffers and AirlineOffers."""
    return {
        "PricedFlightOffers": {
            "PricedFlightOffer": [{"OfferID": {"value": "BaseOffer"}}]
        },
        "AirlineOffers": {
            "AirlineOffer": [
                {"PricedOffer": [{"OfferID": {"value": "Brand1OfferA"}}, {"OfferID": {"value": "Brand1OfferB"}}]},
                {"PricedOffer": [{"OfferID": {"value": "Brand2OfferA"}}]}
            ]
        }
    }

# --- UNIT TESTS FOR HELPERS AND CORE LOGIC ---

def test_collect_all_offers(mock_af_style_response):
    """
    Ensures offers are collected from both PricedFlightOffers and nested AirlineOffers.
    """
    offers = collect_all_offers(mock_af_style_response)
    assert len(offers) == 4
    offer_ids = {o.get('OfferID', {}).get('value') for o in offers}
    assert offer_ids == {"BaseOffer", "Brand1OfferA", "Brand1OfferB", "Brand2OfferA"}

def test_format_allowance_description():
    """
    Tests the baggage description formatting for various structures.
    """
    allowance1 = {'PieceAllowance': [{'TotalQuantity': 2}], 'WeightAllowance': {'MaximumWeight': [{'Value': 23, 'UOM': 'kg'}]}}
    assert _format_allowance_description(allowance1) == "2 pieces, up to 23 Kg"

    allowance2 = {'PieceAllowance': [{'TotalQuantity': 1}]}
    assert _format_allowance_description(allowance2) == "1 piece"
    
    allowance3 = {'WeightAllowance': {'MaximumWeight': [{'Value': 10, 'UOM': 'LBS'}]}}
    assert _format_allowance_description(allowance3) == "up to 10 Lbs"

    allowance4 = {'AllowanceDescription': {'Descriptions': {'Description': [{'Text': {'value': "Custom baggage text"}}]}}}
    assert _format_allowance_description(allowance4) == "Custom baggage text"

    allowance5 = {'PieceAllowance': [{'TotalQuantity': 0}]}
    assert _format_allowance_description(allowance5) == "No baggage"
    
    assert _format_allowance_description({}) == "N/A"

def test_extract_baggage_from_association(mock_refs):
    """
    Tests baggage extraction for both reference-based and inline structures.
    """
    assoc_ref = {
        'ApplicableFlight': {'FlightSegmentReference': [{
            'BagDetailAssociation': {
                'CarryOnReferences': ['CARRY1'],
                'CheckedBagReferences': ['CHECK1']
            }
        }]}
    }
    baggage = extract_baggage_from_association(assoc_ref, mock_refs)
    assert baggage['carryOn'] == "1 piece, up to 7 Kg"
    assert baggage['checked'] == "2 pieces"

    assoc_inline = {
        'ApplicableFlight': {'FlightSegmentReference': [{
            'BagDetailAssociation': {
                'CarryOnAllowance': [{'PieceAllowance': [{'TotalQuantity': 1}]}],
                'CheckedBagAllowance': [{'WeightAllowance': {'MaximumWeight': [{'Value': 32, 'UOM': 'KG'}]}}]
            }
        }]}
    }
    baggage_inline = extract_baggage_from_association(assoc_inline, mock_refs)
    assert baggage_inline['carryOn'] == "1 piece"
    assert baggage_inline['checked'] == "up to 32 Kg"

class TestVDCPenaltyInterpreter:
    @pytest.mark.parametrize("value, expected", [
        (True, True), (False, False),
        ("true", True), ("false", False),
        ("Allowed", True), ("Not Allowed", False), ("NAV", False),
        ("Missing", None), (None, None), ("", None),
        (1, True), (0, False)
    ])
    def test_safe_bool_convert(self, value, expected):
        assert VDCPenaltyInterpreter._safe_bool_convert(value) is expected

    def test_interpret_penalty_cancel_refundable_with_fee(self):
        p_data = {"CancelFeeInd": True, "RefundableInd": True, "Details": {"Detail": [{"Type": "Cancel", "Application": {"Code": "2"}}]}}
        interp = VDCPenaltyInterpreter.interpret_penalty(p_data)
        assert interp.penalty_applicable == "Yes"
        assert interp.refund_applicable == "Yes"
        assert interp.cancel_allowed == "Yes"
        assert "Refunable with penalty" in interp.interpretation

    def test_interpret_penalty_change_not_allowed(self):
        p_data = {"ChangeFeeInd": False, "ChangeAllowedInd": False, "Details": {"Detail": [{"Type": "Change"}]}}
        interp = VDCPenaltyInterpreter.interpret_penalty(p_data)
        assert interp.penalty_applicable == "No"
        assert interp.change_allowed == "No"
        assert interp.interpretation == "Change not allowed"

    def test_interpret_penalty_after_departure_no_show_override(self):
        p_data = {"CancelFeeInd": False, "RefundableInd": True, "Details": {"Detail": [{"Type": "Cancel", "Application": {"Code": "1"}}]}}
        interp = VDCPenaltyInterpreter.interpret_penalty(p_data)
        assert interp.refund_applicable == "No"
        assert interp.cancel_allowed == "No"
        assert "non-refundable (after departure no show)" in interp.interpretation.lower()
        
    def test_interpret_penalty_handles_noshow_type(self):
        p_data = {"CancelFeeInd": True, "RefundableInd": True, "Details": {"Detail": [{"Type": "Cancel-NoShow"}]}}
        interp = VDCPenaltyInterpreter.interpret_penalty(p_data)
        assert interp.action_type == "Cancel-Noshow"
        assert "[No-show]" in interp.interpretation

# --- INTEGRATION TESTS ---

@pytest.mark.parametrize("filename", [
    'FlightPriceRS_KQ.json',
    'FlightPriceRS_AF.json',
])
def test_transform_real_responses(filename):
    """
    Loads real API responses, transforms them, and validates the high-level structure.
    """
    input_path = os.path.join(os.path.dirname(__file__), filename)

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            api_response = json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Test input file not found: {input_path}")
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON from file: {input_path}")

    # Perform the transformation
    result = transform_for_frontend(api_response)

    # --- Assertions ---
    assert isinstance(result, dict)
    assert "offers" in result
    assert isinstance(result["offers"], list)
    assert len(result["offers"]) > 0, f"No offers were transformed from {filename}"

    # Validate the structure of the first transformed offer
    first_offer = result["offers"][0]
    assert "offer_id" in first_offer
    assert "fare_family" in first_offer
    assert "total_price" in first_offer
    assert "amount" in first_offer["total_price"] and "currency" in first_offer["total_price"]
    assert "flight_segments" in first_offer and len(first_offer["flight_segments"]) > 0
    assert "passengers" in first_offer and len(first_offer["passengers"]) > 0

    # Validate passenger group structure
    first_pax_group = first_offer["passengers"][0]
    assert "type" in first_pax_group and "count" in first_pax_group and first_pax_group["count"] > 0
    assert "baggage" in first_pax_group and "carryOn" in first_pax_group["baggage"] and "checked" in first_pax_group["baggage"]
    
    # ## FIX ##: Check for the new 'fare_rules' key instead of the old 'penalties' key.
    assert "fare_rules" in first_pax_group

    print(f"\nSuccessfully transformed {filename} with {len(result['offers'])} offer(s).")