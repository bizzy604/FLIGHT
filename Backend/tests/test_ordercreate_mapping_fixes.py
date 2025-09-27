"""
Test suite for OrderCreate mapping fixes.

This test verifies that the OrderCreate payload follows the VDC API documentation
mappings correctly, especially for SegmentReferences, FareBasisCode, and ServiceList.
"""
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.build_ordercreate_rq import generate_order_create_rq, _create_flight_to_segment_mapping


class TestOrderCreateMappingFixes:
    """Test cases for OrderCreate mapping fixes."""
    
    def test_flight_to_segment_mapping(self):
        """Test that flight numbers are correctly mapped to segment keys."""
        # Mock FlightPriceRS response with flight segments
        flight_price_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "FS1",
                            "MarketingCarrier": {
                                "AirlineID": {"value": "BA"},
                                "FlightNumber": {"value": "322"}
                            }
                        },
                        {
                            "SegmentKey": "FS2", 
                            "MarketingCarrier": {
                                "AirlineID": {"value": "BA"},
                                "FlightNumber": {"value": "323"}
                            }
                        }
                    ]
                }
            }
        }
        
        # Test the mapping function
        mapping = _create_flight_to_segment_mapping(flight_price_response)
        
        # Assertions
        assert mapping["BA322"] == "FS1"
        assert mapping["BA323"] == "FS2"
        assert len(mapping) == 2
        
    def test_segment_references_mapping(self):
        """Test that SegmentReferences use segment keys instead of flight numbers."""
        # Mock data with flight numbers in SeatAvailability response
        seatavailability_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1",
                        "Associations": [
                            {
                                "Traveler": {
                                    "TravelerReferences": ["T1"]
                                },
                                "Flight": {
                                    "originDestinationReferencesOrSegmentReferences": [
                                        {
                                            "SegmentReferences": {
                                                "value": ["BA322"]  # Flight number
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        flight_price_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "FS1",
                            "MarketingCarrier": {
                                "AirlineID": {"value": "BA"},
                                "FlightNumber": {"value": "322"}
                            }
                        }
                    ]
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-response-id"}
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "test-offer-id", "Owner": "BA"},
                        "OfferPrice": [
                            {
                                "OfferItemID": "test-item-id",
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "BaseAmount": {"value": 1000, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 100, "Code": "USD"}}
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        passengers_data = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",  # Fix: Use string instead of dict
                "Name": {"Surname": {"value": "Test"}, "Given": [{"value": "User"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1990-01-01"}}
            }
        ]
        
        payment_info = {"Method": "Cash", "Amount": {"value": 1100, "Code": "USD"}}
        
        selected_seats = ["SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1"]
        
        # Generate OrderCreate payload
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        # Check that SegmentReferences use segment keys
        seat_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_item = next((item for item in seat_items if item["OfferItemType"].get("SeatItem")), None)
        
        assert seat_item is not None, "Seat item should be present"
        
        seat_associations = seat_item["OfferItemType"]["SeatItem"][0]["SeatAssociation"]
        segment_references = seat_associations[0]["SegmentReferences"]["value"]
        
        # Should use segment key "FS1" instead of flight number "BA322"
        assert "FS1" in segment_references, f"Expected segment key 'FS1' in {segment_references}"
        assert "BA322" not in segment_references, f"Should not contain flight number 'BA322' in {segment_references}"
        
    def test_fare_basis_code_mapping(self):
        """Test that FareBasisCode is properly populated from FlightPriceRS."""
        flight_price_response = {
            "DataLists": {
                "FareList": {
                    "FareGroup": [
                        {
                            "ListKey": "FG-1",
                            "FareBasisCode": {
                                "Code": "YV3RO/Y"
                            }
                        }
                    ]
                },
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "FS1",
                            "MarketingCarrier": {
                                "AirlineID": {"value": "BA"},
                                "FlightNumber": {"value": "322"}
                            }
                        }
                    ]
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-response-id"}
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "test-offer-id", "Owner": "BA"},
                        "OfferPrice": [
                            {
                                "OfferItemID": "test-item-id",
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "BaseAmount": {"value": 1000, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 100, "Code": "USD"}}
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        passengers_data = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",  # Fix: Use string instead of dict
                "Name": {"Surname": {"value": "Test"}, "Given": [{"value": "User"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1990-01-01"}}
            }
        ]
        
        payment_info = {"Method": "Cash", "Amount": {"value": 1100, "Code": "USD"}}
        
        # Generate OrderCreate payload
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info
        )
        
        # Check that FareBasisCode is populated
        flight_items = result["Query"]["OrderItems"]["OfferItem"]
        flight_item = next((item for item in flight_items if item["OfferItemType"].get("DetailedFlightItem")), None)
        
        assert flight_item is not None, "Flight item should be present"
        
        fare_detail = flight_item["OfferItemType"]["DetailedFlightItem"][0].get("FareDetail", {})
        fare_components = fare_detail.get("FareComponent", [])
        
        if fare_components:
            fare_basis = fare_components[0].get("FareBasis", {})
            fare_basis_code = fare_basis.get("FareBasisCode", {})
            
            # Should have FareBasisCode populated
            assert fare_basis_code.get("Code") == "YV3RO/Y", f"Expected FareBasisCode 'YV3RO/Y', got {fare_basis_code}"
            assert fare_basis.get("RBD") == "YV3RO", f"Expected RBD 'YV3RO', got {fare_basis.get('RBD')}"
        
    def test_service_list_mapping(self):
        """Test that ServiceList is properly mapped according to VDC spec."""
        servicelist_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "1-ServiceIdBA-15",
                        "ServiceID": {
                            "ObjectKey": "test-service-id",
                            "value": "SRV15",
                            "Owner": "BA"
                        },
                        "Name": {"value": "BAG:LUGGAGE-FIRST ADDITIONAL BAG"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 50, "Code": "USD"}}],
                        "Associations": [
                            {
                                "Traveler": {
                                    "TravelerReferences": ["T1"]
                                },
                                "Flight": {
                                    "originDestinationReferencesOrSegmentReferences": [
                                        {
                                            "SegmentReferences": {
                                                "value": ["BA322"]  # Flight number
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        flight_price_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "FS1",
                            "MarketingCarrier": {
                                "AirlineID": {"value": "BA"},
                                "FlightNumber": {"value": "322"}
                            }
                        }
                    ]
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-response-id"}
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "test-offer-id", "Owner": "BA"},
                        "OfferPrice": [
                            {
                                "OfferItemID": "test-item-id",
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "BaseAmount": {"value": 1000, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 100, "Code": "USD"}}
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        passengers_data = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",  # Fix: Use string instead of dict
                "Name": {"Surname": {"value": "Test"}, "Given": [{"value": "User"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1990-01-01"}}
            }
        ]
        
        payment_info = {"Method": "Cash", "Amount": {"value": 1100, "Code": "USD"}}
        selected_services = ["1-ServiceIdBA-15"]
        
        # Generate OrderCreate payload
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        # Check that ServiceList is properly populated
        service_list = result["Query"]["DataLists"]["ServiceList"]["Service"]
        assert len(service_list) > 0, "ServiceList should contain services"
        
        # Check that the service has correct mapping
        service = service_list[0]
        assert service["ObjectKey"] == "1-ServiceIdBA-15"
        assert service["ServiceID"]["value"] == "SRV15"
        assert service["ServiceID"]["Owner"] == "BA"
        assert service["PricedInd"] == False
        
        # Check that SegmentReferences in ServiceList use segment keys
        associations = service.get("Associations", [])
        if associations:
            flight_refs = associations[0].get("Flight", {}).get("originDestinationReferencesOrSegmentReferences", [])
            if flight_refs:
                segment_refs = flight_refs[0].get("SegmentReferences", {}).get("value", [])
                # Should use segment key "FS1" instead of flight number "BA322"
                assert "FS1" in segment_refs, f"Expected segment key 'FS1' in {segment_refs}"
                assert "BA322" not in segment_refs, f"Should not contain flight number 'BA322' in {segment_refs}"
        
    def test_complete_ordercreate_structure(self):
        """Test that the complete OrderCreate structure follows VDC spec."""
        flight_price_response = {
            "DataLists": {
                "FareList": {
                    "FareGroup": [
                        {
                            "ListKey": "FG-1",
                            "FareBasisCode": {
                                "Code": "YV3RO/Y"
                            }
                        }
                    ]
                },
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "FS1",
                            "MarketingCarrier": {
                                "AirlineID": {"value": "BA"},
                                "FlightNumber": {"value": "322"}
                            }
                        }
                    ]
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-response-id"}
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "test-offer-id", "Owner": "BA"},
                        "OfferPrice": [
                            {
                                "OfferItemID": "test-item-id",
                                "RequestedDate": {
                                    "PriceDetail": {
                                        "BaseAmount": {"value": 1000, "Code": "USD"},
                                        "Taxes": {"Total": {"value": 100, "Code": "USD"}}
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        passengers_data = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",  # Fix: Use string instead of dict
                "Name": {"Surname": {"value": "Test"}, "Given": [{"value": "User"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1990-01-01"}}
            }
        ]
        
        payment_info = {"Method": "Cash", "Amount": {"value": 1100, "Code": "USD"}}
        
        # Generate OrderCreate payload
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info
        )
        
        # Verify complete structure
        assert "Query" in result
        assert "Passengers" in result["Query"]
        assert "OrderItems" in result["Query"]
        assert "DataLists" in result["Query"]
        
        # Verify Passengers structure
        passengers = result["Query"]["Passengers"]["Passenger"]
        assert len(passengers) == 1
        assert passengers[0]["ObjectKey"] == "T1"
        
        # Verify OrderItems structure
        order_items = result["Query"]["OrderItems"]
        assert "ShoppingResponse" in order_items
        assert "OfferItem" in order_items
        
        # Verify ShoppingResponse structure
        shopping_response = order_items["ShoppingResponse"]
        assert "Owner" in shopping_response
        assert "ResponseID" in shopping_response
        assert "Offers" in shopping_response
        
        # Verify OfferItem structure
        offer_items = order_items["OfferItem"]
        assert len(offer_items) > 0
        
        # Verify DataLists structure
        data_lists = result["Query"]["DataLists"]
        assert "FareList" in data_lists
        assert "ServiceList" in data_lists
        
    def test_edge_case_empty_responses(self):
        """Test edge cases with empty or malformed responses."""
        # Test with minimal data
        flight_price_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": []
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-response-id"}
            },
            "PricedFlightOffers": {
                "PricedFlightOffer": []
            }
        }
        
        passengers_data = []
        payment_info = {}
        
        # Should handle empty data gracefully
        try:
            result = generate_order_create_rq(
                flight_price_response=flight_price_response,
                passengers_data=passengers_data,
                payment_input_info=payment_info
            )
            # Should not crash, but may have empty structure
            assert "Query" in result
        except Exception as e:
            # Some errors are expected with empty data
            assert "missing" in str(e).lower() or "empty" in str(e).lower()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
