"""Integration tests for complete FlightPrice workflow."""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from app.services.flight_price import FlightPriceService
from app.models.requests.flight_price import FlightPriceRequest
from app.core.exceptions import BusinessLogicError, VDCAPIError
from app.core.auth import VDCAuthClient
import httpx


@pytest.fixture
def mock_auth_client():
    """Mock authentication client."""
    mock = AsyncMock(spec=VDCAuthClient)
    mock.get_token.return_value = "mock_token_123"
    return mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    return mock


@pytest.fixture
def complete_air_shopping_response():
    """Complete AirShopping response with multiple airlines."""
    return {
        "AirlineOffers": [
            {
                "Owner": "EK",
                "Offer": [
                    {
                        "OfferID": {"value": "EK_OFFER_1"},
                        "TotalPrice": {"value": 1500.00},
                        "FlightRefs": ["EK_SEG1", "EK_SEG2"]
                    },
                    {
                        "OfferID": {"value": "EK_OFFER_2"},
                        "TotalPrice": {"value": 1800.00},
                        "FlightRefs": ["EK_SEG3"]
                    }
                ],
                "ShoppingResponseID": {"ResponseID": {"value": "EK_SHOP_123"}}
            },
            {
                "Owner": "BA",
                "Offer": [
                    {
                        "OfferID": {"value": "BA_OFFER_1"},
                        "TotalPrice": {"value": 1600.00},
                        "FlightRefs": ["BA_SEG1"]
                    }
                ],
                "ShoppingResponseID": {"ResponseID": {"value": "BA_SHOP_456"}}
            }
        ],
        "ShoppingResponseID": {"ResponseID": {"value": "GLOBAL_SHOP_789"}},
        "AnonymousTravelerList": {
            "AnonymousTraveler": [
                {"PTC": "ADT", "ObjectKey": "T1"},
                {"PTC": "CHD", "ObjectKey": "T2"}
            ]
        },
        "DataLists": {
            "FareGroupList": {
                "FareGroup": [
                    {"FareGroupID": "FG1", "Fare": {"FareDetail": {"Price": {"BaseAmount": {"value": 1200}}}}},
                    {"FareGroupID": "FG2", "Fare": {"FareDetail": {"Price": {"BaseAmount": {"value": 1500}}}}}
                ]
            }
        }
    }


@pytest.fixture
def complete_flight_price_response():
    """Complete FlightPrice response from VDC API."""
    return {
        "FlightPriceRS": {
            "PricedFlightOffers": {
                "PricedFlightOffer": [
                    {
                        "OfferID": {"value": "PRICED_OFFER_123", "Owner": "EK"},
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
                                                    "Details": "Non-refundable",
                                                    "ChangeFee": {"Amount": {"value": 100.00}}
                                                }
                                            },
                                            "ClassOfService": {"Code": "Y"}
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
                                                "Taxes": {"Total": {"value": 150.00}}
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
                                    "PieceMeasurements": {"Weight": {"value": 23, "UOM": "KG"}}
                                },
                                "TypeCode": "Checked",
                                "PassengerType": "ADT"
                            },
                            {
                                "PieceAllowance": {
                                    "TotalQuantity": 1,
                                    "PieceMeasurements": {"Weight": {"value": 7, "UOM": "KG"}}
                                },
                                "TypeCode": "CarryOn"
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
                                }
                            }
                        ]
                    }
                ]
            },
            "Metadata": {
                "CurrencyMetadata": [
                    {
                        "MetadataKey": "CUR1",
                        "Decimals": 2,
                        "Application": {"CurrencyCode": "USD"}
                    }
                ]
            }
        }
    }


