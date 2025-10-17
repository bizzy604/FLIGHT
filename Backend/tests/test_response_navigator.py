"""
Unit Tests for FlightResponseNavigator

Tests the utility class for navigating NDC flight response structures.
"""

import pytest
from services.flight.response_navigator import FlightResponseNavigator


class TestExtractId:
    """Test suite for extract_id method."""
    
    def test_extract_shopping_response_id_direct(self):
        """Test extracting ShoppingResponseID from direct field."""
        response = {
            'ShoppingResponseID': {
                'ResponseID': {
                    'value': 'TEST-SHOP-123'
                }
            }
        }
        
        result = FlightResponseNavigator.extract_id(response, 'ShoppingResponseID')
        assert result == 'TEST-SHOP-123'
    
    def test_extract_shopping_response_id_nested_data_raw_response(self):
        """Test extracting ShoppingResponseID from data.raw_response."""
        response = {
            'data': {
                'raw_response': {
                    'ShoppingResponseID': {
                        'ResponseID': {
                            'value': 'NESTED-SHOP-456'
                        }
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_id(response, 'ShoppingResponseID')
        assert result == 'NESTED-SHOP-456'
    
    def test_extract_shopping_response_id_deep_nested(self):
        """Test extracting ShoppingResponseID from data.raw_response.data.raw_response."""
        response = {
            'data': {
                'raw_response': {
                    'data': {
                        'raw_response': {
                            'ShoppingResponseID': {
                                'ResponseID': {
                                    'value': 'DEEP-SHOP-789'
                                }
                            }
                        }
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_id(response, 'ShoppingResponseID')
        assert result == 'DEEP-SHOP-789'
    
    def test_extract_offer_id_with_value_field(self):
        """Test extracting OfferID with value field."""
        response = {
            'OfferID': {
                'value': 'OFFER-ABC-123'
            }
        }
        
        result = FlightResponseNavigator.extract_id(response, 'OfferID')
        assert result == 'OFFER-ABC-123'
    
    def test_extract_id_from_flight_price_rs(self):
        """Test extracting ID from FlightPriceRS structure."""
        response = {
            'FlightPriceRS': {
                'ShoppingResponseID': {
                    'ResponseID': {
                        'value': 'FP-SHOP-999'
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_id(response, 'ShoppingResponseID')
        assert result == 'FP-SHOP-999'
    
    def test_extract_id_returns_none_when_not_found(self):
        """Test that extract_id returns None when ID not found."""
        response = {
            'SomeOtherField': 'value'
        }
        
        result = FlightResponseNavigator.extract_id(response, 'ShoppingResponseID')
        assert result is None
    
    def test_extract_id_handles_empty_response(self):
        """Test that extract_id handles empty response."""
        result = FlightResponseNavigator.extract_id({}, 'ShoppingResponseID')
        assert result is None
    
    def test_extract_id_handles_none_response(self):
        """Test that extract_id handles None response."""
        result = FlightResponseNavigator.extract_id(None, 'ShoppingResponseID')
        assert result is None


class TestExtractOfferIdFromPricedOffers:
    """Test suite for extract_offer_id_from_priced_offers method."""
    
    def test_extract_offer_id_from_direct_priced_offers(self):
        """Test extracting OfferID from direct PricedFlightOffers."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {
                        'OfferID': {
                            'value': 'OFFER-123'
                        }
                    }
                ]
            }
        }
        
        result = FlightResponseNavigator.extract_offer_id_from_priced_offers(response)
        assert result == 'OFFER-123'
    
    def test_extract_offer_id_from_nested_priced_offers(self):
        """Test extracting OfferID from nested structure."""
        response = {
            'data': {
                'raw_response': {
                    'PricedFlightOffers': {
                        'PricedFlightOffer': [
                            {
                                'OfferID': {
                                    'value': 'NESTED-OFFER-456'
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_offer_id_from_priced_offers(response)
        assert result == 'NESTED-OFFER-456'
    
    def test_extract_offer_id_handles_single_offer_as_dict(self):
        """Test extracting OfferID when PricedFlightOffer is a dict (not list)."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': {
                    'OfferID': {
                        'value': 'SINGLE-OFFER'
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_offer_id_from_priced_offers(response)
        assert result == 'SINGLE-OFFER'
    
    def test_extract_offer_id_returns_none_when_not_found(self):
        """Test that method returns None when OfferID not found."""
        response = {
            'SomeOtherField': 'value'
        }
        
        result = FlightResponseNavigator.extract_offer_id_from_priced_offers(response)
        assert result is None


class TestGetPricedFlightOffers:
    """Test suite for get_priced_flight_offers method."""
    
    def test_get_priced_offers_as_list(self):
        """Test getting PricedFlightOffer when it's already a list."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {'OfferID': 'OFFER-1'},
                    {'OfferID': 'OFFER-2'}
                ]
            }
        }
        
        result = FlightResponseNavigator.get_priced_flight_offers(response)
        assert len(result) == 2
        assert result[0]['OfferID'] == 'OFFER-1'
        assert result[1]['OfferID'] == 'OFFER-2'
    
    def test_get_priced_offers_converts_dict_to_list(self):
        """Test converting single PricedFlightOffer dict to list."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': {'OfferID': 'SINGLE-OFFER'}
            }
        }
        
        result = FlightResponseNavigator.get_priced_flight_offers(response)
        assert len(result) == 1
        assert result[0]['OfferID'] == 'SINGLE-OFFER'
    
    def test_get_priced_offers_returns_empty_list_when_not_found(self):
        """Test returning empty list when PricedFlightOffers not found."""
        response = {
            'SomeOtherField': 'value'
        }
        
        result = FlightResponseNavigator.get_priced_flight_offers(response)
        assert result == []
    
    def test_get_priced_offers_handles_none_response(self):
        """Test handling None response."""
        result = FlightResponseNavigator.get_priced_flight_offers(None)
        assert result == []
    
    def test_get_priced_offers_handles_empty_response(self):
        """Test handling empty response."""
        result = FlightResponseNavigator.get_priced_flight_offers({})
        assert result == []


class TestNavigateNested:
    """Test suite for navigate_nested method."""
    
    def test_navigate_simple_path(self):
        """Test navigating a simple path."""
        response = {
            'level1': {
                'level2': {
                    'value': 'target'
                }
            }
        }
        
        result = FlightResponseNavigator.navigate_nested(response, 'level1', 'level2', 'value')
        assert result == 'target'
    
    def test_navigate_returns_none_for_missing_path(self):
        """Test returning None when path doesn't exist."""
        response = {
            'level1': {
                'level2': 'value'
            }
        }
        
        result = FlightResponseNavigator.navigate_nested(response, 'level1', 'level3')
        assert result is None
    
    def test_navigate_handles_none_response(self):
        """Test handling None response."""
        result = FlightResponseNavigator.navigate_nested(None, 'level1')
        assert result is None


class TestExtractAirlineCode:
    """Test suite for extract_airline_code method."""
    
    def test_extract_airline_from_shopping_response_owner(self):
        """Test extracting airline code from ShoppingResponse Owner."""
        response = {
            'Query': {
                'OrderItems': {
                    'ShoppingResponse': {
                        'Owner': 'KQ'
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_airline_code(response)
        assert result == 'KQ'
    
    def test_extract_airline_from_priced_offers_owner(self):
        """Test extracting airline code from PricedFlightOffers OfferID Owner."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {
                        'OfferID': {
                            'Owner': 'WY'
                        }
                    }
                ]
            }
        }
        
        result = FlightResponseNavigator.extract_airline_code(response)
        assert result == 'WY'
    
    def test_extract_airline_from_shopping_response_id(self):
        """Test extracting airline code from ShoppingResponseID."""
        response = {
            'ShoppingResponseID': {
                'ResponseID': {
                    'value': 'KQ-2024-12345'
                }
            }
        }
        
        result = FlightResponseNavigator.extract_airline_code(response)
        assert result == 'KQ'
    
    def test_extract_airline_returns_unknown_when_not_found(self):
        """Test returning 'UNKNOWN' when airline code not found."""
        response = {
            'SomeOtherField': 'value'
        }
        
        result = FlightResponseNavigator.extract_airline_code(response)
        assert result == 'UNKNOWN'


class TestExtractOfferItemIds:
    """Test suite for extract_offer_item_ids method."""
    
    def test_extract_offer_item_ids_from_priced_offers(self):
        """Test extracting OfferItemIDs from PricedFlightOffers."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {
                        'OfferPrice': [
                            {'OfferItemID': 'ITEM-1'},
                            {'OfferItemID': 'ITEM-2'}
                        ]
                    }
                ]
            }
        }
        
        result = FlightResponseNavigator.extract_offer_item_ids(response)
        assert len(result) == 2
        assert 'ITEM-1' in result
        assert 'ITEM-2' in result
    
    def test_extract_offer_item_ids_handles_single_offer_price(self):
        """Test extracting OfferItemIDs when OfferPrice is a dict."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {
                        'OfferPrice': {'OfferItemID': 'SINGLE-ITEM'}
                    }
                ]
            }
        }
        
        result = FlightResponseNavigator.extract_offer_item_ids(response)
        assert len(result) == 1
        assert 'SINGLE-ITEM' in result
    
    def test_extract_offer_item_ids_from_nested_structure(self):
        """Test extracting OfferItemIDs from nested structure."""
        response = {
            'data': {
                'raw_response': {
                    'PricedFlightOffers': {
                        'PricedFlightOffer': [
                            {
                                'OfferPrice': [
                                    {'OfferItemID': 'NESTED-ITEM'}
                                ]
                            }
                        ]
                    }
                }
            }
        }
        
        result = FlightResponseNavigator.extract_offer_item_ids(response)
        assert len(result) == 1
        assert 'NESTED-ITEM' in result
    
    def test_extract_offer_item_ids_removes_duplicates(self):
        """Test that duplicate OfferItemIDs are not included."""
        response = {
            'PricedFlightOffers': {
                'PricedFlightOffer': [
                    {
                        'OfferPrice': [
                            {'OfferItemID': 'ITEM-1'},
                            {'OfferItemID': 'ITEM-1'}  # Duplicate
                        ]
                    }
                ]
            }
        }
        
        result = FlightResponseNavigator.extract_offer_item_ids(response)
        # Should only have one ITEM-1
        assert result.count('ITEM-1') == 1
    
    def test_extract_offer_item_ids_returns_empty_list_when_not_found(self):
        """Test returning empty list when no OfferItemIDs found."""
        response = {
            'SomeOtherField': 'value'
        }
        
        result = FlightResponseNavigator.extract_offer_item_ids(response)
        assert result == []
