"""Tests for FlightPrice request builder."""

import pytest
from app.builders.flight_price import FlightPriceRequestBuilder
from app.core.exceptions import BusinessLogicError


@pytest.fixture
def sample_air_shopping_response():
    """Sample AirShopping response for testing."""
    return {
        "OffersGroup": {
            "AirlineOffers": [
                {
                    "Owner": {"value": "EK"},
                    "AirlineOffer": [
                        {
                            "OfferID": {"value": "OFFER1", "Owner": "EK"},
                            "PricedOffer": {
                                "OfferPrice": [
                                    {
                                        "OfferItemID": "ITEM1",
                                        "RequestedDate": {
                                            "Associations": [
                                                {
                                                    "AssociatedTraveler": {
                                                        "TravelerReferences": ["T1", "T2"]
                                                    },
                                                    "ApplicableFlight": {
                                                        "OriginDestinationReferences": ["OD1"],
                                                        "FlightSegmentReference": [{"ref": "SEG1"}]
                                                    }
                                                }
                                            ]
                                        },
                                        "FareDetail": {
                                            "FareComponent": [
                                                {
                                                    "refs": ["FARE1"],
                                                    "FareRules": {
                                                        "Penalty": {"refs": ["PEN1"]}
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            },
                            "refs": ["REF1", "REF2"]
                        }
                    ]
                },
                {
                    "Owner": {"value": "BA"},
                    "AirlineOffer": [
                        {
                            "OfferID": {"value": "OFFER2", "Owner": "BA"},
                            "PricedOffer": {
                                "OfferPrice": [
                                    {
                                        "OfferItemID": "ITEM2",
                                        "RequestedDate": {
                                            "Associations": [
                                                {
                                                    "AssociatedTraveler": {
                                                        "TravelerReferences": ["T1"]
                                                    },
                                                    "ApplicableFlight": {
                                                        "OriginDestinationReferences": ["OD1"],
                                                        "FlightSegmentReference": [{"ref": "SEG2"}]
                                                    }
                                                }
                                            ]
                                        },
                                        "FareDetail": {
                                            "FareComponent": [{"refs": ["FARE2"]}]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {"ObjectKey": "T1", "PTC": {"value": "ADT"}},
                    {"ObjectKey": "T2", "PTC": {"value": "CHD"}}
                ]
            },
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "SEG1",
                        "Departure": {"AirportCode": {"value": "DXB"}, "Date": "2025-12-01"},
                        "Arrival": {"AirportCode": {"value": "LHR"}, "Date": "2025-12-01"},
                        "MarketingCarrier": {"AirlineID": {"value": "EK"}},
                        "OperatingCarrier": {"AirlineID": {"value": "EK"}},
                        "FlightDetail": {
                            "FlightDuration": "P7H30M",
                            "Stops": {"StopQuantity": 0}
                        }
                    },
                    {
                        "SegmentKey": "SEG2",
                        "Departure": {"AirportCode": {"value": "LHR"}, "Date": "2025-12-01"},
                        "Arrival": {"AirportCode": {"value": "JFK"}, "Date": "2025-12-01"},
                        "MarketingCarrier": {"AirlineID": {"value": "BA"}},
                        "OperatingCarrier": {"AirlineID": {"value": "BA"}},
                        "FlightDetail": {"FlightDuration": "P8H"}
                    }
                ]
            },
            "FareList": {
                "FareGroup": [
                    {"ListKey": "FARE1", "FareBasisCode": {"Code": "YLOW"}},
                    {"ListKey": "FARE2", "FareBasisCode": {"Code": "MFLEX"}}
                ]
            }
        },
        "ShoppingResponse": {
            "ShoppingResponseID": {"value": "SHOP123"}
        },
        "Metadata": {
            "Other": {
                "OtherMetadata": [
                    {
                        "DescriptionMetadatas": {
                            "DescriptionMetadata": [
                                {
                                    "MetadataKey": "SHOPPING_RESPONSE_IDS",
                                    "AugmentationPoint": {
                                        "AugPoint": [
                                            {"Owner": "EK", "Key": "SHOP_EK_123"},
                                            {"Owner": "BA", "Key": "SHOP_BA_456"}
                                        ]
                                    }
                                }
                            ]
                        },
                        "PriceMetadatas": {
                            "PriceMetadata": [
                                {"MetadataKey": "FARE1", "Value": "100"},
                                {"MetadataKey": "PEN1", "Value": "50"},
                                {"MetadataKey": "UNUSED", "Value": "999"}
                            ]
                        }
                    }
                ]
            }
        }
    }


class TestFlightPriceRequestBuilder:
    """Test FlightPrice request builder."""
    
    def test_initialization(self, sample_air_shopping_response):
        """Should initialize with AirShopping response."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        assert builder.response == sample_air_shopping_response
        assert builder.offers_group == sample_air_shopping_response["OffersGroup"]
        assert builder.data_lists == sample_air_shopping_response["DataLists"]
    
    def test_build_requires_airline_owner(self, sample_air_shopping_response):
        """Should require airline_owner parameter."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        with pytest.raises(BusinessLogicError, match="airline_owner is required"):
            builder.build(offer_index=0, airline_owner="")
    
    def test_build_valid_request_for_ek(self, sample_air_shopping_response):
        """Should build valid FlightPrice request for Emirates."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        result = builder.build(offer_index=0, airline_owner="EK")
        
        # Verify Query section
        assert "Query" in result
        assert "OriginDestination" in result["Query"]
        assert "Offers" in result["Query"]
        
        # Verify Offer structure
        offers = result["Query"]["Offers"]["Offer"]
        assert len(offers) == 1
        assert offers[0]["OfferID"]["value"] == "OFFER1"
        assert offers[0]["OfferID"]["Owner"] == "EK"
        
        # Verify OfferItemIDs
        offer_items = offers[0]["OfferItemIDs"]["OfferItemID"]
        assert len(offer_items) == 1
        assert offer_items[0]["value"] == "ITEM1"
        assert offer_items[0]["refs"] == ["T1", "T2"]
        
        # Verify Travelers section
        assert "Travelers" in result
        travelers = result["Travelers"]["Traveler"]
        assert len(travelers) == 2
    
    def test_build_valid_request_for_ba(self, sample_air_shopping_response):
        """Should build valid FlightPrice request for British Airways."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        result = builder.build(offer_index=0, airline_owner="BA")
        
        # Verify correct airline
        offers = result["Query"]["Offers"]["Offer"]
        assert offers[0]["OfferID"]["value"] == "OFFER2"
        assert offers[0]["OfferID"]["Owner"] == "BA"
    
    def test_airline_not_found(self, sample_air_shopping_response):
        """Should raise error if airline not found."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        with pytest.raises(BusinessLogicError, match="No offers found for airline QR"):
            builder.build(offer_index=0, airline_owner="QR")
    
    def test_offer_index_out_of_range(self, sample_air_shopping_response):
        """Should raise error if offer index out of range."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        with pytest.raises(BusinessLogicError, match="out of range"):
            builder.build(offer_index=5, airline_owner="EK")
    
    def test_extract_airline_specific_shopping_response_id(self, sample_air_shopping_response):
        """Should extract airline-specific ShoppingResponseID from metadata."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        # EK should get airline-specific ID
        shopping_id_ek = builder._get_shopping_response_id("EK")
        assert shopping_id_ek == "SHOP_EK_123"
        
        # BA should get airline-specific ID
        shopping_id_ba = builder._get_shopping_response_id("BA")
        assert shopping_id_ba == "SHOP_BA_456"
    
    def test_fallback_to_standard_shopping_response_id(self):
        """Should fallback to standard ShoppingResponseID if airline-specific not found."""
        response = {
            "OffersGroup": {"AirlineOffers": [{"Owner": {"value": "EK"}, "AirlineOffer": []}]},
            "DataLists": {},
            "ShoppingResponse": {"ShoppingResponseID": {"value": "FALLBACK123"}},
            "Metadata": {}
        }
        
        builder = FlightPriceRequestBuilder(response)
        shopping_id = builder._get_shopping_response_id("EK")
        
        assert shopping_id == "FALLBACK123"
    
    def test_extract_offer_references(self, sample_air_shopping_response):
        """Should extract all references from offer."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        offer = sample_air_shopping_response["OffersGroup"]["AirlineOffers"][0]["AirlineOffer"][0]
        refs = builder._extract_offer_references(offer)
        
        # Should include top-level refs and FareComponent refs
        assert "REF1" in refs
        assert "REF2" in refs
        assert "FARE1" in refs
        assert "PEN1" in refs
    
    def test_filter_price_metadata(self, sample_air_shopping_response):
        """Should filter PriceMetadata to only referenced items."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        offer_refs = {"FARE1", "PEN1"}  # Only these should be included
        filtered = builder._filter_price_metadata(offer_refs)
        
        # Verify structure
        assert "Other" in filtered
        metadata_list = filtered["Other"]["OtherMetadata"][0]["PriceMetadatas"]["PriceMetadata"]
        
        # Should only include referenced items
        metadata_keys = {item["MetadataKey"] for item in metadata_list}
        assert "FARE1" in metadata_keys
        assert "PEN1" in metadata_keys
        assert "UNUSED" not in metadata_keys  # Should be filtered out
    
    def test_build_origin_destinations(self, sample_air_shopping_response):
        """Should build OriginDestination list from offer."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        offer = sample_air_shopping_response["OffersGroup"]["AirlineOffers"][0]["AirlineOffer"][0]
        origin_destinations = builder._build_origin_destinations(offer)
        
        assert len(origin_destinations) == 1
        assert "Flight" in origin_destinations[0]
        
        flights = origin_destinations[0]["Flight"]
        assert len(flights) == 1
        assert flights[0]["SegmentKey"] == "SEG1"
        assert flights[0]["Departure"]["AirportCode"]["value"] == "DXB"
    
    def test_flight_detail_stops_filtering(self, sample_air_shopping_response):
        """Should exclude StopLocations from FlightDetail, keep only StopQuantity."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        offer = sample_air_shopping_response["OffersGroup"]["AirlineOffers"][0]["AirlineOffer"][0]
        origin_destinations = builder._build_origin_destinations(offer)
        
        flight_detail = origin_destinations[0]["Flight"][0]["FlightDetail"]
        
        # Should include FlightDuration
        assert "FlightDuration" in flight_detail
        assert flight_detail["FlightDuration"] == "P7H30M"
        
        # Should include Stops with StopQuantity only
        assert "Stops" in flight_detail
        assert "StopQuantity" in flight_detail["Stops"]
        assert flight_detail["Stops"]["StopQuantity"] == 0
        
        # Should NOT include StopLocations
        assert "StopLocations" not in flight_detail.get("Stops", {})
    
    def test_build_travelers(self, sample_air_shopping_response):
        """Should build Travelers list from AnonymousTravelerList."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        travelers = builder._build_travelers()
        
        assert "Traveler" in travelers
        traveler_list = travelers["Traveler"]
        
        assert len(traveler_list) == 2
        assert traveler_list[0]["AnonymousTraveler"][0]["PTC"]["value"] == "ADT"
        assert traveler_list[1]["AnonymousTraveler"][0]["PTC"]["value"] == "CHD"
    
    def test_build_data_lists(self, sample_air_shopping_response):
        """Should build DataLists with filtered FareGroups."""
        builder = FlightPriceRequestBuilder(sample_air_shopping_response)
        
        offer_refs = {"FARE1"}  # Only FARE1 should be included
        data_lists = builder._build_data_lists(offer_refs, "EK")
        
        # Should include FareGroup
        assert "FareGroup" in data_lists
        fare_groups = data_lists["FareGroup"]
        
        assert len(fare_groups) == 1
        assert fare_groups[0]["ListKey"] == "FARE1"
        
        # Should include AnonymousTravelerList
        assert "AnonymousTravelerList" in data_lists
    
    def test_empty_air_shopping_response(self):
        """Should handle empty AirShopping response."""
        response = {"OffersGroup": {"AirlineOffers": []}, "DataLists": {}}
        builder = FlightPriceRequestBuilder(response)
        
        with pytest.raises(BusinessLogicError):
            builder.build(offer_index=0, airline_owner="EK")
    
    def test_single_airline_response_structure(self):
        """Should handle single-airline response structure."""
        response = {
            "OffersGroup": {
                "AirlineOffers": [
                    {
                        "Owner": {"value": "EK"},
                        "AirlineOffer": [
                            {
                                "OfferID": {"value": "SINGLE1", "Owner": "EK"},
                                "PricedOffer": {
                                    "OfferPrice": [
                                        {
                                            "OfferItemID": "ITEM1",
                                            "RequestedDate": {
                                                "Associations": [
                                                    {
                                                        "AssociatedTraveler": {"TravelerReferences": ["T1"]},
                                                        "ApplicableFlight": {
                                                            "OriginDestinationReferences": ["OD1"],
                                                            "FlightSegmentReference": [{"ref": "SEG1"}]
                                                        }
                                                    }
                                                ]
                                            },
                                            "FareDetail": {"FareComponent": [{"refs": ["F1"]}]}
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            },
            "DataLists": {
                "AnonymousTravelerList": {"AnonymousTraveler": [{"ObjectKey": "T1", "PTC": {"value": "ADT"}}]},
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "SEG1",
                            "Departure": {"AirportCode": {"value": "DXB"}},
                            "Arrival": {"AirportCode": {"value": "LHR"}},
                            "MarketingCarrier": {},
                            "OperatingCarrier": {},
                            "FlightDetail": {}
                        }
                    ]
                },
                "FareList": {"FareGroup": [{"ListKey": "F1", "FareBasisCode": {"Code": "Y"}}]}
            },
            "ShoppingResponse": {"ShoppingResponseID": {"value": "SINGLE123"}}
        }
        
        builder = FlightPriceRequestBuilder(response)
        result = builder.build(offer_index=0, airline_owner="EK")
        
        assert result["Query"]["Offers"]["Offer"][0]["OfferID"]["value"] == "SINGLE1"