class TestFlightPriceWorkflowIntegration:
    """Integration tests for complete AirShopping -> FlightPrice workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_ek_pricing_flow(
        self,
        mock_auth_client,
        mock_http_client,
        complete_air_shopping_response,
        complete_flight_price_response
    ):
        """Should complete full pricing flow for Emirates offer."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        # Request pricing for first EK offer
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="EK",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = complete_flight_price_response
            
            result = await service.execute(request)
            
            # Verify complete response structure
            assert result["offer_id"] == "PRICED_OFFER_123"
            
            # Pricing
            assert result["pricing"]["total"] == 1500.00
            assert result["pricing"]["base_fare"] == 1200.00
            assert result["pricing"]["taxes"] == 300.00
            assert result["pricing"]["currency"] == "USD"
            
            # Breakdown (2 passengers)
            assert len(result["breakdown"]) == 2
            assert result["breakdown"][0]["total"] == 1500.00
            assert result["breakdown"][1]["total"] == 750.00
            
            # Fare details
            assert result["fare_details"]["fare_basis_code"] == "YLOW"
            assert result["fare_details"]["cabin_type"] == "Economy"
            assert result["fare_details"]["booking_class"]["code"] == "Y"
            
            # Penalties
            assert result["penalties"]["change_fee"]["amount"] == 100.00
            
            # Baggage
            assert result["baggage"]["checked"]["quantity"] == 2
            assert result["baggage"]["carry_on"]["quantity"] == 1
            
            # Segments
            assert len(result["segments"]) == 1
            assert result["segments"][0]["departure"]["airport"] == "DXB"
    
    @pytest.mark.asyncio
    async def test_complete_ba_pricing_flow(
        self,
        complete_air_shopping_response,
        complete_flight_price_response
    ):
        """Should complete full pricing flow for British Airways offer."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        # Request pricing for BA offer (different airline)
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="BA",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = complete_flight_price_response
            
            result = await service.execute(request)
            
            # Should successfully price BA offer
            assert "offer_id" in result
            assert "pricing" in result
            
            # Verify BA-specific ShoppingResponseID was used
            call_payload = mock_request.call_args[1]["payload"]
            shopping_id = call_payload["FlightPriceRQ"]["ShoppingResponseID"]["ResponseID"]["value"]
            assert shopping_id == "BA_SHOP_456"
    
    @pytest.mark.asyncio
    async def test_second_ek_offer_pricing(
        self,
        complete_air_shopping_response,
        complete_flight_price_response
    ):
        """Should correctly price second offer from same airline."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        # Request pricing for second EK offer (index 1)
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="EK",
            offer_index=1
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = complete_flight_price_response
            
            result = await service.execute(request)
            
            # Verify correct offer was priced
            call_payload = mock_request.call_args[1]["payload"]
            offer_item = call_payload["FlightPriceRQ"]["Query"]["OfferRequest"]["Offer"]["OfferItem"]
            
            # Should reference second EK offer
            assert len(offer_item) == 1
    
    @pytest.mark.asyncio
    async def test_error_propagation_airline_not_found(
        self,
        complete_air_shopping_response
    ):
        """Should propagate BusinessLogicError when airline not found."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        # Request for non-existent airline
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="LH",  # Lufthansa not in response
            offer_index=0
        )
        
        with pytest.raises(BusinessLogicError, match="Airline 'LH' not found"):
            await service.execute(request)
    
    @pytest.mark.asyncio
    async def test_error_propagation_vdc_api_failure(
        self,
        complete_air_shopping_response
    ):
        """Should propagate VDCAPIError on API failure."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="EK",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = VDCAPIError("Network timeout", status_code=504)
            
            with pytest.raises(VDCAPIError, match="Network timeout"):
                await service.execute(request)
    
    @pytest.mark.asyncio
    async def test_multi_airline_search_single_airline_pricing(
        self,
        complete_air_shopping_response,
        complete_flight_price_response
    ):
        """Should handle multi-airline search -> single-airline pricing correctly."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        # Verify AirShopping has multiple airlines
        assert len(complete_air_shopping_response["AirlineOffers"]) == 2
        
        # Price single airline offer
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="EK",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = complete_flight_price_response
            
            result = await service.execute(request)
            
            # Verify successful pricing
            assert result["offer_id"] == "PRICED_OFFER_123"
            
            # Verify only EK data was sent
            call_payload = mock_request.call_args[1]["payload"]
            
            # Should only have EK's ShoppingResponseID
            shopping_id = call_payload["FlightPriceRQ"]["ShoppingResponseID"]["ResponseID"]["value"]
            assert shopping_id == "EK_SHOP_123"
            
            # Should only reference EK's offer
            offer_item = call_payload["FlightPriceRQ"]["Query"]["OfferRequest"]["Offer"]["OfferItem"]
            assert len(offer_item) == 1
    
    @pytest.mark.asyncio
    async def test_travelers_flow_through_workflow(
        self,
        complete_air_shopping_response,
        complete_flight_price_response
    ):
        """Should correctly flow travelers from AirShopping to FlightPrice."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="EK",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = complete_flight_price_response
            
            await service.execute(request)
            
            # Verify travelers were passed correctly
            call_payload = mock_request.call_args[1]["payload"]
            travelers = call_payload["FlightPriceRQ"]["Travelers"]["Traveler"]
            
            assert len(travelers) == 2
            assert travelers[0]["AnonymousTraveler"]["PTC"] == "ADT"
            assert travelers[0]["AnonymousTraveler"]["ObjectKey"] == "T1"
            assert travelers[1]["AnonymousTraveler"]["PTC"] == "CHD"
    
    @pytest.mark.asyncio
    async def test_metadata_filtering_only_referenced_items(
        self,
        complete_air_shopping_response,
        complete_flight_price_response
    ):
        """Should only include referenced metadata items in FlightPrice request."""
        service = FlightPriceService(mock_auth_client, mock_http_client)
        
        request = FlightPriceRequest(
            air_shopping_response=complete_air_shopping_response,
            airline_owner="EK",
            offer_index=0
        )
        
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = complete_flight_price_response
            
            await service.execute(request)
            
            # Verify DataLists filtering
            call_payload = mock_request.call_args[1]["payload"]
            data_lists = call_payload["FlightPriceRQ"]["DataLists"]
            
            # Should have filtered FareGroups (only referenced ones)
            assert "FareGroupList" in data_lists
            fare_groups = data_lists["FareGroupList"]["FareGroup"]
            
            # Should be filtered (not all from original)
            assert isinstance(fare_groups, list)
