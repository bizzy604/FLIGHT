"""
Unit tests for VDCPenaltyInterpreter fare rules mappings using real FlightPrice response data.

This test file validates the correct interpretation of fare rules based on the 
corrected CANCEL_MATRIX and CHANGE_MATRIX mappings using actual penalty data 
from FlightPriceRS_AF.json.
"""

import json
import pytest
from pathlib import Path
from utils.flight_price_transformer import VDCPenaltyInterpreter


class TestFareRulesMappings:
    """Test class for validating fare rules interpretation mappings."""
    
    @classmethod
    def setup_class(cls):
        """Load test data from FlightPriceRS_AF.json."""
        test_file_path = Path(__file__).parent / "FlightPriceRS_AF.json"
        with open(test_file_path, 'r', encoding='utf-8') as f:
            cls.test_data = json.load(f)
        
        # Extract penalty list for easy access
        cls.penalties = {}
        for penalty in cls.test_data.get("DataLists", {}).get("PenaltyList", {}).get("Penalty", []):
            cls.penalties[penalty["ObjectKey"]] = penalty

    def test_change_matrix_true_true_mapping(self):
        """Test Change Fee=TRUE, Change Allowed=TRUE mapping."""
        # Use PEN_Change_PDE_200_Y from test data
        penalty_data = self.penalties["PEN_Change_PDE_200_Y"]
        
        # Verify the penalty data structure
        assert penalty_data["ChangeFeeInd"] is True
        assert penalty_data["ChangeAllowedInd"] is True
        
        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
        
        assert interpretation.penalty_applicable == "Yes"
        assert interpretation.change_allowed == "Yes"
        assert interpretation.interpretation == "Change allowed with penalty + difference in fare"
        assert interpretation.action_type == "Change"

    def test_change_matrix_false_true_mapping(self):
        """Test Change Fee=FALSE, Change Allowed=TRUE mapping."""
        # Use PEN_Change_PDE_0_N from test data (ChangeFeeInd=false, ChangeAllowedInd=true)
        penalty_data = self.penalties["PEN_Change_PDE_0_N"]
        
        # Verify the penalty data structure
        assert penalty_data["ChangeFeeInd"] is False
        assert penalty_data["ChangeAllowedInd"] is True
        
        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
        
        assert interpretation.penalty_applicable == "No"
        assert interpretation.change_allowed == "Yes"
        assert interpretation.interpretation == "Free change + difference in fare"

    def test_change_matrix_false_false_mapping(self):
        """Test Change Fee=FALSE, Change Allowed=FALSE mapping."""
        # Use PEN_NoShow_NOSHOW_CHANGE_225517.00_false from test data
        penalty_data = self.penalties["PEN_NoShow_NOSHOW_CHANGE_225517.00_false"]

        # Verify the penalty data structure
        assert penalty_data["ChangeFeeInd"] is False
        assert penalty_data["ChangeAllowedInd"] is False

        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        assert interpretation.penalty_applicable == "No"
        assert interpretation.change_allowed == "No"
        # Note: This penalty has timing code 1 (After Departure NO Show) which overrides the matrix
        assert "change not allowed" in interpretation.interpretation.lower()

    def test_cancel_matrix_false_true_mapping(self):
        """Test Cancel Fee=FALSE, Refundable=TRUE mapping."""
        # Use PEN_Cancellation_PDE_0_N from test data (has CancelFeeInd=false, RefundableInd=true)
        penalty_data = self.penalties["PEN_Cancellation_PDE_0_N"]

        # Verify the penalty data structure
        assert penalty_data["CancelFeeInd"] is False
        assert penalty_data["RefundableInd"] is True

        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        assert interpretation.penalty_applicable == "No"
        assert interpretation.refund_applicable == "Yes"
        assert interpretation.cancel_allowed == "Yes"
        assert interpretation.interpretation == "Fully refundable (without penalty)"

    def test_cancel_matrix_false_false_mapping(self):
        """Test Cancel Fee=FALSE, Refundable=FALSE mapping."""
        # Use PEN_Cancellation_PDE_225517.00_NAV_N from test data
        penalty_data = self.penalties["PEN_Cancellation_PDE_225517.00_NAV_N"]
        
        # Verify the penalty data structure
        assert penalty_data["CancelFeeInd"] is False
        assert penalty_data["RefundableInd"] is False
        
        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
        
        assert interpretation.penalty_applicable == "No"
        assert interpretation.refund_applicable == "No"
        assert interpretation.cancel_allowed == "No"
        assert interpretation.interpretation == "Non-refundable"

    def test_timing_code_override_after_departure_no_show(self):
        """Test timing code 1 (After Departure NO Show) overrides matrix results."""
        # Use PEN_NoShow_NOSHOW_CHANGE_225517.00_false with timing code 1
        penalty_data = self.penalties["PEN_NoShow_NOSHOW_CHANGE_225517.00_false"]
        
        # Verify timing code
        timing_code = penalty_data["Details"]["Detail"][0]["Application"]["Code"]
        assert timing_code == "1"  # After Departure NO Show
        
        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
        
        # Should override to "No" regardless of matrix result
        assert interpretation.change_allowed == "No"
        assert "change not allowed (after departure no show)" in interpretation.interpretation.lower()

    def test_timing_code_override_after_departure_cancel(self):
        """Test timing code 3 (After Departure) overrides cancel matrix results."""
        # Use PEN_Cancellation_ADE_225517.00_NAV_N with timing code 3
        penalty_data = self.penalties["PEN_Cancellation_ADE_225517.00_NAV_N"]
        
        # Verify timing code
        timing_code = penalty_data["Details"]["Detail"][0]["Application"]["Code"]
        assert timing_code == "3"  # After Departure
        
        # Test the interpretation
        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
        
        # Should override to "No" regardless of matrix result
        assert interpretation.refund_applicable == "No"
        assert interpretation.cancel_allowed == "No"
        assert "non-refundable (after departure)" in interpretation.interpretation.lower()

    def test_amount_extraction_min_max(self):
        """Test MIN/MAX amount extraction from penalty details."""
        from utils.flight_price_transformer import _extract_min_max_amount
        
        # Use PEN_Change_PDE_200_Y which has both MIN and MAX amounts
        penalty_data = self.penalties["PEN_Change_PDE_200_Y"]
        detail = penalty_data["Details"]["Detail"][0]
        
        min_amt, max_amt, currency = _extract_min_max_amount(detail)
        
        assert min_amt == 200.00
        assert max_amt == 200.00
        assert currency == "USD"

    def test_amount_extraction_zero_amounts(self):
        """Test amount extraction for zero penalty amounts."""
        from utils.flight_price_transformer import _extract_min_max_amount
        
        # Use PEN_Change_PDE_0_N which has zero amounts
        penalty_data = self.penalties["PEN_Change_PDE_0_N"]
        detail = penalty_data["Details"]["Detail"][0]
        
        min_amt, max_amt, currency = _extract_min_max_amount(detail)
        
        assert min_amt == 0
        assert max_amt == 0
        assert currency == "INR"

    def test_safe_bool_convert_various_inputs(self):
        """Test the _safe_bool_convert method with various input types."""
        converter = VDCPenaltyInterpreter._safe_bool_convert
        
        # Test boolean inputs
        assert converter(True) is True
        assert converter(False) is False
        
        # Test integer inputs
        assert converter(1) is True
        assert converter(0) is False
        
        # Test string inputs
        assert converter("true") is True
        assert converter("false") is False
        assert converter("yes") is True
        assert converter("no") is False
        assert converter("allowed") is True
        assert converter("not allowed") is False
        
        # Test None and "Missing"
        assert converter(None) is None
        assert converter("Missing") is None
        
        # Test unknown values
        assert converter("unknown") is None
        assert converter(2) is None

    def test_penalty_interpretation_with_real_data_comprehensive(self):
        """Comprehensive test using multiple real penalty scenarios from test data."""
        test_scenarios = [
            {
                "penalty_key": "PEN_Change_PDE_200_Y",
                "expected": {
                    "penalty_applicable": "Yes",
                    "change_allowed": "Yes",
                    "interpretation": "Change allowed with penalty + difference in fare"
                }
            },
            {
                "penalty_key": "PEN_Change_PDE_0_N", 
                "expected": {
                    "penalty_applicable": "No",
                    "change_allowed": "Yes",
                    "interpretation": "Free change + difference in fare"
                }
            },
            {
                "penalty_key": "PEN_NoShow_NOSHOW_CHANGE_225517.00_false",
                "expected": {
                    "penalty_applicable": "No",
                    "change_allowed": "No",  # Overridden by timing code 1
                    "interpretation_contains": "change not allowed (after departure no show)"
                }
            },
            {
                "penalty_key": "PEN_Cancellation_PDE_225517.00_NAV_N",
                "expected": {
                    "penalty_applicable": "No",
                    "refund_applicable": "No",
                    "cancel_allowed": "No",
                    "interpretation": "Non-refundable"
                }
            }
        ]
        
        for scenario in test_scenarios:
            penalty_data = self.penalties[scenario["penalty_key"]]
            interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
            expected = scenario["expected"]
            
            # Check each expected field
            for field, expected_value in expected.items():
                if field == "interpretation_contains":
                    assert expected_value.lower() in interpretation.interpretation.lower(), \
                        f"Failed for {scenario['penalty_key']}: expected '{expected_value}' in '{interpretation.interpretation}'"
                else:
                    actual_value = getattr(interpretation, field)
                    assert actual_value == expected_value, \
                        f"Failed for {scenario['penalty_key']}: {field} expected '{expected_value}', got '{actual_value}'"


    def test_change_matrix_missing_true_corrected_mapping(self):
        """Test the corrected Missing → TRUE mapping for change rules."""
        # Create a synthetic penalty data to test Missing ChangeFeeInd, TRUE ChangeAllowedInd
        penalty_data = {
            "Details": {"Detail": [{"Type": "Change", "Application": {"Code": "2"}}]},
            "ChangeAllowedInd": True
            # ChangeFeeInd is missing (None)
        }

        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        # Should match corrected mapping: (None, True) → ("Unknown", "Yes", "Change allowed, Penalty details unknown")
        assert interpretation.penalty_applicable == "Unknown"  # Fixed from "No" to "Unknown"
        assert interpretation.change_allowed == "Yes"
        assert interpretation.interpretation == "Change allowed, Penalty details unknown"  # Fixed interpretation

    def test_change_matrix_false_missing_corrected_mapping(self):
        """Test the corrected FALSE → Missing mapping for change rules."""
        # Create a synthetic penalty data to test FALSE ChangeFeeInd, Missing ChangeAllowedInd
        penalty_data = {
            "Details": {"Detail": [{"Type": "Change", "Application": {"Code": "2"}}]},
            "ChangeFeeInd": False
            # ChangeAllowedInd is missing (None)
        }

        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        # Should match corrected mapping: (False, None) → ("No", "Unknown", "Change allowed unknown")
        assert interpretation.penalty_applicable == "No"
        assert interpretation.change_allowed == "Unknown"
        assert interpretation.interpretation == "Change allowed unknown"  # Fixed from "Free change + difference in fare"

    def test_change_matrix_true_missing_mapping(self):
        """Test TRUE → Missing mapping for change rules."""
        # Create a synthetic penalty data to test TRUE ChangeFeeInd, Missing ChangeAllowedInd
        penalty_data = {
            "Details": {"Detail": [{"Type": "Change", "Application": {"Code": "2"}}]},
            "ChangeFeeInd": True
            # ChangeAllowedInd is missing (None)
        }

        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        # Should match mapping: (True, None) → ("Yes", "Yes", "Change allowed with fee")
        assert interpretation.penalty_applicable == "Yes"
        assert interpretation.change_allowed == "Yes"
        assert interpretation.interpretation == "Change allowed with fee"

    def test_change_matrix_missing_false_mapping(self):
        """Test Missing → FALSE mapping for change rules."""
        # Create a synthetic penalty data to test Missing ChangeFeeInd, FALSE ChangeAllowedInd
        penalty_data = {
            "Details": {"Detail": [{"Type": "Change", "Application": {"Code": "2"}}]},
            "ChangeAllowedInd": False
            # ChangeFeeInd is missing (None)
        }

        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        # Should match mapping: (None, False) → ("No", "No", "Change not allowed")
        assert interpretation.penalty_applicable == "No"
        assert interpretation.change_allowed == "No"
        assert interpretation.interpretation == "Change not allowed"

    def test_change_matrix_missing_missing_mapping(self):
        """Test Missing → Missing mapping for change rules."""
        # Create a synthetic penalty data to test Missing ChangeFeeInd, Missing ChangeAllowedInd
        penalty_data = {
            "Details": {"Detail": [{"Type": "Change", "Application": {"Code": "2"}}]}
            # Both ChangeFeeInd and ChangeAllowedInd are missing (None)
        }

        interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)

        # Should match mapping: (None, None) → ("Unknown", "Unknown", "Change allowed unknown")
        assert interpretation.penalty_applicable == "Unknown"
        assert interpretation.change_allowed == "Unknown"
        assert interpretation.interpretation == "Change allowed unknown"

    def test_cancel_matrix_comprehensive_mappings(self):
        """Test all cancel matrix mappings comprehensively."""
        test_cases = [
            # (CancelFeeInd, RefundableInd) → (penalty_applicable, refund_applicable, cancel_allowed, interpretation)
            {
                "cancel_fee": True, "refundable": True,
                "expected": ("Yes", "Yes", "Yes", "Refunable with penalty (partially refundable)")
            },
            {
                "cancel_fee": False, "refundable": True,
                "expected": ("No", "Yes", "Yes", "Fully refundable (without penalty)")
            },
            {
                "cancel_fee": False, "refundable": False,
                "expected": ("No", "No", "No", "Non-refundable")
            },
            {
                "cancel_fee": None, "refundable": True,
                "expected": ("Unknown", "Yes", "Yes", "Refundable but penalty is unknown")
            },
            {
                "cancel_fee": None, "refundable": False,
                "expected": ("No", "No", "No", "Non refundable")
            },
            {
                "cancel_fee": False, "refundable": None,
                "expected": ("No", "Unknown", "Unknown", "Refundability Unknown")
            },
            {
                "cancel_fee": True, "refundable": None,
                "expected": ("Yes", "Unknown", "Yes", "Cancel allowed with fee, refundability unknown")
            },
            {
                "cancel_fee": None, "refundable": None,
                "expected": ("Unknown", "Unknown", "Unknown", "Cancellation details unknown")
            }
        ]

        for case in test_cases:
            penalty_data = {
                "Details": {"Detail": [{"Type": "Cancel", "Application": {"Code": "2"}}]}
            }

            # Add indicators only if they're not None
            if case["cancel_fee"] is not None:
                penalty_data["CancelFeeInd"] = case["cancel_fee"]
            if case["refundable"] is not None:
                penalty_data["RefundableInd"] = case["refundable"]

            interpretation = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
            expected = case["expected"]

            assert interpretation.penalty_applicable == expected[0], \
                f"Cancel matrix test failed for {case}: penalty_applicable expected {expected[0]}, got {interpretation.penalty_applicable}"
            assert interpretation.refund_applicable == expected[1], \
                f"Cancel matrix test failed for {case}: refund_applicable expected {expected[1]}, got {interpretation.refund_applicable}"
            assert interpretation.cancel_allowed == expected[2], \
                f"Cancel matrix test failed for {case}: cancel_allowed expected {expected[2]}, got {interpretation.cancel_allowed}"
            assert interpretation.interpretation == expected[3], \
                f"Cancel matrix test failed for {case}: interpretation expected '{expected[3]}', got '{interpretation.interpretation}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
